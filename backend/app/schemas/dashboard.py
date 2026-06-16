from __future__ import annotations

from pydantic import BaseModel


class MetricValue(BaseModel):
    current: float
    previous: float
    change_pct: float | None


class DashboardMetricSet(BaseModel):
    revenue: MetricValue
    net_profit: MetricValue
    profit_margin: MetricValue
    tacos: MetricValue
    acos: MetricValue
    refund_rate: MetricValue
    ad_spend: MetricValue
    roas: MetricValue
    avg_order_value: MetricValue
    orders_count: MetricValue
    units_sold: MetricValue
    ctr: MetricValue
    cpc: MetricValue
    ad_sales: MetricValue
    fees: MetricValue
    taxes: MetricValue
    reimbursements: MetricValue
    refunds: MetricValue
    cogs: MetricValue
    profit_per_order: MetricValue


class DataSourceStatus(BaseModel):
    key: str
    name: str
    active: bool
    status: str
    last_refresh_at: str | None


class RangeCoverageStatus(BaseModel):
    key: str
    label: str
    covered_days: int
    expected_days: int
    coverage_pct: float
    status: str
    latest_data_date: str | None


class MetricTrust(BaseModel):
    metric_key: str
    powered_by: list[str]
    coverage_pct: float
    freshness_at: str | None
    status: str
    note: str


class DashboardSummary(BaseModel):
    start_date: str
    end_date: str
    previous_start_date: str
    previous_end_date: str
    metrics: DashboardMetricSet
    last_data_refresh: str | None = None
    data_sources: list[DataSourceStatus] = []
    range_coverage: list[RangeCoverageStatus] = []
    metric_trust: list[MetricTrust] = []


class DateBounds(BaseModel):
    min_date: str
    max_date: str
    default_start_date: str
    default_end_date: str


class DashboardInsight(BaseModel):
    title: str
    body: str
    severity: str
    metric_keys: list[str]


class KnowledgeChunk(BaseModel):
    id: str
    title: str
    content: str


class DashboardInsightsResponse(BaseModel):
    summary: str
    insights: list[DashboardInsight]
    llm_prompt_template: str
    knowledge_chunks: list[KnowledgeChunk]


class TrendPoint(BaseModel):
    date: str
    revenue: float
    ad_sales: float
    ad_spend: float
    fees: float
    taxes: float
    reimbursements: float
    refund: float
    cogs: float
    net_profit: float
    profit_margin: float
    tacos: float
    acos: float
    roas: float
    refund_rate: float
    orders_count: int
    units_sold: int
    clicks: int
    impressions: int
    ctr: float
    cpc: float
    avg_order_value: float
