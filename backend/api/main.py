from fastapi import FastAPI
from api.routes import router
from api.debug_routes import router as debug_router

app = FastAPI(
    title="GymDB API",
    version="1.0.0",
    description="Gym intelligence built on OpenStreetMap"
)

app.include_router(router, prefix="/v1")
app.include_router(debug_router)

@app.get("/healthz")
def health_check():
    return {"status": "ok"}