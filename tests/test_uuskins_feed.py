"""Offline tests for UUSKINS staging feed parsing and safety gates.
Run: python -m unittest discover -s tests -p 'test_uuskins_feed.py'
No network, credentials, orders or production files required.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_uuskins_feed", ROOT / "scripts" / "build_uuskins_feed.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class TestFeedParsing(unittest.TestCase):
    def test_string_float(self):
        self.assertAlmostEqual(builder.parse_float("0.3447971343994140600"), 0.34479713439941406)
        self.assertEqual(builder.parse_float("0"), 0)
        self.assertEqual(builder.parse_float("1"), 1)
        for invalid in ("nan", "inf", "-0.1", "1.1", "", None, True):
            self.assertIsNone(builder.parse_float(invalid))

    def test_string_paint_values(self):
        self.assertEqual(builder.parse_integer("440"), 440)
        self.assertEqual(builder.parse_integer(282), 282)
        self.assertEqual(builder.parse_integer("0"), 0)
        for invalid in ("4.4", "-1", "nan", "", None, True, "100001"):
            self.assertIsNone(builder.parse_integer(invalid))

    def test_invalid_price_is_rejected(self):
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).isoformat()
        raw = {"fetched_at": timestamp, "currency": "unverified", "results": [{
            "status": "ok", "market_hash_name": "AK-47 | Redline (Field-Tested)",
            "sample_listings": [
                {"id": "invalid", "price": "NaN"},
                {"id": "valid", "price": "24.52", "wearValue": "0.3447971343994140600", "paintSeed": "440", "paintIndex": "282"},
                {"id": "valid", "price": "25.00"}
            ]
        }]}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            output = Path(directory) / "output.json"
            source.write_text(json.dumps(raw), encoding="utf-8")
            with patch.object(builder, "SOURCE", source), patch.object(builder, "OUTPUT", output):
                builder.main()
            feed = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(feed["listing_count"], 1)
        self.assertEqual(feed["listings"][0]["id"], "valid")
        self.assertEqual(feed["listings"][0]["paint_seed"], 440)
        self.assertEqual(feed["listings"][0]["paint_index"], 282)
        self.assertEqual(feed["checkout_enabled"], False)

if __name__ == "__main__":
    unittest.main()
