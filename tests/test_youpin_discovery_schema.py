import unittest
from scripts.youpin_discovery_schema import build_request, validate_request, summarize_response

class DiscoverySchemaTests(unittest.TestCase):
    def test_observed_payload(self):
        expected = {"gameId":"730","listType":"10","listSortType":1,"pageIndex":1,
                    "pageSize":10,"sortType":0,"templateId":"50002"}
        self.assertEqual(build_request("50002"), expected)
        self.assertEqual(validate_request(expected), expected)
    def test_reject_bad_payload(self):
        with self.assertRaises(ValueError):
            validate_request({"gameId":"730","templateId":"50002"})
    def test_no_assumed_listing_ids(self):
        result = summarize_response({"Code":0,"Data":{"items":[{"id":50002}]}})
        self.assertFalse(result["individual_listing_ids_verified"])
    def test_api_error(self):
        self.assertEqual(summarize_response({"Code":403})["status"], "api_error")

if __name__ == "__main__":
    unittest.main()
