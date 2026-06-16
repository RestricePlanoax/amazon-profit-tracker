from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_store
from app.models.store import Store
from app.schemas.analytics import (
    AdAnalysisResponse,
    DailyInsightsResponse,
    ProfitAlertRead,
    ProfitAlertsResponse,
    ReimbursementsResponse,
    ReturnAnalysisResponse,
    StorageAnalysisResponse,
)
from app.services.ad_analytics_service import AdAnalyticsService
from app.services.insight_generation_service import InsightGenerationService
from app.services.profit_analysis_service import ProfitAnalysisService
from app.services.reimbursement_analysis_service import ReimbursementService
from app.services.return_analytics_service import ReturnAnalyticsService
from app.services.storage_analysis_service import StorageAnalysisService


router = APIRouter(tags=["analytics"])
profit_analysis_service = ProfitAnalysisService()
return_analytics_service = ReturnAnalyticsService()
reimbursement_service = ReimbursementService()
storage_analysis_service = StorageAnalysisService()
ad_analytics_service = AdAnalyticsService()
insight_generation_service = InsightGenerationService()


@router.get("/profit-alerts", response_model=ProfitAlertsResponse)
def list_profit_alerts(
    include_resolved: bool = Query(default=False),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> ProfitAlertsResponse:
    return ProfitAlertsResponse(**profit_analysis_service.get_profit_alerts(db, current_store.id, include_resolved))


@router.post("/profit-alerts/{alert_id}/resolve", response_model=ProfitAlertRead)
def resolve_profit_alert(
    alert_id: UUID,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> ProfitAlertRead:
    alert = profit_analysis_service.resolve_alert(db, current_store.id, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    db.commit()
    db.refresh(alert)
    return ProfitAlertRead.model_validate(alert)


@router.get("/return-analysis", response_model=ReturnAnalysisResponse)
def get_return_analysis(
    range: str | None = Query(default=None),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> ReturnAnalysisResponse:
    return ReturnAnalysisResponse(**return_analytics_service.get_return_analysis(db, current_store.id, range))


@router.get("/reimbursements", response_model=ReimbursementsResponse)
def get_reimbursements(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> ReimbursementsResponse:
    return ReimbursementsResponse(**reimbursement_service.get_reimbursements(db, current_store.id))


@router.get("/storage-analysis", response_model=StorageAnalysisResponse)
def get_storage_analysis(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> StorageAnalysisResponse:
    return StorageAnalysisResponse(**storage_analysis_service.get_storage_analysis(db, current_store.id))


@router.get("/ad-analysis", response_model=AdAnalysisResponse)
def get_ad_analysis(
    range: str | None = Query(default=None),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> AdAnalysisResponse:
    return AdAnalysisResponse(**ad_analytics_service.get_ad_analysis(db, current_store.id, range))


@router.get("/daily-insights", response_model=DailyInsightsResponse)
def get_daily_insights(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> DailyInsightsResponse:
    return DailyInsightsResponse(**insight_generation_service.get_daily_insights(db, current_store.id))
