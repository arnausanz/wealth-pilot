import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.db import AsyncSessionLocal
from core.errors import register_error_handlers
from core.logging import setup_logging
from modules.market import service as market_service
from modules.market.router import router as market_router
from modules.networth.router import router as networth_router
from modules.portfolio.router import router as portfolio_router
from modules.sync.router import router as sync_router

logger = logging.getLogger(__name__)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run gap fill on startup so the BD is always up-to-date when the server starts."""
    logger.info("Startup: running market gap fill...")
    try:
        async with AsyncSessionLocal() as db:
            result = await market_service.fill_all_gaps(db)
        logger.info(
            "Startup gap fill done: %d rows inserted, %d assets updated",
            result.rows_inserted, len(result.assets_updated),
        )
    except Exception as exc:
        # Gap fill failure must never prevent the server from starting
        logger.error("Startup gap fill failed (non-fatal): %s", exc)
    yield


app = FastAPI(
    lifespan=lifespan,
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

app.include_router(market_router, prefix="/api/v1")
app.include_router(networth_router)
app.include_router(portfolio_router)
app.include_router(sync_router, prefix="/api/v1")


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
