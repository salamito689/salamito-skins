"""Validate a manually exported Youpin share response without making requests.
Usage: python scripts/probe_youpin_price.py youpin-share-response.json
Optional unauthenticated HTTPS read; no browser automation, production writes, or FX conversion.
Never commit exported responses containing personal data or tokens.
"""
import json
import math
import pathlib
import sys
import urllib.request
import urllib.error
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
        raise SystemExit("Usage: python scripts/probe_youpin_price.py response.json|https://api.youpin898.com/api/youpin/commodity/detail/share?Id=... [expected_listing_id]")
    source = sys.argv[1]
    expected = sys.argv[2] if len(sys.argv) == 3 else None
    if source.startswith("https://"):
        from urllib.parse import urlsplit, parse_qs
        parts = urlsplit(source)
        if (parts.scheme != "https" or parts.netloc != "api.youpin898.com"
                or parts.path != "/api/youpin/commodity/detail/share"
                or parts.fragment or set(parse_qs(parts.query)) != {"Id"}):
            raise ValueError("Only the public Youpin share detail endpoint is allowed")
        identifier = parse_qs(parts.query)["Id"]
        if len(identifier) != 1 or not identifier[0].isdecimal():
            raise ValueError("Invalid listing ID")
        expected = expected or identifier[0]
        request = urllib.request.Request(source, headers={"Accept": "application/json", "User-Agent": "SalamitoSkins-Staging-PriceProbe/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                if response.status != 200:
                    raise ValueError("HTTP response not successful")
                body = response.read(2_000_001)
        except urllib.error.HTTPError as exc:
            raise ValueError(f"Youpin rejected unauthenticated request: HTTP {exc.code}") from exc
        if len(body) > 2_000_000:
            raise ValueError("Response too large")
        payload = json.loads(body)
    else:
        path = pathlib.Path(source)
        if path.stat().st_size > 2_000_000:
            raise ValueError("Response too large")
        payload = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(extract(payload, expected), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
