"""Validate a staging UUSKINS feed before it can be distributed as a test artifact.
This is NOT a production price feed or checkout inventory.
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

FEED = Path("uuskins-feed-staging.json")
MAX_AGE_SECONDS = 900

def main():
    data = json.loads(FEED.read_text(encoding="utf-8"))
    assert data.get("schema_version") == 1, "Unsupported schema"
    assert data.get("currency") == "unverified", "Currency needs independent validation"
    assert data.get("checkout_enabled") is False, "Checkout must stay disabled"
    assert data.get("source") == "UUSKINS staging, read-only", "Unexpected source"
    timestamp = datetime.fromisoformat(data["fetched_at"].replace("Z", "+00:00"))
    assert timestamp.tzinfo is not None, "Timezone required"
    age = (datetime.now(timezone.utc) - timestamp).total_seconds()
    assert -120 <= age <= MAX_AGE_SECONDS, "Snapshot is stale or future dated"
    rows = data.get("listings")
    assert isinstance(rows, list) and rows, "Empty or invalid feed"
    assert len(rows) == data.get("listing_count"), "Incorrect count"
    seen = set()
    for row in rows:
        assert isinstance(row, dict), "Invalid row"
        identifier = row.get("id")
        assert isinstance(identifier, str) and identifier.strip(), "Missing listing ID"
        assert identifier not in seen, "Duplicate listing ID"
        seen.add(identifier)
        assert isinstance(row.get("market_hash_name"), str) and row["market_hash_name"], "Missing name"
        price = row.get("price_original")
        assert type(price) in (int, float) and math.isfinite(price) and 0 < price < 10000000, "Invalid price"
        wear = row.get("float")
        assert wear is None or (type(wear) in (int, float) and math.isfinite(wear) and 0 <= wear <= 1), "Invalid float"
        assert type(row.get("inspect_available")) is bool, "Invalid inspect availability flag"
        for key in ("paint_seed", "paint_index"):
            value = row.get(key)
            assert value is None or (type(value) is int and 0 <= value <= 100000), f"Invalid {key}"
    print(f"Staging feed passed: {len(rows)} unique listings; no BRL prices or checkout")

if __name__ == "__main__":
    main()
