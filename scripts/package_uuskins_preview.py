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
    (OUT / "iniciar-servidor.bat").write_text(
        "@echo off\\r\\n"
        "cd /d \\"%~dp0\\"\\r\\n"
        "where py >nul 2>nul\\r\\n"
        "if %errorlevel%==0 (\\r\\n"
        "  start \\"\\" \\"http://localhost:8765\\"\\r\\n"
        "  py -3 -m http.server 8765 --bind 127.0.0.1\\r\\n"
        ") else (\\r\\n"
        "  where python >nul 2>nul\\r\\n"
        "  if %errorlevel%==0 (\\r\\n"
        "    start \\"\\" \\"http://localhost:8765\\"\\r\\n"
        "    python -m http.server 8765 --bind 127.0.0.1\\r\\n"
        "  ) else (\\r\\n"
        "    echo Python nao encontrado. Instale Python 3 ou execute python -m http.server 8765 nesta pasta.\\r\\n"
        "    pause\\r\\n"
        "  )\\r\\n"
        ")\\r\\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "Salamito Skins — isolated UUSKINS staging preview\\n"
        "Experimental only. No purchases, no reservations, currency unverified.\\n"
        "Windows: execute iniciar-servidor.bat (requires Python 3).\\n"\n        "The server binds only to 127.0.0.1:8765 and opens the preview in a browser.\\n"\n        "Keep the console open during testing; Ctrl+C to stop.\\n"
        "This artifact is NOT deployed to the production catalog.\\n",
        encoding="utf-8",
    )
    print("Isolated static preview packaged (not published).")

if __name__ == "__main__":
    main()
