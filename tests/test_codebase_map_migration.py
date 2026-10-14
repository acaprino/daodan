"""Migration contracts: preserve evidence, bind paths and stop for live writers."""

from __future__ import annotations

import importlib.util
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock


HELPER = Path(os.environ.get(
    "CODEBASE_MAP_MIGRATION_HELPER",
    Path(__file__).resolve().parents[1]
    / "plugins/codebase-map/skills/map-method/scripts/migrate_root.py",
))
SPEC = importlib.util.spec_from_file_location("codebase_map_migration", HELPER)
assert SPEC and SPEC.loader
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=os.environ.get("CODEBASE_MAP_TEST_TEMP"))
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve()
        self.old = self.project / ".codebase-xray"
        self.new = self.project / ".codebase-map"

    def evidence(self, root=None, *, flat=False):
        root = root or self.old
        root.mkdir()
        if flat:
            values = {
                "state.json": b'{"current_phase":7,"completed_phases":[1,2,3,4,5,6,7]}\r\n',
                "07-final-report.md": b"old flat report\r\n",
            }
        else:
            values = {
                "runs.json": b'{"schema":2,"active":[],"latest_completed":"stable-id"}\r\n',
                "state.json": b'{"status":"complete","run_id":"stable-id"}\n',
                "07-final-report.md": b"latest report\r\n",
                "runs/stable-id/state.json": b'{"status":"complete","run_id":"stable-id"}\r\n',
                "runs/stable-id/snapshot/manifest.json": (
                    b'{"root":"foreign-source-root","old":".codebase-xray/runs/stable-id",'
                    b'"sha256":"unchanged"}\r\n'
                ),
                "runs/stable-id/snapshot/sources/blob": bytes(range(256)),
            }
        for name, data in values.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return values

    def assert_evidence(self, root, values):
        for name, data in values.items():
            with self.subTest(path=name):
                self.assertEqual((root / name).read_bytes(), data)

    def test_no_outputs_is_read_only_noop(self):
        result = MIGRATION.migrate(self.project)
        self.assertEqual(result["status"], "absent")
        self.assertEqual(list(self.project.iterdir()), [])

    def test_current_only_is_noop(self):
        values = self.evidence(self.new)
        result = MIGRATION.migrate(self.project)
        self.assertEqual(result["status"], "current")
        self.assertFalse(self.old.exists())
        self.assert_evidence(self.new, values)

    def test_check_does_not_write(self):
        values = self.evidence()
        result = MIGRATION.migrate(self.project, check=True)
        self.assertEqual(result["status"], "migration_required")
        self.assertFalse(self.new.exists())
        self.assert_evidence(self.old, values)
        self.assertEqual(set(p.relative_to(self.old).as_posix() for p in self.old.rglob("*") if p.is_file()), set(values))

    def test_migration_preserves_every_artifact_byte_and_old_run_id(self):
        values = self.evidence()
        result = MIGRATION.migrate(self.project)
        self.assertEqual(result["status"], "migrated")
        self.assert_evidence(self.new, values)
        self.assertEqual([p.name for p in self.old.iterdir()], [MIGRATION.REDIRECT_FILE])
        self.assertEqual(json.loads((self.old / MIGRATION.REDIRECT_FILE).read_text())["canonical_root"], ".codebase-map")

    def test_flat_pre_runs_layout_moves_without_rewriting_or_inventing_runs(self):
        values = self.evidence(flat=True)
        MIGRATION.migrate(self.project)
        self.assert_evidence(self.new, values)
        self.assertFalse((self.new / "runs").exists())

    def test_idempotent_migration_keeps_records_and_bytes(self):
        values = self.evidence()
        MIGRATION.migrate(self.project)
        record = (self.new / MIGRATION.ORIGIN_FILE).read_bytes()
        result = MIGRATION.migrate(self.project)
        self.assertEqual(result["status"], "current")
        self.assertEqual((self.new / MIGRATION.ORIGIN_FILE).read_bytes(), record)
        self.assert_evidence(self.new, values)

    def test_nonempty_roots_are_a_conflict_and_both_preserved(self):
        values = self.evidence()
        self.new.mkdir()
        (self.new / "foreign.txt").write_bytes(b"foreign")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "both"):
            MIGRATION.migrate(self.project)
        self.assert_evidence(self.old, values)
        self.assertEqual((self.new / "foreign.txt").read_bytes(), b"foreign")

    def test_empty_destination_can_be_replaced(self):
        self.new.mkdir()
        values = self.evidence()
        MIGRATION.migrate(self.project)
        self.assert_evidence(self.new, values)

    def test_active_registry_blocks_migration(self):
        self.evidence()
        registry = {"schema": 2, "active": [{"run_id": "live"}]}
        (self.old / "runs.json").write_text(json.dumps(registry))
        before = (self.old / "runs.json").read_bytes()
        with self.assertRaisesRegex(MIGRATION.MigrationError, "active"):
            MIGRATION.migrate(self.project)
        self.assertFalse(self.new.exists())
        self.assertEqual((self.old / "runs.json").read_bytes(), before)

    def test_active_state_blocks_even_if_registry_is_stale(self):
        self.evidence()
        (self.old / "runs/stable-id/state.json").write_text('{"status":"in_progress"}')
        with self.assertRaisesRegex(MIGRATION.MigrationError, "active"):
            MIGRATION.migrate(self.project)
        self.assertFalse(self.new.exists())

    def test_unfinished_flat_state_blocks(self):
        self.evidence(flat=True)
        (self.old / "state.json").write_text('{"current_phase":3,"completed_phases":[1,2]}')
        with self.assertRaisesRegex(MIGRATION.MigrationError, "active"):
            MIGRATION.migrate(self.project)

    def test_invalid_registry_fails_closed(self):
        self.evidence()
        (self.old / "runs.json").write_bytes(b"broken json")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "runs.json"):
            MIGRATION.migrate(self.project)
        self.assertFalse(self.new.exists())

    def test_old_bound_run_path_translates_after_migration(self):
        self.evidence()
        MIGRATION.migrate(self.project)
        result = MIGRATION.resolve_path(self.project, ".codebase-xray/runs/stable-id/snapshot/manifest.json")
        self.assertEqual(result["path"], str(self.new / "runs/stable-id/snapshot/manifest.json"))
        self.assertTrue(result["exists"])
        self.assertTrue(result["translated"])

    def test_absolute_bound_path_translates_without_touching_stored_content(self):
        values = self.evidence()
        old_manifest = self.old / "runs/stable-id/snapshot/manifest.json"
        MIGRATION.migrate(self.project)
        result = MIGRATION.resolve_path(self.project, old_manifest)
        self.assertEqual(Path(result["path"]).read_bytes(), values["runs/stable-id/snapshot/manifest.json"])

    def test_canonical_reference_can_read_legacy_before_migration(self):
        self.evidence()
        result = MIGRATION.resolve_path(self.project, ".codebase-map/07-final-report.md")
        self.assertEqual(result["path"], str(self.old / "07-final-report.md"))
        self.assertFalse(self.new.exists())

    def test_foreign_path_and_parent_traversal_are_rejected(self):
        self.evidence()
        for path in (".codebase-xray/../private", ".codebase-xray/../../private", ".codebase-xray\\..\\private", ".codebase-xray-extra/file", "other/file", self.project.parent / ".codebase-xray/file"):
            with self.subTest(path=path):
                with self.assertRaises(MIGRATION.MigrationError):
                    MIGRATION.resolve_path(self.project, path)

    def make_link(self, target, link, *, directory=True):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except OSError as error:
            self.skipTest(f"symlink creation unavailable: {error}")

    def test_linked_root_is_rejected(self):
        outside = self.project / "outside"
        outside.mkdir()
        (outside / "artifact").write_bytes(b"do not touch")
        self.make_link(outside, self.old)
        with self.assertRaisesRegex(MIGRATION.MigrationError, "link|reparse"):
            MIGRATION.migrate(self.project)
        self.assertFalse(self.new.exists())
        self.assertEqual((outside / "artifact").read_bytes(), b"do not touch")

    def test_windows_reparse_root_is_rejected_without_symlink_privileges(self):
        self.old.mkdir()
        actual_lstat = Path.lstat

        def reparse_lstat(path, *args, **kwargs):
            result = actual_lstat(path, *args, **kwargs)
            if path == self.old:
                return mock.Mock(st_mode=result.st_mode, st_file_attributes=0x400)
            return result

        with mock.patch.object(Path, "lstat", reparse_lstat):
            with self.assertRaisesRegex(MIGRATION.MigrationError, "link|reparse"):
                MIGRATION.migrate(self.project)

    def test_nested_links_cannot_escape_during_resolution(self):
        self.evidence()
        outside = self.project / "outside"
        outside.mkdir()
        (outside / "secret").write_bytes(b"foreign")
        self.make_link(outside, self.old / "linked")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "link|reparse"):
            MIGRATION.resolve_path(self.project, ".codebase-xray/linked/secret")

    def test_nested_links_block_migration_before_any_writes(self):
        values = self.evidence()
        outside = self.project / "outside"
        outside.mkdir()
        self.make_link(outside, self.old / "linked")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "link|reparse"):
            MIGRATION.migrate(self.project)
        self.assertFalse(self.new.exists())
        self.assertFalse((self.old / MIGRATION.ORIGIN_FILE).exists())
        self.assert_evidence(self.old, values)

    def test_unreadable_tree_blocks_migration(self):
        values = self.evidence()

        def unreadable_walk(root, *, followlinks=False, onerror=None):
            if onerror is not None:
                onerror(PermissionError("unreadable run directory"))
            return iter(())

        with mock.patch.object(MIGRATION.os, "walk", unreadable_walk):
            with self.assertRaisesRegex(OSError, "unreadable"):
                MIGRATION.migrate(self.project)
        self.assertFalse(self.new.exists())
        self.assert_evidence(self.old, values)

    def test_marker_bound_to_another_project_is_rejected(self):
        self.evidence()
        MIGRATION.migrate(self.project)
        marker = self.new / MIGRATION.ORIGIN_FILE
        record = json.loads(marker.read_text())
        record["project"] = str(self.project.parent / "another")
        marker.write_text(json.dumps(record))
        with self.assertRaisesRegex(MIGRATION.MigrationError, "binding"):
            MIGRATION.migrate(self.project)

    def test_interrupted_move_recovers_missing_legacy_marker(self):
        values = self.evidence()
        MIGRATION.migrate(self.project)
        (self.old / MIGRATION.REDIRECT_FILE).unlink()
        self.old.rmdir()
        result = MIGRATION.migrate(self.project)
        self.assertEqual(result["status"], "recovered")
        self.assertTrue((self.old / MIGRATION.REDIRECT_FILE).is_file())
        self.assert_evidence(self.new, values)

    def test_prepared_move_can_resume_after_interruption(self):
        values = self.evidence()
        (self.old / MIGRATION.ORIGIN_FILE).write_text(json.dumps(MIGRATION._record(self.project)))
        result = MIGRATION.migrate(self.project)
        self.assertEqual(result["status"], "migrated")
        self.assert_evidence(self.new, values)

    def test_recovery_check_is_read_only(self):
        values = self.evidence()
        MIGRATION.migrate(self.project)
        (self.old / MIGRATION.REDIRECT_FILE).unlink()
        result = MIGRATION.migrate(self.project, check=True)
        self.assertEqual(result["status"], "recovery_required")
        self.assertEqual(list(self.old.iterdir()), [])
        self.assert_evidence(self.new, values)

    def test_interrupted_redirect_temp_is_recovered_and_preserved(self):
        values = self.evidence()
        actual_write = MIGRATION._write_json_atomic
        temporary = self.old / (MIGRATION.REDIRECT_FILE + ".tmp-interrupted")

        def interrupt_redirect(path, record):
            if path.name == MIGRATION.REDIRECT_FILE:
                temporary.write_text(json.dumps(record))
                raise SystemExit("interrupted before atomic redirect publication")
            return actual_write(path, record)

        with mock.patch.object(MIGRATION, "_write_json_atomic", interrupt_redirect):
            with self.assertRaises(SystemExit):
                MIGRATION.migrate(self.project)
        temporary_bytes = temporary.read_bytes()
        result = MIGRATION.migrate(self.project)
        self.assertEqual(result["status"], "recovered")
        self.assertTrue((self.old / MIGRATION.REDIRECT_FILE).is_file())
        self.assertEqual(temporary.read_bytes(), temporary_bytes)
        self.assertEqual(MIGRATION.migrate(self.project)["status"], "current")
        self.assert_evidence(self.new, values)

    def test_check_recognizes_valid_redirect_temp_without_writing(self):
        values = self.evidence()
        MIGRATION.migrate(self.project)
        redirect = self.old / MIGRATION.REDIRECT_FILE
        temporary = self.old / (MIGRATION.REDIRECT_FILE + ".tmp-interrupted")
        redirect.rename(temporary)
        before = temporary.read_bytes()
        result = MIGRATION.migrate(self.project, check=True)
        self.assertEqual(result["status"], "recovery_required")
        self.assertFalse(redirect.exists())
        self.assertEqual(temporary.read_bytes(), before)
        self.assert_evidence(self.new, values)

    def test_partial_redirect_temp_blocks_and_preserves_both_roots(self):
        values = self.evidence()
        MIGRATION.migrate(self.project)
        (self.old / MIGRATION.REDIRECT_FILE).unlink()
        temporary = self.old / (MIGRATION.REDIRECT_FILE + ".tmp-partial")
        temporary.write_bytes(b'{"schema":"daodan/codebase-map-relocation/v1","project":')
        before = temporary.read_bytes()
        with self.assertRaises(MIGRATION.MigrationError):
            MIGRATION.migrate(self.project)
        self.assertEqual(temporary.read_bytes(), before)
        self.assertFalse((self.old / MIGRATION.REDIRECT_FILE).exists())
        self.assert_evidence(self.new, values)

    def test_foreign_redirect_temp_is_not_trusted(self):
        values = self.evidence()
        MIGRATION.migrate(self.project)
        (self.old / MIGRATION.REDIRECT_FILE).unlink()
        temporary = self.old / (MIGRATION.REDIRECT_FILE + ".tmp-foreign")
        record = MIGRATION._record(self.project)
        record["project"] = str(self.project.parent / "foreign")
        temporary.write_text(json.dumps(record))
        before = temporary.read_bytes()
        with self.assertRaises(MIGRATION.MigrationError):
            MIGRATION.migrate(self.project)
        self.assertEqual(temporary.read_bytes(), before)
        self.assert_evidence(self.new, values)

    def test_redirect_temp_does_not_hide_independent_legacy_evidence(self):
        values = self.evidence()
        MIGRATION.migrate(self.project)
        (self.old / MIGRATION.REDIRECT_FILE).unlink()
        temporary = self.old / (MIGRATION.REDIRECT_FILE + ".tmp-valid")
        temporary.write_text(json.dumps(MIGRATION._record(self.project)))
        (self.old / "foreign.md").write_bytes(b"independent evidence")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "both"):
            MIGRATION.migrate(self.project)
        self.assertEqual((self.old / "foreign.md").read_bytes(), b"independent evidence")
        self.assertTrue(temporary.is_file())
        self.assert_evidence(self.new, values)

    def test_invalid_canonical_origin_cannot_authorize_redirect_temp_recovery(self):
        values = self.evidence()
        MIGRATION.migrate(self.project)
        redirect = self.old / MIGRATION.REDIRECT_FILE
        temporary = self.old / (MIGRATION.REDIRECT_FILE + ".tmp-valid")
        redirect.rename(temporary)
        origin = self.new / MIGRATION.ORIGIN_FILE
        origin.write_bytes(b'{"project":"foreign"}')
        before = origin.read_bytes()
        with self.assertRaisesRegex(MIGRATION.MigrationError, "binding"):
            MIGRATION.migrate(self.project)
        self.assertEqual(origin.read_bytes(), before)
        self.assertTrue(temporary.is_file())
        self.assertFalse(redirect.exists())
        self.assert_evidence(self.new, values)

    def test_partial_origin_temp_before_move_is_preserved_as_content(self):
        values = self.evidence()
        temporary_name = MIGRATION.ORIGIN_FILE + ".tmp-partial"
        original = b'{"schema":'
        (self.old / temporary_name).write_bytes(original)
        MIGRATION.migrate(self.project)
        self.assertEqual((self.new / temporary_name).read_bytes(), original)
        self.assert_evidence(self.new, values)

    def test_new_legacy_evidence_after_migration_blocks_without_merging(self):
        values = self.evidence()
        MIGRATION.migrate(self.project)
        (self.old / "new-old-tool-output.md").write_bytes(b"fresh old evidence")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "additional evidence"):
            MIGRATION.migrate(self.project)
        self.assertEqual((self.old / "new-old-tool-output.md").read_bytes(), b"fresh old evidence")
        self.assert_evidence(self.new, values)

    def test_failed_move_preserves_original(self):
        values = self.evidence()
        with mock.patch.object(MIGRATION, "_rename_root", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(MIGRATION.MigrationError, "denied"):
                MIGRATION.migrate(self.project)
        self.assert_evidence(self.old, values)
        self.assertFalse(self.new.exists())
        self.assertFalse((self.old / MIGRATION.ORIGIN_FILE).exists())

    @staticmethod
    def windows_permission_error(code):
        error = PermissionError("simulated Windows rename lock")
        error.winerror = code
        return error

    def test_temporary_windows_rename_lock_retries_and_preserves_evidence(self):
        actual_rename = MIGRATION.os.rename
        for code in (5, 32, 33):
            with self.subTest(winerror=code):
                project = self.project / str(code)
                project.mkdir()
                values = self.evidence(project / MIGRATION.LEGACY_ROOT)
                attempts = []

                def temporary_lock(source, destination):
                    attempts.append((source, destination))
                    if len(attempts) == 1:
                        raise self.windows_permission_error(code)
                    return actual_rename(source, destination)

                with mock.patch.object(MIGRATION.os, "rename", temporary_lock):
                    self.assertEqual(MIGRATION.migrate(project)["status"], "migrated")
                self.assertEqual(len(attempts), 2)
                self.assert_evidence(project / MIGRATION.CANONICAL_ROOT, values)

    def test_permanent_windows_rename_lock_has_a_short_bound_and_rolls_back(self):
        values = self.evidence()
        started = time.monotonic()
        with mock.patch.object(MIGRATION.os, "rename", side_effect=self.windows_permission_error(5)) as rename:
            with self.assertRaisesRegex(MIGRATION.MigrationError, "restored"):
                MIGRATION.migrate(self.project)
        self.assertGreater(rename.call_count, 1)
        self.assertLessEqual(rename.call_count, 30)
        self.assertLess(time.monotonic() - started, 1.5)
        self.assertFalse(self.new.exists())
        self.assertFalse((self.old / MIGRATION.ORIGIN_FILE).exists())
        self.assert_evidence(self.old, values)

    def test_destination_appearing_between_rename_attempts_is_not_overwritten(self):
        values = self.evidence()

        def new_destination(source, destination):
            destination.mkdir()
            (destination / "foreign.md").write_bytes(b"unrelated concurrent evidence")
            raise self.windows_permission_error(5)

        with mock.patch.object(MIGRATION.os, "rename", side_effect=new_destination) as rename:
            with self.assertRaisesRegex(MIGRATION.MigrationError, "destination appeared"):
                MIGRATION.migrate(self.project)
        self.assertEqual(rename.call_count, 1)
        self.assertEqual((self.new / "foreign.md").read_bytes(), b"unrelated concurrent evidence")
        self.assert_evidence(self.old, values)

    def test_active_state_appearing_between_attempts_stops_the_retry(self):
        values = self.evidence()

        def writer_started(source, destination):
            (source / "runs.json").write_text('{"active":[{"run_id":"new-active"}]}')
            raise self.windows_permission_error(32)

        with mock.patch.object(MIGRATION.os, "rename", side_effect=writer_started) as rename:
            with self.assertRaisesRegex(MIGRATION.MigrationError, "active"):
                MIGRATION.migrate(self.project)
        self.assertEqual(rename.call_count, 1)
        self.assertFalse(self.new.exists())
        values.pop("runs.json")
        self.assert_evidence(self.old, values)
        self.assertEqual(json.loads((self.old / "runs.json").read_text())["active"][0]["run_id"], "new-active")

    def test_unknown_permission_error_does_not_retry(self):
        values = self.evidence()
        for error in (PermissionError("ordinary permission failure"), self.windows_permission_error(87)):
            with self.subTest(error=str(error)):
                with mock.patch.object(MIGRATION.os, "rename", side_effect=error) as rename:
                    with self.assertRaises(MIGRATION.MigrationError):
                        MIGRATION.migrate(self.project)
                self.assertEqual(rename.call_count, 1)
                self.assertFalse(self.new.exists())
                self.assert_evidence(self.old, values)

    def test_failed_redirect_rolls_back_original_and_empty_destination(self):
        values = self.evidence()
        self.new.mkdir()
        with mock.patch.object(MIGRATION, "_write_redirect", side_effect=PermissionError("redirect denied")):
            with self.assertRaisesRegex(MIGRATION.MigrationError, "redirect denied"):
                MIGRATION.migrate(self.project)
        self.assert_evidence(self.old, values)
        self.assertEqual(list(self.new.iterdir()), [])
        self.assertFalse((self.old / MIGRATION.ORIGIN_FILE).exists())

    def test_rollback_failure_leaves_evidence_in_canonical_root(self):
        values = self.evidence()
        actual_rename = MIGRATION._rename_root

        def fail_rollback(source, destination):
            if source == self.new:
                raise PermissionError("rollback denied")
            return actual_rename(source, destination)

        with mock.patch.object(MIGRATION, "_rename_root", side_effect=fail_rollback):
            with mock.patch.object(MIGRATION, "_write_redirect", side_effect=PermissionError("redirect denied")):
                with self.assertRaisesRegex(MIGRATION.MigrationError, "rollback"):
                    MIGRATION.migrate(self.project)
        self.assert_evidence(self.new, values)
        self.assertTrue((self.new / MIGRATION.ORIGIN_FILE).exists())

    def test_concurrent_preflights_keep_relocation_metadata_and_evidence(self):
        for iteration in range(10):
            project = self.project / f"concurrent-{iteration}"
            project.mkdir()
            values = self.evidence(project / MIGRATION.LEGACY_ROOT)
            ready = threading.Barrier(4)

            def invoke():
                ready.wait(timeout=5)
                return MIGRATION.migrate(project)["status"]

            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(invoke) for _ in range(4)]
                results = [future.result(timeout=10) for future in futures]
            with self.subTest(iteration=iteration):
                self.assertEqual(results.count("migrated"), 1)
                self.assertEqual(results.count("current"), 3)
                self.assertEqual(MIGRATION.migrate(project)["status"], "current")
                self.assertTrue((project / MIGRATION.CANONICAL_ROOT / MIGRATION.ORIGIN_FILE).is_file())
                self.assert_evidence(project / MIGRATION.CANONICAL_ROOT, values)

    def test_concurrent_process_preflights_share_project_lock(self):
        values = self.evidence()
        command = [sys.executable, str(HELPER), "--project", str(self.project)]
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(4)]
        results = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, stderr + stdout)
            results.append(json.loads(stdout)["status"])
        self.assertEqual(results.count("migrated"), 1)
        self.assertEqual(results.count("current"), 3)
        self.assert_evidence(self.new, values)

    def test_project_lock_wait_is_bounded(self):
        self.evidence()
        with mock.patch.object(MIGRATION, "LOCK_TIMEOUT_SECONDS", 0.1):
            with MIGRATION._migration_lock(self.project):
                with ThreadPoolExecutor(max_workers=1) as pool:
                    started = time.monotonic()
                    future = pool.submit(MIGRATION.migrate, self.project)
                    with self.assertRaisesRegex(MIGRATION.MigrationError, "lock"):
                        future.result(timeout=3)
                    self.assertLess(time.monotonic() - started, 2)
        self.assertFalse(self.new.exists())

    def test_abrupt_lock_owner_exit_does_not_leave_a_stale_filesystem_lock(self):
        values = self.evidence()
        program = (
            "import importlib.util,os,sys;from pathlib import Path;"
            "s=importlib.util.spec_from_file_location('migration',sys.argv[1]);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "lock=m._migration_lock(Path(sys.argv[2]));lock.__enter__();"
            "print('locked',flush=True);sys.stdin.readline();os._exit(0)"
        )
        process = subprocess.Popen([sys.executable, "-c", program, str(HELPER), str(self.project)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline(), "locked\n")
            with ThreadPoolExecutor(max_workers=1) as pool:
                waiter = pool.submit(MIGRATION.migrate, self.project)
                time.sleep(0.05)
                stdout, stderr = process.communicate("exit\n", timeout=10)
                self.assertEqual(process.returncode, 0, stderr + stdout)
                self.assertEqual(waiter.result(timeout=10)["status"], "migrated")
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)
        self.assert_evidence(self.new, values)

    def test_cli_uses_json_and_failure_exit_code(self):
        self.evidence()
        check = subprocess.run([sys.executable, str(HELPER), "--project", str(self.project), "--check"], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertEqual(json.loads(check.stdout)["status"], "migration_required")
        self.assertFalse(self.new.exists())
        run = subprocess.run([sys.executable, str(HELPER), "--project", str(self.project)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["status"], "migrated")
        resolved = subprocess.run([sys.executable, str(HELPER), "resolve", "--project", str(self.project), ".codebase-xray/07-final-report.md"], capture_output=True, text=True)
        self.assertEqual(resolved.returncode, 0, resolved.stderr)
        self.assertEqual(Path(json.loads(resolved.stdout)["path"]), self.new / "07-final-report.md")
        failure = subprocess.run([sys.executable, str(HELPER), "resolve", "--project", str(self.project), "../foreign"], capture_output=True, text=True)
        self.assertEqual(failure.returncode, 1, failure.stderr)
        self.assertEqual(json.loads(failure.stdout)["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
