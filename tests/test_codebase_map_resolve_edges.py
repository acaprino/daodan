"""The derived edge pass: the analyzers' stages, the edge store bound to its snapshot, declared coverage."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from importlib import metadata
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import resolve_edges
import engine_pass  # noqa: E402
import engine_tools  # noqa: E402
import semantic_store  # noqa: E402
import snapshot
from snapshot_store import _unpack, open_snapshot
from test_codebase_map_edge_view import end, outside, write_answers


def coverage_sums(coverage: dict) -> tuple[int, int]:
    """(sites, answered + holes) of one language's coverage: the invariant says they are equal."""
    return coverage["sites"], sum(coverage["answered"].values()) + sum(
        hole["count"] for hole in coverage["holes"].values())


class EdgeStoreTests(unittest.TestCase):
    """The store bound to its snapshot: refused when it is of another revision, malformed or of another resolver."""

    SOURCES = {
        # `helper.run()` leaves the lexical resolver with an unknown receiver: the index answers it.
        "app/use.py": "class User:\n    def go(self, helper):\n        return helper.run()\n",
        "app/tool.py": "class Tool:\n    def run(self):\n        return 1\n\n\ndef free():\n    return 2\n",
    }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        self.root.mkdir()
        for rel, text in self.SOURCES.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.manifest = self.root.parent / "manifest.sqlite"
        snapshot.read_project(self.root, self.manifest)
        self.edges = self.root.parent / "engine-edges.sqlite"

    def answer_run(self):
        """The store with `helper.run()` answered by `Tool.run`."""
        _identity, before = self.unresolved_run_reference()
        write_answers(self.manifest, self.edges, {("app/use.py", before["span"][0]): [end("app/tool.py", "run", 2)]})

    def references(self):
        with open_snapshot(self.manifest) as store:
            return [(row[0], row[1], _unpack(row[2])) for row in store.connection.execute(
                "SELECT id, resolution, payload FROM sem_references WHERE kind='call' ORDER BY id")]

    def stored_edges(self):
        with open_snapshot(self.manifest) as store:
            return resolve_edges.read_edge_store(self.edges, store)

    def unresolved_run_reference(self):
        for identity, resolution, payload in self.references():
            if payload["file"] == "app/use.py" and resolution == "unresolved" \
                    and payload["parts"] == ["helper", "run"]:
                return identity, payload
        raise AssertionError("the unknown-receiver call was not recorded")

    def test_every_reference_names_its_resolver_before_any_engine_runs(self):
        rows = self.references()
        self.assertTrue(rows)
        self.assertEqual({payload.get("resolver") for _id, _res, payload in rows},
                         {resolve_edges.resolution.LEXICAL_RESOLVER})

    def test_edges_of_another_snapshot_revision_are_refused_not_joined(self):
        self.answer_run()
        (self.root / "app" / "use.py").write_text(
            "class User:\n    def go(self, helper):\n        return helper.run()\n"
            "# edited after the engine pass\n", encoding="utf-8")
        snapshot.read_project(self.root, self.manifest)
        edges, binding, reason = self.stored_edges()
        self.assertIsNone(edges)
        self.assertIsNotNone(binding)
        self.assertIn("different snapshot revision", reason)

    def test_a_malformed_derived_store_is_refused_with_a_reason(self):
        self.edges.write_bytes(b"not a SQLite database")
        edges, binding, reason = self.stored_edges()
        self.assertIsNone(edges)
        self.assertIsNone(binding)
        self.assertIn("invalid engine edge store", reason)

    def test_resolver_version_mismatch_is_rejected(self):
        self.answer_run()
        with mock.patch.object(semantic_store, "RESOLVER_VERSION", 999):
            edges, binding, reason = self.stored_edges()
        self.assertIsNone(edges)
        self.assertIsNotNone(binding)
        self.assertIn("resolver version", reason)

    def test_completed_empty_pass_is_distinct_from_missing_store(self):
        with open_snapshot(self.manifest) as store:
            missing_edges, missing_binding, missing_reason = resolve_edges.read_edge_store(self.edges, store)
        self.assertIsNone(missing_edges)
        self.assertIsNone(missing_binding)
        self.assertIn("no engine edge store", missing_reason)

        write_answers(self.manifest, self.edges, {})
        edges, binding, reason = self.stored_edges()
        self.assertIsNone(reason)
        self.assertEqual(edges, [])
        self.assertEqual(binding["languages"]["python"]["state"], "fresh")
        self.assertTrue(binding["languages"]["python"]["coverage"]["holes"])

    def test_engine_target_must_belong_to_snapshot(self):
        self.answer_run()
        import sqlite3
        conn = sqlite3.connect(self.edges)
        try:
            conn.execute("UPDATE edges SET target_id='app/ghost.py::function@1:0'")
            conn.commit()
        finally:
            conn.close()
        edges, binding, reason = self.stored_edges()
        self.assertIsNone(edges)
        self.assertIsNotNone(binding)
        self.assertIn("not in snapshot", reason)

    def test_divergent_targets_remain_conflicts(self):
        import edge_view
        _identity, _before = self.unresolved_run_reference()
        self.answer_run()
        with open_snapshot(self.manifest) as store:
            row = store.connection.execute(
                "SELECT id FROM sem_declarations WHERE file='app/tool.py' AND name='free'"
            ).fetchone()
            free_id = row[0]
        # A reference the caller resolves lexically to `free` while the store says `run`.
        with open_snapshot(self.manifest) as store:
            edges, binding, reason = resolve_edges.read_edge_store(self.edges, store)
            self.assertIsNone(reason)
            view = edge_view.load_edge_view(
                store,
                engine_store=self.edges,
                lexical_overrides={_identity: free_id},
            )
        self.assertEqual(len(view["conflicts"]), 1)
        conflict = view["conflicts"][0]
        self.assertEqual(conflict["reference_id"], _identity)
        self.assertEqual(conflict["lexical_target_id"], free_id)
        self.assertTrue(conflict["engine_target_id"].startswith("app/tool.py::function@2:4"))
        ref_by_id = {item["id"]: item for item in view["references"]}
        self.assertEqual(ref_by_id[_identity]["target_id"], free_id)


# The entries with Python on an entry named as the stores of `write_answers` name their resolver.
STUB_ENGINES = (engine_pass.EngineSpec("stub", ("python",), (), "tree_sitter", engine_pass.INDEXER_INSTALL, "python"),
                    *(spec for spec in resolve_edges.ENGINES if spec.name != "scip-python"))
STUB_LANGUAGES = {language: spec for spec in reversed(STUB_ENGINES) for language in spec.languages}


def install_stub_entry(test):
    """The stub entry plays the installed Python analyzer in these pass lifecycle tests."""
    from indexers import python
    test.enterContext(mock.patch.object(engine_pass, "ENGINES", STUB_ENGINES))
    test.enterContext(mock.patch.object(engine_pass, "ENGINE_LANGUAGES", STUB_LANGUAGES))
    test.enterContext(mock.patch.object(python, "VERSION", "1.0"))


class PassLifecycleTests(unittest.TestCase):
    """The store's lifecycle: its state, the detached pass, the snapshot it follows."""

    SOURCES = {
        # One call of each kind: a builtin, a callee named after nothing the
        # project declares, and an unknown receiver whose method the project has.
        "app/use.py": ("class User:\n    def go(self, helper):\n"
                       "        helper.append(len(helper))\n        return helper.run()\n"),
        "app/tool.py": "class Tool:\n    def run(self):\n        return 1\n",
        "notes.md": "# Notes\n",
    }

    def setUp(self):
        install_stub_entry(self)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        for rel, text in self.SOURCES.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.manifest = self.root.parent / "manifest.sqlite"
        snapshot.read_project(self.root, self.manifest)

    def record(self, **process) -> Path:
        """The pass's record of its process, where the pass keeps it: outside the store."""
        path = resolve_edges.running_record(self.manifest)
        self.addCleanup(path.unlink, missing_ok=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(process), encoding="utf-8")
        self.assertNotIn(self.root.parent, path.parents)
        return path

    def run_line(self):
        return self.SOURCES["app/use.py"].split("\n").index("        return helper.run()") + 1

    def run_pass(self):
        """The Python entry's store, `helper.run()` answered by `Tool.run`."""
        write_answers(self.manifest, resolve_edges.default_edge_store(self.manifest),
                      {("app/use.py", self.run_line()): [end("app/tool.py", "run", 2)]}, languages=("python",))

    def test_each_language_says_whether_an_engine_covers_it(self):
        (self.root / "app/use.ts").write_text(
            "function use(helper) { return helper.run(); }\n", encoding="utf-8")
        snapshot.read_project(self.root, self.manifest)
        self.run_pass()
        state = resolve_edges.edge_state(self.manifest)
        self.assertEqual((state["languages"]["python"]["engine"], state["languages"]["typescript"]["state"]),
                         ("stub@1.0", "missing"))
        self.assertEqual(state["coverage"]["python"]["answered"]["project-callable"], 1)

    def test_the_store_state_follows_the_pass_and_the_snapshot(self):
        self.assertEqual(resolve_edges.edge_state(self.manifest)["state"], "missing")
        self.run_pass()
        state = resolve_edges.edge_state(self.manifest)
        self.assertEqual(state["state"], "fresh")
        self.assertEqual(state["coverage"]["python"]["answered"]["project-callable"], 1)
        self.assertEqual(state["languages"]["python"]["coverage"], state["coverage"]["python"])
        (self.root / "app/tool.py").write_text("class Tool:\n    def run(self):\n        return 2\n",
                                                encoding="utf-8")
        snapshot.read_project(self.root, self.manifest)
        self.assertEqual(resolve_edges.edge_state(self.manifest)["state"], "stale")

    def test_a_missing_engine_is_unavailable_and_starts_no_process(self):
        with mock.patch.object(engine_tools, "uv_binary", side_effect=OSError("no network")), \
                mock.patch.object(shutil, "which", side_effect=AssertionError("the PATH's uv")), \
                mock.patch.object(importlib.util, "find_spec", return_value=None), \
                mock.patch.object(engine_pass, "_spawn_detached") as spawn:
            result = resolve_edges.ensure_edges(self.manifest)
        spawn.assert_not_called()
        self.assertEqual((result["state"], result["action"]), ("unavailable", "none"))
        self.assertIn("uv", result["install"])
        self.assertEqual(resolve_edges.edge_state(self.manifest)["state"], "unavailable")

    def test_the_pass_runs_under_uv_with_the_snapshots_parser_set(self):
        report = self.manifest.with_name(resolve_edges.REPORT_NAME)

        def version(name):
            if name == "tree-sitter":
                return "0.25.2"
            raise metadata.PackageNotFoundError(name)

        # Daodan's pinned uv, never the PATH's: no configuration file, its cache Daodan's.
        with mock.patch.object(engine_tools, "uv_binary", return_value=Path("/daodan/uv")), \
                mock.patch.object(shutil, "which", side_effect=AssertionError("the PATH's uv")), \
                mock.patch.object(metadata, "version", side_effect=version):
            command = resolve_edges.stage_command(engine_pass.ENGINE_LANGUAGES["python"], self.manifest, report)
        python = f"{sys.version_info[0]}.{sys.version_info[1]}"
        self.assertEqual(command[:9], [str(Path("/daodan/uv")), "run", "--quiet", *engine_tools.uv_options(),
                                       "--no-project", "--python", python])
        self.assertEqual(command[3:6], ["--no-config", "--cache-dir", str(engine_tools.shared_cache_dir() / "uv")])
        self.assertEqual(command[9:11], ["--with", "tree-sitter==0.25.2"])
        self.assertEqual(command[11:15], ["python", "-B", "-X", "faulthandler"])
        self.assertIn(str(report), command)
        # Without the pin, this interpreter, when it holds the engine.
        with mock.patch.object(engine_tools, "uv_binary", side_effect=OSError("no network")), \
                mock.patch.object(shutil, "which", side_effect=AssertionError("the PATH's uv")), \
                mock.patch.object(importlib.util, "find_spec", return_value=object()):
            self.assertEqual(resolve_edges.stage_command(engine_pass.ENGINE_LANGUAGES["python"], self.manifest,
                                                         report)[:4],
                             [sys.executable, "-B", "-X", "faulthandler"])
        # The detached pass itself needs nothing beyond this interpreter.
        self.assertEqual(resolve_edges.engine_command(self.manifest, report)[-3:],
                         ["--pass", "--report-out", str(report)])

    def test_a_background_pass_is_running_while_its_process_lives(self):
        child = mock.Mock(pid=os.getpid())
        with mock.patch.object(engine_pass, "engine_command", return_value=["engine"]), \
                mock.patch.object(engine_pass, "_spawn_detached", return_value=child) as spawn:
            started = resolve_edges.ensure_edges(self.manifest)
            again = resolve_edges.ensure_edges(self.manifest)
        self.assertEqual((started["state"], started["action"]), ("running", "started"))
        self.assertEqual((again["state"], again["action"]), ("running", "none"))
        spawn.assert_called_once()
        self.assertEqual(spawn.call_args.args[0], ["engine"])
        ended = subprocess.Popen([sys.executable, "-c", "pass"])
        ended.wait()
        self.record(pid=ended.pid)
        state = resolve_edges.edge_state(self.manifest)
        self.assertEqual(state["state"], "failed")
        self.assertIn(resolve_edges.LOG_NAME, state["reason"])

    def test_on_windows_the_pass_has_a_console_of_its_own_and_no_window(self):
        """Under DETACHED_PROCESS the interpreter a venv's launcher starts opens a console window, and closing that
        window ends the pass with no word and exit code 0xC000013A: so it ended on Windows 11, 19 November 2026."""
        with mock.patch.object(engine_pass.os, "name", "nt"), mock.patch.object(subprocess, "Popen") as popen:
            engine_pass._spawn_detached(["engine"], None)
        flags = popen.call_args.kwargs["creationflags"]
        self.assertTrue(flags & 0x08000000 and flags & 0x00000200)  # CREATE_NO_WINDOW, CREATE_NEW_PROCESS_GROUP
        self.assertFalse(flags & 0x00000008)  # DETACHED_PROCESS: no console, and CREATE_NO_WINDOW is ignored with it

    def test_a_pass_that_ends_with_no_report_says_the_exit_code_its_starter_saw(self):
        """A pass ended from outside writes nothing: the process that started it keeps how it ended."""
        with mock.patch.object(engine_pass, "engine_command", return_value=[sys.executable, "-c", "raise SystemExit(3)"]):
            started = resolve_edges.ensure_edges(self.manifest)
        self.assertEqual(started["action"], "started")
        deadline = time.monotonic() + 30
        state = resolve_edges.edge_state(self.manifest)
        while "exit code" not in str(state.get("reason")) and time.monotonic() < deadline:
            time.sleep(0.1)
            state = resolve_edges.edge_state(self.manifest)
        self.assertEqual(state["state"], "failed")
        self.assertIn("exit code 3", state["reason"])
        self.assertIn(resolve_edges.LOG_NAME, state["reason"])

    def test_interruption_after_analysis_is_repairable_despite_fresh_edges(self):
        self.run_pass()
        self.record(pid=0, exit_code=17)
        report = self.manifest.with_name(resolve_edges.REPORT_NAME)
        for value in ('{"pass":', "[]", "{}", json.dumps({"pass": True, "pipeline_complete": False,
                                                    "languages": {"python": {"state": "fresh"}}})):
            with self.subTest(value=value):
                report.write_text(value, encoding="utf-8")
                self.assertEqual(resolve_edges.pass_state(self.manifest)["state"], "failed")
                state = resolve_edges.ensure_edges(self.manifest, check=True)
                self.assertEqual((state["state"], state["action"]), ("failed", "reported"))
                self.assertEqual(state["languages"]["python"]["state"], "fresh")
        import pipeline
        child = mock.Mock(pid=0)
        child.wait.return_value = 0
        with mock.patch.object(engine_pass, "_spawn_detached", return_value=child):
            self.assertEqual(resolve_edges.ensure_edges(self.manifest)["action"], "started")
        with mock.patch.object(engine_pass, "_launch", side_effect=AssertionError("the static index is fresh")), \
                mock.patch.object(pipeline.RunAndObserve, "run", return_value={"languages": {}}) as dynamic:
            result = pipeline.run(self.manifest, start="link_calls")
        dynamic.assert_called_once()
        self.assertTrue(result["link_calls"]["pipeline_complete"])
        self.assertEqual(resolve_edges.ensure_edges(self.manifest)["action"], "none")

    def test_the_edge_view_carries_coverage_and_names_a_running_pass(self):
        import edge_view
        self.record(pid=os.getpid(), started_at="2026-11-08T00:00:00Z")
        view = edge_view.load_edge_view(self.manifest)
        self.assertEqual(view["coverage"]["status"], "missing_store")
        self.assertEqual(view["coverage"]["engine_pass"]["state"], "running")
        self.assertTrue(any(gap.startswith("engine pass running") for gap in view["gaps"]), view["gaps"])
        self.assertEqual(view["coverage"]["languages"], {})

    def test_rewriting_a_manifest_first_ends_the_pass_over_its_old_revision(self):
        import contextlib
        import io
        running = self.record(pid=4242)
        partial = self.manifest.with_name(".engine-edges.sqlite.abc.partial")
        partial.write_bytes(b"half a store")
        with mock.patch.object(engine_pass, "_process_alive", return_value=True), \
                mock.patch.object(engine_pass, "_terminate_tree") as terminate, \
                mock.patch.object(resolve_edges, "ensure_edges",
                                  return_value={"state": "running", "edges_store": "x"}), \
                contextlib.redirect_stdout(io.StringIO()):
            code = snapshot.main(["write", str(self.root), "--out", str(self.manifest), "--no-index",
                                  "--no-modules"])
        self.assertEqual(code, 0)
        terminate.assert_called_once_with(4242)
        self.assertFalse(running.exists())
        self.assertFalse(partial.exists())

    def test_snapshot_write_starts_the_pass_unless_told_not_to(self):
        import contextlib
        import io
        out = self.root.parent / "written.sqlite"
        for options, calls in (([], 1), (["--no-engine"], 0)):
            with self.subTest(options=options), \
                    mock.patch.object(resolve_edges, "ensure_edges",
                                      return_value={"state": "running", "edges_store": "x"}) as ensure, \
                    contextlib.redirect_stdout(io.StringIO()):
                code = snapshot.main(["write", str(self.root), "--out", str(out), "--no-index",
                                      "--no-modules", *options])
            self.assertEqual(code, 0)
            self.assertEqual(ensure.call_count, calls)
            if calls:
                self.assertEqual(ensure.call_args.args, (out,))


class PreparedEnvironmentTests(unittest.TestCase):
    """The project's declared packages, read from its manifests and installed outside it, from wheels only."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        (self.root / "api").mkdir(parents=True)
        (self.root / "pyproject.toml").write_text(
            '[project]\nname = "proj"\ndependencies = ["httpx>=0.27"]\n'
            '[project.optional-dependencies]\ndev = ["pytest"]\n[dependency-groups]\nlint = ["ruff==0.6.0"]\n',
            encoding="utf-8")
        (self.root / "api/requirements.txt").write_text(
            "fastapi==0.115.0  # web\n-e .\n./local\n-r other.txt\ngit+https://example.org/x.git\n"
            "tool @ file:///tmp/tool\n\n# note\n", encoding="utf-8")
        self.names = ["pyproject.toml", "api/requirements.txt", "api/app.py"]
        self.cache = Path(self.temp.name).resolve() / "cache"
        self.commands, self.refused, self.cwds = [], None, []
        # Daodan's own uv: no configuration file read (the project's, the user's), its cache Daodan's.
        self.own = ["--no-config", "--cache-dir", str(self.cache / "uv")]

    def run_uv(self, command, **kwargs):
        self.commands.append(command[1:])
        self.cwds.append(kwargs.get("cwd"))
        if command[1] == "venv":
            if self.refused:
                return subprocess.CompletedProcess(command, 2, "", self.refused)
            Path(command[2]).mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, "", "")

    def prepare(self, python=None, names=None):
        with mock.patch.object(engine_tools, "shared_cache_dir", return_value=self.cache), \
                mock.patch.object(engine_tools, "uv_binary", return_value=Path("uv")), \
                mock.patch.object(subprocess, "run", side_effect=self.run_uv):
            return resolve_edges.python_environment(self.root, names or self.names, python)

    def test_only_package_lines_are_declared_requirements(self):
        manifests = resolve_edges.python_manifests(self.root, self.names)
        self.assertEqual(manifests, ["api/requirements.txt", "pyproject.toml"])
        self.assertEqual(resolve_edges._declared_requirements(self.root, manifests, "uv"),
                         ["fastapi==0.115.0", "httpx>=0.27", "pytest", "ruff==0.6.0"])

    def test_uv_is_daodan_s_pin_checked_against_its_release_and_never_the_path_s(self):
        """The uv on the PATH comes from a release Daodan cannot vouch for: uv is the pin the pre-map and the
        containers use, downloaded once into the shared directory and checked against the release's sha256; a
        platform without a pinned build has none."""
        import tarfile
        import preparation
        from premap import uv as pinned
        self.assertEqual(engine_tools.UV_VERSION, pinned.VERSION)
        self.assertEqual(preparation.UV[:2], (f"https://github.com/astral-sh/uv/releases/download/{pinned.VERSION}/"
                                              f"{engine_tools.UV_ASSETS['linux-x64'][0]}",
                                              engine_tools.UV_ASSETS["linux-x64"][1]))
        fetched = []

        def download(url, target, *, sha256=None, sha1_url=None):
            fetched.append((url, sha256))
            source = target.parent / "uv-x86_64-unknown-linux-gnu" / engine_tools.executable_name("uv")
            source.parent.mkdir(parents=True)
            source.write_text("#!/bin/sh\n", encoding="utf-8")
            with tarfile.open(target, "w:gz") as archive:
                archive.add(source.parent, arcname=source.parent.name)
            shutil.rmtree(source.parent)
            return target

        with mock.patch.object(engine_tools, "shared_cache_dir", return_value=self.cache), \
                mock.patch.object(engine_tools, "_platform", return_value="linux-x64"), \
                mock.patch.object(engine_tools, "download", side_effect=download), \
                mock.patch.object(shutil, "which", side_effect=AssertionError("the PATH's uv")):
            self.assertIsNone(engine_tools.uv_binary(fetch=False))
            first, again = engine_tools.uv_binary(), engine_tools.uv_binary()
            with mock.patch.object(engine_tools, "_platform", return_value="win-arm64"):
                shutil.rmtree(self.cache / "engines/uv")
                with self.assertRaisesRegex(OSError, f"no uv {engine_tools.UV_VERSION} build for win-arm64"):
                    engine_tools.uv_binary()
        asset, digest = engine_tools.UV_ASSETS["linux-x64"]
        self.assertEqual(fetched, [(f"https://github.com/astral-sh/uv/releases/download/{engine_tools.UV_VERSION}/"
                                    f"{asset}", digest)])
        self.assertEqual(first, again)
        self.assertEqual(first, self.cache / "engines/uv" / engine_tools.UV_VERSION / engine_tools.executable_name("uv"))

    def test_two_first_downloads_of_the_pinned_uv_at_once_both_end_with_it(self):
        """As every pinned release: each download fills its own folder, the first published wins."""
        import contextlib
        import io
        import tarfile
        calls = []

        def download(url, target, *, sha256=None, sha1_url=None):
            calls.append(target.parent)
            source = target.parent / "uv-x86_64-unknown-linux-gnu" / engine_tools.executable_name("uv")
            source.parent.mkdir(parents=True)
            source.write_text(f"#!/bin/sh\n# {len(calls)}\n", encoding="utf-8")
            with tarfile.open(target, "w:gz") as archive:
                archive.add(source.parent, arcname=source.parent.name)
            shutil.rmtree(source.parent)
            if len(calls) == 1:  # the other process, done while this one is half-way
                engine_tools.uv_binary()
            return target

        with mock.patch.object(engine_tools, "shared_cache_dir", return_value=self.cache), \
                mock.patch.object(engine_tools, "_platform", return_value="linux-x64"), \
                mock.patch.object(engine_tools, "download", side_effect=download), \
                contextlib.redirect_stdout(io.StringIO()):
            binary = engine_tools.uv_binary()
        self.assertEqual(len(set(calls)), 2)
        self.assertIn("# 2", binary.read_text(encoding="utf-8"))  # the first one published
        self.assertEqual(sorted(path.name for path in binary.parent.parent.iterdir()), [engine_tools.UV_VERSION])

    def test_a_lock_is_exported_by_daodan_s_own_uv_and_nothing_is_built(self):
        """uv reads the lock as it is (`--frozen`), builds nothing (`--no-build`), reads no configuration file and
        keeps its cache in Daodan's shared directory."""
        (self.root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
        exported = []

        def export(command, **kwargs):
            exported.append(command[1:])
            return subprocess.CompletedProcess(command, 0, "httpx==0.27.2\n", "")

        with mock.patch.object(engine_tools, "shared_cache_dir", return_value=self.cache), \
                mock.patch.object(subprocess, "run", side_effect=export):
            requirements = resolve_edges._declared_requirements(self.root, ["pyproject.toml", "uv.lock"], "uv")
        self.assertEqual(requirements, ["httpx==0.27.2"])
        [command] = exported
        self.assertEqual(command[:2], ["export", "--frozen"])
        self.assertIn("--no-build", command)
        self.assertEqual(command[-3:], self.own)

    def test_a_package_without_a_wheel_is_a_failure_naming_it_and_nothing_is_built(self):
        """`--only-binary :all:` on every install: uv builds no source distribution and runs none of its code. A
        package that has no wheel is not installed; the environment records it with uv's words."""
        def refused(command, **kwargs):
            done = self.run_uv(command, **kwargs)
            if command[1:3] == ["pip", "install"]:
                self.assertIn(":all:", command[command.index("--only-binary") + 1:][:1])
                if "-r" in command or "fastapi==0.115.0" in command:
                    return subprocess.CompletedProcess(command, 1, "", "  x No solution found\n  hint: Wheels are "
                                                       "required for `fastapi` because building from source is "
                                                       "disabled for all packages")
            return done

        with mock.patch.object(engine_tools, "shared_cache_dir", return_value=self.cache), \
                mock.patch.object(engine_tools, "uv_binary", return_value=Path("uv")), \
                mock.patch.object(subprocess, "run", side_effect=refused):
            environment = resolve_edges.python_environment(self.root, self.names)
        built = json.loads((environment / "daodan-environment.json").read_text(encoding="utf-8"))
        self.assertEqual(built["installed"], 3)
        self.assertEqual(built["failed"], [{"requirement": "fastapi==0.115.0", "cause": "x No solution found hint: "
                                            "Wheels are required for `fastapi` because building from source is "
                                            "disabled for all packages"}])

    def test_the_environment_is_built_once_outside_the_project_from_wheels(self):
        before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        first = self.prepare()
        self.assertTrue(first.is_relative_to(self.cache / "python"))
        install = next(command for command in self.commands if command[:2] == ["pip", "install"])
        self.assertIn("--only-binary", install)
        self.assertEqual(sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*")), before)
        count = len(self.commands)
        self.assertEqual(self.prepare(), first)
        self.assertEqual(len(self.commands), count)

    def test_changed_manifests_build_another_environment_and_none_declared_builds_none(self):
        first = self.prepare()
        (self.root / "api/requirements.txt").write_text("fastapi==0.116.0\n", encoding="utf-8")
        self.assertNotEqual(self.prepare(), first)
        self.assertIsNone(resolve_edges.python_environment(self.root, ["api/app.py"]))

    def test_a_python_the_project_states_is_the_one_uv_resolves_for_its_environment(self):
        """The Python the run's folder states where Daodan's interpreter is not one it admits: uv resolves the
        statement as `uv sync` does (an installed Python that matches, else its download) into another
        environment, which a project that declares no package gets too. What uv cannot provide fails with its
        words."""
        own = self.prepare()
        stated = self.prepare(">=3.14,<4.0")
        self.assertNotEqual(stated, own)
        self.assertEqual([command for command in self.commands if command[0] == "venv"][-1],
                         ["venv", str(stated), "--python", ">=3.14,<4.0", *self.own])
        self.assertEqual(self.prepare(">=3.14,<4.0"), stated)
        bare = self.prepare("3.14", ["api/app.py"])
        self.assertTrue(bare.is_relative_to(self.cache / "python"))
        self.assertEqual(self.commands[-1], ["venv", str(bare), "--python", "3.14", *self.own])  # nothing to install
        self.refused = "error: No interpreter found for Python 3.99 in managed installations or search path"
        with self.assertRaisesRegex(subprocess.SubprocessError, "uv could not provide Python 3.99: error: No interp"):
            self.prepare("3.99")

    def test_what_an_interpreter_would_run_from_the_environment_is_removed_before_uv_starts_it(self):
        """AGENTS.md: the project's code never runs on the host. uv starts the environment's interpreter at each
        install (`-I`: with `site`), the analyzers to ask it its paths: a `.pth` file's import lines and
        `sitecustomize`, which a wheel may install, would run. They are removed before each install and after the
        last, and from an environment built before, when it is used again; the folders a `.pth` file names stay.
        uv runs outside the project: a configuration of the project's (a mirror for the interpreter it downloads)
        is not read."""
        seen, run = [], self.run_uv

        def installed(command, **kwargs):
            done = run(command, **kwargs)
            if command[1:3] != ["pip", "install"]:
                return done
            site = Path(command[command.index("--python") + 1]) / "lib/python3.13/site-packages"
            seen.append({path.name: path.read_text(encoding="utf-8") for path in site.glob("*")})
            if "-r" in command:  # the whole list fails: one at a time
                return subprocess.CompletedProcess(command, 1, "", "no wheel for one")
            site.mkdir(parents=True, exist_ok=True)
            (site / "mark.pth").write_text("import mark_hook\n# a note\nextra\n\timport kept\n", encoding="utf-8")
            (site / "sitecustomize.py").write_text("import mark_hook\n", encoding="utf-8")
            return done

        self.run_uv = installed
        environment = self.prepare()
        inert = {"mark.pth": "# a note\nextra\n\timport kept\n"}
        self.assertEqual(seen, [{}, {}, inert, inert, inert])  # the list, then its four requirements one at a time
        site = environment / "lib/python3.13/site-packages"
        self.assertEqual({path.name: path.read_text(encoding="utf-8") for path in site.iterdir()}, inert)
        (site / "mark.pth").write_text("﻿import old\nkept\n", encoding="utf-8")  # an environment built before
        (site / "sitecustomize").mkdir()
        self.run_uv = run
        self.assertEqual(self.prepare(), environment)
        self.assertEqual({path.name: path.read_text(encoding="utf-8") for path in site.iterdir()},
                         {"mark.pth": "kept\n"})
        self.assertEqual({cwd and Path(cwd) for cwd in self.cwds}, {self.cache / "python"})
        self.assertEqual({tuple(command[-3:]) for command in self.commands}, {tuple(self.own)})


class MultiLanguageTests(unittest.TestCase):
    """One store with one entry per language, written by one engine at a time."""

    SOURCES = {
        "app/use.py": "class User:\n    def go(self, helper):\n        return helper.run()\n",
        "app/tool.py": "class Tool:\n    def run(self):\n        return 1\n",
        "web/tool.ts": ("export class Tool {\n  run(): number { return 1; }\n}\n"
                        "export function make(a: string): Tool;\nexport function make(a: number): Tool;\n"
                        "export function make(a: any): Tool { return new Tool(); }\n"),
        "web/use.ts": ("import { Tool } from './tool';\nexport function go(tool: Tool) {\n  return tool.run();\n}\n"
                       "const twice = (t: Tool) => t.run();\nfoo().bar();\n"),
    }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        for rel, text in self.SOURCES.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.manifest = self.root.parent / "manifest.sqlite"
        snapshot.read_project(self.root, self.manifest)

    def declarations(self, rel):
        with open_snapshot(self.manifest) as store:
            return {(row[0], row[1]): _unpack(row[2]) for row in store.connection.execute(
                "SELECT name, kind, payload FROM sem_declarations WHERE file=? AND kind IN "
                "('function','method','class')", (rel,))}

    def test_tree_sitter_declarations_record_where_an_engine_names_them(self):
        tool = self.declarations("web/tool.ts")
        self.assertEqual(tool[("Tool", "class")]["name_span"][:2], [1, 13])
        self.assertEqual(tool[("run", "method")]["name_span"][:2], [2, 2])
        make = tool[("make", "function")]
        self.assertEqual(make["name_span"][:2], [6, 16])
        self.assertEqual([span[:2] for span in make["signature_spans"]], [[4, 16], [5, 16]])
        # An arrow function is named where its variable is.
        self.assertEqual(self.declarations("web/use.ts")[("twice", "function")]["name_span"][:2], [5, 6])

    def test_a_call_on_a_computed_value_keeps_its_member_name(self):
        with open_snapshot(self.manifest) as store:
            calls = [_unpack(row[0]) for row in store.connection.execute(
                "SELECT payload FROM sem_references WHERE file='web/use.ts' AND kind='call'")]
        bar = next(call for call in calls if call["parts"][-1:] == ["bar"])
        self.assertEqual((bar["parts"], bar["reason"]), (["(expr)", "bar"], "dynamic-callee"))

    def test_an_overload_signature_names_its_implementation(self):
        with open_snapshot(self.manifest) as store:
            table, ambiguous = resolve_edges.symbol_table(
                store.connection, "web/tool.ts", self.SOURCES["web/tool.ts"])
        implementation = table[(6, 16)]
        self.assertEqual(implementation[1], "function")
        self.assertEqual((table[(4, 16)], table[(5, 16)]), (implementation, implementation))
        self.assertEqual(ambiguous, set())

    def test_each_engine_keeps_the_entries_of_the_other_languages(self):
        store = resolve_edges.default_edge_store(self.manifest)
        python = {("app/use.py", 3): [end("app/tool.py", "run", 2)]}
        write_answers(self.manifest, store, python, languages=("python",))
        write_answers(self.manifest, store, {("web/use.ts", 3): [end("web/tool.ts", "run", 2)]},
                      resolver="tsstub@1.0", languages=("typescript",))
        write_answers(self.manifest, store, python, languages=("python",))
        with open_snapshot(self.manifest) as store:
            edges, binding, reason = resolve_edges.read_edge_store(
                resolve_edges.default_edge_store(self.manifest), store)
        self.assertIsNone(reason, reason)
        self.assertEqual({edge["language"]: edge["resolver"] for edge in edges},
                         {"python": "stub@1.0", "typescript": "tsstub@1.0"})
        self.assertEqual({language: entry["engine"] for language, entry in binding["languages"].items()},
                         {"python": "stub@1.0", "typescript": "tsstub@1.0"})
        self.assertEqual(sorted(language for language, entry in binding["languages"].items() if entry["coverage"]),
                         ["python", "typescript"])

    def stage_runner(self, outcomes, calls):
        """A fake `subprocess.run` writing each stage's report as the stage would."""
        def run(command, **_options):
            name, report = command[0], Path(command[1])
            calls.append(name)
            if outcomes[name] is not None:
                report.write_text(json.dumps(outcomes[name]), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0 if outcomes[name] else 1)
        return run

    def run_whole_pass(self, outcomes, free=8 * 2**30):
        calls = []
        report = self.manifest.with_name(resolve_edges.REPORT_NAME)
        with mock.patch.object(engine_pass, "stage_command",
                               side_effect=lambda spec, manifest, path, offline=False:
                               [spec.name, str(path)]), \
                mock.patch.object(engine_pass, "cached_offline", return_value=False), \
                mock.patch.object(subprocess, "run", side_effect=self.stage_runner(outcomes, calls)), \
                mock.patch.object(engine_pass, "free_memory", return_value=free):
            result = resolve_edges.run_pass(self.manifest, report)
        return result, calls

    def test_the_pass_runs_one_engine_at_a_time_and_records_each_language(self):
        result, calls = self.run_whole_pass({
            "scip-python": {"available": True, "engine": "scip-python@0.6.8",
                            "languages": {"python": {"state": "fresh"}}},
            "scip-typescript": {"available": False, "reason": "node and npm are needed",
                           "install": "install Node.js 18 or later with npm (https://nodejs.org)"}})
        self.assertEqual(calls, ["scip-python", "scip-typescript"])  # the lightest first
        self.assertEqual(result["languages"]["python"], {"state": "fresh", "engine": "scip-python@0.6.8"})
        self.assertEqual(result["languages"]["typescript"]["state"], "unavailable")
        self.assertIn("Node.js", result["languages"]["typescript"]["install"])
        state = resolve_edges.edge_state(self.manifest)
        self.assertEqual(state["languages"]["typescript"]["state"], "unavailable")
        # No store was written by the fake stages, so Python reads as not yet passed.
        self.assertEqual(state["state"], "missing")

    def test_an_engine_that_runs_out_of_memory_starts_no_other(self):
        result, calls = self.run_whole_pass({
            "scip-python": {"available": False, "reason": "MemoryError in scip-python",
                            "memory_exhausted": True},
            "scip-typescript": {"available": True}})
        self.assertEqual(calls, ["scip-python"])
        self.assertEqual(result["languages"]["python"]["state"], "failed")
        self.assertEqual(result["languages"]["typescript"],
                         {"state": "failed", "engine": "scip-typescript",
                          "reason": "not started: the scip-python engine ran out of memory"})

    def test_an_engine_waits_for_free_memory(self):
        result, calls = self.run_whole_pass({"scip-python": None, "scip-typescript": None}, free=2**30)
        self.assertEqual(calls, [])
        self.assertTrue(all(outcome["state"] == "failed" and "GB of memory free" in outcome["reason"]
                            for outcome in result["languages"].values()), result)
        self.assertEqual(resolve_edges.edge_state(self.manifest)["state"], "failed")

    def test_a_stage_without_a_report_failed_and_says_where_to_look(self):
        result, _calls = self.run_whole_pass({"scip-python": None, "scip-typescript": {"available": True}})
        self.assertEqual(result["languages"]["python"]["state"], "failed")
        self.assertIn(resolve_edges.LOG_NAME, result["languages"]["python"]["reason"])


class DigestTests(unittest.TestCase):
    """A file's digest moves with what it imports: the index cache's inputs (`engine_pass._inputs`)."""

    def test_digests_follow_imports_and_cycles(self):
        hashes = {"a": "1", "b": "2", "c": "3", "d": "4"}
        dependencies = {"a": {"b"}, "b": {"a", "c"}, "d": set()}
        import code_graph
        before = code_graph.dependency_digests(hashes, dependencies)
        self.assertEqual(before["a"], before["b"])
        after = code_graph.dependency_digests({**hashes, "c": "changed"}, dependencies)
        self.assertNotEqual(after["a"], before["a"])
        self.assertNotEqual(after["c"], before["c"])
        self.assertEqual(after["d"], before["d"])


class ContractTests(unittest.TestCase):
    """Calls that go through a type's contract arrive at it; a value holder is never a target."""

    TYPES = "\n".join([
        "export interface Client {",
        "  get(url: string): string;",
        "  post: (url: string) => string;",
        "  json: { <T>(): T; raw(): string };",
        "  timeout: number;",
        "}",
        "export type Factory = {",
        "  (base: string): Client;",
        "};",
        "export class Box {",
        "  constructor(size: number) {}",
        "}",
        "export const box = new Box(1);",
        "",
    ])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        self.root.mkdir()
        (self.root / "types.ts").write_text(self.TYPES, encoding="utf-8")
        self.manifest = self.root.parent / "manifest.sqlite"
        snapshot.read_project(self.root, self.manifest)
        self.lines = self.TYPES.split("\n")

    def at(self, line, text, offset=0):
        return line, self.lines[line - 1].index(text) + offset

    def table(self):
        with open_snapshot(self.manifest) as store:
            return resolve_edges.symbol_table(store.connection, "types.ts", self.TYPES)

    def test_callable_members_of_interfaces_and_types_are_contracts(self):
        table, ambiguous = self.table()
        self.assertEqual(ambiguous, set())
        for position in (self.at(2, "get"), self.at(3, "post"), self.at(4, "raw"), self.at(8, "(")):
            with self.subTest(position=position):
                self.assertEqual(table[position][1], "function")
        # A property's own call signature names the property.
        self.assertEqual(table[self.at(4, "<")], table[self.at(4, "json")])
        self.assertEqual(table[self.at(5, "timeout")][1], "binding")

    def test_a_constructor_names_its_class(self):
        table, _ambiguous = self.table()
        self.assertEqual(table[self.at(11, "constructor")], table[self.at(10, "Box")])

    def test_contracts_are_never_lexical_bindings(self):
        with open_snapshot(self.manifest) as store:
            rows = [_unpack(row[0]) for row in store.connection.execute(
                "SELECT payload FROM sem_declarations WHERE kind IN ('method','property')")]
        contracts = [row for row in rows if row.get("contract") or row["kind"] == "property"]
        self.assertTrue(contracts)
        self.assertTrue(all(row.get("lexical") is False for row in contracts), contracts)
        self.assertIn("Client.get", {row["qualified_name"] for row in contracts})


class OfflineStageTests(unittest.TestCase):
    def test_a_cached_stage_runs_uv_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest, report = Path(temp) / "manifest.sqlite", Path(temp) / "report.json"
            spec = resolve_edges.ENGINES[1]
            asked = []

            def run(command, **kwargs):
                asked.append(kwargs.get("cwd"))
                return subprocess.CompletedProcess(command, 0)

            with mock.patch.object(engine_tools, "uv_binary", return_value=Path("uv")), \
                    mock.patch.object(subprocess, "run", side_effect=run):
                online = resolve_edges.stage_command(spec, manifest, report)
                offline = resolve_edges.stage_command(spec, manifest, report, offline=True)
                self.assertTrue(engine_pass.cached_offline(spec, manifest, report))
            self.assertNotIn("--offline", online)
            self.assertEqual(offline[:8], ["uv", "run", "--quiet", *engine_tools.uv_options(), "--no-project",
                                           "--offline"])
            self.assertEqual(asked, [str(engine_pass.SCRIPT_DIR)])  # outside the project, as the stage runs


class ToolMirrorTests(unittest.TestCase):
    """A tool the pass runs on the host (`indexers/runtime.py`): its install, published whole, and its mirror."""

    def test_two_first_installs_of_one_release_at_once_both_end_with_it_installed(self):
        """The pass and a worker may install one pinned release at once (Node, scip-python): each fills its own
        folder, the first published wins, the other's is dropped and no install fails."""
        import contextlib
        import io
        from indexers import runtime
        with tempfile.TemporaryDirectory() as temp:
            engine, other = (runtime.Tool(Path(temp), "tool", "1") for _ in "12")
            engine.install_root = other.install_root = Path(temp) / "engines"
            home = engine.home()

            def fill(partial, inner=True):
                (partial / "tool").write_text("one" if inner else "two", encoding="utf-8")
                if inner:  # the other process, done while this one is half-way
                    other._install(home, lambda folder: fill(folder, inner=False))
                (partial / "more").write_text("x", encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                engine._install(home, fill)
            self.assertTrue((home / ".installed").is_file())
            self.assertEqual((home / "tool").read_text(encoding="utf-8"), "two")  # the first one published
            self.assertEqual(sorted(path.name for path in home.parent.iterdir()), ["1"])

    def test_the_mirror_links_the_project_and_its_removal_leaves_every_target_intact(self):
        from indexers import runtime
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "proj"
            (root / "src/deep").mkdir(parents=True)
            (root / "src/deep/a.ts").write_text("export const a = 1;\n", encoding="utf-8")
            (root / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
            modules = Path(temp) / "shared/node_modules/pkg"
            modules.mkdir(parents=True)
            (modules / "index.d.ts").write_text("export declare const p: number;\n", encoding="utf-8")
            with runtime.mirrored(runtime.Tool(root, "tool", "1"), {"node_modules": modules.parent}) as mirror:
                self.assertEqual((mirror / "src/deep/a.ts").read_text(encoding="utf-8"), "export const a = 1;\n")
                self.assertTrue((mirror / "node_modules/pkg/index.d.ts").is_file())
            self.assertFalse(mirror.exists())
            self.assertTrue((root / "src/deep/a.ts").is_file())
            self.assertTrue((modules / "index.d.ts").is_file())
            self.assertEqual(sorted(path.name for path in root.iterdir()), ["package.json", "src"])

    def test_a_link_below_the_root_makes_its_parents_real_directories_without_writing_into_the_project(self):
        from indexers import runtime
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve() / "proj"
            (root / "web/src").mkdir(parents=True)
            (root / "web/src/a.ts").write_text("export const a = 1;\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs/readme.md").write_text("# Docs\n", encoding="utf-8")
            modules = Path(temp).resolve() / "shared/node_modules"
            (modules / "left").mkdir(parents=True)
            (modules / "left/index.d.ts").write_text("export declare const l: number;\n", encoding="utf-8")
            with runtime.mirrored(runtime.Tool(root, "tool", "1"), {"web/node_modules": modules}) as mirror:
                self.assertTrue((mirror / "web/node_modules/left/index.d.ts").is_file())
                self.assertEqual((mirror / "web/src/a.ts").read_text(encoding="utf-8"), "export const a = 1;\n")
                self.assertTrue((mirror / "docs/readme.md").is_file())
                self.assertFalse((root / "web/node_modules").exists())
            self.assertFalse(mirror.exists())
            self.assertTrue((root / "web/src/a.ts").is_file())
            self.assertTrue((modules / "left/index.d.ts").is_file())


class MavenArtifactTests(unittest.TestCase):
    def test_a_maven_jar_on_disk_is_reused_and_a_download_is_verified(self):
        import io
        payload = b"jar bytes"
        with tempfile.TemporaryDirectory() as temp,                 mock.patch.object(engine_tools, "shared_cache_dir", return_value=Path(temp) / "cache"),                 mock.patch.object(Path, "home", return_value=Path(temp) / "home"):
            local = Path(temp) / "home/.m2/repository/org/demo/lib/1.0/lib-1.0.jar"
            local.parent.mkdir(parents=True)
            local.write_bytes(payload)
            with mock.patch("urllib.request.urlopen") as urlopen:
                self.assertEqual(resolve_edges.maven_artifact("org.demo:lib:1.0"), local)
            urlopen.assert_not_called()

            def answer(request, timeout):
                digest = hashlib.sha1(payload).hexdigest().encode()
                return io.BytesIO(digest if request.full_url.endswith(".sha1") else payload)

            with mock.patch("urllib.request.urlopen", side_effect=answer):
                fetched = resolve_edges.maven_artifact("org.demo:other:2.0")
            self.assertEqual(fetched, resolve_edges.maven_central_dir() / "org/demo/other/2.0/other-2.0.jar")
            self.assertEqual(fetched.read_bytes(), payload)
            with mock.patch("urllib.request.urlopen", side_effect=lambda request, timeout: io.BytesIO(
                    b"0" * 40 if request.full_url.endswith(".sha1") else payload)),                     mock.patch.object(time, "sleep"):
                with self.assertRaises(ValueError):
                    resolve_edges.maven_artifact("org.demo:broken:3.0")
            self.assertFalse((resolve_edges.maven_central_dir() / "org/demo/broken/3.0/broken-3.0.jar").exists())

    def test_a_pinned_sha256_is_checked_beside_maven_central_s_sha1(self):
        """A jar whose sha1 Maven Central confirms but whose sha256 is not the pinned one is refused, and a jar on
        disk with another sha256 is not reused."""
        import io
        payload = b"jar bytes"

        def answer(request, timeout):
            return io.BytesIO(hashlib.sha1(payload).hexdigest().encode() if request.full_url.endswith(".sha1")
                              else payload)

        with tempfile.TemporaryDirectory() as temp, \
                mock.patch.object(engine_tools, "shared_cache_dir", return_value=Path(temp) / "cache"), \
                mock.patch.object(Path, "home", return_value=Path(temp) / "home"):
            local = Path(temp) / "home/.m2/repository/org/demo/lib/1.0/lib-1.0.jar"
            local.parent.mkdir(parents=True)
            local.write_bytes(b"another build of the jar")
            with mock.patch("urllib.request.urlopen", side_effect=answer):
                fetched = resolve_edges.maven_artifact("org.demo:lib:1.0", hashlib.sha256(payload).hexdigest())
            self.assertEqual(fetched, resolve_edges.maven_central_dir() / "org/demo/lib/1.0/lib-1.0.jar")
            with mock.patch("urllib.request.urlopen", side_effect=answer), mock.patch.object(time, "sleep"):
                with self.assertRaises(ValueError):
                    resolve_edges.maven_artifact("org.demo:other:2.0", "0" * 64)
            self.assertFalse((resolve_edges.maven_central_dir() / "org/demo/other/2.0/other-2.0.jar").exists())

    def test_two_downloads_of_one_file_at_once_both_end_with_it(self):
        """Two processes may fetch one file into the shared directory at once (a Maven jar): each writes a partial
        file of its own, verified, and neither retries nor fails."""
        import io
        payload, fetched = b"jar bytes", []
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "lib.jar"

            class Response(io.BytesIO):
                def read(self, size=-1):
                    if len(fetched) == 1 and self.tell() == 0:  # the other process, done while this one is half-way
                        resolve_edges.download("https://repo.example/lib.jar", target, sha256=digest)
                    return super().read(size)

            def opened(request, timeout=None):
                fetched.append(request.full_url)
                return Response(payload)

            with mock.patch("urllib.request.urlopen", side_effect=opened), mock.patch.object(time, "sleep"):
                self.assertEqual(resolve_edges.download("https://repo.example/lib.jar", target, sha256=digest),
                                 target)
            self.assertEqual(len(fetched), 2)
            self.assertEqual(target.read_bytes(), payload)
            self.assertEqual([path.name for path in target.parent.iterdir()], ["lib.jar"])


class RustGoContractTests(unittest.TestCase):
    """A method with no body, an interface's or a trait's, is a contract; an enum variant builds through its name."""

    def table(self, name, source):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "proj"
            root.mkdir()
            (root / name).write_text(source, encoding="utf-8")
            manifest = Path(temp) / "manifest.sqlite"
            snapshot.read_project(root, manifest)
            with open_snapshot(manifest) as store:
                return resolve_edges.symbol_table(store.connection, name, source)

    def test_go_interface_methods_are_contracts(self):
        source = "package demo\n\ntype Router interface {\n\tRoute(pattern string)\n\tRoutes() []string\n}\n"
        table, ambiguous = self.table("demo.go", source)
        self.assertEqual(ambiguous, set())
        self.assertEqual(table[(4, source.split("\n")[3].index("Route"))][1], "function")
        self.assertEqual(table[(5, source.split("\n")[4].index("Routes"))][1], "function")

    def test_rust_trait_signatures_and_enum_variants_are_contracts(self):
        source = ("pub trait Tool {\n    fn run(&self) -> u32;\n    fn name(&self) -> u32 { 1 }\n}\n\n"
                  "pub enum Code {\n    Message(String),\n    Eof,\n}\n")
        lines = source.split("\n")
        table, ambiguous = self.table("lib.rs", source)
        self.assertEqual(ambiguous, set())
        for line, text in ((2, "run"), (3, "name"), (7, "Message")):
            with self.subTest(text=text):
                self.assertEqual(table[(line, lines[line - 1].index(text))][1], "function")


class NativeToolchainTests(unittest.TestCase):
    def test_downloads_name_daodan_as_their_agent(self):
        # The Temurin API answers 403 to Python's default agent: Kotlin had no engine on a machine without Java.
        import io
        import urllib.request
        agents = []

        def opened(request, timeout=None):
            agents.append(request.get_header("User-agent") if isinstance(request, urllib.request.Request) else None)
            return io.BytesIO(b"jar")

        with tempfile.TemporaryDirectory() as temp, mock.patch("urllib.request.urlopen", side_effect=opened):
            resolve_edges.download("https://repo.example/a.jar", Path(temp) / "a.jar")
            with resolve_edges.open_url("https://api.example/jre", timeout=5) as response:
                self.assertEqual(response.read(), b"jar")
        self.assertEqual(agents, [resolve_edges.USER_AGENT, resolve_edges.USER_AGENT])
        self.assertFalse(resolve_edges.USER_AGENT.startswith("Python-urllib"))

    def test_a_mirror_keeps_what_the_tool_writes_out_of_the_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "proj"
            (root / "src").mkdir(parents=True)
            (root / "src/lib.rs").write_bytes(b"pub fn a() {}\n")
            (root / "Cargo.toml").write_text('[package]\nname = "demo"\n', encoding="utf-8")
            (root / ".git").mkdir()
            from indexers import runtime
            with runtime.mirrored(runtime.Tool(root, "rust-analyzer", "1")) as mirror:
                self.assertFalse((mirror / ".git").exists())
                (mirror / "Cargo.lock").write_text("lock", encoding="utf-8")
                self.assertEqual((mirror / "src/lib.rs").read_bytes(), b"pub fn a() {}\n")
            self.assertFalse(mirror.exists())
            self.assertEqual(sorted(path.name for path in root.iterdir()), [".git", "Cargo.toml", "src"])
            self.assertTrue((root / "src/lib.rs").is_file())


class PositionUnitTests(unittest.TestCase):
    def test_positions_convert_explicitly_between_units(self):
        line = 'x = "é😀"; run()'
        byte = len(line[:line.index("run")].encode("utf-8"))
        self.assertEqual(resolve_edges.byte_to_char(line, byte), line.index("run"))
        self.assertEqual(resolve_edges.byte_to_utf16(line, byte), line.index("run") + 1)
        self.assertEqual(resolve_edges.utf16_to_byte(line, line.index("run") + 1), byte)
        self.assertEqual(resolve_edges.char_to_byte(line, line.index("run")), byte)
        # A byte inside a character and a unit inside a surrogate pair name no position.
        self.assertIsNone(resolve_edges.byte_to_char(line, line.index("é") + 1))
        self.assertIsNone(resolve_edges.utf16_to_byte(line, line.index("😀") + 1))


class CalleePositionTests(unittest.TestCase):
    def test_the_callee_name_is_probed_not_the_receiver(self):
        line = "        return helper.run()"
        start = line.index("helper")
        span = [2, start, 2, start + len("helper.run")]
        self.assertEqual(resolve_edges.callee_column(line, span, "run"),
                         start + len("helper."))

    def test_a_name_outside_its_own_span_is_not_probed_at_a_guess(self):
        line = "        return helper.run()"
        start = line.index("helper")
        span = [2, start, 2, start + len("helper")]
        self.assertIsNone(resolve_edges.callee_column(line, span, "run"))


class LexicalCheckTests(unittest.TestCase):
    """The store answers the calls the lexical resolver bound too, and its answer wins."""

    SOURCES = {
        "app/use.py": "from app.tool import free\n\n\ndef go():\n    return free()\n",
        "app/tool.py": "def free():\n    return 2\n\n\ndef other():\n    return 3\n",
    }
    setUp = EdgeStoreTests.setUp
    references = EdgeStoreTests.references

    def bound_call(self):
        for identity, resolution, payload in self.references():
            if resolution == "resolved" and payload["parts"] == ["free"]:
                return identity, payload["span"][0]
        raise AssertionError("the lexical resolver did not bind the call")

    def declaration(self, name):
        with open_snapshot(self.manifest) as store:
            return store.connection.execute(
                "SELECT id FROM sem_declarations WHERE file='app/tool.py' AND name=?", (name,)).fetchone()[0]

    def check(self, ends):
        """The view and the bound call's reference under the store's ends there."""
        import edge_view
        identity, line = self.bound_call()
        write_answers(self.manifest, self.edges, {("app/use.py", line): ends} if ends else {})
        with open_snapshot(self.manifest) as store:
            view = edge_view.load_edge_view(store, engine_store=self.edges)
        self.assertEqual(view["conflicts"], [])
        return view, {item["id"]: item for item in view["references"]}[identity]

    def test_the_same_answer_adds_the_engine_to_the_provenance(self):
        view, reference = self.check([end("app/tool.py", "free", 1)])
        self.assertEqual(reference["target_id"], self.declaration("free"))
        self.assertEqual(reference["provenance"], [resolve_edges.resolution.LEXICAL_RESOLVER, "stub@1.0"])
        self.assertEqual(view["coverage"]["languages"]["python"]["answered"].get("project-callable"), 1)

    def test_another_project_declaration_replaces_the_lexical_target(self):
        view, reference = self.check([end("app/tool.py", "other", 5)])
        self.assertEqual((reference["target_id"], reference["resolver"], reference["provenance"]),
                         (self.declaration("other"), "stub@1.0", ["stub@1.0"]))
        self.assertEqual(reference["lexical_target_id"], self.declaration("free"))
        self.assertEqual(view["coverage"]["languages"]["python"]["answered"].get("project-callable"), 1)

    def test_a_definition_outside_the_project_removes_the_lexical_edge(self):
        view, reference = self.check([outside("vendor-lib")])
        self.assertEqual((reference["target_id"], reference["resolution"], reference["reason"]),
                         (None, "unresolved", "external"))
        self.assertEqual(reference["lexical_target_id"], self.declaration("free"))
        answered = view["coverage"]["languages"]["python"]["answered"]
        self.assertEqual((answered.get("external"), answered.get("project-callable")), (1, None))

    def test_no_engine_answer_keeps_the_lexical_target(self):
        view, reference = self.check(None)
        self.assertEqual((reference["target_id"], reference["provenance"]),
                         (self.declaration("free"), [resolve_edges.resolution.LEXICAL_RESOLVER]))
        answered = view["coverage"]["languages"]["python"]["answered"]
        self.assertEqual((answered.get("lexical"), answered.get("project-callable")), (1, None))


class CommandLineTests(unittest.TestCase):
    def test_the_command_reports_a_missing_engine_as_a_failure_with_its_recovery(self):
        """Without a container Vue is a gap with its cause: nothing of it starts on the host (AGENTS.md)."""
        import contextlib
        import io
        import container
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve() / "proj"
            root.mkdir()
            (root / "a.vue").write_text("<script>\nfunction f(x) { return x.f(); }\n</script>\n",
                                        encoding="utf-8")
            (root / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
            manifest = Path(temp).resolve() / "manifest.sqlite"
            snapshot.read_project(root, manifest)
            stdout = io.StringIO()
            gap = container.Gap("no container engine answers", "install Docker or Podman, then analyze again")
            with mock.patch.object(container, "find_engine", side_effect=gap), contextlib.redirect_stdout(stdout):
                code = resolve_edges.main([str(manifest), "--engine", "scip-typescript"])
        self.assertEqual(code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["available"])
        self.assertEqual(payload["reason"], "the build runs only in a container: no container engine answers")
        self.assertEqual(payload["install"], "install Docker or Podman, then analyze again")


class CoverageTests(unittest.TestCase):
    """What one language's store entry covers (`language_coverage`): the owner's answer to question 3."""

    @staticmethod
    def site(identity, kind="call", lexical=False):
        return {"reference_id": identity, "kind": kind, "site": f"a.go:{identity} f", "lexical": lexical}

    @staticmethod
    def edge(identity, verdict, confidence="confirmed", external=None):
        return {"reference_id": identity, "verdict": verdict, "confidence": confidence, "external": external}

    FILES = {"snapshot": 1, "indexed": 1, "missing": []}

    def test_a_language_all_indexed_without_holes_is_complete(self):
        package = {"manager": "gomod", "package": "std", "version": "go1.24"}
        coverage = resolve_edges.language_coverage(
            [self.site(1), self.site(2, "read"), self.site(3, lexical=True), self.site(4)],
            [self.edge(1, "project-callable"), self.edge(1, "dead-end"), self.edge(2, "external", external=package),
             self.edge(4, "project-callable", "uncertain")],
            [{"reference_id": 3, "class": "not-asked"}], self.FILES)
        self.assertEqual(coverage["state"], "complete")
        self.assertEqual(coverage["answered"], {"external": 1, "lexical": 1, "project-callable": 2})
        self.assertEqual((coverage["sites"], coverage["holes"], coverage["uncertain"]), (4, {}, 1))
        self.assertEqual((coverage["externals"], coverage["files"]), ({"gomod std@go1.24": 1}, self.FILES))
        self.assertNotIn("violations", coverage)

    def test_a_value_a_dead_end_a_hole_or_a_missing_file_leaves_a_lower_bound(self):
        missing = {"snapshot": 2, "indexed": 1, "missing": [{"path": "b.go", "reason": "no document in the index"}]}
        cases = {
            "value": ([self.edge(1, "project-value")], [], self.FILES, {"answered": {"project-value": 1}}),
            "dead end": ([self.edge(1, "dead-end")], [], self.FILES,
                         {"holes": {"dead-end": {"count": 1, "examples": ["a.go:1 f"]}}}),
            "hole": ([], [{"reference_id": 1, "class": "no-occurrence"}], self.FILES,
                     {"holes": {"no-occurrence": {"count": 1, "examples": ["a.go:1 f"]}}}),
            "missing file": ([self.edge(1, "project-callable")], [], missing, {"files": missing}),
        }
        for name, (edges, holes, files, expected) in cases.items():
            with self.subTest(name):
                coverage = resolve_edges.language_coverage([self.site(1)], edges, holes, files)
                self.assertEqual(coverage["state"], "lower-bound")
                self.assertEqual({key: coverage[key] for key in expected}, expected)
                self.assertEqual(*coverage_sums(coverage))

    def test_a_site_the_store_holds_nothing_for_is_listed_never_counted(self):
        coverage = resolve_edges.language_coverage([self.site(1), self.site(2, "read")], [self.edge(1, "external")],
                                                   [], self.FILES)
        self.assertEqual(coverage["violations"], {"read": ["a.go:2 f"]})
        self.assertEqual((coverage["sites"], coverage_sums(coverage)[1]), (2, 1))


class FreeMemoryTests(unittest.TestCase):
    """The memory a new process can have, which decides whether an engine or an indexer starts."""

    @unittest.skipUnless(os.name == "nt", "the Windows memory status")
    def test_on_windows_it_is_the_smaller_of_free_physical_memory_and_free_commit(self):
        import ctypes
        for physical, commit in ((5 * 2**30, 2 * 2**30), (2**30, 6 * 2**30)):
            def status(reference, physical=physical, commit=commit):
                reference._obj.available, reference._obj.page_free = physical, commit
                return 1

            with mock.patch.object(ctypes.windll.kernel32, "GlobalMemoryStatusEx", status):
                self.assertEqual(resolve_edges.free_memory(), min(physical, commit))


class IndexerStageTests(unittest.TestCase):
    """An indexer's entry in the pass: the indexer's contract in, the language's entry and the store out."""

    FIXTURES = Path(__file__).resolve().parent / "fixtures/code-graph"
    PYTHON = {"app/use.py": "class User:\n    def go(self, helper):\n        return helper.run()\n",
              "app/tool.py": "class Tool:\n    def run(self):\n        return 1\n"}

    def project(self, which: str, extra: dict | None = None) -> tuple[Path, Path]:
        import shutil
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve()
        shutil.copytree(self.FIXTURES / which, root / which, ignore=shutil.ignore_patterns("index.scip", "expected.json"))
        for rel, text in (extra or {}).items():
            (root / which / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / which / rel).write_text(text, encoding="utf-8")
        manifest = root / "manifest.sqlite"
        snapshot.read_project(root / which, manifest)
        return root / which, manifest

    def contract(self, which: str, indexer: dict | None = None, **outcome) -> dict:
        indexer = indexer or {"name": "scip-go", "version": "v0.2.9", "seconds": 1.0, "peak_mb": None}
        if outcome:
            return {"indexes": [], "runs": [], "indexer": indexer, **outcome}
        return {"indexes": [[str(self.FIXTURES / which / "index.scip"), ""]], "runs": [], "indexer": indexer}

    def run_stage(self, name: str, manifest: Path, index, free: int = 64 * 2**30, **patches):
        """The pass with `name`'s entry serving its languages and its stage run in this process, `index` standing
        in for the indexer's `index()`: the pass's report, the stages started, the stand-in."""
        import contextlib
        import importlib
        import io
        import container
        # An analyzer whose build runs only in a container is handed the engine the pass found.
        patches.setdefault("engine", (container, "find_engine", lambda: container.Engine("fake", ("x",))))
        spec = next(spec for spec in resolve_edges.ENGINES if spec.name == name)
        module = importlib.import_module(f"indexers.{spec.indexer}")
        started, real = [], subprocess.run

        def stage(command, **options):
            if command[1:2] != ["--engine"]:
                return real(command, **options)  # what the stage itself starts, such as git
            started.append(command)
            with contextlib.redirect_stdout(io.StringIO()):
                resolve_edges.main(command)
            return subprocess.CompletedProcess(command, 0)

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(engine_pass, "ENGINES", (spec,)))
            stack.enter_context(mock.patch.object(engine_pass, "ENGINE_LANGUAGES",
                                                  {language: spec for language in spec.languages}))
            stack.enter_context(mock.patch.object(
                engine_pass, "stage_command", side_effect=lambda spec, manifest, path, offline=False:
                [str(manifest), "--engine", spec.name, "--report-out", str(path)]))
            stack.enter_context(mock.patch.object(engine_pass, "cached_offline", return_value=False))
            stack.enter_context(mock.patch.object(subprocess, "run", side_effect=stage))
            stack.enter_context(mock.patch.object(engine_pass, "free_memory", return_value=free))
            for target, attribute, value in patches.values():
                stack.enter_context(mock.patch.object(target, attribute, value))
            indexed = stack.enter_context(mock.patch.object(module, "index", side_effect=index))
            result = resolve_edges.run_pass(manifest, manifest.with_name(resolve_edges.REPORT_NAME))
        return result, started, indexed

    def test_entry_is_fresh_with_its_resolver(self):
        project, manifest = self.project("go")
        seen = []

        def index(project_dir, work_dir, files=None, **given):
            seen.append((Path(project_dir), Path(work_dir), Path(work_dir).is_dir()))
            return self.contract("go")

        result, started, _indexed = self.run_stage("scip-go", manifest, index)
        self.assertEqual(len(started), 1)
        self.assertEqual(result["languages"]["go"], {"state": "fresh", "engine": "scip-go@v0.2.9"})
        self.assertEqual((seen[0][0], seen[0][2]), (project, True))
        self.assertFalse(seen[0][1].exists())  # the indexer's work directory goes with the stage
        with open_snapshot(manifest) as store:
            edges, binding, reason = resolve_edges.read_edge_store(resolve_edges.default_edge_store(manifest), store)
        self.assertIsNone(reason, reason)
        self.assertTrue(edges)
        self.assertEqual({edge["resolver"] for edge in edges}, {"scip-go@v0.2.9"})
        self.assertEqual(binding["languages"]["go"]["engine"], "scip-go@v0.2.9")
        self.assertEqual(binding["languages"]["go"]["indexer"]["name"], "scip-go")
        self.assertEqual(binding["languages"]["go"]["adapter_digest"], engine_pass.adapter_fingerprint("go"))
        self.assertEqual(resolve_edges.edge_state(manifest)["languages"]["go"]["state"], "fresh")
        import edge_view
        from indexers import go
        with mock.patch.object(go, "VERSION", "v99"):
            self.assertNotIn("go", resolve_edges.edge_state(manifest)["coverage"])
            self.assertEqual(edge_view.load_edge_view(manifest)["coverage"]["status"], "rejected_store")
            replay = edge_view.load_edge_view(manifest, engine_store=resolve_edges.default_edge_store(manifest))
            self.assertIn("go", replay["coverage"]["languages"])

    def test_unchanged_inputs_reuse_the_index_and_a_change_runs_the_language_once(self):
        # The cache is of the whole language: every adapter runs all its units in one container and gives one
        # contract, which it does not split per unit.
        project, manifest = self.project("go")
        calls = []

        def index(project_dir, work_dir, files=None, **given):
            # The index in the work directory, removed after the stage, with a file beside it named after it.
            calls.append(True)
            written = Path(work_dir) / "scip-go-0.scip"
            shutil.copyfile(self.FIXTURES / "go/index.scip", written)
            written.with_suffix(".unbound.jsonl").write_text("{}\n", encoding="utf-8")
            return {**self.contract("go"), "indexes": [[str(written), ""]]}

        def stage():
            resolve_edges.default_edge_store(manifest).unlink(missing_ok=True)  # the stage runs again
            result, started, _indexed = self.run_stage("scip-go", manifest, index)
            self.assertEqual(len(started), 1)
            self.assertEqual(result["languages"]["go"], {"state": "fresh", "engine": "scip-go@v0.2.9"})
            return len(calls)

        self.assertEqual(stage(), 1)
        kept = manifest.parent / engine_pass.INDEX_CACHE / "scip-go" / "files"
        self.assertEqual(sorted(path.name for path in kept.rglob("*") if path.is_file()),
                         ["scip-go-0.scip", "scip-go-0.unbound.jsonl"])
        self.assertEqual(stage(), 1)  # snapshot and dependencies unchanged: no indexer run
        (project / "extra").mkdir()
        (project / "extra/more.go").write_text("package extra\n\nfunc More() int { return 1 }\n", encoding="utf-8")
        snapshot.read_project(project, manifest)
        self.assertEqual(stage(), 2)  # a unit changed: one run for the language, whole
        self.assertEqual(stage(), 2)
        with open(project / "go.mod", "a", encoding="utf-8") as handle:
            handle.write("\nrequire example.com/dep v1.0.0\n")
        snapshot.read_project(project, manifest)
        self.assertEqual(stage(), 3)  # a manifest changed, no Go file did: the language runs again, whole

    def test_reuse_requires_the_installed_pin_and_the_adapter_that_built_the_entry(self):
        from indexers import go
        entry = {"engine": f"scip-go@{go.VERSION}", "indexer": {"version": go.VERSION}}
        self.assertFalse(engine_pass.from_source("go", entry))  # older stores have no adapter fingerprint
        entry["adapter_digest"] = engine_pass.adapter_fingerprint("go")
        self.assertTrue(engine_pass.from_source("go", entry))
        self.assertFalse(engine_pass.from_source("go", {**entry, "adapter_digest": "former adapter"}))
        with mock.patch.object(go, "VERSION", "v99"):
            self.assertFalse(engine_pass.from_source("go", entry))

    def test_the_stage_builds_its_traversal_from_every_hook_the_adapter_defines(self):
        import code_graph
        from indexers import go
        _project, manifest = self.project("go")
        calls, hops = [], go.hops
        hooks = {"prepare": lambda index, snap: calls.append("prepare"),
                 "hops": lambda index: calls.append("hops") or hops(index),
                 "same_range": lambda index: calls.append("same_range") or {},
                 "classify": lambda index: calls.append("classify") or (lambda key: None),
                 "unanswered": lambda index: calls.append("unanswered") or (lambda position: None)}
        self.assertEqual(set(hooks), {"hops", *code_graph.TRAVERSAL_HOOKS})
        with mock.patch.multiple(go, create=True, **hooks):
            result, _started, _indexed = self.run_stage(
                "scip-go", manifest, lambda project_dir, work_dir, files=None, **given: self.contract("go"))
        self.assertEqual(result["languages"]["go"], {"state": "fresh", "engine": "scip-go@v0.2.9"})
        self.assertEqual((calls[:2], sorted(calls[2:])), (["prepare", "hops"], ["classify", "same_range", "unanswered"]))

    def test_the_stage_gives_the_indexer_the_folders_the_pre_map_names(self):
        """The stage reads the pre-map and hands the indexer its structure: the indexer looks for no manifest."""
        extra = {"tools/go.mod": "module example.com/tools" + chr(10) + chr(10) + "go 1.21" + chr(10),
                 "tools/tool.go": "package tools" + chr(10)}
        _project, manifest = self.project("go", extra)
        seen = {}

        def index(project_dir, work_dir, files=None, **given):
            seen.update(given)
            return self.contract("go")

        result, _started, _indexed = self.run_stage("scip-go", manifest, index)
        self.assertEqual(result["languages"]["go"], {"state": "fresh", "engine": "scip-go@v0.2.9"})
        self.assertEqual(seen["roots"], {"", "tools"})
        # Its build runs only in a container: the engine the pass found, and the hosts the project declares.
        self.assertEqual((seen["engine"].name, seen["declared"]["hosts"]), ("fake", ()))

    def test_the_stage_keeps_the_entries_of_the_other_languages(self):
        _project, manifest = self.project("go", self.PYTHON)
        write_answers(manifest, resolve_edges.default_edge_store(manifest),
                      {("app/use.py", 3): [end("app/tool.py", "run", 2)]}, languages=("python",))
        self.run_stage("scip-go", manifest, lambda project_dir, work_dir, files=None, **given: self.contract("go"))
        with open_snapshot(manifest) as store:
            edges, binding, reason = resolve_edges.read_edge_store(resolve_edges.default_edge_store(manifest), store)
        self.assertIsNone(reason, reason)
        self.assertEqual({language: entry["engine"] for language, entry in binding["languages"].items()},
                         {"go": "scip-go@v0.2.9", "python": "stub@1.0"})
        self.assertEqual({edge["resolver"] for edge in edges}, {"scip-go@v0.2.9", "stub@1.0"})

    def test_failed_index_leaves_failed(self):
        _project, manifest = self.project("go")
        reason = "scip-go wrote no index (exit code 1): panic: no packages"
        result, _started, _indexed = self.run_stage(
            "scip-go", manifest, lambda project_dir, work_dir, files=None, **given: self.contract(
                "go", state="failed", reason=reason, errors=2))
        self.assertEqual(result["languages"]["go"], {"state": "failed", "engine": "scip-go", "reason": reason})
        self.assertFalse(resolve_edges.default_edge_store(manifest).exists())
        self.assertEqual(resolve_edges.edge_state(manifest)["languages"]["go"]["state"], "failed")

    def test_unavailable_index_leaves_unavailable_with_install(self):
        _project, manifest = self.project("go")
        reason = "Go 1.27.3 and scip-go v0.2.9 could not be downloaded: no network"
        install = "check the network: Daodan downloads Go 1.27.3 and scip-go v0.2.9 from go.dev and proxy.golang.org"
        result, _started, _indexed = self.run_stage(
            "scip-go", manifest, lambda project_dir, work_dir, files=None, **given: self.contract(
                "go", state="unavailable", reason=reason, install=install))
        self.assertEqual(result["languages"]["go"],
                         {"state": "unavailable", "engine": "scip-go", "reason": reason, "install": install})

    def test_the_gaps_an_indexer_reports_reach_the_pass_and_its_events(self):
        """What the preparation could not do (a restore, a toolchain) is said by the stage and the pass, with the
        language indexed all the same."""
        from pipeline import events
        _project, manifest = self.project("go")
        gap = {"kind": "restore_failed", "manager": "maven", "path": ".", "detail": "[ERROR] Could not resolve x"}
        result, _started, _indexed = self.run_stage(
            "scip-go", manifest, lambda *args, **kwargs: {**self.contract("go"), "gaps": [gap]})
        self.assertEqual(result["languages"]["go"]["state"], "fresh")
        self.assertEqual(result["engines"]["scip-go"]["gaps"], [gap])
        journal, _cursor = events.read(manifest.with_name(events.JOURNAL))
        said = [event for event in journal if event["kind"] == "gap" and event["step"] == "link_calls"]
        self.assertEqual([(event["analyzer"], event["data"]["gap"]) for event in said], [("scip-go", gap)])

    def test_container_language_without_container_is_unavailable(self):
        import container
        _project, manifest = self.project("java")

        def no_engine(*_args, **_kwargs):
            raise container.Gap("no container engine answers: neither docker nor podman", "start Docker or Podman")

        spec = next(spec for spec in resolve_edges.ENGINES if spec.name == "scip-java")
        self.assertTrue(spec.needs_container)
        result, started, indexed = self.run_stage("scip-java", manifest, lambda *args, **kwargs: {},
                                                  engine=(container, "find_engine", no_engine))
        self.assertEqual(len(started), 1)
        indexed.assert_not_called()
        self.assertEqual(result["languages"]["java"], {
            "state": "unavailable", "engine": "scip-java",
            "reason": "the build runs only in a container: no container engine answers: neither docker nor podman",
            "install": "start Docker or Podman"})

    def python_contract(self, **outcome) -> dict:
        indexer = {"name": "scip-python", "version": "0.6.8", "seconds": 1.0, "peak_mb": None}
        return self.contract("python", indexer, **outcome)

    def test_c_reads_from_scip_clang_with_the_units_the_pre_map_names(self):
        """C and C++ come from scip-clang in a container: the stage hands it the pre-map's native units and
        workspaces, and the graph of C is built from the index it returns."""
        import container
        _project, manifest = self.project("c")
        seen = {}

        def index(project_dir, work_dir, files=None, **given):
            seen.update(given)
            indexer = {"name": "scip-clang", "version": "v0.4.1", "seconds": 1.0, "peak_mb": None}
            return self.contract("c", indexer)

        result, started, _indexed = self.run_stage(
            "scip-clang", manifest, index, engine=(container, "find_engine", lambda: container.Engine("fake", ("x",))))
        self.assertEqual(len(started), 1)
        self.assertEqual(result["languages"]["c"], {"state": "fresh", "engine": "scip-clang@v0.4.1"})
        self.assertEqual({unit["kind"] for unit in seen["units"]}, {"cmake-target"})
        self.assertIn("workspace", seen)
        self.assertIsInstance(seen["engine"], container.Engine)

    def test_python_reads_from_its_index_and_an_entry_of_a_former_engine_is_not_fresh(self):
        _project, manifest = self.project("python")
        write_answers(manifest, resolve_edges.default_edge_store(manifest), {}, resolver="jedi@0.20.1",
                      languages=("python",))
        self.assertEqual(resolve_edges.edge_state(manifest)["languages"]["python"]["state"], "missing")
        result, started, _indexed = self.run_stage(
            "scip-python", manifest, lambda project_dir, work_dir, files=None, **given: self.python_contract())
        self.assertEqual(len(started), 1)
        self.assertEqual(result["languages"]["python"], {"state": "fresh", "engine": "scip-python@0.6.8"})
        state = resolve_edges.edge_state(manifest)
        self.assertEqual(state["languages"]["python"]["state"], "fresh")
        self.assertTrue(state["coverage"]["python"]["answered"].get("project-callable"))

    def test_python_without_a_container_engine_where_scip_python_cannot_start_is_unavailable_until_one_answers(self):
        import container
        from indexers import python, runtime
        _project, manifest = self.project("python")
        real_index = python.index

        def no_engine(*_args, **_kwargs):
            raise container.Gap("no container engine answers: neither docker nor podman", "start Docker or Podman")

        node = mock.Mock(side_effect=AssertionError("nothing is downloaded without an engine"))
        result, started, _indexed = self.run_stage(
            "scip-python", manifest, real_index, here=(python, "RUNS_HERE", False),
            engine=(container, "find_engine", no_engine), memory=(container, "free_memory", lambda: 64 * 2**30),
            node=(runtime, "node", node))
        self.assertEqual(len(started), 1)
        node.assert_not_called()
        entry = result["languages"]["python"]
        self.assertEqual((entry["state"], entry["engine"], entry["install"]),
                         ("unavailable", "scip-python", "start Docker or Podman"))
        self.assertIn("path separator", entry["reason"])
        self.assertIn("no container engine answers", entry["reason"])
        self.assertEqual(resolve_edges.edge_state(manifest)["languages"]["python"]["state"], "unavailable")
        # The next pass asks again; with an engine that answers, the language is fresh.
        result, started, _indexed = self.run_stage(
            "scip-python", manifest, lambda project_dir, work_dir, files=None, **given: self.python_contract())
        self.assertEqual(len(started), 1)
        self.assertEqual(result["languages"]["python"], {"state": "fresh", "engine": "scip-python@0.6.8"})

    def test_memory_under_min_free_starts_no_stage(self):
        from indexers import go
        _project, manifest = self.project("go")
        spec = next(spec for spec in resolve_edges.ENGINES if spec.name == "scip-go")
        self.assertEqual(spec.min_free, go.MIN_FREE)
        result, started, indexed = self.run_stage(
            "scip-go", manifest,
            lambda project_dir, work_dir, files=None, **given: self.contract("go"), free=go.MIN_FREE - 1)
        self.assertEqual(started, [])
        indexed.assert_not_called()
        self.assertEqual(result["languages"]["go"]["state"], "failed")
        self.assertIn(f"{(go.MIN_FREE - 1) / 2**30:.1f} GB of memory free", result["languages"]["go"]["reason"])
        # At the indexer's own minimum, the stage starts.
        _result, started, _indexed = self.run_stage(
            "scip-go", manifest,
            lambda project_dir, work_dir, files=None, **given: self.contract("go"), free=go.MIN_FREE)
        self.assertEqual(len(started), 1)

    def test_a_missing_file_and_a_hole_give_lower_bound_with_the_counts(self):
        _project, manifest = self.project("go", {"extra.go": "package fx\n\nfunc Extra() int { return len(\"x\") }\n"})
        result, _started, _indexed = self.run_stage(
            "scip-go", manifest, lambda project_dir, work_dir, files=None, **given: self.contract("go"))
        self.assertEqual(result["languages"]["go"]["state"], "fresh")
        state = resolve_edges.edge_state(manifest)
        go = state["coverage"]["go"]
        self.assertEqual(go["state"], "lower-bound")
        self.assertIn({"path": "extra.go", "reason": "no document in the index"}, go["files"]["missing"])
        self.assertEqual((go["files"]["snapshot"], go["files"]["indexed"]), (3, 2))
        with open_snapshot(manifest) as store:
            sites = store.connection.execute(
                "SELECT count(*) FROM sem_references r JOIN sem_coverage c ON c.file=r.file "
                "WHERE r.kind IN ('call','read') AND c.language='go'").fetchone()[0]
        self.assertEqual(coverage_sums(go), (sites, sites))
        self.assertTrue(go["holes"] and go["answered"]["project-callable"])
        self.assertTrue(all(len(hole["examples"]) <= 3 for hole in go["holes"].values()))

    def test_a_broken_invariant_fails_the_stage_with_the_list(self):
        import code_graph
        _project, manifest = self.project("go")
        real = code_graph.build

        def dropping(*args, **kwargs):
            graph, references = real(*args, **kwargs)
            references.pop(next(identity for identity, reference in references.items()
                                if reference["kind"] == "call"))  # a call the store would hold nothing for
            return graph, references

        result, _started, _indexed = self.run_stage(
            "scip-go", manifest, lambda project_dir, work_dir, files=None, **given: self.contract("go"),
            build=(code_graph, "build", dropping))
        go = result["languages"]["go"]
        self.assertEqual(go["state"], "failed")
        self.assertIn("sites = answered + holes", go["reason"])
        self.assertRegex(go["reason"], r"call 1: \S+\.go:\d+")
        self.assertFalse(resolve_edges.default_edge_store(manifest).exists())

    def test_each_language_reads_from_its_source(self):
        self.assertEqual({language: spec.name for language, spec in resolve_edges.ENGINE_LANGUAGES.items()},
                         {"python": "scip-python", "typescript": "scip-typescript", "javascript": "scip-typescript",
                          "vue": "scip-typescript", "svelte": "scip-typescript", "java": "scip-java",
                          "kotlin": "scip-kotlin",
                          "rust": "scip-rust", "go": "scip-go", "c": "scip-clang", "cpp": "scip-clang",
                          "csharp": "scip-dotnet", "stylesheet": "stylesheet"})
        indexers = {spec.name: (spec.languages, spec.indexer, spec.needs_container) for spec in resolve_edges.ENGINES}
        self.assertEqual(indexers, {
            "scip-go": (("go",), "go", True), "scip-rust": (("rust",), "rust", True),
            "scip-typescript": (("typescript", "javascript", "vue", "svelte"), "typescript", True),
            "scip-python": (("python",), "python", False), "scip-java": (("java",), "java", True),
            "scip-kotlin": (("kotlin",), "kotlin", True), "scip-clang": (("c", "cpp"), "clang", True),
            "scip-dotnet": (("csharp",), "csharp", True),
            "stylesheet": (("stylesheet",), "css", False)})

    def test_the_resolver_names_the_entry_not_the_indexer(self):
        # scip-java indexes Kotlin too: the entry names the source.
        import container
        _project, manifest = self.project("rust")
        indexer = {"name": "rust-analyzer", "version": "2026-11-09", "seconds": 1.0, "peak_mb": None}
        result, _started, _indexed = self.run_stage(
            "scip-rust", manifest, lambda project_dir, work_dir, files=None, **given: self.contract("rust", indexer),
            engine=(container, "find_engine", lambda: container.Engine("fake", ("x",))))
        self.assertEqual(result["languages"]["rust"], {"state": "fresh", "engine": "scip-rust@2026-11-09"})

    def test_an_entry_from_the_former_source_is_not_fresh(self):
        _project, manifest = self.project("go")
        write_answers(manifest, resolve_edges.default_edge_store(manifest), {}, resolver="gopls@0.20.0",
                      languages=("go",))
        with open_snapshot(manifest) as store:
            _edges, binding, _reason = resolve_edges.read_edge_store(resolve_edges.default_edge_store(manifest), store)
        self.assertEqual(binding["languages"]["go"]["engine"], "gopls@0.20.0")
        self.assertEqual(resolve_edges.edge_state(manifest)["languages"]["go"]["state"], "missing")
        self.assertEqual(resolve_edges.ensure_edges(manifest, check=True)["action"], "reported")
        _result, started, _indexed = self.run_stage(
            "scip-go", manifest, lambda project_dir, work_dir, files=None, **given: self.contract("go"))
        self.assertEqual(len(started), 1)
        self.assertEqual(resolve_edges.edge_state(manifest)["languages"]["go"]["state"], "fresh")
        # From the source that serves it, the entry is fresh: no stage starts again.
        _result, started, _indexed = self.run_stage(
            "scip-go", manifest, lambda project_dir, work_dir, files=None, **given: self.contract("go"))
        self.assertEqual(started, [])

if __name__ == "__main__":
    unittest.main()
