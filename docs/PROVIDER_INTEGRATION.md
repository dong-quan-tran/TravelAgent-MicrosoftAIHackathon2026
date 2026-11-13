# Connecting Real Flight and Hotel Data

## What the starter provides
`starter_app/travel/providers.py` is an **optional** SerpApi-based search adapter. The student's own authorized API key goes in local `starter_app/.env`:

```
SERPAPI_KEY=YOUR_PRIVATE_API_KEY_HERE
```

Then run `python server.py` and select **Live** in the browser. The backend makes **three** API calls: outbound one-way flight search, inbound one-way flight search, and hotel listings. It takes the first few results, builds an estimate, and flags uncertainty.

**Important:** Combining two one-way search prices is **not** the same as verifying an actual round-trip fare. This adapter does not retrieve carrier-specific checkout offers, bag fees, real hotel mandatory-fee details, or reward award inventory. The returned combination is a teaching scaffold, **not a production-quality bargain finder**.

## Service references (verify terms and current docs yourself)
- [SerpApi Google Flights API](https://serpapi.com/google-flights-api): engine `google_flights`, parameters include `departure_id`, `arrival_id`, `outbound_date`, `return_date`, `type`, `adults`.
- [SerpApi Google Hotels API](https://serpapi.com/google-hotels-api): engine `google_hotels`, fields include `q`, `check_in_date`, `check_out_date`, `adults`, `properties` and `total_rate`.
- [Agent Skills open specification](https://agentskills.io/specification).

SerpApi is a third-party service, not Google's official public flight-booking API. Availability, usage plans, quota and costs can change. Ask organizers for pre-provisioned authorized credentials if real searches are a requirement.

## Build a stronger integration
1. Create a separate provider adapter for each permitted data source. Follow API terms.
2. Map results to a consistent data schema. Record currency, collection time UTC, all-in vs partial price, and precise inventory identity.
3. Confirm whether `price` is **per person** or for the whole party. Never multiply a party-total by travelers.
4. For round trips, use an actual round-trip offer/selected-leg pricing flow if your provider supports it; otherwise explicitly show separate-ticket status and risks.
5. Do not assume bags are free if fee fields are missing. Represent `unknown`, request user input, or exclude from verified comparison.
6. Hotels: confirm same room type, check-in/out, taxes, mandatory resort fees, occupancy and cancellation terms.
7. Verify the actual booking link and same-session checkout price before claiming savings.
8. Keep evidence: provider, search URL or booking URL, observed price, UTC timestamp, screenshots if allowed.

## Credit card logic
The default UI lets users manually enter points per dollar and their own cents-per-point valuation. It does **not** know live terms for Chase, Amex, Bilt, Citi, Capital One, or hotel/airline partners. For issuer-specific recommendations, students need sourced, date-stamped product terms and a separately validated rewards-eligibility engine. Do not recommend churning or a new card as if approval or bonus eligibility were guaranteed.

## Debugging
- `Live mode requires SERPAPI_KEY`: create your untracked `.env`, enter authorized key.
- `Provider HTTP error`: check quota, plan, and current docs.
- Empty flight or hotel list: search did not return parsable priced offers; don't silently replace with demo offers.
- Live price does not match a browser: search result / currency / timing / missing-fee differences are common. Display uncertainty and verify checkout.

## Privacy and security
Never paste real credit card numbers, passwords, airline login cookies or API keys into a prompt or commit. Don't scrape authenticated pages without authorization. The demo card wallet contains illustrative rate inputs, **not financial credentials**.
