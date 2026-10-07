"""Runtime dependency contracts are read from kernels before catalog generation."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import lint_dependency_graph as graph  # noqa: E402


class DependencyGraphTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.plugins = self.root / "plugins"
        self.plugins.mkdir()
        self.patch = patch.object(graph, "PLUGINS", self.plugins)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def kernel(self, name, *, dependencies=(), optional=(), roles=(), exports=()):
        root = self.plugins / name
        root.mkdir()
        (root / "plugin.toml").write_text(
            f'name = "{name}"\n'
            '[dependencies]\n'
            f'required = {json.dumps(list(dependencies))}\n'
            f'optional = {json.dumps(list(optional))}\n'
            '[components]\n'
            f'roles = {json.dumps(list(roles))}\n'
            '[contracts]\n'
            f'exports = {json.dumps(list(exports))}\n',
            encoding="utf-8")
        return root

    def sidecar(self, owner, content):
        path = self.plugins / owner / "workflows" / "review.toml"
        path.parent.mkdir(exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def body(self, owner, content):
        path = self.plugins / owner / "workflows" / "review.md"
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(content, encoding="utf-8")
        return path

    def references(self):
        plugins = graph.load_plugins()
        return plugins, graph.extract_references(plugins)

    def test_phase_role_is_declared_used_and_resolves_without_catalog(self):
        self.kernel("coordinator", dependencies=["reviewer"])
        self.kernel("reviewer", roles=["audit"])
        self.sidecar("coordinator", '[[phases]]\nid = "audit"\nrole = "reviewer/audit"\n')
        # A generated catalog from an older tree must not be the authority.
        catalog = self.root / ".claude-plugin" / "marketplace.json"
        catalog.parent.mkdir()
        catalog.write_text('{"plugins": []}', encoding="utf-8")
        plugins, refs = self.references()
        self.assertEqual(graph.check_declarations(plugins), [])
        self.assertEqual(graph.check_runtime_refs(plugins, refs), [])
        self.assertEqual(graph.check_deps_are_used(plugins, refs), [])
        self.assertEqual([(ref.namespace, ref.target) for ref in refs], [("reviewer", "audit")])

    def test_multiline_fanout_reads_only_role_bindings_and_reports_field_line(self):
        self.kernel("coordinator", dependencies=["reviewer"])
        self.kernel("reviewer", roles=["audit", "check"])
        self.sidecar("coordinator", '''[[phases]]
id = "review"
fanout = [
    "role:reviewer/audit",
    "reviewer/check",
    "artifact:ignored/data",
]
''')
        plugins, refs = self.references()
        self.assertEqual([ref.target for ref in refs], ["audit", "check"])
        self.assertEqual([ref.line_no for ref in refs], [3, 3])
        self.assertEqual(graph.check_runtime_refs(plugins, refs), [])
        self.assertEqual(graph.check_deps_are_used(plugins, refs), [])

    def test_shared_schema_is_runtime_use_without_a_role_or_skill_load(self):
        self.kernel("coordinator", dependencies=["protocol"])
        self.kernel("protocol", exports=["contracts/result.toml"])
        self.sidecar("coordinator", '''[contract]
shared_schemas = ["protocol/contracts/result.toml"]
''')
        plugins, refs = self.references()
        self.assertEqual([ref.kind for ref in refs], ["shared-schema"])
        self.assertEqual(graph.check_runtime_refs(plugins, refs), [])
        self.assertEqual(graph.check_deps_are_used(plugins, refs), [])

    def test_method_dispatch_and_inline_worker_are_declared_runtime_use(self):
        self.kernel("coordinator", dependencies=["reviewer", "project-protocol"])
        self.kernel("reviewer", roles=["audit"])
        self.kernel("project-protocol", roles=["isolated-worker"])
        self.sidecar("coordinator", '''[dispatch]
roles = ["reviewer/audit", "coordinator/local"]
isolated = true
inline_workers = true
''')
        plugins, refs = self.references()
        self.assertEqual([(ref.namespace, ref.target) for ref in refs],
                         [("reviewer", "audit"), ("project-protocol", "isolated-worker")])
        self.assertEqual(graph.check_runtime_refs(plugins, refs), [])
        self.assertEqual(graph.check_deps_are_used(plugins, refs), [])

    def test_explicit_neutral_role_brief_is_runtime_use(self):
        self.kernel("coordinator", dependencies=["reviewer"])
        self.kernel("reviewer", roles=["audit"])
        self.body("coordinator", 'Isolated worker brief:\n  - role: "reviewer:audit"\n')
        plugins, refs = self.references()
        self.assertEqual([ref.kind for ref in refs], ["neutral-role"])
        self.assertEqual(graph.check_runtime_refs(plugins, refs), [])
        self.assertEqual(graph.check_deps_are_used(plugins, refs), [])

    def test_undeclared_provider_fails_for_each_exact_runtime_binding(self):
        for binding in ("phase", "fanout", "schema", "brief"):
            with self.subTest(binding=binding):
                # Each variant uses the same provider but no declared dependency.
                if binding == "phase":
                    self.kernel("coordinator")
                    self.kernel("reviewer", roles=["audit"], exports=["contracts/result.toml"])
                if binding == "brief":
                    sidecar = self.plugins / "coordinator" / "workflows" / "review.toml"
                    sidecar.unlink()
                    self.body("coordinator", 'role: reviewer:audit\n')
                else:
                    content = {
                        "phase": '[[phases]]\nrole = "reviewer/audit"\n',
                        "fanout": '[[phases]]\nfanout = ["role:reviewer/audit"]\n',
                        "schema": '[contract]\nshared_schemas = ["reviewer/contracts/result.toml"]\n',
                    }[binding]
                    self.sidecar("coordinator", content)
                plugins, refs = self.references()
                problems = graph.check_runtime_refs(plugins, refs)
                self.assertTrue(any("not in coordinator's dependencies" in p for p in problems), problems)

    def test_unknown_neutral_provider_is_not_discarded_as_a_prose_namespace(self):
        self.kernel("coordinator")
        self.body("coordinator", '  - role: "missing:audit"\n')
        plugins, refs = self.references()
        self.assertEqual([ref.namespace for ref in refs], ["missing"])
        self.assertTrue(any("unknown provider 'missing'" in p
                            for p in graph.check_runtime_refs(plugins, refs)))

    def test_unknown_metadata_provider_and_unregistered_owner_fail(self):
        self.kernel("coordinator", dependencies=["missing"])
        self.sidecar("coordinator", '[[phases]]\nrole = "missing/audit"\n')
        self.body("orphan", 'role: missing:audit\n')
        plugins, refs = self.references()
        self.assertTrue(any("bare dependency 'missing'" in p
                            for p in graph.check_declarations(plugins)))
        problems = graph.check_runtime_refs(plugins, refs)
        self.assertTrue(any("unknown provider 'missing'" in p for p in problems), problems)
        self.assertTrue(any("orphan: has runtime references but no plugin.toml" in p
                            for p in problems), problems)
        self.assertEqual(graph.check_degrade_notes(plugins, refs), [])

    def test_explicit_role_and_schema_must_exist_in_provider_exports(self):
        self.kernel("coordinator", dependencies=["reviewer"])
        self.kernel("reviewer", roles=["audit"], exports=["contracts/result.toml"])
        self.sidecar("coordinator", '''[[phases]]
role = "reviewer/absent"
[contract]
shared_schemas = ["reviewer/contracts/absent.toml"]
''')
        plugins, refs = self.references()
        problems = graph.check_runtime_refs(plugins, refs)
        self.assertTrue(any("role 'reviewer/absent' is not declared" in p for p in problems), problems)
        self.assertTrue(any("shared schema 'reviewer/contracts/absent.toml' is not exported" in p
                            for p in problems), problems)

    def test_prose_suggestions_and_artifact_selections_do_not_back_dependencies(self):
        self.kernel("coordinator", dependencies=["reviewer"])
        self.kernel("reviewer", roles=["audit"])
        self.body("coordinator", '''See reviewer:audit for background.
Next step: run /reviewer:audit.
TRIGGER WHEN: dispatch reviewer:audit for this topic.
role: "user" | "admin";
''')
        self.sidecar("coordinator", '''# role = "reviewer/audit" is only an example here.
[[phases]]
id = "select"
fanout_from = "selection:reviewer"
produces = ["artifact:reviewer/audit"]
[contract]
schemas = ["contracts/reviewer.toml"]
''')
        plugins, refs = self.references()
        self.assertEqual(refs, [])
        self.assertEqual(len(graph.check_deps_are_used(plugins, refs)), 1)

    def test_malformed_shared_schema_cannot_become_a_used_edge(self):
        self.kernel("coordinator", dependencies=["protocol"])
        self.kernel("protocol")
        self.sidecar("coordinator", '[contract]\nshared_schemas = ["protocol/../result.toml"]\n')
        with self.assertRaisesRegex(ValueError, "invalid shared schema"):
            self.references()

    def test_static_phase_provider_cannot_be_an_optional_external_dependency(self):
        self.kernel("coordinator", optional=["reviewer@external"])
        self.sidecar("coordinator", '[[phases]]\nrole = "reviewer/audit"\n')
        plugins, refs = self.references()
        self.assertTrue(any("phase role provider 'reviewer' must be a required dependency" in p
                            for p in graph.check_runtime_refs(plugins, refs)))


if __name__ == "__main__":
    unittest.main()
