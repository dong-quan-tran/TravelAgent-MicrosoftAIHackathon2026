# HACKATHON #3 — FareForge AI Travel Agent

## Your mission
Build an AI travel agent that helps travelers choose **the least expensive bookable flight + hotel combination**, then explains whether to pay cash or use points. Your judge must be able to run it on **a different computer**.

**Key rule: fictional prices are never real offers.** The included starter demonstrates the UI and calculations with clearly labeled synthetic fixtures; your team must add and verify real sources to earn live-pricing credit.

## Start in 5 minutes
1. Extract the entire ZIP to a folder (do not run individual files inside the ZIP).
2. Open a terminal inside `starter_app/`.
3. Run `python server.py` (Windows: `py server.py`; macOS/Linux: `python3 server.py`).
4. Open **http://127.0.0.1:8000** in a browser.
5. Try **New York**, **Tokyo**, and **Las Vegas**. Adjust baggage, traveler count and rewards inputs.
6. Run the portable automated tests: `python -m unittest discover -s tests -v`.

Python 3.10+ required. **No pip installs, cloud account, paid license, or credentials are needed for demo mode.**

## What to read (in this order)
1. [`docs/CHALLENGE_BRIEF.md`](docs/CHALLENGE_BRIEF.md) — requirements and deliverables.
2. [`docs/JUDGING_RUBRIC.md`](docs/JUDGING_RUBRIC.md) — 100-point evaluation rules.
3. [`docs/SCHEDULE_AND_ROLES.md`](docs/SCHEDULE_AND_ROLES.md) — 9 AM–3 PM build plan.
4. [`docs/PROVIDER_INTEGRATION.md`](docs/PROVIDER_INTEGRATION.md) — live flight/hotel integration.
5. [`docs/PORTABILITY.md`](docs/PORTABILITY.md) — transfer skills + app to another computer.
6. [`submission_templates/TEAM_SUBMISSION.md`](submission_templates/TEAM_SUBMISSION.md) — final submission checklist.

## What is already included
- A functional local website, searchable fictional test fares, hotel comparison and editable rewards model.
- Python pricing/recommendation engine, optional **SerpApi** adapter for unverified live flight/hotel search listings, and unit tests.
- A transferable `SKILL.md` Agent Skill, reference docs, reusable AI development prompt, test scenarios, and scorecards.

## What is deliberately NOT implemented yet
- A verified, direct airline booking engine or guaranteed lowest checkout price.
- Every airline/OTA and hotel booking site; comprehensive nearby airport searches.
- Verified award availability or card-to-loyalty transfer partnerships.
- Live current credit card product rules, fee schedules, card application decisions or payments.

Teams should add honest verification rather than hiding these gaps. **False claims of live pricing are penalized.**
