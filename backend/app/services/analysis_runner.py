from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.ad_analytics_service import AdAnalyticsService
from app.services.insight_generation_service import InsightGenerationService
from app.services.profit_analysis_service import ProfitAnalysisService
from app.services.reimbursement_analysis_service import ReimbursementService
from app.services.return_analytics_service import ReturnAnalyticsService
from app.services.storage_analysis_service import StorageAnalysisService


class StoreAnalysisRunner:
    def __init__(self) -> None:
        self.profit_analysis = ProfitAnalysisService()
        self.return_analysis = ReturnAnalyticsService()
        self.reimbursement_analysis = ReimbursementService()
        self.storage_analysis = StorageAnalysisService()
        self.ad_analysis = AdAnalyticsService()
        self.insight_generation = InsightGenerationService()

    def run(self, db: Session, store_id) -> dict:
        self.storage_analysis.refresh_inventory_aging(db, store_id)
        alerts = self.profit_analysis.refresh_alerts(db, store_id)
        insights = self.insight_generation.refresh_daily_insights(db, store_id)
        db.flush()
        return {
            "alerts_created": len(alerts),
            "insights_created": len(insights),
        }
