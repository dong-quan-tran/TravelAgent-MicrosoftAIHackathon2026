# Hackathon #3 — Judging Rubric (100 points)

| Category | Points | Full-credit evidence |
|---|---:|---|
| Verified total travel cost / savings | **25** | Lowest real, equivalent, bookable flight+hotel price with verified fees and screenshots/URLs. No credit here for mock prices. |
| Rewards optimization | **20** | Correct earning rules and real award availability where claimed; transparent point economics and balance checks. |
| Accuracy and verification | **20** | Timestamped sources; correct traveler/occupancy, taxes, bags, booking links; handles missing/changed price honestly. |
| User experience | **10** | Search, sort and understand results in a clean, genuinely interactive app. |
| Agent functionality | **10** | Takes changed requirements, calls data tools, applies consistent rules, explains decision and errors. |
| Portability and documentation | **10** | Cold install on a different laptop, runnable app plus Agent Skill, no secret dependencies, tests pass. |
| Creativity | **5** | Useful differentiator: flexible locations/dates, destination discovery, alert, loyalty value etc. |
| **TOTAL** | **100** | |

## Recommended objective price-scoring method
- A judge chooses the exact itinerary/hotel constraints at demo time.
- For each comparable option, record the **checkout-confirmed USD total** (or the deepest verifiable step available) *at roughly the same time*. A stale API fare or materially different hotel room cannot win.
- Among teams with verified comparable results, score savings relative to the judge's manually verified reference at the same time. Suggested **price score**: `25 × clamp(verified_savings / target_savings, 0, 1)`, where a reasonable target (e.g., 10% of baseline) is announced beforehand. If no verified lower price, still award method credit in other categories.
- Do **not** compare a 1-person economy airfare to 2-person premium economy, or a nonrefundable hotel to a refundable rate without identifying the difference.
- Keep subjective convenience separate from lowest price; time, cancellations and loyalty benefits should appear in the explanation.

## Price verification example
Baseline manual total = $1,500. Student claims $1,320; reviewer finds the actual linked checkout total is $1,420 after fees. **Verified savings = $80**, not $180. If unavailable at checkout, count as *unverified* and award no verified-price credit for that offer.

## Rewards correctness checks
- Show **cash outlay**, **points burned**, **points earned**, and **economic cost** separately.
- Economic cost of redemption (simple model): `award fees + points used × user's cents-per-point / 100`.
- Points earned on cash (simple model): `eligible spend × user-entered earn multiplier`.
- Student must state when earn multipliers, transfer ratios, eligibility, surcharges or availability are **not validated**.
- Distinguish cash savings from subjective valuation. There is no universal fixed "best" points value.

## Portability pass/fail checklist
1. Zip extraction does not require the student's original machine or private cloud account.
2. Judge runs app using written instructions and fresh credentials if live APIs are involved.
3. New query differs from prepared demo and is processed normally.
4. `SKILL.md` has the portable format and points to its references.
5. Tests and dependency manifest included; no secrets or hardcoded personal data.

## Scoring reminders
Accuracy is a gate: **misrepresenting fake data as live receives zero for Verified Cost and Accuracy**. Wording changes and API errors should not be hidden. Award partial credit for transparent engineering even when paid source access is restricted.
