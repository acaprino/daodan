"""The working run: refresh, the pre-query gate and the PostToolUse hook filters."""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import mcp_service  # noqa: E402
import modules  # noqa: E402
import resolve_edges  # noqa: E402
import retrieval  # noqa: E402
import snapshot  # noqa: E402


def run_bytes(run: Path) -> dict:
    return {path.relative_to(run).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(run.rglob("*")) if path.is_file()}


class WorkingRunTests(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp(prefix="map-working-")).resolve()
        self.addCleanup(shutil.rmtree, self.project, True)
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        self.src = self.project / "src"
        self.src.mkdir()
        for index in range(10):
            (self.src / f"mod{index}.py").write_text(f"def helper{index}():\n    return {index}\n", encoding="utf-8")
        (self.src / "app.py").write_text("def greet():\n    return 'hi'\n", encoding="utf-8")
        self.service = mcp_service.MapService(self.project)
        self.service.create_run("src", "base", engine=False)
        self.root = self.project / ".daodan/map"
        self.published = self.root / "runs/base"
        state = json.loads((self.published / "state.json").read_text(encoding="utf-8"))
        state["status"] = "complete"
        (self.published / "state.json").write_text(json.dumps(state), encoding="utf-8")
        (self.published / "01-structure.md").write_text(
            "# Structure\n\n`src/app.py::greet` says hello.\n`src/mod1.py::helper1` is untouched.\n",
            encoding="utf-8")
        (self.root / "runs.json").write_text(json.dumps(
            {"schema": 2, "active": [], "latest_completed": "base"}), encoding="utf-8")
        self.working = self.root / "runs/working"

    def edit(self, name, text):
        path = self.src / name
        path.write_text(text, encoding="utf-8")
        stamp = time.time() + 2
        import os
        os.utime(path, (stamp, stamp))

    def refresh(self):
        return snapshot.refresh_working(self.root)

    def report(self):
        return json.loads((self.working / "refresh.json").read_text(encoding="utf-8"))

    def gate(self):
        return snapshot.query_gate(self.working / "snapshot/manifest.sqlite")

    def test_1_stale_search_warns_and_refresh_serves_the_new_symbol(self):
        self.edit("app.py", "def greet():\n    return 'hi'\n\ndef farewell_wave():\n    return 'bye'\n")
        warned = self.service.search("base", "farewell_wave")
        self.assertEqual(warned["state"], "needs_refresh")
        self.assertIn("snapshot.py refresh", warned["action"])
        self.assertIn("src/app.py", warned["reason"])
        self.assertNotIn("results", warned)

        self.assertEqual(self.refresh()["status"], "fresh")
        found = self.service.search("working", "farewell_wave")
        self.assertEqual(found.get("index_state"), "fresh", found)
        self.assertIn("farewell_wave", json.dumps(found))
        packet = self.service.read("working", [{"path": "src/app.py", "symbols": ["farewell_wave"]}])
        self.assertIn("return 'bye'", json.dumps(packet))
        report = self.report()
        self.assertEqual(report["since_published"]["files"]["modified"], ["src/app.py"])
        self.assertIn({"file": "src/app.py", "symbol": "farewell_wave", "kind": "function"},
                      report["since_published"]["symbols"]["added"])
        self.assertEqual([claim["line"] for claim in report["since_published"]["claims"]], [])
        self.edit("app.py", "def greet():\n    return 'hello'\n")
        self.refresh()
        claims = self.report()["since_published"]["claims"]
        self.assertEqual([(c["phase_file"], c["line"], c["reason"]) for c in claims],
                         [("01-structure.md", 3, "symbol-changed")])

    def test_2_the_published_run_stays_byte_identical(self):
        before = run_bytes(self.published)
        self.edit("app.py", "def greet():\n    return 'changed'\n")
        self.assertEqual(self.refresh()["status"], "fresh")
        self.edit("mod2.py", "def helper2():\n    return 22\n")
        self.assertEqual(self.refresh()["status"], "fresh")
        self.assertEqual(run_bytes(self.published), before)

    def test_3_one_refresh_runs_one_waits_the_rest_are_dropped(self):
        self.assertEqual(self.refresh()["status"], "fresh")
        self.edit("app.py", "def greet():\n    return 'queued'\n")
        active = snapshot._hold(self.working / ".refresh.lock", wait=True)
        command = [sys.executable, "-B", str(SCRIPTS / "snapshot.py"), "refresh", str(self.project)]
        waiting = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 20
            while (probe := snapshot._hold(self.working / ".refresh-queue.lock", wait=False)) is not None:
                probe.unlink()  # free: the child has not taken the queue slot yet
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.05)
            dropped = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(json.loads(dropped.stdout)["status"], "queued")
            self.assertIsNone(waiting.poll())
        finally:
            active.unlink()
        out, _ = waiting.communicate(timeout=60)
        self.assertEqual(json.loads(out)["status"], "fresh")
        self.assertIsNone(self.gate())

    def test_3_two_refreshes_at_once_leave_an_intact_snapshot(self):
        self.edit("app.py", "def greet():\n    return 'concurrent'\n")
        command = [sys.executable, "-B", str(SCRIPTS / "snapshot.py"), "refresh", str(self.project)]
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, text=True) for _ in range(2)]
        outcomes = sorted(json.loads(p.communicate(timeout=120)[0])["status"] for p in processes)
        self.assertEqual([p.returncode for p in processes], [0, 0])
        self.assertIn("fresh", outcomes)
        self.assertTrue(set(outcomes) <= {"fresh", "unchanged", "queued"}, outcomes)
        self.assertIsNone(self.gate())
        from snapshot_store import open_snapshot
        with open_snapshot(self.working / "snapshot/manifest.sqlite") as store:
            snapshot.validate_reuse_manifest(store)
            self.assertEqual(store.file_count, 11)
        self.assertEqual(retrieval.index_state(self.working / "snapshot/manifest.sqlite")["state"], "fresh")

    def test_3_reads_wait_for_refresh_and_warn_after_an_error(self):
        seen = {}
        original = retrieval.ensure_index

        def during(manifest, *args, **kwargs):
            seen["gate"] = snapshot.query_gate(manifest)
            seen["search"] = pool.submit(self.service.search, "working", "greet")
            return original(manifest, *args, **kwargs)

        self.edit("app.py", "def greet():\n    return 'during'\n")
        with ThreadPoolExecutor(max_workers=1) as pool, mock.patch.object(retrieval, "ensure_index", during):
            self.assertEqual(self.refresh()["status"], "fresh")
            self.assertEqual(seen["search"].result(timeout=10)["index_state"], "fresh")
        self.assertIn("refresh is running", seen["gate"]["reason"])

        self.edit("app.py", "def greet():\n    return 'broken'\n")
        with mock.patch.object(modules, "ensure_graph", return_value={"state": "failed", "reason": "boom"}):
            self.assertEqual(self.refresh()["status"], "failed")
        warned = self.service.read("working", [{"path": "src/app.py", "symbols": ["greet"]}])
        self.assertEqual(warned["state"], "needs_refresh")
        self.assertIn("failed", warned["reason"])
        self.assertIn("boom", warned["reason"])

    def test_3_an_edit_during_a_refresh_leaves_the_run_to_refresh(self):
        original = retrieval.ensure_index

        def edit_after_snapshot(manifest, *args, **kwargs):
            self.edit("mod3.py", "def helper3():\n    return 'late'\n")
            return original(manifest, *args, **kwargs)

        self.edit("app.py", "def greet():\n    return 'first'\n")
        with mock.patch.object(retrieval, "ensure_index", edit_after_snapshot):
            # The index verifies each source against the new snapshot, so the
            # late edit either fails this refresh or is caught by the gate.
            self.assertIn(self.refresh()["status"], ("fresh", "failed"))
        self.assertEqual(self.gate()["state"], "needs_refresh")
        self.assertEqual(self.refresh()["status"], "fresh")
        self.assertIsNone(self.gate())

    def test_3_another_manifest_than_the_refreshed_one_is_refused(self):
        self.refresh()
        report = self.report()
        report["manifest_stat"] = [0, 0, 0]
        (self.working / "refresh.json").write_text(json.dumps(report), encoding="utf-8")
        self.assertIn("not the one", self.gate()["reason"])

    def test_4_over_forty_percent_rebuilds_then_one_file_reparses_one(self):
        self.assertEqual(self.refresh()["status"], "fresh")
        for index in range(5):
            self.edit(f"mod{index}.py", f"def renamed{index}():\n    return {index}\n")
        result = self.refresh()
        self.assertEqual((result["status"], result["rebuild"], result["changed_since_last"]), ("fresh", "full", 5))
        self.assertIn("renamed4", json.dumps(self.service.search("working", "renamed4")))
        self.edit("mod9.py", "def helper9():\n    return 99\n")
        result = self.refresh()
        self.assertEqual((result["rebuild"], result["changed_since_last"], result["parsed_files"]),
                         ("incremental", 1, 1))
        self.assertEqual(self.refresh()["status"], "unchanged")

    def test_engine_pass_starts_on_the_working_snapshot_and_its_state_is_recorded(self):
        state = json.loads((self.published / "state.json").read_text(encoding="utf-8"))
        state["engine"] = True
        (self.published / "state.json").write_text(json.dumps(state), encoding="utf-8")
        with mock.patch.object(resolve_edges, "ensure_edges", return_value={"state": "running"}) as ensure:
            self.assertEqual(self.refresh()["engine"], "running")
        ensure.assert_called_once_with(self.working / "snapshot/manifest.sqlite")

    def test_refresh_waits_for_an_mcp_reader_before_stopping_and_restarting_engines(self):
        self.assertEqual(self.refresh()["status"], "fresh")
        state_path = self.working / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["engine"] = True
        state_path.write_text(json.dumps(state), encoding="utf-8")
        reading, release, refresh_started, refreshing = (threading.Event() for _ in range(4))
        original_read = mcp_service.source_reader.read_packet
        original_hold = snapshot._hold
        original_refresh = snapshot._refresh_locked

        def hold_reader(*args, **kwargs):
            packet = original_read(*args, **kwargs)
            reading.set()
            if not release.wait(10):
                raise TimeoutError("test reader was not released")
            return packet

        def hold_refresh(path, wait):
            lock = original_hold(path, wait)
            if path.name == ".refresh.lock":
                refresh_started.set()
            return lock

        def refresh_after_reading(*args):
            refreshing.set()
            return original_refresh(*args)

        with mock.patch.object(mcp_service.source_reader, "read_packet", side_effect=hold_reader), \
                mock.patch.object(snapshot, "_hold", side_effect=hold_refresh), \
                mock.patch.object(snapshot, "_refresh_locked", side_effect=refresh_after_reading), \
                mock.patch.object(resolve_edges, "reset_pass") as reset, \
                mock.patch.object(resolve_edges, "ensure_edges", return_value={"state": "running"}) as ensure, \
                ThreadPoolExecutor(max_workers=2) as pool:
            reader = pool.submit(self.service.read, "working", [{"path": "src/mod0.py", "full_file": True}])
            try:
                self.assertTrue(reading.wait(10))
                self.edit("app.py", "def greet():\n    return 'after reading'\n")
                refresh = pool.submit(self.refresh)
                self.assertTrue(refresh_started.wait(10))
                self.assertFalse(refreshing.wait(0.2), "refresh started while the MCP reader was open")
                reset.assert_not_called()
            finally:
                release.set()
            self.assertIn("helper0", json.dumps(reader.result(timeout=10)))
            self.assertEqual(refresh.result(timeout=60)["status"], "fresh")
            ensure.assert_called_once_with(self.working / "snapshot/manifest.sqlite")
        self.assertIsNone(self.gate())

    def test_mcp_closes_its_snapshot_before_releasing_the_project_lock(self):
        captured = []
        original_lock = mcp_service.confinement.project_lock
        original_read = mcp_service.source_reader.read_packet

        def read(store, *args, **kwargs):
            captured.append(store)
            return original_read(store, *args, **kwargs)

        @contextmanager
        def checked_lock(project):
            with original_lock(project):
                yield
                self.assertTrue(captured)
                self.assertTrue(all(store.closed for store in captured), "snapshot outlived the project lock")

        with mock.patch.object(mcp_service.confinement, "project_lock", checked_lock), \
                mock.patch.object(mcp_service.source_reader, "read_packet", side_effect=read):
            self.service.read("base", [{"path": "src/mod0.py", "full_file": True}])

    def test_working_run_serves_no_documents_reviews_or_phases(self):
        self.refresh()
        for call in (lambda: self.service.artifact("working", "01-structure.md"),
                     lambda: self.service.create_run("src", "working", engine=False),
                     lambda: self.service.resume("working"),
                     lambda: self.service.publish("working")):
            with self.subTest(call=call), self.assertRaisesRegex(ValueError, "working run"):
                call()

    def test_cli_entries_return_the_warning(self):
        self.refresh()
        self.edit("app.py", "def greet():\n    return 'cli'\n")
        manifest = self.working / "snapshot/manifest.sqlite"
        for args in (["snapshot.py", "search", str(manifest), "--query", "greet"],
                     ["source_reader.py", "read", str(manifest), "--path", "src/app.py", "--full"]):
            with self.subTest(args=args[:2]):
                proc = subprocess.run([sys.executable, "-B", str(SCRIPTS / args[0]), *args[1:]],
                                      capture_output=True, text=True)
                self.assertEqual(proc.returncode, 1, proc.stderr)
                self.assertEqual(json.loads(proc.stdout)["state"], "needs_refresh")

    def hook(self, payload):
        return subprocess.run([sys.executable, "-B", str(SCRIPTS / "snapshot.py"), "hook"],
                              input=json.dumps({"cwd": str(self.project), **payload}),
                              capture_output=True, text=True)

    def test_5_hook_filters(self):
        outside = self.project / "notes.py"
        outside.write_text("x = 1\n", encoding="utf-8")
        for name, payload in (
                ("team-review", {"tool_name": "Write", "tool_input": {"file_path": str(self.project / ".team-review/00-scope.md")}}),
                ("daodan", {"tool_name": "Write", "tool_input": {"file_path": ".daodan/map/x.json"}}),
                ("outside perimeter", {"tool_name": "Edit", "tool_input": {"file_path": str(outside)}}),
                ("dot directory", {"tool_name": "Edit", "tool_input": {"file_path": str(self.src / ".cache/a.py")}})):
            with self.subTest(name):
                proc = self.hook(payload)
                self.assertEqual((proc.returncode, proc.stdout), (0, ""))
                self.assertFalse((self.working / "refresh.json").exists())
        proc = self.hook({"tool_name": "NotebookEdit", "tool_input": {"notebook_path": "src/app.py"}})
        self.assertEqual(json.loads(proc.stdout)["status"], "fresh")
        proc = self.hook({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        self.assertEqual(json.loads(proc.stdout)["status"], "unchanged")

    def test_5_hook_needs_a_published_run(self):
        (self.root / "runs.json").write_text(json.dumps(
            {"schema": 2, "active": [], "latest_completed": None}), encoding="utf-8")
        proc = self.hook({"tool_name": "Edit", "tool_input": {"file_path": "src/app.py"}})
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))
        self.assertFalse(self.working.exists())


if __name__ == "__main__":
    unittest.main()
