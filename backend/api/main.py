from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.debug_routes import router as debug_router
from api.observability import request_logging_middleware
from api.routes_v2 import router as v2_router
from api.geo.nearby_routes import router as nearby_router
from api.health import router as health_router
from api.routes_metrics import router as metrics_router
from api.internal_routes.internal import router as status_router
from api.internal_routes.jobs import router as jobs_router

# Application lifecycle

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup / shutdown lifecycle.

    All side-effectful initialization MUST happen here.
    """
    logging.getLogger("gymdb" ).info("GymDB API starting up")

    yield   # application runs here

    logging.getLogger("gymdb").info("GymDB API shutting down")

# Application

app = FastAPI(
    title="GymDB API",
    version="1.0.0",
    description="Gym intelligence built on OpenStreetMap",
    response_model_exclude_none=True,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "gyms", "description": "Gym discovery and filtering"},
        {"name": "embeddings", "descripton": "Vector embeddings"},
        {"name": "health", "description": "Service health checks"},
        {"name": "debug", "description": "Inference inspection and audits"},
        {"name": "internal", "description": "Administrative and ops endpoints"},
    ],
)

# Logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# Middleware

app.middleware("http")(request_logging_middleware)

# Routers

# Public API
app.include_router(nearby_router)
app.include_router(v2_router)
app.include_router(metrics_router)

# Internal / ops (fully gated)
app.include_router(
    status_router,
    prefix="/internal",
    tags=["internal"],
)
app.include_router(jobs_router)

# Infra
app.include_router(health_router)
app.include_router(debug_router)