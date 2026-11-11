import unittest
from datetime import datetime, timezone
from scripts.youpin_price_math import price_quote

class PriceMathTests(unittest.TestCase):
    def fx(self):
        return {"pair":"CNY/BRL","source":"Wise API","rate":0.8,
                "fetched_at":datetime.now(timezone.utc).isoformat()}
    def test_spread_and_fee(self):
        result = price_quote("100", self.fx())
        self.assertEqual(result["estimated_cost_brl"], "83.33")
        self.assertIsNone(result["sell_price_brl"])
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
