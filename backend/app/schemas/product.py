from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProductRead(BaseModel):
    id: uuid.UUID
    sku: str
    name: str | None
    cogs: float
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateCogsRequest(BaseModel):
    cogs: float = Field(ge=0)


class ProductProfitability(BaseModel):
    sku: str
    name: str | None
    cogs_per_unit: float
    units_sold: int
    revenue: float
    ad_spend: float
    ad_sales: float
    fees: float
    refund: float
    cogs: float
    net_profit: float
    profit_margin: float
    refund_rate: float
    acos: float
    roas: float
    profit_per_unit: float
