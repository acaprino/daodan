"""Load budgets for the loop and review methods a coordinator reads.

A coordinator holding several thousand words of normative prose as simultaneous
constraints is where an economical model fails. These tests make density a
number the CI controls: each unit has a word cap, each step of the loop has a cap
on the union of units it loads, and the micro-task worker receives a template
small enough to hold whole. A cap only goes down. When a unit is lightened, lower
its cap in the same change; never raise one to make an edit pass.

Words are whitespace-separated tokens of the body, front matter excluded, the
same measure tests/test_xray_load_budget.py applies to the Codebase Map.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = REPO_ROOT / "plugins/project-lifecycle/skills/lifecycle-method"
PROTOCOL = REPO_ROOT / "plugins/project-protocol/skills/project-protocol/SKILL.md"
ADR = REPO_ROOT / "plugins/project-knowledge/skills/adr-method"
REVIEW = REPO_ROOT / "plugins/senior-review/skills"

UNIT_CAPS = {
    LIFECYCLE / "SKILL.md": 630,
    LIFECYCLE / "references/change.md": 325,
    LIFECYCLE / "references/preflight.md": 580,
    LIFECYCLE / "references/interview.md": 445,
    LIFECYCLE / "references/waves.md": 515,
    LIFECYCLE / "references/worker-brief.md": 300,
    LIFECYCLE / "references/verify.md": 380,
    LIFECYCLE / "references/finish.md": 250,
    LIFECYCLE / "references/realign.md": 260,
    LIFECYCLE / "references/sync.md": 175,
    LIFECYCLE / "references/retention.md": 420,
    LIFECYCLE / "references/brainstorm.md": 300,
    LIFECYCLE / "references/init.md": 265,
    LIFECYCLE / "references/refactor.md": 245,
    LIFECYCLE / "references/continue.md": 195,
    LIFECYCLE / "references/status.md": 150,
    LIFECYCLE / "references/repair.md": 335,
    LIFECYCLE / "references/assess.md": 740,
    PROTOCOL: 1_695,
    ADR / "SKILL.md": 430,
    ADR / "references/adr-template.md": 375,
    REVIEW / "review-method/SKILL.md": 565,
    REVIEW / "review-method/references/light.md": 600,
    REVIEW / "investigation-method/SKILL.md": 595,
    REVIEW / "review-preparation/SKILL.md": 525,
    REVIEW / "review-preparation/references/candidate-grounding.md": 1_215,
    REVIEW / "review-preparation/references/stack-dimensions.md": 650,
    REVIEW / "review-preparation/references/knowledge-bindings.md": 465,
    REVIEW / "review-quality-gates/SKILL.md": 895,
    REVIEW / "review-quality-gates/references/context-sharing.md": 560,
    REVIEW / "review-quality-gates/references/verification-panel.md": 535,
    REVIEW / "review-preparation/references/team-review.md": 3_130,
    REVIEW / "review-consolidation/SKILL.md": 595,
}

# What one coordinator context holds at each step, beside the always-loaded
# project instructions. The protocol skill is loaded once per run and counted
# in every step, because it stays in the context.
STEPS = {
    "change: preflight": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/preflight.md"),
    "change: interview and record": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/interview.md",
                                     ADR / "SKILL.md", ADR / "references/adr-template.md"),
    "change: plan and execution": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/waves.md",
                                   LIFECYCLE / "references/worker-brief.md"),
    "verify": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/verify.md"),
    "change: wave review": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/waves.md",
                            REVIEW / "review-method/SKILL.md", REVIEW / "review-method/references/light.md"),
    "finish": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/finish.md",
               LIFECYCLE / "references/realign.md", ADR / "SKILL.md"),
    "sync": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/sync.md",
             LIFECYCLE / "references/realign.md", ADR / "SKILL.md"),
    "brainstorm": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/brainstorm.md", ADR / "SKILL.md"),
    "light review, standalone": (PROTOCOL, REVIEW / "review-method/SKILL.md", REVIEW / "review-method/references/light.md"),
    "investigation": (PROTOCOL, REVIEW / "investigation-method/SKILL.md"),
    "initialization": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/init.md", ADR / "SKILL.md"),
    "refactor: plan and execution": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/refactor.md",
                                     LIFECYCLE / "references/waves.md", LIFECYCLE / "references/worker-brief.md"),
    "continue": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/continue.md"),
    "status": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/status.md"),
    "review preparation, before the variant": (
        REVIEW / "review-method/SKILL.md", REVIEW / "review-preparation/SKILL.md",
        REVIEW / "review-preparation/references/candidate-grounding.md",
        REVIEW / "review-preparation/references/stack-dimensions.md",
        REVIEW / "review-preparation/references/knowledge-bindings.md"),
    "team review: preparation and dispatch": (
        REVIEW / "review-method/SKILL.md", REVIEW / "review-preparation/SKILL.md",
        REVIEW / "review-preparation/references/candidate-grounding.md",
        REVIEW / "review-preparation/references/team-review.md",
        REVIEW / "review-preparation/references/stack-dimensions.md",
        REVIEW / "review-preparation/references/knowledge-bindings.md",
        REVIEW / "review-quality-gates/SKILL.md",
        REVIEW / "review-quality-gates/references/context-sharing.md"),
    "review consolidation": (
        REVIEW / "review-consolidation/SKILL.md", REVIEW / "review-quality-gates/SKILL.md",
        REVIEW / "review-quality-gates/references/verification-panel.md"),
}
STEP_CAPS = {
    "change: preflight": 2_895,
    "change: interview and record": 3_565,
    "change: plan and execution": 3_125,
    "verify": 2_695,
    "change: wave review": 3_990,
    "finish": 3_255,
    "sync": 3_180,
    "brainstorm": 3_050,
    "light review, standalone": 2_855,
    "investigation": 2_285,
    "initialization": 3_015,
    "refactor: plan and execution": 3_370,
    "continue": 2_515,
    "status": 2_470,
    "review preparation, before the variant": 3_410,
    # Before the split, this step loaded the whole quality-gates skill (1,800 words)
    # and the unlightened team preparation (3,562): 9,647 words.
    "team review: preparation and dispatch": 7_985,
    "review consolidation": 2_020,
}


def words(path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        text = text.split("\n---\n", 1)[1]
    return len(re.findall(r"\S+", text))


class SkillLoadBudgetTests(unittest.TestCase):
    def test_every_unit_stays_under_its_cap(self):
        for path, cap in UNIT_CAPS.items():
            with self.subTest(unit=path.relative_to(REPO_ROOT).as_posix()):
                self.assertTrue(path.is_file())
                self.assertLessEqual(words(path), cap)

    def test_every_loop_step_holds_a_bounded_context(self):
        self.assertEqual(set(STEPS), set(STEP_CAPS))
        for step, units in STEPS.items():
            with self.subTest(step=step):
                self.assertLessEqual(sum(words(path) for path in units), STEP_CAPS[step])

    def test_the_lifecycle_load_map_names_only_shipped_units(self):
        method = (LIFECYCLE / "SKILL.md").read_text(encoding="utf-8")
        load_map = method.split("## Load map", 1)[1].split("\n## ", 1)[0]
        named = set(re.findall(r"`(references/[\w.-]+\.md)`", load_map))
        self.assertTrue(named)
        for relative in sorted(named):
            with self.subTest(reference=relative):
                self.assertTrue((LIFECYCLE / relative).is_file())
        shipped = {f"references/{path.name}" for path in (LIFECYCLE / "references").glob("*.md")}
        self.assertEqual(shipped - named, set(), "every reference is reachable from the load map")

    def test_the_worker_receives_a_closed_template_not_the_methods(self):
        brief = (LIFECYCLE / "references/worker-brief.md").read_text(encoding="utf-8")
        for field in ("write_set:", "expected failure before the change:", "verification after the change:",
                      "examples to make pass:", "invariants to keep:", "## Prior rulings in this run"):
            self.assertIn(field, brief)
        for code in ("- OK,", "- NEEDS_REPLAN,", "- ORACLE_INVALID,"):
            self.assertIn(code, brief)
        for method in ("review-quality-gates", "lifecycle-method", "review-method"):
            self.assertNotIn(method, brief, "a worker never loads a coordinator method")


if __name__ == "__main__":
    unittest.main()
