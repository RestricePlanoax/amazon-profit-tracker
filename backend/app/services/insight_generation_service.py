from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.profit_alert import ProfitAlert
from app.models.seller_insight import SellerInsight
from app.services.metrics_service import MIN_SELECTABLE_DATE, get_product_profitability, get_store_date_bounds
from app.services.reimbursement_analysis_service import ReimbursementService


class InsightGenerationService:
    def __init__(self) -> None:
        self.reimbursement_service = ReimbursementService()

    def refresh_daily_insights(self, db: Session, store_id) -> list[SellerInsight]:
        db.execute(
            delete(SellerInsight)
            .where(SellerInsight.store_id == store_id)
            .where(SellerInsight.insight_type == "daily_briefing")
        )

        bounds = get_store_date_bounds(db, store_id)
        end_date = date.fromisoformat(bounds["max_date"])
        start_date = max(MIN_SELECTABLE_DATE, end_date - timedelta(days=6))
        products = get_product_profitability(db, store_id, start_date=start_date, end_date=end_date)
        alerts = db.scalars(
            select(ProfitAlert)
            .where(ProfitAlert.store_id == store_id)
            .where(ProfitAlert.resolved.is_(False))
            .order_by(ProfitAlert.severity.desc(), ProfitAlert.created_at.desc())
        ).all()
        reimbursements = self.reimbursement_service.get_reimbursements(db, store_id)

        insights: list[SellerInsight] = []
        if alerts:
            lead_alert = alerts[0]
            insights.append(
                SellerInsight(
                    store_id=store_id,
                    priority="critical" if lead_alert.severity == "critical" else "high",
                    headline="Today's biggest profit leak",
                    insight_text=lead_alert.message,
                )
            )

        if products:
            best_product = products[0]
            worst_product = min(products, key=lambda item: item["net_profit"])
            insights.append(
                SellerInsight(
                    store_id=store_id,
                    priority="medium",
                    headline="Best performing SKU",
                    insight_text=(
                        f"{best_product['sku']} generated {best_product['net_profit']:.2f} net profit "
                        f"at {best_product['profit_margin']:.1f}% margin."
                    ),
                )
            )
            insights.append(
                SellerInsight(
                    store_id=store_id,
                    priority="high" if worst_product["net_profit"] < 0 else "medium",
                    headline="Worst SKU today",
                    insight_text=(
                        f"{worst_product['sku']} is at {worst_product['profit_margin']:.1f}% margin "
                        f"with {worst_product['net_profit']:.2f} net profit."
                    ),
                )
            )

        if reimbursements["summary"]["total_pending_amount"] > 0:
            insights.append(
                SellerInsight(
                    store_id=store_id,
                    priority="high",
                    headline="Reimbursement recovery",
                    insight_text=(
                        f"Amazon owes you {reimbursements['summary']['total_pending_amount']:.2f} across "
                        f"{reimbursements['summary']['open_cases']} open reimbursement cases."
                    ),
                )
            )

        if not insights:
            insights.append(
                SellerInsight(
                    store_id=store_id,
                    priority="medium",
                    headline="Daily briefing unavailable",
                    insight_text="Upload more operational data to unlock profit leak decisions.",
                )
            )

        for insight in insights[:6]:
            db.add(insight)

        db.flush()
        return db.scalars(
            select(SellerInsight)
            .where(SellerInsight.store_id == store_id)
            .where(SellerInsight.insight_type == "daily_briefing")
            .order_by(SellerInsight.created_at.desc())
        ).all()

    def get_daily_insights(self, db: Session, store_id) -> dict:
        insights = db.scalars(
            select(SellerInsight)
            .where(SellerInsight.store_id == store_id)
            .where(SellerInsight.insight_type == "daily_briefing")
            .order_by(SellerInsight.created_at.desc())
        ).all()
        products = get_product_profitability(
            db,
            store_id,
            start_date=date.fromisoformat(get_store_date_bounds(db, store_id)["default_start_date"]),
            end_date=date.fromisoformat(get_store_date_bounds(db, store_id)["default_end_date"]),
        )
        alerts = db.scalars(
            select(ProfitAlert)
            .where(ProfitAlert.store_id == store_id)
            .where(ProfitAlert.resolved.is_(False))
            .order_by(ProfitAlert.severity.desc(), ProfitAlert.created_at.desc())
        ).all()

        return {
            "biggest_profit_leak": alerts[0].message if alerts else None,
            "worst_sku_today": products[-1]["sku"] if products else None,
            "best_sku_today": products[0]["sku"] if products else None,
            "recommended_actions": [insight.headline for insight in insights[:4]],
            "insights": insights,
        }
