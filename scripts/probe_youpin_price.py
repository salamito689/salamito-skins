"""Validate a manually exported Youpin share response without making requests.
Usage: python scripts/probe_youpin_price.py youpin-share-response.json
No authentication, browser automation, production writes, or FX conversion.
Never commit exported responses containing personal data or tokens.
"""
import json
import math
import pathlib
import sys
from datetime import datetime, timezone

def extract(payload, expected_id=None):
    if not isinstance(payload, dict) or payload.get("code", payload.get("Code")) not in (0, "0"):
        raise ValueError("Youpin response unsuccessful")
    data = payload.get("data", payload.get("Data"))
    if not isinstance(data, dict):
        raise ValueError("Missing individual listing data")
    identifier = str(data.get("Id", data.get("id", "")))
    if not identifier.isdecimal() or (expected_id and identifier != str(expected_id)):
        raise ValueError("Listing ID missing or mismatched")
    raw_price = data.get("Price")
    if isinstance(raw_price, bool) or not isinstance(raw_price, (int, float, str)):
        raise ValueError("Missing price")
    try:
        price = float(raw_price)
    except ValueError as exc:
        raise ValueError("Invalid price") from exc
    if not math.isfinite(price) or not 0 < price < 10000000:
        raise ValueError("Price outside permitted range")
    return {
        "source": "youpin", "listing_id": identifier,
        "market_hash_name": str(data.get("MarketHashName") or "")[:200],
        "price_rmb": round(price, 2), "currency": "CNY",
        "float": data.get("Abrade"),
        "paint_seed": data.get("PaintSeed"),
        "paint_index": data.get("PaintIndex"),
        "source_status": "snapshot_only",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "checkout_enabled": False,
    }

def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit("Usage: python scripts/probe_youpin_price.py response.json [expected_listing_id]")
    path = pathlib.Path(sys.argv[1])
    if path.stat().st_size > 2_000_000:
        raise ValueError("Response too large")
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(extract(payload, sys.argv[2] if len(sys.argv) == 3 else None), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
