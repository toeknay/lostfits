"""Background tasks for aggregating fit data."""

from datetime import date, datetime, timedelta

from loguru import logger
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from app.db import SessionLocal
from app.models import Fit, FitAggregateDaily, KillmailRaw


def aggregate_fits_daily(target_date: date | None = None) -> str:
    """
    Aggregate fits for a specific date.
    Counts losses by ship type and fit signature, stores in fit_aggregate_daily.

    Args:
        target_date: Date to aggregate (defaults to yesterday)

    Returns:
        str: Status message
    """
    if target_date is None:
        # Default to yesterday (since today's data is still coming in)
        target_date = (datetime.utcnow() - timedelta(days=1)).date()

    db = SessionLocal()
    try:
        logger.info(f"Starting daily fit aggregation for {target_date}")

        # Query fits for the target date, grouped by ship and signature
        # Join with killmail_raw to get kill_time
        aggregates = (
            db.query(
                Fit.ship_type_id,
                Fit.fit_signature,
                func.count(Fit.fit_id).label("loss_count"),
            )
            .join(KillmailRaw, Fit.killmail_id == KillmailRaw.killmail_id)
            .filter(func.date(KillmailRaw.kill_time) == target_date)
            .group_by(Fit.ship_type_id, Fit.fit_signature)
            .all()
        )

        if not aggregates:
            logger.info(f"No fits found for {target_date}")
            return f"No data to aggregate for {target_date}"

        # Use PostgreSQL's INSERT ... ON CONFLICT to upsert
        for ship_type_id, fit_signature, loss_count in aggregates:
            stmt = insert(FitAggregateDaily).values(
                date=target_date,
                ship_type_id=ship_type_id,
                fit_signature=fit_signature,
                loss_count=loss_count,
            )

            # On conflict, update the loss_count and last_updated
            stmt = stmt.on_conflict_do_update(
                index_elements=["date", "ship_type_id", "fit_signature"],
                set_={
                    "loss_count": stmt.excluded.loss_count,
                    "last_updated": func.now(),
                },
            )

            db.execute(stmt)

        db.commit()
        logger.info(
            f"Aggregated {len(aggregates)} unique fits for {target_date} "
            f"(total {sum(agg[2] for agg in aggregates)} losses)"
        )
        return f"Aggregated {len(aggregates)} fits for {target_date}"

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to aggregate fits for {target_date}: {e}")
        raise

    finally:
        db.close()


def aggregate_fits_date_range(start_date: date, end_date: date) -> str:
    """
    Aggregate fits for a date range.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        str: Status message
    """
    current_date = start_date
    aggregated_days = 0

    while current_date <= end_date:
        try:
            aggregate_fits_daily(current_date)
            aggregated_days += 1
        except Exception as e:
            logger.error(f"Failed to aggregate {current_date}: {e}")

        current_date += timedelta(days=1)

    return f"Aggregated {aggregated_days} days from {start_date} to {end_date}"


def aggregate_all_historical_data() -> str:
    """
    Aggregate all historical fit data from the database.
    Useful for backfilling when first implementing aggregations.

    Returns:
        str: Status message
    """
    db = SessionLocal()
    try:
        # Find the earliest and latest kill times
        earliest = (
            db.query(func.min(KillmailRaw.kill_time))
            .filter(KillmailRaw.kill_time.isnot(None))
            .scalar()
        )
        latest = (
            db.query(func.max(KillmailRaw.kill_time))
            .filter(KillmailRaw.kill_time.isnot(None))
            .scalar()
        )

        if not earliest or not latest:
            return "No killmail data found"

        start_date = earliest.date()
        end_date = latest.date()

        logger.info(f"Aggregating historical data from {start_date} to {end_date}")
        return aggregate_fits_date_range(start_date, end_date)

    finally:
        db.close()
