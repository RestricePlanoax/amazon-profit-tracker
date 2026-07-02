from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.debug import router as debug_router
from app.api.demo import router as demo_router
from app.api.integrations import router as integrations_router
from app.api.metrics import router as metrics_router
from app.api.products import router as products_router
from app.api.uploads import router as uploads_router
from app.core.config import settings


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db_context = settings.database_log_context
    logger.info(
        "Database runtime selected: source=%s host=%s database=%s scheme=%s sslmode=%s",
        db_context["source"],
        db_context["host"],
        db_context["database"],
        db_context["scheme"],
        db_context["sslmode"],
    )
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="CSV-first SaaS MVP for Amazon seller profit tracking.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(debug_router)
app.include_router(integrations_router)
app.include_router(uploads_router)
app.include_router(dashboard_router)
app.include_router(demo_router)
app.include_router(metrics_router)
app.include_router(products_router)
app.include_router(analytics_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
