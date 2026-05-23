from __future__ import annotations

import hashlib
from dataclasses import asdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.database import SessionLocal, utcnow
from app.models.ad import Ad
from app.models.import_batch import ImportBatch
from app.models.order import Order
from app.models.product import Product
from app.models.settlement import Settlement
from app.models.upload import Upload
from app.services.csv_parser import (
    CSVValidationError,
    parse_ads_csv,
    parse_orders_csv,
    parse_settlement_csv,
)
from app.services.metrics_service import recompute_daily_metrics


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
        else:
            raise ValueError(f"Unsupported upload type '{upload.upload_type}'.")

        recompute_daily_metrics(db, upload.store_id)
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
