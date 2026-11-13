# Travel evidence + apples-to-apples comparison

## Evidence levels
- `synthetic_demo`: artificial fixture; no real supplier or booking link. Cannot be ranked as a live deal.
- `live_search_unverified`: a real provider returned the price, but taxes, extra fees, class, availability or final checkout may not be confirmed.
- `checkout_verified`: an equivalent offer was observed through the provider's final pre-payment checkout step, all known mandatory charges included, with a UTC capture time. Still not guaranteed after capture.

## Flight identity
Match origin and arrival airport, dates, journey legs, departure and arrival times, fare class, bags, cabin, passengers, cancellation/change options, and travel-day boundaries. Separate one-way tickets are **not identical** to a single protected round-trip itinerary. Don't join outbound and inbound quotes without labeling the risks.

## Hotel identity
Match hotel property, date, number of rooms, occupancy, room type, board type, cancellation terms, taxes, mandatory fees, currency and status of loyalty member pricing. Cheap "room from" pricing is not a confirmed stay cost.

## Provider observation record
For every claim of savings, show provider, UTC time, quote URL/ID, exact product identity, currency, raw price, normalization, fee assumptions and screenshot if permitted. Retain raw response when terms allow.

## Card + points
Separate verified benefits from user-entered assumptions. Verify issuer, card edition, current earning terms, purchase channel, bonus caps, award availability, transfer ratios and tax/fee treatment. Points valuations are subjective and should be adjustable.

## Reliability
If the endpoint fails, show an error and leave the source unchecked. Do not silently replace it with the synthetic fixtures or stale caches. Mark which providers were actually checked, not merely intended.
