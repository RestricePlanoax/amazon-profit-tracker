from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.database_errors import raise_database_http_error
from app.core.security import create_access_token, get_current_user
from app.models.integration import Integration
from app.models.store import Store
from app.models.upload import Upload
from app.models.user import User
from app.schemas.auth import AuthRequest, MeResponse, StoreInfo, TokenResponse
from app.services.auth_service import authenticate_user, create_user_with_default_store


router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


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
    try:
        store = db.scalar(
            select(Store).where(Store.user_id == current_user.id).order_by(Store.created_at.asc())
        )
        if store is None:
            logger.warning("User %s has no default store.", current_user.id)
            raise ValueError("missing store")

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
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found for user.",
        )
    except SQLAlchemyError as exc:
        raise_database_http_error(exc, action="load auth profile", logger_name=__name__)

    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
        store=StoreInfo.model_validate(store),
        needs_onboarding=not bool(has_uploads or has_integration),
    )
