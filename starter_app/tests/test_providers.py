import os
import unittest
from unittest.mock import patch
from travel.providers import _flight_leg_fares, _hotel_data, _primary_airport, _safe_url, live_offers
from travel.engine import compare, validate

# Synthetic payloads shaped like SerpApi responses. Names, prices and flight
# numbers are fictional; no test here makes a network call or needs a key.
FLIGHT_OUT = {
    "search_metadata": {"google_flights_url": "https://www.google.com/travel/flights?test=out"},
    "best_flights": [{"price": 200, "total_duration": 300, "flights": [
        {"airline": "United", "flight_number": "TA 100",
         "departure_airport": {"id": "DFW", "time": "2027-03-11 06:00"},
         "arrival_airport": {"id": "ORD", "time": "2027-03-11 08:30"}},
        {"airline": "Air Canada", "flight_number": "OA 200",
         "departure_airport": {"id": "ORD", "time": "2027-03-11 09:30"},
         "arrival_airport": {"id": "JFK", "time": "2027-03-11 12:00"}}]}],
}
FLIGHT_BACK = {
    "search_metadata": {"google_flights_url": "javascript:alert(1)"},
    "other_flights": [{"price": 150, "total_duration": 240, "flights": [
        {"airline": "United", "flight_number": "TA 300",
         "departure_airport": {"id": "JFK", "time": "2027-03-15 10:00"},
         "arrival_airport": {"id": "DFW", "time": "2027-03-15 13:00"}}]}],
}
HOTELS = {"properties": [
    {"name": "Courtyard Fictional Midtown", "type": "hotel", "link": "https://example.com/hotel",
     "total_rate": {"extracted_lowest": 800, "extracted_before_taxes_fees": 690},
     "rate_per_night": {"extracted_lowest": 200}},
    {"name": "Hampton Inn Fictional Lodge", "link": "ftp://example.com/x", "rate_per_night": {"extracted_lowest": 100}},
    {"name": "Fictional No Price Hotel"},
    {"name": "Fictional Independent Hotel", "total_rate": {"extracted_lowest": 300}},
]}


def live_query(travelers=1):
    return validate({"origin": "DFW", "destination": "JFK", "depart_date": "2027-03-11",
                     "return_date": "2027-03-15", "travelers": travelers, "mode": "live"})


def fake_provider(flights=None, hotels=None, flight_error=None, hotel_error=None):
    def respond(params, key):
        if params["engine"] == "google_flights":
            if flight_error:
                raise ValueError(flight_error)
            return (flights or {})[params["departure_id"]]
        if hotel_error:
            raise ValueError(hotel_error)
        return hotels
    return respond


class ProvidersTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict(os.environ, {"SERPAPI_KEY": "test-not-a-real-key"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_live(self, travelers=1, **kwargs):
        defaults = {"flights": {"DFW": FLIGHT_OUT, "JFK": FLIGHT_BACK}, "hotels": HOTELS}
        defaults.update(kwargs)
        with patch("travel.providers._request", side_effect=fake_provider(**defaults)):
            return live_offers(live_query(travelers))

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
        self.assertIsNone(result["max_occupancy"], "occupancy must not be invented")

    def test_hotel_nightly_fallback_is_labeled_estimate(self):
        q = {"destination": "NYC", "depart_date": "2027-03-11", "return_date": "2027-03-15", "travelers": 1}
        result = _hotel_data({"name": "Nightly", "rate_per_night": {"extracted_lowest": 100}}, q, 1)
        self.assertEqual(result["stay_rate_usd"], 400)
        self.assertTrue(result["rate_basis"].startswith("Estimate"))

    def test_hotel_without_any_price_is_skipped(self):
        q = {"destination": "NYC", "depart_date": "2027-03-11", "return_date": "2027-03-15", "travelers": 1}
        self.assertIsNone(_hotel_data({"name": "No price", "total_rate": {"extracted_lowest": "N/A"}}, q, 1))

    def test_safe_url_only_allows_http_and_https(self):
        self.assertEqual(_safe_url("https://example.com/a"), "https://example.com/a")
        self.assertIsNone(_safe_url("javascript:alert(1)"))
        self.assertIsNone(_safe_url("ftp://example.com"))
        self.assertIsNone(_safe_url(None))

    def test_city_mapping_primary_not_nearby_search(self):
        self.assertEqual(_primary_airport("DALLAS"), "DFW")

    def test_live_requires_credential_and_no_demo_fallback(self):
        with patch.dict(os.environ, {"SERPAPI_KEY": ""}):
            with self.assertRaisesRegex(ValueError, "SERPAPI_KEY"):
                live_offers(live_query())

    def test_flight_legs_carriers_and_party_basis(self):
        flights, _, _ = self.run_live(travelers=2)
        self.assertEqual(len(flights), 1)
        offer = flights[0]
        self.assertEqual(offer["carrier"], "United / Air Canada")
        self.assertEqual([leg["direction"] for leg in offer["legs"]], ["outbound", "return"])
        self.assertEqual(offer["legs"][0]["flight_numbers"], ["TA 100", "OA 200"])
        self.assertEqual(offer["legs"][0]["depart_time"], "2027-03-11 06:00")
        self.assertEqual(offer["stops"], 1)
        self.assertEqual(offer["base_per_traveler_usd"], 350)
        self.assertIn("1 adult", offer["price_basis"])
        self.assertEqual(offer["source_url"], "https://www.google.com/travel/flights?test=out")
        self.assertIsNone(offer["legs"][1]["search_url"], "unsafe provider URL must be dropped")
        self.assertIsNone(offer["carry_on_included"])
        self.assertTrue(offer["fees_incomplete"])

    def test_live_hotels_report_skipped_listings(self):
        _, hotels, warnings = self.run_live()
        # Marriott (Chase + Amex) ranks above Hilton (Amex only) even though it costs more;
        # the independent hotel fills the list after them instead of being dropped.
        self.assertEqual([h["name"] for h in hotels],
                         ["Courtyard Fictional Midtown", "Hampton Inn Fictional Lodge", "Fictional Independent Hotel"])
        self.assertEqual(hotels[0]["stay_rate_before_taxes_usd"], 690)
        self.assertIsNone(hotels[1]["stay_rate_before_taxes_usd"])
        self.assertTrue(any("Showing 3 of 3 priced hotels" in w and "Only 2 qualified" in w for w in warnings))
        self.assertEqual(hotels[0]["source_url"], "https://example.com/hotel")
        self.assertIsNone(hotels[1]["source_url"])
        self.assertTrue(any("1 hotel listing(s) had no price" in w for w in warnings))
        self.assertTrue(len({h["observed_utc"] for h in hotels}) == 1)

    def test_empty_hotel_results_explain_why(self):
        _, hotels, warnings = self.run_live(hotels={"properties": []})
        self.assertEqual(hotels, [])
        self.assertTrue(any("returned no listings" in w for w in warnings))
        _, hotels, warnings = self.run_live(hotels={"properties": [{"name": "Unpriced"}]})
        self.assertEqual(hotels, [])
        self.assertTrue(any("none included a price" in w for w in warnings))
        _, hotels, warnings = self.run_live(hotels={"properties": [{"name": "Indie Inn", "total_rate": {"extracted_lowest": 90}}]})
        self.assertEqual([h["name"] for h in hotels], ["Indie Inn"], "never filtered to nothing")
        self.assertTrue(any("Only 0 qualified" in w for w in warnings))

    def test_flights_filtered_to_card_compatible_pairings(self):
        def leg(airline, price, origin, dest):
            return {"price": price, "flights": [{"airline": airline, "departure_airport": {"id": origin},
                                                 "arrival_airport": {"id": dest}}]}
        out = {"best_flights": [leg("Spirit", 90, "DFW", "JFK"), leg("Southwest", 200, "DFW", "JFK"),
                                leg("American", 250, "DFW", "JFK")]}
        back = {"best_flights": [leg("Spirit", 95, "JFK", "DFW"), leg("Emirates", 600, "JFK", "DFW"),
                                 leg("American", 260, "JFK", "DFW")]}
        flights, _, warnings = self.run_live(flights={"DFW": out, "JFK": back})
        carriers = [f["carrier"] for f in flights]
        self.assertEqual(len(flights), 9, "all 9 pairings shown: fewer than 10, so nothing is dropped")
        self.assertEqual(carriers[0], "American", "American both ways: Chase AND Amex via Avios partners")
        # Southwest/American: Chase only. American/Emirates: Amex only. Then the uncovered ones by price.
        self.assertEqual(set(carriers[1:3]), {"Southwest / American", "American / Emirates"})
        self.assertEqual(carriers[3:5], ["Spirit", "Southwest / Spirit"])
        self.assertTrue(any("Only 3 qualified" in w for w in warnings))

    def test_hotels_capped_at_ten_and_second_page_fetched_when_short(self):
        page1 = {"properties": [{"name": f"Holiday Inn Test {i}", "total_rate": {"extracted_lowest": 100 + i}} for i in range(6)]
                 + [{"name": "Indie", "total_rate": {"extracted_lowest": 50}}],
                 "serpapi_pagination": {"next_page_token": "tok"}}
        page2 = {"properties": [{"name": f"Westin Test {i}", "total_rate": {"extracted_lowest": 900 + i}} for i in range(6)],
                 "serpapi_pagination": {"next_page_token": "tok2"}}
        calls = []
        def respond(params, key):
            if params["engine"] == "google_flights":
                return {"DFW": FLIGHT_OUT, "JFK": FLIGHT_BACK}[params["departure_id"]]
            calls.append(params.get("next_page_token"))
            return page2 if params.get("next_page_token") else page1
        with patch("travel.providers._request", side_effect=respond):
            _, hotels, _ = live_offers(live_query())
        self.assertEqual(calls, [None, "tok"], "fetches exactly one extra page")
        self.assertEqual(len(hotels), 10)
        self.assertTrue(all(h["name"].startswith("Westin") for h in hotels[:6]), "two-card hotels first")
        self.assertEqual(len({h["id"] for h in hotels}), 10)

    def test_empty_flight_leg_is_reported(self):
        flights, _, warnings = self.run_live(flights={"DFW": FLIGHT_OUT, "JFK": {"best_flights": []}})
        self.assertEqual(flights, [])
        self.assertTrue(any("no priced return listings" in w for w in warnings))

    def test_hotel_provider_error_keeps_flights_without_demo_fallback(self):
        flights, hotels, warnings = self.run_live(hotel_error="Live provider HTTP error (500).")
        self.assertEqual(len(flights), 1)
        self.assertEqual(hotels, [])
        self.assertTrue(any("Live hotel search failed" in w and "NOT substituted" in w for w in warnings))
        self.assertTrue(all(f["data_status"].startswith("LIVE") for f in flights))

    def test_flight_provider_error_keeps_hotels(self):
        flights, hotels, warnings = self.run_live(flight_error="Cannot reach live provider")
        self.assertEqual(flights, [])
        self.assertEqual(len(hotels), 3)
        self.assertTrue(any("Live flight search failed" in w for w in warnings))

    def test_both_provider_errors_raise(self):
        with self.assertRaisesRegex(ValueError, "flights .* and hotels"):
            self.run_live(flight_error="down", hotel_error="down")

    def test_live_offers_pass_through_engine(self):
        query = live_query(travelers=2)
        flights, hotels, warnings = self.run_live(travelers=2)
        result = compare(query, flights, hotels, warnings)
        self.assertEqual(result["flights"][0]["total_cash_usd"], 700)
        self.assertEqual(result["hotels"][0]["id"], "LIVE-H4", "cheapest hotel overall, even without a points option")
        self.assertTrue(all(o["fees_incomplete"] for o in result["flights"] + result["hotels"]))


if __name__ == "__main__":
    unittest.main()
