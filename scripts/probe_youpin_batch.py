"""Read-only, low-volume Youpin known-ID price batch probe.
No account credentials, retries, checkout, or production updates.
"""
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlencode
from scripts.probe_youpin_price import extract

BASE = "https://api.youpin898.com/api/youpin/commodity/detail/share?"
MAX_IDS = 5
DELAY_SECONDS = 3

def run(ids):
    if not ids or len(ids) > MAX_IDS or len(set(ids)) != len(ids) or any(not x.isdecimal() for x in ids):
        raise ValueError("Provide 1-5 distinct numeric listing IDs")
    output = {"schema_version": 1, "source": "youpin", "currency": "CNY",
              "queried_at": datetime.now(timezone.utc).isoformat(),
              "checkout_enabled": False, "results": []}
    for index, identifier in enumerate(ids):
        if index:
            time.sleep(DELAY_SECONDS)
        url = BASE + urlencode({"Id": identifier})
        req = urllib.request.Request(url, headers={"Accept": "application/json",
            "User-Agent": "SalamitoSkins-Staging-PriceProbe/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status != 200:
                    raise ValueError("Unexpected HTTP status")
                body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise ValueError("Response too large")
            item = extract(json.loads(body), identifier)
            output["results"].append({"listing_id": identifier, "status": "ok", "item": item})
        except urllib.error.HTTPError as exc:
            output["results"].append({"listing_id": identifier, "status": "http_error", "http_status": exc.code})
            if exc.code in (401, 403, 429):
                output["stopped_early"] = "Access denied or throttled; no retries"
                break
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            output["results"].append({"listing_id": identifier, "status": "unavailable_or_invalid", "error_type": type(exc).__name__})
    return output

if __name__ == "__main__":
    ids = sys.argv[1:]
    if not ids:
        raise SystemExit("Usage: python -m scripts.probe_youpin_batch ID [ID ...] (max 5)")
    print(json.dumps(run(ids), ensure_ascii=False, indent=2))
