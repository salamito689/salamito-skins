"""Read-only Salamito pricing math for individual UUSKINS listings.

No API price is assumed to be USD or CNY. The caller must supply an
independently verified source currency and two fresh Wise rates.
This module never changes storefront prices or enables checkout.
"""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime, timezone

MAX_QUOTE_AGE_SECONDS = 900

def decimal_positive(value, label):
    if isinstance(value, bool):
        raise ValueError(f"{label}: boolean is not a price")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label}: invalid number") from None
    if not result.is_finite() or result <= 0:
        raise ValueError(f"{label}: must be finite and positive")
    return result

def verified_wise_rate(quote, pair, now=None):
    if not isinstance(quote, dict) or quote.get("pair") != pair or quote.get("source") != "Wise API":
        raise ValueError(f"Missing verified Wise {pair} quote")
    timestamp = datetime.fromisoformat(quote["fetched_at"].replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("Wise timestamp needs timezone")
    now = now or datetime.now(timezone.utc)
    age = (now - timestamp).total_seconds()
    if not -120 <= age <= MAX_QUOTE_AGE_SECONDS:
        raise ValueError("Wise quote stale or future dated")
    return decimal_positive(quote["rate"], pair)

def price_brl(raw_price, source_currency, cny_brl_quote, usd_cny_quote=None, now=None):
    """Apply exactly 1% to CNY/BRL and add R$0.025 per yuan.

    USD input first converts to CNY using Wise USD/CNY; it does not
    reconstruct an original seller RMB price or remove platform fees.
    """
    amount = decimal_positive(raw_price, "raw_price")
    if source_currency not in ("CNY", "USD"):
        raise ValueError("UUSKINS price currency must be independently verified")
    cny_brl = verified_wise_rate(cny_brl_quote, "CNY/BRL", now)
    cny_amount = amount if source_currency == "CNY" else amount * verified_wise_rate(usd_cny_quote, "USD/CNY", now)
    adjusted_cny_brl = cny_brl * Decimal("1.01") + Decimal("0.025")
    return {
        "source_currency": source_currency,
        "raw_price": str(amount),
        "cny_equivalent": str(cny_amount),
        "wise_cny_brl": str(cny_brl),
        "adjusted_cny_brl": str(adjusted_cny_brl),
        "price_brl": str((cny_amount * adjusted_cny_brl).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "price_is_seller_original_cny": source_currency == "CNY",
        "checkout_enabled": False,
    }
