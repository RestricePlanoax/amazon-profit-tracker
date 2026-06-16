from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ad import Ad
from app.models.ad_campaign_metric import AdCampaignMetric
from app.models.order import Order
from app.services.metrics_service import resolve_date_range


def _decimal(value: Decimal | None) -> Decimal:
    return value or Decimal("0")


class AdAnalyticsService:
    def get_ad_analysis(
        self,
        db: Session,
        store_id,
        range_value: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        start_date, end_date = resolve_date_range(db, store_id, range_value, start_date, end_date)
        rows = db.scalars(
            select(AdCampaignMetric)
            .where(AdCampaignMetric.store_id == store_id)
            .where(AdCampaignMetric.metric_date >= start_date)
            .where(AdCampaignMetric.metric_date <= end_date)
            .order_by(AdCampaignMetric.metric_date.desc())
        ).all()

        if rows:
            return self._campaign_metric_response(rows)
        return self._fallback_sku_response(db, store_id, start_date, end_date)

    def _campaign_metric_response(self, rows: list[AdCampaignMetric]) -> dict:
        grouped: dict[tuple[str, str], dict] = {}
        for row in rows:
            key = (row.campaign_id, row.sku)
            bucket = grouped.setdefault(
                key,
                {
                    "campaign_id": row.campaign_id,
                    "campaign_name": row.campaign_name or row.campaign_id,
                    "sku": row.sku,
                    "daily_spend": Decimal("0"),
                    "clicks": 0,
                    "orders": 0,
                    "acos_total": Decimal("0"),
                    "roas_total": Decimal("0"),
                    "conversion_total": Decimal("0"),
                    "days": 0,
                },
            )
            bucket["daily_spend"] += _decimal(row.daily_spend)
            bucket["clicks"] += row.clicks
            bucket["orders"] += row.orders
            bucket["acos_total"] += _decimal(row.acos)
            bucket["roas_total"] += _decimal(row.roas)
            bucket["conversion_total"] += _decimal(row.conversion_rate)
            bucket["days"] += 1

        campaigns: list[dict] = []
        for bucket in grouped.values():
            days = max(bucket["days"], 1)
            avg_spend = bucket["daily_spend"] / Decimal(days)
            avg_acos = bucket["acos_total"] / Decimal(days)
            avg_roas = bucket["roas_total"] / Decimal(days)
            avg_conversion = bucket["conversion_total"] / Decimal(days)
            waste_flag = avg_spend >= Decimal("500") and (avg_roas < Decimal("1.8") or avg_conversion < Decimal("5"))
            campaigns.append(
                {
                    "campaign_id": bucket["campaign_id"],
                    "campaign_name": bucket["campaign_name"],
                    "sku": bucket["sku"],
                    "daily_spend": round(float(avg_spend), 2),
                    "clicks": bucket["clicks"],
                    "orders": bucket["orders"],
                    "acos": round(float(avg_acos), 2),
                    "roas": round(float(avg_roas), 2),
                    "conversion_rate": round(float(avg_conversion), 2),
                    "waste_flag": waste_flag,
                }
            )

        campaigns.sort(key=lambda item: (item["waste_flag"], item["daily_spend"], -item["roas"]), reverse=True)
        return {
            "summary_text": (
                f"{sum(1 for row in campaigns if row['waste_flag'])} campaigns are burning spend."
                if campaigns
                else "No campaign metrics available."
            ),
            "worst_campaigns": campaigns[:10],
        }

    def _fallback_sku_response(self, db: Session, store_id, start_date: date, end_date: date) -> dict:
        ad_rows = db.execute(
            select(
                Ad.sku,
                func.coalesce(func.sum(Ad.spend), 0).label("spend"),
                func.coalesce(func.sum(Ad.sales), 0).label("sales"),
                func.coalesce(func.sum(Ad.clicks), 0).label("clicks"),
            )
            .where(Ad.store_id == store_id)
            .where(Ad.date >= start_date)
            .where(Ad.date <= end_date)
            .group_by(Ad.sku)
        ).all()
        order_counts = {
            row.sku: int(row.orders_count or 0)
            for row in db.execute(
                select(Order.sku, func.coalesce(func.count(Order.id), 0).label("orders_count"))
                .where(Order.store_id == store_id)
                .where(Order.order_date >= start_date)
                .where(Order.order_date <= end_date)
                .group_by(Order.sku)
            ).all()
        }

        period_days = max((end_date - start_date).days + 1, 1)
        campaigns = []
        for row in ad_rows:
            spend = _decimal(row.spend)
            sales = _decimal(row.sales)
            clicks = int(row.clicks or 0)
            orders = order_counts.get(row.sku, 0)
            conversion = (Decimal(orders) / Decimal(clicks) * Decimal("100")) if clicks else Decimal("0")
            acos = (spend / sales * Decimal("100")) if sales else Decimal("0")
            roas = (sales / spend) if spend else Decimal("0")
            daily_spend = spend / Decimal(period_days)
            waste_flag = daily_spend >= Decimal("250") and (roas < Decimal("1.8") or conversion < Decimal("5"))
            campaigns.append(
                {
                    "campaign_id": f"SKU::{row.sku}",
                    "campaign_name": f"{row.sku} SKU aggregate",
                    "sku": row.sku,
                    "daily_spend": round(float(daily_spend), 2),
                    "clicks": clicks,
                    "orders": orders,
                    "acos": round(float(acos), 2),
                    "roas": round(float(roas), 2),
                    "conversion_rate": round(float(conversion), 2),
                    "waste_flag": waste_flag,
                }
            )

        campaigns.sort(key=lambda item: (item["waste_flag"], item["daily_spend"], -item["roas"]), reverse=True)
        return {
            "summary_text": (
                f"{sum(1 for row in campaigns if row['waste_flag'])} SKU ad buckets look wasteful."
                if campaigns
                else "No ad data available yet."
            ),
            "worst_campaigns": campaigns[:10],
        }
