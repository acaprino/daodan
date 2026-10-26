"""Real Git fixtures for worktree identity, preservation and interrupted creation."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/worktree-manager/skills/worktree-method/scripts/workspaces.py"
SPEC = importlib.util.spec_from_file_location("daodan_workspaces", SCRIPT)
workspaces = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workspaces)


class WorktreeCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(os.environ.get("DAODAN_TEST_TMPDIR", tempfile.gettempdir())).resolve()
        self.temp = Path(tempfile.mkdtemp(prefix="daodan-worktree-test-", dir=self.temp_root)).resolve()
        self.addCleanup(self.remove_temp)
        self.project = self.temp / "main checkout"
        self.project.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Test fixture")
        self.git("config", "commit.gpgsign", "false")
        (self.project / ".gitignore").write_text(".daodan/\nignored.txt\n", encoding="utf-8")
        (self.project / "app.txt").write_text("original\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-m", "Fixture baseline")
        self.base = self.git("rev-parse", "HEAD").strip()

    def remove_temp(self):
        self.assertTrue(self.temp.is_relative_to(self.temp_root))
        def writable_remove(function, path, _error):
            os.chmod(path, stat.S_IWRITE)
            function(path)
        shutil.rmtree(self.temp, onerror=writable_remove)

    def git(self, *args, project=None):
        result = subprocess.run(["git", "-C", str(project or self.project), *args],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def backend(self, project, args, executable=None):
        self.assertEqual(args[0:2], ["switch", "--create"])
        self.assertIn("--no-hooks", args)
        self.assertIn("--no-cd", args)
        self.git("worktree", "add", "-b", args[2], args[args.index("--path") + 1],
                 args[args.index("--base") + 1], project=project)
        return {"schema_version": 1}

    def create(self, **kwargs):
        options = {"task_id": "task-123", "kind": "fix", "slug": "login-timeout", "base": self.base}
        options.update(kwargs)
        with patch.object(workspaces, "run_worktrunk", side_effect=self.backend):
            return workspaces.create(self.project, **options)

    def test_list_is_read_only_and_includes_external_detached_and_main(self):
        external = self.temp / "external checkout"
        self.git("worktree", "add", "--detach", str(external), self.base)
        result = workspaces.list_workspaces(external)
        self.assertEqual(Path(result["home"]), self.project)
        self.assertEqual(len(result["worktrees"]), 2)
        self.assertEqual(sum(bool(row["main"]) for row in result["worktrees"]), 1)
        self.assertTrue(next(row for row in result["worktrees"] if not row["main"])["detached"])
        self.assertFalse((self.project / ".daodan").exists())

    def test_annotations_share_main_catalog_and_survive_worktree_removal(self):
        external = self.temp / "external checkout"
        self.git("worktree", "add", "--detach", str(external), self.base)
        workspaces.annotate(external, external, "Investigate cache", ["analysis", "cache", "cache"])
        self.assertFalse((external / ".daodan").exists())
        self.git("worktree", "remove", str(external))
        result = workspaces.list_workspaces(self.project)
        self.assertEqual(result["missing"][0]["description"], "Investigate cache")
        self.assertEqual(result["missing"][0]["tags"], ["analysis", "cache"])
        self.assertEqual(len(result["worktrees"]), 1)

    def test_tag_deltas_preserve_changes_after_two_clients_read_one_revision(self):
        external = self.temp / "external checkout"
        self.git("worktree", "add", "--detach", str(external), self.base)
        initial = workspaces.annotate(self.project, self.project, tags=["initial", "obsolete"])
        first_read = workspaces.list_workspaces(self.project)
        second_read = workspaces.list_workspaces(external)
        self.assertEqual(first_read["revision"], second_read["revision"])
        workspaces.annotate(self.project, self.project, add_tags=["alpha"], remove_tags=["obsolete"])
        second = workspaces.annotate(external, self.project, add_tags=["beta"], remove_tags=["initial"])
        self.assertEqual(second["entry"]["tags"], ["alpha", "beta"])
        self.assertEqual(second["revision"], initial["revision"] + 2)
        replaced = workspaces.annotate(external, self.project, tags=["replacement"])
        self.assertEqual(replaced["entry"]["tags"], ["replacement"])

    def test_tag_delta_limit_failure_preserves_previous_catalog(self):
        initial = workspaces.annotate(self.project, self.project, tags=[f"tag-{number}" for number in range(32)])
        catalog = self.project / ".daodan/worktrees.json"
        before = catalog.read_bytes()
        with self.assertRaisesRegex(workspaces.WorkspaceError, "at most 32"):
            workspaces.annotate(self.project, self.project, add_tags=["extra"])
        self.assertEqual(catalog.read_bytes(), before)
        changed = workspaces.annotate(self.project, self.project, add_tags=["extra"], remove_tags=["tag-0"])
        self.assertIn("extra", changed["entry"]["tags"])
        self.assertNotIn("tag-0", changed["entry"]["tags"])
        self.assertEqual(changed["revision"], initial["revision"] + 1)

    def test_tag_cli_deltas_and_conflicting_modes(self):
        workspaces.annotate(self.project, self.project, tags=["initial", "keep"])
        arguments = [sys.executable, str(SCRIPT), "--project", str(self.project), "annotate", "--path", str(self.project)]
        changed = subprocess.run(arguments + ["--add-tag", "new", "--remove-tag", "initial"],
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(changed.returncode, 0, changed.stderr)
        self.assertEqual(json.loads(changed.stdout)["entry"]["tags"], ["keep", "new"])
        catalog = self.project / ".daodan/worktrees.json"
        before = catalog.read_bytes()
        conflicts = (["--tag", "replace", "--add-tag", "new"],
                     ["--tag", "replace", "--remove-tag", "keep"],
                     ["--clear-tags", "--add-tag", "new"],
                     ["--clear-tags", "--remove-tag", "keep"],
                     ["--tag", "replace", "--clear-tags"],
                     ["--add-tag", "same", "--remove-tag", "same"])
        for options in conflicts:
            with self.subTest(options=options):
                rejected = subprocess.run(arguments + options, capture_output=True, text=True, timeout=30)
                self.assertEqual(rejected.returncode, 1, rejected.stdout)
                self.assertEqual(json.loads(rejected.stderr)["error"], "invalid_metadata")
                self.assertEqual(catalog.read_bytes(), before)
        cleared = subprocess.run(arguments + ["--clear-tags"], capture_output=True, text=True, timeout=30)
        self.assertEqual(cleared.returncode, 0, cleared.stderr)
        self.assertEqual(json.loads(cleared.stdout)["entry"]["tags"], [])

    def test_oversized_utf8_annotation_preserves_readable_catalog_and_revision(self):
        initial = workspaces.annotate(self.project, self.project, "Main")
        catalog = workspaces.load_catalog(self.project)
        def encoded():
            return (json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        def retained(number):
            path = self.temp / f"retained-{number:05d}"
            return workspaces.key(path), {"path": str(path), "managed": False, "description": "界" * 500, "tags": []}
        base_size = len(encoded())
        identity, entry = retained(0)
        catalog["entries"][identity] = entry
        entry_size = len(encoded()) - base_size
        count = (workspaces.CATALOG_LIMIT - base_size - 128) // entry_size
        for number in range(1, count):
            identity, entry = retained(number)
            catalog["entries"][identity] = entry
        before = encoded()
        self.assertLessEqual(len(before), workspaces.CATALOG_LIMIT)
        self.assertLess(workspaces.CATALOG_LIMIT - len(before), entry_size + 128)
        path = self.project / ".daodan/worktrees.json"
        path.write_bytes(before)
        self.assertEqual(workspaces.list_workspaces(self.project)["revision"], initial["revision"])
        with self.assertRaisesRegex(workspaces.WorkspaceError, "previous catalog is unchanged"):
            workspaces.annotate(self.project, self.project, "界" * 500,
                                [f"{number:02d}" + "界" * 62 for number in range(32)])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(workspaces.list_workspaces(self.project)["revision"], initial["revision"])
        self.assertEqual(list(path.parent.glob(".worktrees-*.tmp")), [])
        self.assertFalse((path.parent / ".worktrees.lock").exists())
        updated = workspaces.annotate(self.project, self.project, "Main updated")
        self.assertEqual(updated["revision"], initial["revision"] + 1)

    def test_create_is_confined_and_preserves_all_preexisting_files(self):
        (self.project / "app.txt").write_text("dirty\n", encoding="utf-8")
        (self.project / "untracked.txt").write_text("untracked", encoding="utf-8")
        (self.project / "ignored.txt").write_text("ignored", encoding="utf-8")
        before = self.git("status", "--porcelain")
        result = self.create(description="Repair timeout", tags=["login"])
        target = Path(result["entry"]["path"])
        self.assertTrue(target.is_relative_to(self.project / ".daodan/worktrees"))
        self.assertTrue(result["entry"]["branch"].startswith("task/fix/login-timeout-"))
        self.assertEqual(self.git("status", "--porcelain"), before)
        self.assertEqual((self.project / "ignored.txt").read_text(), "ignored")
        self.assertEqual((target / "app.txt").read_text(), "original\n")

    def test_create_from_nested_worktree_uses_one_catalog_and_main_root(self):
        first = self.create()
        with patch.object(workspaces, "run_worktrunk", side_effect=self.backend):
            second = workspaces.create(Path(first["entry"]["path"]), "second", "analysis", "cache", self.base)
        self.assertTrue(Path(second["entry"]["path"]).is_relative_to(self.project / ".daodan/worktrees"))
        self.assertEqual(len(workspaces.list_workspaces(self.project)["worktrees"]), 3)

    def test_repeated_create_resumes_without_overwriting_annotations(self):
        first = self.create(description="Initial")
        workspaces.annotate(self.project, first["entry"]["path"], "User description", ["urgent"])
        with patch.object(workspaces, "run_worktrunk") as backend:
            second = workspaces.create(self.project, "task-123", "fix", "login-timeout", self.base)
        backend.assert_not_called()
        self.assertEqual(second["action"], "resumed")
        self.assertEqual(second["entry"]["description"], "User description")
        self.assertEqual(second["entry"]["tags"], ["urgent"])

    def test_resume_reports_actual_descendant_head(self):
        first = self.create()
        target = Path(first["entry"]["path"])
        (target / "app.txt").write_text("task change\n", encoding="utf-8")
        self.git("add", "app.txt", project=target)
        self.git("commit", "-m", "Task change", project=target)
        head = self.git("rev-parse", "HEAD", project=target).strip()
        self.assertNotEqual(head, self.base)
        resumed = self.create()
        self.assertEqual(resumed["action"], "resumed")
        self.assertEqual(resumed["head"], head)

    def test_relative_worktree_links_create_and_resume(self):
        self.git("config", "worktree.useRelativePaths", "true")
        first = self.create()
        target = Path(first["entry"]["path"])
        gitfile = (target / ".git").read_text(encoding="utf-8").strip().removeprefix("gitdir: ")
        if Path(gitfile).is_absolute():
            self.skipTest("Installed Git does not support worktree.useRelativePaths")
        resumed = self.create()
        self.assertEqual(resumed["action"], "resumed")
        self.assertEqual(resumed["entry"]["path"], first["entry"]["path"])

    def replace_checkout(self, target, foreign=True):
        moved = self.temp / f"preserved-{target.name}"
        self.assertTrue(target.resolve().is_relative_to(self.temp))
        self.assertTrue(moved.resolve().is_relative_to(self.temp))
        target.rename(moved)
        target.mkdir()
        (target / "keep.txt").write_text("replacement contents", encoding="utf-8")
        if foreign:
            self.git("init", "-b", "foreign", project=target)
            self.git("-c", "user.name=Test fixture", "-c", "user.email=fixture@example.invalid",
                     "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "Foreign baseline", project=target)
        return moved

    def test_replaced_checkout_cannot_resume_or_change_catalog(self):
        for foreign in (True, False):
            with self.subTest(foreign=foreign):
                # Each subcase has a separate managed path and preserved checkout.
                result = self.create(task_id=f"replacement-{foreign}", slug=f"replacement-{str(foreign).lower()}")
                target = Path(result["entry"]["path"])
                moved = self.replace_checkout(target, foreign)
                catalog = self.project / ".daodan/worktrees.json"
                before = catalog.read_bytes()
                with self.assertRaises(workspaces.WorkspaceError) as raised:
                    self.create(task_id=f"replacement-{foreign}", slug=f"replacement-{str(foreign).lower()}")
                self.assertEqual(raised.exception.code, "checkout_mismatch" if foreign else "missing_worktree")
                self.assertEqual(catalog.read_bytes(), before)
                self.assertEqual((target / "keep.txt").read_text(), "replacement contents")
                self.assertEqual((moved / "app.txt").read_text(), "original\n")

    def test_foreign_linked_checkout_cannot_resume(self):
        first = self.create()
        target = Path(first["entry"]["path"])
        moved = self.temp / "preserved-checkout"
        self.assertTrue(target.resolve().is_relative_to(self.temp))
        self.assertTrue(moved.resolve().is_relative_to(self.temp))
        target.rename(moved)
        foreign = self.temp / "foreign repository"
        foreign.mkdir()
        self.git("init", "-b", "foreign", project=foreign)
        (foreign / "foreign.txt").write_text("foreign contents", encoding="utf-8")
        self.git("add", "foreign.txt", project=foreign)
        self.git("-c", "user.name=Test fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-m", "Foreign baseline", project=foreign)
        self.git("worktree", "add", "-b", "foreign-linked", str(target), "HEAD", project=foreign)
        self.assertTrue((target / ".git").is_file())
        before = (self.project / ".daodan/worktrees.json").read_bytes()
        with self.assertRaises(workspaces.WorkspaceError) as raised:
            self.create()
        self.assertEqual(raised.exception.code, "checkout_mismatch")
        self.assertEqual((self.project / ".daodan/worktrees.json").read_bytes(), before)
        self.assertEqual((moved / "app.txt").read_text(), "original\n")
        self.assertEqual((target / "foreign.txt").read_text(), "foreign contents")
        self.assertEqual((foreign / "foreign.txt").read_text(), "foreign contents")

    def test_postcreate_replacement_stays_reserved_and_preserves_both_checkouts(self):
        preserved = []
        def replace_after_creation(project, args, executable=None):
            self.backend(project, args, executable)
            preserved.append(self.replace_checkout(Path(args[args.index("--path") + 1])))
        with patch.object(workspaces, "run_worktrunk", side_effect=replace_after_creation):
            with self.assertRaises(workspaces.WorkspaceError) as raised:
                workspaces.create(self.project, "task-123", "fix", "login-timeout", self.base)
        self.assertEqual(raised.exception.code, "checkout_mismatch")
        catalog = workspaces.load_catalog(self.project)
        entry = next(iter(catalog["entries"].values()))
        self.assertEqual(entry["creation"], "reserved")
        self.assertEqual(catalog["revision"], 1)
        self.assertEqual((Path(entry["path"]) / "keep.txt").read_text(), "replacement contents")
        self.assertEqual((preserved[0] / "app.txt").read_text(), "original\n")

    def test_interruption_after_git_creation_is_reconciled_without_second_create(self):
        def partial(project, args, executable=None):
            self.backend(project, args, executable)
            raise workspaces.WorkspaceError("backend_timeout", "Simulated timeout after Git completed")
        with patch.object(workspaces, "run_worktrunk", side_effect=partial):
            with self.assertRaisesRegex(workspaces.WorkspaceError, "Simulated timeout"):
                workspaces.create(self.project, "task-123", "fix", "login-timeout", self.base)
        reserved = next(iter(workspaces.load_catalog(self.project)["entries"].values()))
        self.assertEqual(reserved["creation"], "reserved")
        self.assertFalse((self.project / ".daodan/.worktrees.lock").exists())
        with patch.object(workspaces, "run_worktrunk") as backend:
            result = workspaces.create(self.project, "task-123", "fix", "login-timeout", self.base)
        backend.assert_not_called()
        self.assertEqual(result["entry"]["creation"], "confirmed")
        self.assertEqual(len(workspaces.inventory(self.project)), 2)

    def test_failure_before_git_creation_retries_same_reservation(self):
        with patch.object(workspaces, "run_worktrunk", side_effect=workspaces.WorkspaceError("missing", "Missing backend")):
            with self.assertRaises(workspaces.WorkspaceError):
                workspaces.create(self.project, "task-123", "fix", "login-timeout", self.base)
        result = self.create()
        self.assertEqual(result["action"], "created")
        self.assertEqual(len(workspaces.load_catalog(self.project)["entries"]), 1)

    def test_existing_branch_without_workspace_is_not_adopted(self):
        with patch.object(workspaces, "run_worktrunk", side_effect=workspaces.WorkspaceError("missing", "Missing backend")):
            with self.assertRaises(workspaces.WorkspaceError):
                workspaces.create(self.project, "task-123", "fix", "login-timeout", self.base)
        entry = next(iter(workspaces.load_catalog(self.project)["entries"].values()))
        self.git("branch", entry["branch"], self.base)
        with self.assertRaisesRegex(workspaces.WorkspaceError, "target branch exists"):
            self.create()
        self.assertFalse(Path(entry["path"]).exists())

    def test_existing_path_without_registration_is_preserved(self):
        with patch.object(workspaces, "run_worktrunk", side_effect=workspaces.WorkspaceError("missing", "Missing backend")):
            with self.assertRaises(workspaces.WorkspaceError):
                workspaces.create(self.project, "task-123", "fix", "login-timeout", self.base)
        entry = next(iter(workspaces.load_catalog(self.project)["entries"].values()))
        occupied = Path(entry["path"])
        occupied.mkdir()
        (occupied / "keep.txt").write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(workspaces.WorkspaceError, "target path already exists"):
            self.create()
        self.assertEqual((occupied / "keep.txt").read_text(), "keep")

    def test_changed_task_name_and_changed_base_are_rejected(self):
        self.create()
        with self.assertRaisesRegex(workspaces.WorkspaceError, "different name"):
            self.create(slug="different")
        (self.project / "new.txt").write_text("new", encoding="utf-8")
        self.git("add", "new.txt")
        self.git("commit", "-m", "Move target")
        with self.assertRaisesRegex(workspaces.WorkspaceError, "creation identity"):
            self.create(base="main")

    def test_unignored_location_is_rejected_without_state_creation(self):
        (self.project / ".gitignore").write_text("", encoding="utf-8")
        with self.assertRaisesRegex(workspaces.WorkspaceError, "must already be ignored"):
            self.create()
        self.assertFalse((self.project / ".daodan").exists())

    def test_ignoring_only_worktrees_is_not_enough_to_protect_the_catalog(self):
        (self.project / ".gitignore").write_text(".daodan/worktrees/\n", encoding="utf-8")
        with self.assertRaisesRegex(workspaces.WorkspaceError, "must already be ignored"):
            self.create()
        self.assertFalse((self.project / ".daodan").exists())

    def test_git_environment_cannot_redirect_repository_probes(self):
        with patch.dict(os.environ, {"GIT_DIR": str(self.temp / "foreign.git"), "GIT_WORK_TREE": str(self.temp)}):
            result = workspaces.list_workspaces(self.project)
        self.assertEqual(Path(result["home"]), self.project)

    def test_missing_registered_directory_cannot_resume_as_success(self):
        result = self.create()
        target = Path(result["entry"]["path"])
        # Move only this test-owned directory. Git retains a stale registration.
        moved = self.temp / "moved-checkout"
        self.assertTrue(target.resolve().is_relative_to(self.temp))
        target.rename(moved)
        with self.assertRaisesRegex(workspaces.WorkspaceError, "missing checkout"):
            self.create()

    @unittest.skipUnless(os.environ.get("DAODAN_WORKTRUNK_EXECUTABLE"), "Set DAODAN_WORKTRUNK_EXECUTABLE for the live pinned-binary probe")
    def test_live_worktrunk_create_and_resume(self):
        arguments = [sys.executable, str(SCRIPT), "--project", str(self.project), "create",
                     "--task-id", "live", "--kind", "analysis", "--slug", "live-probe", "--base", self.base,
                     "--executable", os.environ.get("DAODAN_WORKTRUNK_EXECUTABLE", "")]
        first = subprocess.run(arguments, capture_output=True, text=True, timeout=60)
        self.assertEqual(first.returncode, 0, first.stderr)
        created = json.loads(first.stdout)
        self.assertEqual(created["action"], "created")
        self.assertEqual(Path(created["entry"]["path"]).parent, self.project / ".daodan/worktrees")
        second = subprocess.run(arguments, capture_output=True, text=True, timeout=60)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout)["action"], "resumed")
        self.assertEqual(len(workspaces.inventory(self.project)), 2)

    def test_lock_is_not_stolen_and_catalog_is_unchanged(self):
        workspaces.annotate(self.project, self.project, "Main")
        catalog = self.project / ".daodan/worktrees.json"
        before = catalog.read_bytes()
        lock = self.project / ".daodan/.worktrees.lock"
        lock.write_text('{"pid":123}', encoding="utf-8")
        with self.assertRaisesRegex(workspaces.WorkspaceError, "Another catalog writer"):
            workspaces.annotate(self.project, self.project, "Overwrite")
        self.assertEqual(catalog.read_bytes(), before)
        self.assertTrue(lock.exists())

    def test_symlink_state_root_is_rejected(self):
        outside = self.temp / "outside"
        outside.mkdir()
        try:
            (self.project / ".daodan").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Platform does not permit symlink creation")
        with self.assertRaisesRegex(workspaces.WorkspaceError, "contains a link"):
            self.create()
        self.assertEqual(list(outside.iterdir()), [])

    def test_malformed_catalog_is_preserved(self):
        root = workspaces.ensure_state_home(self.project)
        catalog = root / "worktrees.json"
        catalog.write_text('{"schema":"another-owner"}', encoding="utf-8")
        before = catalog.read_bytes()
        with self.assertRaisesRegex(workspaces.WorkspaceError, "Catalog schema"):
            workspaces.annotate(self.project, self.project, "Main")
        self.assertEqual(catalog.read_bytes(), before)

    def test_caller_supplied_path_and_branch_injections_do_not_execute(self):
        for slug in ("../escape", "word;command", "word/name"):
            with self.subTest(slug=slug), self.assertRaises(workspaces.WorkspaceError):
                self.create(slug=slug)
        with self.assertRaises(workspaces.WorkspaceError):
            self.create(prefix="../escape")
        self.assertFalse((self.project / ".daodan").exists())


if __name__ == "__main__":
    unittest.main()
