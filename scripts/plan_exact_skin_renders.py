"""Plan exact-SKU image renders without making paid requests or exposing API keys.

Input: uuskins-feed-staging.json; output: exact-render-plan-staging.json.
This is a DRY RUN. No renderer is called; no images are claimed generated.
"""
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote

SOURCE = Path("uuskins-feed-staging.json")
OUTPUT = Path("exact-render-plan-staging.json")
PROVIDERS = ("inspekt", "steamdt")

def plan_item(item, provider):
    code = item.get("inspect_embed_code")
    if not isinstance(code, str) or len(code) < 24 or len(code) > 4096 or len(code) % 2 or any(ch not in "0123456789abcdefABCDEF" for ch in code):
        return None
    link = "steam://run/730/en/+csgo_econ_action_preview%20" + code
    digest = hashlib.sha256(code.upper().encode("ascii")).hexdigest()
    result = {
        "listing_id": item["id"], "model": item["market_hash_name"],
        "float": item["float"], "pattern": item["paint_seed"],
        "inspect_sha256": digest, "inspect_url": link,
        "render_status": "not_requested", "image_url": None,
        "exactness_verified": False, "approved_for_public_catalog": False,
    }
    if provider == "inspekt":
        result["provider_request_preview"] = (
            "https://inspekt.gg/api/still?inspect=" + quote(link, safe="")
            + "&view=front&bg=rarity&w=640&h=400&key=REQUIRES_USER_API_KEY"
        )
    else:
        result["provider_request_preview"] = (
            "SteamDT /open/cs2/v1/inspect (authentication and exact request format must be verified)"
        )
    return result

def main():
    provider = os.getenv("CS2_RENDER_PROVIDER", "inspekt").lower()
    if provider not in PROVIDERS:
        raise ValueError("Unknown provider")
    feed = json.loads(SOURCE.read_text(encoding="utf-8"))
    if feed.get("checkout_enabled") is not False or feed.get("currency") != "unverified":
        raise ValueError("Only isolated unverified staging feed allowed")
    records = [plan_item(item, provider) for item in feed.get("listings", [])]
    records = [record for record in records if record is not None]
    result = {
        "schema_version": 1, "provider": provider, "dry_run": True,
        "network_requests_sent": 0, "rendered_images": 0,
        "currency": "unverified", "checkout_enabled": False,
        "notes": "Provider authorization, pricing, quotas and image correctness require separate validation.",
        "listings": records,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Planned {len(records)} exact-SKU render requests via {provider}; zero requests sent")

if __name__ == "__main__":
    main()
