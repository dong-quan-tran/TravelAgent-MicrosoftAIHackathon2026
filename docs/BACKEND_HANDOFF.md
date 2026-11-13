# Backend handoff for Nguyen

Implemented in Johnny's backend branch. Existing request fields and response sections stay in place.

## Price fields

- Each offer now has `price_complete` and `unknown_fee_categories`.
- `fees_incomplete` is set when required amounts are missing or the provider flags incomplete coverage.
- `total_cash_usd` remains the known modeled amount. It is not a confirmed all-in amount when `price_complete` is false.
- Summary `known_trip_cash_usd` contains the known flight + hotel estimate, or null if either component is missing.
- Summary `modeled_trip_cash_usd` is null when either selected component has unknown fees or is missing.
- Summary `price_complete` describes modeled price coverage, never booking availability.

Frontend now distinguishes unknown fees from missing results. When the known total exists but the complete total is null, it shows the known estimate and lists unknown fees. Cards show dates and bag inclusion status. A cash-versus-points panel displays the single-award trip comparison. Search clears old results and ignores stale responses.

## Awards

`best_illustrative_award` is null unless one affordable, fully modeled award beats the lowest known cash combination with complete fees. Savings compare against the cheapest cash option in that category, rather than the award offer's own cash price.

The candidate retains existing fields and adds `cash_alternative_offer_id`, `cash_alternative_usd`, `award_economic_cost_usd`, `trip_cash_outlay_usd`, `trip_economic_cost_usd`, and `scenario_only`.

Only one redemption is recommended. The other component is paid in cash. No combined program balance or transfer eligibility is assumed. Missing award taxes exclude a candidate. Earned points remain separate and are excluded from the award savings comparison.

Fare/room conditions can differ between alternatives; the explanation flags that limitation. These are scenario comparisons, not verified equivalent booking quotes.

## Provider expectations

Keep `fees_incomplete=true` when the provider has unknown fees, even if legacy numeric fields contain zero. Prefer null for genuinely missing prices. Keep real zero only for a confirmed zero charge. Set bag inclusion flags to true only when confirmed.

Johnny has also updated `starter_app/web/app.js` and `styles.css` while Nguyen handles the API. Provider files are unchanged. Pull these frontend changes before editing those files.

## Verification

Run `python scripts/portability_check.py` from the repo root. Regression cases cover missing fees, selected baggage, missing trip components, award baseline errors, missing award taxes, and insufficient points.
