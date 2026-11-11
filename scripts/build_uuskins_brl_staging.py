"""Generate read-only BRL diagnostics for UUSKINS staging listings.

Requires explicit verified currency input. Never guesses USD/CNY from price
magnitude; never changes public storefront or enables checkout.
"""
import json
import os
from pathlib import Path
from uuskins_price_math import price_brl

SOURCE = Path("uuskins-feed-staging.json")
QUOTES = Path("uuskins-wise-quotes-staging.json")
OUTPUT = Path("uuskins-prices-brl-staging.json")

def main():
    currency = os.getenv("UUSKINS_VERIFIED_PRICE_CURRENCY", "").strip().upper()
    simulation = os.getenv("UUSKINS_STAGING_ASSUME_USD", "") == "1"
    if simulation and currency:
        raise SystemExit("Simulation and verified currency are mutually exclusive")
    if simulation:
        currency = "USD"
    if currency not in ("USD", "CNY"):
        raise SystemExit("Currency not verified: set UUSKINS_VERIFIED_PRICE_CURRENCY only after authoritative confirmation")
    feed = json.loads(SOURCE.read_text(encoding="utf-8"))
    if feed.get("currency") != "unverified" or feed.get("checkout_enabled") is not False:
        raise ValueError("Unexpected UUSKINS staging feed state")
    quote_bundle = json.loads(QUOTES.read_text(encoding="utf-8"))
    if quote_bundle.get("production") is not False or quote_bundle.get("checkout_enabled") is not False:
        raise ValueError("Unexpected Wise staging quote state")
    quotes = quote_bundle["quotes"]
    results = []
    for item in feed["listings"]:
        computed = price_brl(item["price_original"], currency,
                             quotes["CNY/BRL"], quotes.get("USD/CNY"))
        results.append({"id": item["id"], "market_hash_name": item["market_hash_name"],
                        "float": item["float"], "paint_seed": item["paint_seed"],
                        "raw_price": computed["raw_price"],
                        "source_currency": currency,
                        "price_brl": computed["price_brl"]})
    OUTPUT.write_text(json.dumps({
        "source": "UUSKINS + Wise staging, not for checkout",
        "source_currency": currency,
        "currency_verification": "unverified_assumption_usd" if simulation else "external_manual_required",
        "simulation_only": simulation,
        "wise_quotes": {k: {"rate": v["rate"], "fetched_at": v["fetched_at"]} for k, v in quotes.items()},
        "production": False, "checkout_enabled": False,
        "listings": results
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Calculated {len(results)} staging prices; no production files changed")

if __name__ == "__main__":
    main()
