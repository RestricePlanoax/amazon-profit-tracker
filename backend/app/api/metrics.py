from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.metric import MetricCatalogItem
from app.services.metric_catalog import get_metric_catalog


router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/catalog", response_model=list[MetricCatalogItem])
def list_metric_catalog(
    current_user: User = Depends(get_current_user),
) -> list[MetricCatalogItem]:
    _ = current_user
    return [MetricCatalogItem(**item) for item in get_metric_catalog()]
