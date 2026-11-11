"""Staging-only Youpin CNY -> BRL pricing, Decimal arithmetic.
The Wise quote must be supplied from a fresh trusted fx.json snapshot.
Confirmed delivery-cost formula:
  (listing RMB * (Wise BRL per CNY + 0.025)) * 1.01
This is NOT a sales margin, nor a checkout price.
"""
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

MAX_FX_AGE_SECONDS = 3600
SPREAD_BRL_PER_CNY = Decimal("0.025")
DELIVERY_FEE = Decimal("0.01")

def decimal(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a number")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Invalid number") from exc
    if not d.is_finite():
        raise ValueError("Nonfinite number")
    return d

def price_quote(price_rmb, fx):
    if fx.get("pair") != "CNY/BRL" or fx.get("source") != "Wise API":
        raise ValueError("Expected Wise CNY/BRL quote")
    rate = decimal(fx.get("rate"))
    if not Decimal("0.1") < rate < Decimal("3"):
        raise ValueError("Implausible FX quote")
    stamp = datetime.fromisoformat(fx["fetched_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("FX timestamp missing timezone")
    age = (datetime.now(timezone.utc) - stamp).total_seconds()
    if not 0 <= age <= MAX_FX_AGE_SECONDS:
        raise ValueError("FX quote stale or future-dated")
    amount = decimal(price_rmb)
    if not Decimal("0") < amount < Decimal("10000000"):
        raise ValueError("Invalid listing price")
    effective = rate + SPREAD_BRL_PER_CNY
    base = amount * effective
    total = (base * (Decimal("1") + DELIVERY_FEE)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"currency": "BRL", "source_currency": "CNY", "price_rmb": str(amount),
            "wise_rate": str(rate), "spread_brl_per_cny": str(SPREAD_BRL_PER_CNY),
            "effective_rate": str(effective), "delivery_fee_percent": "1",
            "subtotal_brl": str(base.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "estimated_cost_brl": str(total), "sell_price_brl": None,
            "status": "staging_estimate_not_for_checkout"}

def selling_price(cost_brl, markup_percent):
    """Optional markup on total acquisition/delivery cost, not profit margin on revenue."""
    cost = decimal(cost_brl)
    markup = decimal(markup_percent)
    if cost <= 0 or not Decimal("0") <= markup <= Decimal("100"):
        raise ValueError("Invalid cost or markup")
    result = (cost * (Decimal("1") + markup / Decimal("100"))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"cost_brl": str(cost), "markup_percent": str(markup),
            "sell_price_brl": str(result), "gross_profit_brl": str(result - cost),
            "status": "staging_only"}

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--rmb", required=True)
    p.add_argument("--fx", default="fx.json")
    a = p.parse_args()
    with open(a.fx, encoding="utf-8") as file:
        fx = json.load(file)
    print(json.dumps(price_quote(a.rmb, fx), ensure_ascii=False, indent=2))
