"""API routes for viewing popular ship fittings."""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Fit, FitAggregateDaily, ItemType, KillmailRaw

router = APIRouter()


@router.get("/api/fits/popular")
def get_popular_fits(
    limit: int = Query(default=20, ge=1, le=100),
    days: int = Query(default=7, ge=1, le=90, description="Number of days to look back"),
    ship_type_id: int | None = Query(default=None, description="Filter by ship type"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Get most popular ship fits based on recent losses.

    Args:
        limit: Number of fits to return
        days: Number of days to look back (default: 7)
        ship_type_id: Optional filter by specific ship type
        db: Database session

    Returns:
        dict with popular fits and their loss counts
    """
    # Calculate date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    # Query aggregated data
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

    # Filter by ship type if provided
    if ship_type_id:
        query = query.filter(FitAggregateDaily.ship_type_id == ship_type_id)

    # Order by total losses and limit
    popular_fits = query.order_by(desc("total_losses")).limit(limit).all()

    # Get ship names for the results
    ship_type_ids = {fit.ship_type_id for fit in popular_fits}
    ship_names = (
        db.query(ItemType.type_id, ItemType.name).filter(ItemType.type_id.in_(ship_type_ids)).all()
    )
    ship_name_map = {type_id: name for type_id, name in ship_names}

    return {
        "days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "ship_type_filter": ship_type_id,
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

    return {
        "fit_signature": fit_signature,
        "found": True,
        "ship_type_id": first_fit.ship_type_id,
        "ship_name": ship_type.name if ship_type else "Unknown",
        "slot_counts": first_fit.slot_counts,
        "total_occurrences": total_count,
        "fitted_items": victim_items,
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
