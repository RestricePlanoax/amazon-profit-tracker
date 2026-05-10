from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user
from app.models.integration import Integration
from app.models.store import Store
from app.models.upload import Upload
from app.models.user import User
from app.schemas.auth import AuthRequest, MeResponse, StoreInfo, TokenResponse
from app.services.auth_service import authenticate_user, create_user_with_default_store


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: AuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = create_user_with_default_store(db, payload.email, payload.password)
    access_token = create_access_token(str(user.id))
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(payload: AuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    access_token = create_access_token(str(user.id))
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=MeResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    store = db.scalar(
        select(Store).where(Store.user_id == current_user.id).order_by(Store.created_at.asc())
    )
    has_uploads = db.scalar(
        select(Upload.id)
        .where(Upload.store_id == store.id)
        .limit(1)
    )
    has_integration = db.scalar(
        select(Integration.id)
        .where(Integration.user_id == current_user.id, Integration.store_id == store.id)
        .limit(1)
    )
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
        store=StoreInfo.model_validate(store),
        needs_onboarding=not bool(has_uploads or has_integration),
    )
