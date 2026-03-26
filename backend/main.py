from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.errors import register_error_handlers
from core.logging import setup_logging

setup_logging()

app = FastAPI(
    title="WealthPilot API",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

# ─── Routers ──────────────────────────────────────────────────────────────────
# Afegir nous mòduls aquí. El reste del codi no es toca mai.
#
# from modules.portfolio.router import router as portfolio_router
# app.include_router(portfolio_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "env": settings.ENV,
    }


@app.get("/api/v1", tags=["system"])
async def api_root():
    return {
        "version": "v1",
        "modules": [],  # Auto-populated as modules are added
    }
