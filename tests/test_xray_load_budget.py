"""Measure explicit section/mode reads, not every resource mentioned in prose.

The unchanged core caps are the step 1 bounds. Runtime Method loads tables name
what a context reads; worker briefs belong to their worker, not the coordinator.
Named sections are actual bounded reads, never a discount on a whole-file read.
Missing resources, unknown selectors and missing boundaries fail closed.
"""

import re
import unittest
from collections import deque
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

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

# Separate optional baseline at 89a47aebbc99e5f92ffb96a7a0c52c425a61bb39.
# Step 1 did not measure these existing on-demand references. Core caps stay put.
# Methodology includes its already-declared bound-analysis reading dependency.
OPTIONAL_ALLOWANCES = {
    "methodology": 1_919 + 164,
    "patterns": 1_628,
    "comments": 1_869,
}
READ_CONDITIONS = {"always", "full", "lite", "update", "documentation", *OPTIONAL_ALLOWANCES}


def _words(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


def _rows(body: str):
    result = []
    in_loads, in_fence = False, False
    for line in body.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.match(r"^#{1,2} ", line):
            in_loads = line == "## Method loads"
            continue
        if not in_loads or not line.startswith("|"):
            continue
        fields = [value.strip().strip("`") for value in line.strip("|").split("|")]
        if fields[0] == "Resource" or all(re.fullmatch(r":?-+:?", field) for field in fields):
            continue
        if len(fields) != 3:
            raise ValueError(f"Malformed method load: {line}")
        path = fields[0].removeprefix("${CLAUDE_PLUGIN_ROOT}/skills/xray-method/")
        if path != "SKILL.md" and not re.fullmatch(r"references/[A-Za-z0-9_-]+\.md", path):
            raise ValueError(f"Unknown method resource: {path}")
        result.append((path, fields[1], fields[2]))
    return result


def _selected(text: str, selector: str) -> set[int]:
    lines = text.splitlines()
    titles, skeletons = {}, set()
    fence, opening = None, None
    for index, line in enumerate(lines):
        if line.startswith("```"):
            if fence is None:
                fence, opening = line[3:].strip(), index
            else:
                if fence == "markdown":
                    skeletons.update(range(opening, index + 1))
                fence = opening = None
            continue
        if fence is None and (match := re.match(r"^(#+) (.+)$", line)):
            titles[match[2]] = (index, len(match[1]))
    result = set()
    for part in selector.split(";"):
        part = part.strip()
        if part == "all":
            result.update(range(len(lines)))
        elif part == "skeletons":
            if not skeletons:
                raise ValueError("Requested canonical skeletons are absent")
            result.update(skeletons)
        else:
            kind, separator, title = part.partition(": ")
            if not separator or kind not in ("before", "from", "section"):
                raise ValueError(f"Unknown section selector: {part}")
            if title not in titles:
                raise ValueError(f"Missing section boundary: {title}")
            index, level = titles[title]
            if kind == "before":
                result.update(range(index))
            elif kind == "from":
                result.update(range(index, len(lines)))
            else:
                end = min((i for i, depth in titles.values() if i > index and depth <= level), default=len(lines))
                result.update(range(index, end))
    return result


def load(body: str, *, mode="full", documentation=False, options=frozenset()) -> tuple[int, set[str]]:
    """Follow declared loads in selected text, counting each source line once."""
    if mode not in ("full", "lite", "update"):
        raise ValueError(f"Unknown read mode: {mode}")
    if unknown := set(options) - OPTIONAL_ALLOWANCES.keys():
        raise ValueError(f"Unknown read options: {sorted(unknown)}")
    selected, texts, resource_lines = {}, {}, {}
    pending = deque([body])
    while pending:
        for path, selector, when in _rows(pending.popleft()):
            if when not in READ_CONDITIONS:
                raise ValueError(f"Unknown read condition: {when}")
            if path not in texts:
                # Declared optional paths must exist even before selecting them.
                texts[path] = (METHOD / path).read_text(encoding="utf-8")
                resource_lines[path] = texts[path].splitlines()
            indexes = _selected(texts[path], selector)
            if when == "documentation" and not documentation:
                continue
            if when in ("update", "full", "lite") and mode != when:
                continue
            if when in OPTIONAL_ALLOWANCES and when not in options:
                continue
            already_read = selected.setdefault(path, set())
            if indexes - already_read:
                already_read.update(indexes)
                lines = resource_lines[path]
                pending.append("\n".join(lines[index] for index in sorted(already_read)))
    total = sum(
        len("\n".join(resource_lines[path][index] for index in sorted(indexes)).split())
        for path, indexes in selected.items()
    )
    return total, set(selected)


def _option_sets():
    names = tuple(OPTIONAL_ALLOWANCES)
    return [frozenset(items) for size in range(len(names) + 1) for items in combinations(names, size)]


def _optional_allowance(options):
    return sum(OPTIONAL_ALLOWANCES[name] for name in options)


class XrayLoadBudgetTests(unittest.TestCase):
    def test_optional_loads_are_selected_and_follow_nested_tables(self) -> None:
        with TemporaryDirectory(dir=REPO_ROOT, prefix=".xray-budget-") as directory, patch.dict(globals(), {"METHOD": Path(directory)}):
            (METHOD / "references").mkdir()
            (METHOD / "SKILL.md").write_text(
                "# Router\n\n## Method loads\n\n"
                "| Resource | Sections | When |\n|---|---|---|\n"
                "| `references/semantic.md` | all | methodology |\n"
                "| `references/comments.md` | all | comments |\n",
                encoding="utf-8",
            )
            semantic = "# Semantic\n\n## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `references/reading.md` | all | always |\n"
            (METHOD / "references/semantic.md").write_text(semantic, encoding="utf-8")
            (METHOD / "references/comments.md").write_text("comment rules", encoding="utf-8")
            (METHOD / "references/reading.md").write_text("bound source reading", encoding="utf-8")
            body = "## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `SKILL.md` | all | always |\n"
            baseline, files = load(body)
            self.assertEqual(files, {"SKILL.md"})
            semantic_words, files = load(body, options=frozenset({"methodology"}))
            self.assertEqual(files, {"SKILL.md", "references/semantic.md", "references/reading.md"})
            self.assertEqual(semantic_words - baseline, len(semantic.split()) + 3)
            both_words, files = load(body, options=frozenset({"methodology", "comments"}))
            self.assertEqual(both_words - semantic_words, 2)
            self.assertIn("references/comments.md", files)

    def test_nested_missing_optional_resource_fails_without_selecting_option(self) -> None:
        with TemporaryDirectory(dir=REPO_ROOT, prefix=".xray-budget-") as directory, patch.dict(globals(), {"METHOD": Path(directory)}):
            (METHOD / "SKILL.md").write_text(
                "# Router\n\n## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `references/missing.md` | all | methodology |\n",
                encoding="utf-8",
            )
            with self.assertRaises(FileNotFoundError):
                load("## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `SKILL.md` | all | always |\n")

    def test_transitive_loads_deduplicate_and_converge_cycles(self) -> None:
        with TemporaryDirectory(dir=REPO_ROOT, prefix=".xray-budget-") as directory, patch.dict(globals(), {"METHOD": Path(directory)}):
            (METHOD / "references").mkdir()
            table = "\n\n## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `references/{resource}.md` | all | always |\n"
            first = "# First\n\nkept source" + table.format(resource="second")
            second = "# Second\n\nsource rules" + table.format(resource="first")
            (METHOD / "references/first.md").write_text(first, encoding="utf-8")
            (METHOD / "references/second.md").write_text(second, encoding="utf-8")
            body = "## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `references/first.md` | all | always |\n| `references/first.md` | section: First | always |\n"
            words, files = load(body)
            self.assertEqual(words, len(first.split()) + len(second.split()))
            self.assertEqual(files, {"references/first.md", "references/second.md"})

    def test_tables_outside_selected_text_are_not_traversed(self) -> None:
        with TemporaryDirectory(dir=REPO_ROOT, prefix=".xray-budget-") as directory, patch.dict(globals(), {"METHOD": Path(directory)}):
            (METHOD / "references").mkdir()
            (METHOD / "references/guide.md").write_text(
                "# Guide\n\n## Shared\n\nsource rules\n\n## Unused\n\n"
                "## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `references/missing.md` | all | always |\n",
                encoding="utf-8",
            )
            body = "## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `references/guide.md` | section: Shared | always |\n"
            self.assertEqual(load(body), (4, {"references/guide.md"}))

    def test_unknown_conditions_modes_and_options_fail_closed(self) -> None:
        body = "## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `SKILL.md` | all | guessing |\n"
        with self.assertRaisesRegex(ValueError, "Unknown read condition"):
            load(body)
        with self.assertRaisesRegex(ValueError, "Unknown read mode"):
            load("", mode="fast")
        with self.assertRaisesRegex(ValueError, "Unknown read options"):
            load("", options=frozenset({"guessing"}))

    def test_missing_named_load_fails_instead_of_disappearing(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load("## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `references/missing.md` | all | always |\n")

    def test_resource_mention_is_not_an_instruction_to_load_it(self) -> None:
        words, _ = load("The glossary mentions `references/evidence.md`.")
        self.assertEqual(words, 0)

    def test_reader_loads_stay_within_budget(self) -> None:
        for rel, budget in BUDGETS.items():
            if rel == "consumer":
                continue
            body = (PLUGIN / rel).read_text(encoding="utf-8")
            self.assertTrue(_rows(body), f"{rel} has no explicit runtime read contract")
            for mode in ("full", "lite", "update"):
                for documentation in (False, True):
                    for options in _option_sets():
                        method_words, files = load(body, mode=mode, documentation=documentation, options=options)
                        total = len(body.split()) + method_words
                        with self.subTest(reader=rel, mode=mode, documentation=documentation, options=sorted(options)):
                            self.assertLessEqual(total, budget + _optional_allowance(options), f"{rel} loads {total} words from {sorted(files)}")

    def test_consumer_reading_an_analysis_stays_within_budget(self) -> None:
        # The consumer map: router, then reading.md, plus evidence.md to read source.
        total = sum(_words(METHOD / f) for f in ("SKILL.md", "references/reading.md", "references/evidence.md"))
        self.assertLessEqual(total, BUDGETS["consumer"])

    def test_consumer_optional_worst_cases_stay_within_separate_allowance(self) -> None:
        body = """## Method loads

| Resource | Sections | When |
|---|---|---|
| `SKILL.md` | all | always |
| `references/reading.md` | all | always |
| `references/evidence.md` | before: Maintained documentation | always |
| `references/evidence.md` | from: Maintained documentation | documentation |
"""
        for mode in ("full", "lite", "update"):
            for documentation in (False, True):
                for options in _option_sets():
                    words, files = load(body, mode=mode, documentation=documentation, options=options)
                    with self.subTest(mode=mode, documentation=documentation, options=sorted(options)):
                        self.assertLessEqual(words, BUDGETS["consumer"] + _optional_allowance(options), str(sorted(files)))

    def test_optional_graphs_stay_within_the_frozen_resource_baseline(self) -> None:
        body = "## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `SKILL.md` | all | always |\n"
        baseline, files = load(body)
        self.assertEqual(files, {"SKILL.md"}, "Optional references entered the default load")
        resources = {
            "methodology": {"references/AI_ANALYSIS_METHODOLOGY.md", "references/reading.md"},
            "patterns": {"references/SEMANTIC_PATTERNS.md"},
            "comments": {"references/ANTIREZ_COMMENTING_STANDARDS.md"},
        }
        for options in _option_sets():
            words, files = load(body, options=options)
            with self.subTest(options=sorted(options)):
                self.assertEqual(files, {"SKILL.md"}.union(*(resources[name] for name in options)))
                self.assertLessEqual(words - baseline, _optional_allowance(options))


if __name__ == "__main__":
    unittest.main()
