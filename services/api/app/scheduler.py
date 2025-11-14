"""APScheduler daemon for periodic task execution."""

import asyncio
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from redis import Redis
from rq import Queue

from app.tasks.aggregate import aggregate_fits_daily
from app.tasks.ingest import enqueue_killmail_fetch, seed_types_from_killmails


async def main() -> None:
    """Run the scheduler daemon."""
    logger.info("Starting LostFits scheduler")

    sched = AsyncIOScheduler(timezone="UTC")

    # Fetch killmails from zKillboard every 10 seconds
    # RedisQ has a rate limit of ~1 request per second, so 10s is safe
    sched.add_job(
        enqueue_killmail_fetch,
        "interval",
        seconds=10,
        id="fetch_killmails",
        max_instances=1,  # Prevent overlapping jobs
    )

    # Seed new item types daily at 3 AM UTC
    # This discovers any new ships/modules from killmails we've ingested
    redis = Redis.from_url(os.environ.get("REDIS_URL", "redis://redis:6379/0"))
    q = Queue("default", connection=redis)

    def enqueue_item_type_seeding() -> None:
        """Enqueue the item type seeding task."""
        job = q.enqueue(seed_types_from_killmails, job_timeout="30m")
        logger.info(f"Enqueued daily item type seeding job: {job.id}")

    sched.add_job(
        enqueue_item_type_seeding,
        "cron",
        hour=3,
        minute=0,
        id="seed_item_types_daily",
        max_instances=1,
    )

    # Aggregate fits daily at 4 AM UTC (after item type seeding)
    # This powers the /api/fits/popular endpoint
    def enqueue_daily_aggregation() -> None:
        """Enqueue the daily aggregation task."""
        job = q.enqueue(aggregate_fits_daily, job_timeout="30m")
        logger.info(f"Enqueued daily aggregation job: {job.id}")

    sched.add_job(
        enqueue_daily_aggregation,
        "cron",
        hour=4,
        minute=0,
        id="aggregate_fits_daily",
        max_instances=1,
    )

    sched.start()
    logger.info(
        "Scheduler started:\n"
        "  - Fetching killmails every 10 seconds\n"
        "  - Seeding item types daily at 03:00 UTC\n"
        "  - Aggregating fits daily at 04:00 UTC"
    )

    # Keep the scheduler running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
