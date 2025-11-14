from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routes import admin, example, fits, health, killmails

# Rate limiter for API protection
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(default_response_class=ORJSONResponse, title="LostFits API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - configurable via CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
