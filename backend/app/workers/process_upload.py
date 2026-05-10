from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert

from app.core.database import SessionLocal
from app.models.ad import Ad
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


def process_upload(upload_id: str) -> None:
    parsed_upload_id = UUID(upload_id)
    db = SessionLocal()

    try:
        upload = db.get(Upload, parsed_upload_id)
        if upload is None:
            return

        upload.status = "processing"
        upload.error_message = None
        db.commit()

        if upload.upload_type == "orders":
            rows = parse_orders_csv(upload.file_path)
            _ensure_products_exist(db, upload.store_id, {row.sku for row in rows})
            for row in rows:
                db.add(
                    Order(
                        store_id=upload.store_id,
                        sku=row.sku,
                        order_date=row.order_date,
                        order_id=row.order_id,
                        units=row.units,
                        revenue=row.revenue,
                        fees=row.fees,
                        refund=row.refund,
                    )
                )
            upload.rows_inserted = len(rows)
            upload.rows_skipped = 0
        elif upload.upload_type == "ads":
            rows = parse_ads_csv(upload.file_path)
            _ensure_products_exist(db, upload.store_id, {row.sku for row in rows})
            for row in rows:
                db.add(
                    Ad(
                        store_id=upload.store_id,
                        sku=row.sku,
                        date=row.date,
                        spend=row.spend,
                        sales=row.sales,
                        clicks=row.clicks,
                        impressions=row.impressions,
                    )
                )
            upload.rows_inserted = len(rows)
            upload.rows_skipped = 0
        elif upload.upload_type == "settlement":
            rows = parse_settlement_csv(upload.file_path)
            for row in rows:
                db.add(
                    Settlement(
                        store_id=upload.store_id,
                        settlement_date=row.settlement_date,
                        settlement_id=row.settlement_id,
                        total_amount=row.total_amount,
                        fees=row.fees,
                        taxes=row.taxes,
                        reimbursements=row.reimbursements,
                    )
                )
            upload.rows_inserted = len(rows)
            upload.rows_skipped = 0
        else:
            raise ValueError(f"Unsupported upload type '{upload.upload_type}'.")

        recompute_daily_metrics(db, upload.store_id)
        upload.status = "completed"
        upload.error_message = None
        db.commit()
    except CSVValidationError as exc:
        db.rollback()
        _mark_upload_failed(parsed_upload_id, str(exc))
    except Exception as exc:  # pragma: no cover - defensive path
        db.rollback()
        _mark_upload_failed(parsed_upload_id, f"Processing failed: {exc}")
    finally:
        db.close()
