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

### Flight and hotel shortlist + points sort (live mode)
- **Shortlist (never empty):** up to 10 flights and 10 hotels. Offers that Chase or Amex points can pay for come first, ranked by how many of the two cards can (2 before 1), then by price. If fewer than 10 qualify, the list is filled with the cheapest other offers, tagged "No Chase/Amex points option". A search never ends with zero results because of this filter.
- **Hotels:** the chain comes from brand words in the hotel name (Courtyard → Marriott, Hampton Inn → Hilton…). Marriott: both cards; Hyatt, IHG, Wyndham: Chase; Hilton, Choice: Amex. If page 1 has fewer than 10 qualifying hotels, one more SerpApi page is requested (one extra API credit).
- **Flights:** up to 6 outbound × 6 return one-way results are paired (no extra API calls). Each leg uses the first airline on it. A leg can be paid through the airline's own program **or an alliance partner** that can book it, e.g. American → British Airways / Iberia / Qatar Avios (both cards), United → Aeroplan, KrisFlyer, ANA, LifeMiles, Delta → Flying Blue, Virgin Atlantic. A card must reach a program on both legs. Spirit, Frontier and similar airlines have no option.
- **Points estimate:** cash (pre-tax for hotels when SerpApi gives it) ÷ The Points Guy's November 2026 value for the program, converted with each card's transfer ratio and rounded up to the transfer increment. Each card uses whichever reachable program needs the fewest of its points. Partner award charts are **not** modeled, and because the method is cash ÷ value, programs valued higher (e.g. LifeMiles 1.65¢) look cheaper. Treat every figure as a rough estimate.
- **Sort by points:** fewest card points first, whichever card needs fewer; offers with no points figure go last. Demo mode sorts on the fictional award prices.
- Shared estimator: `travel/loyalty.py`; data: `data/hotel_points.json`, `data/airline_points.json` (sources and dates included). Chase → Hyatt is stored as 1:1 (Sapphire Reserve); it is 4:3 on Sapphire Preferred and Ink Business Preferred.

## Debugging
- `Live mode requires SERPAPI_KEY`: create your untracked `.env`, enter authorized key.
- `Provider HTTP error`: check quota, plan, and current docs.
- Empty flight or hotel list: search did not return parsable priced offers; don't silently replace with demo offers.
- Live price does not match a browser: search result / currency / timing / missing-fee differences are common. Display uncertainty and verify checkout.

## Privacy and security
Never paste real credit card numbers, passwords, airline login cookies or API keys into a prompt or commit. Don't scrape authenticated pages without authorization. The demo card wallet contains illustrative rate inputs, **not financial credentials**.
