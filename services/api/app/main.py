from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from app.routes import health, example

app = FastAPI(default_response_class=ORJSONResponse, title="LostFits API", version="0.1.0")

app.include_router(health.router, tags=["health"])
app.include_router(example.router, tags=["example"])

@app.get("/")
def root():
    return {"service": "lostfits-api", "status": "ok"}
