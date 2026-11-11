"""UUSKINS read-only integration probe. Never modifies production prices.json.
Requires UUSKINS_APP_KEY and UUSKINS_PRIVATE_KEY_PEM environment variables.
Uses the signing convention documented in UUSKINS Buy via API Reference v4.
"""
import base64
import json
import os
import pathlib
import urllib.request
import urllib.error
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

    if not app_key.isdecimal():
        raise RuntimeError("AppKey format unexpected: expected numeric application ID.")
    if not pem.startswith("-----BEGIN PRIVATE KEY-----") or not pem.endswith("-----END PRIVATE KEY-----"):
        raise RuntimeError("Private key PEM format unexpected; verify GitHub secret.")
    params = {"appKey": app_key, "pageIndex": 1, "pageSize": 20}
    canonical = "".join(
        key + json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        for key, value in sorted(params.items()) if value is not None
    )
    private_key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    signed_bytes = canonical.encode("utf-8")
    raw_signature = private_key.sign(signed_bytes, padding.PKCS1v15(), hashes.SHA256())
    private_key.public_key().verify(raw_signature, signed_bytes, padding.PKCS1v15(), hashes.SHA256())
    print("Credential format: valid; local RSA SHA-256 signing and verification: passed")
    print("Request: market hash list, pageIndex=1, pageSize=20, read-only")
    signature = base64.b64encode(raw_signature).decode("ascii")
    body = json.dumps({**params, "sign": signature}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + PATH, data=body, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "SalamitoSkins/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print(f'UUSKINS HTTP status: {response.status}')
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'UUSKINS HTTP status: {exc.code}; no production data changed') from None
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected UUSKINS response format")
    code = payload.get("code")
    if code not in (0, 200):
        message = str(payload.get("message") or payload.get("msg") or "").strip().lower()
        known = {"sign error", "invalid sign", "signature error", "invalid signature", "appkey error", "invalid appkey", "invalid app key", "permission denied", "unauthorized", "forbidden", "internal server error"}
        diagnostic = message if message in known else "unclassified"
        raise RuntimeError(f"UUSKINS application code: {code}; safe diagnostic: {diagnostic}. No production data changed.")
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise RuntimeError("Unexpected UUSKINS market data shape; preview not saved")
    items = data["items"]
    # Store only a minimal preview. Do not write appKey, signature, private key or raw response.
    sample = [
        {"market_hash_name": x.get("market_hash_name"), "min_price": x.get("min_price"), "count": x.get("count")}
        for x in items[:20] if isinstance(x, dict)
    ]
    # Inspect response structure without exposing credentials, signatures or raw payloads.
    # Only allowlisted market metadata and field NAMES are exported.
    item_fields = sorted({str(k) for x in items[:20] if isinstance(x, dict) for k in x.keys()})
    data_fields = sorted(str(k) for k in data.keys())
    top_level_fields = sorted(str(k) for k in payload.keys())
    currency_hints = {}
    for parent_name, parent in (("response", payload), ("data", data)):
        for key in ("currency", "currencyCode", "currency_code", "priceCurrency", "priceUnit", "unit"):
            value = parent.get(key)
            if isinstance(value, (str, int, float)) and len(str(value)) <= 30:
                currency_hints[parent_name + "." + key] = value
    print("Market item field names:", ", ".join(item_fields))
    print("Currency hints available:", bool(currency_hints))
    OUT.write_text(json.dumps({
        "source": "UUSKINS test (not production)",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "currency": "unverified",
        "schema": {"response_fields": top_level_fields, "data_fields": data_fields, "item_fields": item_fields, "currency_hints": currency_hints},
        "items": sample
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Read-only UUSKINS query succeeded; preview saved to", OUT)

if __name__ == "__main__":
    main()
