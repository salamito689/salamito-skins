"""Offline tests for guarded UUSKINS/Wise conversion; no network required."""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from uuskins_price_math import price_brl

NOW = datetime(2026, 11, 11, tzinfo=timezone.utc)
def quote(pair, rate, age=0):
    return {"pair": pair, "rate": rate, "source": "Wise API",
            "fetched_at": (NOW - timedelta(seconds=age)).isoformat()}

class PricingTests(unittest.TestCase):
    def test_cny_one_percent_and_two_point_five_cents(self):
        result = price_brl("4500", "CNY", quote("CNY/BRL", "0.833059"), now=NOW)
        self.assertEqual(result["price_brl"], "3897.25")
        self.assertFalse(result["checkout_enabled"])

    def test_usd_two_wise_legs(self):
        result = price_brl("100", "USD", quote("CNY/BRL", "0.8"),
                           quote("USD/CNY", "7"), now=NOW)
        self.assertEqual(result["price_brl"], "583.10")
        self.assertFalse(result["price_is_seller_original_cny"])

    def test_unknown_currency_blocked(self):
        with self.assertRaises(ValueError):
            price_brl("705.22", "unverified", quote("CNY/BRL", "0.8"), now=NOW)

    def test_usd_without_wise_leg_blocked(self):
        with self.assertRaises(ValueError):
            price_brl("705.22", "USD", quote("CNY/BRL", "0.8"), now=NOW)

    def test_stale_wise_blocked(self):
        with self.assertRaises(ValueError):
            price_brl("4500", "CNY", quote("CNY/BRL", "0.8", age=901), now=NOW)

    def test_invalid_prices_blocked(self):
        for value in ("NaN", "-1", "Infinity", 0, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                price_brl(value, "CNY", quote("CNY/BRL", "0.8"), now=NOW)

if __name__ == "__main__":
    unittest.main()
