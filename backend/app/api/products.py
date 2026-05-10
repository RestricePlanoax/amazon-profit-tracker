from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_store
from app.models.product import Product
from app.models.store import Store
from app.schemas.product import ProductProfitability, ProductRead, UpdateCogsRequest
from app.services.metrics_service import get_product_profitability, recompute_daily_metrics


router = APIRouter(prefix="/products", tags=["products"])


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
