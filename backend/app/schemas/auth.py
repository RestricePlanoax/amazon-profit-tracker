from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StoreInfo(BaseModel):
    id: uuid.UUID
    name: str
    marketplace: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime
    store: StoreInfo
    needs_onboarding: bool

    model_config = {"from_attributes": True}
