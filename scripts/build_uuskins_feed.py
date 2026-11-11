"""Build a sanitized, non-transactional UUSKINS listing feed from the SKU probe.
No credentials, checkout actions, currency conversion, or production writes.
"""
import json
import pathlib
from datetime import datetime, timezone

SOURCE = pathlib.Path("uuskins-sku-preview.json")
OUTPUT = pathlib.Path("uuskins-feed-staging.json")
FIELDS = ("id", "skuId", "sku_id")
MAX_AGE_SECONDS = 900

def main():
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    fetched = datetime.fromisoformat(raw["fetched_at"].replace("Z", "+00:00"))
    if fetched.tzinfo is None:
        raise ValueError("Source timestamp must have a timezone")
    age = (datetime.now(timezone.utc) - fetched).total_seconds()
    if age < -120 or age > MAX_AGE_SECONDS:
        raise ValueError("Stale or future-dated source snapshot; no feed published")
    if raw.get("currency") != "unverified":
        raise ValueError("Unexpected currency field; requires manual validation")
    result = []
    seen = set()
    for group in raw.get("results", []):
        if group.get("status") != "ok":
            continue
        for item in group.get("sample_listings", []):
            if not isinstance(item, dict):
                continue
            identifier = next((item[k] for k in FIELDS if item.get(k) is not None), None)
            if identifier is None:
                continue
            identifier = str(identifier).strip()
            if not identifier or identifier in seen:
                continue
            value = item.get("price")
            if isinstance(value, bool):
                continue
            try:
                price = float(value)
            except (ValueError, TypeError):
                continue
            if not 0 < price < 10000000:
                continue
            seen.add(identifier)
            result.append({
                "id": identifier,
                "market_hash_name": str(item.get("steamHashName") or group.get("market_hash_name") or "")[:200],
                "price_original": price,
                "float": item.get("wearValue") if isinstance(item.get("wearValue"), (float, int)) else None,
                "paint_seed": item.get("paintSeed") if isinstance(item.get("paintSeed"), int) else None,
                "paint_index": item.get("paintIndex") if isinstance(item.get("paintIndex"), int) else None
            })
    if not result:
        raise ValueError("No valid individual listings; no feed generated")
    feed = {
        "schema_version": 1,
        "source": "UUSKINS staging, read-only",
        "fetched_at": fetched.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "currency": "unverified",
        "checkout_enabled": False,
        "listing_count": len(result),
        "listings": result
    }
    OUTPUT.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created isolated staging feed with {len(result)} listings; currency unverified; checkout disabled")

if __name__ == "__main__":
    main()
