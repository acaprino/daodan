"""Confinement contracts: bind one project, refuse links and serialize helpers."""

from __future__ import annotations

import importlib.util
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


HELPER = Path(os.environ.get(
    "CODEBASE_MAP_CONFINEMENT_HELPER",
    Path(__file__).resolve().parents[1]
    / "plugins/codebase-map/skills/map-method/scripts/confinement.py",
))
SPEC = importlib.util.spec_from_file_location("codebase_map_confinement", HELPER)
assert SPEC and SPEC.loader
CONFINEMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONFINEMENT)


class ConfinementTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=os.environ.get("CODEBASE_MAP_TEST_TEMP"))
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve()

    def make_link(self, target, link):
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlink creation unavailable: {error}")

    def test_project_must_be_an_existing_directory(self):
        with self.assertRaisesRegex(CONFINEMENT.ConfinementError, "existing directory"):
            CONFINEMENT.bind_project(self.project / "missing")

    def test_linked_path_is_rejected(self):
        outside = self.project / "outside"
        outside.mkdir()
        link = self.project / "linked"
        self.make_link(outside, link)
        with self.assertRaisesRegex(CONFINEMENT.ConfinementError, "link|reparse"):
            CONFINEMENT.reject_link_chain(link / "artifact")

    def test_linked_project_is_rejected(self):
        outside = self.project / "outside"
        outside.mkdir()
        link = self.project / "linked"
        self.make_link(outside, link)
        with self.assertRaisesRegex(CONFINEMENT.ConfinementError, "link|reparse"):
            CONFINEMENT.bind_project(link)

    def test_windows_reparse_point_is_rejected_without_symlink_privileges(self):
        root = self.project / "root"
        root.mkdir()
        actual_lstat = Path.lstat

        def reparse_lstat(path, *args, **kwargs):
            result = actual_lstat(path, *args, **kwargs)
            if path == root:
                return mock.Mock(st_mode=result.st_mode, st_file_attributes=0x400)
            return result

        with mock.patch.object(Path, "lstat", reparse_lstat):
            with self.assertRaisesRegex(CONFINEMENT.ConfinementError, "link|reparse"):
                CONFINEMENT.reject_link(root)

    def test_project_lock_wait_is_bounded(self):
        with mock.patch.object(CONFINEMENT, "LOCK_TIMEOUT_SECONDS", 0.1):
            with CONFINEMENT.project_lock(self.project):
                def contend():
                    with CONFINEMENT.project_lock(self.project):
                        pass

                with ThreadPoolExecutor(max_workers=1) as pool:
                    started = time.monotonic()
                    future = pool.submit(contend)
                    with self.assertRaisesRegex(CONFINEMENT.ConfinementError, "lock"):
                        future.result(timeout=3)
                    self.assertLess(time.monotonic() - started, 2)

    def test_abrupt_lock_owner_exit_does_not_leave_a_stale_lock(self):
        program = (
            "import importlib.util,os,sys;from pathlib import Path;"
            "s=importlib.util.spec_from_file_location('confinement',sys.argv[1]);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "lock=m.project_lock(Path(sys.argv[2]));lock.__enter__();"
            "print('locked',flush=True);sys.stdin.readline();os._exit(0)"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", program, str(HELPER), str(self.project)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )

        def acquire():
            with CONFINEMENT.project_lock(self.project):
                return True

        try:
            self.assertEqual(process.stdout.readline(), "locked\n")
            with ThreadPoolExecutor(max_workers=1) as pool:
                waiter = pool.submit(acquire)
                time.sleep(0.05)
                stdout, stderr = process.communicate("exit\n", timeout=10)
                self.assertEqual(process.returncode, 0, stderr + stdout)
                self.assertTrue(waiter.result(timeout=10))
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)


if __name__ == "__main__":
    unittest.main()
