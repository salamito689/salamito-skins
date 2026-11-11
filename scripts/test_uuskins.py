"""UUSKINS read-only integration probe. Never modifies production prices.json.
Requires UUSKINS_APP_KEY and UUSKINS_PRIVATE_KEY_PEM environment variables.
Uses the signing convention documented in UUSKINS Buy via API Reference v4.
"""
import base64
import json
import os
import pathlib
import urllib.request
from datetime import datetime, timezone

BASE_URL = "https://api.uuskins.com"
PATH = "/api/vertex/commodity/query/market/openapi/list"
OUT = pathlib.Path("uuskins-preview.json")

def main():
    app_key = os.environ.get("UUSKINS_APP_KEY", "").strip()
    pem = os.environ.get("UUSKINS_PRIVATE_KEY_PEM", "").replace("\\n", "\n").strip()
    if not app_key or not pem:
        raise SystemExit("Missing UUSKINS_APP_KEY or UUSKINS_PRIVATE_KEY_PEM. No files changed.")
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError as exc:
        raise SystemExit("Install cryptography: pip install cryptography") from exc

    params = {"appKey": app_key, "pageIndex": 1, "pageSize": 20}
    canonical = "".join(
        key + json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        for key, value in sorted(params.items()) if value is not None
    )
    private_key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    signature = base64.b64encode(
        private_key.sign(canonical.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
    ).decode("ascii")
    body = json.dumps({**params, "sign": signature}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + PATH, data=body, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "SalamitoSkins/1.0"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected UUSKINS response format")
    code = payload.get("code")
    if code not in (0, 200):
        raise RuntimeError("UUSKINS query was not successful; check API permissions/signature (response code: %s)" % code)
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise RuntimeError("Unexpected UUSKINS market data shape; preview not saved")
    items = data["items"]
    # Store only a minimal preview. Do not write appKey, signature, private key or raw response.
    sample = [
        {"market_hash_name": x.get("market_hash_name"), "min_price": x.get("min_price"), "count": x.get("count")}
        for x in items[:20] if isinstance(x, dict)
    ]
    OUT.write_text(json.dumps({
        "source": "UUSKINS test (not production)",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "currency": "unverified",
        "items": sample
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Read-only UUSKINS query succeeded; preview saved to", OUT)

if __name__ == "__main__":
    main()
