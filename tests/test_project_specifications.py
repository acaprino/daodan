"""Specification contracts survive entry and nested-resource rendering on all hosts.

These are package contract checks. They do not demonstrate that a live host
selected a skill, obtained human approval, or executed the delivery workflow.
"""

import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import render_plugin  # noqa: E402
from host_binding_assertions import loaded_instruction_text, without_host_binding  # noqa: E402


class ProjectSpecificationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="daodan-spec-contracts-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.packages = {}
        registry = {path.parent.name: load_plugin(path.parent)
                    for path in (REPO_ROOT / "plugins").glob("*/plugin.toml")}
        cls.registry = registry
        for host in HOSTS:
            adapter = load_adapter(REPO_ROOT / "adapters", host)
            for owner in ("daodan", "project-delivery", "project-knowledge", "python-development"):
                package = Path(cls.temporary.name) / host / owner
                render_plugin(registry[owner], adapter, package,
                              adapters_root=REPO_ROOT / "adapters",
                              plugin_registry=registry)
                cls.packages[host, owner] = package

    def body(self, host, owner, relative):
        path = self.packages[host, owner] / relative
        self.assertTrue(path.is_file(), f"Required specification resource missing: {path}")
        return without_host_binding(self, path.read_text(encoding="utf-8"), host)

    def reference(self, host, name):
        return self.body(host, "project-delivery",
                         f"skills/delivery-method/references/{name}.md")

    def entry(self, host, name):
        paths = {
            "claude": f"commands/{name}.md",
            "codex": f"skills/{name}-workflow/SKILL.md",
            "copilot": f"agents/{name}-coordinator.agent.md",
            "pi": f"prompts/daodan-{name}.md",
            "opencode": f"commands/{name}.md",
        }
        path = self.packages[host, "daodan"] / paths[host]
        return loaded_instruction_text(self, path, host)

    def test_specification_resource_is_reachable_from_every_consuming_phase(self):
        for host in HOSTS:
            with self.subTest(host=host):
                method = self.body(host, "project-delivery", "skills/delivery-method/SKILL.md")
                self.assertIn("references/specification.md", method)
                for phase in ("brainstorm", "interview", "waves", "continue", "verify"):
                    with self.subTest(phase=phase):
                        self.assertIn("references/specification.md", self.reference(host, phase))
                self.reference(host, "specification")

    def test_destination_is_project_owned_and_existing_inputs_remain_usable(self):
        for host in HOSTS:
            with self.subTest(host=host):
                spec = " ".join(self.reference(host, "specification").split())
                self.assertRegex(spec, r"docs/specs/[^`\s]+\.md")
                self.assertRegex(spec, r"(?i)(user|project).{0,100}(destination|path)")
                self.assertRegex(spec, r"(?i)(existing|supplied).{0,140}(spec|document)")
                self.assertRegex(spec, r"(?i)(never|do not|no).{0,80}(move|relocat|migrat)")
                self.assertNotRegex(spec, r"(?i)(default|new).{0,50}docs/(superpowers|daodan)/specs")

    def test_approval_binds_exact_specification_independently_of_adrs(self):
        for host in HOSTS:
            with self.subTest(host=host):
                spec = " ".join(self.reference(host, "specification").split())
                self.assertIn("SHA-256", spec)
                self.assertIn("intent.md", spec)
                self.assertRegex(spec, r"(?i)approv")
                self.assertRegex(spec, r"(?i)(question|answer)")
                self.assertRegex(spec, r"(?i)(without|regardless|with or without|even without).{0,35}(ADR|record)")
                self.assertRegex(spec, r"(?i)(chang|edit|differ).{0,100}(approv|invalidat|review)")
                self.assertRegex(spec, r"(?i)(ADR|decision).{0,120}(separate|distinct|link|decision)")

    def test_entries_keep_one_specification_through_design_and_implementation(self):
        for host in HOSTS:
            with self.subTest(host=host):
                brainstorm = self.entry(host, "brainstorm-idea")
                feature = self.entry(host, "new-feature")
                for entry in (brainstorm, feature):
                    self.assertIn("specification", entry.lower())
                    self.assertRegex(entry, r"(?i)project-delivery.{0,100}delivery-method")
                    self.assertNotRegex(entry, r"(?i)(load|invoke|follow)\s+`?superpowers")
                body = " ".join(self.reference(host, "brainstorm").split())
                self.assertNotIn("the only project file a brainstorm writes", body)
                self.assertRegex(body, r"(?i)(write|draft).{0,100}specification")
                self.assertRegex(body, r"(?i)(empty|no code|without code)")

    def test_durable_instructions_carry_neutral_path_and_design_routing(self):
        for host in HOSTS:
            with self.subTest(host=host):
                text = self.body(host, "project-knowledge", "skills/instructions-method/SKILL.md")
                block = text.split("## Loop block", 1)[1].split("\n## ", 1)[0]
                self.assertIn("docs/specs/", block)
                self.assertRegex(block, r"(?i)brainstorm")
                self.assertNotRegex(block, r"(?i)(always|guarantee).{0,80}(activat|automat)")

    def test_plans_workers_and_resume_preserve_the_same_approval_binding(self):
        for host in HOSTS:
            with self.subTest(host=host):
                waves = " ".join(self.reference(host, "waves").split())
                brief = self.reference(host, "worker-brief")
                resume = " ".join(self.reference(host, "continue").split())
                for text in (waves, brief):
                    self.assertIn("SHA-256", text)
                    self.assertRegex(text, r"(?i)specification.{0,100}(path|binding)")
                    self.assertRegex(text, r"(?i)approval.{0,35}(source|question|run)")
                self.assertIn("specification:", brief)
                self.assertRegex(resume, r"(?i)verify.{0,90}specification.{0,90}before resuming")
                self.assertRegex(resume, r"(?i)changed.{0,90}approval.{0,30}plans")
                self.assertRegex(waves, r"(?i)legacy.{0,100}without a specification")

    def test_brainstorm_handoff_can_dispatch_every_feature_cycle_worker(self):
        workflows = {workflow.name: workflow for workflow in self.registry["daodan"].workflows}
        brainstorm = workflows["brainstorm-idea"]
        feature = workflows["new-feature"]
        self.assertLessEqual(set(feature.worker_references()), set(brainstorm.worker_references()),
                             "Same-context continuation must retain the feature cycle's workers")
        self.assertLessEqual(set(feature.contract.shared_schemas),
                             set(brainstorm.contract.shared_schemas))
        for host in HOSTS:
            with self.subTest(host=host):
                harness = self.entry(host, "brainstorm-idea").split("## Method", 1)[0]
                for owner, role in (("senior-review", "premise-auditor"),
                                    ("python-development", "python-engineer"),
                                    ("typescript-development", "typescript-engineer")):
                    self.assertIn(role, harness)
                    if host in {"codex", "pi"}:
                        resource = f"contracts/dispatch/{owner}/{role}.md"
                        self.assertIn(resource, harness)
                        self.body(host, "daodan", resource)

    def test_candidate_review_consumes_the_approved_specification_requirements(self):
        for host in HOSTS:
            with self.subTest(host=host):
                verify = " ".join(self.reference(host, "verify").split())
                self.assertIn("references/specification.md", verify)
                self.assertRegex(verify, r"(?i)(verify|recheck).{0,100}specification")
                self.assertIn("EX-*", verify)
                self.assertIn("INV-*", verify)
                self.assertRegex(verify, r"(?i)(pass|carry|supply).{0,120}specification")

    def test_standalone_initialization_requires_approved_design_before_scaffolding(self):
        for host in HOSTS:
            with self.subTest(host=host):
                entry = " ".join(self.entry(host, "init-project").split())
                self.assertIn("references/init.md", entry)
                self.assertNotRegex(entry, r"(?i)scaffold(?:ed)? (?:it )?first")
                self.assertRegex(entry, r"(?i)specification.{0,60}approv|approv.{0,60}specification")
                initialization = self.reference(host, "init")
                unscaffolded = " ".join(re.split(
                    r"\n## (?:An existing project|Existing project)", initialization, maxsplit=1
                )[0].split())
                self.assertIn("references/specification.md", unscaffolded)
                self.assertIn("references/brainstorm.md", unscaffolded)
                scaffolder = unscaffolded.index("python-development:python-scaffold-method")
                self.assertLess(unscaffolded.index("references/specification.md"), scaffolder)
                self.assertLess(unscaffolded.index("references/brainstorm.md"), scaffolder)
                other_stack = re.search(r"(?i)(official|stack).{0,30}initializer", unscaffolded)
                self.assertIsNotNone(other_stack)
                self.assertLess(unscaffolded.index("references/brainstorm.md"), other_stack.start())
                self.assertRegex(unscaffolded, r"(?i)(reuse|reus).{0,100}approv")
                self.assertRegex(unscaffolded, r"(?i)(return|resume|continue).{0,80}(initializ|here)")
                self.assertRegex(unscaffolded, r"(?i)(not|no|without).{0,80}(feature|execution|change cycle)")

    def test_initialization_can_dispatch_design_review_and_existing_setup_workers(self):
        workflows = {workflow.name: workflow for workflow in self.registry["daodan"].workflows}
        initialization = workflows["init-project"]
        required = {"senior-review/premise-auditor", "codebase-map/map-analyst",
                    "project-knowledge/instructions-auditor"}
        self.assertLessEqual(required, set(initialization.worker_references()))
        for host in HOSTS:
            with self.subTest(host=host):
                harness = self.entry(host, "init-project").split("## Method", 1)[0]
                for reference in required:
                    owner, role = reference.split("/", 1)
                    self.assertIn(role, harness)
                    if host in {"codex", "pi"}:
                        resource = f"contracts/dispatch/{owner}/{role}.md"
                        self.assertIn(resource, harness)
                        self.body(host, "daodan", resource)

    def test_python_scaffolder_preserves_the_coordinators_documented_project_root(self):
        for host in HOSTS:
            with self.subTest(host=host):
                method = self.body(host, "python-development", "skills/python-scaffold-method/SKILL.md")
                inputs = " ".join(method.split("## Inputs", 1)[1].split("\n## ", 1)[0].split())
                self.assertIn("docs/specs/", inputs)
                self.assertIn(".daodan/", inputs)
                self.assertRegex(inputs, r"(?i)(caller|coordinator|supplied|explicit).{0,80}(root|folder)")
                self.assertRegex(inputs, r"(?i)preserv.{0,90}(document|record|file|content|docs/)")
                self.assertRegex(inputs, r"(?i)(existing|already).{0,60}(application|scaffold)")
                self.assertRegex(inputs, r"(?i)(reject|refuse|out of scope)")
                self.assertRegex(inputs, r"(?i)(never|do not|no).{0,70}(new|different|another|second|nested).{0,40}(root|directory|folder)")

    def test_delivery_requires_its_local_owners_without_superpowers_dispatch(self):
        delivery = self.registry["project-delivery"]
        self.assertIn("work-controller", delivery.required_dependencies)
        self.assertIn("senior-review", delivery.required_dependencies)
        self.assertFalse(any(name.startswith("superpowers")
                             for name in delivery.required_dependencies))


if __name__ == "__main__":
    unittest.main()
