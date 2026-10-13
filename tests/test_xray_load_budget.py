"""What each X-ray reader loads, in words, never grows.

A reader's load is its own body plus every file of the X-ray method it names: the
router when it loads `codebase-xray:xray-method`, and each `references/<unit>.md`
or `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/...md` path it cites. The budgets are
the numbers measured when the method was split into units (marketplace 32.11.0).
They only go down: lower one when a change shrinks a load, never raise one to
make a change pass.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "plugins" / "codebase-xray"
METHOD = PLUGIN / "skills" / "xray-method"

BUDGETS = {
    "workflows/analyze.md": 12_100,
    "workflows/team-analyze.md": 13_900,
    "roles/partition-structure-worker.md": 5_700,
    "roles/partition-behavior-worker.md": 4_600,
    "roles/partition-quality-worker.md": 5_300,
    "roles/semantic-interconnect-mapper.md": 6_700,
    "consumer": 3_600,
}

PATH = re.compile(r"(?:\$\{CLAUDE_PLUGIN_ROOT\}/skills/xray-method/|`)(references/[A-Za-z0-9_-]+\.md|SKILL\.md)")


def _words(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


def load(body: str) -> tuple[int, set[str]]:
    """Words a reader of `body` loads from the method, and which files."""
    files = set(PATH.findall(body))
    if "codebase-xray:xray-method" in body:
        files.add("SKILL.md")
    files = {f for f in files if (METHOD / f).is_file()}
    return sum(_words(METHOD / f) for f in files), files


class XrayLoadBudgetTests(unittest.TestCase):
    def test_reader_loads_stay_within_budget(self) -> None:
        for rel, budget in BUDGETS.items():
            if rel == "consumer":
                continue
            body = (PLUGIN / rel).read_text(encoding="utf-8")
            method_words, files = load(body)
            total = len(body.split()) + method_words
            with self.subTest(reader=rel):
                self.assertLessEqual(total, budget, f"{rel} loads {total} words from {sorted(files)}")

    def test_consumer_reading_an_analysis_stays_within_budget(self) -> None:
        # The consumer map: router, then reading.md, plus evidence.md to read source.
        total = sum(_words(METHOD / f) for f in ("SKILL.md", "references/reading.md", "references/evidence.md"))
        self.assertLessEqual(total, BUDGETS["consumer"])


if __name__ == "__main__":
    unittest.main()
