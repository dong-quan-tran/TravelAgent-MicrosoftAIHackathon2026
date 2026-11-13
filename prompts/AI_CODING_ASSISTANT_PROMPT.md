# Paste this into ChatGPT, Claude, Codex, GitHub Copilot or another AI coding tool

You are my senior full-stack development partner for Hackathon #3, FareForge AI Travel Agent.

Our goal is a **portable, verifiable, student-built travel comparison agent**, NOT a static mockup. Work inside this repository and read `00_START_HERE.md`, `docs/CHALLENGE_BRIEF.md`, `docs/JUDGING_RUBRIC.md` and `skills/travel-deal-auditor/SKILL.md` first.

Project requirements:
1. Maintain working local website and API, and ensure another computer can run the project from the exported ZIP/repo.
2. Search and compare flights + hotels from authorized sources when credentials are available; do not claim unsupported APIs or invent provider data.
3. Make the source/availability state obvious (`synthetic_demo`, `live_search_unverified`, `checkout_verified`). **Never relabel fixtures as live**.
4. Model traveler count, selected baggage, hotel mandatory charges, cancellation and comparability. Represent unknown fees as unknown rather than assuming a real zero.
5. Build a configurable card rewards/points model. Distinguish cash paid, points used, hypothetical points earned and economic value. Validate real card rules or label them assumptions.
6. Provide useful agent-generated reasoning grounded in returned offers (or deterministic logic if no LLM integration). Never invent award seats, transfers or booking URLs.
7. Use backend-only secrets, an `.env.example`, no real credentials in repository, reproducible setup and unit tests.
8. Implement one small improvement at a time, run tests, and report what works plus what remains unverified.
9. Include a portable Agent Skill (`SKILL.md`) and updated documentation. Test cold-start on a fresh machine/environment.
10. Do not execute payments, bookings, point transfers or card applications.

**First task:** Inspect the current working starter and propose the highest-value next improvement for a 9:00 AM–3:00 PM hackathon with lunch/tour at noon and presentations at 3:00 PM. Make the improvement directly, update tests and docs, and tell me how to verify it. Do not spend the event implementing every feature.
