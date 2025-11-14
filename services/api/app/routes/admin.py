"""Admin API routes for managing data ingestion."""

from datetime import date
from typing import Any

from fastapi import APIRouter, Query

from app.tasks.aggregate import aggregate_all_historical_data, aggregate_fits_daily
from app.tasks.ingest import q, seed_types_from_killmails

router = APIRouter()


@router.post("/api/admin/seed-types")
def trigger_type_seeding() -> dict[str, Any]:
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
def get_queue_stats() -> dict[str, Any]:
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
def trigger_full_aggregation() -> dict[str, Any]:
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
