from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import utcnow
from app.models.inventory_aging import InventoryAging
from app.models.profit_alert import ProfitAlert
from app.services.metrics_service import MIN_SELECTABLE_DATE, get_product_profitability, get_store_date_bounds


LOOKBACK_DAYS = 7


@dataclass(slots=True)
class SkuPeriodSnapshot:
    sku: str
    name: str | None
    current_revenue: Decimal
    previous_revenue: Decimal
    current_ad_spend: Decimal
    previous_ad_spend: Decimal
    current_fees: Decimal
    previous_fees: Decimal
    current_refund: Decimal
    previous_refund: Decimal
    current_units_sold: int
    previous_units_sold: int
    current_net_profit: Decimal
    previous_net_profit: Decimal
    current_profit_margin: Decimal
    previous_profit_margin: Decimal
    current_return_rate: Decimal
    previous_return_rate: Decimal
    current_acos: Decimal
    previous_acos: Decimal


@dataclass(slots=True)
class AlertCandidate:
    sku: str | None
    alert_type: str
    severity: str
    title: str
    message: str
    metric_value: Decimal | None
    alert_key: str


def _decimal(value: float | int | Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _percent_change(current: Decimal, previous: Decimal) -> Decimal:
    if previous == 0:
        return Decimal("0")
    return ((current - previous) / abs(previous)) * Decimal("100")


def _format_pct(value: Decimal) -> str:
    return f"{float(value):.1f}%"


def detect_margin_drop(snapshot: SkuPeriodSnapshot) -> AlertCandidate | None:
    drop = snapshot.current_profit_margin - snapshot.previous_profit_margin
    if snapshot.previous_revenue < Decimal("1000") or snapshot.previous_profit_margin <= Decimal("0"):
        return None
    if drop > Decimal("-20"):
        return None

    severity = "critical" if drop <= Decimal("-35") else "high"
    return AlertCandidate(
        sku=snapshot.sku,
        alert_type="margin_drop",
        severity=severity,
        title=f"Margin dropped for {snapshot.sku}",
        message=(
            f"{snapshot.sku} margin moved from {_format_pct(snapshot.previous_profit_margin)} "
            f"to {_format_pct(snapshot.current_profit_margin)} over the last {LOOKBACK_DAYS} days."
        ),
        metric_value=snapshot.current_profit_margin,
        alert_key=f"margin_drop:{snapshot.sku}",
    )


def detect_ad_spend_waste(snapshot: SkuPeriodSnapshot) -> AlertCandidate | None:
    if snapshot.previous_ad_spend <= 0 or snapshot.current_ad_spend <= 0:
        return None

    ad_spend_change = _percent_change(snapshot.current_ad_spend, snapshot.previous_ad_spend)
    revenue_change = _percent_change(snapshot.current_revenue, snapshot.previous_revenue)

    if ad_spend_change < Decimal("30"):
        return None
    if abs(revenue_change) > Decimal("10"):
        return None

    severity = "critical" if ad_spend_change >= Decimal("60") else "high"
    return AlertCandidate(
        sku=snapshot.sku,
        alert_type="ad_waste",
        severity=severity,
        title=f"Ad spend up without sales lift for {snapshot.sku}",
        message=(
            f"Ad spend increased {_format_pct(ad_spend_change)} while sales changed only "
            f"{_format_pct(revenue_change)} for {snapshot.sku}."
        ),
        metric_value=snapshot.current_ad_spend,
        alert_key=f"ad_waste:{snapshot.sku}",
    )


def detect_return_spike(snapshot: SkuPeriodSnapshot) -> AlertCandidate | None:
    increase = snapshot.current_return_rate - snapshot.previous_return_rate
    if snapshot.current_revenue < Decimal("500"):
        return None
    if snapshot.current_return_rate < Decimal("5"):
        return None
    if increase < Decimal("3.5"):
        return None

    severity = "critical" if snapshot.current_return_rate >= Decimal("12") else "high"
    return AlertCandidate(
        sku=snapshot.sku,
        alert_type="return_spike",
        severity=severity,
        title=f"Return pressure rising for {snapshot.sku}",
        message=(
            f"Refund rate rose from {_format_pct(snapshot.previous_return_rate)} to "
            f"{_format_pct(snapshot.current_return_rate)} for {snapshot.sku}."
        ),
        metric_value=snapshot.current_return_rate,
        alert_key=f"return_spike:{snapshot.sku}",
    )


def detect_fee_change(snapshot: SkuPeriodSnapshot) -> AlertCandidate | None:
    if snapshot.current_revenue <= 0 or snapshot.previous_revenue <= 0:
        return None
    current_fee_rate = (snapshot.current_fees / snapshot.current_revenue) * Decimal("100")
    previous_fee_rate = (snapshot.previous_fees / snapshot.previous_revenue) * Decimal("100")
    increase = current_fee_rate - previous_fee_rate
    if increase < Decimal("4"):
        return None

    severity = "high" if increase < Decimal("7") else "critical"
    return AlertCandidate(
        sku=snapshot.sku,
        alert_type="unexpected_fee",
        severity=severity,
        title=f"Fee burden jumped for {snapshot.sku}",
        message=(
            f"Fee rate increased from {_format_pct(previous_fee_rate)} to "
            f"{_format_pct(current_fee_rate)} for {snapshot.sku}."
        ),
        metric_value=current_fee_rate,
        alert_key=f"unexpected_fee:{snapshot.sku}",
    )


class ProfitAnalysisService:
    managed_alert_types = {
        "margin_drop",
        "ad_waste",
        "return_spike",
        "unexpected_fee",
        "storage_risk",
    }

    def _resolve_lookback_window(self, db: Session, store_id) -> tuple[date, date, date, date]:
        bounds = get_store_date_bounds(db, store_id)
        min_date = date.fromisoformat(bounds["min_date"]) if bounds["min_date"] else MIN_SELECTABLE_DATE
        end_date = date.fromisoformat(bounds["max_date"])
        start_date = max(min_date, end_date - timedelta(days=LOOKBACK_DAYS - 1))
        previous_end = start_date - timedelta(days=1)
        previous_start = max(min_date, previous_end - timedelta(days=LOOKBACK_DAYS - 1))
        if previous_end < min_date:
            previous_end = min_date
        return start_date, end_date, previous_start, previous_end

    def _build_snapshots(self, db: Session, store_id) -> list[SkuPeriodSnapshot]:
        start_date, end_date, previous_start, previous_end = self._resolve_lookback_window(db, store_id)
        current_rows = {
            row["sku"]: row
            for row in get_product_profitability(db, store_id, start_date=start_date, end_date=end_date)
        }
        previous_rows = {
            row["sku"]: row
            for row in get_product_profitability(
                db,
                store_id,
                start_date=previous_start,
                end_date=previous_end,
            )
        }

        snapshots: list[SkuPeriodSnapshot] = []
        for sku in sorted(set(current_rows) | set(previous_rows)):
            current = current_rows.get(sku, {})
            previous = previous_rows.get(sku, {})
            snapshots.append(
                SkuPeriodSnapshot(
                    sku=sku,
                    name=current.get("name") or previous.get("name"),
                    current_revenue=_decimal(current.get("revenue")),
                    previous_revenue=_decimal(previous.get("revenue")),
                    current_ad_spend=_decimal(current.get("ad_spend")),
                    previous_ad_spend=_decimal(previous.get("ad_spend")),
                    current_fees=_decimal(current.get("fees")),
                    previous_fees=_decimal(previous.get("fees")),
                    current_refund=_decimal(current.get("refund")),
                    previous_refund=_decimal(previous.get("refund")),
                    current_units_sold=int(current.get("units_sold", 0) or 0),
                    previous_units_sold=int(previous.get("units_sold", 0) or 0),
                    current_net_profit=_decimal(current.get("net_profit")),
                    previous_net_profit=_decimal(previous.get("net_profit")),
                    current_profit_margin=_decimal(current.get("profit_margin")),
                    previous_profit_margin=_decimal(previous.get("profit_margin")),
                    current_return_rate=_decimal(current.get("refund_rate")),
                    previous_return_rate=_decimal(previous.get("refund_rate")),
                    current_acos=_decimal(current.get("acos")),
                    previous_acos=_decimal(previous.get("acos")),
                )
            )
        return snapshots

    def _storage_alerts(self, db: Session, store_id) -> list[AlertCandidate]:
        latest_snapshot = db.scalar(
            select(InventoryAging.snapshot_date)
            .where(InventoryAging.store_id == store_id)
            .order_by(InventoryAging.snapshot_date.desc())
            .limit(1)
        )
        if latest_snapshot is None:
            return []

        rows = db.scalars(
            select(InventoryAging)
            .where(InventoryAging.store_id == store_id)
            .where(InventoryAging.snapshot_date == latest_snapshot)
            .where(InventoryAging.warning_level.in_(["warning", "critical"]))
            .order_by(InventoryAging.days_in_storage.desc())
        ).all()

        alerts: list[AlertCandidate] = []
        for row in rows[:10]:
            alerts.append(
                AlertCandidate(
                    sku=row.sku,
                    alert_type="storage_risk",
                    severity=row.warning_level if row.warning_level != "warning" else "medium",
                    title=f"Slow-moving inventory building on {row.sku}",
                    message=(
                        f"{row.sku} has {row.quantity} units sitting for {row.days_in_storage} days. "
                        "Consider slowing restocks or liquidating inventory."
                    ),
                    metric_value=row.monthly_storage_fee,
                    alert_key=f"storage_risk:{row.sku}",
                )
            )
        return alerts

    def _generate_candidates(self, db: Session, store_id) -> list[AlertCandidate]:
        candidates: list[AlertCandidate] = []
        for snapshot in self._build_snapshots(db, store_id):
            for detector in (
                detect_margin_drop,
                detect_ad_spend_waste,
                detect_return_spike,
                detect_fee_change,
            ):
                candidate = detector(snapshot)
                if candidate is not None:
                    candidates.append(candidate)
        candidates.extend(self._storage_alerts(db, store_id))
        return candidates

    def refresh_alerts(self, db: Session, store_id) -> list[ProfitAlert]:
        candidates = self._generate_candidates(db, store_id)
        candidate_map = {candidate.alert_key: candidate for candidate in candidates}
        existing_alerts = db.scalars(
            select(ProfitAlert).where(ProfitAlert.store_id == store_id)
        ).all()
        existing_by_key = {alert.alert_key: alert for alert in existing_alerts}
        now = utcnow()

        for alert_key, candidate in candidate_map.items():
            alert = existing_by_key.get(alert_key)
            if alert is None:
                db.add(
                    ProfitAlert(
                        store_id=store_id,
                        sku=candidate.sku,
                        alert_key=candidate.alert_key,
                        alert_type=candidate.alert_type,
                        severity=candidate.severity,
                        title=candidate.title,
                        message=candidate.message,
                        metric_value=candidate.metric_value,
                        created_at=now,
                        resolved=False,
                    )
                )
                continue

            alert.sku = candidate.sku
            alert.alert_type = candidate.alert_type
            alert.severity = candidate.severity
            alert.title = candidate.title
            alert.message = candidate.message
            alert.metric_value = candidate.metric_value
            alert.created_at = now
            alert.resolved = False
            alert.resolved_at = None

        for alert in existing_alerts:
            if alert.alert_type not in self.managed_alert_types:
                continue
            if alert.alert_key in candidate_map:
                continue
            if not alert.resolved:
                alert.resolved = True
                alert.resolved_at = now

        db.flush()
        return db.scalars(
            select(ProfitAlert)
            .where(ProfitAlert.store_id == store_id)
            .order_by(ProfitAlert.resolved.asc(), ProfitAlert.created_at.desc())
        ).all()

    def get_profit_alerts(self, db: Session, store_id, include_resolved: bool = False) -> dict:
        query = (
            select(ProfitAlert)
            .where(ProfitAlert.store_id == store_id)
            .order_by(ProfitAlert.resolved.asc(), ProfitAlert.created_at.desc())
        )
        if not include_resolved:
            query = query.where(ProfitAlert.resolved.is_(False))
        alerts = db.scalars(query).all()

        summary = {
            "total_open": sum(0 if alert.resolved else 1 for alert in alerts),
            "high_priority": sum(
                1 for alert in alerts if not alert.resolved and alert.severity in {"high", "critical"}
            ),
            "margin_drop": sum(
                1 for alert in alerts if not alert.resolved and alert.alert_type == "margin_drop"
            ),
            "unexpected_fees": sum(
                1 for alert in alerts if not alert.resolved and alert.alert_type == "unexpected_fee"
            ),
            "ad_waste": sum(
                1 for alert in alerts if not alert.resolved and alert.alert_type == "ad_waste"
            ),
            "return_spike": sum(
                1 for alert in alerts if not alert.resolved and alert.alert_type == "return_spike"
            ),
            "storage_risk": sum(
                1 for alert in alerts if not alert.resolved and alert.alert_type == "storage_risk"
            ),
        }
        return {"summary": summary, "alerts": alerts}

    def resolve_alert(self, db: Session, store_id, alert_id) -> ProfitAlert | None:
        alert = db.scalar(
            select(ProfitAlert)
            .where(ProfitAlert.store_id == store_id)
            .where(ProfitAlert.id == alert_id)
            .limit(1)
        )
        if alert is None:
            return None
        alert.resolved = True
        alert.resolved_at = utcnow()
        db.flush()
        return alert
