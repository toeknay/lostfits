"""API routes for viewing killmail data."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ItemType, KillmailRaw

router = APIRouter()


@router.get("/api/killmails")
def list_killmails(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    List recent killmails with ship names.

    Args:
        limit: Number of killmails to return (1-100)
        offset: Number of killmails to skip
        db: Database session

    Returns:
        dict with total count and killmail list
    """
    # Get total count
    total = db.query(func.count(KillmailRaw.killmail_id)).scalar()

    # Get killmails with ship names (left join in case ship type not seeded yet)
    killmails = (
        db.query(KillmailRaw, ItemType.name.label("ship_name"))
        .outerjoin(ItemType, KillmailRaw.victim_ship_type_id == ItemType.type_id)
        .order_by(desc(KillmailRaw.ingested_at))
        .limit(limit)
        .offset(offset)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "killmails": [
            {
                "killmail_id": km.KillmailRaw.killmail_id,
                "killmail_hash": km.KillmailRaw.killmail_hash,
                "kill_time": (
                    km.KillmailRaw.kill_time.isoformat() if km.KillmailRaw.kill_time else None
                ),
                "solar_system_id": km.KillmailRaw.solar_system_id,
                "victim_ship_type_id": km.KillmailRaw.victim_ship_type_id,
                "victim_ship_name": km.ship_name if km.ship_name else "Unknown",
                "ingested_at": (
                    km.KillmailRaw.ingested_at.isoformat() if km.KillmailRaw.ingested_at else None
                ),
            }
            for km in killmails
        ],
    }


@router.get("/api/killmails/{killmail_id}")
def get_killmail(
    killmail_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Get full killmail details including raw JSON.

    Args:
        killmail_id: The killmail ID
        db: Database session

    Returns:
        Complete killmail data including raw JSON package
    """
    killmail = db.query(KillmailRaw).filter(KillmailRaw.killmail_id == killmail_id).first()

    if not killmail:
        raise HTTPException(status_code=404, detail=f"Killmail {killmail_id} not found")

    return {
        "killmail_id": killmail.killmail_id,
        "killmail_hash": killmail.killmail_hash,
        "kill_time": killmail.kill_time.isoformat() if killmail.kill_time else None,
        "solar_system_id": killmail.solar_system_id,
        "victim_ship_type_id": killmail.victim_ship_type_id,
        "ingested_at": killmail.ingested_at.isoformat() if killmail.ingested_at else None,
        "data": killmail.json,  # Full raw JSON package from zKillboard
    }


@router.get("/api/stats")
def get_stats(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Get database statistics.

    Returns:
        Statistics about ingested data
    """
    killmail_count = db.query(func.count(KillmailRaw.killmail_id)).scalar()
    item_type_count = db.query(func.count(ItemType.type_id)).scalar()

    # Get first and last killmail times
    first_km = db.query(KillmailRaw).order_by(KillmailRaw.ingested_at).first()
    last_km = db.query(KillmailRaw).order_by(desc(KillmailRaw.ingested_at)).first()

    return {
        "total_killmails": killmail_count,
        "total_item_types": item_type_count,
        "first_ingested": first_km.ingested_at.isoformat() if first_km else None,
        "last_ingested": last_km.ingested_at.isoformat() if last_km else None,
    }


@router.get("/api/item-types")
def list_item_types(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    List item types (ships, modules, etc.) loaded from ESI.

    Args:
        limit: Number of items to return (1-200)
        offset: Number of items to skip
        search: Optional search term to filter by name
        db: Database session

    Returns:
        dict with total count and item type list
    """
    query = db.query(ItemType)

    # Apply search filter if provided
    if search:
        query = query.filter(ItemType.name.ilike(f"%{search}%"))

    total = query.count()

    items = query.order_by(ItemType.name).limit(limit).offset(offset).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "search": search,
        "items": [
            {
                "type_id": item.type_id,
                "name": item.name,
                "group_id": item.group_id,
                "category_id": item.category_id,
            }
            for item in items
        ],
    }
