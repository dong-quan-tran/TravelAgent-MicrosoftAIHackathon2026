# Instructor / Organizer Guide (not a secret)

## Event configuration
**Hackathon challenge:** #3, AI Travel + Credit Card Rewards Agent.  
**Start:** 9:00 AM; **Lunch + tour:** noon; **Presentations:** 3:00 PM.  
**Teams:** Suggested 3–4 students.  
**What organizers provide:** This ZIP, Python 3.10+ computers, internet for live providers, a projection screen, test scenarios, and authorized API credentials if live searches are required.

## Set expectations
This is a **student MVP**, not a 6-hour Expedia replacement. With this scaffold, expected outcomes are an interactive local UI, sensible normalization and rewards calculations, transparent sources, and a portable submission. A higher-scoring team will demonstrate verified real prices and unannounced test scenarios.

## Live data access fairness
Check provider plans, quotas and terms **before** the hackathon. Google Flights and Skyscanner are primarily consumer search products, not universally available free developer feeds. The starter's SerpApi integration may have fees and limitations. Do not make paid integration access an unfair secret advantage; supply equivalent resources to teams where possible.

## Distinguish categories
- **Demo:** synthetic price, made-up airline/hotel, no booking link, used for functional engineering testing.
- **Live listing:** observed from a third-party search/API, potentially stale or missing checkout fees.
- **Checkout verified:** checked for the exact traveler/date/room/fare, fees and availability at a documented timestamp.

Only the last category (or the best confirmation realistically obtainable without purchase, with clear evidence) should be eligible for the strongest price-accuracy scores.

## Judge kit
Use `evaluation/judge_scorecard.csv`, `evaluation/price_verification_template.csv`, and `evaluation/test_scenarios.json`. The latter contains **fixture scenarios and a surprise-scenario template**, not fixed winning answers. Never rank teams purely on fictional test data.

## Portable-team check
Have a judge run `python scripts/portability_check.py` from extracted submission and open the app locally. Then verify the standalone skill description and ask another agent to interpret one travel offer. A skill alone is insufficient if the app cannot run.
