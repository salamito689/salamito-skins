"""Read-only UUSKINS SKU endpoint probe. No orders, no production writes."""
import base64
import json
import os
from pathlib import Path
import urllib.request
import urllib.error
from urllib.parse import urlparse
from datetime import datetime, timezone
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

URL = "https://api.uuskins.com/api/vertex/commodity/query/market/sku/list"
OUT = Path("uuskins-sku-preview.json")
ALLOWED = {"id", "skuId", "sku_id", "marketHashName", "steamHashName", "market_hash_name",
           "price", "salePrice", "sellPrice", "min_price", "wearValue", "float",
           "floatValue", "paintSeed", "paintIndex", "phase", "status", "currency",
           "currencyCode", "assetId", "commodityId"}

def describe(obj, depth=0):
    if depth > 3:
        return {"type": type(obj).__name__}
    if isinstance(obj, dict):
        return {str(k): describe(v, depth + 1) for k, v in list(obj.items())[:35]}
    if isinstance(obj, list):
        return {"type": "array", "length": len(obj),
                "first": describe(obj[0], depth + 1) if obj else None}
    return {"type": type(obj).__name__}

def inspect_metadata(row):
    """Classify inspect links and export only non-sensitive structural diagnostics."""
    import re
    from urllib.parse import unquote, parse_qs
    link = row.get("inspectUrl") or row.get("inspect_url")
    if not isinstance(link, str) or not link.strip():
        return {"inspect_available": False, "inspect_format": "missing"}
    value = unquote(link.strip())
    parsed = urlparse(value)
    if parsed.scheme.lower() not in ("steam", "https") or not parsed.netloc:
        return {"inspect_available": False, "inspect_format": "unsupported"}
    # Inspect Steam URLs can contain encoded spaces, slash-delimited commands,
    # and preview tokens in the query or fragment.
    candidates = [value, unquote(value), unquote(unquote(value))]
    payload = ""
    for candidate in candidates:
        match = re.search(r"csgo_econ_action_preview(?:[\\s/+]|%20)+([^\\s&#/?]+)", candidate, re.I)
        if match:
            payload = match.group(1)
            break
    # Steam preview hex commonly uses a leading A before the hex bytes.
    if re.fullmatch(r"A[0-9a-fA-F]{24,}", payload, re.I):
        fmt = "hex_payload"
    elif re.fullmatch(r"[0-9a-fA-F]{24,}", payload):
        fmt = "hex_payload"
    elif re.fullmatch(r"[SM]\\d+A\\d+D\\d+", payload, re.I):
        fmt = "legacy_asset"
    else:
        fmt = "unknown"
    # Only booleans and coarse structural categories: never print or save link,
    # identifiers, query parameter values, or actual preview payloads.
    diagnostic = {
        "inspect_available": True,
        "inspect_format": fmt,
        "inspect_scheme": parsed.scheme.lower(),
        "has_preview_command": "csgo_econ_action_preview" in value.lower(),
        "has_query": bool(parsed.query),
        "has_fragment": bool(parsed.fragment),
        "has_encoded_spaces": "%20" in link.lower() or "+" in link,
        "has_legacy_token": bool(re.search(r"[SM]\\d+A\\d+D\\d+", value, re.I)),
        "has_hex_token": bool(re.search(r"(?<![0-9a-fA-F])[0-9a-fA-F]{24,}(?![0-9a-fA-F])", value)),\n        "payload_prefix": "A_hex" if re.fullmatch(r"A[0-9a-fA-F]{24,}", payload, re.I) else ("hex" if re.fullmatch(r"[0-9a-fA-F]{24,}", payload) else "other"),
    }
    return diagnostic


def safe_samples(obj):
    if isinstance(obj, list):
        return [{**{k: v for k, v in row.items() if k in ALLOWED and isinstance(v, (str, int, float, bool)) and len(str(v)) < 150}, **inspect_metadata(row)}
                for row in obj[:20] if isinstance(row, dict)]
    if isinstance(obj, dict):
        for key in ("items", "list", "records", "skuList", "sku_list"):
            if isinstance(obj.get(key), list):
                return safe_samples(obj[key])
        for value in obj.values():
            samples = safe_samples(value)
            if samples:
                return samples
    return []

def main():
    app_key = os.environ.get("UUSKINS_APP_KEY", "").strip()
    pem = os.environ.get("UUSKINS_PRIVATE_KEY_PEM", "").replace("\\n", "\n").strip()
    if not app_key.isdecimal() or not pem.startswith("-----BEGIN PRIVATE KEY-----"):
        raise SystemExit("Invalid/missing secret formats")
    private_key = serialization.load_pem_private_key(pem.encode(), password=None)
    results = []
    for name in ("AK-47 | Redline (Field-Tested)", "AWP | Asiimov (Field-Tested)"):
        params = {"appKey": app_key, "marketHashName": name}
        canonical = "".join(k + json.dumps(v, ensure_ascii=False, separators=(",", ":"))
                            for k, v in sorted(params.items()) if v is not None)
        signature = base64.b64encode(private_key.sign(canonical.encode(), padding.PKCS1v15(), hashes.SHA256())).decode()
        body = json.dumps({**params, "sign": signature}, ensure_ascii=False).encode()
        req = urllib.request.Request(URL, data=body, method="POST",
                                     headers={"Content-Type": "application/json", "Accept": "application/json",
                                              "User-Agent": "SalamitoSkins/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.load(response)
                http_status = response.status
        except urllib.error.HTTPError as exc:
            results.append({"market_hash_name": name, "http_status": exc.code, "status": "http_error"})
            continue
        except (TimeoutError, urllib.error.URLError, ValueError):
            results.append({"market_hash_name": name, "status": "network_or_json_error"})
            continue
        if not isinstance(payload, dict):
            results.append({"market_hash_name": name, "http_status": http_status, "status": "unexpected_shape"})
            continue
        code = payload.get("code")
        results.append({"market_hash_name": name, "http_status": http_status,
                        "application_code": code if isinstance(code, (str, int)) else None,
                        "status": "ok" if code in (0, 200) else "application_error",
                        "schema": describe(payload.get("data")),
                        "sample_listings": safe_samples(payload.get("data"))})
        print(f"SKU query {name}: HTTP {http_status}, application code {code}; no orders created")
    OUT.write_text(json.dumps({"source": "UUSKINS read-only SKU test, not production",
                               "fetched_at": datetime.now(timezone.utc).isoformat(),
                               "currency": "unverified", "results": results},
                              indent=2, ensure_ascii=False), encoding="utf-8")
    print("Saved sanitized SKU preview; no secrets, orders, or production files touched")

if __name__ == "__main__":
    main()
