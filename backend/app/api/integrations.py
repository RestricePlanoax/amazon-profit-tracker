from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db, utcnow
from app.core.security import get_current_store, get_current_user
from app.models.integration import Integration
from app.models.store import Store
from app.models.sync_job import SyncJob
from app.models.user import User
from app.schemas.integration import (
    IntegrationConnectRequest,
    IntegrationRead,
    IntegrationStatusResponse,
    SyncJobRead,
)
from app.workers.process_integration_sync import run_integration_sync


router = APIRouter(prefix="/integrations", tags=["integrations"])


def _get_integration(db: Session, user_id, store_id) -> Integration | None:
    return db.scalar(
        select(Integration)
        .where(Integration.user_id == user_id, Integration.store_id == store_id)
        .order_by(Integration.updated_at.desc())
    )


def _get_latest_sync_job(db: Session, integration_id) -> SyncJob | None:
    return db.scalar(
        select(SyncJob)
        .where(SyncJob.integration_id == integration_id)
        .order_by(SyncJob.created_at.desc())
    )


def _build_status_response(db: Session, integration: Integration | None) -> IntegrationStatusResponse:
    latest_job = _get_latest_sync_job(db, integration.id) if integration else None
    return IntegrationStatusResponse(
        integration=IntegrationRead.model_validate(integration) if integration else None,
        has_connection=integration is not None and integration.status != "disconnected",
        latest_job=SyncJobRead.model_validate(latest_job) if latest_job else None,
    )


@router.get("/status", response_model=IntegrationStatusResponse)
def get_integration_status(
    current_user: User = Depends(get_current_user),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> IntegrationStatusResponse:
    integration = _get_integration(db, current_user.id, current_store.id)
    return _build_status_response(db, integration)


@router.post("/connect", response_model=IntegrationRead)
def connect_integration(
    payload: IntegrationConnectRequest,
    current_user: User = Depends(get_current_user),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> IntegrationRead:
    integration = _get_integration(db, current_user.id, current_store.id)

    if integration is None:
        integration = Integration(
            user_id=current_user.id,
            store_id=current_store.id,
            provider="amazon",
            status="connected",
            region=payload.marketplace.lower(),
            connected_at=utcnow(),
        )
        db.add(integration)
    else:
        integration.provider = "amazon"
        integration.status = "connected"
        integration.region = payload.marketplace.lower()
        if integration.connected_at is None:
            integration.connected_at = utcnow()

    db.commit()
    db.refresh(integration)
    return IntegrationRead.model_validate(integration)


@router.post("/sync", response_model=IntegrationStatusResponse)
def sync_integration(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> IntegrationStatusResponse:
    integration = _get_integration(db, current_user.id, current_store.id)
    if integration is None or integration.status == "disconnected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connect Amazon before starting a sync.",
        )

    active_job = db.scalar(
        select(SyncJob)
        .where(SyncJob.integration_id == integration.id)
        .where(SyncJob.status.in_(["queued", "running"]))
        .order_by(SyncJob.created_at.desc())
    )
    if active_job is not None:
        return _build_status_response(db, integration)

    integration.status = "syncing"
    job = SyncJob(
        integration_id=integration.id,
        job_type="full_sync",
        status="queued",
        progress_percent=0,
        rows_processed=0,
    )
    db.add(job)
    db.commit()
    db.refresh(integration)
    db.refresh(job)

    background_tasks.add_task(run_integration_sync, integration.id, job.id)
    return _build_status_response(db, integration)


@router.post("/reconnect", response_model=IntegrationStatusResponse)
def reconnect_integration(
    payload: IntegrationConnectRequest,
    current_user: User = Depends(get_current_user),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> IntegrationStatusResponse:
    integration = _get_integration(db, current_user.id, current_store.id)
    if integration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Amazon connection exists yet.",
        )

    integration.provider = "amazon"
    integration.region = payload.marketplace.lower()
    integration.status = "connected"
    integration.connected_at = integration.connected_at or utcnow()
    db.commit()
    db.refresh(integration)
    return _build_status_response(db, integration)


@router.post("/disconnect", response_model=IntegrationStatusResponse)
def disconnect_integration(
    current_user: User = Depends(get_current_user),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> IntegrationStatusResponse:
    integration = _get_integration(db, current_user.id, current_store.id)
    if integration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Amazon connection exists yet.",
        )

    integration.status = "disconnected"
    db.commit()
    db.refresh(integration)
    return _build_status_response(db, integration)
