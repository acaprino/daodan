"""The codebase-xray script suite, exercised on small sources.

These scripts are what the X-ray method tells every phase to run instead of
reading files by hand, and until this file they had no test at all. Each case
here pins a behaviour the first review found wrong or unverified: the
classifier calling every file with an author line security-critical, the
TypeScript parser missing arrow-function methods, the Java parser missing
nested types, duplicate import modules in the CLI output, and a documentation
scan that shouted "ALL DOCUMENTATION SHOULD BE CONSIDERED UNVERIFIED" at any
project not born with this toolkit's marker convention.

Tree-sitter is optional for the scripts and absent on CI, so the cases that
need it are skipped there and the regex fallback is what CI exercises.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import types
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/codebase-xray/skills/xray-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import classifier  # noqa: E402
from ast_parser import parse_file  # noqa: E402
from languages._treesitter import get_parser  # noqa: E402
from usage_finder import find_all_usages  # noqa: E402

HAVE_TREE_SITTER = get_parser("typescript") is not None
HAVE_GIT = shutil.which("git") is not None

TYPESCRIPT = textwrap.dedent(
    """
    import { Router } from "express";
    import type { User } from "./types";
    const DEFAULT_TTL = 300;
    export interface Repo<T> { get(id: string): Promise<T | null>; }
    export enum Status { Active = "active", Archived = "archived" }
    export type Handler = (u: User) => void;
    export class UserService implements Repo<User> {
      private cache = new Map<string, User>();
      constructor(private readonly router: Router) {}
      async get(id: string): Promise<User | null> { return this.cache.get(id) ?? null; }
      onUser = (u: User): void => { this.cache.set(u.id, u); };
    }
    export const makeService = (r: Router) => new UserService(r);
    """
)

JAVA = textwrap.dedent(
    """
    package com.example;
    import java.util.Map;
    import java.util.HashMap;
    public class Svc<T extends Comparable<T>> {
        private static final int MAX = 10;
        private final Map<String, T> store = new HashMap<>();
        @Override
        public String toString() { return "Svc"; }
        public synchronized void put(String k,
                                     T v) { store.put(k, v); }
        public static class Inner { public int x; }
        interface Listener { void on(String s); }
    }
    """
)

RUST = textwrap.dedent(
    """
    use std::collections::HashMap;
    pub const MAX: usize = 10;
    pub struct Store<'a, T: Clone> { items: HashMap<&'a str, T> }
    pub trait Repo { fn get(&self, k: &str) -> Option<String>; }
    impl<'a, T: Clone> Repo for Store<'a, T> { fn get(&self, k: &str) -> Option<String> { None } }
    """
)

PYTHON = textwrap.dedent(
    """
    import os
    from pathlib import Path

    class Loader:
        def read(self, path: Path) -> str:
            return path.read_text()

    def helper(x: int) -> int:
        return x + 1
    """
)

# Span fixtures: every symbol body covers more than one line and starts on line
# 1 of the file, so each expected (first, last) pair below is read off the
# source by counting.
JS_SPANS = textwrap.dedent(
    """\
    export class Store {
      get(key) {
        return key;
      }
    }

    function load(path) {
      return path;
    }

    const save = (value) => {
      return value;
    };
    """
)

TS_SPANS = textwrap.dedent(
    """\
    export interface Repo {
      get(id: string): string;
    }
    export enum Status {
      Active = "active",
    }
    export type Handler = (
      u: string,
    ) => void;
    export class Cache {
      clear(): void {
        return;
      }
    }
    """
)

JAVA_SPANS = textwrap.dedent(
    """\
    public class Svc {
      public int put(int x) {
        return x;
      }
      interface Listener {
        void on();
      }
    }
    """
)

RUST_SPANS = textwrap.dedent(
    """\
    pub struct Store {
        items: Vec<u8>,
    }
    impl Store {
        pub fn len(&self) -> usize {
            self.items.len()
        }
    }
    pub trait Repo {
        fn get(&self) -> u8;
    }
    pub fn load() -> u8 {
        0
    }
    pub mod inner {
        pub fn helper() {}
    }
    pub type Id = u64;
    """
)


def _write(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _spans(result) -> dict[tuple[str, str], tuple[int, int | None]]:
    """(qualified name, kind) to (first line, last line) for every symbol."""
    spans = {}
    for cls in result.classes:
        spans[(cls.name, cls.kind)] = (cls.line_number, cls.end_line)
        for method in cls.methods:
            spans[(f"{cls.name}.{method.name}", "method")] = (method.line_number, method.end_line)
    for func in result.functions:
        spans[(func.name, "function")] = (func.line_number, func.end_line)
    return spans


def _unreachable_grammar_pack():
    """A grammar pack that is installed but cannot fetch a grammar.

    It mirrors tree-sitter-language-pack 1.x: `get_parser` downloads a grammar
    on first use and raises the pack's own `DownloadError`, a plain Exception
    subclass, when the cache it looks in is empty and the network is not there.
    Returns the module and the list of languages it was asked for.
    """
    pack = types.ModuleType("tree_sitter_language_pack")
    calls: list[str] = []

    class Error(Exception):
        pass

    class DownloadError(Error):
        pass

    def get_parser(name):
        calls.append(name)
        raise DownloadError(f"Failed to fetch manifest for {name}: dns error")

    pack.Error = Error
    pack.DownloadError = DownloadError
    pack.get_parser = get_parser
    return pack, calls


class ClassifierTests(unittest.TestCase):
    def test_an_author_line_is_not_a_security_signal(self):
        result = classifier.classify_from_content(
            "author = 'someone'\nauthored_by = 'x'\nimport os\n", "meta.py"
        )
        self.assertNotEqual(result.classification, classifier.Classification.CRITICAL)
        self.assertEqual(result.critical_patterns_found, [])

    def test_authentication_still_is(self):
        result = classifier.classify_from_content(
            "def authenticate(user, token):\n    return True\n", "login.py"
        )
        self.assertEqual(result.classification, classifier.Classification.CRITICAL)

    def test_an_ordinary_import_count_is_not_high_complexity(self):
        imports = "\n".join(f"import mod{i}" for i in range(6))
        body = "\n".join(f"value_{i} = {i}" for i in range(150))
        result = classifier.classify_from_content(f"{imports}\n{body}\n", "plain.py")
        self.assertEqual(result.classification, classifier.Classification.STANDARD)
        self.assertFalse(result.verification_required)


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.temp, ignore_errors=True))

    def test_python_uses_the_stdlib_parser(self):
        result = parse_file(_write(self.temp, "mod.py", PYTHON))
        self.assertIn("parser=stdlib-ast", result.notes)
        self.assertEqual([c.name for c in result.classes], ["Loader"])
        self.assertEqual([m.name for m in result.classes[0].methods], ["read"])
        self.assertIn("helper", [f.name for f in result.functions])

    def test_typescript_finds_the_class_on_either_parser(self):
        result = parse_file(_write(self.temp, "svc.ts", TYPESCRIPT))
        self.assertIn("UserService", [c.name for c in result.classes])
        self.assertIn("UserService", result.exported_symbols)
        # Members too, on either parser. Asserting only the class name was the
        # gap that let the regex fallback ship with no member extraction at
        # all: snapshot.py then recorded one span for the whole class, so an
        # edit to one method was indistinguishable from an edit to any other,
        # and every overload collapsed into nothing to key a span on.
        service = next(c for c in result.classes if c.name == "UserService")
        self.assertEqual(
            {m.name for m in service.methods}, {"constructor", "get", "onUser"}
        )

    @unittest.skipUnless(HAVE_TREE_SITTER, "tree-sitter not installed")
    def test_typescript_tree_sitter_sees_arrow_methods_and_const_functions(self):
        result = parse_file(_write(self.temp, "svc.ts", TYPESCRIPT))
        self.assertIn("parser=tree-sitter (ts)", result.notes)
        service = next(c for c in result.classes if c.name == "UserService")
        self.assertIn("get", [m.name for m in service.methods])
        self.assertIn("onUser", [m.name for m in service.methods])
        self.assertIn("makeService", [f.name for f in result.functions])
        self.assertEqual(
            {c.kind for c in result.classes}, {"class", "interface", "enum", "type-alias"}
        )

    def test_java_finds_the_class_on_either_parser(self):
        result = parse_file(_write(self.temp, "Svc.java", JAVA))
        self.assertIn("Svc", [c.name for c in result.classes])

    @unittest.skipUnless(HAVE_TREE_SITTER, "tree-sitter not installed")
    def test_java_tree_sitter_sees_nested_types_and_multiline_methods(self):
        result = parse_file(_write(self.temp, "Svc.java", JAVA))
        names = [c.name for c in result.classes]
        self.assertIn("Svc.Inner", names)
        self.assertIn("Svc.Listener", names)
        outer = next(c for c in result.classes if c.name == "Svc")
        self.assertEqual({m.name for m in outer.methods}, {"toString", "put"})
        listener = next(c for c in result.classes if c.name == "Svc.Listener")
        self.assertEqual(listener.kind, "interface")

    def test_rust_finds_struct_and_trait(self):
        result = parse_file(_write(self.temp, "lib.rs", RUST))
        names = [c.name for c in result.classes]
        self.assertIn("Store", names)
        self.assertIn("Repo", names)
        self.assertIn("MAX", result.constants)

    def test_cli_output_lists_each_import_module_once(self):
        source = _write(self.temp, "Svc.java", JAVA)
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "ast_parser.py"), str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        external = payload["imports"]["external"]
        self.assertEqual(len(external), len(set(external)), external)


class TreeSitterSpanTests(unittest.TestCase):
    """Tree-sitter knows where every symbol ends, and the result must say so.

    Without an end line snapshot.py spans a symbol to the line before the next
    one, so code between two symbols counts as the first one's body and an edit
    there re-derives claims about a symbol that did not change. Python carried
    exact ends from the stdlib parser; every Tree-sitter adapter had the same
    fact in each node and dropped it.
    """

    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)

    @unittest.skipUnless(HAVE_TREE_SITTER, "tree-sitter not installed")
    def test_every_symbol_carries_its_last_line(self):
        cases = [
            ("svc.js", JS_SPANS, {
                ("Store", "class"): (1, 5),
                ("Store.get", "method"): (2, 4),
                ("load", "function"): (7, 9),
                ("save", "function"): (11, 13),
            }),
            ("svc.ts", TS_SPANS, {
                ("Repo", "interface"): (1, 3),
                ("Status", "enum"): (4, 6),
                ("Handler", "type-alias"): (7, 9),
                ("Cache", "class"): (10, 14),
                ("Cache.clear", "method"): (11, 13),
            }),
            ("Svc.java", JAVA_SPANS, {
                ("Svc", "class"): (1, 8),
                ("Svc.put", "method"): (2, 4),
                ("Svc.Listener", "interface"): (5, 7),
                ("Svc.Listener.on", "method"): (6, 6),
            }),
            ("lib.rs", RUST_SPANS, {
                ("Store", "struct"): (1, 3),
                ("Store", "impl"): (4, 8),
                ("Store.len", "method"): (5, 7),
                ("Repo", "trait"): (9, 11),
                ("Repo.get", "method"): (10, 10),
                ("load", "function"): (12, 14),
                ("inner", "mod"): (15, 17),
                ("Id", "type-alias"): (18, 18),
            }),
        ]
        for name, source, expected in cases:
            with self.subTest(name):
                result = parse_file(_write(self.temp, name, source))
                self.assertTrue(result.notes[0].startswith("parser=tree-sitter"), result.notes)
                spans = _spans(result)
                for key, span in expected.items():
                    self.assertEqual(spans.get(key), span, key)


class GrammarPackFailureTests(unittest.TestCase):
    """An installed grammar pack that fails is not a missing one.

    The 2026-10-10 analysis-speed pilot ran the scripts where the pack's
    grammar cache resolved to an empty directory. Its get_parser tried a
    download, raised DownloadError, and the loader, which caught only import
    and version errors, let it through: parse_file crashed, and snapshot.py
    recorded every JavaScript file with no symbols at all.
    """

    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        # The loader caches per process: drop the real entries now and the
        # fake pack's entries once the real modules are back.
        get_parser.cache_clear()
        self.addCleanup(get_parser.cache_clear)

    def _install(self, pack) -> None:
        # None in sys.modules makes an import raise ImportError, which keeps
        # the per-grammar strategy out of the way wherever it is installed.
        patcher = mock.patch.dict(
            sys.modules, {"tree_sitter_language_pack": pack, "tree_sitter": None}
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_pack_that_cannot_fetch_a_grammar_falls_back_and_says_why(self):
        pack, _calls = _unreachable_grammar_pack()
        self._install(pack)
        cases = [
            ("svc.js", JS_SPANS, "Store", "parser=regex-fallback"),
            ("svc.ts", TS_SPANS, "Cache", "parser=regex-fallback (ts)"),
            ("Svc.java", JAVA_SPANS, "Svc", "parser=regex-fallback"),
            ("lib.rs", RUST_SPANS, "Store", "parser=regex-fallback"),
        ]
        for name, source, symbol, provenance in cases:
            with self.subTest(name):
                result = parse_file(_write(self.temp, name, source))
                self.assertIn(provenance, result.notes)
                self.assertIn(symbol, [c.name for c in result.classes])
                self.assertTrue(
                    any(n.startswith("tree-sitter unavailable: DownloadError") for n in result.notes),
                    result.notes,
                )

    def test_a_failed_grammar_fetch_is_not_retried_for_every_file(self):
        pack, calls = _unreachable_grammar_pack()
        self._install(pack)
        parse_file(_write(self.temp, "a.js", JS_SPANS))
        parse_file(_write(self.temp, "b.js", JS_SPANS))
        self.assertEqual(calls, ["javascript"])

    def test_a_pack_that_is_not_installed_falls_back_without_a_failure_note(self):
        self._install(None)
        result = parse_file(_write(self.temp, "svc.js", JS_SPANS))
        self.assertIn("parser=regex-fallback", result.notes)
        self.assertFalse(
            any(n.startswith("tree-sitter unavailable") for n in result.notes), result.notes
        )


class UsageFinderTests(unittest.TestCase):
    def test_finds_import_and_reference(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        _write(temp, "core.py", "class Engine:\n    pass\n")
        _write(temp, "app.py", "from core import Engine\n\nengine = Engine()\n")
        result = find_all_usages("Engine", temp / "core.py", temp)
        self.assertGreaterEqual(len(result.usages), 2)
        self.assertTrue(any("app.py" in str(u) for u in result.usages), result.usages)

    def test_a_usage_under_a_dot_directory_is_not_reported(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        _write(temp, "core.py", "class Engine:\n    pass\n")
        _write(temp, "app.py", "from core import Engine\n\nengine = Engine()\n")
        _write(temp, ".daodan/runs/r1/replay.py", "from core import Engine\n\nengine = Engine()\n")
        files = {Path(u.file_path).as_posix() for u in find_all_usages("Engine", temp / "core.py", temp).usages}
        self.assertTrue([f for f in files if f.endswith("/app.py")], files)
        self.assertFalse([f for f in files if "/.daodan/" in f], files)

    def test_an_importer_under_a_dot_directory_is_not_reported(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        _write(temp, "core.py", "class Engine:\n    pass\n")
        _write(temp, "app.py", "from core import Engine\n\nengine = Engine()\n")
        _write(temp, ".daodan/runs/r1/replay.py", "from core import Engine\n\nengine = Engine()\n")
        importers = find_all_usages("Engine", temp / "core.py", temp).importing_modules
        self.assertTrue([m for m in importers if m.endswith("app.py")], importers)
        self.assertFalse([m for m in importers if ".daodan" in m], importers)

    @unittest.skipUnless(HAVE_GIT, "git is not installed")
    def test_a_usage_in_a_file_git_ignores_is_not_reported(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        subprocess.run(["git", "-C", str(temp), "init", "-q"], check=True, capture_output=True)
        _write(temp, ".gitignore", "generated/\n")
        _write(temp, "core.py", "class Engine:\n    pass\n")
        _write(temp, "app.py", "from core import Engine\n\nengine = Engine()\n")
        _write(temp, "generated/replay.py", "from core import Engine\n\nengine = Engine()\n")
        files = {Path(u.file_path).as_posix() for u in find_all_usages("Engine", temp / "core.py", temp).usages}
        self.assertTrue([f for f in files if f.endswith("/app.py")], files)
        self.assertFalse([f for f in files if "/generated/" in f], files)


class DocReviewTests(unittest.TestCase):
    def test_a_project_without_markers_is_not_shouted_at(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        docs = temp / "docs"
        docs.mkdir()
        _write(docs, "guide.md", "# Guide\n\nPlain documentation with no markers.\n")
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "doc_review.py"), "scan", "--path", "docs"],
            cwd=temp,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertNotIn("ALL DOCUMENTATION SHOULD BE CONSIDERED UNVERIFIED", completed.stdout)
        self.assertIn("does not use the", completed.stdout)
        self.assertIn("not used by this project", completed.stdout)
        self.assertNotIn("Phase 8", completed.stdout + completed.stderr)

    def _docs_with_a_hidden_vault(self):
        from doc_review import DocReviewer

        temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        _write(temp, "docs/guide.md", "# Guide\n\nPlain documentation.\n")
        _write(
            temp,
            "docs/.obsidian/note.md",
            "# Note\n\nSee [the plan](missing-plan.md). Checked [VERIFIED: src/gone.py::gone].\n",
        )
        return DocReviewer(str(temp))

    def test_a_scan_does_not_count_documents_under_a_dot_directory(self):
        self.assertEqual(self._docs_with_a_hidden_vault().scan("docs/").total_files, 1)

    def test_link_validation_does_not_read_documents_under_a_dot_directory(self):
        self.assertEqual(self._docs_with_a_hidden_vault().validate_links("docs/"), [])

    def test_marker_validation_does_not_read_documents_under_a_dot_directory(self):
        self.assertEqual(self._docs_with_a_hidden_vault().validate_markers("docs/"), [])


class CommentAnalysisTests(unittest.TestCase):
    def test_analyze_runs_on_a_python_file(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        source = _write(temp, "mod.py", '"""Module docstring."""\n\n# increment x\nx = 1\n')
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "rewrite_comments.py"), "analyze", str(source), "--report"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("Comment Analysis", completed.stdout)

    def test_a_recursive_scan_skips_source_under_a_dot_directory(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        _write(temp, "src/mod.py", '"""Module docstring."""\n\n# increment x\nx = 1\n')
        _write(temp, ".cache/copy.py", '"""Module docstring."""\n\n# increment x\nx = 1\n')
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "rewrite_comments.py"), "scan", str(temp), "--recursive", "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        scanned = [Path(entry["file"]).as_posix() for entry in json.loads(completed.stdout)["files"]]
        self.assertEqual(len(scanned), 1, scanned)
        self.assertTrue(scanned[0].endswith("src/mod.py"), scanned)


if __name__ == "__main__":
    unittest.main()
