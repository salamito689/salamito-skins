"""Fetch both Wise FX legs for isolated UUSKINS staging.

Uses existing WISE_API_TOKEN secret; never logs or stores credentials.
Does not write production fx.json, prices.json, or storefront files.
"""
import json
import os
import pathlib
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

OUT = pathlib.Path("uuskins-wise-quotes-staging.json")
PAIRS = (("CNY", "BRL"), ("USD", "CNY"))

def fetch_pair(source, target, token):
    url = f"https://api.wise.com/v1/rates?source={source}&target={target}"
    request = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "User-Agent": "SalamitoSkins-UUSKINS-Staging/1.0",
    })
    with urllib.request.urlopen(request, timeout=18) as response:
        payload = json.load(response)
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        raise ValueError(f"Wise {source}/{target}: unexpected response")
    try:
        rate = Decimal(str(payload[0]["rate"]))
    except (KeyError, ValueError, InvalidOperation, TypeError):
        raise ValueError(f"Wise {source}/{target}: invalid rate") from None
    if not rate.is_finite() or rate <= 0:
        raise ValueError(f"Wise {source}/{target}: nonpositive rate")
    if (source, target) == ("CNY", "BRL") and not Decimal("0.1") < rate < Decimal("3"):
        raise ValueError("Wise CNY/BRL outside conservative range")
    if (source, target) == ("USD", "CNY") and not Decimal("1") < rate < Decimal("20"):
        raise ValueError("Wise USD/CNY outside conservative range")
    return {"pair": f"{source}/{target}", "rate": str(rate),
            "source": "Wise API", "fetched_at": datetime.now(timezone.utc).isoformat()}

def main():
    token = os.environ.get("WISE_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("Missing WISE_API_TOKEN; no staging quotes generated")
    quotes = {f"{source}/{target}": fetch_pair(source, target, token)
              for source, target in PAIRS}
    OUT.write_text(json.dumps({"schema_version": 1, "quotes": quotes,
                                "production": False, "checkout_enabled": False},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    print("Staging Wise CNY/BRL and USD/CNY quotes fetched; no production files changed")

if __name__ == "__main__":
    main()
