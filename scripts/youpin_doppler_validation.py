"""Validate phase-specific Doppler pricing input; no network calls or production writes."""
from decimal import Decimal, InvalidOperation

DOPPLER_PHASES = frozenset(("Phase 1", "Phase 2", "Phase 3", "Phase 4", "Ruby", "Sapphire", "Black Pearl"))
GAMMA_PHASES = frozenset(("Phase 1", "Phase 2", "Phase 3", "Phase 4", "Emerald"))

def validate_phase_price(record):
    if not isinstance(record, dict):
        raise ValueError("Expected record")
    name = record.get("market_hash_name")
    phase = record.get("phase")
    family = record.get("family")
    allowed = DOPPLER_PHASES if family == "Doppler" else GAMMA_PHASES if family == "Gamma Doppler" else frozenset()
    if not isinstance(name, str) or family not in name or phase not in allowed:
        raise ValueError("Missing or inconsistent Doppler family/phase")
    if record.get("currency") != "CNY":
        raise ValueError("Expected source CNY")
    try:
        price = Decimal(str(record["price_rmb"]))
    except (KeyError, TypeError, InvalidOperation) as exc:
        raise ValueError("Invalid RMB price") from exc
    if not price.is_finite() or not 0 < price < 10000000:
        raise ValueError("Invalid RMB price")
    if not record.get("source") or not record.get("fetched_at"):
        raise ValueError("Source and timestamp required")
    return {"market_hash_name": name, "family": family, "phase": phase,
            "price_rmb": str(price), "currency": "CNY",
            "source": record["source"], "fetched_at": record["fetched_at"],
            "status": "reference_only_not_verified_listing"}

def validate_distinct_phases(records):
    output = {}
    for record in records:
        item = validate_phase_price(record)
        key = (item["market_hash_name"], item["family"], item["phase"])
        if key in output:
            raise ValueError("Duplicate phase quote; explicit selection required")
        output[key] = item
    return output
