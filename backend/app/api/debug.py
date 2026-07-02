from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import engine
from app.core.database_errors import is_missing_table_error


router = APIRouter(prefix="/debug", tags=["debug"])
REQUIRED_TABLES = ("users", "stores")


def _require_debug_token(provided_token: str | None) -> None:
    expected_token = settings.debug_admin_token
    if not expected_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debug endpoint disabled.")
    if provided_token != expected_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid debug token.")


@router.get("/db")
def debug_database(x_debug_token: str | None = Header(default=None)) -> dict[str, object]:
    _require_debug_token(x_debug_token)

    database = {
        "source": settings.resolved_database_config.source,
        "host": settings.resolved_database_config.host,
        "database": settings.resolved_database_config.database,
        "scheme": settings.resolved_database_config.scheme,
        "sslmode": settings.resolved_database_config.sslmode,
    }

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            table_names = set(inspect(connection).get_table_names())
    except SQLAlchemyError as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "ok": False,
                "database": database,
                "checks": {
                    "select_1": False,
                    "required_tables": {table: False for table in REQUIRED_TABLES},
                },
                "error": {
                    "type": "missing_table" if is_missing_table_error(exc) else "database_error",
                    "message": (
                        "Required tables are missing. Run `python -m alembic upgrade head`."
                        if is_missing_table_error(exc)
                        else "Database connection or query failed. Check env vars, password, SSL, and connectivity."
                    ),
                },
            },
        )

    return {
        "ok": True,
        "database": database,
        "checks": {
            "select_1": True,
            "required_tables": {table: table in table_names for table in REQUIRED_TABLES},
        },
    }
