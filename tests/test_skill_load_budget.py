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
LIFECYCLE = REPO_ROOT / "plugins/project-delivery/skills/delivery-method"
ASSESS = REPO_ROOT / "plugins/project-lifecycle/skills/assess-method"
PROTOCOL = REPO_ROOT / "plugins/work-controller/skills/work-record/SKILL.md"
AUTHORING = PROTOCOL.parent / "references/component-authoring.md"
QUESTIONS = PROTOCOL.parent / "references/questions.md"
ADR = REPO_ROOT / "plugins/project-delivery/skills/adr-method"
FRD = REPO_ROOT / "plugins/project-delivery/skills/frd-method"
BOOTSTRAP = REPO_ROOT / "plugins/project-delivery/skills/project-bootstrap/SKILL.md"
REVIEW = REPO_ROOT / "plugins/senior-review/skills"

UNIT_CAPS = {
    LIFECYCLE / "SKILL.md": 578,
    LIFECYCLE / "references/change.md": 321,
    LIFECYCLE / "references/preflight.md": 580,
    LIFECYCLE / "references/interview.md": 354,
    LIFECYCLE / "references/waves.md": 515,
    LIFECYCLE / "references/worker-brief.md": 300,
    LIFECYCLE / "references/verify.md": 300,
    LIFECYCLE / "references/finish.md": 250,
    LIFECYCLE / "references/realign.md": 243,
    LIFECYCLE / "references/sync.md": 175,
    LIFECYCLE / "references/retention.md": 420,
    LIFECYCLE / "references/brainstorm.md": 260,
    LIFECYCLE / "references/init.md": 265,
    LIFECYCLE / "references/first-use.md": 291,
    LIFECYCLE / "references/refactor.md": 245,
    LIFECYCLE / "references/continue.md": 188,
    LIFECYCLE / "references/status.md": 150,
    LIFECYCLE / "references/repair.md": 335,
    LIFECYCLE / "references/investigate.md": 180,
    LIFECYCLE / "references/document.md": 240,
    FRD / "SKILL.md": 500,
    FRD / "references/frd-schema.md": 900,
    BOOTSTRAP: 400,
    ASSESS / "SKILL.md": 230,
    ASSESS / "references/assess.md": 740,
    ASSESS / "references/native-reports.md": 230,
    PROTOCOL: 1_325,
    QUESTIONS: 95,
    AUTHORING: 208,
    ADR / "SKILL.md": 428,
    ADR / "references/adr-template.md": 375,
    REVIEW / "review-method/SKILL.md": 450,
    REVIEW / "review-method/references/light.md": 500,
    REVIEW / "investigation-method/SKILL.md": 595,
    REVIEW / "review-preparation/SKILL.md": 520,
    REVIEW / "review-preparation/references/candidate-grounding.md": 1_215,
    REVIEW / "review-preparation/references/stack-dimensions.md": 650,
    REVIEW / "review-preparation/references/knowledge-bindings.md": 465,
    REVIEW / "review-quality-gates/SKILL.md": 895,
    REVIEW / "review-quality-gates/references/context-sharing.md": 560,
    REVIEW / "review-quality-gates/references/verification-panel.md": 500,
    REVIEW / "review-preparation/references/team-review.md": 3_050,
    REVIEW / "review-consolidation/SKILL.md": 480,
}

# What one coordinator context holds at each step, beside the always-loaded
# project instructions. The protocol skill is loaded once per run and counted
# in every step, because it stays in the context.
STEPS = {
    "component authoring": (PROTOCOL, AUTHORING),
    "change: preflight": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/preflight.md"),
    "change: interview and record": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/interview.md",
                                     QUESTIONS, ADR / "SKILL.md", ADR / "references/adr-template.md"),
    "change: plan and execution": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/waves.md",
                                   LIFECYCLE / "references/worker-brief.md"),
    "verify": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/verify.md"),
    "change: wave review": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/waves.md",
                            REVIEW / "review-method/SKILL.md", REVIEW / "review-method/references/light.md"),
    "finish": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/finish.md",
               LIFECYCLE / "references/realign.md", ADR / "SKILL.md"),
    "sync": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/sync.md",
             LIFECYCLE / "references/realign.md", ADR / "SKILL.md"),
    "brainstorm": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/brainstorm.md", QUESTIONS, ADR / "SKILL.md"),
    "light review, standalone": (PROTOCOL, REVIEW / "review-method/SKILL.md", REVIEW / "review-method/references/light.md"),
    "investigation": (PROTOCOL, REVIEW / "investigation-method/SKILL.md"),
    "initialization": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/init.md", ADR / "SKILL.md"),
    "first use": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/first-use.md", ADR / "SKILL.md"),
    "refactor: plan and execution": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/refactor.md",
                                     LIFECYCLE / "references/waves.md", LIFECYCLE / "references/worker-brief.md"),
    "continue": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/continue.md"),
    "status": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/status.md"),
    "investigation handoff": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/investigate.md"),
    "documentation": (PROTOCOL, LIFECYCLE / "SKILL.md", LIFECYCLE / "references/document.md"),
    "knowledge bootstrap": (PROTOCOL, BOOTSTRAP, FRD / "SKILL.md", FRD / "references/frd-schema.md", ADR / "SKILL.md"),
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
    "component authoring": 1_538,
    "change: preflight": 2_543,
    "change: interview and record": 3_212,
    "change: plan and execution": 2_773,
    "verify": 2_343,
    "change: wave review": 3_638,
    "finish": 2_895,
    "sync": 2_820,
    "brainstorm": 2_697,
    "light review, standalone": 2_503,
    "investigation": 1_933,
    "initialization": 2_662,
    "first use": 2_646,
    "refactor: plan and execution": 3_018,
    "continue": 2_160,
    "status": 2_118,
    "investigation handoff": 2_200,
    "documentation": 2_250,
    "knowledge bootstrap": 3_300,
    "review preparation, before the variant": 3_410,
    # Before the split, this step loaded the whole quality-gates skill (1,800 words)
    # and the unlightened team preparation (3,562): 9,647 words.
    "team review: preparation and dispatch": 7_985,
    "review consolidation": 2_020,
}


# Count the brief after first loading it; no existing step cap increases.
CONTEXT_BRIEF = LIFECYCLE / "references/context-cycle.md"
UNIT_CAPS[CONTEXT_BRIEF] = 22
STEPS = {name: (*units, CONTEXT_BRIEF) if LIFECYCLE / "SKILL.md" in units else units
         for name, units in STEPS.items()}


def words(path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        text = text.split("\n---\n", 1)[1]
    return len(re.findall(r"\S+", text))


class SkillLoadBudgetTests(unittest.TestCase):
    def test_component_authoring_load_is_required_only_for_authoring(self):
        protocol = PROTOCOL.read_text(encoding="utf-8")
        section = protocol.split("## Authoring components\n", 1)[1].split("\n## ", 1)[0]
        hook = " ".join(section.split())
        self.assertRegex(hook, r"^Before creating or updating\b")
        for component in ("skills", "agents", "roles", "workflows", "prompts",
                          "tools", "templates", "specialist guidance"):
            self.assertIn(component, hook)
        self.assertRegex(hook, r", read and apply `references/component-authoring\.md`\.$")
        self.assertEqual(STEPS["component authoring"], (PROTOCOL, AUTHORING))
        for step, units in STEPS.items():
            if step != "component authoring":
                self.assertNotIn(AUTHORING, units, "unrelated steps do not load authoring detail")

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
        for method in ("review-quality-gates", "delivery-method", "review-method"):
            self.assertNotIn(method, brief, "a worker never loads a coordinator method")


if __name__ == "__main__":
    unittest.main()
