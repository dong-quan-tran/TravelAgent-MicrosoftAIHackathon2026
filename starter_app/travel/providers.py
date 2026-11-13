"""Optional SerpApi adapter; requires user's own authorized API key.

Flight route uses TWO SEPARATE ONE-WAY SEARCHES, NOT A ROUND-TRIP BOOKING
QUOTE. Hotel listings may omit mandatory fees, taxes and exact room terms.
No scraping, bookings, payment collection, or unauthorized API access.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from .engine import airports, hotel_city, number

ENDPOINT = "https://serpapi.com/search.json"
HOTEL_SEARCH_NAMES = {"NYC": "New York City hotels", "TYO": "Tokyo hotels", "LAS": "Las Vegas hotels"}
CITY_PRIMARY_AIRPORT = {"DALLAS": "DFW", "NYC": "JFK", "NEW YORK": "JFK", "TYO": "HND", "TOKYO": "HND", "LAS VEGAS": "LAS"}
FLIGHT_SOURCE = "Google Flights search via SerpApi"
HOTEL_SOURCE = "Google Hotels search via SerpApi"
LIVE_STATUS = "LIVE SEARCH ESTIMATE / NOT CHECKOUT VERIFIED"


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


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_url(value: object) -> str | None:
    """Return a provider-supplied http(s) URL, or None. Never builds or guesses links."""
    if not isinstance(value, str) or len(value) > 2000:
        return None
    try:
        parts = urlsplit(value.strip())
    except ValueError:
        return None
    return value.strip() if parts.scheme in {"http", "https"} and parts.netloc else None


def _search_url(payload: dict, field: str) -> str | None:
    return _safe_url((payload.get("search_metadata") or {}).get(field))


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


def _leg_summary(item: dict, direction: str, search_url: str | None = None) -> dict:
    """Describe one one-way itinerary using only fields the provider supplied."""
    segments = [s for s in (item.get("flights") or []) if isinstance(s, dict)]
    carriers: list[str] = []
    for segment in segments:
        airline = str(segment.get("airline") or "").strip()
        if airline and airline not in carriers:
            carriers.append(airline)
    first = (segments[0].get("departure_airport") or {}) if segments else {}
    last = (segments[-1].get("arrival_airport") or {}) if segments else {}
    duration = int(number(item.get("total_duration")))
    return {
        "direction": direction,
        "carrier": " / ".join(carriers) or "Unknown airline",
        "flight_numbers": [str(s["flight_number"])[:20] for s in segments if s.get("flight_number")],
        "from": first.get("id"), "to": last.get("id"),
        "depart_time": first.get("time"), "arrive_time": last.get("time"),
        "stops": max(0, len(segments) - 1) if segments else None,
        "duration_minutes": duration or None,
        "price_per_adult_usd": round(number(item.get("price")), 2),
        "search_url": search_url,
    }


def _flight_combo_data(outbound: dict, inbound: dict, query: dict, origin: str, destination: str, index: int,
                       observed_utc: str | None = None, out_url: str | None = None, back_url: str | None = None) -> dict:
    out_leg = _leg_summary(outbound, "outbound", out_url)
    back_leg = _leg_summary(inbound, "return", back_url)
    carriers = []
    for leg in (out_leg, back_leg):
        for name in leg["carrier"].split(" / "):
            if name not in carriers:
                carriers.append(name)
    durations = [leg["duration_minutes"] for leg in (out_leg, back_leg)]
    stops = [leg["stops"] for leg in (out_leg, back_leg)]
    return {
        "id": f"LIVE-F{index}", "source": FLIGHT_SOURCE, "carrier": " / ".join(carriers),
        "origin": origin, "destination": destination,
        "depart_date": query["depart_date"], "return_date": query["return_date"],
        "duration_minutes": sum(durations) if all(durations) else None,
        "stops": sum(stops) if all(s is not None for s in stops) else None,
        "legs": [out_leg, back_leg],
        "fare_label": "Two independent one-way search results; NOT a round-trip bookable quote",
        "price_basis": f"Searched for 1 adult, multiplied by {query['travelers']} traveler(s); party seat availability not confirmed",
        "base_per_traveler_usd": round(out_leg["price_per_adult_usd"] + back_leg["price_per_adult_usd"], 2),
        "mandatory_per_traveler_usd": 0, "checked_bag_per_traveler_usd": 0,
        "carry_on_per_traveler_usd": 0, "carry_on_included": None,
        "checked_bag_included": None,
        "award_points_per_traveler": 0, "award_taxes_per_traveler_usd": 0,
        "award_program": None, "data_status": LIVE_STATUS,
        "fees_incomplete": True, "checkout_verified": False, "booking_url": None,
        "source_url": out_url,
        "observed_utc": observed_utc or _now_utc(),
    }


def _nights(query: dict) -> int:
    try:
        return (date.fromisoformat(query["return_date"]) - date.fromisoformat(query["depart_date"])).days
    except (KeyError, ValueError):
        return 0


def _hotel_data(prop: dict, query: dict, index: int, observed_utc: str | None = None) -> dict | None:
    total = number((prop.get("total_rate") or {}).get("extracted_lowest"), -1)
    basis = "Listing total-stay rate (lowest, after listed taxes/fees)"
    if total <= 0:
        nightly = number((prop.get("rate_per_night") or {}).get("extracted_lowest"), -1)
        nights = _nights(query)
        if nightly <= 0 or nights <= 0:
            return None
        total = round(nightly * nights, 2)
        basis = f"Estimate: listed nightly rate × {nights} night(s); no total-stay rate supplied"
    return {"id": f"LIVE-H{index}", "source": HOTEL_SOURCE,
            "name": str(prop.get("name", "Unnamed hotel"))[:120],
            "property_type": str(prop.get("type") or "")[:40] or None,
            "city": hotel_city(query["destination"]), "checkin": query["depart_date"], "checkout": query["return_date"],
            "nights": _nights(query) or None,
            "room_type": "Unspecified listing (confirm occupancy and room type)",
            "rate_basis": basis,
            "stay_rate_usd": total, "mandatory_fees_usd": 0, "refundable": None,
            "max_occupancy": None, "searched_adults": query["travelers"],
            "award_points_total": 0, "award_taxes_usd": 0,
            "award_program": None, "data_status": LIVE_STATUS,
            "fees_incomplete": True, "checkout_verified": False, "booking_url": None,
            "source_url": _safe_url(prop.get("link")),
            "observed_utc": observed_utc or _now_utc()}


def _live_flights(query: dict, key: str, observed: str) -> tuple[list[dict], list[str]]:
    origin = _primary_airport(query["origin"])
    destination = _primary_airport(query["destination"])
    common = {"engine": "google_flights", "type": 2, "currency": "USD", "gl": "us", "hl": "en", "adults": 1}
    outbound = _request({**common, "departure_id": origin, "arrival_id": destination,
                         "outbound_date": query["depart_date"]}, key)
    inbound = _request({**common, "departure_id": destination, "arrival_id": origin,
                        "outbound_date": query["return_date"]}, key)
    out_url, back_url = _search_url(outbound, "google_flights_url"), _search_url(inbound, "google_flights_url")
    out_prices = _flight_leg_fares(outbound)
    back_prices = _flight_leg_fares(inbound)
    flights = []
    for o in out_prices[:3]:
        for i in back_prices[:3]:
            flights.append(_flight_combo_data(o, i, query, origin, destination, len(flights) + 1,
                                              observed, out_url, back_url))
    notes = []
    if not out_prices or not back_prices:
        missing = " and ".join(name for name, legs in (("outbound", out_prices), ("return", back_prices)) if not legs)
        notes.append(f"Live flight search returned no priced {missing} listings for {origin} ↔ {destination} on these dates.")
    return flights, notes


def _live_hotels(query: dict, key: str, observed: str) -> tuple[list[dict], list[str]]:
    city = hotel_city(query["destination"])
    hotel_query = HOTEL_SEARCH_NAMES.get(city, query["destination"] + " hotels")
    response = _request({"engine": "google_hotels", "q": hotel_query, "gl": "us", "hl": "en",
                         "currency": "USD", "check_in_date": query["depart_date"],
                         "check_out_date": query["return_date"], "adults": query["travelers"]}, key)
    properties = [p for p in (response.get("properties") or []) if isinstance(p, dict)][:12]
    hotels = []
    for idx, property_item in enumerate(properties, 1):
        hotel = _hotel_data(property_item, query, idx, observed)
        if hotel:
            hotels.append(hotel)
    notes = []
    if not properties:
        notes.append(f"Live hotel search for “{hotel_query}” returned no listings for these dates.")
    elif not hotels:
        notes.append(f"Live hotel search returned {len(properties)} listing(s), but none included a price for these dates.")
    elif len(hotels) < len(properties):
        notes.append(f"{len(properties) - len(hotels)} hotel listing(s) had no price and were left out.")
    if any(h["rate_basis"].startswith("Estimate") for h in hotels):
        notes.append("Some hotel totals are nightly rate × nights estimates because the provider gave no total-stay rate.")
    return hotels, notes


def live_offers(query: dict) -> tuple[list[dict], list[dict], list[str]]:
    key = os.environ.get("SERPAPI_KEY", "").strip()
    if not key:
        raise ValueError("Live mode requires SERPAPI_KEY. Copy .env.example to .env and provide your own key, or use Demo mode.")
    observed = _now_utc()
    flights: list[dict] = []
    hotels: list[dict] = []
    notes: list[str] = []
    errors: list[str] = []
    try:
        flights, flight_notes = _live_flights(query, key, observed)
        notes += flight_notes
    except ValueError as exc:
        errors.append(f"flights ({exc})")
        notes.append(f"Live flight search failed: {exc} No flight results are shown; demo prices were NOT substituted.")
    try:
        hotels, hotel_notes = _live_hotels(query, key, observed)
        notes += hotel_notes
    except ValueError as exc:
        errors.append(f"hotels ({exc})")
        notes.append(f"Live hotel search failed: {exc} No hotel results are shown; demo prices were NOT substituted.")
    if len(errors) == 2:
        raise ValueError("Live search failed for " + " and ".join(errors))
    warnings = notes + [
        "Flights combine separate outbound and return one-way searches. These are not verified round-trip fares, and booking separately can change cost/protection.",
        "Flight prices were searched for 1 adult and multiplied by the traveler count. Seats for the whole party are not confirmed.",
        "Bag fees are not supplied by this live search. They are shown as Unknown and are NOT included in any price. Do not call this the all-in cheapest price.",
        "Hotel prices are search-listing estimates. Room type, occupancy, cancellation terms and resort/mandatory fees are not confirmed.",
        "City searches currently choose one primary airport rather than scanning all nearby airports.",
        "Points transfer and real award inventory are not supported by this live adapter.",
    ]
    return flights, hotels, warnings
