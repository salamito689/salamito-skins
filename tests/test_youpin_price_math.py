import unittest
from datetime import datetime, timezone
from scripts.youpin_price_math import price_quote, DEFAULT_SPREAD_BRL_PER_CNY, DEFAULT_DELIVERY_FEE_PERCENT

class PriceMathTests(unittest.TestCase):
    def fx(self):
        return {"pair":"CNY/BRL","source":"Wise API","rate":0.8,
                "fetched_at":datetime.now(timezone.utc).isoformat()}
    def test_confirmed_defaults(self):
        self.assertEqual(str(DEFAULT_SPREAD_BRL_PER_CNY), "0.025")
        self.assertEqual(str(DEFAULT_DELIVERY_FEE_PERCENT), "1")
        quote = price_quote("157.40", self.fx())
        self.assertEqual(quote["estimated_cost_brl"], "131.16")
        self.assertEqual(quote["spread_brl_per_cny"], "0.025")
        self.assertEqual(quote["delivery_fee_percent"], "1")
        self.assertIsNone(quote["sell_price_brl"])
    def test_spread_and_fee(self):
        result = price_quote("100", self.fx())
        self.assertEqual(result["estimated_cost_brl"], "83.33")
        self.assertIsNone(result["sell_price_brl"])
    def test_delivery_fee_label(self):
        self.assertEqual(price_quote("100", self.fx())["delivery_fee_percent"], "1")
    def test_custom_spread_and_fee(self):
        result = price_quote("100", self.fx(), "0.05", "2")
        self.assertEqual(result["estimated_cost_brl"], "86.70")
        self.assertEqual(result["spread_brl_per_cny"], "0.05")
        self.assertEqual(result["delivery_fee_percent"], "2")
    def test_reject_invalid_configuration(self):
        with self.assertRaises(ValueError):
            price_quote("100", self.fx(), "-0.01", "1")
        with self.assertRaises(ValueError):
            price_quote("100", self.fx(), "0.025", "-1")
    def test_reject_wrong_pair(self):
        f = self.fx(); f["pair"]="USD/BRL"
        with self.assertRaises(ValueError): price_quote("100", f)
    def test_reject_invalid(self):
        for value in ["NaN", "-1", 0]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                price_quote(value, self.fx())
    def test_reject_stale(self):
        f=self.fx(); f["fetched_at"]="2020-01-01T00:00:00Z"
        with self.assertRaises(ValueError): price_quote("100", f)

if __name__ == "__main__": unittest.main()
