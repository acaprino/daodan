"""Cross-host contract parity for the review pipeline.

`team-review` is the complex canary: fan-out over selected dimensions, isolated
reviewer contexts, a delivery barrier, cross-examination in fresh contexts and a
single writer for the final report. The topology each host picks may differ. The
observable contract may not.

Since marketplace 38.0.0 the variant runs under `daodan:review-branch`. Its
sidecar declares the reviewers, isolated and inline dispatch, the shared record
contracts and the seven outcomes, but no phase graph: the order, the barrier and
the single report owner that `senior-review`'s own team-review graph used to
render are stated by the three units the variant reads in sequence, preparation,
method and consolidation. These tests hold the obligations there.
"""

import json
import re
import sys
import tomllib
import unittest
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402

CLUSTER = (
    "repo-hygiene",
    "react-development",
    "platform-engineering",
    "typescript-development",
    "testing",
    "codebase-map",
    "abstraction-architect",
    "senior-review",
)

#: The units the team-review variant reads, in the order it reads them.
UNITS = ("review-preparation", "review-method", "review-consolidation")

#: Phase headings across those units. Until 38.0.0 this order was the phase
#: graph of `senior-review/workflows/team-review.toml`; the units now own it.
PHASE_ORDER = ("0", "0b", "0c", "1", "1a", "1c", "1d", "1b", "2", "3", "4", "4b", "4c", "5")

RECORD_CONTRACTS = (
    "review-brief",
    "reviewer-binding",
    "reviewer-selection",
    "evidenced-finding",
    "reviewer-result",
    "delivery-ledger",
    "final-report",
)

OUTCOMES = (
    "reviewers-use-isolated-contexts",
    "every-selected-dimension-is-dispatched-exactly-once",
    "every-expected-reviewer-is-delivered-or-failed",
    "consolidation-runs-only-after-the-delivery-barrier",
    "cross-examination-runs-in-fresh-contexts",
    "every-retained-finding-carries-evidence",
    "only-the-consolidator-writes-the-final-report",
)

#: What the preparation unit requires of any harness, one line per obligation.
EXECUTION_REQUIREMENTS = (
    "every reviewer runs in its own context and never reads another reviewer's result",
    "exactly the selected dimensions are dispatched, once each",
    "every expected reviewer is recorded `delivered` or `failed` before anything is consolidated",
    "cross-examination runs after that barrier, in fresh contexts",
    "only the consolidation phase writes the final report",
)

ISOLATION = ("dispatch the **most specialized agent** from the table below, "
             "each reviewer in its own isolated context.")
BARRIER = "Hold the delivery barrier: wait until every dispatched reviewer is recorded `delivered` or `failed`."
GATE = ("consolidation does not start until every spawned reviewer has either delivered "
        "its findings file or delivered an explicit no-findings report.")
EXPECTED_SET = "The dispatched reviewers are the expected set that Phase 3's delivery barrier waits on."
CONSOLIDATED = "Write `.team-review/99-consolidated.md`."
VERIFIES_CONSOLIDATED = "select consolidated findings with confidence `>= 50%`"
FRESH_LENSES = ("dispatch lenses 1 and 2 independently through the declared "
                "`project-protocol:isolated-worker` binding")
FINAL_REPORT = "Save this complete native final report"
SINGLE_WRITER = "A single final writer emits the report."
REPORT_OWNER = "Keep one review preparation and final report owner"


def prose(text: str) -> str:
    return " ".join(text.split())


def unit_text(skills: Path, skill: str) -> str:
    return (skills / skill / "references/team-review.md").read_text(encoding="utf-8")


def phase_ids(text: str) -> list[str]:
    return re.findall(r"(?m)^#{2,3} Phase ([0-9][a-z]?):", text)


def load_review_branch():
    plugin = load_plugin(REPO_ROOT / "plugins/daodan")
    return next(workflow for workflow in plugin.workflows if workflow.name == "review-branch")


@dataclass(frozen=True)
class CompiledPackage:
    """The entry package and the method package one host installs together."""

    host: str
    root: Path

    @property
    def entry(self) -> Path:
        return self.root / "daodan"

    @property
    def review(self) -> Path:
        return self.root / "senior-review"

    @property
    def _workflow(self) -> dict:
        with (self.entry / "contracts/review-branch.workflow.toml").open("rb") as handle:
            return tomllib.load(handle)

    @property
    def _strategy(self):
        provenance = json.loads(
            (self.entry / ".daodan-provenance.json").read_text(encoding="utf-8")
        )
        name = provenance["harnessStrategies"]["review-branch"]
        adapter = load_adapter(REPO_ROOT / "adapters", self.host)
        return next(item for item in adapter.strategies if item.name == name)

    def _unit(self, skill: str) -> str:
        return prose(unit_text(self.review / "skills", skill))

    @property
    def has_isolated_workers(self) -> bool:
        dispatch = self._workflow["dispatch"]
        return (
            self._strategy.isolated
            and dispatch["isolated"] is True
            and dispatch["inline_workers"] is True
            and ISOLATION in self._unit("review-method")
        )

    @property
    def has_delivery_barrier(self) -> bool:
        method = self._unit("review-method")
        return (
            BARRIER in method
            and GATE in method
            and (self.review / "contracts/delivery-ledger.toml").is_file()
            and "senior-review/contracts/delivery-ledger.toml"
            in self._workflow["contract"]["shared_schemas"]
        )

    @property
    def has_cross_examination(self) -> bool:
        # Verification reads the consolidated set, never the raw one.
        unit = self._unit("review-consolidation")
        return (
            unit.index(CONSOLIDATED) < unit.index("## Phase 4b")
            and VERIFIES_CONSOLIDATED in unit
            and FRESH_LENSES in unit
        )

    @property
    def has_consolidation(self) -> bool:
        # The report is written once, after verification and the critic close.
        unit = self._unit("review-consolidation")
        skill = prose((self.review / "skills/review-consolidation/SKILL.md").read_text(encoding="utf-8"))
        return (
            unit.index("## Phase 4c") < unit.index("## Phase 5") < unit.index(FINAL_REPORT)
            and SINGLE_WRITER in skill
        )

    def artifact_root(self, name: str) -> str:
        policy = REPO_ROOT / "exports" / self.host / "plugins/codebase-map/policies/write-confinement.toml"
        with policy.open("rb") as handle:
            return tomllib.load(handle)["roots"][name]


def compiled_review_package(host: str) -> CompiledPackage:
    return CompiledPackage(host, REPO_ROOT / "exports" / host / "plugins")


class ReviewPipelinePortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skills = REPO_ROOT / "plugins/senior-review/skills"
        cls.units = {skill: unit_text(cls.skills, skill) for skill in UNITS}

    def test_the_whole_cluster_is_a_neutral_kernel(self):
        for name in CLUSTER:
            with self.subTest(plugin=name):
                self.assertTrue((REPO_ROOT / "plugins" / name / "plugin.toml").is_file())

    def test_team_review_kernel_requires_isolated_fanout_and_barrier(self):
        # Until 38.0.0 the team-review graph declared an isolated, preferred-parallel
        # fan-out over `selection:reviewers` joined by `all-delivered`, then
        # consolidation and cross-examination. The entry now declares isolated
        # dispatch of every reviewer the units can select; the units state the rest.
        workflow = load_review_branch()
        self.assertTrue(workflow.dispatch.isolated)
        self.assertTrue(workflow.dispatch.inline_workers)
        registry = {path.parent.name: load_plugin(path.parent)
                    for path in (REPO_ROOT / "plugins").glob("*/plugin.toml")}
        named = set()
        for text in (*self.units.values(),
                     (self.skills / "review-preparation/references/stack-dimensions.md").read_text(encoding="utf-8")):
            for owner, role in re.findall(r"`([a-z-]+):([a-z-]+)`", text):
                if owner in registry and role in registry[owner].components.roles:
                    named.add(f"{owner}/{role}")
        named.discard("project-protocol/isolated-worker")
        self.assertGreaterEqual(len(named), 18, sorted(named))
        self.assertEqual(sorted(named - set(workflow.dispatch.roles)), [])

        method = prose(self.units["review-method"])
        self.assertIn("## Phase 2: Adversarial Review (parallel)", method)
        self.assertIn("For each selected dimension (always-on + detected conditional)", method)
        self.assertIn(ISOLATION, method)
        self.assertIn(EXPECTED_SET, method)
        self.assertIn(BARRIER, method)
        self.assertIn(GATE, method)
        skill = prose((self.skills / "review-method/SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("Account for every selected worker before starting consolidation.", skill)
        self.assertIn("No worker receives peer findings before delivery.", skill)
        consolidation = prose(self.units["review-consolidation"])
        self.assertLess(consolidation.index(CONSOLIDATED), consolidation.index("## Phase 4b"))
        self.assertIn(VERIFIES_CONSOLIDATED, consolidation)
        self.assertIn(FRESH_LENSES, consolidation)

    def test_team_review_declares_every_phase_in_order(self):
        sequence = [identity for skill in UNITS for identity in phase_ids(self.units[skill])]
        self.assertEqual(tuple(sequence), PHASE_ORDER)
        overview = re.findall(r"(?m)^\| ([0-9]) \|", self.units["review-preparation"])
        self.assertEqual(overview, ["0", "1", "2", "3", "4", "5"])
        requirements = prose(self.units["review-preparation"])
        for requirement in EXECUTION_REQUIREMENTS:
            with self.subTest(requirement=requirement):
                self.assertIn(f"- {requirement}", requirements)

    def test_only_the_final_phase_produces_the_report(self):
        # The graph's `consolidation` phase was the only producer of
        # `artifact:final-report`. Since 38.0.0 the consolidation unit's last
        # phase saves it, its skill names a single final writer, and reviewers
        # write only their own findings files.
        self.assertIn("only-the-consolidator-writes-the-final-report", load_review_branch().contract.outcomes)
        writers = [skill for skill in UNITS if FINAL_REPORT in self.units[skill]]
        self.assertEqual(writers, ["review-consolidation"])
        consolidation = prose(self.units["review-consolidation"])
        self.assertLess(consolidation.index("## Phase 5"), consolidation.index(FINAL_REPORT))
        self.assertIn(SINGLE_WRITER, prose(
            (self.skills / "review-consolidation/SKILL.md").read_text(encoding="utf-8")))
        self.assertIn(REPORT_OWNER, prose((self.skills / "review-method/SKILL.md").read_text(encoding="utf-8")))
        self.assertIn("Write your output to .team-review/findings-{dimension}.md", self.units["review-method"])

    def test_every_record_contract_exists(self):
        plugin = load_plugin(REPO_ROOT / "plugins/senior-review")
        shared = load_review_branch().contract.shared_schemas
        for name in RECORD_CONTRACTS:
            with self.subTest(contract=name):
                self.assertTrue(
                    (REPO_ROOT / "plugins/senior-review/contracts" / f"{name}.toml").is_file()
                )
                self.assertIn(Path("contracts") / f"{name}.toml", plugin.contract_exports)
                self.assertIn(f"senior-review/contracts/{name}.toml", shared)

    def test_review_branch_keeps_the_team_review_outcomes(self):
        outcomes = load_review_branch().contract.outcomes
        for outcome in OUTCOMES:
            with self.subTest(outcome=outcome):
                self.assertIn(outcome, outcomes)

    def test_every_host_preserves_team_review_contract(self):
        for host in HOSTS:
            with self.subTest(host=host):
                package = compiled_review_package(host)
                self.assertTrue(package.has_isolated_workers)
                self.assertTrue(package.has_delivery_barrier)
                self.assertTrue(package.has_cross_examination)
                self.assertTrue(package.has_consolidation)
                self.assertEqual(package.artifact_root("xray"), ".codebase-map")

    def test_senior_review_no_longer_depends_on_an_external_team_runtime(self):
        plugin = load_plugin(REPO_ROOT / "plugins/senior-review")
        self.assertNotIn(
            "agent-teams",
            " ".join(plugin.required_dependencies),
            "scheduling belongs to the host harness, not to a runtime dependency",
        )

    def test_unified_review_keeps_all_dimension_providers_required(self):
        # The method's owner and the entry that dispatches its reviewers both
        # declare every dimension provider (the entry since 38.0.0).
        for owner in ("senior-review", "daodan"):
            plugin = load_plugin(REPO_ROOT / "plugins" / owner)
            for dimension in (
                "repo-hygiene",
                "codebase-map",
                "abstraction-architect",
                "testing",
                "project-protocol",
                "react-development",
                "platform-engineering",
                "typescript-development",
            ):
                with self.subTest(owner=owner, dimension=dimension):
                    self.assertIn(dimension, plugin.required_dependencies)

    def test_every_reviewer_states_the_anchor_metric_as_the_method_does(self):
        # Each reviewer carries its own copy of the pipeline conventions on purpose, so a
        # correction has to reach every copy. The method calls anchor citations an
        # operational measure; twelve roles kept calling them a quality metric.
        canonical = ("Findings that cite map anchors feed the map utilization rate, "
                     "an operational measure of map consumption, not a quality signal.")
        method = (REPO_ROOT / "plugins/senior-review/skills/review-quality-gates/SKILL.md").read_text(encoding="utf-8")
        self.assertIn(canonical, " ".join(method.split()))
        carriers = []
        for role in sorted((REPO_ROOT / "plugins").glob("*/roles/*.md")):
            text = " ".join(role.read_text(encoding="utf-8").split())
            label = f"{role.parent.parent.name}/{role.stem}"
            with self.subTest(role=label):
                self.assertNotIn("quality metric", text)
                if "Findings that cite map anchors" in text:
                    self.assertIn(canonical, text)
                    carriers.append(label)
        self.assertGreaterEqual(len(carriers), 12, carriers)


if __name__ == "__main__":
    unittest.main()
