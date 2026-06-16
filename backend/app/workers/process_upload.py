from __future__ import annotations

import hashlib
from dataclasses import asdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.database import SessionLocal, utcnow
from app.models.ad import Ad
from app.models.ad_campaign_metric import AdCampaignMetric
from app.models.import_batch import ImportBatch
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.reimbursement import Reimbursement
from app.models.return_analytics import ReturnAnalytics
from app.models.settlement import Settlement
from app.models.upload import Upload
from app.services.analysis_runner import StoreAnalysisRunner
from app.services.csv_parser import (
    CSVValidationError,
    parse_ads_csv,
    parse_campaigns_csv,
    parse_inventory_csv,
    parse_orders_csv,
    parse_reimbursements_csv,
    parse_returns_csv,
    parse_settlement_csv,
)
from app.services.metrics_service import recompute_daily_metrics

analysis_runner = StoreAnalysisRunner()


def _mark_upload_failed(upload_id: UUID, error_message: str) -> None:
    db = SessionLocal()
    try:
        upload = db.get(Upload, upload_id)
        if upload is None:
            return
        upload.status = "failed"
        upload.error_message = error_message
        upload.rows_inserted = 0
        if upload.import_batch_id:
            batch = db.get(ImportBatch, upload.import_batch_id)
            if batch is not None:
                batch.status = "failed"
                batch.error_message = error_message
                batch.rows_inserted = 0
                batch.completed_at = utcnow()
        db.commit()
    finally:
        db.close()


def _ensure_products_exist(db, store_id, skus: set[str]) -> None:
    if not skus:
        return

    db.execute(
        insert(Product)
        .values(
            [{"store_id": store_id, "sku": sku, "cogs": Decimal("0")} for sku in sorted(skus)]
        )
        .on_conflict_do_nothing(index_elements=["store_id", "sku"])
    )


def _product_ids_by_sku(db, store_id, skus: set[str]) -> dict[str, UUID]:
    if not skus:
        return {}
    rows = db.execute(
        select(Product.sku, Product.id).where(Product.store_id == store_id).where(Product.sku.in_(skus))
    ).all()
    return {row.sku: row.id for row in rows}


def _variant_key(base_sku: str, variant: str, variant_sku: str | None) -> str:
    if variant_sku:
        return variant_sku
    normalized = "".join(character.lower() if character.isalnum() else "-" for character in variant).strip("-")
    normalized = normalized or "default"
    return f"{base_sku}::{normalized}"


def _ensure_variants_exist(db, store_id, rows) -> dict[tuple[str, str], UUID]:
    skus = {row.sku for row in rows}
    _ensure_products_exist(db, store_id, skus)
    product_ids = _product_ids_by_sku(db, store_id, skus)
    payload = []
    for row in rows:
        variant_sku = _variant_key(row.sku, row.variant, row.variant_sku)
        product_id = product_ids.get(row.sku)
        if product_id is None:
            continue
        payload.append(
            {
                "product_id": product_id,
                "store_id": store_id,
                "variant_name": row.variant,
                "sku": variant_sku,
            }
        )
    if payload:
        db.execute(
            insert(ProductVariant)
            .values(payload)
            .on_conflict_do_nothing(index_elements=["store_id", "sku"])
        )
    variant_skus = {item["sku"] for item in payload}
    if not variant_skus:
        return {}
    variant_rows = db.execute(
        select(ProductVariant.id, ProductVariant.sku)
        .where(ProductVariant.store_id == store_id)
        .where(ProductVariant.sku.in_(variant_skus))
    ).all()
    ids_by_sku = {row.sku: row.id for row in variant_rows}
    return {
        (row.sku, row.variant): ids_by_sku[_variant_key(row.sku, row.variant, row.variant_sku)]
        for row in rows
        if _variant_key(row.sku, row.variant, row.variant_sku) in ids_by_sku
    }


def _row_hash(import_type: str, row) -> str:
    payload = asdict(row)
    canonical = "|".join(f"{key}={payload[key]}" for key in sorted(payload))
    return hashlib.sha256(f"{import_type}|{canonical}".encode("utf-8")).hexdigest()


def _existing_hashes(db, model, store_id, hashes: set[str]) -> set[str]:
    if not hashes:
        return set()
    return set(
        db.scalars(
            select(model.source_row_hash)
            .where(model.store_id == store_id)
            .where(model.source_row_hash.in_(hashes))
        ).all()
    )


def _is_duplicate_hash(source_row_hash: str, duplicate_hashes: set[str], seen_hashes: set[str]) -> bool:
    if source_row_hash in duplicate_hashes or source_row_hash in seen_hashes:
        return True
    seen_hashes.add(source_row_hash)
    return False


def _upsert_inventory_rows(db, payload: list[dict]) -> None:
    if not payload:
        return
    statement = insert(Inventory).values(payload)
    db.execute(
        statement.on_conflict_do_update(
            index_elements=["store_id", "sku", "snapshot_date"],
            set_={
                "import_batch_id": statement.excluded.import_batch_id,
                "source_row_hash": statement.excluded.source_row_hash,
                "available_units": statement.excluded.available_units,
                "reserved_units": statement.excluded.reserved_units,
                "inbound_units": statement.excluded.inbound_units,
                "days_in_storage": statement.excluded.days_in_storage,
                "monthly_storage_fee": statement.excluded.monthly_storage_fee,
            },
        )
    )


def _upsert_campaign_rows(db, payload: list[dict]) -> None:
    if not payload:
        return
    statement = insert(AdCampaignMetric).values(payload)
    db.execute(
        statement.on_conflict_do_update(
            index_elements=["store_id", "campaign_id", "sku", "metric_date"],
            set_={
                "import_batch_id": statement.excluded.import_batch_id,
                "source_row_hash": statement.excluded.source_row_hash,
                "campaign_name": statement.excluded.campaign_name,
                "daily_spend": statement.excluded.daily_spend,
                "clicks": statement.excluded.clicks,
                "orders": statement.excluded.orders,
                "acos": statement.excluded.acos,
                "roas": statement.excluded.roas,
                "conversion_rate": statement.excluded.conversion_rate,
            },
        )
    )


def process_upload(upload_id: str) -> None:
    parsed_upload_id = UUID(upload_id)
    db = SessionLocal()

    try:
        upload = db.get(Upload, parsed_upload_id)
        if upload is None:
            return
        batch = db.get(ImportBatch, upload.import_batch_id) if upload.import_batch_id else None

        upload.status = "processing"
        upload.error_message = None
        if batch is not None:
            batch.status = "processing"
            batch.started_at = utcnow()
            batch.error_message = None
        db.commit()

        if upload.upload_type == "orders":
            rows = parse_orders_csv(upload.file_path)
            hashes_by_index = [_row_hash("orders", row) for row in rows]
            duplicate_hashes = _existing_hashes(db, Order, upload.store_id, set(hashes_by_index))
            _ensure_products_exist(db, upload.store_id, {row.sku for row in rows})
            inserted = 0
            skipped = 0
            seen_hashes: set[str] = set()
            for row, source_row_hash in zip(rows, hashes_by_index, strict=True):
                if _is_duplicate_hash(source_row_hash, duplicate_hashes, seen_hashes):
                    skipped += 1
                    continue
                db.add(
                    Order(
                        store_id=upload.store_id,
                        import_batch_id=upload.import_batch_id,
                        source_row_hash=source_row_hash,
                        sku=row.sku,
                        order_date=row.order_date,
                        order_id=row.order_id,
                        units=row.units,
                        revenue=row.revenue,
                        fees=row.fees,
                        refund=row.refund,
                    )
                )
                inserted += 1
            upload.rows_inserted = inserted
            upload.rows_skipped = skipped
        elif upload.upload_type == "ads":
            rows = parse_ads_csv(upload.file_path)
            hashes_by_index = [_row_hash("ads", row) for row in rows]
            duplicate_hashes = _existing_hashes(db, Ad, upload.store_id, set(hashes_by_index))
            _ensure_products_exist(db, upload.store_id, {row.sku for row in rows})
            inserted = 0
            skipped = 0
            seen_hashes: set[str] = set()
            for row, source_row_hash in zip(rows, hashes_by_index, strict=True):
                if _is_duplicate_hash(source_row_hash, duplicate_hashes, seen_hashes):
                    skipped += 1
                    continue
                db.add(
                    Ad(
                        store_id=upload.store_id,
                        import_batch_id=upload.import_batch_id,
                        source_row_hash=source_row_hash,
                        sku=row.sku,
                        date=row.date,
                        spend=row.spend,
                        sales=row.sales,
                        clicks=row.clicks,
                        impressions=row.impressions,
                    )
                )
                inserted += 1
            upload.rows_inserted = inserted
            upload.rows_skipped = skipped
        elif upload.upload_type == "settlement":
            rows = parse_settlement_csv(upload.file_path)
            hashes_by_index = [_row_hash("settlement", row) for row in rows]
            duplicate_hashes = _existing_hashes(db, Settlement, upload.store_id, set(hashes_by_index))
            inserted = 0
            skipped = 0
            seen_hashes: set[str] = set()
            for row, source_row_hash in zip(rows, hashes_by_index, strict=True):
                if _is_duplicate_hash(source_row_hash, duplicate_hashes, seen_hashes):
                    skipped += 1
                    continue
                db.add(
                    Settlement(
                        store_id=upload.store_id,
                        import_batch_id=upload.import_batch_id,
                        source_row_hash=source_row_hash,
                        settlement_date=row.settlement_date,
                        settlement_id=row.settlement_id,
                        total_amount=row.total_amount,
                        fees=row.fees,
                        taxes=row.taxes,
                        reimbursements=row.reimbursements,
                    )
                )
                inserted += 1
            upload.rows_inserted = inserted
            upload.rows_skipped = skipped
        elif upload.upload_type == "returns":
            rows = parse_returns_csv(upload.file_path)
            hashes_by_index = [_row_hash("returns", row) for row in rows]
            duplicate_hashes = _existing_hashes(db, ReturnAnalytics, upload.store_id, set(hashes_by_index))
            variant_ids = _ensure_variants_exist(db, upload.store_id, rows)
            inserted = 0
            skipped = 0
            seen_hashes: set[str] = set()
            for row, source_row_hash in zip(rows, hashes_by_index, strict=True):
                if _is_duplicate_hash(source_row_hash, duplicate_hashes, seen_hashes):
                    skipped += 1
                    continue
                db.add(
                    ReturnAnalytics(
                        store_id=upload.store_id,
                        import_batch_id=upload.import_batch_id,
                        source_row_hash=source_row_hash,
                        product_variant_id=variant_ids.get((row.sku, row.variant)),
                        sku=row.sku,
                        variant=row.variant,
                        return_reason=row.return_reason,
                        refund_amount=row.refund_amount,
                        returned_units=row.returned_units,
                        return_date=row.return_date,
                    )
                )
                inserted += 1
            upload.rows_inserted = inserted
            upload.rows_skipped = skipped
        elif upload.upload_type == "reimbursements":
            rows = parse_reimbursements_csv(upload.file_path)
            hashes_by_index = [_row_hash("reimbursements", row) for row in rows]
            duplicate_hashes = _existing_hashes(db, Reimbursement, upload.store_id, set(hashes_by_index))
            _ensure_products_exist(db, upload.store_id, {row.sku for row in rows})
            inserted = 0
            skipped = 0
            seen_hashes: set[str] = set()
            for row, source_row_hash in zip(rows, hashes_by_index, strict=True):
                if _is_duplicate_hash(source_row_hash, duplicate_hashes, seen_hashes):
                    skipped += 1
                    continue
                db.add(
                    Reimbursement(
                        store_id=upload.store_id,
                        import_batch_id=upload.import_batch_id,
                        source_row_hash=source_row_hash,
                        sku=row.sku,
                        issue_type=row.issue_type,
                        amount=row.amount,
                        status=row.status,
                        detected_at=row.detected_at,
                        claim_deadline=row.claim_deadline,
                        claimed=row.claimed,
                        received=row.received,
                    )
                )
                inserted += 1
            upload.rows_inserted = inserted
            upload.rows_skipped = skipped
        elif upload.upload_type == "campaigns":
            rows = parse_campaigns_csv(upload.file_path)
            hashes_by_index = [_row_hash("campaigns", row) for row in rows]
            duplicate_hashes = _existing_hashes(db, AdCampaignMetric, upload.store_id, set(hashes_by_index))
            _ensure_products_exist(db, upload.store_id, {row.sku for row in rows})
            inserted = 0
            skipped = 0
            seen_hashes: set[str] = set()
            payload = []
            for row, source_row_hash in zip(rows, hashes_by_index, strict=True):
                if _is_duplicate_hash(source_row_hash, duplicate_hashes, seen_hashes):
                    skipped += 1
                    continue
                payload.append(
                    {
                        "store_id": upload.store_id,
                        "import_batch_id": upload.import_batch_id,
                        "source_row_hash": source_row_hash,
                        "campaign_id": row.campaign_id,
                        "campaign_name": row.campaign_name,
                        "sku": row.sku,
                        "metric_date": row.metric_date,
                        "daily_spend": row.spend,
                        "clicks": row.clicks,
                        "orders": row.orders,
                        "acos": row.acos,
                        "roas": row.roas,
                        "conversion_rate": row.conversion_rate,
                    }
                )
                inserted += 1
            _upsert_campaign_rows(db, payload)
            upload.rows_inserted = inserted
            upload.rows_skipped = skipped
        elif upload.upload_type == "inventory":
            rows = parse_inventory_csv(upload.file_path)
            hashes_by_index = [_row_hash("inventory", row) for row in rows]
            duplicate_hashes = _existing_hashes(db, Inventory, upload.store_id, set(hashes_by_index))
            _ensure_products_exist(db, upload.store_id, {row.sku for row in rows})
            inserted = 0
            skipped = 0
            seen_hashes: set[str] = set()
            payload = []
            for row, source_row_hash in zip(rows, hashes_by_index, strict=True):
                if _is_duplicate_hash(source_row_hash, duplicate_hashes, seen_hashes):
                    skipped += 1
                    continue
                payload.append(
                    {
                        "store_id": upload.store_id,
                        "import_batch_id": upload.import_batch_id,
                        "source_row_hash": source_row_hash,
                        "sku": row.sku,
                        "snapshot_date": row.snapshot_date,
                        "available_units": row.available_units,
                        "reserved_units": row.reserved_units,
                        "inbound_units": row.inbound_units,
                        "days_in_storage": row.days_in_storage,
                        "monthly_storage_fee": row.monthly_storage_fee,
                    }
                )
                inserted += 1
            _upsert_inventory_rows(db, payload)
            upload.rows_inserted = inserted
            upload.rows_skipped = skipped
        else:
            raise ValueError(f"Unsupported upload type '{upload.upload_type}'.")

        recompute_daily_metrics(db, upload.store_id)
        analysis_runner.run(db, upload.store_id)
        upload.status = "completed"
        upload.error_message = None
        if batch is not None:
            batch.status = "completed"
            batch.rows_inserted = upload.rows_inserted
            batch.rows_skipped = upload.rows_skipped
            batch.error_message = None
            batch.completed_at = utcnow()
        db.commit()
    except CSVValidationError as exc:
        db.rollback()
        _mark_upload_failed(parsed_upload_id, str(exc))
    except Exception as exc:  # pragma: no cover - defensive path
        db.rollback()
        _mark_upload_failed(parsed_upload_id, f"Processing failed: {exc}")
    finally:
        db.close()
