from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.ad import Ad
from app.models.daily_metric import DailyMetric
from app.models.integration import Integration
from app.models.order import Order
from app.models.product import Product
from app.models.settlement import Settlement
from app.models.upload import Upload


MIN_SELECTABLE_DATE = date(2024, 1, 1)

SOURCE_LABELS = {
    "orders": "Orders",
    "ads": "Ads",
    "settlement": "Settlements",
    "returns": "Returns",
    "reimbursements": "Reimbursements",
    "campaigns": "Campaigns",
    "inventory": "Inventory",
    "amazon_sync": "Amazon Sync",
}

METRIC_SOURCE_MAP = {
    "revenue": ["orders"],
    "net_profit": ["orders", "ads", "settlement"],
    "profit_margin": ["orders", "ads", "settlement"],
    "tacos": ["orders", "ads"],
    "acos": ["ads"],
    "refund_rate": ["orders"],
    "ad_spend": ["ads"],
    "roas": ["ads"],
    "avg_order_value": ["orders"],
    "orders_count": ["orders"],
    "units_sold": ["orders"],
    "ctr": ["ads"],
    "cpc": ["ads"],
    "ad_sales": ["ads"],
    "fees": ["orders"],
    "taxes": ["settlement"],
    "reimbursements": ["settlement"],
    "refunds": ["orders"],
    "cogs": ["orders"],
    "profit_per_order": ["orders", "ads", "settlement"],
}


def _decimal(value: Decimal | None) -> Decimal:
    return value or Decimal("0")


def _float(value: Decimal | None) -> float:
    return float(_decimal(value))


def _safe_divide(numerator: Decimal, denominator: Decimal, multiplier: Decimal | None = None) -> Decimal:
    if denominator == 0:
        return Decimal("0")
    result = numerator / denominator
    if multiplier is not None:
        result *= multiplier
    return result


def _percent(numerator: Decimal, denominator: Decimal) -> Decimal:
    return _safe_divide(numerator, denominator, Decimal("100"))


def _metric_value(current: Decimal, previous: Decimal) -> dict[str, float | None]:
    change_pct: float | None = None
    if previous != 0:
        change_pct = round(float(((current - previous) / abs(previous)) * Decimal("100")), 2)

    return {
        "current": round(float(current), 2),
        "previous": round(float(previous), 2),
        "change_pct": change_pct,
    }


def get_store_date_bounds(db: Session, store_id) -> dict[str, str]:
    max_daily_metric_date = db.scalar(
        select(func.max(DailyMetric.date)).where(DailyMetric.store_id == store_id)
    )
    max_order_date = db.scalar(select(func.max(Order.order_date)).where(Order.store_id == store_id))
    max_ad_date = db.scalar(select(func.max(Ad.date)).where(Ad.store_id == store_id))

    candidates = [value for value in [max_daily_metric_date, max_order_date, max_ad_date] if value]
    max_date = max(candidates) if candidates else date.today()
    default_end_date = max_date
    default_start_date = max(MIN_SELECTABLE_DATE, default_end_date - timedelta(days=29))

    return {
        "min_date": MIN_SELECTABLE_DATE.isoformat(),
        "max_date": max_date.isoformat(),
        "default_start_date": default_start_date.isoformat(),
        "default_end_date": default_end_date.isoformat(),
    }


def resolve_date_range(
    db: Session,
    store_id,
    range_value: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[date, date]:
    bounds = get_store_date_bounds(db, store_id)
    max_date = date.fromisoformat(bounds["max_date"])

    if start_date or end_date:
        if start_date is None or end_date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both start_date and end_date are required together.",
            )
        if start_date < MIN_SELECTABLE_DATE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"start_date cannot be earlier than {MIN_SELECTABLE_DATE.isoformat()}.",
            )
        if end_date > max_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"end_date cannot be later than {max_date.isoformat()}.",
            )
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date cannot be after end_date.",
            )
        return start_date, end_date

    normalized = (range_value or "30d").strip().lower()
    if not normalized.endswith("d"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Range must look like '30d' or '90d'.",
        )

    try:
        days = int(normalized[:-1])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Range must use a numeric day value.",
        ) from exc

    if days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Range must be greater than zero.",
        )

    start = max(MIN_SELECTABLE_DATE, max_date - timedelta(days=days - 1))
    return start, max_date


def recompute_daily_metrics(db: Session, store_id) -> None:
    db.flush()

    product_cogs = {
        product.sku: _decimal(product.cogs)
        for product in db.scalars(select(Product).where(Product.store_id == store_id)).all()
    }

    order_rows = db.execute(
        select(
            Order.order_date.label("metric_date"),
            Order.sku.label("sku"),
            func.count(Order.id).label("orders_count"),
            func.coalesce(func.sum(Order.units), 0).label("units_sold"),
            func.coalesce(func.sum(Order.revenue), 0).label("revenue"),
            func.coalesce(func.sum(Order.fees), 0).label("fees"),
            func.coalesce(func.sum(Order.refund), 0).label("refund"),
        )
        .where(Order.store_id == store_id)
        .group_by(Order.order_date, Order.sku)
    ).all()

    ad_rows = db.execute(
        select(
            Ad.date.label("metric_date"),
            Ad.sku.label("sku"),
            func.coalesce(func.sum(Ad.spend), 0).label("ad_spend"),
            func.coalesce(func.sum(Ad.sales), 0).label("ad_sales"),
            func.coalesce(func.sum(Ad.clicks), 0).label("clicks"),
            func.coalesce(func.sum(Ad.impressions), 0).label("impressions"),
        )
        .where(Ad.store_id == store_id)
        .group_by(Ad.date, Ad.sku)
    ).all()

    settlement_rows = db.execute(
        select(
            Settlement.settlement_date.label("metric_date"),
            func.coalesce(func.sum(Settlement.taxes), 0).label("taxes"),
            func.coalesce(func.sum(Settlement.reimbursements), 0).label("reimbursements"),
        )
        .where(Settlement.store_id == store_id)
        .group_by(Settlement.settlement_date)
    ).all()

    daily_totals: dict[date, dict[str, Decimal | int]] = defaultdict(
        lambda: {
            "revenue": Decimal("0"),
            "ad_spend": Decimal("0"),
            "ad_sales": Decimal("0"),
            "fees": Decimal("0"),
            "taxes": Decimal("0"),
            "reimbursements": Decimal("0"),
            "refund": Decimal("0"),
            "cogs": Decimal("0"),
            "orders_count": 0,
            "units_sold": 0,
            "clicks": 0,
            "impressions": 0,
        }
    )

    for row in order_rows:
        totals = daily_totals[row.metric_date]
        units_sold = int(row.units_sold or 0)
        totals["revenue"] += _decimal(row.revenue)
        totals["fees"] += _decimal(row.fees)
        totals["refund"] += _decimal(row.refund)
        totals["cogs"] += product_cogs.get(row.sku, Decimal("0")) * Decimal(units_sold)
        totals["orders_count"] += int(row.orders_count or 0)
        totals["units_sold"] += units_sold

    for row in ad_rows:
        totals = daily_totals[row.metric_date]
        totals["ad_spend"] += _decimal(row.ad_spend)
        totals["ad_sales"] += _decimal(row.ad_sales)
        totals["clicks"] += int(row.clicks or 0)
        totals["impressions"] += int(row.impressions or 0)

    for row in settlement_rows:
        totals = daily_totals[row.metric_date]
        totals["taxes"] += _decimal(row.taxes)
        totals["reimbursements"] += _decimal(row.reimbursements)

    db.execute(delete(DailyMetric).where(DailyMetric.store_id == store_id))

    for metric_date, totals in sorted(daily_totals.items()):
        revenue = totals["revenue"]
        ad_spend = totals["ad_spend"]
        ad_sales = totals["ad_sales"]
        fees = totals["fees"]
        taxes = totals["taxes"]
        reimbursements = totals["reimbursements"]
        refund = totals["refund"]
        cogs = totals["cogs"]
        net_profit = revenue - fees - taxes - refund - ad_spend - cogs + reimbursements

        db.add(
            DailyMetric(
                store_id=store_id,
                date=metric_date,
                revenue=revenue,
                ad_spend=ad_spend,
                ad_sales=ad_sales,
                fees=fees,
                taxes=taxes,
                reimbursements=reimbursements,
                refund=refund,
                cogs=cogs,
                net_profit=net_profit,
                orders_count=int(totals["orders_count"]),
                units_sold=int(totals["units_sold"]),
                clicks=int(totals["clicks"]),
                impressions=int(totals["impressions"]),
            )
        )


def _aggregate_period_metrics(db: Session, store_id, start_date: date, end_date: date) -> dict[str, Decimal]:
    row = db.execute(
        select(
            func.coalesce(func.sum(DailyMetric.revenue), 0).label("revenue"),
            func.coalesce(func.sum(DailyMetric.ad_spend), 0).label("ad_spend"),
            func.coalesce(func.sum(DailyMetric.ad_sales), 0).label("ad_sales"),
            func.coalesce(func.sum(DailyMetric.fees), 0).label("fees"),
            func.coalesce(func.sum(DailyMetric.taxes), 0).label("taxes"),
            func.coalesce(func.sum(DailyMetric.reimbursements), 0).label("reimbursements"),
            func.coalesce(func.sum(DailyMetric.refund), 0).label("refunds"),
            func.coalesce(func.sum(DailyMetric.cogs), 0).label("cogs"),
            func.coalesce(func.sum(DailyMetric.net_profit), 0).label("net_profit"),
            func.coalesce(func.sum(DailyMetric.orders_count), 0).label("orders_count"),
            func.coalesce(func.sum(DailyMetric.units_sold), 0).label("units_sold"),
            func.coalesce(func.sum(DailyMetric.clicks), 0).label("clicks"),
            func.coalesce(func.sum(DailyMetric.impressions), 0).label("impressions"),
        )
        .where(DailyMetric.store_id == store_id)
        .where(DailyMetric.date >= start_date)
        .where(DailyMetric.date <= end_date)
    ).one()

    revenue = _decimal(row.revenue)
    ad_spend = _decimal(row.ad_spend)
    ad_sales = _decimal(row.ad_sales)
    fees = _decimal(row.fees)
    taxes = _decimal(row.taxes)
    reimbursements = _decimal(row.reimbursements)
    refunds = _decimal(row.refunds)
    cogs = _decimal(row.cogs)
    net_profit = _decimal(row.net_profit)
    orders_count = Decimal(int(row.orders_count or 0))
    units_sold = Decimal(int(row.units_sold or 0))
    clicks = Decimal(int(row.clicks or 0))
    impressions = Decimal(int(row.impressions or 0))

    return {
        "revenue": revenue,
        "ad_spend": ad_spend,
        "ad_sales": ad_sales,
        "fees": fees,
        "taxes": taxes,
        "reimbursements": reimbursements,
        "refunds": refunds,
        "cogs": cogs,
        "net_profit": net_profit,
        "orders_count": orders_count,
        "units_sold": units_sold,
        "profit_margin": _percent(net_profit, revenue),
        "tacos": _percent(ad_spend, revenue),
        "acos": _percent(ad_spend, ad_sales),
        "roas": _safe_divide(ad_sales, ad_spend),
        "ctr": _percent(clicks, impressions),
        "cpc": _safe_divide(ad_spend, clicks),
        "avg_order_value": _safe_divide(revenue, orders_count),
        "refund_rate": _percent(refunds, revenue),
        "profit_per_order": _safe_divide(net_profit, orders_count),
    }


def _serialise_metric_bundle(current: dict[str, Decimal], previous: dict[str, Decimal]) -> dict[str, Any]:
    return {
        key: _metric_value(current[key], previous[key])
        for key in [
            "revenue",
            "net_profit",
            "profit_margin",
            "tacos",
            "acos",
            "refund_rate",
            "ad_spend",
            "roas",
            "avg_order_value",
            "orders_count",
            "units_sold",
            "ctr",
            "cpc",
            "ad_sales",
            "fees",
            "taxes",
            "reimbursements",
            "refunds",
            "cogs",
            "profit_per_order",
        ]
    }


def _coverage_status_label(coverage_pct: float) -> str:
    if coverage_pct >= 95:
        return "complete"
    if coverage_pct >= 40:
        return "partial"
    if coverage_pct > 0:
        return "limited"
    return "missing"


def _get_upload_data_sources(db: Session, store_id) -> list[dict[str, Any]]:
    upload_types = ["orders", "ads", "settlement", "returns", "reimbursements", "campaigns", "inventory"]
    data_sources: list[dict[str, Any]] = []
    for upload_type in upload_types:
        latest_upload_at = db.scalar(
            select(func.max(Upload.uploaded_at))
            .where(Upload.store_id == store_id)
            .where(Upload.upload_type == upload_type)
            .where(Upload.status == "completed")
        )
        data_sources.append(
            {
                "key": upload_type,
                "name": SOURCE_LABELS[upload_type],
                "active": latest_upload_at is not None,
                "status": "healthy" if latest_upload_at is not None else "waiting",
                "last_refresh_at": latest_upload_at.isoformat() if latest_upload_at else None,
            }
        )
    return data_sources


def _get_range_coverage(db: Session, store_id, start_date: date, end_date: date) -> list[dict[str, Any]]:
    expected_days = (end_date - start_date).days + 1
    source_queries = {
        "orders": (
            select(
                func.count(func.distinct(Order.order_date)).label("covered_days"),
                func.max(Order.order_date).label("latest_data_date"),
            )
            .where(Order.store_id == store_id)
            .where(Order.order_date >= start_date)
            .where(Order.order_date <= end_date)
        ),
        "ads": (
            select(
                func.count(func.distinct(Ad.date)).label("covered_days"),
                func.max(Ad.date).label("latest_data_date"),
            )
            .where(Ad.store_id == store_id)
            .where(Ad.date >= start_date)
            .where(Ad.date <= end_date)
        ),
        "settlement": (
            select(
                func.count(func.distinct(Settlement.settlement_date)).label("covered_days"),
                func.max(Settlement.settlement_date).label("latest_data_date"),
            )
            .where(Settlement.store_id == store_id)
            .where(Settlement.settlement_date >= start_date)
            .where(Settlement.settlement_date <= end_date)
        ),
    }

    coverage_rows: list[dict[str, Any]] = []
    for source_key, query in source_queries.items():
        row = db.execute(query).one()
        covered_days = int(row.covered_days or 0)
        coverage_pct = round((covered_days / expected_days) * 100, 2) if expected_days else 0.0
        coverage_rows.append(
            {
                "key": source_key,
                "label": SOURCE_LABELS[source_key],
                "covered_days": covered_days,
                "expected_days": expected_days,
                "coverage_pct": coverage_pct,
                "status": _coverage_status_label(coverage_pct),
                "latest_data_date": row.latest_data_date.isoformat() if row.latest_data_date else None,
            }
        )
    return coverage_rows


def _build_metric_trust(
    data_sources: list[dict[str, Any]],
    range_coverage: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    data_source_map = {source["key"]: source for source in data_sources}
    coverage_map = {row["key"]: row for row in range_coverage}
    trust_rows: list[dict[str, Any]] = []

    for metric_key, sources in METRIC_SOURCE_MAP.items():
        coverage_values = [coverage_map[source]["coverage_pct"] for source in sources if source in coverage_map]
        coverage_pct = round(sum(coverage_values) / len(coverage_values), 2) if coverage_values else 0.0
        freshness_candidates = [
            data_source_map[source]["last_refresh_at"]
            for source in sources
            if source in data_source_map and data_source_map[source]["last_refresh_at"]
        ]
        status = _coverage_status_label(coverage_pct)
        missing_sources = [
            SOURCE_LABELS[source]
            for source in sources
            if source in coverage_map and coverage_map[source]["coverage_pct"] == 0
        ]

        if missing_sources:
            note = f"Powered by {', '.join(SOURCE_LABELS[source] for source in sources)}. Missing {', '.join(missing_sources)} in the selected range."
        elif status == "partial":
            note = f"Powered by {', '.join(SOURCE_LABELS[source] for source in sources)} with partial date coverage."
        elif status == "limited":
            note = f"Powered by {', '.join(SOURCE_LABELS[source] for source in sources)} but only lightly covered in the selected window."
        else:
            note = f"Powered by {', '.join(SOURCE_LABELS[source] for source in sources)}."

        trust_rows.append(
            {
                "metric_key": metric_key,
                "powered_by": [SOURCE_LABELS[source] for source in sources],
                "coverage_pct": coverage_pct,
                "freshness_at": max(freshness_candidates) if freshness_candidates else None,
                "status": status,
                "note": note,
            }
        )

    return trust_rows


def get_dashboard_data_freshness(db: Session, store_id) -> dict[str, Any]:
    latest_upload_at = db.scalar(
        select(func.max(Upload.uploaded_at))
        .where(Upload.store_id == store_id)
        .where(Upload.status == "completed")
    )
    latest_sync_at = db.scalar(
        select(func.max(Integration.last_synced_at)).where(Integration.store_id == store_id)
    )

    last_refresh_candidates = [value for value in [latest_upload_at, latest_sync_at] if value]
    last_data_refresh = max(last_refresh_candidates) if last_refresh_candidates else None
    data_sources = _get_upload_data_sources(db, store_id)
    data_sources.append(
        {
            "key": "amazon_sync",
            "name": SOURCE_LABELS["amazon_sync"],
            "active": latest_sync_at is not None,
            "status": "healthy" if latest_sync_at is not None else "waiting",
            "last_refresh_at": latest_sync_at.isoformat() if latest_sync_at else None,
        }
    )

    return {
        "last_data_refresh": last_data_refresh.isoformat() if last_data_refresh else None,
        "data_sources": data_sources,
    }


def get_dashboard_summary(
    db: Session,
    store_id,
    range_value: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    start_date, end_date = resolve_date_range(db, store_id, range_value, start_date, end_date)
    period_days = (end_date - start_date).days + 1
    previous_end_date = start_date - timedelta(days=1)
    previous_start_date = previous_end_date - timedelta(days=period_days - 1)

    current_metrics = _aggregate_period_metrics(db, store_id, start_date, end_date)
    previous_metrics = _aggregate_period_metrics(db, store_id, previous_start_date, previous_end_date)
    freshness = get_dashboard_data_freshness(db, store_id)
    range_coverage = _get_range_coverage(db, store_id, start_date, end_date)
    metric_trust = _build_metric_trust(freshness["data_sources"], range_coverage)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "previous_start_date": previous_start_date.isoformat(),
        "previous_end_date": previous_end_date.isoformat(),
        "metrics": _serialise_metric_bundle(current_metrics, previous_metrics),
        **freshness,
        "range_coverage": range_coverage,
        "metric_trust": metric_trust,
    }


def get_dashboard_trends(
    db: Session,
    store_id,
    range_value: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    start_date, end_date = resolve_date_range(db, store_id, range_value, start_date, end_date)

    metric_rows = {
        metric.date: metric
        for metric in db.scalars(
            select(DailyMetric)
            .where(DailyMetric.store_id == store_id)
            .where(DailyMetric.date >= start_date)
            .where(DailyMetric.date <= end_date)
            .order_by(DailyMetric.date.asc())
        ).all()
    }

    trend_points: list[dict[str, Any]] = []
    cursor = start_date
    while cursor <= end_date:
        metric = metric_rows.get(cursor)
        revenue = _decimal(metric.revenue if metric else None)
        ad_sales = _decimal(metric.ad_sales if metric else None)
        ad_spend = _decimal(metric.ad_spend if metric else None)
        fees = _decimal(metric.fees if metric else None)
        taxes = _decimal(metric.taxes if metric else None)
        reimbursements = _decimal(metric.reimbursements if metric else None)
        refund = _decimal(metric.refund if metric else None)
        cogs = _decimal(metric.cogs if metric else None)
        net_profit = _decimal(metric.net_profit if metric else None)
        orders_count = int(metric.orders_count if metric else 0)
        units_sold = int(metric.units_sold if metric else 0)
        clicks = int(metric.clicks if metric else 0)
        impressions = int(metric.impressions if metric else 0)

        trend_points.append(
            {
                "date": cursor.isoformat(),
                "revenue": round(float(revenue), 2),
                "ad_sales": round(float(ad_sales), 2),
                "ad_spend": round(float(ad_spend), 2),
                "fees": round(float(fees), 2),
                "taxes": round(float(taxes), 2),
                "reimbursements": round(float(reimbursements), 2),
                "refund": round(float(refund), 2),
                "cogs": round(float(cogs), 2),
                "net_profit": round(float(net_profit), 2),
                "profit_margin": round(float(_percent(net_profit, revenue)), 2),
                "tacos": round(float(_percent(ad_spend, revenue)), 2),
                "acos": round(float(_percent(ad_spend, ad_sales)), 2),
                "roas": round(float(_safe_divide(ad_sales, ad_spend)), 2),
                "refund_rate": round(float(_percent(refund, revenue)), 2),
                "orders_count": orders_count,
                "units_sold": units_sold,
                "clicks": clicks,
                "impressions": impressions,
                "ctr": round(float(_percent(Decimal(clicks), Decimal(impressions))), 2),
                "cpc": round(float(_safe_divide(ad_spend, Decimal(clicks))), 2),
                "avg_order_value": round(
                    float(_safe_divide(revenue, Decimal(orders_count))), 2
                ),
            }
        )
        cursor += timedelta(days=1)

    return trend_points


def get_product_profitability(
    db: Session,
    store_id,
    range_value: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    start_date, end_date = resolve_date_range(db, store_id, range_value, start_date, end_date)

    products = db.scalars(select(Product).where(Product.store_id == store_id)).all()
    product_map = {product.sku: product for product in products}

    order_rows = db.execute(
        select(
            Order.sku.label("sku"),
            func.coalesce(func.sum(Order.units), 0).label("units_sold"),
            func.coalesce(func.sum(Order.revenue), 0).label("revenue"),
            func.coalesce(func.sum(Order.fees), 0).label("fees"),
            func.coalesce(func.sum(Order.refund), 0).label("refund"),
            func.coalesce(func.count(Order.id), 0).label("orders_count"),
        )
        .where(Order.store_id == store_id)
        .where(Order.order_date >= start_date)
        .where(Order.order_date <= end_date)
        .group_by(Order.sku)
    ).all()

    ad_rows = db.execute(
        select(
            Ad.sku.label("sku"),
            func.coalesce(func.sum(Ad.spend), 0).label("ad_spend"),
            func.coalesce(func.sum(Ad.sales), 0).label("ad_sales"),
        )
        .where(Ad.store_id == store_id)
        .where(Ad.date >= start_date)
        .where(Ad.date <= end_date)
        .group_by(Ad.sku)
    ).all()

    metrics_by_sku: dict[str, dict[str, Decimal | int | str | None]] = {}

    def get_bucket(sku: str) -> dict[str, Decimal | int | str | None]:
        if sku not in metrics_by_sku:
            product = product_map.get(sku)
            metrics_by_sku[sku] = {
                "sku": sku,
                "name": product.name if product else None,
                "cogs_per_unit": _decimal(product.cogs) if product else Decimal("0"),
                "units_sold": 0,
                "orders_count": 0,
                "revenue": Decimal("0"),
                "ad_spend": Decimal("0"),
                "ad_sales": Decimal("0"),
                "fees": Decimal("0"),
                "refund": Decimal("0"),
            }
        return metrics_by_sku[sku]

    for row in order_rows:
        bucket = get_bucket(row.sku)
        bucket["units_sold"] = int(row.units_sold or 0)
        bucket["orders_count"] = int(row.orders_count or 0)
        bucket["revenue"] = _decimal(row.revenue)
        bucket["fees"] = _decimal(row.fees)
        bucket["refund"] = _decimal(row.refund)

    for row in ad_rows:
        bucket = get_bucket(row.sku)
        bucket["ad_spend"] = _decimal(row.ad_spend)
        bucket["ad_sales"] = _decimal(row.ad_sales)

    results: list[dict[str, Any]] = []
    for sku, bucket in metrics_by_sku.items():
        units_sold = int(bucket["units_sold"])
        revenue = _decimal(bucket["revenue"])
        fees = _decimal(bucket["fees"])
        refund = _decimal(bucket["refund"])
        ad_spend = _decimal(bucket["ad_spend"])
        ad_sales = _decimal(bucket["ad_sales"])
        cogs_per_unit = _decimal(bucket["cogs_per_unit"])
        total_cogs = cogs_per_unit * Decimal(units_sold)
        net_profit = revenue - fees - refund - ad_spend - total_cogs
        profit_margin = _percent(net_profit, revenue)
        refund_rate = _percent(refund, revenue)
        profit_per_unit = _safe_divide(net_profit, Decimal(units_sold))

        results.append(
            {
                "sku": sku,
                "name": bucket["name"],
                "cogs_per_unit": round(float(cogs_per_unit), 2),
                "units_sold": units_sold,
                "revenue": round(float(revenue), 2),
                "ad_spend": round(float(ad_spend), 2),
                "ad_sales": round(float(ad_sales), 2),
                "fees": round(float(fees), 2),
                "refund": round(float(refund), 2),
                "cogs": round(float(total_cogs), 2),
                "net_profit": round(float(net_profit), 2),
                "profit_margin": round(float(profit_margin), 2),
                "refund_rate": round(float(refund_rate), 2),
                "acos": round(float(_percent(ad_spend, ad_sales)), 2),
                "roas": round(float(_safe_divide(ad_sales, ad_spend)), 2),
                "profit_per_unit": round(float(profit_per_unit), 2),
            }
        )

    results.sort(key=lambda item: (item["net_profit"], item["sku"]), reverse=True)
    return results
