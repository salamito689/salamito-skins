"""Prepare a self-contained static UUSKINS staging preview for isolated hosting.

Never publishes to GitHub Pages or production. The output is a downloadable
artifact only. Source must have passed feed validation in the workflow.
"""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "uuskins-staging-preview"
FEED = ROOT / "uuskins-feed-staging.json"
HTML = ROOT / "uuskins-lab.html"

def main():
    data = json.loads(FEED.read_text(encoding="utf-8"))
    if data.get("checkout_enabled") is not False or data.get("currency") != "unverified":
        raise ValueError("Only non-transactional unverified-currency preview may be packaged")
    if not data.get("listings"):
        raise ValueError("Empty preview feed")
    if not HTML.is_file():
        raise FileNotFoundError(HTML)
    OUT.mkdir(exist_ok=True)
    shutil.copyfile(HTML, OUT / "index.html")
    shutil.copyfile(FEED, OUT / "uuskins-feed-staging.json")
    (OUT / "README.txt").write_text(
        "Salamito Skins — isolated UUSKINS staging preview\\n"
        "Experimental only. No purchases, no reservations, currency unverified.\\n"
        "Serve this folder over HTTP(S) to load the JSON automatically.\\n"
        "This artifact is NOT deployed to the production catalog.\\n",
        encoding="utf-8",
    )
    print("Isolated static preview packaged (not published).")

if __name__ == "__main__":
    main()
