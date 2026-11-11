"""Bounded per-variant, per-float-range selection for UUSKINS staging data.

Input is a fetched candidate pool, not guaranteed full market inventory.
No network, currency conversion, checkout, or production changes.
"""
import math

MAX_VISIBLE = 10

DOPPLER_PHASES = {415: "Ruby", 416: "Sapphire", 417: "Black Pearl",
                  418: "Phase 1", 419: "Phase 2", 420: "Phase 3", 421: "Phase 4"}
GAMMA_PHASES = {568: "Emerald", 569: "Phase 1", 570: "Phase 2",
                571: "Phase 3", 572: "Phase 4"}


def variant_of(row):
    name = row.get("market_hash_name", "")
    index = row.get("paint_index")
    if not isinstance(name, str):
        return None
    if type(index) is not int:
        return None if "Doppler" in name else "standard"
    if "Gamma Doppler" in name:
        return GAMMA_PHASES.get(index)
    if "Talon Knife" in name and "Doppler" in name:
        return {852: "Phase 1", 853: "Phase 2", 854: "Phase 3", 855: "Phase 4", **DOPPLER_PHASES}.get(index)
    if "Doppler" in name:
        return DOPPLER_PHASES.get(index)
    return "standard"


def select_listings(rows, market_hash_name, minimum, maximum, variant=None, limit=MAX_VISIBLE, *, require_complete=False, coverage=None):
    """Select at most 10 cheapest candidates in [minimum, maximum).

    The last float range may explicitly end at 1.0, which is inclusive.
    The returned subset cannot establish global cheapest offers without source-side
    filters/sorting or exhaustive coverage.
    """
    if type(require_complete) is not bool:\n        raise ValueError("require_complete must be boolean")\n    if require_complete:\n        if not isinstance(coverage, dict) or coverage.get("global_cheapest_verified") is not True or coverage.get("source_pagination_verified") is not True or coverage.get("scope") != "complete_market":\n            raise ValueError("Complete market coverage not independently verified; cannot claim global cheapest listings")\n    if not isinstance(market_hash_name, str) or not market_hash_name:
        raise ValueError("Market hash name required")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in (minimum, maximum)):
        raise ValueError("Invalid float range")
    if not (0 <= minimum < maximum <= 1):
        raise ValueError("Invalid float boundaries")
    if type(limit) is not int or not 1 <= limit <= MAX_VISIBLE:
        raise ValueError("Maximum 10 listings")
    chosen = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("market_hash_name") != market_hash_name:
            continue
        if variant is not None and variant_of(row) != variant:
            continue
        identifier = row.get("id")
        wear = row.get("float")
        price = row.get("price_original")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            continue
        if type(wear) not in (int, float) or not math.isfinite(wear):
            continue
        if not (minimum <= wear < maximum or (maximum == 1 and wear == 1)):
            continue
        if type(price) not in (int, float) or not math.isfinite(price) or price <= 0:
            continue
        seen.add(identifier)
        chosen.append(row)
    return sorted(chosen, key=lambda row: (row["price_original"], row["float"], row["id"]))[:limit]
