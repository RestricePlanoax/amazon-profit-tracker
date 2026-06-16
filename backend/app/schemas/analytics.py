from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class ProfitAlertRead(BaseModel):
    id: uuid.UUID
    sku: str | None
    alert_type: str
    severity: str
    title: str
    message: str
    metric_value: float | None
    created_at: datetime
    resolved: bool
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class ProfitAlertSummary(BaseModel):
    total_open: int
    high_priority: int
    margin_drop: int
    unexpected_fees: int
    ad_waste: int
    return_spike: int
    storage_risk: int


class ProfitAlertsResponse(BaseModel):
    summary: ProfitAlertSummary
    alerts: list[ProfitAlertRead]


class VariantReturnRow(BaseModel):
    sku: str
    variant: str
    return_rate: float
    refund_cost: float
    return_units: int
    top_reason: str | None


class ReturnReasonRow(BaseModel):
    reason: str
    occurrences: int
    refund_cost: float


class ReturnAnalysisResponse(BaseModel):
    worst_variants: list[VariantReturnRow]
    top_return_reasons: list[ReturnReasonRow]
    summary_text: str


class ReimbursementRow(BaseModel):
    id: uuid.UUID
    sku: str
    issue_type: str
    amount: float
    status: str
    detected_at: date
    claim_deadline: date | None
    claimed: bool
    received: bool

    model_config = {"from_attributes": True}


class ReimbursementSummary(BaseModel):
    total_pending_amount: float
    near_expiry_count: int
    open_cases: int


class ReimbursementsResponse(BaseModel):
    summary: ReimbursementSummary
    cases: list[ReimbursementRow]


class StorageRiskRow(BaseModel):
    sku: str
    quantity: int
    days_in_storage: int
    monthly_storage_fee: float
    warning_level: str
    recommended_action: str


class StorageAnalysisResponse(BaseModel):
    summary_text: str
    slow_moving_inventory: list[StorageRiskRow]


class CampaignWasteRow(BaseModel):
    campaign_id: str
    campaign_name: str
    sku: str
    daily_spend: float
    clicks: int
    orders: int
    acos: float
    roas: float
    conversion_rate: float
    waste_flag: bool


class AdAnalysisResponse(BaseModel):
    summary_text: str
    worst_campaigns: list[CampaignWasteRow]


class SellerInsightRead(BaseModel):
    id: uuid.UUID
    priority: str
    headline: str
    insight_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DailyInsightsResponse(BaseModel):
    biggest_profit_leak: str | None
    worst_sku_today: str | None
    best_sku_today: str | None
    recommended_actions: list[str]
    insights: list[SellerInsightRead]
