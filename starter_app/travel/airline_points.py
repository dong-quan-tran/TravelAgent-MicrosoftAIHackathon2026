"""Airline program detection and Chase/Amex points estimates for flights (see travel/loyalty.py).

Each leg is priced from the FIRST airline on that leg (usually the marketing/validating
carrier). A leg can be paid through the airline's own program or an alliance partner
program (e.g. American via British Airways or Iberia Avios); each card uses whichever
reachable program needs the fewest card points. Partner award charts are not modeled:
partner prices are cash-based estimates like everything else here.
"""
from __future__ import annotations

import math
import re
from functools import lru_cache
from typing import Any

from . import loyalty

TOP_FLIGHTS = 10
CATALOG = loyalty.Catalog("airline_points.json")


def table() -> dict[str, Any]:
    return CATALOG.data


@lru_cache(maxsize=1)
def _airline_patterns() -> list[tuple[re.Pattern, dict[str, Any]]]:
    return [(re.compile(r"\b(?:" + "|".join(a["brands"]) + r")\b", re.IGNORECASE), a)
            for a in table()["airlines"]]


def airline_programs(airline: Any) -> tuple[str | None, list[str]]:
    """(own program, partner programs) for an airline name; (None, []) if unknown."""
    if isinstance(airline, str):
        for pattern, entry in _airline_patterns():
            if pattern.search(airline):
                return entry["own_program"], list(entry["partner_programs"])
    return None, []


def detect_program(airline: Any) -> str | None:
    return airline_programs(airline)[0]


def _leg_parts(flight: dict[str, Any], travelers: int) -> list[loyalty.Part]:
    parts = []
    for leg in flight.get("legs") or []:
        own, partners = airline_programs(str(leg.get("carrier") or "").split(" / ")[0])
        cash = leg.get("price_per_adult_usd")
        cash = cash * travelers if isinstance(cash, (int, float)) else 0
        parts.append((own, partners, cash, leg.get("direction") or "leg"))
    return parts


def card_count(flight: dict[str, Any]) -> int:
    return len(CATALOG.cards_covering(_leg_parts(flight, 1)))


def estimate(flight: dict[str, Any], travelers: int) -> dict[str, Any] | None:
    return CATALOG.estimate(_leg_parts(flight, travelers))


def top_compatible(flights: list[dict[str, Any]], limit: int = TOP_FLIGHTS) -> tuple[list[dict[str, Any]], int]:
    return loyalty.top_compatible(flights, card_count,
                                  lambda f: f.get("base_per_traveler_usd", math.inf), limit)
