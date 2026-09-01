"""
Enterprise AI Research Agent — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.storage.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup + shutdown."""
    setup_logging()
    logging.getLogger("research_agent").info("Starting Research Agent API...")

    # Create all DB tables on startup
    Base.metadata.create_all(bind=engine)
    logging.getLogger("research_agent").info("Database tables ready.")

    yield

    logging.getLogger("research_agent").info("Shutting down Research Agent API.")


app = FastAPI(
    title="Enterprise AI Research Agent",
    description="A structured research intelligence platform for the MODUS Enterprise AI Build Challenge.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.routes import research, sessions, knowledge, query, health  # noqa: E402

app.include_router(research.router, tags=["Research"])
app.include_router(sessions.router, tags=["Sessions"])
app.include_router(knowledge.router, tags=["Knowledge"])
app.include_router(query.router, tags=["Query"])
app.include_router(health.router, tags=["Health"])