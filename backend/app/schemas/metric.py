from __future__ import annotations

from pydantic import BaseModel


class MetricCatalogItem(BaseModel):
    key: str
    label: str
    category: str
    format: str
    polarity: str
    description: str
    formula_label: str
    business_question: str
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    visible_by_default: bool
    dashboard_slot: str
    onboarding_required: bool = False
    sort_order: int
