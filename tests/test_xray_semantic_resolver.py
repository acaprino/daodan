"""Conservative source-bound static references, independent of extraction syntax."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import shutil
import sys
import subprocess
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))
import snapshot
import usage_finder
try:
    import semantic_index
except ModuleNotFoundError:
    semantic_index = None


def payload(*, declarations=(), imports=(), exports=(), references=(), scopes=None):
    return {"version": 1, "backend": "stdlib-ast", "status": "ast", "notes": [],
            "scopes": scopes or [{"id": "module", "parent": None, "kind": "module"}],
            "declarations": list(declarations), "imports": list(imports),
            "exports": list(exports), "references": list(references)}


def declaration(name="save", kind="function", scope="module", identity="function@1:0", span=None, **extra):
    return {"id": identity, "name": name, "kind": kind, "scope": scope,
            "span": span or [1, 0, 2, 8], **extra}


def reference(parts, line=1, column=0, end=None, scope="module", caller=None, **extra):
    return {"scope": scope, "parts": parts, "kind": "call", "span": [line, column, line, end if end is not None else column + len(".".join(parts))],
            "caller": caller, **extra}


class SemanticResolverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.files = {}
        self.graph = {}

    def add(self, path, text, semantic=None, language="python"):
        source = self.root / path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(text.encode("utf-8"))
        imports = semantic.get("imports", []) if semantic else []
        entry = {"status": "parsed", "language": language,
                 "raw_hash": hashlib.sha256(source.read_bytes()).hexdigest(),
                 "imports": list(dict.fromkeys(i["module"] for i in imports)),
                 "import_bindings": [{"module": i["module"], "names": [i["imported"]], "from": i["mode"] != "namespace"} for i in imports]}
        if semantic is not None:
            entry["semantic"] = semantic
        self.files[path] = entry
        return source

    def manifest(self):
        return {"schema": snapshot.SCHEMA, "root": self.root.as_posix(), "target": ".",
                "parser_fingerprint": snapshot.parser_fingerprint(), "files": copy.deepcopy(self.files)}

    def index(self, manifest=None, **kwargs):
        self.assertIsNotNone(semantic_index, "portable source-bound semantic index is missing")
        return semantic_index.build_semantic_index(manifest or self.manifest(), import_graph=self.graph, **kwargs)

    def core(self, name="core.py"):
        return self.add(name, "def save():\n    pass\n", payload(
            declarations=[declaration()], exports=[{"exported": "save", "local": "save"}]))

    def alias_fixture(self):
        source = self.core()
        self.core("other.py")
        self.add("main.py", "from core import save as persist\nfrom other import save\npersist(); persist(); save()\n", payload(
            imports=[{"scope": "module", "local": "persist", "module": "core", "imported": "save", "mode": "named", "span": [1, 0, 1, 1]},
                     {"scope": "module", "local": "save", "module": "other", "imported": "save", "mode": "named", "span": [2, 0, 2, 1]}],
            references=[reference(["persist"], 3, 0), reference(["persist"], 3, 11), reference(["save"], 3, 22)]))
        self.graph = {"main.py": {"core": ["core.py"], "other": ["other.py"]}}
        return source

    def test_named_aliases_resolve_all_calls_without_original_spelling(self):
        self.alias_fixture()
        index = self.index()
        self.assertEqual([r["target_id"] for r in index["references"]],
                         ["core.py::function@1:0", "core.py::function@1:0", "other.py::function@1:0"])
        self.assertEqual([r["span"] for r in index["references"]], [[3, 0, 3, 7], [3, 11, 3, 18], [3, 22, 3, 26]])

    def test_namespace_and_default_imports_link_only_direct_members(self):
        self.core()
        self.add("main.py", "import core as ns\nns.save()\nns.factory.save()\n", payload(
            imports=[{"scope": "module", "local": "ns", "module": "core", "imported": "*", "mode": "namespace", "span": [1, 0, 1, 1]}],
            references=[reference(["ns", "save"], 2), reference(["ns", "factory", "save"], 3)]))
        self.graph = {"main.py": {"core": ["core.py"]}}
        refs = self.index()["references"]
        self.assertEqual(refs[0]["target_id"], "core.py::function@1:0")
        self.assertIsNone(refs[1]["target_id"])
        self.assertEqual(refs[1]["resolution"], "unresolved")
        self.add("core.js", "function save() {}\nexport default save;\n", payload(
            declarations=[declaration(span=[1, 0, 1, 18])], exports=[{"exported": "default", "local": "save"}]), language="javascript")
        self.add("main.js", "import Alias from './core.js';\nAlias();\n", payload(
            imports=[{"scope": "module", "local": "Alias", "module": "./core.js", "imported": "default", "mode": "default", "span": [1, 0, 1, 1]}],
            references=[reference(["Alias"], 2)]), language="javascript")
        self.graph["main.js"] = {"./core.js": ["core.js"]}
        self.assertEqual([r["target_id"] for r in self.index()["references"] if r["file"] == "main.js"], ["core.js::function@1:0"])

    def test_parameter_shadowing_and_repeated_bindings_block_false_links(self):
        self.core()
        self.add("main.py", "from core import save\ndef run(save):\n    save()\nsave = 1\nsave()\n", payload(
            scopes=[{"id": "module", "parent": None, "kind": "module"}, {"id": "run", "parent": "module", "kind": "function"}],
            declarations=[declaration("run", identity="function@2:0", span=[2, 0, 3, 10]),
                          declaration("save", "parameter", "run", "parameter@2:8", [2, 8, 2, 12]),
                          declaration("save", "binding", identity="binding@4:0", span=[4, 0, 4, 4])],
            imports=[{"scope": "module", "local": "save", "module": "core", "imported": "save", "mode": "named", "span": [1, 0, 1, 1]}],
            references=[reference(["save"], 3, 4, scope="run", caller="function@2:0"), reference(["save"], 5)]))
        self.graph = {"main.py": {"core": ["core.py"]}}
        refs = self.index()["references"]
        self.assertEqual([r["target_id"] for r in refs], [None, None])
        self.assertTrue(refs[0]["known_unrelated"])
        self.assertEqual(refs[0]["caller"], "main.py::function@2:0")
        self.assertEqual(refs[1]["reason"], "ambiguous-binding")

    def test_unknown_scope_dynamic_receivers_and_type_only_imports_stay_unresolved(self):
        self.core()
        self.add("main.py", "save()\nobj.save()\ngetattr(obj, 'save')()\n", payload(
            scopes=[{"id": "module", "parent": None, "kind": "module", "unresolved": True, "reason": "dynamic-scope"}],
            imports=[{"scope": "module", "local": "save", "module": "core", "imported": "save", "mode": "named", "span": [1, 0, 1, 1]}],
            references=[reference(["save"], 1), reference(["obj", "save"], 2), reference([], 3, end=20, reason="dynamic-callee")]))
        self.graph = {"main.py": {"core": ["core.py"]}}
        refs = self.index()["references"]
        self.assertTrue(all(r["target_id"] is None for r in refs))
        self.assertIn("dynamic", refs[2]["reason"])
        self.files["main.py"]["semantic"]["scopes"][0].pop("unresolved")
        self.files["main.py"]["semantic"]["imports"][0]["type_only"] = True
        self.assertEqual(self.index()["references"][0]["reason"], "type-only-import")

    def test_repeated_declarations_and_reexport_chains_are_not_guessed(self):
        self.core()
        self.files["core.py"]["semantic"]["declarations"].append(declaration(identity="function@1:0#2"))
        self.add("main.py", "save()\n", payload(
            imports=[{"scope": "module", "local": "save", "module": "core", "imported": "save", "mode": "named", "span": [1, 0, 1, 1]}],
            references=[reference(["save"])]))
        self.graph = {"main.py": {"core": ["core.py"]}}
        self.assertIsNone(self.index()["references"][0]["target_id"])
        self.files["core.py"]["semantic"]["declarations"].pop()
        self.files["core.py"]["semantic"]["exports"][0]["module"] = "elsewhere"
        self.files["core.py"]["language"] = "javascript"
        self.assertEqual(self.index()["references"][0]["reason"], "reexport-unsupported")

    def test_source_observations_avoid_second_read_and_stale_bytes_disable_semantics(self):
        self.alias_fixture()
        manifest = self.manifest()
        observations = {rel: (self.root / rel).read_bytes() for rel in self.files}
        real_read = Path.read_bytes
        def forbid_source_read(path):
            if path.parent == self.root:
                self.fail(f"observed source reread: {path}")
            return real_read(path)
        with mock.patch.object(Path, "read_bytes", forbid_source_read):
            index = self.index(manifest, source_observations=observations)
        self.assertEqual(len(index["references"]), 3)
        observations["core.py"] = b"def changed():\n    pass\n"
        stale = self.index(manifest, source_observations=observations)
        self.assertEqual(stale["coverage"]["core.py"]["status"], "stale")
        self.assertTrue(all(r["target_id"] is None for r in stale["references"] if r["file"] == "main.py" and r["parts"] == ["persist"]))

    def test_manifest_without_observations_reads_each_permitted_source_once(self):
        self.alias_fixture()
        manifest = self.manifest()
        reads = []
        real_read = Path.read_bytes
        def observe(path):
            if path.parent == self.root:
                reads.append(path.name)
            return real_read(path)
        with mock.patch.object(Path, "read_bytes", observe):
            index = self.index(manifest)
        self.assertEqual(sorted(reads), ["core.py", "main.py", "other.py"])
        self.assertIn("persist(); persist(); save()", index["_source_text"]["main.py"])

    def test_reused_index_rejects_changed_manifest_fingerprint_or_payload(self):
        source = self.alias_fixture()
        manifest = self.manifest()
        observations = {rel: (self.root / rel).read_bytes() for rel in self.files}
        index = self.index(manifest, source_observations=observations)
        old_fingerprint = copy.deepcopy(manifest)
        old_fingerprint["parser_fingerprint"] = "old-helper"
        result = usage_finder.find_all_usages_batch(
            ["save"], source, self.root, manifest=old_fingerprint,
            source_observations=observations, semantic_index=index)["save"]
        self.assertEqual(result.resolved_count, 0)
        self.assertEqual(result.coverage["main.py"]["status"], "fingerprint-mismatch")
        manifest["files"]["main.py"]["semantic"]["references"][0]["scope"] = "missing"
        result = usage_finder.find_all_usages_batch(
            ["save"], source, self.root, manifest=manifest,
            source_observations=observations, semantic_index=index)["save"]
        self.assertEqual(result.resolved_count, 0)
        self.assertEqual(result.coverage["main.py"]["status"], "malformed")

    def test_reused_index_with_partial_observations_rechecks_unobserved_source(self):
        source = self.alias_fixture()
        manifest = self.manifest()
        observations = {rel: (self.root / rel).read_bytes() for rel in self.files}
        index = self.index(manifest, source_observations=observations)
        (self.root / "main.py").write_text("from core import save\nsave = unknown\nsave()\n", encoding="utf-8")
        result = usage_finder.find_all_usages_batch(
            ["save"], source, self.root, manifest=manifest,
            source_observations={"core.py": observations["core.py"]}, semantic_index=index)["save"]
        self.assertEqual(result.resolved_count, 0)
        self.assertEqual(result.coverage["main.py"]["status"], "stale")
        self.assertGreater(result.lexical_candidate_count, 0)

    def test_reused_index_rechecks_the_current_git_perimeter(self):
        if not shutil.which("git"):
            self.skipTest("git unavailable")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        source = self.alias_fixture()
        manifest = self.manifest()
        observations = {rel: (self.root / rel).read_bytes() for rel in self.files}
        index = self.index(manifest, source_observations=observations)
        (self.root / ".gitignore").write_text("main.py\n", encoding="utf-8")
        result = usage_finder.find_all_usages_batch(
            ["save"], source, self.root, manifest=manifest,
            source_observations=observations, semantic_index=index)["save"]
        self.assertEqual(result.usages, [])
        self.assertEqual(result.coverage["main.py"]["status"], "excluded")

    def test_fingerprint_malformed_scope_and_bad_span_degrade_explicitly(self):
        self.core()
        manifest = self.manifest()
        manifest["parser_fingerprint"] = "old-helper"
        index = self.index(manifest)
        self.assertEqual(index["declarations"], {})
        self.assertEqual(index["coverage"]["core.py"]["status"], "fingerprint-mismatch")
        malformed = self.manifest()
        malformed["files"]["core.py"]["semantic"]["scopes"][0]["parent"] = "module"
        self.assertEqual(self.index(malformed)["coverage"]["core.py"]["status"], "malformed")
        malformed = self.manifest()
        malformed["files"]["core.py"]["semantic"]["declarations"][0]["span"] = [200, 0, 201, 8]
        self.assertEqual(self.index(malformed)["coverage"]["core.py"]["status"], "malformed")

    def test_ignored_hidden_and_outside_paths_are_never_read_or_linked(self):
        self.core()
        hidden = self.add(".records/hidden.py", "save()\n", payload(references=[reference(["save"])]))
        manifest = self.manifest()
        manifest["files"]["../outside.py"] = copy.deepcopy(self.files["core.py"])
        real_read = Path.read_bytes
        def prohibit(path):
            if path == hidden or path.name == "outside.py":
                self.fail(f"excluded source was read: {path}")
            return real_read(path)
        with mock.patch.object(Path, "read_bytes", prohibit):
            index = self.index(manifest)
        self.assertEqual(index["coverage"][".records/hidden.py"]["status"], "excluded")
        self.assertEqual(index["coverage"]["../outside.py"]["status"], "excluded")

    def test_usage_aliases_are_separate_calls_and_unrelated_module_is_excluded(self):
        source = self.alias_fixture()
        manifest = self.manifest()
        index = self.index(manifest)
        result = usage_finder.find_all_usages_batch(["save"], source, self.root, manifest=manifest, semantic_index=index)["save"]
        calls = [u for u in result.usages if u.usage_type == "call"]
        imports = [u for u in result.usages if u.usage_type == "import"]
        self.assertEqual([u.line_content for u in calls], ["persist(); persist(); save()", "persist(); persist(); save()"])
        self.assertEqual([u.column for u in calls], [0, 11])
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].line_number, 1)
        self.assertEqual(imports[0].reason, "import-binding-not-call")
        self.assertIsNone(imports[0].target_id)
        self.assertEqual(result.resolved_count, 2)
        self.assertEqual(result.ast_candidate_count, 1)
        self.assertEqual(result.lexical_candidate_count, 0)
        self.assertTrue(all(u.precision == "resolved-static" for u in calls))
        self.assertEqual(imports[0].precision, "ast-candidate")

    def test_native_import_rows_are_ast_candidates_without_additional_source_reads(self):
        source = self.add("core.py", "def save():\n    pass\n")
        self.add("other.py", "def save():\n    pass\n")
        self.add("main.py", "from core import save as persist\nfrom other import save\n# from core import save\ntext = 'from core import save'\npersist()\n")
        observations = {}
        manifest = snapshot.build_manifest(self.root, source_observations=observations)
        index = semantic_index.build_semantic_index(manifest, source_observations=observations)
        original_read = Path.read_bytes

        def forbid_source_read(path):
            if path.is_relative_to(self.root):
                self.fail(f"import reporting reread source: {path}")
            return original_read(path)

        with mock.patch.object(Path, "read_bytes", forbid_source_read):
            result = usage_finder.find_all_usages_batch(
                ["save"], source, self.root, manifest=manifest,
                source_observations=observations, semantic_index=index)["save"]
        self.assertEqual([(u.usage_type, u.line_number) for u in result.usages], [("import", 1), ("call", 5)])
        self.assertEqual((result.resolved_count, result.ast_candidate_count, result.lexical_candidate_count), (1, 1, 0))
        imported = result.usages[0]
        self.assertEqual(imported.precision, "ast-candidate")
        self.assertEqual(imported.reason, "import-binding-not-call")
        self.assertEqual(imported.span, [1, 17, 1, 32])
        self.assertIsNone(imported.target_id)

    def test_native_js_import_rows_follow_export_alias_default_and_namespace(self):
        from languages._treesitter import get_parser
        if get_parser("javascript") is None:
            self.skipTest("native JavaScript grammar unavailable")
        source = self.add("core.js", "function save() {}\nexport {save as PublicSave};\nexport default save;\nexport function other() {}\n", language="javascript")
        self.add("other.js", "export function PublicSave() {}\n", language="javascript")
        self.add("main.js", "import {PublicSave as local} from './core.js';\nimport defaultAlias from './core.js';\nimport * as ns from './core.js';\nimport {other} from './core.js';\nimport {PublicSave} from './other.js';\n// import {PublicSave} from './core.js';\nconst text = \"import {PublicSave} from './core.js';\";\n", language="javascript")
        result = usage_finder.find_all_usages_batch(["save"], source, self.root)["save"]
        self.assertEqual([u.line_number for u in result.usages], [1, 2, 3])
        self.assertEqual((result.resolved_count, result.ast_candidate_count, result.lexical_candidate_count), (0, 3, 0))
        self.assertTrue(all(u.usage_type == "import" and u.reason == "import-binding-not-call" for u in result.usages))
        self.assertTrue(all(u.target_id is None for u in result.usages))

    def test_lexical_import_fallback_is_not_duplicated_as_an_ast_candidate(self):
        source = self.core()
        self.add("main.py", "from core import save\nsave()\n")
        manifest = self.manifest()
        result = usage_finder.find_all_usages_batch(["save"], source, self.root, manifest=manifest)["save"]
        self.assertEqual([(u.usage_type, u.line_number) for u in result.usages], [("import", 1), ("call", 2)])
        self.assertEqual((result.resolved_count, result.ast_candidate_count, result.lexical_candidate_count), (0, 0, 2))

    def test_usage_fallback_remains_lexical_and_native_literals_do_not_become_usages(self):
        source = self.core()
        self.add("main.py", "# save()\ntext = 'save()'\n", payload())
        self.add("Legacy.java", "save();\n", language="java")
        manifest = self.manifest()
        index = self.index(manifest)
        result = usage_finder.find_all_usages_batch(["save"], source, self.root, manifest=manifest, semantic_index=index)["save"]
        self.assertEqual([Path(u.file_path).name for u in result.usages], ["Legacy.java"])
        self.assertEqual(result.resolved_count, 0)
        self.assertEqual(result.lexical_candidate_count, 1)
        self.assertEqual(result.usages[0].precision, "lexical-candidate")

    def test_reassigned_alias_remains_an_unresolved_candidate_for_original_export(self):
        source = self.core()
        self.add("main.py", "from core import save as persist\npersist = unknown\npersist()\n", payload(
            declarations=[declaration("persist", "binding", identity="binding@2:0", span=[2, 0, 2, 7])],
            imports=[{"scope": "module", "local": "persist", "module": "core", "imported": "save", "mode": "named", "span": [1, 0, 1, 1]}],
            references=[reference(["persist"], 3)]))
        self.graph = {"main.py": {"core": ["core.py"]}}
        manifest = self.manifest()
        result = usage_finder.find_all_usages_batch(["save"], source, self.root, manifest=manifest, semantic_index=self.index(manifest))["save"]
        self.assertEqual(result.resolved_count, 0)
        self.assertEqual(result.ast_candidate_count, 2)
        self.assertEqual([u.reason for u in result.usages if u.usage_type == "call"], ["ambiguous-binding"])
        self.assertEqual([u.reason for u in result.usages if u.usage_type == "import"], ["import-binding-not-call"])

    def test_native_python_aliases_ignore_literals_shadowing_and_unrelated_exports(self):
        source = self.add("core.py", "def save():\n    pass\n")
        self.add("other.py", "def save():\n    pass\n")
        self.add("main.py", "from core import save as persist\nfrom other import save\n# persist() save()\ntext = 'persist() save()'\npersist(); persist(); save()\ntext = f'{persist()}'\ndef run(persist):\n    persist()\n")
        result = usage_finder.find_all_usages_batch(["save"], source, self.root)["save"]
        self.assertEqual(result.resolved_count, 3)
        self.assertEqual(result.ast_candidate_count, 1)
        self.assertEqual(result.lexical_candidate_count, 0)
        self.assertEqual([u.line_number for u in result.usages if u.usage_type == "call"], [5, 5, 6])
        self.assertEqual([u.line_number for u in result.usages if u.usage_type == "import"], [1])

    def test_native_js_default_named_and_namespace_aliases_use_static_exports(self):
        from languages._treesitter import get_parser
        if get_parser("javascript") is None:
            self.skipTest("native JavaScript grammar unavailable")
        source = self.add("core.js", "export default function save() {}\nexport function other() {}\n", language="javascript")
        self.add("main.js", "import persist, {other as local} from './core.js';\nimport * as ns from './core.js';\n// save persist()\nconst text = 'save persist()';\npersist(); ns.default(); local();\n", language="javascript")
        result = usage_finder.find_all_usages_batch(["save", "other"], source, self.root)
        self.assertEqual(result["save"].resolved_count, 2)
        self.assertEqual(result["other"].resolved_count, 1)
        self.assertEqual(result["save"].lexical_candidate_count, 0)
        self.assertEqual([u.line_number for u in result["save"].usages if u.usage_type == "import"], [1, 2])
        self.assertEqual([u.line_number for u in result["other"].usages if u.usage_type == "import"], [1, 2])

    def test_malformed_reference_keys_degrade_instead_of_crashing(self):
        self.core()
        self.files["core.py"]["semantic"]["references"] = [reference(["save"])]
        for key, value in [("scope", {}), ("caller", []), ("scope", None)]:
            with self.subTest(key=key, value=value):
                manifest = self.manifest()
                manifest["files"]["core.py"]["semantic"]["references"][0][key] = value
                index = self.index(manifest)
                self.assertEqual(index["coverage"]["core.py"]["status"], "malformed")
                self.assertEqual(index["references"], [])

    def test_imported_constant_remains_a_candidate_with_unsupported_target_reason(self):
        source = self.add("core.py", "VALUE = 42\n")
        self.add("main.py", "from core import VALUE\nprint(VALUE)\n")
        result = usage_finder.find_all_usages_batch(["VALUE"], source, self.root)["VALUE"]
        self.assertEqual(result.resolved_count, 0)
        self.assertEqual(result.ast_candidate_count, 2)
        references = [u for u in result.usages if u.usage_type == "reference"]
        self.assertEqual([(u.line_number, u.reason) for u in references], [(2, "unsupported-target-kind")])
        self.assertEqual([u.reason for u in result.usages if u.usage_type == "import"], ["import-binding-not-call"])

    def test_utf8_reference_columns_are_byte_boundaries(self):
        source = self.add("core.py", "def save():\n    pass\n")
        self.add("main.py", "from core import save as persist\nπ = 'é'; persist()\n")
        result = usage_finder.find_all_usages_batch(["save"], source, self.root)["save"]
        self.assertEqual(result.resolved_count, 1)
        self.assertEqual([u.span for u in result.usages if u.usage_type == "call"], [[2, 11, 2, 18]])
        self.assertEqual([u.line_number for u in result.usages if u.usage_type == "import"], [1])
        self.add("core.py", "π = 1\ndef save():\n    pass\n", payload(
            declarations=[declaration(identity="function@2:0", span=[2, 0, 3, 8])],
            references=[reference(["π"], 1, 1, end=2)]))
        self.assertEqual(self.index()["coverage"]["core.py"]["status"], "malformed")

    def test_cli_reports_candidate_counts_and_source_spans(self):
        source = self.add("core.py", "VALUE = 42\n")
        self.add("main.py", "from core import VALUE\nprint(VALUE)\n")
        completed = subprocess.run([sys.executable, "-B", str(SCRIPTS / "usage_finder.py"), "VALUE", str(source)],
                                   cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        import json
        result = json.loads(completed.stdout)
        self.assertEqual((result.get("resolved_count"), result.get("ast_candidate_count"), result.get("lexical_candidate_count")), (0, 2, 0))
        self.assertTrue(all(u["precision"] == "ast-candidate" for u in result["usages"]))
        self.assertEqual([u["span"] for u in result["usages"] if u["type"] == "reference"], [[2, 6, 2, 11]])
        self.assertEqual([u["reason"] for u in result["usages"] if u["type"] == "import"], ["import-binding-not-call"])
        self.assertIn("includes candidates", result["usage_count_meaning"])

    def test_python_instance_receiver_and_module_attribute_resolve_to_project_declarations(self):
        """The resolution rule the resolver measurement made a prerequisite.

        A method inherited from a project base class and a callable reached as an
        attribute of a module bound by `from . import worker` were 146 of the
        positions an engine resolved and the symbol table did not; 40 of 40 sampled
        records read true at both ends (evals/codebase-map/python-parser/RESULTS.md,
        section 6). Both resolve lexically now, and neither invents an edge where
        the target is not a project callable.
        """
        if semantic_index is None:
            self.skipTest("semantic index unavailable")
        self.add("pkg/base.py", "class LoggingMixin:\n    def info(self, msg):\n        return msg\n")
        self.add("pkg/attr.py", "class Helper:\n    def run(self):\n        return 1\n")
        self.add(
            "pkg/service.py",
            "from .base import LoggingMixin\n"          # 1
            "\n"                                        # 2
            "class Service(LoggingMixin):\n"            # 3
            "    def __init__(self):\n"                 # 4
            "        self.callback = None\n"            # 5
            "\n"                                        # 6
            "    def run(self):\n"                      # 7
            "        return self.info('x')\n"           # 8
            "\n"                                        # 9
            "    def own(self):\n"                      # 10
            "        return self.run()\n"               # 11
            "\n"                                        # 12
            "    def missing(self):\n"                  # 13
            "        return self.nope()\n"              # 14
            "\n"                                        # 15
            "    def attribute(self):\n"                # 16
            "        return self.callback()\n"          # 17
            "\n"                                        # 18
            "class Deep(Service):\n"                   # 19
            "    def go(self):\n"                       # 20
            "        return self.info('y')\n"           # 21
            "\n"                                        # 22
            "def helper(service, other):\n"             # 23
            "    return other.run()\n"                  # 24
            "\n"                                        # 25
            "class Mutating:\n"                        # 26
            "    def write(self):\n"                    # 27
            "        self.callback = None\n"            # 28
            "        return self.callback()\n",         # 29
        )
        self.add("pkg/main.py",
                 "from . import attr\n"
                 "\n"
                 "def go():\n"
                 "    return attr.Helper().run()\n")
        manifest = snapshot.build_manifest(self.root)
        index = semantic_index.build_semantic_index(manifest)
        calls = {(r["file"], tuple(r["parts"]), r["span"][0]): r
                 for r in index["references"] if r["kind"] == "call"}

        def call(parts, line, file="pkg/service.py"):
            record = calls[(file, tuple(parts), line)]
            return record["resolution"], record["reason"], record["target_id"]

        # Inherited from a project base class in another file.
        self.assertEqual(call(["self", "info"], 8),
                         ("resolved", "inherited-project-method", "pkg/base.py::function@2:4"))
        # The same method through two levels of MRO: Deep -> Service -> LoggingMixin.
        self.assertEqual(call(["self", "info"], 21),
                         ("resolved", "inherited-project-method", "pkg/base.py::function@2:4"))
        # Declared on the class itself, so not an inheritance claim.
        self.assertEqual(call(["self", "run"], 11),
                         ("resolved", "instance-method", "pkg/service.py::function@7:4"))
        # An attribute of a module bound by `from . import attr`.
        self.assertEqual(call(["attr", "Helper"], 4, "pkg/main.py"),
                         ("resolved", "module-attribute", "pkg/attr.py::class@1:0"))
        # No project base declares it: unresolved, not guessed.
        self.assertEqual(call(["self", "nope"], 14)[:2], ("unresolved", "unknown-receiver"))
        # An instance attribute is a binding, not a symbol: it has no arrival node.
        self.assertEqual(call(["self", "callback"], 17), ("unresolved", "unknown-receiver", None))
        # Only the first parameter is the instance; a second one is not a receiver.
        self.assertEqual(call(["other", "run"], 24)[:2], ("unresolved", "unknown-receiver"))
        # An attribute write in the same body invalidates the receiver binding
        # before any MRO walk, so the reference never becomes an edge either.
        self.assertEqual(call(["self", "callback"], 29), ("unresolved", "ambiguous-binding", None))

    def python_calls_with_storage_parity(self):
        """Exercise both graph owners over real source, not scripted lookup answers."""
        from snapshot_store import _unpack, open_snapshot
        index = semantic_index.build_semantic_index(snapshot.build_manifest(self.root))
        memory = {record["id"]: record for record in index["references"] if record["kind"] == "call"}
        directory = self.root / ".test-snapshots"
        directory.mkdir(exist_ok=True)
        path = directory / "manifest.sqlite"
        snapshot.write_snapshot(self.root, path)
        with open_snapshot(path) as store:
            persisted = {row[0]: _unpack(row[1]) for row in store.connection.execute(
                "SELECT id,payload FROM sem_references WHERE kind='call'")}
        self.assertEqual(memory, persisted)
        return list(memory.values())

    def test_python_multiple_inheritance_uses_c3_in_both_graph_owners(self):
        self.add("main.py", "class A:\n"
                 "    def target(self): return 'A'\n"
                 "class B(A): pass\n"
                 "class C:\n"
                 "    def target(self): return 'C'\n"
                 "class D(B, C):\n"
                 "    def run(self): return self.target()\n")
        calls = self.python_calls_with_storage_parity()
        self.assertEqual([(r["resolution"], r["target_id"], r["reason"]) for r in calls],
                         [("resolved", "main.py::function@2:4", "inherited-project-method")])

    def test_python_project_namespace_bases_and_builtin_object_resolve(self):
        self.add("pkg/base.py", "class Base(object):\n    def target(self): return 1\n")
        self.add("pkg/use.py", "import pkg.base as namespace\n"
                 "from . import base\n"
                 "class Direct(namespace.Base):\n"
                 "    def run(self): return self.target()\n"
                 "class Relative(base.Base):\n"
                 "    def run(self): return self.target()\n")
        calls = self.python_calls_with_storage_parity()
        self.assertEqual([(r["resolution"], r["target_id"]) for r in calls],
                         [("resolved", "pkg/base.py::function@2:4")] * 2)

    def test_python_inconsistent_or_cyclic_hierarchies_have_no_partial_mro(self):
        sources = (
            "class Root:\n    def target(self): return 1\n"
            "class X(Root): pass\nclass Y(Root): pass\n"
            "class A(X, Y): pass\nclass B(Y, X): pass\n"
            "class Child(A, B):\n    def run(self): return self.target()\n",
            "class A(B):\n    def target(self): return 1\n"
            "class B(A): pass\n"
            "class Child(A):\n    def run(self): return self.target()\n",
        )
        for source in sources:
            with self.subTest(source=source):
                self.add("main.py", source)
                calls = self.python_calls_with_storage_parity()
                self.assertEqual([(r["resolution"], r["target_id"]) for r in calls], [("unresolved", None)])

    def test_python_partial_hierarchies_never_skip_an_unknown_base(self):
        for base in ("Unknown", "factory()", "Generic[int]", "namespace.Unknown"):
            with self.subTest(base=base):
                self.add("main.py", "class Base:\n"
                         "    def target(self): return 1\n"
                         f"class Child({base}, Base):\n"
                         "    def run(self): return self.target()\n")
                calls = self.python_calls_with_storage_parity()
                target = next(r for r in calls if r["parts"] == ["self", "target"])
                self.assertEqual((target["resolution"], target["target_id"]), ("unresolved", None))

    def test_python_member_shadows_and_dynamic_receivers_remain_unresolved(self):
        cases = {
            "class assignment": "    target = None\n    def run(self): return self.target()\n",
            "method rebound": "    def target(self): return 2\n    target = None\n"
                              "    def run(self): return self.target()\n",
            "method redefined": "    def target(self): return 2\n    def target(self): return 3\n"
                                "    def run(self): return self.target()\n",
            "instance assignment in another method":
                "    def __init__(self): self.target = lambda: 2\n"
                "    def run(self): return self.target()\n",
            "static method argument": "    @staticmethod\n    def run(value): return value.target()\n",
            "setattr in another method":
                "    def __init__(self): setattr(self, 'target', lambda: 2)\n"
                "    def run(self): return self.target()\n",
            "setattr of unknown name":
                "    def replace(self, name): setattr(self, name, lambda: 2)\n"
                "    def run(self): return self.target()\n",
            "custom attribute lookup":
                "    def __getattribute__(self, name): return lambda: 2\n"
                "    def run(self): return self.target()\n",
            "decorated receiver": "    @arbitrary\n    def run(self): return self.target()\n",
            "decorated target": "    @property\n    def target(self): return lambda: 2\n"
                                "    def run(self): return self.target()\n",
            "keyword only argument": "    def run(*, value): return value.target()\n",
            "conditional member": "    if False:\n        def target(self): return 2\n"
                                  "    def run(self): return self.target()\n",
        }
        for label, body in cases.items():
            with self.subTest(case=label):
                self.add("main.py", "class Base:\n    def target(self): return 1\nclass Child(Base):\n" + body)
                calls = self.python_calls_with_storage_parity()
                target = next(r for r in calls if r["parts"] and r["parts"][-1] == "target")
                self.assertEqual((target["resolution"], target["target_id"]), ("unresolved", None))

    def test_python_dynamic_class_construction_prevents_member_claims(self):
        for header in ("@arbitrary\nclass Child(Base):", "class Child(Base, metaclass=type):"):
            with self.subTest(header=header):
                self.add("main.py", "class Base:\n    def target(self): return 1\n" + header
                         + "\n    def run(self): return self.target()\n")
                calls = self.python_calls_with_storage_parity()
                target = next(r for r in calls if r["parts"] == ["self", "target"])
                self.assertEqual((target["resolution"], target["target_id"]), ("unresolved", None))

    def test_python_existing_package_attribute_does_not_become_a_submodule(self):
        self.add("pkg/__init__.py", "class base:\n    class Base:\n        def target(self): return 0\n")
        self.add("pkg/base.py", "class Base:\n    def target(self): return 1\n")
        self.add("pkg/use.py", "from . import base\nclass Child(base.Base):\n"
                 "    def run(self): return self.target()\n")
        calls = self.python_calls_with_storage_parity()
        self.assertEqual([(r["resolution"], r["target_id"]) for r in calls], [("unresolved", None)])

    def test_python_imported_class_with_module_name_does_not_become_a_module(self):
        self.add("base.py", "class base:\n    pass\n\ndef target(): return 1\n")
        self.add("use.py", "from base import base\n\ndef run(): return base.target()\n")
        calls = self.python_calls_with_storage_parity()
        self.assertEqual([(r["resolution"], r["target_id"]) for r in calls], [("unresolved", None)])

    def test_native_java_semantics_resolve_same_class_and_cross_file_calls_conservatively(self):
        from languages._treesitter import get_parser
        if get_parser("java") is None:
            self.skipTest("native Java grammar unavailable")
        core = self.add(
            "src/com/acme/Core.java",
            "package com.acme;\npublic class Core<T> {\n    public void run(int x) { helper(x); this.helper(x); overloaded(x); }\n    void helper(int z) {}\n    public static void staticHelper(int z) {}\n    void overloaded(int a) {}\n    void overloaded(String b) {}\n    void shadowed(int helper) { helper(); }\n}\n",
            language="java",
        )
        other = self.add("src/com/acme/Other.java", "package com.acme;\npublic class Other {}\n", language="java")
        self.add(
            "src/com/acme/Main.java",
            "package com.acme;\nimport com.acme.Core;\nimport com.acme.Other;\npublic class Main {\n    public void start() {\n        Core<String> c = new Core<String>();\n        c.run(1);\n        Core.staticHelper(2);\n        new Core<String>().run(3);\n        new Other();\n    }\n}\n",
            language="java",
        )
        manifest = snapshot.build_manifest(self.root)
        index = semantic_index.build_semantic_index(manifest)
        self.assertEqual(index["coverage"]["src/com/acme/Core.java"]["status"], "ast")
        core_calls = [r for r in index["references"] if r["file"] == "src/com/acme/Core.java" and r["kind"] == "call"]
        by_parts = {tuple(r["parts"]) + (r["span"][0],): r for r in core_calls}
        self.assertEqual(by_parts[("helper", 3)]["resolution"], "resolved")
        self.assertEqual(by_parts[("helper", 3)]["reason"], "unique-lexical-binding")
        self.assertEqual(by_parts[("this", "helper", 3)]["resolution"], "unresolved")
        self.assertEqual(by_parts[("overloaded", 3)]["resolution"], "unresolved")
        self.assertEqual(by_parts[("overloaded", 3)]["reason"], "ambiguous-binding")
        self.assertTrue(by_parts[("helper", 8)]["known_unrelated"])
        main_calls = [r for r in index["references"] if r["file"] == "src/com/acme/Main.java" and r["kind"] == "call"]
        self.assertEqual([(r["parts"], r["resolution"], r["reason"]) for r in main_calls], [
            (["Core"], "resolved", "direct-internal-import"),
            (["c", "run"], "unresolved", "unknown-receiver"),
            (["Core", "staticHelper"], "unresolved", "unknown-receiver-or-import-form"),
            (["(expr)", "run"], "unresolved", "dynamic-callee"),
            (["Core"], "resolved", "direct-internal-import"),
            (["Other"], "resolved", "direct-internal-import"),
        ])
        for m_arg in (None, manifest):
            usages = usage_finder.find_all_usages_batch(["Core", "staticHelper", "run"], core, self.root, manifest=m_arg)
            self.assertEqual(usages["Core"].resolved_count, 2)
            self.assertEqual(usages["Core"].importing_modules, ["src/com/acme/Main.java"])
            self.assertEqual(usages["staticHelper"].ast_candidate_count, 1)
            self.assertEqual(usages["run"].ast_candidate_count, 2)
            other_usages = usage_finder.find_all_usages_batch(["Core"], other, self.root, manifest=m_arg)
            self.assertEqual(other_usages["Core"].importing_modules, [])

    def test_native_rust_semantics_resolve_functions_and_crate_imports_conservatively(self):
        import semantic_store
        from snapshot_store import open_snapshot
        from languages._treesitter import get_parser
        if get_parser("rust") is None:
            self.skipTest("native Rust grammar unavailable")
        core = self.add(
            "src/core.rs",
            "pub(crate) fn save<T>(x: T) { helper(1); }\nfn helper(z: i32) {}\npub struct Store { pub helper: i32 }\nimpl Store { pub fn method(&self) { helper(1); } }\npub mod inner { pub fn sub_fn() {} }\n",
            language="rust",
        )
        self.add("src/other.rs", "pub fn a() {}\npub fn b() {}\n", language="rust")
        self.add("src/log.rs", "pub fn info() {}\n", language="rust")
        self.add(
            "src/sub/child.rs",
            "use super::core::save;\npub fn relay() { save(1); }\n",
            language="rust",
        )
        self.add(
            "src/main.rs",
            "use crate::core::save as persist;\nuse crate::other::{a, b as b2};\nuse log::info;\npub fn log() {}\npub fn run(opt: Option<i32>) {\n    if let Some(helper) = opt {\n        helper();\n    }\n    persist(1);\n    a();\n    b2();\n    log!(\"macro\");\n    info();\n}\n",
            language="rust",
        )
        manifest = snapshot.build_manifest(self.root)
        index = semantic_index.build_semantic_index(manifest)
        self.assertEqual(index["coverage"]["src/core.rs"]["status"], "ast")
        self.assertIn("macro expansion bindings are not inferred", index["coverage"]["src/main.rs"]["notes"])
        core_calls = [r for r in index["references"] if r["file"] == "src/core.rs" and r["kind"] == "call"]
        self.assertEqual(len(core_calls), 2)
        self.assertTrue(all(r["resolution"] == "resolved" and r["reason"] == "unique-lexical-binding" for r in core_calls))
        child_calls = [r for r in index["references"] if r["file"] == "src/sub/child.rs" and r["kind"] == "call"]
        self.assertEqual(len(child_calls), 1)
        self.assertEqual(child_calls[0]["resolution"], "resolved")
        self.assertEqual(child_calls[0]["target_id"], "src/core.rs::function@1:0")
        main_calls = {tuple(r["parts"]): r for r in index["references"] if r["file"] == "src/main.rs" and r["kind"] == "call"}
        self.assertEqual(main_calls[("persist",)]["resolution"], "resolved")
        self.assertEqual(main_calls[("a",)]["resolution"], "resolved")
        self.assertEqual(main_calls[("b2",)]["resolution"], "resolved")
        self.assertTrue(main_calls[("helper",)]["known_unrelated"])
        self.assertEqual(main_calls[("info",)]["resolution"], "unresolved")
        self.assertNotIn(("log",), main_calls)
        for m_arg in (None, manifest):
            usages = usage_finder.find_all_usages_batch(["save"], core, self.root, manifest=m_arg)
            self.assertEqual(usages["save"].resolved_count, 2)
            self.assertEqual(usages["save"].importing_modules, ["src/main.rs", "src/sub/child.rs"])
        db_path = self.root / ".codebase-map/manifest.sqlite"
        snapshot.write_snapshot(self.root, db_path)
        with open_snapshot(db_path) as store1:
            meta1 = {s["name"]: s for s in semantic_store.query_meta_code(store1)["symbols"] if s["file"] == "src/core.rs"}
        self.assertIn("Store.method", meta1)
        self.assertIn("inner.sub_fn", meta1)
        core.write_text(
            "pub(crate) fn save<T>(x: T) { helper(1); }\nfn helper(z: i32) {}\npub struct Store { pub helper: i32 }\nimpl Store { pub fn method(&self) { let changed = 99; helper(changed); } }\npub mod inner { pub fn sub_fn() {} }\n",
            encoding="utf-8",
        )
        db_path2 = self.root / ".codebase-map/manifest2.sqlite"
        with open_snapshot(db_path) as store1:
            snapshot.write_snapshot(self.root, db_path2, previous=store1)
        with open_snapshot(db_path2) as store2:
            meta2 = {s["name"]: s for s in semantic_store.query_meta_code(store2)["symbols"] if s["file"] == "src/core.rs"}
        self.assertEqual(meta1["Store.method"]["interface_hash"], meta2["Store.method"]["interface_hash"])
        self.assertNotEqual(meta1["Store.method"]["body_hash"], meta2["Store.method"]["body_hash"])

    def test_go_semantics_and_personalized_pagerank_validation(self):
        from dependency_graph import dependency_graph_metrics
        from languages.semantic import go_semantics
        from languages._treesitter import get_parser, get_tags_query, query_tags
        if get_parser("rust") is not None:
            parser, _ = get_parser("rust")
            tree = parser.parse(b"pub struct Store;\npub fn save() { helper(); }\nfn helper() {}\n")
            self.assertTrue(get_tags_query("rust"))
            tags = query_tags("rust", tree.root_node)
            self.assertIn("definition.function", tags)
            self.assertIn("reference.call", tags)

        class _FakeNode:
            def __init__(self, ntype, start_b, end_b, row, col, end_row, end_col, children=None, fields=None):
                self.type = ntype
                self.start_byte, self.end_byte = start_b, end_b
                self.start_point, self.end_point = (row, col), (end_row, end_col)
                self.children = list(children or ())
                self.named_children = [c for c in self.children if getattr(c, "is_named", True)]
                self._fields = dict(fields or {})
                self.is_named = True

            def child_by_field_name(self, name):
                return self._fields.get(name)

            def children_by_field_name(self, name):
                val = self._fields.get(name)
                return val if isinstance(val, list) else ([val] if val is not None else [])

        src = b"package main\nfunc (i *Invoice) Pay() { helper() }\nfunc helper() {}\n"
        t_node = _FakeNode("type_identifier", 22, 29, 1, 9, 1, 16)
        p_decl = _FakeNode("parameter_declaration", 19, 29, 1, 6, 1, 16, [t_node], {"type": t_node})
        recv = _FakeNode("parameter_list", 18, 30, 1, 5, 1, 17, [p_decl])
        m_name = _FakeNode("field_identifier", 31, 34, 1, 18, 1, 21)
        c_ident = _FakeNode("identifier", 39, 45, 1, 26, 1, 32)
        c_expr = _FakeNode("call_expression", 39, 47, 1, 26, 1, 34, [c_ident], {"function": c_ident})
        m_body = _FakeNode("block", 37, 49, 1, 24, 1, 36, [c_expr])
        m_node = _FakeNode("method_declaration", 13, 49, 1, 0, 1, 36, [recv, m_name, m_body],
                           {"receiver": recv, "name": m_name, "body": m_body})
        h_name = _FakeNode("identifier", 55, 61, 2, 5, 2, 11)
        h_body = _FakeNode("block", 64, 66, 2, 14, 2, 16)
        h_node = _FakeNode("function_declaration", 50, 66, 2, 0, 2, 16, [h_name, h_body],
                           {"name": h_name, "body": h_body})
        root = _FakeNode("source_file", 0, len(src), 0, 0, 3, 0, [m_node, h_node])
        sem = go_semantics(root, src)
        self.assertIsNone(semantic_index._validate(sem, src))
        self.assertIn({"exported": "Invoice.Pay", "local": "Invoice.Pay"}, sem["exports"])
        decls = {d["name"]: d for d in sem["declarations"]}
        self.assertFalse(decls["Invoice.Pay"].get("lexical", True))
        self.assertTrue(decls["helper"].get("lexical", True))

        graph = {"a.py": ["b.py"], "b.py": [], "x.py": ["y.py"], "y.py": []}
        uniform = dependency_graph_metrics(graph)["pagerank"]
        seeded = dependency_graph_metrics(graph, personalization=["a.py"])["pagerank"]
        weighted = dependency_graph_metrics(graph, personalization={"a.py": 3.0, "x.py": 1.0})["pagerank"]
        self.assertAlmostEqual(uniform["b.py"], uniform["y.py"])
        self.assertGreater(seeded["b.py"], seeded["y.py"])
        self.assertGreater(weighted["b.py"], weighted["y.py"])
        for bad in ("a.py", b"a.py", [123], {1: 1.0}, {"a.py": True}, {"a.py": -1.0},
                    {"a.py": float("inf")}, {"a.py": float("nan")}):
            with self.assertRaises(ValueError):
                dependency_graph_metrics(graph, personalization=bad)


if __name__ == "__main__":
    unittest.main()
