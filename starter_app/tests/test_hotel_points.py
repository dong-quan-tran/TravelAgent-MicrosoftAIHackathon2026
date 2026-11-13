import unittest

from travel.engine import demo_offers, price_hotel, validate
from travel.hotel_points import card_count, detect_program, estimate, table, top_compatible
from travel import airline_points


class DetectTests(unittest.TestCase):
    def test_brands_map_to_programs(self):
        cases = {
            "Courtyard by Marriott New York Manhattan": "marriott",
            "The St. Regis New York": "marriott",
            "W New York - Times Square": "marriott",
            "The Times Square EDITION": "marriott",
            "Le Méridien New York, Central Park": "marriott",
            "Hilton Garden Inn Times Square": "hilton",
            "DoubleTree by Hilton Hotel New York": "hilton",
            "Hampton Inn Manhattan": "hilton",
            "Park Hyatt Tokyo": "hyatt",
            "Andaz Tokyo Toranomon Hills": "hyatt",
            "Holiday Inn Express Manhattan": "ihg",
            "Kimpton Hotel Eventi": "ihg",
            "La Quinta Inn by Wyndham": "wyndham",
            "Days Inn by Wyndham": "wyndham",
            "Comfort Inn Midtown": "choice",
            "Cambria Hotel New York": "choice",
        }
        for name, program in cases.items():
            self.assertEqual(detect_program(name), program, name)

    def test_independent_and_lookalikes_are_not_matched(self):
        for name in ("The Plaza", "Pod Times Square", "Wanderlust Inn", "Bellagio", "Edition Coffee Hostel",
                     "Shiltonia Inn", None, 123):
            self.assertIsNone(detect_program(name), name)


class EstimateTests(unittest.TestCase):
    def test_marriott_both_cards_one_to_one(self):
        est = estimate("Westin Times Square", 600)  # 600 / $0.0075 = 80,000 Bonvoy
        self.assertEqual(est["programs"][0]["program_points"], 80_000)
        self.assertEqual(est["card_count"], 2)
        self.assertEqual({o["card_points"] for o in est["cards"]}, {80_000})
        self.assertEqual(est["lowest_cards"], ["Amex", "Chase"])
        self.assertTrue(est["estimate"])

    def test_hilton_amex_one_to_two_halves_points(self):
        est = estimate("Hilton Midtown", 540)  # 540 / $0.004 = 135,000 Hilton -> 67,500 -> 68,000 Amex
        self.assertEqual(est["programs"][0]["program_points"], 135_000)
        self.assertEqual([o["card"] for o in est["cards"]], ["amex_mr"])
        self.assertEqual(est["lowest_card_points"], 68_000)

    def test_hyatt_chase_only_with_ratio_note(self):
        est = estimate("Grand Hyatt", 330)  # 330 / $0.0165 = 20,000
        self.assertEqual(est["lowest_card_points"], 20_000)
        self.assertEqual(est["lowest_cards"], ["Chase"])
        self.assertIn("4:3", est["cards"][0]["notes"][0])

    def test_no_estimate_without_program_or_price(self):
        self.assertIsNone(estimate("Independent Inn", 300))
        self.assertIsNone(estimate("Westin", 0))

    def test_card_counts_follow_table(self):
        self.assertEqual(card_count("Marriott Marquis"), 2)
        for name in ("Hyatt Place", "Holiday Inn", "Ramada", "Hilton", "Quality Inn"):
            self.assertEqual(card_count(name), 1, name)
        self.assertEqual(card_count("The Plaza"), 0)


class RankingTests(unittest.TestCase):
    def test_top_compatible_prefers_more_cards_then_cash_and_caps(self):
        hotels = ([{"name": f"Hyatt Place {i}", "stay_rate_usd": 100 + i} for i in range(8)] +
                  [{"name": f"Sheraton {i}", "stay_rate_usd": 500 - i} for i in range(5)] +
                  [{"name": "Indie", "stay_rate_usd": 10}])
        top, compatible = top_compatible(hotels)
        self.assertEqual((len(top), compatible), (10, 10))
        self.assertEqual([h["name"] for h in top[:5]], [f"Sheraton {i}" for i in (4, 3, 2, 1, 0)])
        self.assertEqual([h["name"] for h in top[5:]], [f"Hyatt Place {i}" for i in range(5)])

    def test_top_compatible_never_returns_nothing(self):
        hotels = [{"name": "Indie B", "stay_rate_usd": 200}, {"name": "Westin", "stay_rate_usd": 900},
                  {"name": "Indie A", "stay_rate_usd": 100}]
        top, compatible = top_compatible(hotels)
        self.assertEqual([h["name"] for h in top], ["Westin", "Indie A", "Indie B"])
        self.assertEqual(compatible, 1)
        top, compatible = top_compatible([{"name": "Indie", "stay_rate_usd": 50}])
        self.assertEqual((len(top), compatible), (1, 0))

    def test_engine_attaches_estimate_and_sort_value(self):
        q = validate({"origin": "DFW", "destination": "NYC", "depart_date": "2027-03-11",
                      "return_date": "2027-03-15", "mode": "live"})
        live = {"id": "LIVE-H1", "name": "Hilton Midtown", "stay_rate_usd": 640, "mandatory_fees_usd": 0,
                "stay_rate_before_taxes_usd": 540, "award_points_total": 0, "award_taxes_usd": 0}
        priced = price_hotel(live, q)
        self.assertEqual(priced["points_estimate"]["programs"][0]["cash_basis_usd"], 540, "uses pre-tax rate when given")
        self.assertEqual(priced["points_sort_value"], 68_000)
        indie = price_hotel({**live, "name": "Indie Inn"}, q)
        self.assertIsNone(indie["points_estimate"])
        self.assertIsNone(indie["points_sort_value"])

    def test_demo_hotels_sort_on_listed_award_points(self):
        q = validate({"origin": "DALLAS", "destination": "NYC", "depart_date": "2027-03-11",
                      "return_date": "2027-03-15", "mode": "demo"})
        _, hotels = demo_offers(q)
        values = {h["id"]: price_hotel(h, q)["points_sort_value"] for h in hotels}
        self.assertEqual(values, {"NYC-H1": None, "NYC-H2": 45_000})

    def test_table_sources_dated(self):
        data = table()
        self.assertTrue(data["valuation_source"]["url"].startswith("https://"))
        for card in data["cards"].values():
            self.assertTrue(card["source_url"].startswith("https://"))
            for partner in card["partners"]:
                self.assertIn(partner["program"], data["programs"])


class AirlineTests(unittest.TestCase):
    @staticmethod
    def flight(out_airline, out_price, back_airline, back_price):
        return {"legs": [{"direction": "outbound", "carrier": out_airline, "price_per_adult_usd": out_price},
                         {"direction": "return", "carrier": back_airline, "price_per_adult_usd": back_price}]}

    def test_detects_carriers(self):
        cases = {"United": "united", "Delta": "delta", "Air France": "flying_blue", "KLM": "flying_blue",
                 "ANA": "ana", "Aeroméxico": "aeromexico", "British Airways": "british_airways",
                 "American": None, "Alaska": None, "Spirit": None, "Banana Air": None}
        for name, program in cases.items():
            self.assertEqual(airline_points.detect_program(name), program, name)

    def test_jetblue_differs_by_card(self):
        # $270 round trip on JetBlue / 1.35c = 20,000 TrueBlue. Chase 1:1 = 20,000; Amex 5:4 = 25,000.
        est = airline_points.estimate(self.flight("JetBlue", 135, "JetBlue", 135), 1)
        self.assertEqual(est["programs"][0]["program_points"], 20_000)
        self.assertEqual({c["card_short"]: c["card_points"] for c in est["cards"]}, {"Chase": 20_000, "Amex": 25_000})
        self.assertEqual(est["lowest_cards"], ["Chase"])

    def test_partner_programs_open_up_airlines(self):
        # American: neither card transfers to AAdvantage, but both reach oneworld Avios partners.
        self.assertEqual(airline_points.detect_program("American"), None)
        est = airline_points.estimate(self.flight("American", 135, "American", 135), 1)
        self.assertEqual(est["card_count"], 2)
        self.assertTrue(all(p["via_partner"] for c in est["cards"] for p in c["programs"]))
        # $270 / 1.35c Avios = 20,000 for Chase; Amex picks the same value via BA/Iberia/Qatar Avios.
        self.assertEqual({c["card_short"]: c["card_points"] for c in est["cards"]}, {"Chase": 20_000, "Amex": 20_000})
        # United (own program Chase-only) is reachable from Amex through Star Alliance partners.
        self.assertEqual(airline_points.card_count(self.flight("United", 200, "United", 200)), 2)

    def test_card_must_cover_every_leg(self):
        # Southwest: Chase only, no partners. Emirates: Amex only (5:4), no partners. No single card covers both.
        self.assertIsNone(airline_points.estimate(self.flight("Southwest", 200, "Emirates", 600), 1))
        self.assertEqual(airline_points.card_count(self.flight("Southwest", 200, "Emirates", 600)), 0)
        self.assertEqual(airline_points.card_count(self.flight("Spirit", 90, "Spirit", 90)), 0)
        est = airline_points.estimate(self.flight("Emirates", 400, "Emirates", 400), 1)  # $800/1c=80,000 -> 100,000 Amex
        self.assertEqual([(c["card_short"], c["card_points"]) for c in est["cards"]], [("Amex", 100_000)])

    def test_same_program_both_legs_is_one_transfer(self):
        est = airline_points.estimate(self.flight("Southwest", 61, "Southwest", 61), 1)  # $122/1.25c = 9,760 -> 9,800
        self.assertEqual(len(est["programs"]), 1)
        self.assertEqual(est["programs"][0]["covers"], ["outbound", "return"])
        self.assertEqual(est["programs"][0]["program_points"], 9_800)
        self.assertEqual(est["lowest_card_points"], 10_000, "one transfer rounded once, not 2 x 5,000")

    def test_engine_flight_sort_value(self):
        q = validate({"origin": "DFW", "destination": "JFK", "depart_date": "2027-03-11",
                      "return_date": "2027-03-15", "mode": "live", "travelers": 1})
        from travel.engine import price_flight
        offer = {**self.flight("Southwest", 125, "Southwest", 125), "id": "LIVE-F1",
                 "base_per_traveler_usd": 250, "mandatory_per_traveler_usd": 0}
        self.assertEqual(price_flight(offer, q)["points_sort_value"], 20_000)
        self.assertIsNone(price_flight({**offer, "legs": []}, q)["points_sort_value"])


if __name__ == "__main__":
    unittest.main()
