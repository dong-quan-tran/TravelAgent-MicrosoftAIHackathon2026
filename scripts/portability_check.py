#!/usr/bin/env python3
"""Check source bundle and tests using only Python standard library."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    "00_START_HERE.md", "README.md", "docs/CHALLENGE_BRIEF.md", "docs/JUDGING_RUBRIC.md",
    "docs/PORTABILITY.md", "starter_app/server.py", "starter_app/.env.example",
    "starter_app/travel/engine.py", "starter_app/travel/providers.py",
    "starter_app/data/sample_offers.json", "starter_app/web/index.html", "starter_app/web/app.js",
    "skills/travel-deal-auditor/SKILL.md", "evaluation/test_scenarios.json",
    "submission_templates/TEAM_SUBMISSION.md"
]
missing = [name for name in required if not (root / name).is_file()]
if missing:
    print("FAIL: missing package files:", *missing, sep="\n- ")
    sys.exit(1)
secret_files = [f for f in root.rglob(".env") if f.is_file()]
if secret_files:
    print("FAIL: .env files should NEVER be exported.")
    sys.exit(1)
skill = (root / "skills/travel-deal-auditor/SKILL.md").read_text(encoding="utf-8")
if not (skill.startswith("---\n") and "name: travel-deal-auditor" in skill and "description:" in skill):
    print("FAIL: skill YAML metadata missing")
    sys.exit(1)
print("PASS: required files exist, no .env, skill metadata present.")
cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
print("Running tests:", " ".join(cmd), flush=True)
result = subprocess.run(cmd, cwd=root / "starter_app", check=False)
sys.exit(result.returncode)
