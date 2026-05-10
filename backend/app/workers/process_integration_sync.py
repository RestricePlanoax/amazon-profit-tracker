from __future__ import annotations

import time
import uuid
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import delete, select

from app.core.database import SessionLocal, utcnow
from app.models.ad import Ad
from app.models.integration import Integration
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.product import Product
from app.models.settlement import Settlement
from app.models.sync_job import SyncJob
from app.services.metrics_service import recompute_daily_metrics


SYNC_PRODUCT_BLUEPRINTS = [
    {
        "sku": "SYNC-CORE-001",
        "name": "Launch Bottle 1L",
        "cogs": Decimal("320.00"),
        "unit_price": Decimal("1499.00"),
        "ad_ratio": Decimal("0.13"),
    },
    {
        "sku": "SYNC-CORE-002",
        "name": "Travel Flask 750ml",
        "cogs": Decimal("410.00"),
        "unit_price": Decimal("1899.00"),
        "ad_ratio": Decimal("0.11"),
    },
    {
        "sku": "SYNC-CORE-003",
        "name": "Desk Tumbler 600ml",
        "cogs": Decimal("260.00"),
        "unit_price": Decimal("999.00"),
        "ad_ratio": Decimal("0.16"),
    },
]


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _set_job_progress(job: SyncJob, progress_percent: int, rows_processed: int | None = None) -> None:
    job.progress_percent = progress_percent
    if rows_processed is not None:
        job.rows_processed = rows_processed


def _ensure_products(db, store_id: uuid.UUID, region_label: str) -> list[dict[str, Decimal | str]]:
    products = []

    for blueprint in SYNC_PRODUCT_BLUEPRINTS:
        sku = str(blueprint["sku"])
        product = db.scalar(
            select(Product).where(Product.store_id == store_id, Product.sku == sku)
        )

        if product is None:
            product = Product(
                store_id=store_id,
                sku=sku,
                name=f"{blueprint['name']} ({region_label})",
                cogs=blueprint["cogs"],
            )
            db.add(product)
        else:
            product.name = f"{blueprint['name']} ({region_label})"
            product.cogs = blueprint["cogs"]

        products.append(blueprint)

    db.flush()
    return products


def _clear_previous_sync_data(db, store_id: uuid.UUID, skus: list[str]) -> None:
    db.execute(
        delete(Order)
        .where(Order.store_id == store_id)
        .where(Order.sku.in_(skus))
        .where(Order.order_id.like("SYNC-%"))
    )
    db.execute(delete(Ad).where(Ad.store_id == store_id).where(Ad.sku.in_(skus)))
    db.execute(
        delete(Settlement)
        .where(Settlement.store_id == store_id)
        .where(Settlement.settlement_id.like("SYNC-%"))
    )
    db.execute(delete(Inventory).where(Inventory.store_id == store_id).where(Inventory.sku.in_(skus)))


def _seed_sync_data(db, store_id: uuid.UUID, region: str | None) -> int:
    region_label = (region or "amazon").upper()
    products = _ensure_products(db, store_id, region_label)
    skus = [str(product["sku"]) for product in products]
    _clear_previous_sync_data(db, store_id, skus)

    rows_processed = 0
    today = date.today()

    for offset in range(34, -1, -1):
        metric_date = today - timedelta(days=offset)

        for index, blueprint in enumerate(products):
            sku = str(blueprint["sku"])
            unit_price = Decimal(str(blueprint["unit_price"]))
            ad_ratio = Decimal(str(blueprint["ad_ratio"]))
            units = max(1, 2 + ((offset + index * 2) % 4) - (1 if offset % 9 == 0 else 0))
            revenue = _money(unit_price * Decimal(units))
            fees = _money(revenue * Decimal("0.155"))
            refund = (
                _money(unit_price * Decimal("0.30"))
                if offset % (11 + index) == 0
                else Decimal("0.00")
            )
            ad_spend = _money(revenue * (ad_ratio + Decimal(index) * Decimal("0.01")))
            ad_sales = _money(revenue * Decimal("0.72"))
            clicks = 14 + ((offset + index * 3) % 11)
            impressions = clicks * (38 + index * 4)

            db.add(
                Order(
                    store_id=store_id,
                    sku=sku,
                    order_date=metric_date,
                    order_id=f"SYNC-{metric_date.isoformat()}-{index + 1}",
                    units=units,
                    revenue=revenue,
                    fees=fees,
                    refund=refund,
                )
            )
            db.add(
                Ad(
                    store_id=store_id,
                    sku=sku,
                    date=metric_date,
                    spend=ad_spend,
                    sales=ad_sales,
                    clicks=clicks,
                    impressions=impressions,
                )
            )
            rows_processed += 2

        if offset % 7 == 0:
            settlement_revenue = sum(
                _money(Decimal(str(product["unit_price"])) * Decimal(3 + index))
                for index, product in enumerate(products)
            )
            settlement_fees = _money(settlement_revenue * Decimal("0.13"))
            taxes = _money(settlement_revenue * Decimal("0.02"))
            reimbursements = Decimal("150.00") if offset % 14 == 0 else Decimal("0.00")
            db.add(
                Settlement(
                    store_id=store_id,
                    settlement_date=metric_date,
                    settlement_id=f"SYNC-SETTLEMENT-{metric_date.isoformat()}",
                    total_amount=settlement_revenue,
                    fees=settlement_fees,
                    taxes=taxes,
                    reimbursements=reimbursements,
                )
            )
            rows_processed += 1

    for index, blueprint in enumerate(products):
        db.add(
            Inventory(
                store_id=store_id,
                sku=str(blueprint["sku"]),
                snapshot_date=today,
                available_units=90 - index * 12,
                reserved_units=5 + index,
                inbound_units=18 + index * 4,
            )
        )
        rows_processed += 1

    db.flush()
    return rows_processed


def run_integration_sync(integration_id: uuid.UUID, job_id: uuid.UUID) -> None:
    db = SessionLocal()

    try:
        integration = db.get(Integration, integration_id)
        job = db.get(SyncJob, job_id)

        if integration is None or job is None:
            return

        job.status = "running"
        job.started_at = utcnow()
        _set_job_progress(job, 8)
        integration.status = "syncing"
        db.commit()

        time.sleep(0.25)

        _set_job_progress(job, 22)
        db.commit()

        rows_processed = _seed_sync_data(db, integration.store_id, integration.region)
        _set_job_progress(job, 78, rows_processed)
        db.commit()

        time.sleep(0.25)

        recompute_daily_metrics(db, integration.store_id)
        timestamp = utcnow()
        job.status = "success"
        job.completed_at = timestamp
        _set_job_progress(job, 100, rows_processed)
        job.error_message = None
        integration.status = "connected"
        integration.connected_at = integration.connected_at or timestamp
        integration.last_synced_at = timestamp
        db.commit()
    except Exception as exc:  # pragma: no cover - defensive background worker guard
        db.rollback()

        integration = db.get(Integration, integration_id)
        job = db.get(SyncJob, job_id)
        if integration is not None:
            integration.status = "error"
        if job is not None:
            job.status = "failed"
            job.completed_at = utcnow()
            job.error_message = str(exc)
        db.commit()
    finally:
        db.close()
