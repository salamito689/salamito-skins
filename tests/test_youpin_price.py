import unittest
from scripts.probe_youpin_price import extract

class YoupinPriceTests(unittest.TestCase):
    def test_valid(self):
        result = extract({"code": 0, "data": {"Id": 2097902427, "Price": "157.4", "MarketHashName": "AK-47 | Redline (Field-Tested)", "PaintSeed": 299}}, "2097902427")
        self.assertEqual(result["price_rmb"], 157.4)
        self.assertEqual(result["currency"], "CNY")
        self.assertFalse(result["checkout_enabled"])
    def test_wrong_listing(self):
        with self.assertRaises(ValueError):
            extract({"code": 0, "data": {"Id": 12, "Price": 100}}, "2097902427")
    def test_bad_price(self):
        for price in (-1, 0, "NaN", True):
            with self.subTest(price=price), self.assertRaises(ValueError):
                extract({"code": 0, "data": {"Id": 2097902427, "Price": price}})
    def test_failed_response(self):
        with self.assertRaises(ValueError):
            extract({"code": 403, "data": {"Id": 2097902427, "Price": 157.4}})
if __name__ == "__main__":
    unittest.main()
