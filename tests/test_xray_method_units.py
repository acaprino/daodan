"""The Codebase Map method is a router plus units, and each paragraph lives once.

`map-method/SKILL.md` names every unit under `references/` in its load map, and
the `analyze` workflow loads units instead of restating them. The failure this
guards against is the one the split removed: two copies of a procedure (Phase 0
lived in both the skill and the workflow) that drift apart while each stays
internally plausible.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "plugins" / "codebase-map"
METHOD = PLUGIN / "skills" / "map-method"
ROUTER = METHOD / "SKILL.md"
ANALYZE = METHOD / "references/entry-analyze.md"
UNITS = (
    "migration",
    "run",
    "snapshot",
    "update",
    "evidence",
    "reading",
    "phase-0",
    "phases-1-2",
    "phases-3-4",
    "phases-5-6",
    "phase-7",
)


def _paragraphs(text: str) -> list[str]:
    out, buf, fence = [], [], False
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.startswith("```"):
            fence = not fence
        if not fence and not line.strip() and not line.startswith("```"):
            if buf:
                out.append(" ".join(" ".join(buf).split()))
                buf = []
            continue
        buf.append(line)
    if buf:
        out.append(" ".join(" ".join(buf).split()))
    # Headings, rules, table rows and short lines repeat legitimately.
    return [
        p
        for p in out
        if len(p) > 80 and not re.fullmatch(r"#+ .*|---", p) and not p.startswith("|")
    ]


def _load_map(router: str) -> list[str]:
    section = router.split("## Load map", 1)[1].split("\n## ", 1)[0]
    return re.findall(r"`references/([a-z0-9-]+)\.md`", section)


class XrayMethodUnitsTests(unittest.TestCase):
    def test_load_map_names_every_unit_and_only_existing_ones(self) -> None:
        named = _load_map(ROUTER.read_text(encoding="utf-8"))
        self.assertEqual(sorted(named), sorted(UNITS))
        for unit in named:
            self.assertTrue((METHOD / "references" / f"{unit}.md").is_file(), unit)

    def test_no_paragraph_lives_twice(self) -> None:
        files = [ROUTER, ANALYZE] + [METHOD / "references" / f"{u}.md" for u in UNITS]
        seen: dict[str, Path] = {}
        for path in files:
            for paragraph in _paragraphs(path.read_text(encoding="utf-8")):
                with self.subTest(paragraph=paragraph[:80]):
                    self.assertNotIn(
                        paragraph,
                        seen,
                        f"{path.name} repeats a paragraph of {seen.get(paragraph, path).name}",
                    )
                seen.setdefault(paragraph, path)

    def test_analyze_loads_every_phase_unit(self) -> None:
        analyze = ANALYZE.read_text(encoding="utf-8")
        for unit in ("phase-0", "phases-1-2", "phases-3-4", "phases-5-6", "phase-7"):
            self.assertIn(
                f"${{CLAUDE_PLUGIN_ROOT}}/skills/map-method/references/{unit}.md", analyze
            )
        self.assertNotIn("## Phase 0: Project Knowledge Discovery", analyze)


if __name__ == "__main__":
    unittest.main()
