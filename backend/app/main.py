from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.demo import router as demo_router
from app.api.integrations import router as integrations_router
from app.api.metrics import router as metrics_router
from app.api.products import router as products_router
from app.api.uploads import router as uploads_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="CSV-first SaaS MVP for Amazon seller profit tracking.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(integrations_router)
app.include_router(uploads_router)
app.include_router(dashboard_router)
app.include_router(demo_router)
app.include_router(metrics_router)
app.include_router(products_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
