"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import (
    auth,
    dashboard,
    smtp_accounts,
    emails,
    templates,
    recipients,
    history,
    system,
)

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SMTP Mail Management Platform — REST API",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.ALLOWED_ORIGINS) if isinstance(settings.ALLOWED_ORIGINS, (list, tuple)) else [str(settings.ALLOWED_ORIGINS)],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Router ────────────────────────────────────────────────────────────────
PREFIX = settings.API_V1_PREFIX

app.include_router(auth.router, prefix=f"{PREFIX}/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix=f"{PREFIX}/dashboard", tags=["Dashboard"])
app.include_router(smtp_accounts.router, prefix=f"{PREFIX}/smtp-accounts", tags=["SMTP Accounts"])
app.include_router(emails.router, prefix=f"{PREFIX}/emails", tags=["Emails"])
app.include_router(templates.router, prefix=f"{PREFIX}/templates", tags=["Templates"])
app.include_router(recipients.router, prefix=f"{PREFIX}/contacts", tags=["Contacts"])
app.include_router(history.router, prefix=f"{PREFIX}/history", tags=["History"])
app.include_router(system.router, prefix=f"{PREFIX}", tags=["System"])
app.include_router(system.router, tags=["Health"])


@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse(
        {"message": f"Welcome to {settings.APP_NAME}", "version": settings.APP_VERSION}
    )
