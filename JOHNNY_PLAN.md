# Johnny — Backend and team integration

## Goal

In four hours, deliver a working travel comparison app that Nguyen can run on his computer. Users enter a trip, compare flight and hotel costs, and see a clear cash-versus-points explanation. Demo prices must stay labeled fictional. Live listings must stay labeled unverified.

The GitHub repo currently has only a README. The working starter is in the local `Hackathon_03_AI_Travel_Agent_Student_Kit` folder. Start by putting that source into this repo so you both use the same code.

## Ownership

- You own `starter_app/server.py`, `starter_app/travel/engine.py`, backend tests, and backend documentation.
- Nguyen owns `starter_app/web/`, `starter_app/travel/providers.py`, provider tests, and live API setup.
- You handle merging, final tests, and the submission checklist.
- Agree together before changing JSON field names. Avoid editing each other's files without a message first.

## First 20 minutes — share the working starter

1. Copy the contents of `Hackathon_03_AI_Travel_Agent_Student_Kit` into the repo root. Keep `starter_app/`, `docs/`, `scripts/`, `skills/`, and the other kit folders together. Preserve both task guides.
2. Do not copy `.env`, API keys, virtual environments, or `__pycache__` folders. Add root ignore rules for `.env`, `__pycache__/`, `*.pyc`, and `.venv/` before staging.
3. Keep the starter's no-dependency Python setup. No framework migration.
4. Run the baseline checks:

   ```powershell
   cd starter_app
   python -m unittest discover -s tests -v
   $env:PORT = "8080"
   python server.py
   ```

5. Open `http://127.0.0.1:8080`. Check that the New York sample works. Stop the server with Ctrl+C when needed.
6. Commit and push the starter to `main`. Tell Nguyen to pull it before he starts editing.
7. Create your branch:

   ```powershell
   git switch -c johnny/backend
   ```

The local starter already has stricter input validation and 20 passing tests. Preserve those changes when copying it.

## Shared API contract — agree before coding

Keep the existing `POST /api/search` request and response shape. Discuss any added fields with Nguyen before either side uses them.

Request fields:

| Field | Meaning |
|---|---|
| `origin`, `destination` | Airport codes or supported city names |
| `depart_date`, `return_date` | Dates in `YYYY-MM-DD` format |
| `travelers` | Whole number from 1 to 6 |
| `carry_on`, `checked_bag` | JSON booleans |
| `mode` | `demo` or `live` |
| `card_name` | User's label; no claim that card rules are verified |
| `card_multiplier` | Assumed points earned per dollar |
| `point_value_cents` | User's chosen point value |
| `award_points_balance` | Whole-number scenario balance |

Keep `query`, `flights`, `hotels`, `summary`, and `warnings` in the response. Keep `total_cash_usd` as the known modeled amount so the current UI continues to work. Add the following fields rather than silently changing its meaning:

- Offer `price_complete`: whether all required price components are known. This does not mean checkout verified.
- Offer `unknown_fee_categories`: names of missing charges or unconfirmed inclusions.
- Summary `price_complete`: true only when both selected components have complete price information.
- Summary `known_trip_cash_usd`: combined known amount when both flights and hotels exist; otherwise null.
- Summary `modeled_trip_cash_usd`: complete modeled total only when both parts exist and price information is complete; otherwise null.

Synthetic fixtures can have complete modeled prices but remain fictional. Live offers with `fees_incomplete=true` cannot have a complete all-in total. Preserve `data_status`, `checkout_verified`, and any `observed_utc` values.

## Minutes 20–90 — fix cost handling

1. Trace `validate → demo_offers/live_offers → compare → response`.
2. Keep the current validation checks. Invalid traveler counts, rewards values, dates, or baggage flags must return a clear 400 error.
3. Add the agreed price-completeness fields. Unknown bag fees and hotel fees must not appear as confirmed zero-dollar charges.
4. Keep known prices available for comparison, but say “lowest known estimate” when required fees are missing. Do not describe it as the cheapest bookable trip.
5. Missing flights or hotels must leave the complete trip total null. Never display a partial result as a complete trip.
6. Add focused tests for incomplete live fees, missing flight/hotel results, party-size multiplication, and unchanged demo totals.

Done when the API distinguishes a complete fictional model from an incomplete live estimate without breaking existing clients.

## Minutes 90–150 — improve points reasoning

1. Keep cash paid separate from the value of earned points. Earned points are not a checkout discount.
2. Calculate award economic cost as `cash fees + points used × cents per point / 100`.
3. Compare an award with the cheapest acceptable cash alternative in the same category. Comparing only against that offer's own expensive cash price can exaggerate savings.
4. Include the other trip component when explaining the resulting trip cost.
5. Respect the scenario points balance. Do not recommend two awards that jointly spend more than that balance.
6. Keep flight and hotel program balances separate in the explanation. A generic balance does not prove points can transfer between programs. For this deadline, recommend at most one illustrative redemption at a time.
7. Do not infer award availability, transfer eligibility, or issuer rules. Label every unverified award as a scenario.
8. Add tests where an apparently attractive award loses to a cheaper cash option, and where the points balance is too small.

Done when each recommendation includes the cash alternative, points used, cash fees, economic cost, and assumptions.

## Minutes 150–180 — integrate Nguyen's changes

1. Commit your work. Ask Nguyen to finish and push a small, working commit.
2. Merge one branch at a time. Review conflicts together, especially the response contract.
3. Run the tests and all three sample trips after merging.
4. Check the live flow only if authorized access is ready. Do not spend the remaining hour replacing providers.
5. Verify the app shows API failures clearly and never silently switches to fictional offers.

## Last 60 minutes — freeze, test, submit

Stop adding features. Run from the repo root:

```powershell
python scripts/portability_check.py
```

Check these together in the browser:

- New York, Tokyo, and Las Vegas samples work.
- Changing travelers and bags changes the right costs.
- Changing point value changes the award reasoning, not the cash price.
- Missing fixture dates return no matches.
- Live mode without a key shows a clear error.
- Missing live fees show unknown, not free.
- A provider failure does not produce demo prices under a live label.
- Nguyen can run the app from a clean copy using the README.

Update the README with port 8080 instructions, test commands, API setup, and known limitations. Fill `submission_templates/TEAM_SUBMISSION.md` with actual results. Do not claim a second-computer test or live verification unless completed.

## Git workflow

Use small commits with clear messages. Stage only the files you intend to share. Before each push, run `git diff --cached` and check for secrets.

```powershell
git add starter_app/travel/engine.py starter_app/tests/test_engine.py
git commit -m "Handle incomplete travel prices and improve award comparisons"
git push -u origin johnny/backend
```

Merge finished work into `main`, then have both people pull and test that exact version. Never force-push shared work.

## Your demo script

1. Enter a sample trip and explain the data label.
2. Show the flight plus hotel total.
3. Change bags or traveler count and explain the cost change.
4. Change point value and show the cash-versus-award tradeoff.
5. Explain what is verified, what is assumed, and what still needs checkout confirmation.

## Cut first if time runs short

Skip a chatbot, accounts, saved trips, maps, flexible dates, alerts, payments, and new card recommendations. Finish correct costs, honest labels, clear explanations, tests, and portability.
