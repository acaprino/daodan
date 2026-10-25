"""Measure explicit section/mode reads, not every resource mentioned in prose.

Core caps only decrease as declared reads narrow. Runtime Method loads tables name
what a context reads; worker briefs belong to their worker, not the coordinator.
Named sections are actual bounded reads, never a discount on a whole-file read.
Missing resources, unknown selectors and missing boundaries fail closed.
"""

import re
import tomllib
import unittest
from collections import deque
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "plugins" / "codebase-map"
METHOD = PLUGIN / "skills" / "map-method"

UNIT_BUDGETS = {
    "SKILL.md": 927,
    "references/run.md": 811,
    "references/snapshot.md": 938,
    "references/update.md": 597,
    "references/deepen.md": 380,
    "references/evidence.md": 2_436,
    "references/reading.md": 142,
    "references/standalone.md": 280,
    "references/phase-0.md": 355,
    "references/phases-1-2.md": 801,
    "references/phases-3-4.md": 1_348,
    "references/phases-5-6.md": 1_265,
    "references/phase-7.md": 871,
}

# Since marketplace 38.0.0 the map's coordinator is `/daodan:map-code`, which loads
# `map-method` and runs one entry unit, then deepens the area. These bodies are what
# that coordinator reads, so the closure is measured from the entry units themselves.
COORDINATORS = {
    "coordinator:classic": (
        "## Method loads\n"
        "\n"
        "| Resource | Sections | When |\n"
        "|---|---|---|\n"
        "| `references/entry-analyze.md` | all | always |\n"
        "| `references/deepen.md` | section: Coordinator | always |\n"
    ),
    "coordinator:team": (
        "## Method loads\n"
        "\n"
        "| Resource | Sections | When |\n"
        "|---|---|---|\n"
        "| `references/entry-team-analyze.md` | all | always |\n"
        "| `references/deepen.md` | section: Coordinator | always |\n"
    ),
}

BUDGETS = {
    "coordinator:classic": 3_918,
    "roles/map-analyst.md": 9_128,
    "coordinator:team": 7_522,
    "roles/partition-structure-worker.md": 4_691,
    "roles/partition-behavior-worker.md": 4_846,
    "roles/partition-quality-worker.md": 5_635,
    "roles/partition-synthesizer.md": 3_977,
    "roles/semantic-interconnect-mapper.md": 5_795,
    "consumer": 3_742,
    "standalone-consumer": 1_717,
}

# Separate optional baseline at 89a47aebbc99e5f92ffb96a7a0c52c425a61bb39.
# Step 1 did not measure these existing on-demand references. Their caps stay put.
# Methodology includes its already-declared bound-analysis reading dependency.
OPTIONAL_ALLOWANCES = {
    "methodology": 1_919 + 164 + 290,
    "patterns": 1_628,
    "comments": 1_869,
    # New legacy-root branch is measured separately; original core caps stay fixed.
    "migration": 209,
}
READ_CONDITIONS = {
    "always", "full", "lite", "update", "cards", "documentation", "not-lite",
    "comments and not-lite", "documentation and not-lite", *OPTIONAL_ALLOWANCES,
    *(f"phase-{phase}" for phase in range(8)),
    "comments and phase-6",
    "comments and phase-6 and not-lite",
}

ROLE_RESOURCES = {
    "roles/partition-structure-worker.md": {"SKILL.md", "references/evidence.md", "references/phases-1-2.md", "references/run.md", "references/standalone.md", "references/reading.md"},
    "roles/partition-behavior-worker.md": {"SKILL.md", "references/evidence.md", "references/phases-3-4.md", "references/standalone.md", "references/reading.md"},
    "roles/partition-quality-worker.md": {"SKILL.md", "references/evidence.md", "references/phases-5-6.md", "references/standalone.md", "references/reading.md"},
    "roles/semantic-interconnect-mapper.md": {"SKILL.md", "references/evidence.md", "references/reading.md", "references/standalone.md"},
}


# Registration wrappers load exactly one owned instruction unit.
ROLE_RESOURCES = {
    role: resources | {f"references/role-{Path(role).stem}.md"}
    for role, resources in ROLE_RESOURCES.items()
}


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
        path = fields[0].removeprefix("${CLAUDE_PLUGIN_ROOT}/skills/map-method/")
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


def load(body: str, *, mode="full", documentation=False, options=frozenset(), phases=None) -> tuple[int, set[str]]:
    """Follow declared loads in selected text, counting each source line once."""
    if mode not in ("full", "lite", "update", "cards"):
        raise ValueError(f"Unknown read mode: {mode}")
    if unknown := set(options) - OPTIONAL_ALLOWANCES.keys():
        raise ValueError(f"Unknown read options: {sorted(unknown)}")
    if phases is None:
        phases = {0, 1, 2, 5, 7} if mode == "lite" else set() if mode == "cards" else set(range(8))
    if any(type(phase) is not int or phase not in range(8) for phase in phases):
        raise ValueError("Unknown analysis phase")
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
            if any(
                (condition == "documentation" and not documentation)
                or (condition == "not-lite" and mode == "lite")
                or (condition in ("update", "full", "lite", "cards") and mode != condition)
                or (condition in OPTIONAL_ALLOWANCES and condition not in options)
                or (condition.startswith("phase-") and int(condition[6:]) not in phases)
                for condition in when.split(" and ")
            ):
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
    def test_method_units_stay_within_their_word_budgets(self) -> None:
        for resource, budget in UNIT_BUDGETS.items():
            with self.subTest(resource=resource):
                self.assertLessEqual(_words(METHOD / resource), budget)

    def test_every_registered_reader_has_a_budget(self) -> None:
        components = tomllib.loads((PLUGIN / "plugin.toml").read_text(encoding="utf-8"))["components"]
        readers = {f"{kind}/{name}.md" for kind in ("roles", "workflows")
                   for name in components[kind]}
        self.assertEqual(set(BUDGETS) - {"consumer", "standalone-consumer"} - set(COORDINATORS), readers,
                         "A registered reader must not silently escape load measurement")

    def test_lite_phase_six_does_not_load_analyst_comment_procedures(self) -> None:
        body = (PLUGIN / "roles/map-analyst.md").read_text(encoding="utf-8")
        path = METHOD / "references/phases-5-6.md"
        original_read = Path.read_text
        text = path.read_text(encoding="utf-8")
        changed = text.replace("## Comment Type Classification\n", "## Comment Type Classification\n\ncomment-sentinel\n")
        self.assertNotEqual(text, changed)
        options = frozenset({"comments"})
        baseline = load(body, mode="lite", phases={0, 6}, options=options)
        with patch.object(Path, "read_text", autospec=True, side_effect=lambda p, **kw: changed if p == path else original_read(p, **kw)):
            self.assertEqual(load(body, mode="lite", phases={0, 6}, options=options), baseline)

    def test_analyst_partial_profiles_exclude_unselected_phase_units(self) -> None:
        body = (PLUGIN / "roles/map-analyst.md").read_text(encoding="utf-8")
        cases = {
            frozenset({0, 5}): {"references/phase-0.md", "references/phases-5-6.md"},
            frozenset({0, 6}): {"references/phase-0.md", "references/phases-5-6.md"},
            frozenset({0, 1, 2, 3, 4}): {"references/phase-0.md", "references/phases-1-2.md", "references/phases-3-4.md"},
            frozenset({7}): {"references/phase-7.md"},
        }
        common = {"SKILL.md", "references/evidence.md", "references/snapshot.md", "references/standalone.md", "references/reading.md"}
        for phases, resources in cases.items():
            with self.subTest(phases=sorted(phases)):
                words, files = load(body, phases=phases)
                self.assertEqual(files, common | resources)
                self.assertLessEqual(words + len(body.split()), BUDGETS["roles/map-analyst.md"])

    def test_analyst_cards_mode_reads_only_the_deepening_section(self) -> None:
        body = (PLUGIN / "roles/map-analyst.md").read_text(encoding="utf-8")
        words, files = load(body, mode="cards")
        self.assertEqual(files, {"SKILL.md", "references/evidence.md", "references/snapshot.md", "references/deepen.md", "references/standalone.md", "references/reading.md"})
        self.assertLessEqual(words + len(body.split()), BUDGETS["roles/map-analyst.md"])

    def test_classic_coordinator_closure_excludes_analysis_units(self) -> None:
        body = COORDINATORS["coordinator:classic"]
        core = {"SKILL.md", "references/entry-analyze.md", "references/run.md", "references/snapshot.md",
                "references/deepen.md"}
        for mode in ("full", "lite", "update"):
            for documentation in (False, True):
                for options in _option_sets():
                    _, files = load(body, mode=mode, documentation=documentation, options=options)
                    expected = core | ({"references/migration.md"} if "migration" in options else set())
                    with self.subTest(mode=mode, documentation=documentation, options=sorted(options)):
                        self.assertEqual(files, expected)

    def test_phase_seven_does_not_grant_workers_completion_or_view_ownership(self) -> None:
        body = (METHOD / "references/phase-7.md").read_text(encoding="utf-8")
        self.assertNotIn("Classic owner: set", body)
        self.assertIn("entry coordinator", body)
        self.assertIn("Workers never load presentation instructions", body)

    def test_phase_reads_select_only_requested_analysis_units(self) -> None:
        body = (
            "## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n"
            "| `references/phases-1-2.md` | all | phase-1 |\n"
            "| `references/phases-3-4.md` | all | phase-3 |\n"
            "| `references/phase-7.md` | all | phase-7 |\n"
        )
        self.assertEqual(load(body, phases={0, 1})[1], {"references/phases-1-2.md"})
        self.assertEqual(load(body, mode="lite")[1], {"references/phases-1-2.md", "references/phase-7.md"})
        self.assertEqual(load(body, phases={0, 3})[1], {"references/phases-3-4.md"})
        self.assertEqual(load(body, phases={7})[1], {"references/phase-7.md"})

    def test_phase_selectors_validate_inactive_inputs_and_reject_unknown_phase(self) -> None:
        for phases in ({8}, {-1}, {True}, {"1"}):
            with self.subTest(phases=phases), self.assertRaisesRegex(ValueError, "Unknown analysis phase"):
                load("", phases=phases)
        missing = "## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `references/missing.md` | all | phase-3 |\n"
        with self.assertRaises(FileNotFoundError):
            load(missing, phases={0, 1})

    def test_roles_load_only_their_owned_core_units(self) -> None:
        for role, expected in ROLE_RESOURCES.items():
            body = (PLUGIN / role).read_text(encoding="utf-8")
            for mode in ("full", "lite", "update"):
                for documentation in (False, True):
                    with self.subTest(role=role, mode=mode, documentation=documentation):
                        self.assertEqual(load(body, mode=mode, documentation=documentation)[1], expected)

    def test_quality_skipped_phase_and_comment_commands_are_not_loaded(self) -> None:
        body = (PLUGIN / "roles/partition-quality-worker.md").read_text(encoding="utf-8")
        path = "references/phases-5-6.md"
        original = (METHOD / path).read_text(encoding="utf-8")
        original_read = Path.read_text
        baselines = {
            (mode, options): load(body, mode=mode, options=options)[0]
            for mode in ("full", "lite", "update")
            for options in (frozenset(), frozenset({"comments"}))
        }
        sentinels = {
            "## Phase 6: Documentation Health": "phase-six-sentinel",
            "## Documentation Diagnosis Commands (Phase 6)": "doc-tools-sentinel",
            "## Comment Quality Commands (Antirez Standards)": "comment-tools-sentinel",
            "## Comment Type Classification": "comment-taxonomy-sentinel",
            "## Comment quality analysis": "comment-boundary-sentinel",
            "### Red Flags to Identify": "risk-taxonomy-sentinel",
        }
        for heading, sentinel in sentinels.items():
            with self.subTest(heading=heading):
                modified = original.replace(heading + "\n", heading + "\n\n" + sentinel + "\n")
                self.assertNotEqual(original, modified)
                with patch.object(Path, "read_text", autospec=True, side_effect=lambda p, **kw: modified if p == METHOD / path else original_read(p, **kw)):
                    for mode in ("full", "lite", "update"):
                        for options in (frozenset(), frozenset({"comments"})):
                            before = baselines[mode, options]
                            after, _ = load(body, mode=mode, options=options)
                            expected = heading == "### Red Flags to Identify" or (mode != "lite" and (not sentinel.startswith("comment-") or "comments" in options))
                            self.assertEqual(after - before, int(expected), (mode, options, heading))

    def test_role_optional_closures_do_not_admit_unrelated_units(self) -> None:
        resources = {
            "methodology": {"references/AI_ANALYSIS_METHODOLOGY.md", "references/reading.md", "references/standalone.md"},
            "patterns": {"references/SEMANTIC_PATTERNS.md"},
            "comments": {"references/ANTIREZ_COMMENTING_STANDARDS.md"},
            "migration": {"references/migration.md"},
        }
        for role, core in ROLE_RESOURCES.items():
            body = (PLUGIN / role).read_text(encoding="utf-8")
            for mode in ("full", "lite", "update"):
                for documentation in (False, True):
                    for options in _option_sets():
                        expected = core.union(*(resources[option] for option in options))
                        with self.subTest(role=role, mode=mode, documentation=documentation, options=sorted(options)):
                            self.assertEqual(load(body, mode=mode, documentation=documentation, options=options)[1], expected)

    def test_required_worker_evidence_and_partition_sections_remain_loaded(self) -> None:
        requirements = {
            "references/evidence.md": ["## Forbidden Files", "### Source reading in every code phase", "## File Classification Criteria"],
            "references/run.md": ["## Perimeter"],
            "references/phases-1-2.md": ["### Partition worker", "### Team extensions"],
            "references/phases-3-4.md": ["### Partition worker"],
            "references/phases-5-6.md": ["### Partition worker", "### Team extensions"],
        }
        original_read = Path.read_text
        for role, core in ROLE_RESOURCES.items():
            body = (PLUGIN / role).read_text(encoding="utf-8")
            for resource in core & requirements.keys():
                original = original_read(METHOD / resource, encoding="utf-8")
                for heading in requirements[resource]:
                    changed = original.replace(heading + "\n", heading + "\n\nrequired-rule-sentinel\n")
                    self.assertNotEqual(changed, original)
                    for mode in ("full", "lite", "update"):
                        before = load(body, mode=mode)[0]
                        with patch.object(Path, "read_text", autospec=True, side_effect=lambda p, **kw: changed if p == METHOD / resource else original_read(p, **kw)):
                            with self.subTest(role=role, heading=heading, mode=mode):
                                self.assertEqual(load(body, mode=mode)[0] - before, 1)

    def test_conjoined_conditions_are_closed_and_validate_inactive_resources(self) -> None:
        for condition in ("comments and guessing", "full and lite", "not-lite or comments"):
            body = "## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `SKILL.md` | all | " + condition + " |\n"
            with self.subTest(condition=condition), self.assertRaisesRegex(ValueError, "Unknown read condition"):
                load(body)
        body = "## Method loads\n\n| Resource | Sections | When |\n|---|---|---|\n| `references/missing.md` | all | comments and not-lite |\n"
        with self.assertRaises(FileNotFoundError):
            load(body, mode="lite")

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
            if rel in ("consumer", "standalone-consumer"):
                continue
            body = COORDINATORS[rel] if rel in COORDINATORS else (PLUGIN / rel).read_text(encoding="utf-8")
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

    def test_standalone_consumer_stays_within_budget(self) -> None:
        body = """## Method loads

| Resource | Sections | When |
|---|---|---|
| `references/standalone.md` | all | always |
| `references/reading.md` | section: Task views | always |
| `references/evidence.md` | section: CRITICAL PRINCIPLE: EVIDENCE-ANCHORED OUTPUT | always |
| `references/evidence.md` | section: Forbidden Files | always |
"""
        words, files = load(body)
        self.assertEqual(files, {
            "references/standalone.md", "references/reading.md", "references/evidence.md",
        })
        self.assertLessEqual(_words(METHOD / "SKILL.md") + words, BUDGETS["standalone-consumer"])

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
            "methodology": {"references/AI_ANALYSIS_METHODOLOGY.md", "references/reading.md", "references/standalone.md"},
            "patterns": {"references/SEMANTIC_PATTERNS.md"},
            "comments": {"references/ANTIREZ_COMMENTING_STANDARDS.md"},
            "migration": {"references/migration.md"},
        }
        for options in _option_sets():
            words, files = load(body, options=options)
            with self.subTest(options=sorted(options)):
                self.assertEqual(files, {"SKILL.md"}.union(*(resources[name] for name in options)))
                self.assertLessEqual(words - baseline, _optional_allowance(options))


if __name__ == "__main__":
    unittest.main()
