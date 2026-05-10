from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.store import Store
from app.models.user import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user_with_default_store(db: Session, email: str, password: str) -> User:
    normalized_email = normalize_email(email)
    existing_user = db.scalar(select(User).where(User.email == normalized_email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    user = User(email=normalized_email, password_hash=hash_password(password))
    default_store = Store(name="My Amazon Store", marketplace="amazon_in", user=user)
    db.add_all([user, default_store])
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    normalized_email = normalize_email(email)
    user = db.scalar(select(User).where(User.email == normalized_email))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return user
