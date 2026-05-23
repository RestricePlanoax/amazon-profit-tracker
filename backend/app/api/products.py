from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_store
from app.models.product import Product
from app.models.store import Store
from app.services.csv_parser import normalize_column_name
from app.schemas.product import (
    BulkCogsResult,
    ProductProfitability,
    ProductRead,
    UpdateCogsRequest,
)
from app.services.metrics_service import get_product_profitability, recompute_daily_metrics


router = APIRouter(prefix="/products", tags=["products"])


def _canonical_header(name: str) -> str:
    normalized = normalize_column_name(name)
    aliases = {
        "sku": {"sku", "seller_sku", "merchant_sku"},
        "name": {"name", "product_name", "title"},
        "cogs": {"cogs", "cost", "cost_of_goods", "cogs_per_unit"},
    }
    compact = normalized.replace("_", "")
    for canonical, options in aliases.items():
        if normalized in options or compact in options:
            return canonical
    return normalized


@router.get("/profitability", response_model=list[ProductProfitability])
def list_product_profitability(
    range: str | None = Query(default=None),
    start_date: date | None = None,
    end_date: date | None = None,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> list[ProductProfitability]:
    rows = get_product_profitability(db, current_store.id, range, start_date, end_date)
    return [ProductProfitability(**row) for row in rows]


@router.put("/{sku}/cogs", response_model=ProductRead)
def update_product_cogs(
    sku: str,
    payload: UpdateCogsRequest,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> ProductRead:
    product = db.scalar(
        select(Product).where(Product.store_id == current_store.id, Product.sku == sku)
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found for this store.",
        )

    product.cogs = Decimal(str(payload.cogs))
    recompute_daily_metrics(db, current_store.id)
    db.commit()
    db.refresh(product)
    return ProductRead.model_validate(product)


@router.post("/cogs/bulk", response_model=BulkCogsResult)
async def bulk_upload_cogs(
    file: UploadFile = File(...),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
) -> BulkCogsResult:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A CSV file is required.")

    raw_content = await file.read()
    if not raw_content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="COGS CSV is empty.")

    text = raw_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="COGS CSV is missing a header row.",
        )
    reader.fieldnames = [_canonical_header(field or "") for field in reader.fieldnames]
    required = {"sku", "cogs"}
    missing = sorted(required - set(reader.fieldnames))
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"COGS CSV is missing required columns: {', '.join(missing)}.",
        )

    products_created = 0
    products_updated = 0
    rows_skipped = 0
    errors: list[str] = []

    for row_number, row in enumerate(reader, start=2):
        sku = (row.get("sku") or "").strip()
        name = (row.get("name") or "").strip() or None
        raw_cogs = (row.get("cogs") or "").strip()

        if not sku:
            rows_skipped += 1
            errors.append(f"Row {row_number}: sku is required.")
            continue
        try:
            cogs = Decimal(raw_cogs)
        except Exception:
            rows_skipped += 1
            errors.append(f"Row {row_number}: cogs must be a valid number.")
            continue
        if cogs < 0:
            rows_skipped += 1
            errors.append(f"Row {row_number}: cogs cannot be negative.")
            continue

        product = db.scalar(
            select(Product).where(Product.store_id == current_store.id, Product.sku == sku)
        )
        if product is None:
            product = Product(store_id=current_store.id, sku=sku, name=name, cogs=cogs)
            db.add(product)
            products_created += 1
        else:
            product.cogs = cogs
            if name:
                product.name = name
            products_updated += 1

    recompute_daily_metrics(db, current_store.id)
    db.commit()

    return BulkCogsResult(
        rows_processed=products_created + products_updated + rows_skipped,
        products_created=products_created,
        products_updated=products_updated,
        rows_skipped=rows_skipped,
        errors=errors[:20],
    )
