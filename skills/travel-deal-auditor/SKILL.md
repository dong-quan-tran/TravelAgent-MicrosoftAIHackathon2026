---
name: travel-deal-auditor
description: Compare flight and hotel offers, normalize full travel costs, evaluate hypothetical or verified credit card rewards, and provide transparent cash-versus-points recommendations. Use when building or evaluating a travel search agent or auditing travel price comparisons.
license: MIT
compatibility: Requires access to the offer data supplied by the user or an authorized travel provider. Does not itself grant API access or booking permission.
metadata:
  version: "1.0"
  project: "Hackathon Challenge 03 FareForge AI"
---

# Travel Deal Auditor

## Mission
Help a traveler decide **how to travel for the lowest verifiable all-in cost**, with a separate assessment of convenience and point value. Use tools only if available and authorized. **Never fabricate a live price, confirmed availability, verified award, booking URL, transfer partner or credit card term.**

## Standard workflow
1. **Collect inputs.** Origin(s), destination(s), outbound and return date, travelers, acceptable cabin and stops, carry-on/checked-bag counts, hotel rooms, occupancy, location, cancellation policy, point balances and user-entered points valuations.
2. **Plan sources.** Identify accessible authorized search APIs/web sources. State when requested sources are unavailable. Do not assume Google Flights, Skyscanner, airline direct and OTA prices are all available through a single endpoint.
3. **Search and capture.** For each returned offer record data source, retrieval timestamp UTC, currency, complete itinerary (including connections and fares) or specific hotel room, taxes/fees, and link status. Treat search listings as preliminary, not final booking prices.
4. **Normalize.** Compare like with like. Flight total = fare + known mandatory charges + required baggage and traveler count. Hotel total = stay base + required taxes, resort fees, cleaning and other mandatory charges. If amounts are unknown, mark the comparison as **not verified all-in**.
5. **Classify evidence.** Every offer is `synthetic_demo`, `live_search_unverified`, or `checkout_verified`. Never upgrade a status without supporting evidence. A static fixture or cache is not live.
6. **Evaluate payment choices.** Show separately: cash outlay, points burned, award taxes/fees, earned points on eligible cash spend, subjective economic value of points. Only call an award "available" if the inventory was actually verified.
7. **Recommend carefully.** State the lowest verified cash total, best convenience tradeoff, and potential points strategy. Provide direct comparison arithmetic and explicitly mention any missing data or evidence.
8. **Re-check at action time.** Before an actual booking, verify availability/price with the provider. Ask user approval for any payment, card application or point transfer. This skill has no authority to complete transactions.

## Core math
- Cash flight cost: `travelers × (base_per_person + mandatory_per_person + needed_bag_fees_per_person)` (unless source explicitly returns party-total; **do not multiply again**).
- Cash hotel cost: `stay base + mandatory taxes + mandatory resort/cleaning fees`, for the **correct rooms and occupancy**.
- Points earned approximation: `eligible cash spend × issuer-specific earn multiplier` (or user-input assumption; label appropriately).
- Redemption economic cost: `cash copay + points consumed × user-defined cents-per-point / 100`.
- Points redemption is not necessarily best just because the cash copay is low. Report both **cash savings** and **economic savings**.
- Compare only redemptions permitted by the user's real balances and transfer eligibility, verified where possible.

## Critical anti-error rules
- Never present search-screen prices as checkout confirmed.
- Never assert a transfer partner/bonus/award rate without current authoritative evidence.
- Never treat points earned as dollars saved without stating a valuation assumption.
- Never suppress carrier bags, fare restrictions, hotel taxes/fees or cancellation differences.
- Never substitute a fabricated price when tools fail.
- Never leak API keys, account logins, passport numbers or full payment details into prompts or outputs.
- Never place orders or take financial actions without explicit user permission.
- When a source cannot be searched, explicitly say "not checked"; do not invent a result.

## Preferred output
1. Brief recommendation and caveat level.
2. Compact flights table and hotels table, emphasizing comparable total **USD** costs.
3. Card cash versus points comparison, separated from eligibility assumptions.
4. Clickable source/booking links only if actually provided by tools; UTC time of observed prices.
5. Next verification steps and missing-fee / missing-inventory flags.

## Additional references
- Offer evidence and comparison rules: [`references/comparison_rules.md`](references/comparison_rules.md)
- Machine-readable source and verification example: [`references/offer_schema.json`](references/offer_schema.json)

## Example invocation
"Compare DFW/DAL to New York area March 11–15, 2027, one passenger and carry-on; compare three hotels. My card earns an assumed 3 points/$ and I value points at 1.5 cents. Only recommend an award if verified; otherwise treat it as a scenario."
