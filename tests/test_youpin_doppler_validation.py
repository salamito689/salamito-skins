import unittest
from scripts.youpin_doppler_validation import validate_phase_price, validate_distinct_phases

class DopplerValidationTests(unittest.TestCase):
    def item(self, phase="Phase 2", family="Doppler"):
        return {"market_hash_name": "★ Karambit | "+family+" (Factory New)",
                "family": family, "phase": phase, "currency": "CNY",
                "price_rmb": "1000.00", "source": "test_fixture",
                "fetched_at": "2026-11-11T00:00:00Z"}
    def test_valid_phase(self):
        self.assertEqual(validate_phase_price(self.item())["phase"], "Phase 2")
    def test_distinct_phase_keys(self):
        result=validate_distinct_phases([self.item("Phase 1"),self.item("Phase 2")])
        self.assertEqual(len(result),2)
    def test_reject_duplicate(self):
        with self.assertRaises(ValueError): validate_distinct_phases([self.item(),self.item()])
    def test_reject_wrong_family_phase(self):
        with self.assertRaises(ValueError): validate_phase_price(self.item("Ruby","Gamma Doppler"))
    def test_reject_missing_phase(self):
        with self.assertRaises(ValueError): validate_phase_price(self.item(None))
    def test_reject_wrong_currency(self):
        x=self.item();x["currency"]="USD"
        with self.assertRaises(ValueError): validate_phase_price(x)

if __name__=="__main__": unittest.main()
