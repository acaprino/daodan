"""The fixture splits into at least three groups for one security reviewer, without a model run.

Snapshot of app/, snapshot.py files, then composition.py bind with the README budget:
every file gets one cell, each group stays within the budget or holds one file, and
files linked by an import fall into different groups.
"""
import json
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
APP = HERE / "app"
for scripts in ("plugins/codebase-map/skills/map/scripts", "plugins/senior-review/skills/review-preparation/scripts"):
    sys.path.insert(0, str(REPO / scripts))
import composition  # noqa: E402
import snapshot  # noqa: E402

SECURITY = "senior-review:security-auditor"
CANDIDATE = {"ref": "fixture"}
LINKS = [("server/handlers.py", "server/storage.py"), ("server/handlers.py", "server/auth.py")]


def readme_budget() -> int:
    return int(re.search(r"\| `budget` \| (\d+) byte", (HERE / "README.md").read_text(encoding="utf-8")).group(1))


class FixtureTest(unittest.TestCase):
    def test_security_reviewer_gets_three_groups_across_a_link(self):
        budget = readme_budget()
        with tempfile.TemporaryDirectory(prefix="whole-source-") as tmp:
            root = Path(tmp) / "app"
            shutil.copytree(APP, root, ignore=shutil.ignore_patterns("__pycache__"))
            manifest = Path(tmp) / "manifest.sqlite"
            snapshot.write_snapshot(root, manifest)
            files = Path(tmp) / "FILES.json"
            with redirect_stdout(StringIO()):
                self.assertEqual(snapshot.main(["files", str(manifest), "--out", str(files)]), 0)
            paths = [row["path"] for row in json.loads(files.read_text(encoding="utf-8"))["files"]]
            roster = {"schema": composition.ROSTER_SCHEMA, "shape": "branch", "review_basis": "content",
                      "roster": [SECURITY], "support": [], "required_specialists": [], "jobs": [], "gaps": [],
                      "grounding": {"scope_id": "candidate", "candidate": CANDIDATE, "conclusion_paths": paths}}
            bindings = {"candidate": CANDIDATE, "knowledge_selection": "", "output_dir": ".team-review/jobs",
                        "selection": "automatic", "coverage": {"files": str(files), "root": str(root), "budget": budget}}
            prepared = composition.bind(roster, bindings, REPO / "plugins/senior-review")

        groups = [job["paths"] for job in prepared["jobs"]]
        self.assertGreaterEqual(len(groups), 3)
        self.assertEqual(sorted(path for group in groups for path in group), sorted(paths))
        for job in prepared["jobs"]:
            self.assertTrue(job["bytes"] <= budget or len(job["paths"]) == 1, job["paths"])
        group_of = {path: index for index, group in enumerate(groups) for path in group}
        for importer, imported in LINKS:
            self.assertIn(f"from .{Path(imported).stem} import", (APP / importer).read_text(encoding="utf-8"))
            self.assertNotEqual(group_of[importer], group_of[imported], (importer, imported))


if __name__ == "__main__":
    unittest.main()
