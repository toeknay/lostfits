from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.routes import admin, example, fits, health, killmails

app = FastAPI(default_response_class=ORJSONResponse, title="LostFits API", version="0.1.0")

app.include_router(health.router, tags=["health"])
app.include_router(example.router, tags=["example"])
app.include_router(killmails.router, tags=["killmails"])
app.include_router(fits.router, tags=["fits"])
app.include_router(admin.router, tags=["admin"])


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "lostfits-api", "status": "ok"}
