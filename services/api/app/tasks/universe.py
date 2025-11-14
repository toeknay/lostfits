"""Universe data seeding tasks for fetching regions, constellations, and solar systems from ESI."""

import httpx
from loguru import logger
from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.db import get_db
from app.models import Constellation, Region, SolarSystem

# Redis queue setup
redis_conn = Redis.from_url(settings.redis_url)
q = Queue("default", connection=redis_conn)

# ESI HTTP client with rate limiting
client = httpx.Client(
    timeout=30.0,
    headers={"User-Agent": settings.esi_user_agent},
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_esi(url: str) -> dict | list:
    """Fetch data from ESI with retry logic."""
    resp = client.get(url)
    resp.raise_for_status()
    return resp.json()


def seed_universe_from_esi() -> None:
    """
    Seed regions, constellations, and solar systems from ESI.
    This is the main task that orchestrates the seeding process.

    Note: This will take several minutes due to ESI rate limiting.
    """
    logger.info("Starting universe data seeding from ESI")

    db: Session = next(get_db())
    try:
        # Step 1: Seed regions
        logger.info("Fetching regions from ESI")
        region_ids = fetch_esi("https://esi.evetech.net/latest/universe/regions/")
        logger.info(f"Found {len(region_ids)} regions to seed")

        for region_id in region_ids:
            try:
                # Check if already exists
                existing = db.query(Region).filter(Region.region_id == region_id).first()
                if existing:
                    continue

                region_data = fetch_esi(
                    f"https://esi.evetech.net/latest/universe/regions/{region_id}/"
                )
                region = Region(region_id=region_id, name=region_data["name"])
                db.add(region)
                db.commit()
                logger.debug(f"Seeded region: {region.name} ({region_id})")
            except Exception as e:
                logger.error(f"Failed to seed region {region_id}: {e}")
                db.rollback()

        logger.info("Regions seeding complete")

        # Step 2: Seed constellations
        logger.info("Fetching constellations from ESI")
        constellation_ids = fetch_esi("https://esi.evetech.net/latest/universe/constellations/")
        logger.info(f"Found {len(constellation_ids)} constellations to seed")

        for constellation_id in constellation_ids:
            try:
                # Check if already exists
                existing = (
                    db.query(Constellation)
                    .filter(Constellation.constellation_id == constellation_id)
                    .first()
                )
                if existing:
                    continue

                constellation_data = fetch_esi(
                    f"https://esi.evetech.net/latest/universe/constellations/{constellation_id}/"
                )
                constellation = Constellation(
                    constellation_id=constellation_id,
                    name=constellation_data["name"],
                    region_id=constellation_data["region_id"],
                )
                db.add(constellation)
                db.commit()
                logger.debug(f"Seeded constellation: {constellation.name} ({constellation_id})")
            except Exception as e:
                logger.error(f"Failed to seed constellation {constellation_id}: {e}")
                db.rollback()

        logger.info("Constellations seeding complete")

        # Step 3: Seed solar systems
        logger.info("Fetching solar systems from ESI")
        system_ids = fetch_esi("https://esi.evetech.net/latest/universe/systems/")
        logger.info(f"Found {len(system_ids)} solar systems to seed")

        for system_id in system_ids:
            try:
                # Check if already exists
                existing = db.query(SolarSystem).filter(SolarSystem.system_id == system_id).first()
                if existing:
                    continue

                system_data = fetch_esi(
                    f"https://esi.evetech.net/latest/universe/systems/{system_id}/"
                )
                solar_system = SolarSystem(
                    system_id=system_id,
                    name=system_data["name"],
                    constellation_id=system_data["constellation_id"],
                )
                db.add(solar_system)
                db.commit()
                logger.debug(f"Seeded solar system: {solar_system.name} ({system_id})")
            except Exception as e:
                logger.error(f"Failed to seed solar system {system_id}: {e}")
                db.rollback()

        logger.info("Solar systems seeding complete")
        logger.info("Universe data seeding finished successfully!")

    except Exception as e:
        logger.error(f"Universe seeding failed: {e}")
        raise
    finally:
        db.close()
