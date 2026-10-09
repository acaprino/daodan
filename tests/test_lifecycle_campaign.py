"""Installed campaign entries and their cross-plugin/run-state boundaries.

These contracts use the real kernels and render every host. A method may name
perfectly good workers yet fail on an installed host if its entry has no binding
for them. The protocol exercise also checks the multi-run candidate transition:
historical stages remain valid, but closure requires a current final verify run.
"""

import contextlib
import fnmatch
import hashlib
import io
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.catalogs import render_catalog  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.model import INLINE_WORKER_REFERENCE  # noqa: E402
from scripts.daodan.render import render_plugin  # noqa: E402

ADAPTERS = REPO_ROOT / "adapters"
LIFECYCLE = REPO_ROOT / "plugins/project-lifecycle"
PROTOCOL = REPO_ROOT / "plugins/project-protocol/skills/project-protocol/scripts/run_state.py"
ENTRIES = {
    "claude": "commands/{name}.md",
    "copilot": "prompts/{name}.prompt.md",
    "codex": "skills/{name}-workflow/SKILL.md",
    "pi": "prompts/project-lifecycle-{name}.md",
    "opencode": "commands/{name}.md",
}


def workflow_roles(plugin, workflow):
    """Resolve the full declared dispatch surface, including dynamic selection."""
    references = set(workflow.dispatch.roles)
    if workflow.dispatch.inline_workers:
        references.add(INLINE_WORKER_REFERENCE)
    for phase in workflow.phases:
        references.update(item.removeprefix("role:") for item in phase.fanout)
        if phase.role:
            references.add(phase.role)
        if phase.fanout_from and not phase.role:
            references.update(plugin.components.roles)
    return {item if "/" in item else f"{plugin.name}/{item}" for item in references}


class LifecycleCampaignRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.registry = {
            path.parent.name: load_plugin(path.parent)
            for path in sorted((REPO_ROOT / "plugins").glob("*/plugin.toml"))
        }
        cls.plugin = cls.registry["project-lifecycle"]
        cls.workflows = {workflow.name: workflow for workflow in cls.plugin.workflows}
        cls.commands = ("maintain", "handover")
        # Fail here when an entry is absent, rather than silently testing a subset.
        cls.references = {
            name: workflow_roles(cls.plugin, cls.workflows[name]) for name in cls.commands
        }
        owners = {reference.partition("/")[0] for roles in cls.references.values()
                  for reference in roles}
        cls.rendered_plugins = [cls.registry[name] for name in sorted(owners | {cls.plugin.name})]
        cls.packages = {}
        cls.catalogs = {}
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            packages = {}
            for plugin in cls.rendered_plugins:
                target = Path(cls.temp.name) / host / plugin.name
                render_plugin(plugin, adapter, target, adapters_root=ADAPTERS,
                              plugin_registry=cls.registry)
                packages[plugin.name] = target
            cls.packages[host] = packages
            cls.catalogs[host] = json.loads(render_catalog(
                host, cls.rendered_plugins, "0.0.0", packages
            ))

    def entry(self, host, name):
        package = self.packages[host][self.plugin.name]
        if host == "copilot":
            return package / f"agents/{name}-coordinator.agent.md"
        return package / ENTRIES[host].format(name=name)

    def test_both_entries_and_their_canonical_methods_are_registered(self):
        self.assertTrue(set(self.commands).issubset(self.plugin.components.workflows))
        self.assertTrue({"maintainer-method", "handover-method"}.issubset(
            self.plugin.components.skills
        ))
        methods = {"maintain": "maintainer-method", "handover": "handover-method"}
        for host in HOSTS:
            for name, skill in methods.items():
                with self.subTest(host=host, workflow=name):
                    package = self.packages[host][self.plugin.name]
                    path = package / ENTRIES[host].format(name=name)
                    self.assertTrue(path.is_file(), path)
                    self.assertTrue((package / f"skills/{skill}/SKILL.md").is_file())
                    self.assertIn(f"project-lifecycle:{skill}", self.entry(host, name).read_text(
                        encoding="utf-8"
                    ))
                    shipped = package / f"contracts/{name}.workflow.toml"
                    self.assertEqual(shipped.read_text(encoding="utf-8"),
                                     (LIFECYCLE / f"workflows/{name}.toml").read_text(encoding="utf-8"))

    def test_maintain_binds_the_composed_methods_entire_dispatch_surface(self):
        required = {"clean-code/clean-code-agent"}
        for name in ("assess", "repair", "change", "verify", "consolidate"):
            required.update(workflow_roles(self.plugin, self.workflows[name]))
        review = self.registry["senior-review"]
        team_review = next(workflow for workflow in review.workflows if workflow.name == "team-review")
        required.update(workflow_roles(review, team_review))
        self.assertTrue(required.issubset(self.references["maintain"]),
                        f"Unbound composed workers: {sorted(required - self.references['maintain'])}")
        self.assertTrue(self.workflows["maintain"].dispatch.isolated)
        self.assertTrue(self.workflows["maintain"].dispatch.inline_workers)

    def test_handover_exposes_only_its_assigned_consultant_workers(self):
        required = {
            "project-knowledge/codebase-explorer",
            "project-knowledge/onboarding-writer",
            "project-knowledge/guide-reviewer",
        }
        permitted = required | {"codebase-xray/semantic-interconnect-mapper"}
        self.assertTrue(required.issubset(self.references["handover"]))
        self.assertTrue(self.references["handover"].issubset(permitted),
                        f"Unscoped handover worker surface: {self.references['handover'] - permitted}")
        self.assertTrue(self.workflows["handover"].dispatch.isolated)
        self.assertFalse(self.workflows["handover"].dispatch.inline_workers)

    def test_handover_has_one_dossier_writer_and_review_before_result(self):
        workflow = self.workflows["handover"]
        writers = [phase for phase in workflow.phases
                   if "artifact:handover-dossier" in phase.produces]
        self.assertEqual(len(writers), 1)
        writer = writers[0]
        self.assertEqual(writer.role, "project-knowledge/onboarding-writer")
        reviewer = next(phase for phase in workflow.phases
                        if phase.role == "project-knowledge/guide-reviewer")
        self.assertIn(writer.id, reviewer.needs)
        self.assertIn("artifact:handover-dossier", reviewer.consumes)
        closures = [phase for phase in workflow.phases if "artifact:result" in phase.produces]
        self.assertEqual(len(closures), 1)
        self.assertIn(reviewer.id, closures[0].needs)
        self.assertIn("artifact:handover-dossier", closures[0].consumes)
        self.assertIn("handover-dossier", workflow.contract.artifacts)
        self.assertIn("project-unchanged", workflow.contract.outcomes)

    def test_every_worker_has_an_actual_hard_dependency_and_registered_role(self):
        for name, references in self.references.items():
            for reference in references:
                with self.subTest(workflow=name, role=reference):
                    owner, _, role = reference.partition("/")
                    self.assertIn(owner, self.plugin.required_dependencies)
                    self.assertIn(owner, self.registry)
                    self.assertIn(role, self.registry[owner].components.roles)
                    self.assertTrue((self.registry[owner].root / f"roles/{role}.md").is_file())

    def test_worker_bindings_reach_installed_bodies_or_native_agent_allowlists(self):
        for host in HOSTS:
            for name, references in self.references.items():
                entry = self.entry(host, name).read_text(encoding="utf-8")
                for reference in references:
                    with self.subTest(host=host, workflow=name, role=reference):
                        owner, _, role = reference.partition("/")
                        identity = f"{owner}:{role}"
                        self.assertIn(identity, entry)
                        if host in {"codex", "pi"}:
                            path = self.packages[host][self.plugin.name] / f"contracts/dispatch/{owner}/{role}.md"
                            source = (self.registry[owner].root / f"roles/{role}.md").read_text(
                                encoding="utf-8"
                            )
                            digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
                            text = path.read_text(encoding="utf-8")
                            self.assertIn(f"Owner: {identity}", text)
                            self.assertIn(f"source-sha256: {digest}", text)
                        elif host == "copilot":
                            allowlist = next(line for line in entry.splitlines() if line.startswith("agents:"))
                            self.assertIn(f"'{identity}'", allowlist)

    def test_native_catalogs_register_commands_and_named_worker_owners(self):
        for host, catalog in self.catalogs.items():
            if host == "opencode":
                listing = catalog["daodan"]["plugins"]
                entry = listing[self.plugin.name]
                commands = {item["name"]: item["file"] for item in entry["commands"]}
                for name in self.commands:
                    self.assertEqual(commands[f"project-lifecycle:{name}"], f"commands/{name}.md")
                for reference in set.union(*self.references.values()):
                    owner, _, role = reference.partition("/")
                    self.assertIn(f"{owner}:{role}", {item["id"] for item in listing[owner]["agents"]})
                continue
            if host == "pi":
                for name in self.commands:
                    parent = f"./exports/pi/plugins/project-lifecycle/{Path(ENTRIES[host].format(name=name)).parent.as_posix()}"
                    self.assertTrue(any(fnmatch.fnmatchcase(parent, pattern) for pattern in catalog["pi"]["prompts"]))
                continue
            listing = {entry["name"]: entry for entry in catalog["plugins"]}
            entry = listing[self.plugin.name]
            for name in self.commands:
                with self.subTest(host=host, workflow=name):
                    kind, path = {
                        "claude": ("commands", f"./commands/{name}.md"),
                        "codex": ("skills", f"./skills/{name}-workflow"),
                        "copilot": ("agents", f"./agents/{name}-coordinator.agent.md"),
                    }[host]
                    self.assertIn(path, entry[kind])
            if host in {"claude", "copilot"}:
                for reference in set.union(*self.references.values()):
                    owner, _, role = reference.partition("/")
                    suffix = ".agent.md" if host == "copilot" else ".md"
                    self.assertIn(f"./agents/{role}{suffix}", listing[owner]["agents"])

    def test_entry_metadata_preserves_protocol_contracts_without_fake_invocation(self):
        for name in self.commands:
            workflow = self.workflows[name]
            with self.subTest(workflow=name):
                self.assertFalse(any(phase.invoke for phase in workflow.phases))
                self.assertTrue({
                    "project-protocol/contracts/work.toml",
                    "project-protocol/contracts/project-result.toml",
                }.issubset(workflow.contract.shared_schemas))


class CampaignRunBoundaryTests(unittest.TestCase):
    """Exercise the protocol calls that a campaign uses between native entries."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project"
        self.project.mkdir()
        self.source = self.project / "app.py"
        self.source.write_text("initial candidate\n", encoding="utf-8")
        self.runtime = runpy.run_path(str(PROTOCOL))
        self.counter = 0

    def call(self, command, run_id, payload=None, extra=(), success=True):
        arguments = [command, "--project", str(self.project), "--run-id", run_id, *extra]
        if payload is not None:
            self.counter += 1
            path = Path(self.temp.name) / f"input-{self.counter}.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            arguments += ["--payload", str(path)]
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            code = self.runtime["main"](arguments)
        if success:
            self.assertEqual(code, 0, error.getvalue())
            return json.loads(output.getvalue())
        self.assertNotEqual(code, 0, output.getvalue())
        return error.getvalue()

    def init(self, operation, run_id, **overrides):
        payload = {
            "operation": operation, "objective": "Consultant handover" if operation == "assess" else "Maintain candidate",
            "scope": {"paths": ["app.py"], "focus": "all"},
            "authorizations": {"mode": "read-only"}, "budget": {"max_workers": 1},
            **overrides,
        }
        return self.call("init", run_id, payload)

    def test_new_entries_use_existing_operations_and_run_owned_dossier_deliveries(self):
        record = self.init("assess", "handover")
        directory = self.project / ".daodan/runs/handover"
        (directory / "handover.md").write_text("Source-observed commands, execution unavailable.\n", encoding="utf-8")
        closed = self.call("update", "handover", {
            "status": "complete",
            "deliveries": {"onboarding": {"status": "delivered", "output": "handover.md"}},
        }, ("--expected-revision", str(record["revision"])))
        self.assertEqual(closed["operation"], "assess")
        self.assertEqual(self.source.read_text(encoding="utf-8"), "initial candidate\n")
        self.assertFalse((self.project / "docs").exists())
        for operation in ("handover", "maintain"):
            with self.subTest(operation=operation):
                error = self.call("init", operation, {
                    "operation": operation, "objective": "Do not invent a protocol operation",
                    "scope": {"paths": ["app.py"]}, "authorizations": {}, "budget": {},
                }, success=False)
                self.assertIn("Unknown lifecycle operation", error)

    def test_historical_stages_survive_new_candidates_but_final_verify_requires_current_gates(self):
        prior = self.init("assess", "analysis")
        self.call("update", "analysis", {"status": "complete"}, ("--expected-revision", "0"))
        self.source.write_text("corrected candidate\n", encoding="utf-8")
        self.assertTrue(self.call("validate", "analysis")["valid"])
        self.assertIn("snapshot", self.call("resume", "analysis", {
            "authorizations": prior["authorizations"]
        }, success=False))
        final = self.init("verify", "final-verify", required_gates=["final-check"])
        self.assertNotEqual(prior["candidate"]["snapshot"], final["candidate"]["snapshot"])
        self.assertIn("required gate", self.call("update", "final-verify", {
            "status": "complete"
        }, ("--expected-revision", "0"), success=False))
        stale_gate = {"status": "passed", "head": prior["candidate"]["head"],
                      "snapshot": prior["candidate"]["snapshot"]["digest"],
                      "evidence": {"command": "project final check"}}
        self.assertIn("Stale candidate gate", self.call("update", "final-verify", {
            "status": "complete", "gates": {"final-check": stale_gate}
        }, ("--expected-revision", "0"), success=False))
        current_gate = {**stale_gate, "head": final["candidate"]["head"],
                        "snapshot": final["candidate"]["snapshot"]["digest"]}
        self.call("update", "final-verify", {
            "status": "complete", "gates": {"final-check": current_gate}
        }, ("--expected-revision", "0"))
        self.assertTrue(self.call("validate", "final-verify", extra=("--current",))["valid"])
        self.source.write_text("candidate changed after verification\n", encoding="utf-8")
        self.assertTrue(self.call("validate", "final-verify")["valid"])
        self.assertIn("snapshot", self.call("validate", "final-verify", extra=("--current",), success=False))


if __name__ == "__main__":
    unittest.main()
