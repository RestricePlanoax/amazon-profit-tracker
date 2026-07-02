from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError, SQLAlchemyError


logger = logging.getLogger(__name__)


def _error_text(exc: BaseException) -> str:
    return str(exc).lower()


def is_missing_table_error(exc: BaseException) -> bool:
    message = _error_text(exc)
    return (
        "does not exist" in message
        or "undefinedtable" in message
        or "no such table" in message
        or "relation" in message and "does not exist" in message
    )


def is_duplicate_email_error(exc: BaseException) -> bool:
    message = _error_text(exc)
    return "unique constraint" in message and "email" in message or "ix_users_email" in message


def raise_database_http_error(
    exc: BaseException,
    *,
    action: str,
    logger_name: str,
) -> None:
    scoped_logger = logging.getLogger(logger_name)

    if isinstance(exc, IntegrityError) and is_duplicate_email_error(exc):
        scoped_logger.info("Duplicate email rejected during %s.", action)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        ) from exc

    if isinstance(exc, ProgrammingError) and is_missing_table_error(exc):
        scoped_logger.exception("Database schema missing during %s.", action)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The application database is not fully initialized yet. Please run migrations.",
        ) from exc

    if isinstance(exc, OperationalError):
        scoped_logger.exception("Database connection failure during %s.", action)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The database is temporarily unavailable. Please try again shortly.",
        ) from exc

    if isinstance(exc, SQLAlchemyError):
        scoped_logger.exception("Database error during %s.", action)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A database error prevented this request. Please try again shortly.",
        ) from exc

    logger.exception("Unexpected non-database error during %s.", action)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred.",
    ) from exc
