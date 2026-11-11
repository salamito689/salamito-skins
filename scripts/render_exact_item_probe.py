"""Isolated, single-item CS2 render probe. Never commits item links or secrets.

Required env:
  CS2_INSPECT_LINK: exact Steam inspect URL for one UUSKINS listing
  INSPEKT_SECRET_KEY: server-only cs2sk_... key from Inspekt dashboard

Output: local image and metadata; never production or public staging.
"""
import json
import os
import pathlib
import urllib.parse
import urllib.request

OUT = pathlib.Path("uuskins-exact-item-preview.webp")
META = pathlib.Path("uuskins-exact-item-render-result.json")

def main():
    inspect = os.environ.get("CS2_INSPECT_LINK", "").strip()
    key = os.environ.get("INSPEKT_SECRET_KEY", "").strip()
    if not inspect.startswith("steam://rungame/730/"):
        raise SystemExit("CS2_INSPECT_LINK must be an exact steam://rungame/730 inspect link")
    if "csgo_econ_action_preview" not in urllib.parse.unquote(inspect).lower():
        raise SystemExit("Inspect command missing")
    if not key.startswith("cs2sk_"):
        raise SystemExit("INSPEKT_SECRET_KEY missing or invalid format")
    params = urllib.parse.urlencode({
        "inspect": inspect, "view": "front", "bg": "transparent",
        "w": 640, "h": 400, "wait": 1,
    })
    request = urllib.request.Request(
        "https://inspekt.gg/api/still?" + params,
        headers={"x-cs2-key": key, "Accept": "image/webp", "User-Agent": "SalamitoSkins-Staging/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=110) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            notes = response.headers.get("x-cs2-notes", "")
            data = response.read(3_000_001)
    except Exception as exc:
        # Avoid logging URL, inspect payload or key in exception messages.
        raise SystemExit("Render request failed; inspect status and Inspekt quota privately") from None
    if status != 200 or content_type != "image/webp" or len(data) > 3_000_000:
        raise SystemExit("Render was not a valid 200 image/webp response")
    # Inspekt can return an inaccurate default-item placeholder. Never accept it.
    if notes and any(word in notes.lower() for word in ("placeholder", "default wear", "not rendered")):
        raise SystemExit("Provider returned a placeholder; exact-item image rejected")
    if not data.startswith(b"RIFF") or data[8:12] != b"WEBP":
        raise SystemExit("Unexpected image bytes")
    OUT.write_bytes(data)
    META.write_text(json.dumps({
        "source": "Inspekt isolated render probe",
        "view": "front", "background": "transparent",
        "http_status": status, "content_type": content_type,
        "rendered": True, "exactness_verified_by_human": False,
        "checkout_enabled": False, "public_deployment": False,
    }, indent=2), encoding="utf-8")
    print("Single image rendered to local preview; visual correspondence still requires manual verification")

if __name__ == "__main__":
    main()
