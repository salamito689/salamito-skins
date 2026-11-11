"""Offline tests for per-range and phase selection."""
import importlib.util
from pathlib import Path
import unittest

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("selector", root / "scripts" / "uuskins_listing_selector.py")
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)


class TestSelector(unittest.TestCase):
    def row(self, ident, wear, price, name="★ Bayonet | Autotronic (Field-Tested)", index=None):
        return {"id": str(ident), "float": wear, "price_original": price,
                "market_hash_name": name, "paint_index": index}

    def test_ten_cheapest_per_float_range(self):
        rows = [self.row(i, 0.16, 100-i) for i in range(15)]
        rows += [self.row(100+i, 0.19, 200-i) for i in range(12)]
        first = selector.select_listings(rows, "★ Bayonet | Autotronic (Field-Tested)", .15, .18)
        second = selector.select_listings(rows, "★ Bayonet | Autotronic (Field-Tested)", .18, .21)
        self.assertEqual(len(first), 10)
        self.assertEqual(len(second), 10)
        self.assertEqual(first[0]["price_original"], 86)
        self.assertEqual(second[0]["price_original"], 189)
        self.assertTrue(all(.15 <= r["float"] < .18 for r in first))
        self.assertTrue(all(.18 <= r["float"] < .21 for r in second))

    def test_phase_separation(self):
        name = "★ Talon Knife | Doppler (Factory New)"
        rows = [self.row(1, .01, 90, name, 418), self.row(2, .01, 70, name, 419)]
        self.assertEqual([r["id"] for r in selector.select_listings(rows, name, 0, .07, "Phase 1")], ["1"])
        self.assertEqual([r["id"] for r in selector.select_listings(rows, name, 0, .07, "Phase 2")], ["2"])

    def test_talon_specific_paint_indices(self):
        name = "★ Talon Knife | Doppler (Factory New)"
        rows = [self.row(1, .01, 90, name, 852), self.row(2, .02, 70, name, 854)]
        self.assertEqual([r["id"] for r in selector.select_listings(rows, name, 0, .07, "Phase 1")], ["1"])
        self.assertEqual([r["id"] for r in selector.select_listings(rows, name, 0, .07, "Phase 3")], ["2"])

    def test_global_cheapest_fails_closed_without_full_coverage(self):
        rows = [self.row(1, .16, 10)]
        name = "★ Bayonet | Autotronic (Field-Tested)"
        for coverage in (None, {}, {"scope": "first_returned_batch_per_model",
                                     "global_cheapest_verified": False,
                                     "source_pagination_verified": False}):
            with self.subTest(coverage=coverage), self.assertRaisesRegex(ValueError, "Complete market coverage"):
                selector.select_listings(rows, name, .15, .18,
                                         require_complete=True, coverage=coverage)
        self.assertEqual(len(selector.select_listings(rows, name, .15, .18)), 1)

    def test_float_boundary_and_invalids(self):
        rows = [self.row("a", .18, 5), self.row("b", None, 1), self.row("c", .16, float("nan"))]
        self.assertEqual(selector.select_listings(rows, "★ Bayonet | Autotronic (Field-Tested)", .15, .18), [])
        self.assertEqual(len(selector.select_listings(rows, "★ Bayonet | Autotronic (Field-Tested)", .18, .21)), 1)
        with self.assertRaises(ValueError):
            selector.select_listings(rows, "★ Bayonet | Autotronic (Field-Tested)", .15, .18, limit=11)


if __name__ == "__main__":
    unittest.main()
