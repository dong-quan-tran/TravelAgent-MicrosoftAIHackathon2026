# Portable to Another Computer and Another AI Agent

## Transfer 1 — working application
Your source tree, deterministic sample data, dependency manifest, tests, and environment template must travel together. The default starter runs on Python 3.10+ with no third-party packages. Export via ZIP or Git. **Do not include `.env` or credentials.**

### Cold-install test
1. Copy your submission ZIP to a *different* laptop or a fresh local directory.
2. Extract it. Do not use packages, database volumes, or environment files from the old machine.
3. Read `README.md` and run the listed installation steps.
4. Run the supplied tests.
5. Launch the app and search a fixture scenario.
6. Edit the dates/card inputs; verify the app reacts appropriately.
7. For live mode, configure **new** authorized credentials from the receiving machine and prove data comes from the provider.
8. Record any system prerequisite that prevents the test from passing.

## Transfer 2 — reusable AI instructions
`skills/travel-deal-auditor/SKILL.md` is a vendor-neutral Agent Skill with YAML `name` and `description`. It includes reference documents describing safe comparisons and the source schema. Follow https://agentskills.io/specification.

Other assistants may accept the folder as a skill, or may need the student to copy/paste skill content or adapt a manifest. **Not every ChatGPT/Claude/Gemini interface loads local SKILL.md automatically.** Skills transfer the workflow knowledge and, sometimes, bundled scripts; they do not automatically transfer cloud logins, live API access, an installed server or working integrations.

### Suggested multi-agent test
- Open another supported AI coding agent or computer.
- Supply the `skills/travel-deal-auditor/` folder (using that agent's supported skill import mechanism, or paste skill instructions).
- Ask: "Compare two offers, include mandatory fees, distinguish real vs fictional, explain points cost, and do not invent availability."
- Verify it follows source validation and the same economic math.

## Portability output checklist
- [ ] App source included, no external machine absolute paths
- [ ] Documented Python/runtime requirement and exact launch command
- [ ] Dependencies pinned or standard-library-only
- [ ] Sample fixtures and tests
- [ ] `.env.example`, but NOT `.env`
- [ ] `SKILL.md` + references
- [ ] No hardcoded passwords, tokens, account numbers or personal traveler data
- [ ] New laptop can run core demo entirely offline
- [ ] New laptop can connect live only after user supplies approved API credentials
- [ ] Student records a successful cold-install demonstration
