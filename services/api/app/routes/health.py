from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter()


@router.get("/healthz")
def healthz(db: Session = Depends(get_db)) -> dict[str, str]:
    """Health check endpoint that verifies database connectivity."""
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
