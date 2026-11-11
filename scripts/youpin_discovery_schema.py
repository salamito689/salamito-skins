"""Offline Youpin model-to-listing discovery validation.

No network requests, credentials, anti-bot bypass or production writes.
Usage:
  python -m scripts.youpin_discovery_schema --payload request.json
  python -m scripts.youpin_discovery_schema --response sanitized-response.json

Only a successful response containing *individual* listing IDs can advance
discovery; template IDs are never treated as listing IDs.
"""
import argparse
import json
from pathlib import Path

EXPECTED_FIELDS = ("gameId", "listType", "listSortType", "pageIndex", "pageSize", "sortType", "templateId")

def build_request(template_id, page=1):
    tid = str(template_id)
    if not tid.isdecimal() or int(tid) <= 0:
        raise ValueError("Invalid template ID")
    if not isinstance(page, int) or not 1 <= page <= 100:
        raise ValueError("Page out of bounded range")
    return {"gameId": "730", "listType": "10", "listSortType": 1,
            "pageIndex": page, "pageSize": 10, "sortType": 0, "templateId": tid}

def validate_request(data):
    if not isinstance(data, dict) or set(data) != set(EXPECTED_FIELDS):
        raise ValueError("Unexpected request fields")
    expected = build_request(data["templateId"], data["pageIndex"])
    if data != expected:
        raise ValueError("Request does not match observed Youpin format")
    return expected

def summarize_response(response):
    if not isinstance(response, dict):
        raise ValueError("Expected JSON object")
    code = response.get("Code", response.get("code"))
    if code not in (0, "0"):
        return {"status": "api_error", "individual_listing_ids_verified": False}
    data = response.get("Data", response.get("data"))
    # Never guess nested schema or infer listing IDs from template IDs.
    return {"status": "schema_inspection_needed", "individual_listing_ids_verified": False,
            "data_type": type(data).__name__,
            "data_keys": sorted(str(k) for k in data)[:30] if isinstance(data, dict) else [],
            "note": "A verified per-unit ID field and sale status are still required."}

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--payload", type=Path)
    group.add_argument("--response", type=Path)
    args = parser.parse_args()
    file = args.payload or args.response
    if file.stat().st_size > 200000:
        raise ValueError("File too large")
    data = json.loads(file.read_text(encoding="utf-8"))
    result = validate_request(data) if args.payload else summarize_response(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
