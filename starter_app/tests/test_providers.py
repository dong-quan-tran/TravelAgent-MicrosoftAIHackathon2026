import os
import unittest
from unittest.mock import patch
from travel.providers import _flight_leg_fares, _hotel_data, _primary_airport, live_offers
from travel.engine import validate


class ProvidersTests(unittest.TestCase):
    def test_parse_flight_result(self):
        result = _flight_leg_fares({"best_flights": [{"price": 200, "flights": []}, {"price": 0}],
                                    "other_flights": [{"price": 250} ,{"price": "N/A"}]})
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["price"], 200)

    def test_parse_hotel_total_rate(self):
        q = {"destination": "NYC", "depart_date": "2027-03-11", "return_date": "2027-03-15", "travelers": 1}
        result = _hotel_data({"name": "Illustrative", "total_rate": {"extracted_lowest": 500}}, q, 1)
        self.assertEqual(result["stay_rate_usd"], 500)
        self.assertTrue(result["fees_incomplete"])
        self.assertFalse(result["checkout_verified"])

    def test_city_mapping_primary_not_nearby_search(self):
        self.assertEqual(_primary_airport("DALLAS"), "DFW")

    def test_live_requires_credential_and_no_demo_fallback(self):
        q = validate({"origin":"DFW", "destination":"JFK", "depart_date":"2027-03-11", "return_date":"2027-03-15", "travelers":1, "mode":"live"})
        with patch.dict(os.environ, {"SERPAPI_KEY": ""}):
            with self.assertRaisesRegex(ValueError, "SERPAPI_KEY"):
                live_offers(q)


if __name__ == "__main__":
    unittest.main()
