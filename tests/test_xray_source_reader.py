"""Hash-bound source selection and its real filesystem/CLI contracts.

The literals below are the oracle: selected bodies and shared declarations
remain visible, while unrelated callable bodies are not silently read in depth.
"""

import builtins
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/codebase-xray/skills/xray-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import snapshot  # noqa: E402
import source_reader  # noqa: E402


SOURCE = '''import marker
RATE = 7

class Language:
    CSS = "css"

class Consumer:
    ENABLED = True

    @tracked(
        category="chosen"
    )
    def selected(
        self,
        count,
    ):
        return count * RATE

    def sibling(self):
        return "SIBLING_BODY_MARKER"

    REVERSE = {Language.CSS: RATE}

def unrelated():
    return "UNRELATED_BODY_MARKER"
'''


def write(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="")
    return path


def numbered_lines(packet):
    """Decode the public numbered-source format, rejecting duplicated lines."""
    found = {}
    for item in packet["files"]:
        for block in item["blocks"]:
            for line in block["source"].splitlines():
                match = re.fullmatch(r"(\d+): (.*)", line)
                if not match:
                    raise AssertionError(f"not a numbered source line: {line!r}")
                number = int(match[1])
                if number in found:
                    raise AssertionError(f"source line emitted twice: {number}")
                found[number] = match[2]
    return found


@contextmanager
def source_must_not_open(paths):
    """Observe file opening at the OS/Path boundary, allowing helper reads."""
    blocked = {str(path.absolute()) for path in paths}
    original_path_open = Path.open
    original_os_open = os.open
    original_builtin_open = builtins.open

    def check(path):
        if isinstance(path, (str, bytes, os.PathLike)):
            spelling = str(Path(os.fsdecode(path)).absolute())
            if spelling in blocked:
                raise AssertionError(f"source opened before refusing the request: {spelling}")

    def path_open(path, *args, **kwargs):
        check(path)
        return original_path_open(path, *args, **kwargs)

    def os_open(path, *args, **kwargs):
        check(path)
        return original_os_open(path, *args, **kwargs)

    def builtin_open(path, *args, **kwargs):
        check(path)
        return original_builtin_open(path, *args, **kwargs)

    with mock.patch.object(Path, "open", path_open), \
            mock.patch.object(os, "open", os_open), \
            mock.patch.object(builtins, "open", builtin_open):
        yield


class SourceReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="xray-source-reader-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        if shutil.which("git"):
            subprocess.run(["git", "init", str(self.tmp)], check=True, capture_output=True)
        self.src = self.tmp / "src"
        self.path = write(self.src, "module.py", SOURCE)
        self.manifest = snapshot.build_manifest(self.src)
        self.key = next(key for key in self.manifest["files"] if key.endswith("module.py"))

    def request(self, **selection):
        return source_reader.read_packet(self.manifest, [{"path": self.key, **selection}])

    def read_native_fixture(self, source, symbols, selected):
        """Replay independently observed native spans without requiring its DLL.

        Tree-sitter 0.26 and the cached JavaScript grammar produced the literal
        spans used below, with no syntax errors. Only backend availability is
        controlled; source identity, target/perimeter and packet reading are real.
        """
        write(self.src, "native.js", source)
        manifest = snapshot.build_manifest(self.src)
        key = next(key for key in manifest["files"] if key.endswith("native.js"))
        profile = {"language": "javascript", "backend": "tree-sitter", "grammar": "javascript"}
        entry = manifest["files"][key]
        entry.update(language="javascript", status="parsed", parser_notes=["parser=tree-sitter"],
                     parser_profile=profile, symbols=symbols)

        with mock.patch.object(snapshot, "parser_profile", return_value=profile):
            return source_reader.read_packet(manifest, [{"path": key, "symbols": [selected]}])

    def run_cli(self, script, *args):
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / script), *map(str, args)],
            capture_output=True, text=True, cwd=self.tmp, env=environment,
        )

    def manifest_file(self):
        path = self.tmp / "manifest.json"
        path.write_text(json.dumps(self.manifest), encoding="utf-8")
        return path

    def test_selected_method_keeps_imports_constants_decorators_and_shared_fields(self):
        packet = self.request(symbols=["Consumer.selected"])

        emitted = numbered_lines(packet)
        self.assertEqual(emitted[1], "import marker")
        self.assertEqual(emitted[2], "RATE = 7")
        self.assertEqual(emitted[5], '    CSS = "css"')
        self.assertEqual(emitted[8], "    ENABLED = True")
        self.assertEqual(emitted[10], "    @tracked(")
        self.assertEqual(emitted[11], '        category="chosen"')
        self.assertEqual(emitted[12], "    )")
        self.assertEqual(emitted[13], "    def selected(")
        self.assertEqual(emitted[17], "        return count * RATE")
        self.assertEqual(emitted[22], "    REVERSE = {Language.CSS: RATE}")
        self.assertNotIn(20, emitted)
        self.assertNotIn(25, emitted)
        self.assertEqual(packet["metrics"]["source_bytes_read"], len(SOURCE.encode("utf-8")))

    def test_exact_method_sharing_class_field_line_uses_full_file_fallback(self):
        source = ("class Config { static ENABLED = true; sibling() { return 1; } }\n"
                  "function selected() {\n  return Config.ENABLED;\n}\n")
        # Native byte ranges for Config and its method differ, but both map to
        # line 1. Removing the method's line removes Config.ENABLED as well.
        spans = {
            "Config": {"kind": "class", "start": 1, "end": 1, "span_precision": "exact"},
            "Config.sibling": {"kind": "method", "start": 1, "end": 1, "span_precision": "exact"},
            "selected": {"kind": "function", "start": 2, "end": 4, "span_precision": "exact"},
        }

        packet = self.read_native_fixture(source, spans, "selected")

        emitted = numbered_lines(packet)
        self.assertEqual(set(emitted), {1, 2, 3, 4, 5})
        self.assertEqual(emitted[1], "class Config { static ENABLED = true; sibling() { return 1; } }")
        self.assertEqual(packet["metrics"]["source_lines_emitted"], 5)

    def test_exact_sibling_functions_sharing_a_line_use_full_file_fallback(self):
        source = ("function left() { return 1; } function right() { return 2; }\n"
                  "function selected() {\n  return left();\n}\n")
        spans = {
            "left": {"kind": "function", "start": 1, "end": 1, "span_precision": "exact"},
            "right": {"kind": "function", "start": 1, "end": 1, "span_precision": "exact"},
            "selected": {"kind": "function", "start": 2, "end": 4, "span_precision": "exact"},
        }

        packet = self.read_native_fixture(source, spans, "selected")

        emitted = numbered_lines(packet)
        self.assertEqual(set(emitted), {1, 2, 3, 4, 5})
        self.assertEqual(emitted[1], "function left() { return 1; } function right() { return 2; }")

    def test_long_minified_exact_source_does_not_drop_shared_global_declaration(self):
        first_line = 'const PAYLOAD = "' + "x" * 11_000 + '"; function sibling() { return 1; }'
        source = first_line + "\nfunction selected() {\n  return PAYLOAD;\n}\n"
        spans = {
            "sibling": {"kind": "function", "start": 1, "end": 1, "span_precision": "exact"},
            "selected": {"kind": "function", "start": 2, "end": 4, "span_precision": "exact"},
        }

        packet = self.read_native_fixture(source, spans, "selected")

        emitted = numbered_lines(packet)
        self.assertEqual(set(emitted), {1, 2, 3, 4, 5})
        self.assertEqual(emitted[1], first_line)

    def test_short_global_beside_exact_callable_is_preserved(self):
        source = ("const RATE = 7; function sibling() { return 1; }\n"
                  "function selected() {\n  return RATE;\n}\n")
        spans = {
            "sibling": {"kind": "function", "start": 1, "end": 1, "span_precision": "exact"},
            "selected": {"kind": "function", "start": 2, "end": 4, "span_precision": "exact"},
        }

        packet = self.read_native_fixture(source, spans, "selected")

        emitted = numbered_lines(packet)
        self.assertEqual(set(emitted), {1, 2, 3, 4, 5})
        self.assertEqual(emitted[1], "const RATE = 7; function sibling() { return 1; }")

    def test_global_after_exact_callable_closure_is_preserved(self):
        source = ("function sibling() {\n  return 1;\n} const RATE = 7;\n"
                  "function selected() {\n  return RATE;\n}\n")
        spans = {
            "sibling": {"kind": "function", "start": 1, "end": 3, "span_precision": "exact"},
            "selected": {"kind": "function", "start": 4, "end": 6, "span_precision": "exact"},
        }

        packet = self.read_native_fixture(source, spans, "selected")

        emitted = numbered_lines(packet)
        self.assertEqual(emitted[3], "} const RATE = 7;")
        self.assertEqual(emitted[5], "  return RATE;")
        self.assertNotIn(2, emitted)

    def test_comma_separated_global_before_exact_arrow_header_is_preserved(self):
        source = ("const RATE = 7, sibling = () => {\n  return 1;\n};\n"
                  "function selected() {\n  return RATE;\n}\n")
        spans = {
            "sibling": {"kind": "function", "start": 1, "end": 3, "span_precision": "exact"},
            "selected": {"kind": "function", "start": 4, "end": 6, "span_precision": "exact"},
        }

        packet = self.read_native_fixture(source, spans, "selected")

        emitted = numbered_lines(packet)
        self.assertEqual(emitted[1], "const RATE = 7, sibling = () => {")
        self.assertEqual(emitted[4], "function selected() {")
        self.assertEqual(emitted[5], "  return RATE;")
        self.assertEqual(emitted[6], "}")
        self.assertNotIn(2, emitted)

    def test_static_field_before_exact_method_header_is_preserved(self):
        source = ("class Config {\n  static ENABLED = true; sibling() {\n    return 1;\n  }\n}\n"
                  "function selected() {\n  return Config.ENABLED;\n}\n")
        spans = {
            "Config": {"kind": "class", "start": 1, "end": 5, "span_precision": "exact"},
            "Config.sibling": {"kind": "method", "start": 2, "end": 4, "span_precision": "exact"},
            "selected": {"kind": "function", "start": 6, "end": 8, "span_precision": "exact"},
        }

        packet = self.read_native_fixture(source, spans, "selected")

        emitted = numbered_lines(packet)
        self.assertEqual(emitted[2], "  static ENABLED = true; sibling() {")
        self.assertEqual(emitted[7], "  return Config.ENABLED;")
        self.assertNotIn(3, emitted)

    def test_explicit_overlapping_ranges_emit_the_requested_source_once(self):
        packet = self.request(ranges=[{"start": 13, "end": 15}, {"start": 15, "end": 17}])

        emitted = numbered_lines(packet)
        for number, text in {
            13: "    def selected(", 14: "        self,", 15: "        count,",
            16: "    ):", 17: "        return count * RATE",
        }.items():
            self.assertEqual(emitted[number], text)
        self.assertNotIn(20, emitted)
        self.assertNotIn(25, emitted)

    def test_full_file_metrics_distinguish_utf8_bytes_from_source_characters(self):
        write(self.src, "module.py", "A = 1\nB = 'ππ'")
        self.manifest = snapshot.build_manifest(self.src)

        packet = self.request(full_file=True)

        self.assertEqual(numbered_lines(packet), {1: "A = 1", 2: "B = 'ππ'"})
        self.assertEqual(packet["metrics"]["source_bytes_read"], 16)
        self.assertEqual(packet["metrics"]["source_lines_emitted"], 2)
        self.assertEqual(packet["metrics"]["source_characters_emitted"], 15)

    def test_unknown_symbol_and_invalid_ranges_are_explicit_errors(self):
        selections = [
            {"symbols": ["Consumer.missing"]},
            {"ranges": [{"start": 0, "end": 1}]},
            {"ranges": [{"start": 9, "end": 2}]},
            {"ranges": [{"start": 1, "end": 999}]},
            {"ranges": [{"start": True, "end": 2}]},
        ]

        for selection in selections:
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                self.request(**selection)

    def test_context_only_request_keeps_declarations_without_callable_bodies(self):
        packet = self.request()

        emitted = numbered_lines(packet)
        self.assertEqual(emitted[1], "import marker")
        self.assertEqual(emitted[5], '    CSS = "css"')
        self.assertEqual(emitted[22], "    REVERSE = {Language.CSS: RATE}")
        self.assertNotIn(17, emitted)
        self.assertNotIn(20, emitted)
        self.assertNotIn(25, emitted)

    def test_same_size_and_timestamp_edit_is_refused_by_content_identity(self):
        initial_stat = self.path.stat()
        self.path.write_text(SOURCE.replace("RATE = 7", "RATE = 8"), encoding="utf-8", newline="")
        os.utime(self.path, ns=(initial_stat.st_atime_ns, initial_stat.st_mtime_ns))
        self.assertEqual(self.path.stat().st_size, initial_stat.st_size)
        self.assertEqual(self.path.stat().st_mtime_ns, initial_stat.st_mtime_ns)

        with self.assertRaises(ValueError):
            self.request(symbols=["Consumer.selected"])

    def test_deleted_source_is_refused(self):
        self.path.unlink()

        with self.assertRaises(ValueError):
            self.request(full_file=True)

    def test_changed_parser_fingerprint_is_refused_before_source_open(self):
        self.manifest["parser_fingerprint"] = "sha256:different-parser-code"

        with source_must_not_open([self.path]), self.assertRaises(ValueError):
            self.request(symbols=["Consumer.selected"])

    def test_changed_backend_profile_is_refused_before_source_open(self):
        entry = self.manifest["files"][self.key]
        entry["parser_profile"] = {**entry["parser_profile"], "backend": "different-backend"}

        with source_must_not_open([self.path]), self.assertRaises(ValueError):
            self.request(symbols=["Consumer.selected"])

    def test_inferred_merged_and_missing_precision_fall_back_to_the_whole_file(self):
        original = copy.deepcopy(self.manifest)
        for precision in ("inferred", "merged", None):
            with self.subTest(precision=precision):
                self.manifest = copy.deepcopy(original)
                symbol = self.manifest["files"][self.key]["symbols"]["Consumer.selected"]
                if precision is None:
                    symbol.pop("span_precision")
                else:
                    symbol["span_precision"] = precision

                packet = self.request(symbols=["Consumer.selected"])

                emitted = numbered_lines(packet)
                self.assertEqual(emitted[20], '        return "SIBLING_BODY_MARKER"')
                self.assertEqual(emitted[25], '    return "UNRELATED_BODY_MARKER"')

    def test_legacy_manifest_checks_normalized_hash_and_reads_the_whole_file(self):
        self.manifest.pop("parser_fingerprint")
        entry = self.manifest["files"][self.key]
        for field in ("raw_hash", "parser_profile", "parser_notes", "status"):
            entry.pop(field, None)
        for symbol in entry["symbols"].values():
            symbol.pop("span_precision", None)

        packet = self.request(symbols=["Consumer.selected"])

        self.assertEqual(numbered_lines(packet)[20], '        return "SIBLING_BODY_MARKER"')
        self.assertRegex(json.dumps(packet).lower(), r"refresh|rebuild|legacy")
        self.path.write_text(SOURCE.replace("RATE = 7", "RATE = 8"), encoding="utf-8", newline="")
        with self.assertRaises(ValueError):
            self.request(full_file=True)

    def test_unknown_absolute_and_traversal_paths_are_refused_before_source_open(self):
        requests = ["unknown.py", self.path.as_posix(), "../outside.py", self.key + "/../module.py"]

        for path in requests:
            with self.subTest(path=path), source_must_not_open([self.path]), self.assertRaises(ValueError):
                source_reader.read_packet(self.manifest, [{"path": path, "full_file": True}])

    def test_forged_inventory_cannot_read_forbidden_dot_or_dependency_paths(self):
        for relative in ("credentials.py", ".cache/hidden.py", "node_modules/pkg/file.py"):
            with self.subTest(relative=relative):
                denied = write(self.src, relative, SOURCE)
                key = denied.relative_to(Path(self.manifest["root"])).as_posix()
                manifest = copy.deepcopy(self.manifest)
                manifest["files"][key] = copy.deepcopy(manifest["files"][self.key])

                with source_must_not_open([denied]), self.assertRaises(ValueError):
                    source_reader.read_packet(manifest, [{"path": key, "full_file": True}])

    def test_inventory_entry_outside_target_is_refused_before_source_open(self):
        denied = write(self.tmp, "outside.py", SOURCE)
        key = denied.relative_to(Path(self.manifest["root"])).as_posix()
        self.manifest["files"][key] = copy.deepcopy(self.manifest["files"][self.key])

        with source_must_not_open([denied]), self.assertRaises(ValueError):
            source_reader.read_packet(self.manifest, [{"path": key, "full_file": True}])

    @unittest.skipUnless(shutil.which("git"), "Git is required for current-ignore perimeter evidence")
    def test_new_git_ignore_rule_refuses_previously_inventoried_source_before_open(self):
        write(self.tmp, ".gitignore", "src/module.py\n")

        with source_must_not_open([self.path]), self.assertRaises(ValueError):
            self.request(full_file=True)

    def test_linked_source_is_refused_before_open_when_symlinks_are_supported(self):
        destination = write(self.tmp, "destination.py", SOURCE)
        self.path.unlink()
        try:
            self.path.symlink_to(destination)
        except OSError as error:
            self.skipTest(f"filesystem/account cannot create a symlink: {error}")

        with source_must_not_open([self.path, destination]), self.assertRaises(ValueError):
            self.request(full_file=True)

    def test_windows_reparse_ancestor_is_refused_before_source_open(self):
        original_lstat = Path.lstat

        def filesystem_lstat(path, *args, **kwargs):
            result = original_lstat(path, *args, **kwargs)
            if path == self.src:
                return SimpleNamespace(st_mode=result.st_mode, st_file_attributes=0x400)
            return result

        # The Windows filesystem attribute is the controlled OS boundary.
        # The path and source bytes remain ordinary real fixture files.
        with mock.patch.object(Path, "lstat", filesystem_lstat), \
                source_must_not_open([self.path]), self.assertRaises(ValueError):
            self.request(full_file=True)

    def test_parse_failure_reads_full_source_instead_of_an_incomplete_range(self):
        write(self.src, "module.py", "def broken(:\n    return 'SYNTAX_BODY'\n")
        self.manifest = snapshot.build_manifest(self.src)
        self.assertEqual(self.manifest["files"][self.key]["status"], "parse-error")

        packet = self.request(ranges=[{"start": 1, "end": 1}])

        self.assertEqual(numbered_lines(packet)[2], "    return 'SYNTAX_BODY'")
        self.assertTrue(packet["files"][0]["parser_notes"])

    def test_oracle_sql_with_invalid_utf8_retains_detected_language_and_full_source(self):
        path = self.src / "archive.sql"
        raw = (b"CREATE OR REPLACE PACKAGE archive AS\n"
               b"  c_rate CONSTANT PLS_INTEGER := 7;\nEND archive;\n/\n"
               b"-- Invalid byte: \xff\n")
        path.write_bytes(raw)
        manifest = snapshot.build_manifest(path)
        key = next(iter(manifest["files"]))
        entry = manifest["files"][key]
        self.assertEqual(entry["language"], "plsql")
        self.assertEqual(entry["parser_profile"]["language"], "plsql")
        self.assertEqual(entry["status"], "parse-error")

        packet = source_reader.read_packet(manifest, [{"path": key, "ranges": [{"start": 1, "end": 1}]}])

        self.assertEqual(numbered_lines(packet), {
            1: "CREATE OR REPLACE PACKAGE archive AS",
            2: "  c_rate CONSTANT PLS_INTEGER := 7;", 3: "END archive;",
            4: "/", 5: "-- Invalid byte: \ufffd", 6: "",
        })
        self.assertEqual(packet["metrics"]["source_bytes_read"], len(raw))

    def test_oversized_oracle_sql_retains_language_and_readable_reused_snapshot(self):
        path = self.src / "archive.sql"
        padding = "x" * 2_000_000
        raw = (b"CREATE OR REPLACE PACKAGE archive AS\n"
               b"  c_rate CONSTANT PLS_INTEGER := 7;\nEND archive;\n/\n-- "
               + padding.encode("ascii") + b"\n")
        path.write_bytes(raw)
        manifest = snapshot.build_manifest(path)
        parent = copy.deepcopy(manifest)
        key = next(iter(manifest["files"]))
        entry = manifest["files"][key]
        self.assertEqual(entry["language"], "plsql")
        self.assertEqual(entry["parser_profile"]["language"], "plsql")
        self.assertEqual(entry["status"], "parse-skipped")
        request = [{"path": key, "ranges": [{"start": 1, "end": 1}]}]

        packet = source_reader.read_packet(manifest, request)
        reused = snapshot.build_manifest(path, previous=manifest)
        reused_packet = source_reader.read_packet(reused, request)

        expected = {
            1: "CREATE OR REPLACE PACKAGE archive AS",
            2: "  c_rate CONSTANT PLS_INTEGER := 7;", 3: "END archive;",
            4: "/", 5: "-- " + padding, 6: "",
        }
        self.assertEqual(numbered_lines(packet), expected)
        self.assertEqual(numbered_lines(reused_packet), expected)
        self.assertEqual(reused["metrics"]["cache_hits"], 1)
        self.assertEqual(reused["metrics"]["parsed_files"], 0)
        self.assertEqual(reused["files"][key]["language"], "plsql")
        self.assertEqual(reused["files"][key]["status"], "parse-skipped")
        self.assertEqual(manifest, parent)

    def test_outline_remains_metadata_only_when_source_is_unavailable(self):
        self.path.unlink()

        with source_must_not_open([self.path]):
            outline = source_reader.outline_manifest(self.manifest, pattern="Consumer.selected", limit=1)

        self.assertEqual([item["symbol"] for item in outline["items"]], ["Consumer.selected"])
        self.assertFalse(outline["truncated"])

    def test_outline_is_bounded_and_never_emits_function_bodies(self):
        manifest_path = self.manifest_file()

        result = self.run_cli("source_reader.py", "outline", manifest_path, "--path", self.key, "--limit", "1")

        self.assertEqual(result.returncode, 0, result.stderr)
        outline = json.loads(result.stdout)
        self.assertEqual(len(outline["items"]), 1)
        self.assertTrue(outline["truncated"])
        self.assertGreater(outline["matched"], 1)
        self.assertNotIn("SIBLING_BODY_MARKER", result.stdout)
        self.assertNotIn("UNRELATED_BODY_MARKER", result.stdout)
        selected = self.run_cli("source_reader.py", "outline", manifest_path, "--pattern", "Consumer.selected")
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertEqual([item["symbol"] for item in json.loads(selected.stdout)["items"]], ["Consumer.selected"])

    def test_write_reuse_and_read_cli_share_one_manifest_contract(self):
        manifest_path = self.tmp / "manifest.json"
        initial = self.run_cli("snapshot.py", "write", self.src, "--out", manifest_path)
        self.assertEqual(initial.returncode, 0, initial.stderr)

        reused = self.run_cli("snapshot.py", "write", self.src, "--out", manifest_path, "--reuse", manifest_path)
        selected = self.run_cli("source_reader.py", "read", manifest_path, "--path", self.key, "--symbol", "Consumer.selected")

        self.assertEqual(reused.returncode, 0, reused.stderr)
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertEqual(numbered_lines(json.loads(selected.stdout))[17], "        return count * RATE")
        self.assertNotIn("SIBLING_BODY_MARKER", selected.stdout)
        requests = self.tmp / "requests.json"
        requests.write_text(json.dumps([{"path": self.key, "ranges": [{"start": 17, "end": 17}]}]), encoding="utf-8")
        by_request = self.run_cli("source_reader.py", "read", manifest_path, "--requests", requests)
        self.assertEqual(by_request.returncode, 0, by_request.stderr)
        self.assertEqual(numbered_lines(json.loads(by_request.stdout))[17], "        return count * RATE")


if __name__ == "__main__":
    unittest.main()
