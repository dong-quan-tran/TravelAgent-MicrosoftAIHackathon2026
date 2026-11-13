# Nguyen — Frontend and live search

## Goal

In four hours, make the existing travel app easy to use and connect live flight and hotel listings if access is ready. Keep a working offline demo throughout. Azure Maps is outside this build's scope; focus on prices and travel comparisons.

The repo currently contains only a README and these guides. Johnny will copy the working Python starter into the repo first. Do not build a second app while waiting.

## Ownership

- You own `starter_app/web/index.html`, `app.js`, and `styles.css`.
- You own `starter_app/travel/providers.py`, provider tests, and API setup instructions.
- Johnny owns the server, pricing engine, backend tests, and final integration.
- Agree before changing JSON fields. Tell Johnny before editing a file he owns.

## First 30 minutes — confirm access and start the app

1. Clone the repo, or pull after Johnny pushes the starter:

   ```powershell
   git clone https://github.com/nguyenleuta/travelagentmicrosoftaihackathon.git
   cd travelagentmicrosoftaihackathon
   git pull origin main
   git switch -c nguyen/frontend-live
   cd starter_app
   $env:PORT = "8080"
   python server.py
   ```

2. Open `http://127.0.0.1:8080` and run New York, Tokyo, and Las Vegas samples.
3. Check whether you already have authorized access to the starter's SerpApi adapter. It supports flight and hotel search listings. Confirm current docs, limits, and cost before making requests:
   - https://serpapi.com/google-flights-api
   - https://serpapi.com/google-hotels-api
4. If access is ready, copy `.env.example` to `.env` and set your key locally. Never commit or send the key. Keep it out of JavaScript, screenshots, logs, and prompts.
5. Test one live request. Confirm the returned data contains actual priced listings, not generated text or map locations.
6. Tell Johnny whether live search works and which fields are missing.

**Hard stop at 30 minutes:** if access is not ready, move to UI work. Keep the existing adapter and explain that live search is unavailable. Do not spend the build signing up for several providers.

## Shared API contract

Use the existing `POST /api/search`. Send the current form fields: origin, destination, dates, traveler count, boolean bag choices, mode, card label, earn multiplier, point valuation, and points balance.

Keep response sections `query`, `flights`, `hotels`, `summary`, and `warnings`. Johnny will add:

| Field | How to display it |
|---|---|
| Offer `price_complete` | Whether the modeled cost includes every required price component |
| Offer `unknown_fee_categories` | A visible list of missing charges or unconfirmed inclusions |
| Summary `price_complete` | Whether both selected components have complete price information |
| Summary `known_trip_cash_usd` | Known combined estimate when both travel parts exist |
| Summary `modeled_trip_cash_usd` | Complete modeled total; null if required prices or a trip component are missing |

Keep offer `total_cash_usd` for the known modeled amount. Do not label it all-in when `price_complete` is false. Preserve source, data status, observed time, and checkout status. During integration, treat an absent `price_complete` conservatively when `fees_incomplete` is true.

Price completeness and real availability are different. A fictional demo total can be fully modeled but cannot be booked.

## Minutes 30–90 — make results honest and clear

1. Keep the current page and improve it in place. No framework migration or redesign from scratch.
2. Make the demo/live mode obvious beside the results, not only at the top of the page.
3. Show each flight's route, dates, party price, stops, baggage status, and source when those fields exist.
4. Show each hotel's full-stay estimate, dates, room details, occupancy limits, cancellation status, and source when supplied.
5. Show missing fees as “Unknown.” A missing fee is not “Included” or “Free.”
6. Show source observation time for live results when returned. Missing time stays unknown.
7. Show a complete trip total only when supported. Otherwise show the known estimate with a clear missing-cost warning, or say a flight/hotel result is missing.
8. Keep all provider text safely escaped before inserting it into HTML. Only render links supplied by the provider, and allow only safe `https:` or `http:` URLs.

Done when a user can tell what the price covers and whether it is fictional, an unverified live listing, or checkout verified. This starter has no checkout verification flow, so do not add that badge to current offers.

## Minutes 90–135 — improve interaction

1. Add simple result sorting by known cash amount. If time allows, add flight stop filtering using existing fields.
2. Keep results and the selected recommendation consistent. If filters only affect the displayed list, state that clearly rather than implying the trip recommendation was recalculated.
3. Disable search while it runs and show a loading message.
4. Show clear input and provider errors. A failed request must not leave old results looking current.
5. Handle empty flight and hotel lists separately.
6. Check that labels, keyboard controls, and status messages work.
7. Check a narrow mobile layout; avoid wide cards or clipped prices.
8. Do not add a chat panel unless all required work is already complete.

## Minutes 135–165 — verify the provider path

If live access works:

1. Keep calls on the Python backend.
2. Check current provider documentation for whether prices are per traveler or for the full party. Tell Johnny the exact basis before changing normalization.
3. The starter searches two independent one-way flight legs. Keep that label visible; do not call it a verified round-trip fare.
4. The starter requests flights for one adult and scales the estimate. This does not verify party-wide seat availability. Clearly state that limitation unless you implement and test actual party pricing.
5. Preserve `fees_incomplete=true` wherever charges or inclusions are unknown.
6. Confirm hotel results use the requested dates and party size. Do not claim a specific room or cancellation policy when the API did not supply it.
7. Keep collection time in UTC and identify the real data source. Add source URLs only when supplied or built from a documented provider search URL; never invent booking links.
8. Add offline tests with saved synthetic response examples or mocked calls. Cover missing price fields, provider errors, and empty results. Do not make unit tests depend on a live key.
9. Save allowed evidence of the real request and result without secrets. A search listing is not checkout confirmation.

If live access fails, finish the UI and document the exact limitation. Never replace failed live results with fictional offers under a live label. If only one component is live, label flights and hotels separately; do not call the combined trip a live quote.

## Minutes 165–180 — hand off for integration

1. Commit and push your branch.
2. Send Johnny a short handoff: files changed, API fields used, live status, tests run, and remaining issues.
3. Help resolve conflicts one file at a time.
4. Test the merged version, not only your branch.

Example commands from the repo root:

```powershell
git add starter_app/web starter_app/travel/providers.py starter_app/tests/test_providers.py
git diff --cached
git commit -m "Improve travel results and live search handling"
git push -u origin nguyen/frontend-live
```

Stage only files you actually changed. Do not stage `.env`. Never force-push shared work.

## Last 60 minutes — test on your computer

After Johnny merges, pull `main` and run:

```powershell
python scripts/portability_check.py
cd starter_app
$env:PORT = "8080"
python server.py
```

Check these in the browser:

- All three sample trips work and stay labeled fictional.
- Changing travelers, bags, and points updates the results.
- Unknown fees remain visible.
- Sorting works and does not mislabel an offer as the recommendation.
- Empty results explain what is missing.
- Live mode without a key gives a clear error.
- Provider failure does not silently show demo prices.
- The page works on a phone-sized screen and with a keyboard.

Help Johnny update the README and submission template. Record only checks you completed. If doing a clean-copy demo, keep your local secret file outside the shared package and configure live access separately.

## Your demo role

Show the search form, results, source labels, fee warnings, and error handling. If live search works, show one real search and explain that prices still need checkout confirmation. If it does not, clearly say the sample is fictional and explain how the adapter would be configured.

## Cut first if time runs short

Skip maps, accounts, animations, chat, saved searches, alerts, new frameworks, and new providers. Keep a clear search form, readable results, honest price labels, and a reliable demo.
