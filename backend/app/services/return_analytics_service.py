from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.return_analytics import ReturnAnalytics
from app.services.metrics_service import resolve_date_range


def _decimal(value: Decimal | None) -> Decimal:
    return value or Decimal("0")


class ReturnAnalyticsService:
    def get_return_analysis(
        self,
        db: Session,
        store_id,
        range_value: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        start_date, end_date = resolve_date_range(db, store_id, range_value, start_date, end_date)

        variant_rows = db.execute(
            select(
                ReturnAnalytics.sku,
                ReturnAnalytics.variant,
                func.coalesce(func.sum(ReturnAnalytics.returned_units), 0).label("returned_units"),
                func.coalesce(func.sum(ReturnAnalytics.refund_amount), 0).label("refund_cost"),
            )
            .where(ReturnAnalytics.store_id == store_id)
            .where(ReturnAnalytics.return_date >= start_date)
            .where(ReturnAnalytics.return_date <= end_date)
            .group_by(ReturnAnalytics.sku, ReturnAnalytics.variant)
        ).all()
        units_by_sku = {
            row.sku: int(row.units_sold or 0)
            for row in db.execute(
                select(
                    Order.sku,
                    func.coalesce(func.sum(Order.units), 0).label("units_sold"),
                )
                .where(Order.store_id == store_id)
                .where(Order.order_date >= start_date)
                .where(Order.order_date <= end_date)
                .group_by(Order.sku)
            ).all()
        }

        reasons: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {"occurrences": 0, "refund_cost": Decimal("0")}
        )
        for row in db.execute(
            select(
                ReturnAnalytics.return_reason,
                func.coalesce(func.count(ReturnAnalytics.id), 0).label("occurrences"),
                func.coalesce(func.sum(ReturnAnalytics.refund_amount), 0).label("refund_cost"),
            )
            .where(ReturnAnalytics.store_id == store_id)
            .where(ReturnAnalytics.return_date >= start_date)
            .where(ReturnAnalytics.return_date <= end_date)
            .group_by(ReturnAnalytics.return_reason)
        ).all():
            key = row.return_reason or "Unknown"
            reasons[key]["occurrences"] = int(row.occurrences or 0)
            reasons[key]["refund_cost"] = _decimal(row.refund_cost)

        worst_variants: list[dict] = []
        for row in variant_rows:
            sold_units = units_by_sku.get(row.sku, 0)
            returned_units = int(row.returned_units or 0)
            denominator = max(sold_units, returned_units, 1)
            refund_cost = _decimal(row.refund_cost)
            top_reason_row = db.execute(
                select(
                    ReturnAnalytics.return_reason,
                    func.count(ReturnAnalytics.id).label("occurrences"),
                )
                .where(ReturnAnalytics.store_id == store_id)
                .where(ReturnAnalytics.sku == row.sku)
                .where(ReturnAnalytics.variant == row.variant)
                .where(ReturnAnalytics.return_date >= start_date)
                .where(ReturnAnalytics.return_date <= end_date)
                .group_by(ReturnAnalytics.return_reason)
                .order_by(func.count(ReturnAnalytics.id).desc())
            ).first()
            worst_variants.append(
                {
                    "sku": row.sku,
                    "variant": row.variant or row.sku,
                    "return_rate": round((returned_units / denominator) * 100, 2),
                    "refund_cost": round(float(refund_cost), 2),
                    "return_units": returned_units,
                    "top_reason": top_reason_row.return_reason if top_reason_row else None,
                }
            )

        worst_variants.sort(key=lambda item: (item["return_rate"], item["refund_cost"]), reverse=True)
        top_return_reasons = [
            {
                "reason": reason,
                "occurrences": int(values["occurrences"]),
                "refund_cost": round(float(values["refund_cost"]), 2),
            }
            for reason, values in sorted(
                reasons.items(),
                key=lambda item: (item[1]["occurrences"], item[1]["refund_cost"]),
                reverse=True,
            )[:5]
        ]

        summary_text = (
            f"{worst_variants[0]['variant']} is the riskiest variant right now."
            if worst_variants
            else "No variant-level return data has been recorded yet."
        )
        return {
            "worst_variants": worst_variants[:10],
            "top_return_reasons": top_return_reasons,
            "summary_text": summary_text,
        }
