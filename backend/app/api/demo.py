from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_store
from app.models.store import Store
from app.schemas.demo import DemoLoadResponse
from app.services.demo_service import load_demo_store


router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/load", response_model=DemoLoadResponse)
def load_demo_data(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> DemoLoadResponse:
    batch, rows_inserted = load_demo_store(db, current_store.id)
    return DemoLoadResponse(
        store_id=str(current_store.id),
        import_batch_id=str(batch.id),
        rows_inserted=rows_inserted,
        message="Demo store loaded with 180 days of realistic Amazon seller data.",
    )
