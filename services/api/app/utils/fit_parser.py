"""Utility functions for parsing ship fittings from killmail data."""

import hashlib
from collections import Counter
from typing import Any


def parse_fitting_from_killmail(killmail_data: dict[str, Any]) -> dict[str, Any] | None:
    """
    Parse ship fitting from killmail JSON data.

    Args:
        killmail_data: The 'killmail' portion of the zKillboard package

    Returns:
        dict with ship_type_id, items, and slot_counts, or None if invalid
    """
    if not killmail_data:
        return None

    victim = killmail_data.get("victim", {})
    ship_type_id = victim.get("ship_type_id")

    if not ship_type_id:
        return None

    # Extract items from victim's fitting
    items = victim.get("items", [])

    # Count items by slot type (flags indicate slot type in EVE)
    slot_counts = count_slots(items)

    # Extract unique item type IDs (for fit signature)
    item_type_ids = [item.get("item_type_id") for item in items if item.get("item_type_id")]

    return {
        "ship_type_id": ship_type_id,
        "items": items,
        "item_type_ids": item_type_ids,
        "slot_counts": slot_counts,
    }


def count_slots(items: list[dict[str, Any]]) -> dict[str, int]:
    """
    Count items by slot type based on EVE's flag system.

    EVE uses 'flag' to indicate where an item is fitted:
    - 11-18: Low slots
    - 19-26: Mid slots
    - 27-34: High slots
    - 92-99: Rig slots
    - 125-132: Subsystem slots
    - 87, 90: Drone bay
    - 5: Cargo hold

    Args:
        items: List of items from killmail

    Returns:
        dict with counts by slot type
    """
    counts = {
        "low_slots": 0,
        "mid_slots": 0,
        "high_slots": 0,
        "rig_slots": 0,
        "subsystem_slots": 0,
        "drones": 0,
        "cargo": 0,
        "other": 0,
    }

    for item in items:
        flag = item.get("flag")
        if not flag:
            continue

        if 11 <= flag <= 18:
            counts["low_slots"] += 1
        elif 19 <= flag <= 26:
            counts["mid_slots"] += 1
        elif 27 <= flag <= 34:
            counts["high_slots"] += 1
        elif 92 <= flag <= 99:
            counts["rig_slots"] += 1
        elif 125 <= flag <= 132:
            counts["subsystem_slots"] += 1
        elif flag in (87, 90):  # Drone bay
            counts["drones"] += 1
        elif flag == 5:  # Cargo
            counts["cargo"] += 1
        else:
            counts["other"] += 1

    return counts


def calculate_fit_signature(ship_type_id: int, item_type_ids: list[int]) -> str:
    """
    Calculate a unique signature for a ship fitting.

    The signature is a hash of the ship type and sorted fitted items,
    allowing us to group identical fits together.

    Args:
        ship_type_id: The ship type ID
        item_type_ids: List of fitted item type IDs

    Returns:
        32-character hex string signature
    """
    # Count each item type (handles multiples of the same module)
    item_counts = Counter(item_type_ids)

    # Create a deterministic representation
    # Format: ship_type:item1_id:count,item2_id:count,...
    items_str = ",".join(f"{type_id}:{count}" for type_id, count in sorted(item_counts.items()))
    signature_input = f"{ship_type_id}:{items_str}"

    # Hash it to get a compact signature
    return hashlib.md5(signature_input.encode()).hexdigest()
