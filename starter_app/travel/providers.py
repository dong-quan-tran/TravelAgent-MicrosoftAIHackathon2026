"""Optional SerpApi adapter; requires user's own authorized API key.

Flight route uses TWO SEPARATE ONE-WAY SEARCHES, NOT A ROUND-TRIP BOOKING
QUOTE. Hotel listings may omit mandatory fees, taxes and exact room terms.
No scraping, bookings, payment collection, or unauthorized API access.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .engine import airports, hotel_city, number

ENDPOINT = "https://serpapi.com/search.json"
HOTEL_SEARCH_NAMES = {"NYC": "New York City hotels", "TYO": "Tokyo hotels", "LAS": "Las Vegas hotels"}
CITY_PRIMARY_AIRPORT = {"DALLAS": "DFW", "NYC": "JFK", "NEW YORK": "JFK", "TYO": "HND", "TOKYO": "HND", "LAS VEGAS": "LAS"}


def _request(params: dict, key: str) -> dict:
    url = ENDPOINT + "?" + urlencode({**params, "api_key": key})
    request = Request(url, headers={"User-Agent": "HackathonTravelAgent/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise ValueError(f"Live provider HTTP error ({exc.code}). Check your API key and limits.") from exc
    except URLError as exc:
        raise ValueError(f"Cannot reach live provider: {exc.reason}") from exc
    if payload.get("error"):
        raise ValueError("Live provider rejected request: " + str(payload["error"])[:220])
    return payload


def _primary_airport(value: str) -> str:
    value = value.strip().upper()
    if value in CITY_PRIMARY_AIRPORT:
        return CITY_PRIMARY_AIRPORT[value]
    selected = sorted(airports(value))
    if not selected:
        raise ValueError("Invalid airport or city")
    return selected[0]


def _flight_leg_fares(payload: dict) -> list[dict]:
    return [item for item in (payload.get("best_flights") or []) + (payload.get("other_flights") or [])
            if isinstance(item, dict) and number(item.get("price"), -1) > 0][:8]


def _flight_combo_data(outbound: dict, inbound: dict, query: dict, origin: str, destination: str, index: int) -> dict:
    out_segs = outbound.get("flights", [])
    back_segs = inbound.get("flights", [])
    airline = (out_segs[0].get("airline", "Unknown airline") if out_segs else "Unknown airline")
    duration = int(number(outbound.get("total_duration")) + number(inbound.get("total_duration")))
    return {
        "id": f"LIVE-F{index}", "source": "Google Flights search via SerpApi", "carrier": airline,
        "origin": origin, "destination": destination,
        "depart_date": query["depart_date"], "return_date": query["return_date"],
        "duration_minutes": duration, "stops": max(0, len(out_segs) - 1) + max(0, len(back_segs) - 1),
        "fare_label": "Two independent one-way search results; NOT a round-trip bookable quote",
        "base_per_traveler_usd": round(number(outbound.get("price")) + number(inbound.get("price")), 2),
        "mandatory_per_traveler_usd": 0, "checked_bag_per_traveler_usd": 0,
        "carry_on_per_traveler_usd": 0, "carry_on_included": None,
        "checked_bag_included": None,
        "award_points_per_traveler": 0, "award_taxes_per_traveler_usd": 0,
        "award_program": None, "data_status": "LIVE SEARCH ESTIMATE / NOT CHECKOUT VERIFIED",
        "fees_incomplete": True, "checkout_verified": False, "booking_url": None,
        "observed_utc": datetime.now(timezone.utc).isoformat(),
    }


def _hotel_data(prop: dict, query: dict, index: int) -> dict | None:
    total_data = prop.get("total_rate") or {}
    total = number(total_data.get("extracted_lowest"), -1)
    if total <= 0:
        return None
    return {"id": f"LIVE-H{index}", "source": "Google Hotels search via SerpApi",
            "name": str(prop.get("name", "Unnamed hotel"))[:120],
            "city": hotel_city(query["destination"]), "checkin": query["depart_date"], "checkout": query["return_date"],
            "room_type": "Unspecified listing (confirm occupancy and room type)",
            "stay_rate_usd": total, "mandatory_fees_usd": 0, "refundable": None,
            "max_occupancy": query["travelers"], "award_points_total": 0, "award_taxes_usd": 0,
            "award_program": None, "data_status": "LIVE SEARCH ESTIMATE / NOT CHECKOUT VERIFIED",
            "fees_incomplete": True, "checkout_verified": False, "booking_url": None,
            "observed_utc": datetime.now(timezone.utc).isoformat()}


def live_offers(query: dict) -> tuple[list[dict], list[dict], list[str]]:
    key = os.environ.get("SERPAPI_KEY", "").strip()
    if not key:
        raise ValueError("Live mode requires SERPAPI_KEY. Copy .env.example to .env and provide your own key, or use Demo mode.")
    origin = _primary_airport(query["origin"])
    destination = _primary_airport(query["destination"])
    common = {"engine": "google_flights", "type": 2, "currency": "USD", "gl": "us", "hl": "en", "adults": 1}
    outbound = _request({**common, "departure_id": origin, "arrival_id": destination,
                         "outbound_date": query["depart_date"]}, key)
    inbound = _request({**common, "departure_id": destination, "arrival_id": origin,
                        "outbound_date": query["return_date"]}, key)
    out_prices = _flight_leg_fares(outbound)
    back_prices = _flight_leg_fares(inbound)
    flights = []
    for o in out_prices[:3]:
        for i in back_prices[:3]:
            flights.append(_flight_combo_data(o, i, query, origin, destination, len(flights) + 1))
    city = hotel_city(query["destination"])
    hotel_query = HOTEL_SEARCH_NAMES.get(city, query["destination"] + " hotels")
    hotels_response = _request({"engine": "google_hotels", "q": hotel_query, "gl": "us", "hl": "en",
                                "currency": "USD", "check_in_date": query["depart_date"],
                                "check_out_date": query["return_date"], "adults": query["travelers"]}, key)
    hotels = []
    for idx, property_item in enumerate(hotels_response.get("properties", [])[:12], 1):
        hotel = _hotel_data(property_item, query, idx)
        if hotel:
            hotels.append(hotel)
    warnings = [
        "Flights combine separate outbound and inbound one-way searches. These are not verified round-trip fares, and booking separately can change cost/protection.",
        "Live provider does not guarantee full bag charges; the prototype assumes $0 when fees are unknown. DO NOT call this the true all-in cheapest price.",
        "Hotel total_rate is a search-listing estimate; occupancy, taxes, room type, mandatory charges and checkout details need verification.",
        "City searches currently choose one primary airport rather than scanning all nearby airports.",
        "Points transfer and real award inventory are not supported by this live adapter."
    ]
    return flights, hotels, warnings
