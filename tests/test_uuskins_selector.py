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

    def test_survival_forest_ddpat_partial_inventory_reference(self):
        # Reproduce the observed first 20 UUSKINS listings, not full Youpin stock.
        name = "★ Survival Knife | Forest DDPAT (Field-Tested)"
        bands = [
            (.15, .18, 1), (.18, .21, 3), (.21, .24, 2),
            (.24, .27, 2), (.27, .30, 1), (.30, .33, 4),
            (.33, .38, 7),
        ]
        rows = []
        for band_index, (minimum, maximum, count) in enumerate(bands):
            for i in range(count):
                rows.append(self.row(f"{band_index}-{i}", (minimum + maximum) / 2,
                                     100 + (count - i), name))
        self.assertEqual(len(rows), 20)
        for minimum, maximum, expected in bands:
            with self.subTest(minimum=minimum, maximum=maximum):
                selected = selector.select_listings(rows, name, minimum, maximum)
                self.assertEqual(len(selected), expected)
                self.assertEqual([x["price_original"] for x in selected],
                                 sorted(x["price_original"] for x in selected))
        self.assertEqual(selector.select_listings(rows, name, .00, .15), [])
        self.assertEqual(len(selector.select_listings(rows, name, .15, .38)), 10)

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
