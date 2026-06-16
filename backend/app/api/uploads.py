from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_store
from app.models.ad import Ad
from app.models.ad_campaign_metric import AdCampaignMetric
from app.models.import_batch import ImportBatch
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.reimbursement import Reimbursement
from app.models.return_analytics import ReturnAnalytics
from app.models.settlement import Settlement
from app.models.store import Store
from app.models.upload import Upload
from app.schemas.upload import UploadRead
from app.services.analysis_runner import StoreAnalysisRunner
from app.workers.process_upload import process_upload


router = APIRouter(prefix="/uploads", tags=["uploads"])
analysis_runner = StoreAnalysisRunner()


def _parse_upload_id(upload_id: str) -> UUID:
    try:
        return UUID(upload_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found.",
        ) from exc


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

    duplicate_upload = db.scalar(
        select(Upload)
        .where(Upload.store_id == current_store.id)
        .where(Upload.upload_type == upload_type)
        .where(Upload.file_hash == file_hash)
        .where(Upload.status.in_(["pending", "processing", "completed"]))
        .order_by(Upload.uploaded_at.desc())
        .limit(1)
    )
    if duplicate_upload is not None:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This exact file has already been imported or is currently processing. "
                "Delete or reprocess the previous import if you need to reload it."
            ),
        )

    batch = ImportBatch(
        store_id=current_store.id,
        source_type="csv",
        import_type=upload_type,
        status="pending",
        file_path=str(file_path),
        file_hash=file_hash,
        rows_inserted=0,
        rows_skipped=0,
        can_reprocess=True,
    )
    db.add(batch)
    db.flush()

    upload = Upload(
        store_id=current_store.id,
        import_batch_id=batch.id,
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


def _delete_batch_rows(db: Session, store_id, batch_id) -> None:
    for model in [Order, Ad, Settlement, Inventory, ReturnAnalytics, Reimbursement, AdCampaignMetric]:
        db.execute(
            delete(model)
            .where(model.store_id == store_id)
            .where(model.import_batch_id == batch_id)
        )


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


@router.post("/returns", response_model=UploadRead, status_code=status.HTTP_202_ACCEPTED)
def upload_returns(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> UploadRead:
    return UploadRead.model_validate(
        _queue_upload("returns", file, background_tasks, current_store, db)
    )


@router.post("/reimbursements", response_model=UploadRead, status_code=status.HTTP_202_ACCEPTED)
def upload_reimbursements(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> UploadRead:
    return UploadRead.model_validate(
        _queue_upload("reimbursements", file, background_tasks, current_store, db)
    )


@router.post("/campaigns", response_model=UploadRead, status_code=status.HTTP_202_ACCEPTED)
def upload_campaigns(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> UploadRead:
    return UploadRead.model_validate(
        _queue_upload("campaigns", file, background_tasks, current_store, db)
    )


@router.post("/inventory", response_model=UploadRead, status_code=status.HTTP_202_ACCEPTED)
def upload_inventory(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> UploadRead:
    return UploadRead.model_validate(
        _queue_upload("inventory", file, background_tasks, current_store, db)
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


@router.delete("/{upload_id}", response_model=UploadRead)
def delete_upload(
    upload_id: str,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> UploadRead:
    upload = db.get(Upload, _parse_upload_id(upload_id))
    if upload is None or upload.store_id != current_store.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found.",
        )
    if upload.import_batch_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This older upload is not linked to an import batch and cannot be deleted safely.",
        )
    if upload.status in {"pending", "processing"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This import is still running. Wait for it to complete or fail before deleting it.",
        )

    _delete_batch_rows(db, current_store.id, upload.import_batch_id)
    batch = db.get(ImportBatch, upload.import_batch_id)
    if batch is not None:
        from app.core.database import utcnow

        batch.status = "deleted"
        batch.deleted_at = utcnow()
        batch.error_message = None

    upload.status = "deleted"
    upload.error_message = None
    upload.can_reprocess = True

    from app.services.metrics_service import recompute_daily_metrics

    recompute_daily_metrics(db, current_store.id)
    analysis_runner.run(db, current_store.id)
    db.commit()
    db.refresh(upload)
    return UploadRead.model_validate(upload)


@router.post("/{upload_id}/reprocess", response_model=UploadRead, status_code=status.HTTP_202_ACCEPTED)
def reprocess_upload(
    upload_id: str,
    background_tasks: BackgroundTasks,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> UploadRead:
    upload = db.get(Upload, _parse_upload_id(upload_id))
    if upload is None or upload.store_id != current_store.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found.",
        )
    if upload.import_batch_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This older upload is not linked to an import batch and cannot be reprocessed safely.",
        )
    if not upload.can_reprocess:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This upload cannot be reprocessed.",
        )
    if upload.status in {"pending", "processing"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This import is still running. Wait for it to complete or fail before reprocessing it.",
        )
    if not Path(upload.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The original CSV file is no longer available for reprocessing.",
        )

    _delete_batch_rows(db, current_store.id, upload.import_batch_id)
    batch = db.get(ImportBatch, upload.import_batch_id)
    if batch is not None:
        batch.status = "pending"
        batch.rows_inserted = 0
        batch.rows_skipped = 0
        batch.error_message = None
        batch.deleted_at = None
        batch.started_at = None
        batch.completed_at = None

    upload.status = "pending"
    upload.rows_inserted = 0
    upload.rows_skipped = 0
    upload.error_message = None
    db.commit()
    db.refresh(upload)

    background_tasks.add_task(process_upload, str(upload.id))
    return UploadRead.model_validate(upload)
