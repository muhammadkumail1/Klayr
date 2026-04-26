"""
FastAPI application factory — init, middleware, router registration, CORS.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.config import get_settings
from api.routes import feedback, health, plan, run, optimize, collaborators, reviews, report, literature_search

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

settings = get_settings()

logging.basicConfig(
    stream=sys.stdout,
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title="The AI Scientist",
        description=(
            "Transforms natural language scientific hypotheses into complete, "
            "operationally realistic experiment plans. "
            "Fulcrum Science × Hack-Nation Hackathon Project."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ------------------------------------------------------------------
    # Middleware
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    app.include_router(health.router, tags=["ops"])
    app.include_router(run.router, tags=["pipeline"])
    app.include_router(plan.router, tags=["plans"])
    app.include_router(feedback.router, tags=["feedback"])
    app.include_router(optimize.router, tags=["cost-optimizer"])
    app.include_router(collaborators.router, tags=["collaboration"])
    app.include_router(reviews.router, tags=["reviews"])
    app.include_router(report.router, tags=["reports"])
    app.include_router(literature_search.router, tags=["literature"])

    # ------------------------------------------------------------------
    # Static Files and Root Route
    # ------------------------------------------------------------------
    # Serve index.html at root
    @app.get("/")
    async def serve_root():
        public_dir = Path(__file__).parent.parent.parent / "public"
        index_file = public_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not available"}

    # Mount public folder for static assets
    public_dir = Path(__file__).parent.parent.parent / "public"
    if public_dir.exists():
        app.mount("/static", StaticFiles(directory=str(public_dir)), name="static")

    # ------------------------------------------------------------------
    # Startup / shutdown events
    # ------------------------------------------------------------------
    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info("AI Scientist API starting up (env=%s)", settings.app_env)

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("AI Scientist API shutting down")

    return app


app = create_app()
