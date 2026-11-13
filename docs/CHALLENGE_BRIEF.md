# Student Challenge: Build the Ultimate AI Travel & Rewards Agent

**Name:** FareForge AI — Hackathon Challenge #3  
**Format:** Teams of ~3–4 students, any approved AI coding assistant and development stack  
**Event:** 9:00 AM kickoff, lunch and tour at noon, demos starting 3:00 PM  
**Deliverable:** Working portable application, Agent Skill, source, test evidence, and documentation

## The problem
A traveler checks Google Flights, Skyscanner, carrier websites, hotels, loyalty programs, and multiple credit card portals. Prices are not always comparable: a cheaper base airfare may have higher bag fees, and a lower hotel nightly rate may have resort fees. Points are also not free; they have an opportunity cost.

**Mission:** Build an agent that can ask for a destination and dates, compare flight + hotel choices, and recommend the best **verifiable** cash-versus-points strategy.

## Input screen
- Departure airport/city; destination(s) or optional "Anywhere"
- Dates, flexible dates if possible, party size
- Cabin, stops, bag count; hotel occupancy and location constraints
- Budget and preferences
- User-selected credit cards, points balances, loyalty memberships and custom points valuations

## Required MVP (achievable on event day)
1. **Working website:** editable travel form; functional search; flight + hotel results and filters or sorting.
2. **Price normalization:** account for traveler count, required bags, mandatory hotel taxes/fees when known, and clearly mark unknown amounts.
3. **Rewards math:** configurable card earn-rate assumption, estimated points earned, and one cash-versus-award economic comparison. NEVER claim verified transfer/award rules from generic assumptions.
4. **Agent-style decision:** recommended option with reasoning, tradeoffs, data provenance, and uncertainty notes; handle changed inputs.
5. **Testing and honesty:** demo fixtures must be labeled fictional; capture evidence of any live price displayed.
6. **Portability:** another laptop can install/run the app from your ZIP/repo, and read the exported `SKILL.md`.

## Live-pricing target (for top price-accuracy scores)
- At least one **authorized** real flight provider AND one real hotel provider; show search timestamps and actual source.
- Where access allows, compare at least two sources for **equivalent itinerary/room**, including direct airline/hotel options.
- Compare the source quoted offer with the final booking step; don't treat an API search listing as a checkout-confirmed fare.
- Real award space only if observed/verified. Otherwise label points redemption **scenario only**.

No team is required to purchase tickets or use personal payment data. If provider access is blocked, demonstrate a safe adapter with transparent test data and explain limitation. Teams cannot claim those fixtures as winning live price evidence.

## Extra credit opportunities (within rubric, not beyond 100)
- Flexible dates or nearby airports; round-trip vs separate one-ways clearly distinguished
- Direct airline vs OTA vs Skyscanner/Google Flights search comparison
- Hotel direct member price vs third-party total (same room, same policy)
- Live points search plus card transfer eligibility rules; honest point valuation
- Deep links, email-ready itinerary, price-change alerts with opt-in
- Helpful conversational refinement and repeatable verification
- Great mobile interface, accessibility, error recovery

## Disallowed shortcuts
- Inventing live prices, fictitious booking availability or fabricated URLs
- Hardcoding answer for the hidden judge scenario
- Exposing API keys in frontend code or shared ZIP
- Scraping against provider terms or bypassing access controls
- Booking, applying for cards or transferring points without explicit permission
- Treating same hotel with different cancellation rules as identical

## Final show-and-tell (suggested 4–5 minutes)
1. 30 sec: problem, architecture, and sources.
2. 90 sec: live search or clearly labeled demo fallback.
3. 60 sec: fees and card/points recommendation.
4. 60 sec: judge changes dates/card/travelers, then retest.
5. 30 sec: portable install explanation and exact limitations.

The goal is **credible decision support**, not a flashy screenshot.
