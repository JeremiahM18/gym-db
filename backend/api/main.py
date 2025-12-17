from fastapi import FastAPI
from api.routes import router
from api.debug_routes import router as debug_router
import logging
from api.observability import request_logging_middleware

app = FastAPI(
    title="GymDB API",
    version="1.0.0",
    description="Gym intelligence built on OpenStreetMap",
    response_model_exclude_none=True,
    openapi_tags=[
        {"name": "gyms", "description": "Gym discovery and filtering"},
        {"name": "debug", "description": "Inference inspection and audits"},
    ],
)

logging.basicConfig(level=logging.INFO)

app.include_router(router, prefix="/v1")
app.include_router(debug_router)
app.middleware("http")(request_logging_middleware)

@app.get("/healthz")
def health_check():
    return {"status": "ok"}