from __future__ import annotations

from datetime import datetime, timezone
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def create_db_engine(url: str) -> Engine:
    engine_kwargs: dict[str, object] = {
        "future": True,
        "pool_pre_ping": True,
    }
    connect_args: dict[str, object] = {}

    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if url == "sqlite://" or ":memory:" in url:
            engine_kwargs["poolclass"] = StaticPool
    else:
        # Serverless-friendly default for Vercel/Supabase style deployments.
        engine_kwargs["poolclass"] = NullPool

    if connect_args:
        engine_kwargs["connect_args"] = connect_args

    return create_engine(url, **engine_kwargs)


engine = create_db_engine(settings.resolved_database_url)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
