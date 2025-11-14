"""Admin API routes for managing data ingestion."""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import APIKeyHeader

from app.config import settings
from app.tasks.aggregate import aggregate_all_historical_data, aggregate_fits_daily
from app.tasks.ingest import q, seed_types_from_killmails
from app.tasks.universe import seed_universe_from_esi

router = APIRouter()

# Simple API key authentication for admin endpoints
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_admin_key(api_key: str | None = Depends(api_key_header)) -> None:
    """
    Verify that the provided API key matches the configured admin key.

    Raises:
        HTTPException: If API key is missing or invalid
    """
    # If no admin key is configured, allow access (development mode)
    if not settings.admin_api_key:
        return

    if not api_key or api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )


@router.post("/api/admin/seed-types")
def trigger_type_seeding(_: None = Depends(verify_admin_key)) -> dict[str, Any]:
    """
    Trigger seeding of item types from existing killmails.
    This will queue jobs to fetch ship and module names from ESI.

    Returns:
        dict with job status and counts
    """
    job = q.enqueue(seed_types_from_killmails, job_timeout="10m")

    return {
        "status": "queued",
        "job_id": job.id,
        "message": "Item type seeding job has been queued. Check RQ dashboard for progress.",
    }


@router.get("/api/admin/queue-stats")
def get_queue_stats(_: None = Depends(verify_admin_key)) -> dict[str, Any]:
    """
    Get Redis queue statistics.

    Returns:
        dict with queue stats
    """
    return {
        "queued_jobs": len(q),
        "started_jobs": q.started_job_registry.count,
        "finished_jobs": q.finished_job_registry.count,
        "failed_jobs": q.failed_job_registry.count,
    }


@router.post("/api/admin/aggregate-daily")
def trigger_daily_aggregation(
    target_date: date | None = Query(default=None, description="Date to aggregate (YYYY-MM-DD)"),
    _: None = Depends(verify_admin_key),
) -> dict[str, Any]:
    """
    Trigger daily fit aggregation for a specific date.
    If no date provided, aggregates yesterday's data.

    Returns:
        dict with job status
    """
    job = q.enqueue(aggregate_fits_daily, target_date, job_timeout="10m")

    return {
        "status": "queued",
        "job_id": job.id,
        "target_date": target_date.isoformat() if target_date else "yesterday",
        "message": "Daily aggregation job has been queued.",
    }


@router.post("/api/admin/aggregate-all")
def trigger_full_aggregation(_: None = Depends(verify_admin_key)) -> dict[str, Any]:
    """
    Trigger aggregation of all historical data.
    This will backfill the fit_aggregate_daily table.

    Returns:
        dict with job status
    """
    job = q.enqueue(aggregate_all_historical_data, job_timeout="30m")

    return {
        "status": "queued",
        "job_id": job.id,
        "message": "Full historical aggregation job has been queued. This may take a while.",
    }


@router.post("/api/admin/seed-universe")
def trigger_universe_seeding(_: None = Depends(verify_admin_key)) -> dict[str, Any]:
    """
    Trigger seeding of universe data (regions, constellations, solar systems) from ESI.
    This will take several minutes due to ESI rate limiting (~8k solar systems).

    Returns:
        dict with job status
    """
    job = q.enqueue(seed_universe_from_esi, job_timeout="60m")

    return {
        "status": "queued",
        "job_id": job.id,
        "message": "Universe seeding job has been queued. This will take 10-15 minutes. Check RQ dashboard for progress.",
    }
