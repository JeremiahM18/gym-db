from fastapi import FastAPI
from api.routes import router


app = FastAPI(
    title="GymDB API",
    version="1.0.0",
    description="Gym intelligence built on OpenStreetMap"
)

app.include_router(router, prefix="/v1")

@app.get("/healthz")
def health_check():
    return {"status": "ok"}