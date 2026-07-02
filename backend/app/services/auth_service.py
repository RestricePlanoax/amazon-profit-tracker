from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database_errors import raise_database_http_error
from app.core.security import hash_password, verify_password
from app.models.store import Store
from app.models.user import User


logger = logging.getLogger(__name__)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user_with_default_store(db: Session, email: str, password: str) -> User:
    normalized_email = normalize_email(email)

    try:
        existing_user = db.scalar(select(User).where(User.email == normalized_email))
    except SQLAlchemyError as exc:
        raise_database_http_error(exc, action="signup lookup", logger_name=__name__)

    if existing_user is not None:
        logger.info("Duplicate signup attempt rejected for %s.", normalized_email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    user = User(email=normalized_email, password_hash=hash_password(password))
    default_store = Store(name="My Amazon Store", marketplace="amazon_in", user=user)
    db.add_all([user, default_store])

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise_database_http_error(exc, action="signup commit", logger_name=__name__)
    except SQLAlchemyError as exc:
        db.rollback()
        raise_database_http_error(exc, action="signup commit", logger_name=__name__)

    logger.info("Created account and default store for %s.", normalized_email)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    normalized_email = normalize_email(email)

    try:
        user = db.scalar(select(User).where(User.email == normalized_email))
    except SQLAlchemyError as exc:
        raise_database_http_error(exc, action="login lookup", logger_name=__name__)

    if user is None:
        logger.info("Login rejected because user was not found for %s.", normalized_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(password, user.password_hash):
        logger.info("Login rejected because password verification failed for %s.", normalized_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    logger.info("Login accepted for %s.", normalized_email)
    return user
