"""Experimental Youpin discovery endpoint probe: one read-only request, no auth.
The response is summarized without publishing raw marketplace or personal data.
Does not bypass anti-bot challenges; HTTP 401/403/429 ends the probe.
"""
import json
import urllib.error
import urllib.request

URL = "https://api.youpin898.com/api/homepage/pc/goods/market/querySaleTemplate"
# Payload shape is unverified; do not assume the endpoint returns individual IDs.
PAYLOAD = {"pageIndex": 1, "pageSize": 1}

def main():
    body = json.dumps(PAYLOAD, separators=(",", ":")).encode()
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "SalamitoSkins-Staging-DiscoveryProbe/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            data = response.read(100001)
            status = response.status
    except urllib.error.HTTPError as exc:
        print(json.dumps({"endpoint": "querySaleTemplate", "status": "http_error", "http_code": exc.code, "no_retry": True}))
        return
    except (urllib.error.URLError, TimeoutError) as exc:
        print(json.dumps({"endpoint": "querySaleTemplate", "status": "network_error", "error_type": type(exc).__name__}))
        return
    if len(data) > 100000:
        print(json.dumps({"endpoint": "querySaleTemplate", "status": "response_too_large"}))
        return
    try:
        result = json.loads(data)
    except ValueError:
        print(json.dumps({"endpoint": "querySaleTemplate", "status": "non_json", "http_code": status}))
        return
    if not isinstance(result, dict):
        print(json.dumps({"endpoint": "querySaleTemplate", "status": "unexpected_schema"}))
        return
    print(json.dumps({
        "endpoint": "querySaleTemplate", "http_code": status,
        "api_code": result.get("code", result.get("Code")),
        "top_level_keys": sorted(str(x) for x in result.keys())[:30],
        "data_type": type(result.get("data", result.get("Data"))).__name__,
        "verified_individual_listing_ids": False,
        "note": "Schema discovery only; no market feed published",
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
