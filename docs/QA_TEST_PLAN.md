# Student QA and Judge Acceptance Tests

## Automated
From `starter_app/` run:

```bash
python -m unittest discover -s tests -v
```

From project root run:

```bash
python scripts/portability_check.py
```

## Manual tests (record pass/fail)

API validation rejects non-finite or malformed numeric inputs, fractional traveler/points counts, and baggage flags other than JSON booleans. Omitted optional rewards fields retain documented defaults; invalid supplied values are never silently replaced.
1. Open the app, select **New York**. The UI displays fictional source warnings.
2. Toggle checked bag: a base fare without included bags increases; a fare with included checked bag does not.
3. Change travelers 1 → 2: flight party price changes; a single hotel room may stay the same (subject to occupancy).
4. Change credit card multiplier: estimated earned points change, while real cash outlay does not.
5. Change cents per point: award economic value changes, while miles required do not.
6. Enter too few points: the award cannot be labeled affordable.
7. Enter a date with no demo fixture: app explicitly says no matching results instead of inventing live inventory.
8. Select Live without credentials: human-readable error, no fallback to fictional data.
9. Run Tokyo and Vegas scenario buttons; no crash and correct stay length/party count.
10. Reinstall on a second machine and run the app without opening the AI assistant used to create it.
11. Ensure no real credentials present in any ZIP file, screenshot or prompt.
12. Validate real provider links and exact matching cancellation/room/flight conditions if using live data.

## Hidden judge test
- Give an unannounced destination/date/card profile.
- Observe actual provider requests (or an honest no-provider error) rather than predetermined results.
- Ask why the cheapest fare is better despite its stops/baggage/cancellation tradeoff.
- Ask judge to refresh booking source and check price and timing.
- Ask to switch AI assistant or computer using the exported skill and app.

## Known starter limitations (students should improve)
- Demo fixtures cover only three itineraries; different dates will return no fixtures.
- Flight/hotel pairing is naive cheapest + cheapest, no geographic/local transit constraints.
- Live flight fares represent an estimated pairing of two independent one-way legs.
- Live fee coverage is not complete and search results lack checkout verification.
- Rewards use an editable generic earn rate and point valuation; no real loyalty login or award API.
- No automated background monitoring, notifications or actual purchase/booking.
