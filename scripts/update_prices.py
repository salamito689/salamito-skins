import json
import pathlib
import urllib.request
from datetime import datetime, timezone

URL = "https://api.openskin.dev/v1/prices/all"
req = urllib.request.Request(URL, headers={"User-Agent": "SalamitoSkins/1.0 (public reference prices)", "Accept": "application/json", "Accept-Encoding": "identity"})
with urllib.request.urlopen(req, timeout=90) as response:
    payload = json.load(response)
data = payload.get("data")
if not isinstance(data, dict) or len(data) < 1000:
    raise RuntimeError("Resposta vazia/inválida; mantendo preços anteriores")
prices = {}
for name, record in data.items():
    if not isinstance(record, dict):
        continue
    yp = record.get("youpin")
    if not isinstance(yp, dict):
        continue
    native = yp.get("native_currency") or {}
    cny = native.get("ask") if isinstance(native, dict) else None
    usd = yp.get("ask")
    try:
        cny = float(cny) if cny is not None else None
        usd = float(usd) if usd is not None else None
    except (ValueError, TypeError):
        continue
    if (cny is None or cny <= 0) and (usd is None or usd <= 0):
        continue
    prices[name] = {"cny": cny if cny and cny > 0 else None, "usd": usd if usd and usd > 0 else None}
if len(prices) < 100:
    raise RuntimeError("Poucos preços válidos; mantendo arquivo anterior")
output = {"source": "OpenSkin / YouPin", "source_updated_at": payload.get("updated_at"), "fetched_at": datetime.now(timezone.utc).isoformat(), "count": len(prices), "prices": prices}
pathlib.Path("prices.json").write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"Preços válidos: {len(prices)}")
