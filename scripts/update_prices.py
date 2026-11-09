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
phase_prices = {}
def positive(value):
    try:
        n = float(value)
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None
def pattern_cny(entry, buff):
    native = entry.get("native_currency") or {}
    cny = positive(native.get("ask")) if isinstance(native, dict) else None
    if cny:
        return cny
    usd = positive(entry.get("ask"))
    generic_usd = positive(buff.get("ask"))
    generic_native = buff.get("native_currency") or {}
    generic_cny = positive(generic_native.get("ask")) if isinstance(generic_native, dict) else None
    if usd and generic_usd and generic_cny:
        return round(usd * generic_cny / generic_usd, 4)
    return None
for name, record in data.items():
    if not isinstance(record, dict):
        continue
    buff = record.get("buff")
    if isinstance(buff, dict):
        patterns = buff.get("patterns")
        if isinstance(patterns, list):
            variants = {}
            for entry in patterns:
                if not isinstance(entry, dict):
                    continue
                pattern = str(entry.get("pattern") or "").strip()
                if pattern not in ("Phase 1", "Phase 2", "Phase 3", "Phase 4", "Ruby", "Sapphire", "Black Pearl", "Emerald"):
                    continue
                cny_phase = pattern_cny(entry, buff)
                if cny_phase:
                    variants[pattern] = {"cny": cny_phase, "source": "Buff163", "updated_at": entry.get("updated_at")}
            if variants:
                phase_prices[name] = variants
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
output = {"phase_prices": phase_prices, "phase_items": len(phase_prices), "source": "OpenSkin / YouPin + Buff163 phases", "source_updated_at": payload.get("updated_at"), "fetched_at": datetime.now(timezone.utc).isoformat(), "count": len(prices), "prices": prices}
pathlib.Path("prices.json").write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"Preços YouPin: {len(prices)}; famílias Doppler Buff com fases: {len(phase_prices)}")
