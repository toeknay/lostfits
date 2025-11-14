"""Background tasks for ingesting killmail data."""

import os
from datetime import datetime

from loguru import logger
from redis import Redis
from rq import Queue
from sqlalchemy.exc import IntegrityError

from app.clients.esi import ESIClient
from app.clients.zkillboard import ZKillboardClient
from app.db import SessionLocal
from app.models import Fit, ItemType, KillmailRaw
from app.utils.fit_parser import calculate_fit_signature, parse_fitting_from_killmail

# Redis connection for RQ
redis = Redis.from_url(os.environ.get("REDIS_URL", "redis://redis:6379/0"))
q = Queue("default", connection=redis)


def enqueue_killmail_fetch() -> None:
    """Enqueue a task to fetch and process a single killmail."""
    job = q.enqueue(fetch_and_store_killmail, job_timeout="5m")
    logger.info(f"Enqueued killmail fetch job: {job.id}")


def fetch_and_store_killmail() -> str:
    """
    Fetch a killmail from zKillboard RedisQ and store it in the database.

    Returns:
        str: Status message
    """
    with ZKillboardClient() as zkill_client:
        package = zkill_client.fetch_killmail()

        if package is None:
            return "Queue empty, no killmail to process"

        # Extract killmail data from package
        killmail_id = package.get("killID")
        killmail_hash = package.get("zkb", {}).get("hash")
        killmail_data = package.get("killmail", {})

        if not killmail_id or not killmail_hash:
            logger.error("Invalid package: missing killmail_id or hash")
            return "Error: Invalid killmail package"

        # Parse killmail details
        kill_time_str = killmail_data.get("killmail_time")
        kill_time = (
            datetime.fromisoformat(kill_time_str.replace("Z", "+00:00")) if kill_time_str else None
        )

        solar_system_id = killmail_data.get("solar_system_id")
        victim = killmail_data.get("victim", {})
        victim_ship_type_id = victim.get("ship_type_id")

        # Store in database
        db = SessionLocal()
        try:
            killmail_raw = KillmailRaw(
                killmail_id=killmail_id,
                killmail_hash=killmail_hash,
                kill_time=kill_time,
                solar_system_id=solar_system_id,
                victim_ship_type_id=victim_ship_type_id,
                json=package,  # Store the full package
            )
            db.add(killmail_raw)
            db.flush()  # Flush to get the killmail_id

            # Parse and store fitting
            fitting = parse_fitting_from_killmail(killmail_data)
            if fitting:
                fit_signature = calculate_fit_signature(
                    fitting["ship_type_id"], fitting["item_type_ids"]
                )

                fit = Fit(
                    killmail_id=killmail_id,
                    ship_type_id=fitting["ship_type_id"],
                    fit_signature=fit_signature,
                    slot_counts=fitting["slot_counts"],
                )
                db.add(fit)
                logger.debug(f"Parsed and stored fit for killmail {killmail_id}")

            db.commit()
            logger.info(f"Stored killmail {killmail_id} in database")
            return f"Success: Stored killmail {killmail_id}"

        except IntegrityError:
            db.rollback()
            logger.debug(f"Killmail {killmail_id} already exists in database")
            return f"Skipped: Killmail {killmail_id} already exists"

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store killmail {killmail_id}: {e}")
            raise

        finally:
            db.close()


def enqueue_item_type_seed(type_id: int) -> None:
    """
    Enqueue a task to fetch and store an item type from ESI.

    Args:
        type_id: The EVE item type ID to fetch
    """
    job = q.enqueue(fetch_and_store_item_type, type_id, job_timeout="2m")
    logger.info(f"Enqueued item type seed job for type_id {type_id}: {job.id}")


def enqueue_batch_item_type_seed(type_ids: list[int]) -> None:
    """
    Enqueue tasks to seed multiple item types from ESI.

    Args:
        type_ids: List of EVE item type IDs to fetch
    """
    for type_id in type_ids:
        job = q.enqueue(fetch_and_store_item_type, type_id, job_timeout="2m")
        logger.info(f"Enqueued item type seed job for type_id {type_id}: {job.id}")


def seed_types_from_killmails() -> str:
    """
    Seed item types from all killmails in the database.
    Extracts victim ship types and all items from killmail JSON.

    Returns:
        str: Status message with count of types queued
    """
    db = SessionLocal()
    try:
        # Get all unique victim ship type IDs
        ship_types = (
            db.query(KillmailRaw.victim_ship_type_id)
            .filter(KillmailRaw.victim_ship_type_id.isnot(None))
            .distinct()
            .all()
        )
        ship_type_ids = {row[0] for row in ship_types}

        # Get all killmails and extract item type IDs from their JSON
        killmails = db.query(KillmailRaw).all()
        item_type_ids = set()

        for km in killmails:
            if not km.json or "killmail" not in km.json:
                continue

            killmail_data = km.json.get("killmail", {})
            victim = killmail_data.get("victim", {})

            # Extract items from victim's fit
            items = victim.get("items", [])
            for item in items:
                item_type_id = item.get("item_type_id")
                if item_type_id:
                    item_type_ids.add(item_type_id)

        # Combine ship types and item types
        all_type_ids = ship_type_ids | item_type_ids

        # Check which types we already have
        existing_types = db.query(ItemType.type_id).filter(ItemType.type_id.in_(all_type_ids)).all()
        existing_type_ids = {row[0] for row in existing_types}

        # Queue only missing types
        missing_type_ids = all_type_ids - existing_type_ids

        logger.info(
            f"Found {len(all_type_ids)} unique types, {len(existing_type_ids)} already in DB, "
            f"queuing {len(missing_type_ids)} new types"
        )

        # Enqueue jobs for missing types
        for type_id in missing_type_ids:
            q.enqueue(fetch_and_store_item_type, type_id, job_timeout="2m")

        return (
            f"Queued {len(missing_type_ids)} item types for seeding "
            f"({len(existing_type_ids)} already existed)"
        )

    finally:
        db.close()


def fetch_and_store_item_type(type_id: int) -> str:
    """
    Fetch item type data from ESI and store it in the database.

    Args:
        type_id: The EVE item type ID

    Returns:
        str: Status message
    """
    with ESIClient() as esi_client:
        type_data = esi_client.get_type(type_id)

        if type_data is None:
            return f"Type {type_id} not found in ESI"

        # Extract relevant fields
        name = type_data.get("name", "Unknown")
        group_id = type_data.get("group_id")
        category_id = type_data.get("category_id")

        # Try to determine slot hint from dogma attributes if available
        # For now, we'll leave it as None and can enhance later
        slot_hint = None

        # Store in database
        db = SessionLocal()
        try:
            item_type = ItemType(
                type_id=type_id,
                name=name,
                group_id=group_id,
                category_id=category_id,
                slot_hint=slot_hint,
            )
            db.add(item_type)
            db.commit()
            logger.info(f"Stored item type {type_id} ({name}) in database")
            return f"Success: Stored item type {type_id} ({name})"

        except IntegrityError:
            db.rollback()
            logger.debug(f"Item type {type_id} already exists in database")
            return f"Skipped: Item type {type_id} already exists"

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store item type {type_id}: {e}")
            raise

        finally:
            db.close()
