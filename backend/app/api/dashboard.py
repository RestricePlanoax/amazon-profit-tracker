from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_store
from app.models.store import Store
from app.schemas.dashboard import (
    DashboardInsightsResponse,
    DashboardSummary,
    DateBounds,
    TrendPoint,
)
from app.services.metrics_service import (
    get_dashboard_summary,
    get_dashboard_trends,
    get_product_profitability,
    get_store_date_bounds,
)
from app.services.recommendation_service import RecommendationContext, RulesBasedRecommendationGenerator


router = APIRouter(prefix="/dashboard", tags=["dashboard"])
recommendation_generator = RulesBasedRecommendationGenerator()


@router.get("/date-bounds", response_model=DateBounds)
def get_date_bounds(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> DateBounds:
    return DateBounds(**get_store_date_bounds(db, current_store.id))


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    range: str | None = Query(default=None),
    start_date: date | None = None,
    end_date: date | None = None,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> DashboardSummary:
    return DashboardSummary(
        **get_dashboard_summary(
            db,
            current_store.id,
            range,
            start_date,
            end_date,
        )
    )


@router.get("/trends", response_model=list[TrendPoint])
def get_trends(
    range: str | None = Query(default=None),
    start_date: date | None = None,
    end_date: date | None = None,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> list[TrendPoint]:
    return [
        TrendPoint(**row)
        for row in get_dashboard_trends(
            db,
            current_store.id,
            range,
            start_date,
            end_date,
        )
    ]


@router.get("/insights", response_model=DashboardInsightsResponse)
def get_insights(
    range: str | None = Query(default=None),
    start_date: date | None = None,
    end_date: date | None = None,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> DashboardInsightsResponse:
    summary = get_dashboard_summary(db, current_store.id, range, start_date, end_date)
    products = get_product_profitability(db, current_store.id, range, start_date, end_date)

    current_metrics = {key: value["current"] for key, value in summary["metrics"].items()}
    previous_metrics = {key: value["previous"] for key, value in summary["metrics"].items()}
    context = RecommendationContext(
        start_date=summary["start_date"],
        end_date=summary["end_date"],
        metrics=current_metrics,
        previous_metrics=previous_metrics,
        top_products=products[:3],
        risk_products=[product for product in reversed(products) if product["profit_margin"] < 10][:3],
    )
    return DashboardInsightsResponse(**recommendation_generator.generate(context))
