from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.inventory_aging import InventoryAging


def _warning_level(days_in_storage: int) -> str:
    if days_in_storage >= 120:
        return "critical"
    if days_in_storage >= 60:
        return "warning"
    return "normal"


def _recommended_action(days_in_storage: int) -> str:
    if days_in_storage >= 120:
        return "Liquidate inventory and stop restocking."
    if days_in_storage >= 60:
        return "Pause restocking and review sell-through."
    return "Healthy inventory cadence."


class StorageAnalysisService:
    def refresh_inventory_aging(self, db: Session, store_id) -> list[InventoryAging]:
        rows = db.scalars(
            select(Inventory)
            .where(Inventory.store_id == store_id)
            .order_by(Inventory.sku.asc(), Inventory.snapshot_date.asc())
        ).all()

        db.execute(delete(InventoryAging).where(InventoryAging.store_id == store_id))
        if not rows:
            db.flush()
            return []

        history: dict[str, list[Inventory]] = defaultdict(list)
        for row in rows:
            history[row.sku].append(row)

        materialized: list[InventoryAging] = []
        for sku, sku_rows in history.items():
            first_seen = sku_rows[0].snapshot_date
            latest = sku_rows[-1]
            total_quantity = latest.available_units + latest.reserved_units + latest.inbound_units
            days_in_storage = (
                latest.days_in_storage
                if latest.days_in_storage is not None
                else max((latest.snapshot_date - first_seen).days, 0)
            )
            warning_level = _warning_level(days_in_storage)
            aging = InventoryAging(
                store_id=store_id,
                sku=sku,
                quantity=total_quantity,
                days_in_storage=days_in_storage,
                monthly_storage_fee=latest.monthly_storage_fee or Decimal("0"),
                snapshot_date=latest.snapshot_date,
                warning_level=warning_level,
            )
            db.add(aging)
            materialized.append(aging)

        db.flush()
        return materialized

    def get_storage_analysis(self, db: Session, store_id) -> dict:
        rows = db.scalars(
            select(InventoryAging)
            .where(InventoryAging.store_id == store_id)
            .order_by(InventoryAging.days_in_storage.desc(), InventoryAging.quantity.desc())
        ).all()
        slow_moving_inventory = [
            {
                "sku": row.sku,
                "quantity": row.quantity,
                "days_in_storage": row.days_in_storage,
                "monthly_storage_fee": float(row.monthly_storage_fee),
                "warning_level": row.warning_level,
                "recommended_action": _recommended_action(row.days_in_storage),
            }
            for row in rows
            if row.warning_level != "normal"
        ]

        summary_text = (
            f"{len(slow_moving_inventory)} SKUs need storage attention."
            if slow_moving_inventory
            else "No storage risk detected from current inventory snapshots."
        )
        return {
            "summary_text": summary_text,
            "slow_moving_inventory": slow_moving_inventory,
        }
