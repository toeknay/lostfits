from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.routes import admin, example, fits, health, killmails

app = FastAPI(default_response_class=ORJSONResponse, title="LostFits API", version="0.1.0")

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(example.router, tags=["example"])
app.include_router(killmails.router, tags=["killmails"])
app.include_router(fits.router, tags=["fits"])
app.include_router(admin.router, tags=["admin"])


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "lostfits-api", "status": "ok"}
