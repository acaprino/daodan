"""senior-review ships its own isolated worker for jobs, lenses and the critic.

Pinned: the worker is a registered agent with five tools, so it starts without the
host's full tool set; it is support, never a reviewer the catalog offers; the roster
lets the coordinator dispatch it; only a lens it delivers counts, never one from the
host's generic worker.
"""

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "plugins/senior-review"
if str(REPO_ROOT / "daodan/core") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "daodan/core"))

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


def section(skill: str, start: str, end: str) -> str:
    """The text of a skill from the line opening with `start` to the next `end`."""
    text = (PLUGIN / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    return " ".join((start + text.split("\n" + start, 1)[1].split(end, 1)[0]).split())


class HostExecutionTest(unittest.TestCase):
    """AGENTS.md: the reviewed project's code runs only in Daodan's container. Where a review or an
    investigation may run it, the text asks for the container and makes its absence a gap with the cause."""

    def test_no_review_or_investigation_step_runs_project_code_on_the_host(self):
        for skill, start, end in (("review-quality-gates", "4. The reviewed project's code", "\n## "),
                                  ("investigation-method", "## 4. Reproduction", "\n## "),
                                  ("investigation-method", "## 5. Bisection", "\n## ")):
            with self.subTest(skill=skill, start=start):
                text = section(skill, start, end)
                self.assertIn("Daodan's container", text)
                self.assertIn("never on the host", text)
                self.assertIn("gap with its cause", text)


class IsolatedWorkerTest(unittest.TestCase):
    def test_registered_agents_exist(self):
        manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["agents"], ["./roles/isolated-worker.md"])  # the reviewers are the application's
        self.assertTrue((PLUGIN / "roles/isolated-worker.md").is_file())

    def test_worker_has_five_tools(self):
        fields = frontmatter(PLUGIN / "roles/isolated-worker.md")
        self.assertEqual(fields["name"], "isolated-worker")
        self.assertEqual(fields["model"], "inherit")
        self.assertEqual(fields["tools"], "Read, Write, Glob, Grep, Bash")

    def test_worker_is_not_a_reviewer(self):
        ids = {entry["id"] for entry in composition.load_catalog(composition.DEFAULT_ROOT)["entries"]}
        self.assertNotIn(WORKER, ids)

    def test_roster_allows_dispatch(self):
        self.assertIn(WORKER, review_roster.SUPPORT)
        roster = {"schema": review_roster.SCHEMA, "roster": [], "support": list(review_roster.SUPPORT), "jobs": []}
        self.assertEqual(review_roster.check(roster, {"roles": [WORKER]}), [])

    def test_only_the_plugin_worker_counts_for_a_lens(self):
        review = {"id": "r1", "support": list(review_roster.SUPPORT), "grounding": {"candidate": "c1"}}
        for role, counted in ((WORKER, True), ("general-purpose", False)):
            delivery = {"review": "r1", "role": role, "status": "delivered", "coverage": "complete",
                        "gaps": [], "candidate": "c1",
                        "check": {"kind": "verification", "lens": 1, "targets": ["F1"],
                                  "input_mode": "verification", "independent": True,
                                  "evidence": ["a.py:3"], "verdict": "REAL"}}
            check = review_experience.lens_check(review, {"d1": delivery}, "F1", 1)
            self.assertEqual(check is not None, counted, role)


if __name__ == "__main__":
    unittest.main()
