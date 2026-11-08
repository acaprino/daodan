"""senior-review ships its own isolated worker for jobs, lenses and the critic.

Pinned: the worker is a registered agent with five tools, so it starts without the
host's full tool set; it is support, never a reviewer the catalog offers; the roster
lets the coordinator dispatch it; a lens it delivers counts like one from the host's
generic worker.
"""

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "plugins/senior-review"
for scripts in ("skills/review-preparation/scripts", "skills/review-consolidation/scripts"):
    if str(PLUGIN / scripts) not in sys.path:
        sys.path.insert(0, str(PLUGIN / scripts))

import composition  # noqa: E402
import review_experience  # noqa: E402
import review_roster  # noqa: E402

WORKER = "senior-review:isolated-worker"


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    head = text.split("---", 2)[1]
    fields = {}
    for line in head.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


class IsolatedWorkerTest(unittest.TestCase):
    def test_registered_agents_exist(self):
        manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertIn("./roles/isolated-worker.md", manifest["agents"])
        for agent in manifest["agents"]:
            self.assertTrue((PLUGIN / agent).is_file(), agent)

    def test_worker_has_five_tools(self):
        fields = frontmatter(PLUGIN / "roles/isolated-worker.md")
        self.assertEqual(fields["name"], "isolated-worker")
        self.assertEqual(fields["model"], "inherit")
        self.assertEqual(fields["tools"], "Read, Write, Glob, Grep, Bash")

    def test_worker_is_not_a_reviewer(self):
        ids = {entry["id"] for entry in composition.load_catalog(PLUGIN)["entries"]}
        self.assertNotIn(WORKER, ids)

    def test_roster_allows_dispatch(self):
        self.assertIn(WORKER, review_roster.SUPPORT)
        roster = {"schema": review_roster.SCHEMA, "roster": [], "support": list(review_roster.SUPPORT), "jobs": []}
        self.assertEqual(review_roster.check(roster, {"roles": [WORKER]}), [])

    def test_lens_from_either_worker_counts(self):
        review = {"id": "r1", "support": list(review_roster.SUPPORT), "grounding": {"candidate": "c1"}}
        for role in (WORKER, "general-purpose"):
            delivery = {"review": "r1", "role": role, "status": "delivered", "coverage": "complete",
                        "gaps": [], "candidate": "c1",
                        "check": {"kind": "verification", "lens": 1, "targets": ["F1"],
                                  "input_mode": "verification", "independent": True,
                                  "evidence": ["a.py:3"], "verdict": "REAL"}}
            check = review_experience.lens_check(review, {"d1": delivery}, "F1", 1)
            self.assertIsNotNone(check, role)


if __name__ == "__main__":
    unittest.main()
