"""Import graph and usage behavior on bounded, independently specified projects."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))

import snapshot
import usage_finder
from languages import get_adapter
from languages.base import FunctionInfo, ParseResult


class EngineImportTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="xray-engine-imports-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def graph(self, files, target="."):
        self.assertTrue(callable(getattr(snapshot, "module_targets", None)),
                        "snapshot must expose its shared internal import resolver")
        return snapshot.module_targets({"root": self.root.as_posix(), "target": target,
                                        "files": files})

    def test_relative_import_does_not_bind_to_an_unrelated_suffix_match(self):
        graph = self.graph({"src/main.ts": {"imports": ["./missing"]},
                            "other/src/missing.ts": {"imports": []}})
        self.assertEqual(graph["src/main.ts"], [])

    def test_jsonc_extends_keeps_base_config_relative_paths(self):
        self.write("configs/base.json", '{"compilerOptions":{"baseUrl":"../src",'
                   '"paths":{"@core/*":["core/*"],},}, // retained base\n}\n')
        self.write("tsconfig.json", '{"extends":"./configs/base.json"}')
        graph = self.graph({"app/main.ts": {"imports": ["@core/engine"]},
                            "src/core/engine.ts": {"imports": []}})
        self.assertEqual(graph["app/main.ts"], ["src/core/engine.ts"])

    def test_base_url_without_paths_disambiguates_same_named_files(self):
        self.write("tsconfig.json", '{"compilerOptions":{"baseUrl":"src/right"}}')
        graph = self.graph({"main.ts": {"imports": ["engine"]},
                            "src/right/engine.ts": {}, "src/wrong/engine.ts": {}})
        self.assertEqual(graph["main.ts"], ["src/right/engine.ts"])

    def test_package_config_overrides_root_aliases(self):
        self.write("tsconfig.json", '{"compilerOptions":{"paths":{"@local/*":["root/*"]}}}')
        self.write("packages/ui/tsconfig.json", '{"extends":"../../tsconfig.json",'
                   '"compilerOptions":{"baseUrl":".","paths":{"@local/*":["src/*"]}}}')
        graph = self.graph({"packages/ui/main.ts": {"imports": ["@local/engine"]},
                            "packages/ui/src/engine.ts": {}, "root/engine.ts": {}})
        self.assertEqual(graph["packages/ui/main.ts"], ["packages/ui/src/engine.ts"])

    def test_extends_cycles_terminate_and_keep_local_options(self):
        self.write("tsconfig.json", '{"extends":"./other.json",'
                   '"compilerOptions":{"baseUrl":"src"}}')
        self.write("other.json", '{"extends":"./tsconfig.json"}')
        graph = self.graph({"main.ts": {"imports": ["engine"]}, "src/engine.ts": {}})
        self.assertEqual(graph["main.ts"], ["src/engine.ts"])

    def test_workspace_package_exports_and_subpaths_resolve(self):
        self.write("package.json", '{"workspaces":["packages/*"]}')
        self.write("packages/core/package.json", json.dumps({"name": "@acme/core", "exports": {
            ".": "./src/index.ts", "./*": "./src/*.ts"}}))
        graph = self.graph({"app/main.ts": {"imports": ["@acme/core", "@acme/core/tools"]},
                            "packages/core/src/index.ts": {}, "packages/core/src/tools.ts": {}})
        self.assertEqual(graph["app/main.ts"], ["packages/core/src/index.ts", "packages/core/src/tools.ts"])

    def test_external_package_never_becomes_a_same_named_internal_file(self):
        graph = self.graph({"app/main.ts": {"imports": ["@unknown/engine", "engine"]},
                            "src/engine.ts": {}})
        self.assertEqual(graph["app/main.ts"], [])

    def test_config_extends_cannot_read_outside_the_target(self):
        self.write("outside.json", '{"compilerOptions":{"paths":{"@core/*":["core/*"]}}}')
        self.write("project/tsconfig.json", '{"extends":"../outside.json"}')
        graph = self.graph({"project/main.ts": {"imports": ["@core/engine"]},
                            "project/core/engine.ts": {}}, target="project")
        self.assertEqual(graph["project/main.ts"], [])

    def test_alias_import_specifiers_survive_manifest_extraction(self):
        path = self.write("main.ts", "import { Engine } from '@core/engine';\nexport const e = new Engine();\n")
        self.assertEqual(snapshot.file_entry(path)["imports"], ["@core/engine"])

    def test_usage_batch_finds_relative_alias_and_commonjs_importers(self):
        self.write("tsconfig.json", '{"compilerOptions":{"paths":{"@core/*":["src/core/*"]}}}')
        source = self.write("src/core/engine.ts", "export class Engine {}\nexport function start() {}\n")
        self.write("src/relative.ts", "import { Engine as Renamed } from './core/engine';\nnew Renamed();\n")
        self.write("src/alias.ts", "import { start } from '@core/engine';\nstart();\n")
        self.write("src/common.cjs", "const { Engine } = require('./core/engine');\nnew Engine();\n")
        self.write("src/unrelated.ts", "import { Engine } from 'external-engine';\nnew Engine();\n")
        result = usage_finder.find_all_usages_batch(["Engine", "start"], source, self.root)
        engine_files = {Path(name).name for name in result["Engine"].importing_modules}
        start_files = {Path(name).name for name in result["start"].importing_modules}
        self.assertEqual(engine_files, {"relative.ts", "common.cjs"})
        self.assertEqual(start_files, {"alias.ts"})

    def test_python_relative_imports_resolve_packages_and_sibling_modules(self):
        self.write("pkg/__init__.py", "")
        self.write("pkg/core.py", "class Engine: pass\n")
        self.write("pkg/child/main.py", "from ..core import Engine\nfrom .. import core\n")
        manifest = snapshot.build_manifest(self.root)
        self.assertEqual(manifest["files"]["pkg/child/main.py"]["imports"], ["..", "..core"])
        self.assertIn("pkg/core.py", snapshot.module_targets(manifest)["pkg/child/main.py"])

    def test_python_from_dot_import_records_the_imported_module(self):
        self.write("pkg/__init__.py", "")
        self.write("pkg/core.py", "class Engine: pass\n")
        self.write("pkg/main.py", "from . import core\n")
        manifest = snapshot.build_manifest(self.root)
        self.assertIn("pkg/core.py", snapshot.module_targets(manifest)["pkg/main.py"])

    def test_incremental_import_index_uses_fresh_from_import_bindings(self):
        self.write("pkg/__init__.py", "")
        self.write("pkg/first.py", "VALUE = 1\n")
        self.write("pkg/other.py", "VALUE = 2\n")
        importer = self.write("pkg/main.py", "from . import first\n")
        manifest = snapshot.build_manifest(self.root)
        importer.write_text("from . import other\n", encoding="utf-8")
        comparison = snapshot.compare_files(manifest, self.root, verify=True)
        symbols = snapshot.compare_symbols(manifest, comparison)
        index = snapshot.build_import_index(manifest, comparison, symbols)
        self.assertIn("pkg/main.py", index.get("pkg/other.py", []))
        self.assertNotIn("pkg/main.py", index.get("pkg/first.py", []))

    def test_paths_targets_use_ordered_fallbacks(self):
        self.write("tsconfig.json", '{"compilerOptions":{"paths":{"@core/*":["first/*","second/*"]}}}')
        graph = self.graph({"main.ts": {"imports": ["@core/engine"]},
                            "first/engine.ts": {}, "second/engine.ts": {}})
        self.assertEqual(graph["main.ts"], ["first/engine.ts"])

    def test_exact_alias_precedes_a_wildcard_matching_the_empty_string(self):
        self.write("tsconfig.json", json.dumps({"compilerOptions": {"paths": {
            "engine*": ["wildcard*"], "engine": ["exact"]}}}))
        graph = self.graph({"main.ts": {"imports": ["engine"]},
                            "wildcard.ts": {}, "exact.ts": {}})
        self.assertEqual(graph["main.ts"], ["exact.ts"])

    def test_longest_wildcard_prefix_and_first_existing_target_win(self):
        self.write("tsconfig.json", json.dumps({"compilerOptions": {"paths": {
            "@*": ["generic/*"], "@core/*": ["missing/*", "specific/*", "last/*"]}}}))
        graph = self.graph({"main.ts": {"imports": ["@core/engine"]},
                            "generic/core/engine.ts": {}, "specific/engine.ts": {}, "last/engine.ts": {}})
        self.assertEqual(graph["main.ts"], ["specific/engine.ts"])

    def test_relative_extends_can_append_json_to_a_dotted_config_name(self):
        self.write("tsconfig.base.json", '{"compilerOptions":{"baseUrl":"src"}}')
        self.write("tsconfig.json", '{"extends":"./tsconfig.base"}')
        graph = self.graph({"main.ts": {"imports": ["engine"]}, "src/engine.ts": {}})
        self.assertEqual(graph["main.ts"], ["src/engine.ts"])

    def test_configuration_inheritance_is_bounded(self):
        self.write("tsconfig.json", '{"extends":"./config0.json"}')
        for index in range(80):
            self.write(f"config{index}.json", json.dumps({"extends": f"./config{index + 1}.json"}))
        observed = []
        read = Path.read_text

        def record(path, *args, **kwargs):
            observed.append(path.name)
            return read(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", record):
            snapshot.ts_path_config(self.root)
        self.assertLessEqual(len(observed), 33)

    def test_inherited_alias_paths_keep_their_declaring_base_url(self):
        self.write("configs/base.json", '{"compilerOptions":{"baseUrl":"../base",'
                   '"paths":{"engine":["engine"]}}}')
        self.write("tsconfig.json", '{"extends":"./configs/base.json","compilerOptions":{"baseUrl":"local"}}')
        graph = self.graph({"main.ts": {"imports": ["engine"]}, "base/engine.ts": {}, "local/engine.ts": {}})
        self.assertEqual(graph["main.ts"], ["base/engine.ts"])

    def test_null_workspace_exports_keep_main_and_subpaths_private(self):
        self.write("package.json", '{"workspaces":["packages/*"]}')
        self.write("packages/core/package.json", '{"name":"@acme/core","exports":null,"main":"index.js"}')
        graph = self.graph({"main.ts": {"imports": ["@acme/core", "@acme/core/private"]},
                            "packages/core/index.ts": {}, "packages/core/private.ts": {}})
        self.assertEqual(graph["main.ts"], [])

    def test_exact_null_export_blocks_a_more_general_wildcard(self):
        self.write("package.json", '{"workspaces":["packages/*"]}')
        self.write("packages/core/package.json", json.dumps({"name": "@acme/core", "exports": {
            "./private*": "./src/private*.ts", "./private": None}}))
        graph = self.graph({"main.ts": {"imports": ["@acme/core/private"]}, "packages/core/src/private.ts": {}})
        self.assertEqual(graph["main.ts"], [])

    def test_graph_rejects_hidden_and_gitignored_paths_in_a_supplied_manifest(self):
        if not shutil.which("git"):
            self.skipTest("git unavailable")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        self.write(".gitignore", "generated/\n")
        self.write("generated/core.ts", "export const Engine = 1;\n")
        self.write(".records/core.ts", "export const Engine = 1;\n")
        graph = self.graph({"main.ts": {"imports": ["./generated/core", "./.records/core"]},
                            "generated/core.ts": {}, ".records/core.ts": {}})
        self.assertEqual(graph["main.ts"], [])

    def test_removed_alias_target_retains_its_unchanged_importers(self):
        self.write("tsconfig.json", '{"compilerOptions":{"paths":{"engine":["src/core"]}}}')
        core = self.write("src/core.ts", "export class Engine {}\n")
        self.write("main.ts", "import { Engine } from 'engine';\n")
        manifest = snapshot.build_manifest(self.root)
        core.unlink()
        comparison = snapshot.compare_files(manifest, self.root, verify=True)
        symbols = snapshot.compare_symbols(manifest, comparison)
        index = snapshot.build_import_index(manifest, comparison, symbols)
        self.assertEqual(snapshot.blast_radius(index, comparison, symbols),
                         [{"file": "main.ts", "imports": ["src/core.ts"]}])

    def test_python_from_package_import_module_exposes_the_modules_exports(self):
        source = self.write("pkg/core.py", "class Engine: pass\nclass Other: pass\n")
        self.write("pkg/__init__.py", "")
        self.write("main.py", "from pkg import core as service\nservice.Engine()\n")
        self.write("direct.py", "from pkg.core import Engine\nEngine()\n")
        result = usage_finder.find_all_usages_batch(["Engine", "Other"], source, self.root)
        self.assertEqual(set(result["Engine"].importing_modules), {"main.py", "direct.py"})
        self.assertEqual(result["Other"].importing_modules, ["main.py"])

    def test_usage_batch_filters_stale_manifest_paths_before_backend_reads(self):
        if not shutil.which("git"):
            self.skipTest("git unavailable")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        source = self.write("core.py", "class Engine: pass\n")
        self.write("main.py", "from core import Engine\nEngine()\n")
        self.write("generated/fake.py", "Engine()\n")
        self.write(".records/fake.py", "Engine()\n")
        manifest = snapshot.build_manifest(self.root)
        manifest["files"][".records/fake.py"] = {"imports": []}
        self.write(".gitignore", "generated/\n")
        reads = []
        original_read = Path.read_bytes

        def read_allowed(path):
            if path.is_relative_to(self.root):
                relative = path.relative_to(self.root).as_posix()
                self.assertNotIn(relative, {"generated/fake.py", ".records/fake.py"})
                reads.append(relative)
            return original_read(path)

        with mock.patch.object(Path, "read_bytes", read_allowed):
            result = usage_finder.find_all_usages_batch(["Engine", "Engine"], source, self.root, manifest=manifest)
        self.assertEqual(sorted(reads), ["core.py", "main.py"])
        self.assertEqual([Path(usage.file_path).name for usage in result["Engine"].usages if usage.usage_type == "call"], ["main.py"])
        self.assertEqual([Path(usage.file_path).name for usage in result["Engine"].usages if usage.usage_type == "import"], ["main.py"])
        self.assertEqual(result["Engine"].resolved_count, 1)
        self.assertEqual(result["Engine"].importing_modules, ["main.py"])
        self.assertEqual(list(result), ["Engine"])

    def test_usage_batch_resolves_the_shared_graph_once(self):
        source = self.write("core.py", "class Engine: pass\ndef start(): pass\n")
        self.write("main.py", "from core import Engine, start\nEngine(); start()\n")
        manifest = snapshot.build_manifest(self.root)
        with mock.patch.object(snapshot, "resolved_imports", wraps=snapshot.resolved_imports) as resolve:
            result = usage_finder.find_all_usages_batch(["Engine", "start", "Engine"], source, self.root, manifest=manifest)
        self.assertEqual(resolve.call_count, 1)
        self.assertEqual(result["Engine"].importing_modules, ["main.py"])

    def test_jsonc_trailing_comma_cleanup_preserves_string_values(self):
        self.write("tsconfig.json", '{"compilerOptions":{"paths":{"engine":["src/,}.ts"],},},}')
        graph = self.graph({"main.ts": {"imports": ["engine"]}, "src/,}.ts": {}})
        self.assertEqual(graph["main.ts"], ["src/,}.ts"])

    def test_alias_candidates_cannot_resolve_files_outside_the_target(self):
        self.write("project/tsconfig.json", '{"compilerOptions":{"paths":{"engine":["../outside"]}}}')
        graph = self.graph({"project/main.ts": {"imports": ["engine"]}, "outside.ts": {}}, target="project")
        self.assertEqual(graph["project/main.ts"], [])

    def test_explicit_javascript_extension_can_resolve_typescript_source(self):
        graph = self.graph({"main.ts": {"imports": ["./core.js"]}, "core.ts": {}})
        self.assertEqual(graph["main.ts"], ["core.ts"])

    def test_dotted_module_basename_keeps_its_full_identity(self):
        graph = self.graph({"main.ts": {"imports": ["./engine.worker"]},
                            "engine.worker.ts": {}, "engine.ts": {}})
        self.assertEqual(graph["main.ts"], ["engine.worker.ts"])

    def test_usage_commonjs_destructuring_fallback_keeps_named_bindings(self):
        from languages import javascript

        source = self.write("core.js", "export class Engine {}\nexport function start() {}\n")
        self.write("main.cjs", "const { Engine: Renamed } = require('./core');\nnew Renamed();\n")
        with mock.patch.object(javascript, "_ts_parse", return_value=None):
            result = usage_finder.find_all_usages_batch(["Engine", "start"], source, self.root)
        self.assertEqual(result["Engine"].importing_modules, ["main.cjs"])
        self.assertEqual(result["start"].importing_modules, [])

    def test_default_import_alias_matches_only_the_default_export(self):
        source = self.write("core.js", "export default class Engine {}\nexport class Other {}\n")
        self.write("main.js", "import Renamed from './core.js';\nnew Renamed();\n")
        self.write("mixed.js", "import Alias, { Other as Named } from './core.js';\n")
        self.write("named.js", "import { Other } from './core.js';\n")
        self.write("default-named.js", "import { default as Renamed } from './core.js';\n")
        self.write("barrel.js", "export { default as PublicEngine } from './core.js';\n")
        manifest = snapshot.build_manifest(self.root)
        self.assertEqual(manifest["files"]["core.js"].get("default_export"), "Engine")
        self.assertEqual(manifest["files"]["main.js"]["import_bindings"][0].get("default_import"), "Renamed")
        result = usage_finder.find_all_usages_batch(["Engine", "Other"], source, self.root, manifest=manifest)
        self.assertEqual(set(result["Engine"].importing_modules),
                         {"main.js", "mixed.js", "default-named.js", "barrel.js"})
        self.assertEqual(set(result["Other"].importing_modules), {"mixed.js", "named.js"})

    def test_default_alias_cannot_impersonate_an_unrelated_named_export(self):
        source = self.write("core.js", "export default class Engine {}\nexport class Other {}\n")
        self.write("main.js", "import Other from './core.js';\n")
        self.write("mixed.js", "import Other, { Other as Named } from './core.js';\n")
        self.write("dual.js", "import Other, { default as Second } from './core.js';\n")
        result = usage_finder.find_all_usages_batch(["Engine", "Other"], source, self.root)
        self.assertEqual(result["Other"].importing_modules, ["mixed.js"])
        self.assertEqual(set(result["Engine"].importing_modules), {"main.js", "mixed.js", "dual.js"})

    def test_default_alias_provenance_is_preserved_in_regex_fallback(self):
        from languages import javascript

        source = self.write("core.js", "export default class Engine {}\nexport class Other {}\n")
        self.write("main.js", "import Other from './core.js';\n")
        self.write("dual.js", "import Other, { default as Second } from './core.js';\n")
        with mock.patch.object(javascript, "_ts_parse", return_value=None):
            manifest = snapshot.build_manifest(self.root)
        result = usage_finder.find_all_usages_batch(["Engine", "Other"], source, self.root, manifest=manifest)
        self.assertEqual(set(result["Engine"].importing_modules), {"main.js", "dual.js"})
        self.assertEqual(result["Other"].importing_modules, [])

    def test_named_default_alias_collision_preserves_a_real_named_export(self):
        source = self.write("core.js", "export default class Engine {}\nexport class Other {}\n")
        self.write("main.js", "import { default as Other, Other as Named } from './core.js';\n")
        self.write("reverse.js", "import { Other as Named, default as Other } from './core.js';\n")
        result = usage_finder.find_all_usages_batch(["Engine", "Other"], source, self.root)
        self.assertEqual(set(result["Engine"].importing_modules), {"main.js", "reverse.js"})
        self.assertEqual(set(result["Other"].importing_modules), {"main.js", "reverse.js"})

    def test_named_default_alias_collision_is_preserved_in_regex_fallback(self):
        from languages import javascript

        source = self.write("core.js", "export default class Engine {}\nexport class Other {}\n")
        self.write("main.js", "import { default as Other, Other as Named } from './core.js';\n")
        self.write("reverse.js", "import { Other as Named, default as Other } from './core.js';\n")
        with mock.patch.object(javascript, "_ts_parse", return_value=None):
            manifest = snapshot.build_manifest(self.root)
        result = usage_finder.find_all_usages_batch(["Engine", "Other"], source, self.root, manifest=manifest)
        self.assertEqual(set(result["Engine"].importing_modules), {"main.js", "reverse.js"})
        self.assertEqual(set(result["Other"].importing_modules), {"main.js", "reverse.js"})

    def test_workspace_exports_do_not_expose_unexported_subpaths(self):
        self.write("package.json", '{"workspaces":["packages/*"]}')
        self.write("packages/core/package.json", '{"name":"@acme/core","exports":"./src/index.ts"}')
        graph = self.graph({"main.ts": {"imports": ["@acme/core/private"]},
                            "packages/core/private.ts": {}, "packages/core/src/index.ts": {}})
        self.assertEqual(graph["main.ts"], [])

    def test_workspace_main_without_dot_prefix_resolves(self):
        self.write("package.json", '{"workspaces":["packages/*"]}')
        self.write("packages/core/package.json", '{"name":"@acme/core","main":"src/index.js"}')
        graph = self.graph({"main.ts": {"imports": ["@acme/core"]}, "packages/core/src/index.ts": {}})
        self.assertEqual(graph["main.ts"], ["packages/core/src/index.ts"])

    def test_ignored_and_hidden_configuration_is_never_read(self):
        if not shutil.which("git"):
            self.skipTest("git unavailable")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        self.write(".gitignore", "generated/\nignored.json\n")
        self.write("ignored.json", '{"compilerOptions":{"baseUrl":"src"}}')
        self.write("tsconfig.json", '{"extends":"./ignored.json"}')
        self.write("generated/tsconfig.json", '{}')
        self.write(".records/tsconfig.json", '{}')
        observed = []
        read = Path.read_text

        def record(path, *args, **kwargs):
            observed.append(path.relative_to(self.root).as_posix())
            return read(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", record):
            graph = self.graph({"main.ts": {"imports": ["engine"]}, "src/engine.ts": {}})
        self.assertEqual(graph["main.ts"], [])
        self.assertEqual(observed, ["tsconfig.json"])

    def test_supplied_parse_uses_the_callers_bytes_without_rereading_or_parsing(self):
        path = self.write("main.py", "def run():\n    return 2\n")
        content = "def run():\r\n    return 1\r\n"
        result = get_adapter("python").parse(content, str(path))
        read = Path.read_bytes

        def reject_target_read(candidate):
            self.assertNotEqual(candidate.resolve(), path.resolve(), "caller supplied source bytes must be reused")
            return read(candidate)

        with mock.patch.object(Path, "read_bytes", reject_target_read), mock.patch.object(
            get_adapter("python"), "parse", side_effect=AssertionError("caller parse must be reused")
        ):
            manifest = snapshot.build_manifest(self.root, parse_results={path: (content, result)})
        row = manifest["files"]["main.py"]
        self.assertEqual(row["size"], len(content.encode("utf-8")))
        self.assertEqual(row["hash"], snapshot.hash_text(content.replace("\r\n", "\n")))
        self.assertEqual(manifest["metrics"]["files_read"], 0)
        self.assertEqual(manifest["metrics"]["parsed_files"], 0)

    def test_syntax_error_keeps_independently_recovered_symbols(self):
        path = self.write("main.ts", "export function intact() {}\nconst broken = ;\n")
        parsed = ParseResult(str(path), language="typescript", functions=[
            FunctionInfo("intact", line_number=1, end_line=1)
        ], notes=["parser=tree-sitter (ts)", "syntax error: missing expression"])
        row = snapshot.file_entry(path, parse_result=parsed)
        self.assertEqual(row["status"], "parse-error")
        self.assertIn("intact", row["symbols"])

    def test_usage_batch_reuses_manifest_without_additional_parses(self):
        source = self.write("core.ts", "export class Engine {}\nexport function start() {}\n")
        self.write("main.ts", "import { Engine, start } from './core';\nnew Engine(); start();\n")
        manifest = snapshot.build_manifest(self.root)
        with mock.patch.object(snapshot, "build_manifest", side_effect=AssertionError("manifest must be reused")), mock.patch.object(
            get_adapter("typescript"), "parse", side_effect=AssertionError("manifest already parsed")
        ):
            result = usage_finder.find_all_usages_batch(["Engine", "start"], source, self.root, manifest=manifest)
        self.assertEqual(result["Engine"].importing_modules, ["main.ts"])
        self.assertEqual(result["start"].importing_modules, ["main.ts"])

    def test_usage_python_fallback_never_reads_ignored_or_hidden_sources(self):
        if not shutil.which("git"):
            self.skipTest("git unavailable")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        self.write(".gitignore", "generated/\n")
        self.write("main.py", "Engine()\n")
        self.write("generated/fake.py", "Engine()\n")
        self.write(".records/fake.py", "Engine()\n")
        observed = []
        read = Path.read_text
        run = subprocess.run

        def no_search_tool(command, *args, **kwargs):
            if command[0] in {"rg", "grep"}:
                raise FileNotFoundError(command[0])
            return run(command, *args, **kwargs)

        def record(path, *args, **kwargs):
            observed.append(path.relative_to(self.root).as_posix())
            return read(path, *args, **kwargs)

        with mock.patch.object(subprocess, "run", no_search_tool), mock.patch.object(Path, "read_text", record):
            result = usage_finder.find_usages_with_grep("Engine", [self.root])
        self.assertEqual(observed, ["main.py"])
        self.assertEqual([Path(item.file_path).name for item in result], ["main.py"])

    def test_usage_batch_python_fallback_reads_each_importer_once(self):
        source = self.write("core.py", "class Engine: pass\ndef start(): pass\n")
        self.write("main.py", "from core import Engine, start\nEngine(); start()\n")
        manifest = snapshot.build_manifest(self.root)
        observations = {"core.py": source.read_bytes()}
        observed = []
        read = Path.read_bytes
        run = subprocess.run

        def no_search_tool(command, *args, **kwargs):
            if command[0] in {"rg", "grep"}:
                raise FileNotFoundError(command[0])
            return run(command, *args, **kwargs)

        def record(path, *args, **kwargs):
            if path.is_relative_to(self.root):
                observed.append(path.name)
            return read(path, *args, **kwargs)

        with mock.patch.object(subprocess, "run", no_search_tool), mock.patch.object(Path, "read_bytes", record):
            result = usage_finder.find_all_usages_batch(["Engine", "start"], source, self.root,
                                                       manifest=manifest, source_observations=observations)
        self.assertEqual(observed, ["main.py"])
        self.assertEqual(result["Engine"].importing_modules, ["main.py"])
        self.assertEqual(result["start"].importing_modules, ["main.py"])


if __name__ == "__main__":
    unittest.main()
