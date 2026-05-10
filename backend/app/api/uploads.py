from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_store
from app.models.store import Store
from app.models.upload import Upload
from app.schemas.upload import UploadRead
from app.workers.process_upload import process_upload


router = APIRouter(prefix="/uploads", tags=["uploads"])


def _save_uploaded_file(upload_file: UploadFile, store_id, upload_type: str) -> tuple[Path, str]:
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A CSV file is required.",
        )

    destination_dir = settings.upload_dir / str(store_id)
    destination_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload_file.filename).suffix or ".csv"
    destination_path = destination_dir / f"{upload_type}-{uuid4()}{suffix}"
    file_hash = hashlib.sha256()

    with destination_path.open("wb") as file_handle:
        while chunk := upload_file.file.read(1024 * 1024):
            file_handle.write(chunk)
            file_hash.update(chunk)

    upload_file.file.seek(0)
    return destination_path, file_hash.hexdigest()


def _queue_upload(
    upload_type: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_store: Store,
    db: Session,
) -> Upload:
    file_path, file_hash = _save_uploaded_file(file, current_store.id, upload_type)

    upload = Upload(
        store_id=current_store.id,
        upload_type=upload_type,
        import_type="csv",
        file_path=str(file_path),
        file_hash=file_hash,
        status="pending",
        rows_inserted=0,
        rows_skipped=0,
        can_reprocess=True,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    background_tasks.add_task(process_upload, str(upload.id))
    return upload


@router.post("/orders", response_model=UploadRead, status_code=status.HTTP_202_ACCEPTED)
def upload_orders(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> UploadRead:
    return UploadRead.model_validate(
        _queue_upload("orders", file, background_tasks, current_store, db)
    )


@router.post("/ads", response_model=UploadRead, status_code=status.HTTP_202_ACCEPTED)
def upload_ads(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> UploadRead:
    return UploadRead.model_validate(
        _queue_upload("ads", file, background_tasks, current_store, db)
    )


@router.post("/settlement", response_model=UploadRead, status_code=status.HTTP_202_ACCEPTED)
def upload_settlement(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> UploadRead:
    return UploadRead.model_validate(
        _queue_upload("settlement", file, background_tasks, current_store, db)
    )


@router.get("", response_model=list[UploadRead])
def list_uploads(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> list[UploadRead]:
    uploads = db.scalars(
        select(Upload)
        .where(Upload.store_id == current_store.id)
        .order_by(Upload.uploaded_at.desc())
    ).all()
    return [UploadRead.model_validate(upload) for upload in uploads]
