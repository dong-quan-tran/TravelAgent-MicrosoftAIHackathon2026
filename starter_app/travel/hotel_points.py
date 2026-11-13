"""Hotel loyalty program detection and Chase/Amex points estimates (see travel/loyalty.py)."""
from __future__ import annotations

import math
from typing import Any

from . import loyalty

TOP_HOTELS = 10
CATALOG = loyalty.Catalog("hotel_points.json")


def table() -> dict[str, Any]:
    return CATALOG.data


def detect_program(hotel_name: Any) -> str | None:
    return CATALOG.detect(hotel_name)


def _parts(hotel_name: Any, cash_usd: float) -> list[loyalty.Part]:
    return [(detect_program(hotel_name), [], cash_usd, "stay")]


def card_count(hotel_name: Any) -> int:
    return len(CATALOG.cards_covering(_parts(hotel_name, 1)))


def estimate(hotel_name: Any, cash_usd: float) -> dict[str, Any] | None:
    return CATALOG.estimate(_parts(hotel_name, cash_usd))


def top_compatible(hotels: list[dict[str, Any]], limit: int = TOP_HOTELS) -> tuple[list[dict[str, Any]], int]:
    return loyalty.top_compatible(hotels, lambda h: card_count(h.get("name")),
                                  lambda h: h.get("stay_rate_usd", math.inf), limit)
