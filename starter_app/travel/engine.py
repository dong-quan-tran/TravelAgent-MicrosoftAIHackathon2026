"""Deterministic quote normalization, card points, and recommendations.

CRITICAL: Demo offers are fictional. Live offers from adapters are search-result
estimates, not checkout-verified booking inventory. Never label as guaranteed.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "sample_offers.json"
CITY_AIRPORTS = {
    "DALLAS": {"DFW", "DAL"}, "NYC": {"JFK", "LGA", "EWR"},
    "NEW YORK": {"JFK", "LGA", "EWR"}, "TYO": {"HND", "NRT"},
    "TOKYO": {"HND", "NRT"}, "LAS VEGAS": {"LAS"}, "LAS": {"LAS"},
}
HOTEL_CITIES = {"JFK": "NYC", "LGA": "NYC", "EWR": "NYC", "NYC": "NYC", "NEW YORK": "NYC",
                "HND": "TYO", "NRT": "TYO", "TYO": "TYO", "TOKYO": "TYO", "LAS": "LAS", "LAS VEGAS": "LAS"}


def airports(value: str) -> set[str]:
    value = value.strip().upper()
    if "," in value:
        return {part.strip() for part in value.split(",") if part.strip()}
    return CITY_AIRPORTS.get(value, {value})


def hotel_city(value: str) -> str:
    return HOTEL_CITIES.get(value.strip().upper(), value.strip().upper())


def number(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
        if result != result or result in (float("inf"), float("-inf")):
            return default
        return result
    except (TypeError, ValueError):
        return default


def validate(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("Provide a JSON object.")
    origin = str(request.get("origin", "")).strip().upper()
    destination = str(request.get("destination", "")).strip().upper()
    depart = str(request.get("depart_date", ""))
    returning = str(request.get("return_date", ""))
    if not origin or not destination or len(origin) > 30 or len(destination) > 40:
        raise ValueError("Enter valid origin and destination airports or city names.")
    try:
        outbound = date.fromisoformat(depart)
        inbound = date.fromisoformat(returning)
    except ValueError as exc:
        raise ValueError("Use YYYY-MM-DD travel dates.") from exc
    if inbound <= outbound:
        raise ValueError("Return date must be after departure date.")
    def input_number(key: str, default: float) -> float:
        value = request.get(key, default)
        if isinstance(value, bool):
            raise ValueError(f"{key} must be a finite number.")
        parsed = number(value, float("nan"))
        if parsed != parsed:
            raise ValueError(f"{key} must be a finite number.")
        return parsed

    traveler_count = input_number("travelers", 1)
    if not traveler_count.is_integer():
        raise ValueError("Travelers must be a whole number.")
    travelers = int(traveler_count)
    if not (1 <= travelers <= 6):
        raise ValueError("Travelers must be between 1 and 6.")
    mode = str(request.get("mode", "demo")).lower()
    if mode not in {"demo", "live"}:
        raise ValueError("Mode must be demo or live.")
    card_name = str(request.get("card_name", "Illustrative travel card"))[:64]
    multiplier = input_number("card_multiplier", 2)
    cpp = input_number("point_value_cents", 1.25)
    balance = input_number("award_points_balance", 0)
    if not balance.is_integer():
        raise ValueError("Points balance must be a whole number.")
    points = int(balance)
    if not (0 <= multiplier <= 20 and 0.1 <= cpp <= 10 and 0 <= points <= 100000000):
        raise ValueError("Review your rewards input values.")
    for key in ("checked_bag", "carry_on"):
        if key in request and not isinstance(request[key], bool):
            raise ValueError(f"{key} must be true or false.")
    return {"origin": origin, "destination": destination, "depart_date": depart, "return_date": returning,
            "travelers": travelers, "mode": mode, "card_name": card_name,
            "card_multiplier": multiplier, "point_value_cents": cpp, "award_points_balance": points,
            "checked_bag": bool(request.get("checked_bag", False)),
            "carry_on": bool(request.get("carry_on", True))}


def demo_offers(query: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    origin_codes, destination_codes = airports(query["origin"]), airports(query["destination"])
    flights = [f for f in data["flights"]
               if f["origin"] in origin_codes and f["destination"] in destination_codes
               and f["depart_date"] == query["depart_date"] and f["return_date"] == query["return_date"]]
    hotels = [h for h in data["hotels"] if h["city"] == hotel_city(query["destination"])
              and h["checkin"] == query["depart_date"] and h["checkout"] == query["return_date"]
              and query["travelers"] <= h["max_occupancy"]]
    for offer in flights + hotels:
        offer["data_status"] = "FICTIONAL DEMO DATA"
        offer["checkout_verified"] = False
        offer["booking_url"] = None
    return flights, hotels


def price_flight(offer: dict[str, Any], query: dict[str, Any]) -> dict[str, Any]:
    travelers = query["travelers"]
    per_person = number(offer.get("base_per_traveler_usd")) + number(offer.get("mandatory_per_traveler_usd"))
    if query["checked_bag"] and not offer.get("checked_bag_included", False):
        per_person += number(offer.get("checked_bag_per_traveler_usd"))
    if query["carry_on"] and not offer.get("carry_on_included", False):
        per_person += number(offer.get("carry_on_per_traveler_usd"))
    total = round(per_person * travelers, 2)
    points = int(number(offer.get("award_points_per_traveler", 0)) * travelers)
    award_fees = round(number(offer.get("award_taxes_per_traveler_usd")) * travelers, 2)
    enriched = dict(offer, total_cash_usd=total, points_required=points, award_fees_usd=award_fees)
    enriched["reward_points_earned"] = int(total * query["card_multiplier"])
    enriched["cash_after_rewards_estimate_usd"] = round(total - enriched["reward_points_earned"] * query["point_value_cents"] / 100, 2)
    enriched["award_economic_cost_usd"] = round(award_fees + points * query["point_value_cents"] / 100, 2) if points else None
    enriched["award_affordable"] = bool(points and query["award_points_balance"] >= points)
    return enriched


def price_hotel(offer: dict[str, Any], query: dict[str, Any]) -> dict[str, Any]:
    total = round(number(offer.get("stay_rate_usd")) + number(offer.get("mandatory_fees_usd")), 2)
    points = int(number(offer.get("award_points_total", 0)))
    fees = round(number(offer.get("award_taxes_usd")), 2)
    enriched = dict(offer, total_cash_usd=total, points_required=points, award_fees_usd=fees)
    enriched["reward_points_earned"] = int(total * query["card_multiplier"])
    enriched["cash_after_rewards_estimate_usd"] = round(total - enriched["reward_points_earned"] * query["point_value_cents"] / 100, 2)
    enriched["award_economic_cost_usd"] = round(fees + points * query["point_value_cents"] / 100, 2) if points else None
    enriched["award_affordable"] = bool(points and query["award_points_balance"] >= points)
    return enriched


def compare(query: dict[str, Any], flight_raw: list[dict], hotel_raw: list[dict], warnings: list[str] | None = None) -> dict[str, Any]:
    flights = sorted([price_flight(f, query) for f in flight_raw], key=lambda f: f["total_cash_usd"])
    hotels = sorted([price_hotel(h, query) for h in hotel_raw], key=lambda h: h["total_cash_usd"])
    lowest_flight, lowest_hotel = (flights[0] if flights else None), (hotels[0] if hotels else None)
    total = round((lowest_flight["total_cash_usd"] if lowest_flight else 0) +
                  (lowest_hotel["total_cash_usd"] if lowest_hotel else 0), 2)
    best_award = None
    for kind, entries in (("flight", flights), ("hotel", hotels)):
        for offer in entries:
            if offer["award_affordable"]:
                savings = round(offer["total_cash_usd"] - offer["award_economic_cost_usd"], 2)
                candidate = {"kind": kind, "offer_id": offer["id"], "points": offer["points_required"],
                             "fees_usd": offer["award_fees_usd"], "economic_savings_usd": savings,
                             "award_program": offer.get("award_program")}
                if best_award is None or savings > best_award["economic_savings_usd"]:
                    best_award = candidate
    recommendations = []
    if lowest_flight:
        recommendations.append(f"Lowest modeled flight cost: ${lowest_flight['total_cash_usd']:,.2f} for {query['travelers']} traveler(s), including selected bag fees.")
    if lowest_hotel:
        recommendations.append(f"Lowest modeled hotel cost: ${lowest_hotel['total_cash_usd']:,.2f} for the full stay, including modeled mandatory fees.")
    if best_award and best_award["economic_savings_usd"] > 0:
        recommendations.append(f"Illustrative {best_award['kind']} award {best_award['offer_id']} could save an estimated ${best_award['economic_savings_usd']:,.2f} in economic value at your custom point valuation. Verify inventory and eligibility.")
    if not flights or not hotels:
        recommendations.append("Incomplete trip results: no flight or hotel match for part of this search. Do not describe the total as a complete trip quote.")
    all_warnings = list(warnings or [])
    if query["mode"] == "demo":
        all_warnings.insert(0, "DEMO MODE: all fares, hotels, carriers, points and rewards examples are fictional and cannot be booked.")
    else:
        all_warnings.insert(0, "LIVE SEARCH RESULTS are preliminary. Taxes, bag fees, room inclusions, fare rules, booking links, and checkout availability require independent verification.")
    return {"query": query, "flights": flights, "hotels": hotels,
            "summary": {"flight_offer_id": lowest_flight["id"] if lowest_flight else None,
                        "hotel_offer_id": lowest_hotel["id"] if lowest_hotel else None,
                        "modeled_trip_cash_usd": total if flights and hotels else None,
                        "best_illustrative_award": best_award,
                        "modeled_points_earned_if_cash": (lowest_flight["reward_points_earned"] if lowest_flight else 0) + (lowest_hotel["reward_points_earned"] if lowest_hotel else 0),
                        "recommendations": recommendations},
            "warnings": all_warnings}
