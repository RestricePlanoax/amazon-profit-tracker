from __future__ import annotations

import hashlib
import uuid
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import utcnow
from app.models.ad import Ad
from app.models.ad_campaign_metric import AdCampaignMetric
from app.models.import_batch import ImportBatch
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.reimbursement import Reimbursement
from app.models.return_analytics import ReturnAnalytics
from app.models.seller_insight import SellerInsight
from app.models.profit_alert import ProfitAlert
from app.models.inventory_aging import InventoryAging
from app.models.settlement import Settlement
from app.services.analysis_runner import StoreAnalysisRunner
from app.services.metrics_service import recompute_daily_metrics

analysis_runner = StoreAnalysisRunner()


DEMO_PRODUCTS = [
    ("DEMO-BOTTLE-1L", "Insulated Bottle 1L", Decimal("330.00"), Decimal("1499.00"), Decimal("0.13")),
    ("DEMO-FLASK-750", "Travel Flask 750ml", Decimal("420.00"), Decimal("1899.00"), Decimal("0.11")),
    ("DEMO-TUMBLER", "Desk Tumbler 600ml", Decimal("260.00"), Decimal("999.00"), Decimal("0.17")),
    ("DEMO-LUNCHBOX", "Steel Lunch Box", Decimal("510.00"), Decimal("1599.00"), Decimal("0.20")),
]


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _source_hash(import_type: str, *parts: object) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(f"demo|{import_type}|{payload}".encode("utf-8")).hexdigest()


def _clear_previous_demo_data(db: Session, store_id: uuid.UUID) -> None:
    batch_ids = list(
        db.scalars(
            select(ImportBatch.id)
            .where(ImportBatch.store_id == store_id)
            .where(ImportBatch.source_type == "demo")
        ).all()
    )
    if not batch_ids:
        return

    for model in [Order, Ad, Settlement, Inventory]:
        db.execute(
            delete(model)
            .where(model.store_id == store_id)
            .where(model.import_batch_id.in_(batch_ids))
        )
    for model in [ProductVariant, ReturnAnalytics, Reimbursement, AdCampaignMetric, InventoryAging, ProfitAlert, SellerInsight]:
        db.execute(delete(model).where(model.store_id == store_id))
    db.execute(delete(ImportBatch).where(ImportBatch.id.in_(batch_ids)))


def load_demo_store(db: Session, store_id: uuid.UUID) -> tuple[ImportBatch, int]:
    _clear_previous_demo_data(db, store_id)

    batch = ImportBatch(
        store_id=store_id,
        source_type="demo",
        source_id="demo-store-v1",
        import_type="full_demo",
        status="processing",
        rows_inserted=0,
        rows_skipped=0,
        can_reprocess=False,
        started_at=utcnow(),
    )
    db.add(batch)
    db.flush()

    rows_inserted = 0
    today = date.today()
    start_date = today - timedelta(days=179)

    variant_records: list[tuple[str, str, str]] = []
    for sku, name, cogs, _, _ in DEMO_PRODUCTS:
        product = db.scalar(select(Product).where(Product.store_id == store_id, Product.sku == sku))
        if product is None:
            product = Product(store_id=store_id, sku=sku, name=name, cogs=cogs)
            db.add(product)
        else:
            product.name = name
            product.cogs = cogs
        rows_inserted += 1
        db.flush()
        variant_records.extend(
            [
                (sku, f"{sku}-STD", "Standard"),
                (sku, f"{sku}-XL", "XL"),
            ]
        )
        for _, variant_sku, variant_name in variant_records[-2:]:
            if db.scalar(
                select(ProductVariant).where(ProductVariant.store_id == store_id, ProductVariant.sku == variant_sku)
            ) is None:
                db.add(
                    ProductVariant(
                        product_id=product.id,
                        store_id=store_id,
                        variant_name=variant_name,
                        sku=variant_sku,
                    )
                )

    for day_offset in range(180):
        metric_date = start_date + timedelta(days=day_offset)
        seasonality = Decimal("1.18") if day_offset % 30 in range(18, 27) else Decimal("1.00")
        weekend_lift = Decimal("1.12") if metric_date.weekday() >= 5 else Decimal("1.00")

        for product_index, (sku, _, _, price, ad_ratio) in enumerate(DEMO_PRODUCTS):
            base_units = 1 + ((day_offset + product_index * 3) % 5)
            units = max(1, int(Decimal(base_units) * seasonality * weekend_lift))
            revenue = _money(price * Decimal(units))
            fees = _money(revenue * Decimal("0.155"))
            refund = (
                _money(price * Decimal("0.35"))
                if (day_offset + product_index) % (19 + product_index) == 0
                else Decimal("0.00")
            )
            ad_spend = _money(revenue * (ad_ratio + Decimal(product_index) * Decimal("0.012")))
            ad_sales = _money(revenue * Decimal("0.70"))
            clicks = 12 + ((day_offset + product_index * 5) % 18)
            impressions = clicks * (34 + product_index * 7)

            db.add(
                Order(
                    store_id=store_id,
                    import_batch_id=batch.id,
                    source_row_hash=_source_hash("orders", metric_date, sku),
                    sku=sku,
                    order_date=metric_date,
                    order_id=f"DEMO-{metric_date.isoformat()}-{product_index + 1}",
                    units=units,
                    revenue=revenue,
                    fees=fees,
                    refund=refund,
                )
            )
            db.add(
                Ad(
                    store_id=store_id,
                    import_batch_id=batch.id,
                    source_row_hash=_source_hash("ads", metric_date, sku),
                    sku=sku,
                    date=metric_date,
                    spend=ad_spend,
                    sales=ad_sales,
                    clicks=clicks,
                    impressions=impressions,
                )
            )
            db.add(
                AdCampaignMetric(
                    store_id=store_id,
                    campaign_id=f"DEMO-CAMPAIGN-{product_index + 1}",
                    campaign_name=f"{sku} Growth Campaign",
                    sku=sku,
                    metric_date=metric_date,
                    daily_spend=ad_spend,
                    clicks=clicks,
                    orders=units,
                    acos=_money((ad_spend / ad_sales) * Decimal("100")) if ad_sales else Decimal("0"),
                    roas=_money(ad_sales / ad_spend) if ad_spend else Decimal("0"),
                    conversion_rate=_money((Decimal(units) / Decimal(clicks)) * Decimal("100")) if clicks else Decimal("0"),
                )
            )
            rows_inserted += 3

        if day_offset % 14 == 0:
            total_amount = Decimal("24500.00") + Decimal(day_offset * 175)
            db.add(
                Settlement(
                    store_id=store_id,
                    import_batch_id=batch.id,
                    source_row_hash=_source_hash("settlement", metric_date),
                    settlement_date=metric_date,
                    settlement_id=f"DEMO-SETTLEMENT-{metric_date.isoformat()}",
                    total_amount=_money(total_amount),
                    fees=_money(total_amount * Decimal("0.12")),
                    taxes=_money(total_amount * Decimal("0.018")),
                    reimbursements=Decimal("275.00") if day_offset % 28 == 0 else Decimal("0.00"),
                )
            )
            rows_inserted += 1

    for product_index, (sku, _, _, _, _) in enumerate(DEMO_PRODUCTS):
        db.add(
            Inventory(
                store_id=store_id,
                import_batch_id=batch.id,
                source_row_hash=_source_hash("inventory", today, sku),
                sku=sku,
                snapshot_date=today,
                available_units=120 - product_index * 18,
                reserved_units=8 + product_index * 2,
                inbound_units=22 + product_index * 6,
                days_in_storage=35 + product_index * 28,
                monthly_storage_fee=Decimal("420.00") + Decimal(product_index * 185),
            )
        )
        rows_inserted += 1

    for variant_index, (base_sku, variant_sku, variant_name) in enumerate(variant_records):
        product_variant = db.scalar(
            select(ProductVariant).where(ProductVariant.store_id == store_id, ProductVariant.sku == variant_sku)
        )
        db.add(
            ReturnAnalytics(
                store_id=store_id,
                product_variant_id=product_variant.id if product_variant else None,
                sku=base_sku,
                variant=variant_name,
                return_reason="Size mismatch" if variant_name == "XL" else "Changed mind",
                refund_amount=Decimal("249.00") if variant_name == "XL" else Decimal("79.00"),
                returned_units=3 if variant_name == "XL" else 1,
                return_date=today - timedelta(days=variant_index * 2),
            )
        )
        rows_inserted += 1

    for product_index, (sku, _, _, _, _) in enumerate(DEMO_PRODUCTS[:3]):
        db.add(
            Reimbursement(
                store_id=store_id,
                sku=sku,
                issue_type="lost_inventory" if product_index == 0 else "warehouse_damage",
                amount=Decimal("1450.00") + Decimal(product_index * 325),
                status="pending",
                detected_at=today - timedelta(days=7 + product_index),
                claim_deadline=today + timedelta(days=21 - product_index * 4),
                claimed=False,
                received=False,
            )
        )
        rows_inserted += 1

    recompute_daily_metrics(db, store_id)
    analysis_runner.run(db, store_id)
    batch.status = "completed"
    batch.rows_inserted = rows_inserted
    batch.completed_at = utcnow()
    db.commit()
    db.refresh(batch)
    return batch, rows_inserted
