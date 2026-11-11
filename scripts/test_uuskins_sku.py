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
        match = re.search(r"csgo_econ_action_preview(?:[\s/+]|%20)+([^\s&#/?]+)", candidate, re.I)
        if match:
            payload = match.group(1)
            break
    # Steam preview hex commonly uses a leading A before the hex bytes.
    if re.fullmatch(r"A[0-9a-fA-F]{24,}", payload, re.I):
        fmt = "hex_payload"
    elif re.fullmatch(r"[0-9a-fA-F]{24,}", payload):
        fmt = "hex_payload"
    elif re.fullmatch(r"[SM]\d+A\d+D\d+", payload, re.I):
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
        "has_legacy_token": bool(re.search(r"[SM]\d+A\d+D\d+", value, re.I)),
        "has_hex_token": bool(re.search(r"(?<![0-9a-fA-F])[0-9a-fA-F]{24,}(?![0-9a-fA-F])", value)),
        "payload_prefix": "A_hex" if re.fullmatch(r"A[0-9a-fA-F]{24,}", payload, re.I) else ("hex" if re.fullmatch(r"[0-9a-fA-F]{24,}", payload) else "other"),
    }
    return diagnostic


def exact_embed_code(row):
    """Extract the actual hex inspect payload for this exact SKU, never credentials."""
    import re
    from urllib.parse import unquote
    link = row.get("inspectUrl") or row.get("inspect_url")
    if not isinstance(link, str):
        return None
    value = unquote(unquote(link.strip()))
    match = re.search(r"csgo_econ_action_preview(?:[\s/+]|%20)+([A-Fa-f0-9]{24,})", value, re.I)
    if not match:
        return None
    code = match.group(1)
    if code.upper().startswith("A") and len(code) % 2 == 1:
        code = code[1:]
    return code.upper() if len(code) % 2 == 0 and len(code) <= 4096 else None

IMAGE_KEYWORDS = ("image", "img", "photo", "picture", "screenshot", "thumbnail", "icon", "preview", "render")

def image_field_diagnostics(row):
    """Describe possible source images without exposing unverified URLs or claiming exactness."""
    from urllib.parse import urlparse
    findings = []
    def scan(obj, prefix="", depth=0):
        if depth > 2 or len(findings) >= 20:
            return
        if isinstance(obj, dict):
            for key, value in obj.items():
                label = (prefix + "." if prefix else "") + str(key)
                if any(word in str(key).lower() for word in IMAGE_KEYWORDS):
                    kind = type(value).__name__
                    is_https = False
                    host = None
                    if isinstance(value, str):
                        parsed = urlparse(value)
                        is_https = parsed.scheme == "https" and bool(parsed.hostname)
                        host = parsed.hostname if is_https else None
                    findings.append({"field": label[:100], "type": kind, "https_url": is_https, "host": host})
                elif isinstance(value, dict):
                    scan(value, label, depth + 1)
    scan(row)
    return findings

def safe_samples(obj):
    if isinstance(obj, list):
        return [{**{k: v for k, v in row.items() if k in ALLOWED and isinstance(v, (str, int, float, bool)) and len(str(v)) < 150}, **inspect_metadata(row), "inspect_embed_code": exact_embed_code(row), "image_field_diagnostics": image_field_diagnostics(row)}
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

def first_inspect_link(obj):
    """Find one exact item link; do not print it to Actions logs."""
    if isinstance(obj, list):
        for row in obj:
            if isinstance(row, dict):
                link = row.get("inspectUrl") or row.get("inspect_url")
                if isinstance(link, str) and link.strip().startswith("steam://") and "csgo_econ_action_preview" in link.lower():
                    return link.strip()
        return None
    if isinstance(obj, dict):
        for value in obj.values():
            result = first_inspect_link(value)
            if result:
                return result
    return None

def main():
    app_key = os.environ.get("UUSKINS_APP_KEY", "").strip()
    pem = os.environ.get("UUSKINS_PRIVATE_KEY_PEM", "").replace("\\n", "\n").strip()
    if not app_key.isdecimal() or not pem.startswith("-----BEGIN PRIVATE KEY-----"):
        raise SystemExit("Invalid/missing secret formats")
    private_key = serialization.load_pem_private_key(pem.encode(), password=None)
    results = []
    inspect_example = None
    # Bounded read-only sampling: two established controls plus three Doppler models.
    # Market hash names identify models, not Phase/Ruby/Sapphire; use paintIndex
    # and verified source fields before assigning a phase or publishing prices.
    models = (
        "AK-47 | Redline (Field-Tested)",
        "AWP | Asiimov (Field-Tested)",
        "★ Karambit | Doppler (Factory New)",
        "★ Butterfly Knife | Doppler (Factory New)",
        "★ Karambit | Gamma Doppler (Factory New)",
    )
    for name in models:
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
        if name == "AK-47 | Redline (Field-Tested)" and inspect_example is None and code in (0, 200):
            inspect_example = first_inspect_link(payload.get("data"))
        sample = safe_samples(payload.get("data"))
        phase_diagnostics = {
            "sample_count": len(sample),
            "with_paint_index": sum(row.get("paintIndex") is not None for row in sample),
            "with_paint_seed": sum(row.get("paintSeed") is not None for row in sample),
            "with_price": sum(row.get("price") is not None for row in sample),
            "with_phase_field": sum(row.get("phase") is not None for row in sample),
            "currency_fields": sorted({str(row.get("currency") or row.get("currencyCode")) for row in sample if row.get("currency") or row.get("currencyCode")}),
            "note": "Sample only; no total count, phase or currency inferred",
        }
        results.append({"market_hash_name": name, "http_status": http_status,
                        "phase_diagnostics": phase_diagnostics,
                        "application_code": code if isinstance(code, (str, int)) else None,
                        "status": "ok" if code in (0, 200) else "application_error",
                        "schema": describe(payload.get("data")),
                        "sample_listings": sample})
        print(f"SKU query {name}: HTTP {http_status}, application code {code}; no orders created")
        # Print bounded aggregate diagnostics only; no credentials, inspect links or item IDs.
        if "Doppler" in name and code in (0, 200):
            from collections import Counter
            indices = Counter(str(row["paintIndex"]) for row in sample if row.get("paintIndex") is not None)
            prices = []
            for row in sample:
                try:
                    value = float(row.get("price"))
                    if 0 < value < 10000000 and __import__("math").isfinite(value):
                        prices.append(value)
                except (TypeError, ValueError):
                    pass
            print(json.dumps({
                "model": name, "sample_count": len(sample),
                "paint_index_counts": dict(sorted(indices.items())[:30]),
                "prices_observed": len(prices),
                "price_min_raw": min(prices) if prices else None,
                "price_max_raw": max(prices) if prices else None,
                "currency_hints": phase_diagnostics["currency_fields"],
                "warning": "Raw price currency unverified; paint indices are not yet mapped to phases; sample is not total stock",
            }, ensure_ascii=False))
    if inspect_example:
        Path("uuskins-one-inspect-link.txt").write_text(
            "LINK DE INSPECAO DE UMA AK-47 REDLINE (anuncio individual, temporario):\\n"
            + inspect_example + "\\n\\n"
            + "Cole apenas a linha steam:// no campo INSPECT LINK do Inspekt Sandbox.\\n"
            + "Este link nao e uma chave de API. Nao publica-lo no catalogo.\\n",
            encoding="utf-8",
        )
        print("One individual inspect link saved to isolated artifact (not printed)")
    else:
        print("No valid AK-47 Redline inspect link found; artifact will not be created")
    OUT.write_text(json.dumps({"source": "UUSKINS read-only SKU test, not production",
                               "fetched_at": datetime.now(timezone.utc).isoformat(),
                               "currency": "unverified", "results": results},
                              indent=2, ensure_ascii=False), encoding="utf-8")
    print("Saved sanitized SKU preview; no secrets, orders, or production files touched")

if __name__ == "__main__":
    main()
