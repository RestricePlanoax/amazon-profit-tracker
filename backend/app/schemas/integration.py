from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class IntegrationConnectRequest(BaseModel):
    marketplace: str = Field(min_length=2, max_length=8)


class IntegrationRead(BaseModel):
    id: uuid.UUID
    provider: str
    status: str
    region: str | None
    external_seller_id: str | None
    connected_at: datetime | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SyncJobRead(BaseModel):
    id: uuid.UUID
    job_type: str
    status: str
    progress_percent: int
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    rows_processed: int
    created_at: datetime

    model_config = {"from_attributes": True}


class IntegrationStatusResponse(BaseModel):
    integration: IntegrationRead | None
    has_connection: bool
    latest_job: SyncJobRead | None = None
