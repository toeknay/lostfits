"""API routes for viewing popular ship fittings."""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    Constellation,
    Fit,
    FitAggregateDaily,
    ItemType,
    KillmailRaw,
    Region,
    SolarSystem,
)
from app.utils.cache import cache_forever

router = APIRouter()


@router.get("/api/fits/popular")
def get_popular_fits(
    limit: int = Query(default=20, ge=1, le=100),
    days: int = Query(default=7, ge=1, le=90, description="Number of days to look back"),
    ship_type_ids: list[int] = Query(
        default=[], description="Filter by ship types (can specify multiple)"
    ),
    ship_mode: str = Query(default="include", description="Ship filter mode: include or exclude"),
    region_ids: list[int] = Query(
        default=[], description="Filter by regions (can specify multiple)"
    ),
    region_mode: str = Query(
        default="include", description="Region filter mode: include or exclude"
    ),
    constellation_ids: list[int] = Query(
        default=[], description="Filter by constellations (can specify multiple)"
    ),
    constellation_mode: str = Query(
        default="include", description="Constellation filter mode: include or exclude"
    ),
    solar_system_ids: list[int] = Query(
        default=[], description="Filter by solar systems (can specify multiple)"
    ),
    system_mode: str = Query(
        default="include", description="System filter mode: include or exclude"
    ),
    security_status: str | None = Query(
        default=None,
        description="Filter by security status: highsec, lowsec, nullsec, w-space, or abyssal",
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Get most popular ship fits based on recent losses.

    Args:
        limit: Number of fits to return
        days: Number of days to look back (default: 7)
        ship_type_ids: Optional list of ship types to include/exclude
        ship_mode: Mode for ship filter (include or exclude)
        region_ids: Optional list of regions to include/exclude
        region_mode: Mode for region filter (include or exclude)
        constellation_ids: Optional list of constellations to include/exclude
        constellation_mode: Mode for constellation filter (include or exclude)
        solar_system_ids: Optional list of solar systems to include/exclude
        system_mode: Mode for system filter (include or exclude)
        security_status: Optional filter by security status
        db: Database session

    Returns:
        dict with popular fits and their loss counts
    """
    # Calculate date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    # If we need location filtering, we must query from Fit table joined with KillmailRaw
    # Otherwise we can use the faster aggregated data
    if region_ids or constellation_ids or solar_system_ids or security_status:
        # Query individual fits and count them
        query = (
            db.query(
                Fit.ship_type_id,
                Fit.fit_signature,
                func.count(Fit.fit_id).label("total_losses"),
            )
            .join(KillmailRaw, Fit.killmail_id == KillmailRaw.killmail_id)
            .filter(func.date(KillmailRaw.kill_time) >= start_date)
            .filter(func.date(KillmailRaw.kill_time) <= end_date)
        )

        # Join universe tables if any location filters are provided
        needs_system_join = solar_system_ids or constellation_ids or region_ids
        needs_constellation_join = constellation_ids or region_ids

        if needs_system_join:
            query = query.join(SolarSystem, KillmailRaw.solar_system_id == SolarSystem.system_id)
        if needs_constellation_join:
            query = query.join(
                Constellation, SolarSystem.constellation_id == Constellation.constellation_id
            )

        # Filter by region if provided
        if region_ids:
            if region_mode == "exclude":
                query = query.filter(Constellation.region_id.notin_(region_ids))
            else:  # include mode
                query = query.filter(Constellation.region_id.in_(region_ids))

        # Filter by constellation if provided
        if constellation_ids:
            if constellation_mode == "exclude":
                query = query.filter(SolarSystem.constellation_id.notin_(constellation_ids))
            else:  # include mode
                query = query.filter(SolarSystem.constellation_id.in_(constellation_ids))

        # Filter by solar system if provided
        if solar_system_ids:
            if system_mode == "exclude":
                query = query.filter(KillmailRaw.solar_system_id.notin_(solar_system_ids))
            else:  # include mode
                query = query.filter(KillmailRaw.solar_system_id.in_(solar_system_ids))

        # Filter by security status if provided
        if security_status:
            # Build the location label to search for as a JSON array
            loc_label_json = f'["loc:{security_status}"]'
            # Use PostgreSQL's JSONB @> (contains) operator
            # This checks if zkb.labels contains the location string
            query = query.filter(
                text(f"(json::jsonb)->'zkb'->'labels' @> '{loc_label_json}'::jsonb")
            )

        query = query.group_by(Fit.ship_type_id, Fit.fit_signature)
    else:
        # Use aggregated data for better performance
        query = (
            db.query(
                FitAggregateDaily.ship_type_id,
                FitAggregateDaily.fit_signature,
                func.sum(FitAggregateDaily.loss_count).label("total_losses"),
            )
            .filter(FitAggregateDaily.date >= start_date)
            .filter(FitAggregateDaily.date <= end_date)
            .group_by(FitAggregateDaily.ship_type_id, FitAggregateDaily.fit_signature)
        )

    # Filter by ship type if provided (works for both query paths)
    if ship_type_ids:
        if region_ids or constellation_ids or solar_system_ids or security_status:
            if ship_mode == "exclude":
                query = query.filter(Fit.ship_type_id.notin_(ship_type_ids))
            else:  # include mode
                query = query.filter(Fit.ship_type_id.in_(ship_type_ids))
        else:
            if ship_mode == "exclude":
                query = query.filter(FitAggregateDaily.ship_type_id.notin_(ship_type_ids))
            else:  # include mode
                query = query.filter(FitAggregateDaily.ship_type_id.in_(ship_type_ids))

    # Order by total losses and limit
    popular_fits = query.order_by(desc("total_losses")).limit(limit).all()

    # Get ship names for the results
    result_ship_ids = {fit.ship_type_id for fit in popular_fits}
    ship_names = (
        db.query(ItemType.type_id, ItemType.name)
        .filter(ItemType.type_id.in_(result_ship_ids))
        .all()
    )
    ship_name_map = {type_id: name for type_id, name in ship_names}

    return {
        "days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "ship_type_filters": ship_type_ids,
        "ship_mode": ship_mode,
        "region_filters": region_ids,
        "region_mode": region_mode,
        "constellation_filters": constellation_ids,
        "constellation_mode": constellation_mode,
        "solar_system_filters": solar_system_ids,
        "system_mode": system_mode,
        "security_status_filter": security_status,
        "total_results": len(popular_fits),
        "fits": [
            {
                "ship_type_id": fit.ship_type_id,
                "ship_name": ship_name_map.get(fit.ship_type_id, "Unknown"),
                "fit_signature": fit.fit_signature,
                "total_losses": fit.total_losses,
            }
            for fit in popular_fits
        ],
    }


@router.get("/api/fits/{fit_signature}")
def get_fit_details(
    fit_signature: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Get details about a specific fit signature.
    Returns example killmails and fitted items.

    Args:
        fit_signature: The fit signature hash
        db: Database session

    Returns:
        dict with fit details and example killmails
    """
    # Get some example fits with this signature
    example_fits = (
        db.query(Fit, KillmailRaw)
        .join(KillmailRaw, Fit.killmail_id == KillmailRaw.killmail_id)
        .filter(Fit.fit_signature == fit_signature)
        .limit(5)
        .all()
    )

    if not example_fits:
        return {
            "fit_signature": fit_signature,
            "found": False,
            "message": "No fits found with this signature",
        }

    # Get ship info
    first_fit = example_fits[0].Fit
    ship_type = db.query(ItemType).filter(ItemType.type_id == first_fit.ship_type_id).first()

    # Extract items from the first example
    first_killmail_json = example_fits[0].KillmailRaw.json
    victim_items = []
    if first_killmail_json and "killmail" in first_killmail_json:
        killmail_data = first_killmail_json["killmail"]
        victim = killmail_data.get("victim", {})
        items = victim.get("items", [])

        # Get item names
        item_type_ids = {item.get("item_type_id") for item in items if item.get("item_type_id")}
        item_names = (
            db.query(ItemType.type_id, ItemType.name)
            .filter(ItemType.type_id.in_(item_type_ids))
            .all()
        )
        item_name_map = {type_id: name for type_id, name in item_names}

        # Build items list
        for item in items:
            type_id = item.get("item_type_id")
            if type_id:
                victim_items.append(
                    {
                        "type_id": type_id,
                        "name": item_name_map.get(type_id, "Unknown"),
                        "quantity": item.get("quantity_destroyed", 0)
                        + item.get("quantity_dropped", 0),
                        "flag": item.get("flag"),
                    }
                )

    # Count total occurrences
    total_count = (
        db.query(func.count(Fit.fit_id)).filter(Fit.fit_signature == fit_signature).scalar()
    )

    # Get location summary (top 3 security zones)
    security_summary_query = """
        SELECT
            CASE
                WHEN (km.json::jsonb)->'zkb'->'labels' @> '["loc:highsec"]'::jsonb THEN 'highsec'
                WHEN (km.json::jsonb)->'zkb'->'labels' @> '["loc:lowsec"]'::jsonb THEN 'lowsec'
                WHEN (km.json::jsonb)->'zkb'->'labels' @> '["loc:nullsec"]'::jsonb THEN 'nullsec'
                WHEN (km.json::jsonb)->'zkb'->'labels' @> '["loc:w-space"]'::jsonb THEN 'w-space'
                WHEN (km.json::jsonb)->'zkb'->'labels' @> '["loc:abyssal"]'::jsonb THEN 'abyssal'
                ELSE 'unknown'
            END AS security_type,
            COUNT(*) AS count
        FROM fit f
        JOIN killmail_raw km ON f.killmail_id = km.killmail_id
        WHERE f.fit_signature = :fit_signature
        GROUP BY security_type
        ORDER BY count DESC
        LIMIT 3
    """

    security_summary = db.execute(
        text(security_summary_query), {"fit_signature": fit_signature}
    ).fetchall()

    return {
        "fit_signature": fit_signature,
        "found": True,
        "ship_type_id": first_fit.ship_type_id,
        "ship_name": ship_type.name if ship_type else "Unknown",
        "slot_counts": first_fit.slot_counts,
        "total_occurrences": total_count,
        "fitted_items": victim_items,
        "location_summary": [
            {"security_type": row.security_type, "count": row.count} for row in security_summary
        ],
        "example_killmails": [
            {
                "killmail_id": fit.KillmailRaw.killmail_id,
                "kill_time": (
                    fit.KillmailRaw.kill_time.isoformat() if fit.KillmailRaw.kill_time else None
                ),
            }
            for fit in example_fits
        ],
    }


@router.get("/api/fits/ships/popular")
def get_popular_ships(
    limit: int = Query(default=20, ge=1, le=100),
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Get most commonly destroyed ships (aggregated across all fits).

    Args:
        limit: Number of ships to return
        days: Number of days to look back
        db: Database session

    Returns:
        dict with popular ships and their total loss counts
    """
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    # Query aggregated data grouped by ship type only
    popular_ships = (
        db.query(
            FitAggregateDaily.ship_type_id,
            func.sum(FitAggregateDaily.loss_count).label("total_losses"),
        )
        .filter(FitAggregateDaily.date >= start_date)
        .filter(FitAggregateDaily.date <= end_date)
        .group_by(FitAggregateDaily.ship_type_id)
        .order_by(desc("total_losses"))
        .limit(limit)
        .all()
    )

    # Get ship names
    ship_type_ids = {ship.ship_type_id for ship in popular_ships}
    ship_names = (
        db.query(ItemType.type_id, ItemType.name).filter(ItemType.type_id.in_(ship_type_ids)).all()
    )
    ship_name_map = {type_id: name for type_id, name in ship_names}

    return {
        "days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_results": len(popular_ships),
        "ships": [
            {
                "ship_type_id": ship.ship_type_id,
                "ship_name": ship_name_map.get(ship.ship_type_id, "Unknown"),
                "total_losses": ship.total_losses,
            }
            for ship in popular_ships
        ],
    }


@router.get("/api/fits/{fit_signature}/by-location")
def get_fit_by_location(
    fit_signature: str,
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Get location breakdown for a specific fit signature.
    Shows where this fit is being destroyed (systems and security zones).

    Args:
        fit_signature: The fit signature hash
        days: Number of days to look back (default: 30)
        db: Database session

    Returns:
        dict with location breakdown for this specific fit
    """
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    # Get top regions for this fit
    top_regions = (
        db.query(Region.region_id, Region.name, func.count(Fit.fit_id).label("loss_count"))
        .select_from(KillmailRaw)
        .join(Fit, KillmailRaw.killmail_id == Fit.killmail_id)
        .join(SolarSystem, KillmailRaw.solar_system_id == SolarSystem.system_id)
        .join(Constellation, SolarSystem.constellation_id == Constellation.constellation_id)
        .join(Region, Constellation.region_id == Region.region_id)
        .filter(Fit.fit_signature == fit_signature)
        .filter(func.date(KillmailRaw.kill_time) >= start_date)
        .filter(func.date(KillmailRaw.kill_time) <= end_date)
        .group_by(Region.region_id, Region.name)
        .order_by(desc("loss_count"))
        .limit(10)
        .all()
    )

    # Get top constellations for this fit
    top_constellations = (
        db.query(
            Constellation.constellation_id,
            Constellation.name,
            Region.name.label("region_name"),
            func.count(Fit.fit_id).label("loss_count"),
        )
        .select_from(KillmailRaw)
        .join(Fit, KillmailRaw.killmail_id == Fit.killmail_id)
        .join(SolarSystem, KillmailRaw.solar_system_id == SolarSystem.system_id)
        .join(Constellation, SolarSystem.constellation_id == Constellation.constellation_id)
        .join(Region, Constellation.region_id == Region.region_id)
        .filter(Fit.fit_signature == fit_signature)
        .filter(func.date(KillmailRaw.kill_time) >= start_date)
        .filter(func.date(KillmailRaw.kill_time) <= end_date)
        .group_by(Constellation.constellation_id, Constellation.name, Region.name)
        .order_by(desc("loss_count"))
        .limit(10)
        .all()
    )

    # Get top solar systems for this fit (with names!)
    top_systems = (
        db.query(
            SolarSystem.system_id,
            SolarSystem.name,
            Constellation.name.label("constellation_name"),
            Region.name.label("region_name"),
            func.count(Fit.fit_id).label("loss_count"),
        )
        .select_from(KillmailRaw)
        .join(Fit, KillmailRaw.killmail_id == Fit.killmail_id)
        .join(SolarSystem, KillmailRaw.solar_system_id == SolarSystem.system_id)
        .join(Constellation, SolarSystem.constellation_id == Constellation.constellation_id)
        .join(Region, Constellation.region_id == Region.region_id)
        .filter(Fit.fit_signature == fit_signature)
        .filter(func.date(KillmailRaw.kill_time) >= start_date)
        .filter(func.date(KillmailRaw.kill_time) <= end_date)
        .group_by(SolarSystem.system_id, SolarSystem.name, Constellation.name, Region.name)
        .order_by(desc("loss_count"))
        .limit(10)
        .all()
    )

    # Get security status breakdown for this fit
    security_breakdown_query = """
        SELECT
            CASE
                WHEN (km.json::jsonb)->'zkb'->'labels' @> '["loc:highsec"]'::jsonb THEN 'highsec'
                WHEN (km.json::jsonb)->'zkb'->'labels' @> '["loc:lowsec"]'::jsonb THEN 'lowsec'
                WHEN (km.json::jsonb)->'zkb'->'labels' @> '["loc:nullsec"]'::jsonb THEN 'nullsec'
                WHEN (km.json::jsonb)->'zkb'->'labels' @> '["loc:w-space"]'::jsonb THEN 'w-space'
                WHEN (km.json::jsonb)->'zkb'->'labels' @> '["loc:abyssal"]'::jsonb THEN 'abyssal'
                ELSE 'unknown'
            END AS security_type,
            COUNT(*) AS loss_count
        FROM fit f
        JOIN killmail_raw km ON f.killmail_id = km.killmail_id
        WHERE f.fit_signature = :fit_signature
            AND DATE(km.kill_time) >= :start_date
            AND DATE(km.kill_time) <= :end_date
        GROUP BY security_type
        ORDER BY loss_count DESC
    """

    security_breakdown = db.execute(
        text(security_breakdown_query),
        {"fit_signature": fit_signature, "start_date": start_date, "end_date": end_date},
    ).fetchall()

    # Get total count
    total_losses = (
        db.query(func.count(Fit.fit_id))
        .join(KillmailRaw, Fit.killmail_id == KillmailRaw.killmail_id)
        .filter(Fit.fit_signature == fit_signature)
        .filter(func.date(KillmailRaw.kill_time) >= start_date)
        .filter(func.date(KillmailRaw.kill_time) <= end_date)
        .scalar()
    )

    if total_losses == 0:
        return {
            "fit_signature": fit_signature,
            "found": False,
            "message": "No losses found for this fit in the specified time range",
        }

    return {
        "fit_signature": fit_signature,
        "found": True,
        "days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_losses": total_losses,
        "top_regions": [
            {
                "region_id": region.region_id,
                "name": region.name,
                "loss_count": region.loss_count,
                "percentage": round((region.loss_count / total_losses) * 100, 1),
            }
            for region in top_regions
        ],
        "top_constellations": [
            {
                "constellation_id": const.constellation_id,
                "name": const.name,
                "region_name": const.region_name,
                "loss_count": const.loss_count,
                "percentage": round((const.loss_count / total_losses) * 100, 1),
            }
            for const in top_constellations
        ],
        "top_solar_systems": [
            {
                "system_id": system.system_id,
                "name": system.name,
                "constellation_name": system.constellation_name,
                "region_name": system.region_name,
                "loss_count": system.loss_count,
                "percentage": round((system.loss_count / total_losses) * 100, 1),
            }
            for system in top_systems
        ],
        "security_breakdown": [
            {
                "security_type": row.security_type,
                "loss_count": row.loss_count,
                "percentage": round((row.loss_count / total_losses) * 100, 1),
            }
            for row in security_breakdown
        ],
    }


@router.get("/api/locations/popular")
def get_popular_locations(
    limit: int = Query(default=20, ge=1, le=100),
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Get most popular kill locations (solar systems and security zones).

    Args:
        limit: Number of systems to return
        days: Number of days to look back
        db: Database session

    Returns:
        dict with top solar systems and security status breakdown
    """
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    # Get top solar systems by kill count
    top_systems = (
        db.query(
            KillmailRaw.solar_system_id, func.count(KillmailRaw.killmail_id).label("kill_count")
        )
        .filter(func.date(KillmailRaw.kill_time) >= start_date)
        .filter(func.date(KillmailRaw.kill_time) <= end_date)
        .filter(KillmailRaw.solar_system_id.isnot(None))
        .group_by(KillmailRaw.solar_system_id)
        .order_by(desc("kill_count"))
        .limit(limit)
        .all()
    )

    # Get security status breakdown
    # We need to extract and count the loc: labels from the JSON
    security_breakdown_query = """
        SELECT
            CASE
                WHEN (json::jsonb)->'zkb'->'labels' @> '["loc:highsec"]'::jsonb THEN 'highsec'
                WHEN (json::jsonb)->'zkb'->'labels' @> '["loc:lowsec"]'::jsonb THEN 'lowsec'
                WHEN (json::jsonb)->'zkb'->'labels' @> '["loc:nullsec"]'::jsonb THEN 'nullsec'
                WHEN (json::jsonb)->'zkb'->'labels' @> '["loc:w-space"]'::jsonb THEN 'w-space'
                WHEN (json::jsonb)->'zkb'->'labels' @> '["loc:abyssal"]'::jsonb THEN 'abyssal'
                ELSE 'unknown'
            END AS security_type,
            COUNT(*) AS kill_count
        FROM killmail_raw
        WHERE DATE(kill_time) >= :start_date AND DATE(kill_time) <= :end_date
        GROUP BY security_type
        ORDER BY kill_count DESC
    """

    security_breakdown = db.execute(
        text(security_breakdown_query), {"start_date": start_date, "end_date": end_date}
    ).fetchall()

    return {
        "days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "top_solar_systems": [
            {"solar_system_id": system.solar_system_id, "kill_count": system.kill_count}
            for system in top_systems
        ],
        "security_breakdown": [
            {"security_type": row.security_type, "kill_count": row.kill_count}
            for row in security_breakdown
        ],
    }


@router.get("/api/ships")
def list_ships(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    List all ship types that have been destroyed (have fits in the database).

    Returns:
        dict with list of ship types
    """
    # Get distinct ship types from fits
    ship_types = db.query(Fit.ship_type_id).distinct().order_by(Fit.ship_type_id).all()
    ship_type_ids = [st.ship_type_id for st in ship_types]

    # Get ship names
    ship_names = (
        db.query(ItemType.type_id, ItemType.name)
        .filter(ItemType.type_id.in_(ship_type_ids))
        .order_by(ItemType.name)
        .all()
    )

    return {
        "total": len(ship_names),
        "ships": [
            {
                "ship_type_id": type_id,
                "name": name,
            }
            for type_id, name in ship_names
        ],
    }


@cache_forever("universe", exclude_first_arg=True)
def _get_all_regions(db: Session) -> dict[str, Any]:
    """Cached helper to get all regions."""
    regions = db.query(Region).order_by(Region.name).all()
    return {
        "total": len(regions),
        "regions": [
            {
                "region_id": region.region_id,
                "name": region.name,
            }
            for region in regions
        ],
    }


@router.get("/api/universe/regions")
def list_regions(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    List all EVE regions for filtering.
    Results are cached indefinitely as this data never changes.

    Returns:
        dict with list of regions
    """
    return _get_all_regions(db)


@cache_forever("universe", exclude_first_arg=True)
def _get_all_constellations(db: Session) -> dict[str, Any]:
    """Cached helper to get all constellations."""
    constellations = db.query(Constellation).order_by(Constellation.name).all()
    return {
        "total": len(constellations),
        "constellations": [
            {
                "constellation_id": const.constellation_id,
                "name": const.name,
                "region_id": const.region_id,
            }
            for const in constellations
        ],
    }


@router.get("/api/universe/constellations")
def list_all_constellations(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    List all EVE constellations for filtering.
    Results are cached indefinitely as this data never changes.

    Returns:
        dict with list of all constellations
    """
    return _get_all_constellations(db)


@cache_forever("universe")
def _get_constellations_in_region(region_id: int, db: Session) -> dict[str, Any]:
    """Cached helper to get constellations in a specific region."""
    constellations = (
        db.query(Constellation)
        .filter(Constellation.region_id == region_id)
        .order_by(Constellation.name)
        .all()
    )
    return {
        "region_id": region_id,
        "total": len(constellations),
        "constellations": [
            {
                "constellation_id": const.constellation_id,
                "name": const.name,
                "region_id": const.region_id,
            }
            for const in constellations
        ],
    }


@router.get("/api/universe/regions/{region_id}/constellations")
def list_constellations_in_region(
    region_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    List all constellations in a specific region.
    Results are cached indefinitely as this data never changes.

    Args:
        region_id: The EVE region ID
        db: Database session

    Returns:
        dict with list of constellations in the region
    """
    return _get_constellations_in_region(region_id, db)


@cache_forever("universe", exclude_first_arg=True)
def _get_all_systems(db: Session) -> dict[str, Any]:
    """Cached helper to get all solar systems."""
    systems = db.query(SolarSystem).order_by(SolarSystem.name).all()
    return {
        "total": len(systems),
        "systems": [
            {
                "system_id": system.system_id,
                "name": system.name,
                "constellation_id": system.constellation_id,
            }
            for system in systems
        ],
    }


@router.get("/api/universe/systems")
def list_all_systems(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    List all EVE solar systems for filtering.
    Results are cached indefinitely as this data never changes.

    Returns:
        dict with list of all solar systems
    """
    return _get_all_systems(db)


@cache_forever("universe")
def _get_systems_in_constellation(constellation_id: int, db: Session) -> dict[str, Any]:
    """Cached helper to get systems in a specific constellation."""
    systems = (
        db.query(SolarSystem)
        .filter(SolarSystem.constellation_id == constellation_id)
        .order_by(SolarSystem.name)
        .all()
    )
    return {
        "constellation_id": constellation_id,
        "total": len(systems),
        "systems": [
            {
                "system_id": system.system_id,
                "name": system.name,
                "constellation_id": system.constellation_id,
            }
            for system in systems
        ],
    }


@router.get("/api/universe/constellations/{constellation_id}/systems")
def list_systems_in_constellation(
    constellation_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    List all solar systems in a specific constellation.
    Results are cached indefinitely as this data never changes.

    Args:
        constellation_id: The EVE constellation ID
        db: Database session

    Returns:
        dict with list of systems in the constellation
    """
    return _get_systems_in_constellation(constellation_id, db)
