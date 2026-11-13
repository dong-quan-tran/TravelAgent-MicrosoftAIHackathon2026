"""Shared loyalty-points estimator for hotel and airline catalogs.

ESTIMATES ONLY. Live listings carry no award prices, so points are derived from cash:
cash ÷ a published average value per point, then converted to each card's points with
its transfer ratio. Real award prices are dynamic and can differ substantially.

Catalog JSON shape (data/hotel_points.json, data/airline_points.json):
  programs: {id: {name, short, cents_per_point, brands: [regex, ...]}}
  cards:    {id: {name, short, source_url, source_updated, increment,
                  partners: [{program, points, program_points, minimum?, increment?, note?}]}}
A ratio of points:program_points = 5:4 means 1,000 card points -> 800 program points.
"""
from __future__ import annotations

import json
import math
import re
from functools import cached_property
from pathlib import Path
from typing import Any, Callable, Iterable

# (own_program or None, partner_programs, cash_usd, label)
Part = tuple[str | None, list[str], float, str]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def ratio_label(partner: dict[str, Any]) -> str:
    points, units = partner["points"], partner["program_points"]
    scale = 1000 // points if 1000 % points == 0 else 1
    return f"{points * scale:,}:{units * scale:,}"


class Catalog:
    def __init__(self, filename: str):
        self.path = DATA_DIR / filename

    @cached_property
    def data(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    @cached_property
    def _patterns(self) -> list[tuple[str, re.Pattern]]:
        return [(pid, re.compile(r"\b(?:" + "|".join(p["brands"]) + r")\b", re.IGNORECASE))
                for pid, p in self.data["programs"].items() if p.get("brands")]

    def detect(self, name: Any) -> str | None:
        """Program whose brand words appear in `name`; None if unrecognised."""
        if not isinstance(name, str):
            return None
        return next((pid for pid, pattern in self._patterns if pattern.search(name)), None)

    def _partner(self, card: dict[str, Any], program_id: str) -> dict[str, Any] | None:
        return next((p for p in card["partners"] if p["program"] == program_id), None)

    def _program_points(self, program_id: str, cash: float) -> int:
        cents = self.data["programs"][program_id]["cents_per_point"]
        return math.ceil(cash / (cents / 100) / 100) * 100

    def _card_points(self, program_points: int, card: dict[str, Any], partner: dict[str, Any]) -> int:
        increment = int(partner.get("increment", card["increment"]))
        minimum = int(partner.get("minimum", increment))
        raw = math.ceil(program_points * partner["points"] / partner["program_points"])
        transfer = max(minimum, math.ceil(raw / increment) * increment)
        while transfer * partner["program_points"] // partner["points"] < program_points:
            transfer += increment
        return transfer

    def _choose(self, card: dict[str, Any], part: Part) -> str | None:
        """Cheapest program (in card points) this card can reach for one part; own program wins ties."""
        own, partners, cash, _ = part
        options = ([own] if own else []) + [p for p in partners if p != own]
        reachable = [p for p in options if self._partner(card, p)]
        if not reachable:
            return None
        def cost(pid: str) -> float:
            partner = self._partner(card, pid)
            return self._program_points(pid, max(cash, 0.01)) * partner["points"] / partner["program_points"]
        return min(reachable, key=lambda pid: (cost(pid), pid != own))

    def cards_covering(self, parts: Iterable[Part]) -> list[str]:
        """Cards that can reach a program for EVERY part (empty if any part has no program)."""
        parts = list(parts)
        if not parts:
            return []
        return [cid for cid, card in self.data["cards"].items()
                if all(self._choose(card, part) for part in parts)]

    def estimate(self, parts: list[Part]) -> dict[str, Any] | None:
        """Estimate for one offer made of parts (own_program, partner_programs, cash_usd, label),
        e.g. one part per flight leg. Each card books each part through its cheapest reachable program."""
        if not parts or any(not isinstance(cash, (int, float)) or cash <= 0 for _, _, cash, _ in parts):
            return None
        cards = []
        for cid in self.cards_covering(parts):
            card = self.data["cards"][cid]
            grouped: dict[str, dict[str, Any]] = {}
            for part in parts:  # same program on several parts -> one transfer
                pid = self._choose(card, part)
                entry = grouped.setdefault(pid, {"cash": 0.0, "labels": [], "partner": False})
                entry["cash"] += part[2]
                entry["labels"].append(part[3])
                entry["partner"] = entry["partner"] or pid != part[0]
            programs, total, ratios, notes = [], 0, [], []
            for pid, entry in grouped.items():
                program = self.data["programs"][pid]
                partner = self._partner(card, pid)
                points = self._program_points(pid, entry["cash"])
                total += self._card_points(points, card, partner)
                programs.append({"program": pid, "name": program["name"], "short": program["short"],
                                 "cents_per_point": program["cents_per_point"],
                                 "cash_basis_usd": round(entry["cash"], 2), "program_points": points,
                                 "covers": entry["labels"], "via_partner": entry["partner"]})
                ratios.append(f"{program['short']} {ratio_label(partner)}")
                if partner.get("note"):
                    notes.append(f"{program['short']}: {partner['note']}")
            cards.append({"card": cid, "card_name": card["name"], "card_short": card["short"],
                          "card_points": total, "ratios": ratios, "notes": notes, "programs": programs})
        if not cards:
            return None
        cards.sort(key=lambda c: (c["card_points"], c["card_name"]))
        lowest = cards[0]["card_points"]
        source = self.data["valuation_source"]
        return {"estimate": True, "programs": cards[0]["programs"], "cards": cards, "card_count": len(cards),
                "lowest_card_points": lowest,
                "lowest_cards": [c["card_short"] for c in cards if c["card_points"] == lowest],
                "valuation_source": source["name"], "valuation_url": source["url"]}

    def public_sources(self) -> dict[str, Any]:
        return {"checked_on": self.data["checked_on"], "notice": self.data["notice"],
                "valuation_source": self.data["valuation_source"],
                "cards": [{"name": c["name"], "source_url": c["source_url"], "source_updated": c["source_updated"]}
                          for c in self.data["cards"].values()]}


def top_compatible(items: list[dict[str, Any]], card_count: Callable[[dict[str, Any]], int],
                   cash: Callable[[dict[str, Any]], float], limit: int = 10) -> tuple[list[dict[str, Any]], int]:
    """Up to `limit` items: those reachable from the most cards first (cheaper first within a tie),
    then, only if there are not enough, the cheapest items no card can pay for. Never filters to nothing.
    Returns (items, number_of_card_compatible_items_included)."""
    counted = [(card_count(item), item) for item in items]
    compatible = sorted((pair for pair in counted if pair[0] > 0), key=lambda pair: (-pair[0], cash(pair[1])))
    others = sorted((item for count, item in counted if count == 0), key=cash)
    chosen = [item for _, item in compatible[:limit]]
    return chosen + others[:limit - len(chosen)], len(chosen)
