"""Behavioral protection for graph-based file classification and CLI analysis."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import classifier
from analyze_file import analyze_single_file
from languages import get_adapter


class FanInTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="map-engine-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def hub(self, importers=8):
        target = self.write("hub.py", "".join(f"def item_{i}():\n    return {i}\n\n" for i in range(7)))
        for i in range(importers):
            self.write(f"app_{i}.py", "from hub import item_6\nfrom hub import item_0\nitem_6()\n")
        return target

    def test_counts_distinct_importing_files_including_side_effect_imports(self):
        self.write("core.py", "VALUE = 1\n")
        self.write("first.py", "import core\nfrom core import VALUE\n")
        self.write("second.py", "import core\n")
        counts = classifier.compute_fan_in(self.root)
        self.assertEqual(counts["core.py"], 2)
        self.assertEqual(counts["first.py"], 0)

    def test_analysis_fan_in_is_independent_of_usage_search_and_export_limit(self):
        target = self.hub()
        analysis = analyze_single_file(target, project_root=self.root)
        self.assertEqual(analysis["imported_by_count"], 8)
        self.assertEqual(analysis["classification"]["imported_by_count"], 8)
        self.assertEqual(analysis["classification"]["level"], "high-complexity")
        self.assertNotIn("usages", analysis)

    def test_reads_and_parses_target_once_while_building_its_import_graph(self):
        target = self.hub(1)
        reads = []
        parses = []
        read_bytes = Path.read_bytes
        adapter = get_adapter("python")
        parse = adapter.parse

        def observe_read(path):
            if path.resolve() == target.resolve():
                reads.append(path)
            return read_bytes(path)

        def observe_parse(content, file_path):
            if Path(file_path).resolve() == target.resolve():
                parses.append(file_path)
            return parse(content, file_path)

        with mock.patch.object(Path, "read_bytes", observe_read), mock.patch.object(adapter, "parse", observe_parse):
            analysis = analyze_single_file(target, project_root=self.root)
        self.assertEqual(analysis["imported_by_count"], 1)
        self.assertEqual(len(reads), 1)
        self.assertEqual(len(parses), 1)

    def test_directory_classification_uses_graph_without_requiring_usages(self):
        self.hub()
        results = classifier.classify_directory(self.root)
        self.assertEqual(results["hub.py"].imported_by_count, 8)
        self.assertEqual(results["hub.py"].classification, classifier.Classification.HIGH_COMPLEXITY)

    def test_omitted_project_root_keeps_project_wide_importers_and_usages(self):
        self.write("pyproject.toml", "[project]\nname = 'example'\n")
        target = self.write("engine/core.py", "def run():\n    return 1\n")
        self.write("app/main.py", "from engine.core import run\nrun()\n")
        analysis = analyze_single_file(target, find_usages=True)
        self.assertEqual(analysis["imported_by_count"], 1)
        self.assertEqual(analysis["usages"]["run"]["importing_modules"], ["app/main.py"])
        self.assertEqual(analysis["usages"]["run"]["count"], 2)

    def test_analysis_reports_resolved_aliases_as_internal_dependencies(self):
        self.write("tsconfig.json", '{"compilerOptions":{"paths":{"@core/*":["src/core/*"]}}}')
        self.write("src/core/engine.ts", "export class Engine {}\n")
        target = self.write(
            "src/main.ts", "import { Engine } from '@core/engine';\n"
            "import client from 'external-client';\nexport const engine = new Engine();\n",
        )
        analysis = analyze_single_file(target, project_root=self.root)
        self.assertEqual(analysis["dependencies"]["internal"], ["@core/engine"])
        self.assertEqual(analysis["dependencies"]["external"], ["external-client"])

    def test_fan_in_respects_hidden_and_git_ignored_directories(self):
        if not shutil.which("git"):
            self.skipTest("git unavailable")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        self.write(".gitignore", "generated/\n")
        self.write("core.py", "VALUE = 1\n")
        self.write("app.py", "import core\n")
        self.write("generated/fake.py", "import core\n")
        self.write(".records/fake.py", "import core\n")
        self.assertEqual(classifier.compute_fan_in(self.root)["core.py"], 1)

    def test_cli_exposes_call_names_and_fan_in_as_additive_json_fields(self):
        target = self.write("app.py", "def run():\n    return helper()\n")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "analyze_file.py"), "--file", str(target),
             "--project-root", str(self.root), "--output-format", "json"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["imported_by_count"], 0)
        self.assertEqual(result["structure"]["functions"][0]["calls_made"], ["helper"])


if __name__ == "__main__":
    unittest.main()
