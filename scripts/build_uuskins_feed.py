"""Build a sanitized, non-transactional UUSKINS listing feed from the SKU probe.
No credentials, checkout actions, currency conversion, or production writes.
"""
import json
import hashlib
import re
import math
import pathlib
from datetime import datetime, timezone

SOURCE = pathlib.Path("uuskins-sku-preview.json")
OUTPUT = pathlib.Path("uuskins-feed-staging.json")
FIELDS = ("id", "skuId", "sku_id")
MAX_AGE_SECONDS = 900
IMAGE_MANIFEST = pathlib.Path("exact-images/manifest.json")

def validated_images():
    """Only explicitly attested SKU+inspect matches may enter the staging feed."""
    if not IMAGE_MANIFEST.is_file():
        return {}
    payload = json.loads(IMAGE_MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or not isinstance(payload.get("images"), list):
        raise ValueError("Invalid exact image manifest")
    result = {}
    for record in payload["images"]:
        if not isinstance(record, dict) or record.get("source") != "UUSKINS":
            continue
        identifier = record.get("listing_id")
        filename = record.get("file")
        fingerprint = record.get("inspect_sha256")
        if not isinstance(identifier, str) or not isinstance(filename, str) or not isinstance(fingerprint, str):
            continue
        if not re.fullmatch(r"[a-zA-Z0-9_-]+\.(?:webp|avif|png)", filename) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            continue
        path = IMAGE_MANIFEST.parent / filename
        if path.is_file() and 0 < path.stat().st_size <= 2_000_000:
            result[identifier] = (filename, fingerprint)
    return result


def parse_float(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and 0 <= number <= 1 else None

def parse_integer(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        text = str(value).strip()
        if not text.isdecimal():
            return None
        number = int(text)
    except (TypeError, ValueError):
        return None
    return number if 0 <= number <= 100000 else None

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
    images = validated_images()
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
            if not math.isfinite(price) or not 0 < price < 10000000:
                continue
            seen.add(identifier)
            code = item.get("inspect_embed_code")
            code = code.upper() if isinstance(code, str) and re.fullmatch(r"[0-9a-fA-F]{24,4096}", code) and len(code) % 2 == 0 else None
            fingerprint = hashlib.sha256(code.encode("ascii")).hexdigest() if code else None
            image_entry = images.get(identifier)
            exact_image = image_entry[0] if image_entry and image_entry[1] == fingerprint else None
            result.append({
                "id": identifier,
                "market_hash_name": str(item.get("steamHashName") or group.get("market_hash_name") or "")[:200],
                "price_original": price,
                "exact_image_file": exact_image,
                "float": parse_float(item.get("wearValue")),
                "paint_seed": parse_integer(item.get("paintSeed")),
                "paint_index": parse_integer(item.get("paintIndex")),
                "inspect_available": item.get("inspect_available") is True,
                "inspect_embed_code": item.get("inspect_embed_code") if isinstance(item.get("inspect_embed_code"), str) and 24 <= len(item["inspect_embed_code"]) <= 4096 and len(item["inspect_embed_code"]) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in item["inspect_embed_code"]) else None,
                "inspect_format": item.get("inspect_format") if item.get("inspect_format") in ("hex_payload", "legacy_asset", "unknown", "missing", "unsupported") else "unknown"
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
