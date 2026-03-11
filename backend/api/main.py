from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

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

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    """
    Global HTTP exception handler.

    This enforces a stable error response shape for all API consumers.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": (
                    exc.detail
                    if isinstance(exc.detail, (dict, list))
                    else {"detail": exc.detail}
                )
            }
        },
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    """
    Catch-all handler for unexpected server errors.
    """
    logging.getLogger("gymdb").exception(
        "Unhandled exception",
        extra={"path": request.url.path},
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
            }
        },
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
app.include_router(
    metrics_router,
    include_in_schema=False,
)

# Internal / ops (fully gated)
app.include_router(
    status_router,
    prefix="/internal",
    tags=["internal"],
)
app.include_router(
    jobs_router,
    include_in_schema=False,
)

# Infra
app.include_router(health_router)
app.include_router(
    debug_router,
    include_in_schema=False,
)

