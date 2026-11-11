"""Package a local-only HTTP staging preview. Never deploys production."""
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
    # Exact-item images are opt-in and must be independently verified against SKU ID.
    # Never fall back to a generic model picture.
    image_dir = ROOT / "exact-images"
    if image_dir.is_dir():
        output_images = OUT / "exact-images"
        output_images.mkdir(exist_ok=True)
        for item in data["listings"]:
            name = item.get("exact_image_file")
            if not isinstance(name, str) or not name.isascii():
                continue
            if not name.replace("_", "").replace("-", "").replace(".", "").isalnum() or not name.lower().endswith((".webp", ".avif", ".png")):
                continue
            source = image_dir / name
            if source.is_file() and source.stat().st_size <= 2_000_000:
                shutil.copyfile(source, output_images / name)
    launcher = """@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  start "" "http://127.0.0.1:8765"
  py -3 -m http.server 8765 --bind 127.0.0.1
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    start "" "http://127.0.0.1:8765"
    python -m http.server 8765 --bind 127.0.0.1
  ) else (
    echo Python 3 nao encontrado. Instale Python 3 para executar este teste.
    pause
  )
)
"""
    (OUT / "iniciar-servidor.bat").write_bytes(launcher.replace("\n", "\r\n").encode("utf-8"))
    (OUT / "README.txt").write_text(
        "Salamito Skins — isolated UUSKINS staging preview\n"
        "Experimental only. No purchases, reservations or validated currency.\n"
        "Windows: double-click iniciar-servidor.bat (requires Python 3).\n"
        "Preview opens at http://127.0.0.1:8765; keep console open during testing.\n"
        "Press Ctrl+C in console to stop. Not deployed to production.\n",
        encoding="utf-8",
    )
    print("Isolated static HTTP preview packaged (not published).")

if __name__ == "__main__":
    main()
