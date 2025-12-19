from fastapi import FastAPI
import logging

from api.routes import router
from api.debug_routes import router as debug_router
from api.observability import request_logging_middleware
from api.routes_v2 import router as v2_router
from api.nearby_routes import router as nearby_router
from api.health import router as health_router

app = FastAPI(
    title="GymDB API",
    version="1.0.0",
    description="Gym intelligence built on OpenStreetMap",
    response_model_exclude_none=True,
    openapi_tags=[
        {"name": "gyms", "description": "Gym discovery and filtering"},
        {"name": "embeddings", "descripton": "Vector embeddings"},
        {"name": "health", "description": "Service health checks"},
        {"name": "debug", "description": "Inference inspection and audits"},
    ],
)

logging.basicConfig(level=logging.INFO)

app.middleware("http")(request_logging_middleware)

# API routes
app.include_router(router, prefix="/v1")
app.include_router(v2_router)
app.include_router(nearby_router)

# Infra / ops
app.include_router(health_router)
app.include_router(debug_router)