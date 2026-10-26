"""Contracts for delegated Worktrunk identity, JSON and upstream update checks."""

from contextlib import chdir, contextmanager
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import urllib.error


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/worktree-manager/skills/worktree-method/scripts/worktrunk_runtime.py"
spec = importlib.util.spec_from_file_location("worktrunk_runtime_under_test", SCRIPT)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("DAODAN_TEST_TMPDIR"))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = self.root / "git-wt.exe"
        self.binary.touch()
        self.git_directory = str(Path(shutil.which("git")).parent)

    def external_directory(self):
        directory = tempfile.TemporaryDirectory(dir=os.environ.get("DAODAN_TEST_TMPDIR"))
        self.addCleanup(directory.cleanup)
        return Path(directory.name)

    def automatic_probe(self, entries, project=None):
        environment = {"PATH": os.pathsep.join([*map(str, entries), self.git_directory])}
        with chdir(self.root), patch.dict(os.environ, environment):
            os.environ.pop("NoDefaultCurrentDirectoryInExePath", None)
            before = dict(os.environ)
            try:
                return runtime.probe(project=project or self.root)
            finally:
                self.assertEqual(dict(os.environ), before)

    @contextmanager
    def non_repository_cwd(self, current):
        # Owned scratch is below the source repository. Model only the external
        # cwd's no-repository response; target-repository Git calls stay real.
        workspace = runtime._workspace_module()
        git = workspace.git

        def inspect(project, *arguments, **options):
            if Path(project).resolve() == current.resolve():
                self.assertEqual(arguments, ("rev-parse", "--is-inside-work-tree"))
                return self.completed("", 128)
            return git(project, *arguments, **options)

        with chdir(current), patch.object(runtime, "_workspace_module", return_value=workspace), patch.object(workspace, "git", side_effect=inspect):
            yield

    def completed(self, text, code=0, stderr=""):
        return subprocess.CompletedProcess([], code, text, stderr)

    def repository(self):
        subprocess.run(["git", "init", "-b", "main", str(self.root)], check=True, capture_output=True)
        name = "git-wt.exe" if os.name == "nt" else "wt"
        executable = self.root / ".daodan/tools/worktrunk/0.81.0" / name
        executable.parent.mkdir(parents=True)
        executable.touch()
        (self.root / ".daodan/.daodan-root").touch()
        with (self.root / ".git/info/exclude").open("a", encoding="utf-8") as stream:
            stream.write("\n/.daodan/\n")
        return executable

    def test_project_runtime_precedes_path_discovery(self):
        executable = self.repository()
        with patch.object(runtime, "_execute", return_value=self.completed("wt v0.81.0")), patch.object(runtime, "_path_executable") as which:
            result = runtime.probe(project=self.root)
        self.assertEqual(Path(result["executable"]), executable)
        which.assert_not_called()

    def test_nested_worktree_discovers_main_checkout_runtime(self):
        executable = self.repository()
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Probe", "-c", "user.email=probe@example.invalid", "commit", "--allow-empty", "-m", "Probe"], check=True, capture_output=True)
        nested = self.root / ".daodan/worktrees/nested"
        subprocess.run(["git", "-C", str(self.root), "worktree", "add", "-b", "nested", str(nested)], check=True, capture_output=True)
        with patch.object(runtime, "_execute", return_value=self.completed("wt v0.81.0")), patch.object(runtime, "_path_executable") as which:
            result = runtime.probe(project=nested)
        self.assertEqual(Path(result["executable"]), executable)
        which.assert_not_called()

    def test_managed_runtime_symlink_is_refused(self):
        executable = self.repository()
        executable.unlink()
        try:
            executable.symlink_to(self.binary)
        except OSError as error:
            self.skipTest(f"Creating symlinks is unavailable: {error}")
        with patch.object(runtime, "_execute") as execute, patch.object(runtime, "_path_executable") as which:
            with self.assertRaises(runtime.WorktrunkError) as error:
                runtime.probe(project=self.root)
        self.assertEqual(error.exception.code, "linked_path")
        execute.assert_not_called()
        which.assert_not_called()

    def test_invalid_project_does_not_silently_use_path(self):
        with patch.object(runtime, "_path_executable") as which:
            with self.assertRaises(runtime.WorktrunkError) as error:
                runtime.probe(project=self.root / "missing-project")
        self.assertEqual(error.exception.code, "git_failed")
        which.assert_not_called()

    def test_tracked_managed_executable_is_never_run(self):
        executable = self.repository()
        subprocess.run(["git", "-C", str(self.root), "add", "--force", "--", str(executable)], check=True, capture_output=True)
        with patch.object(runtime, "_execute") as execute, patch.object(runtime, "_path_executable") as which:
            with self.assertRaises(runtime.WorktrunkError) as error:
                runtime.probe(project=self.root)
        self.assertEqual(error.exception.code, "untrusted_runtime")
        execute.assert_not_called()
        which.assert_not_called()

    def test_managed_runtime_without_sentinel_is_never_run(self):
        self.repository()
        (self.root / ".daodan/.daodan-root").unlink()
        with patch.object(runtime, "_execute") as execute, patch.object(runtime, "_path_executable") as which:
            with self.assertRaises(runtime.WorktrunkError) as error:
                runtime.probe(project=self.root)
        self.assertEqual(error.exception.code, "unowned_runtime")
        execute.assert_not_called()
        which.assert_not_called()

    def test_unignored_managed_executable_is_never_run(self):
        self.repository()
        (self.root / ".git/info/exclude").write_text("", encoding="utf-8")
        with patch.object(runtime, "_execute") as execute:
            with self.assertRaises(runtime.WorktrunkError) as error:
                runtime.probe(project=self.root)
        self.assertEqual(error.exception.code, "untrusted_runtime")
        execute.assert_not_called()

    def test_version_identity_is_checked_before_commands(self):
        with patch.object(runtime.subprocess, "run", return_value=self.completed("Windows Terminal 1.24")) as run:
            with self.assertRaises(runtime.WorktrunkError) as error:
                runtime.run_worktrunk(self.root, ["list"], str(self.binary))
        self.assertEqual(error.exception.code, "wrong_executable")
        self.assertEqual(run.call_count, 1)

    def test_new_version_is_blocked_until_adapter_pin_changes(self):
        with patch.object(runtime.subprocess, "run", return_value=self.completed("wt v0.82.0")):
            with self.assertRaises(runtime.WorktrunkError) as error:
                runtime.probe(str(self.binary))
        self.assertEqual(error.exception.code, "unsupported_version")

    @unittest.skipUnless(os.name == "nt", "Windows executable discovery")
    def test_windows_discovery_never_selects_windows_terminal(self):
        self.repository().unlink()
        directory = self.external_directory()
        (directory / "wt.exe").touch()
        with patch.object(runtime, "_execute") as execute:
            with self.assertRaises(runtime.WorktrunkError) as error:
                self.automatic_probe([directory])
        self.assertEqual(error.exception.code, "missing_runtime")
        execute.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows implicit cwd and batch executable discovery")
    def test_tracked_current_directory_batch_is_never_executed(self):
        self.repository().unlink()
        self.binary.unlink()
        marker = self.root / "batch-was-run"
        batch = self.root / "git-wt.cmd"
        batch.write_text('@echo off\necho invoked>"' + str(marker) + '"\necho wt v0.81.0\n', encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "--", str(batch)], check=True, capture_output=True)
        # The harmless marker proves the fixture can execute and that explicit
        # caller authorization remains separate from automatic discovery.
        self.assertTrue(runtime.probe(str(batch))["supported"])
        self.assertTrue(marker.exists())
        marker.unlink()
        for entries in ([], [self.root], ["", "."]):
            with self.subTest(entries=entries), self.assertRaises(runtime.WorktrunkError) as error:
                self.automatic_probe(entries)
            self.assertEqual(error.exception.code, "missing_runtime")
            self.assertFalse(marker.exists())

    def test_repository_native_executable_is_not_discovered_from_absolute_path(self):
        self.repository().unlink()
        name = "git-wt.exe" if os.name == "nt" else "git-wt"
        candidate = self.root / name
        candidate.touch()
        candidate.chmod(0o700)
        subprocess.run(["git", "-C", str(self.root), "add", "--", str(candidate)], check=True, capture_output=True)
        with patch.object(runtime, "_execute") as execute:
            with self.assertRaises(runtime.WorktrunkError) as error:
                self.automatic_probe([self.root])
        self.assertEqual(error.exception.code, "missing_runtime")
        execute.assert_not_called()

    def test_relative_path_to_external_executable_is_not_discovered(self):
        self.repository().unlink()
        directory = self.external_directory()
        candidate = directory / ("git-wt.exe" if os.name == "nt" else "git-wt")
        candidate.touch()
        candidate.chmod(0o700)
        relative = os.path.relpath(directory, self.root)
        with patch.object(runtime, "_execute") as execute:
            with self.assertRaises(runtime.WorktrunkError) as error:
                self.automatic_probe([relative])
        self.assertEqual(error.exception.code, "missing_runtime")
        execute.assert_not_called()

    def test_implicit_project_rejects_executable_in_checkout_ancestor(self):
        self.repository().unlink()
        directory = self.root / "nested"
        directory.mkdir()
        candidate = self.root / ("git-wt.exe" if os.name == "nt" else "git-wt")
        candidate.touch()
        candidate.chmod(0o700)
        environment = {"PATH": os.pathsep.join((str(self.root), self.git_directory))}
        with chdir(directory), patch.dict(os.environ, environment), patch.object(runtime, "_execute") as execute:
            with self.assertRaises(runtime.WorktrunkError) as error:
                runtime.probe()
        self.assertEqual(error.exception.code, "missing_runtime")
        execute.assert_not_called()

    def test_linked_worktree_path_executable_is_never_discovered(self):
        self.repository().unlink()
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Probe", "-c", "user.email=probe@example.invalid", "commit", "--allow-empty", "-m", "Probe"], check=True, capture_output=True)
        linked = self.external_directory()
        subprocess.run(["git", "-C", str(self.root), "worktree", "add", "-b", "linked", str(linked)], check=True, capture_output=True)
        candidate = linked / ("git-wt.exe" if os.name == "nt" else "git-wt")
        candidate.touch()
        candidate.chmod(0o700)
        with patch.object(runtime, "_execute") as execute:
            with self.assertRaises(runtime.WorktrunkError) as error:
                self.automatic_probe([linked])
        self.assertEqual(error.exception.code, "missing_runtime")
        execute.assert_not_called()

    def test_external_path_link_into_repository_is_never_discovered(self):
        self.repository().unlink()
        directory = self.external_directory()
        candidate = directory / ("git-wt.exe" if os.name == "nt" else "git-wt")
        self.binary.chmod(0o700)
        try:
            candidate.symlink_to(self.binary)
        except OSError as error:
            self.skipTest(f"Creating symlinks is unavailable: {error}")
        with patch.object(runtime, "_execute") as execute:
            with self.assertRaises(runtime.WorktrunkError) as error:
                self.automatic_probe([directory])
        self.assertEqual(error.exception.code, "missing_runtime")
        execute.assert_not_called()

    @unittest.skipUnless(os.environ.get("DAODAN_WORKTRUNK_EXECUTABLE"), "Set DAODAN_WORKTRUNK_EXECUTABLE for the live external installation probe")
    def test_live_external_absolute_path_installation_is_discovered(self):
        self.repository().unlink()
        directory = self.external_directory()
        candidate = directory / ("git-wt.exe" if os.name == "nt" else "git-wt")
        shutil.copy2(os.environ["DAODAN_WORKTRUNK_EXECUTABLE"], candidate)
        result = self.automatic_probe([self.root, directory])
        self.assertEqual(Path(result["executable"]), candidate.resolve())
        self.assertEqual(result["version"], runtime.upstream_pin()["version"])
        self.assertTrue(result["supported"])

    @unittest.skipUnless(os.environ.get("DAODAN_WORKTRUNK_EXECUTABLE"), "Set DAODAN_WORKTRUNK_EXECUTABLE for the live external installation probe")
    def test_live_installation_below_non_repository_cwd_is_discovered(self):
        self.repository().unlink()
        current = self.external_directory()
        directory = current / "user-tools"
        directory.mkdir()
        candidate = directory / ("git-wt.exe" if os.name == "nt" else "git-wt")
        shutil.copy2(os.environ["DAODAN_WORKTRUNK_EXECUTABLE"], candidate)
        environment = {"PATH": os.pathsep.join((str(directory), self.git_directory))}
        with self.non_repository_cwd(current), patch.dict(os.environ, environment):
            result = runtime.probe(project=self.root)
        self.assertEqual(Path(result["executable"]), candidate.resolve())
        self.assertTrue(result["supported"])

    def test_non_repository_cwd_executable_is_not_discovered(self):
        self.repository().unlink()
        current = self.external_directory()
        candidate = current / ("git-wt.exe" if os.name == "nt" else "git-wt")
        candidate.touch()
        candidate.chmod(0o700)
        environment = {"PATH": os.pathsep.join((str(current), self.git_directory))}
        with self.non_repository_cwd(current), patch.dict(os.environ, environment), patch.object(runtime, "_execute") as execute:
            with self.assertRaises(runtime.WorktrunkError) as error:
                runtime.probe(project=self.root)
        self.assertEqual(error.exception.code, "missing_runtime")
        execute.assert_not_called()

    def test_json_schema_and_explicit_cwd_without_shell(self):
        envelope = {"schema": 2, "items": [], "repo": {}, "collected": {"ci": False, "summary": False}}
        with patch.object(runtime.subprocess, "run", side_effect=[self.completed("wt v0.81.0"), self.completed(json.dumps(envelope))]) as run:
            self.assertEqual(runtime.run_worktrunk(self.root, ["list"], str(self.binary)), envelope)
        invocation = run.call_args
        self.assertEqual(invocation.kwargs["cwd"], self.root.resolve())
        self.assertFalse(invocation.kwargs["shell"])
        self.assertEqual(invocation.kwargs["stdin"], subprocess.DEVNULL)
        self.assertIn("--format=json", invocation.args[0])

    def test_old_schema_and_malformed_json_fail_closed(self):
        for raw in ("[]", "{bad", '{"schema":1,"items":[]}'):
            with self.subTest(raw=raw), patch.object(runtime.subprocess, "run", side_effect=[self.completed("wt v0.81.0"), self.completed(raw)]):
                with self.assertRaises(runtime.WorktrunkError):
                    runtime.run_worktrunk(self.root, ["list"], str(self.binary))

    def test_timeout_and_nonzero_command_are_not_success(self):
        for effect, expected in ((subprocess.TimeoutExpired(["git-wt"], 1), "timeout"),
                                 (self.completed("{}", 1, "failed"), "command_failed")):
            with self.subTest(expected=expected), patch.object(runtime.subprocess, "run", side_effect=effect if isinstance(effect, Exception) else None, return_value=effect):
                with self.assertRaises(runtime.WorktrunkError) as error:
                    runtime.probe(str(self.binary))
                self.assertEqual(error.exception.code, expected)

    def test_unsafe_options_cannot_execute(self):
        cases = [["merge"], ["list", "--full"], ["list", "--config-set=x"],
                 ["switch", "topic", "--path", str(self.root / "topic")],
                 ["switch", "topic", "--path", str(self.root / "topic"), "--no-hooks", "--no-cd", "-xecho"]]
        with patch.object(runtime.subprocess, "run") as run:
            for args in cases:
                with self.subTest(args=args), self.assertRaises(runtime.WorktrunkError):
                    runtime.run_worktrunk(self.root, args, str(self.binary))
        run.assert_not_called()

    def test_git_and_worktrunk_environment_cannot_redirect_operation(self):
        with patch.dict(os.environ, {"GIT_DIR": "/other/.git", "WORKTRUNK_CONFIG_PATH": "/other/config", "TASK_VALUE": "kept",
                                    "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_1": "core.hooksPath", "GIT_CONFIG_VALUE_1": "/foreign/hooks"}):
            environment = runtime._environment()
        self.assertNotIn("GIT_DIR", environment)
        self.assertNotIn("WORKTRUNK_CONFIG_PATH", environment)
        self.assertEqual(environment["TASK_VALUE"], "kept")
        self.assertEqual(environment["GIT_CONFIG_COUNT"], "1")
        self.assertEqual(environment["GIT_CONFIG_KEY_0"], "core.hooksPath")
        self.assertEqual(environment["GIT_CONFIG_VALUE_0"], str(runtime.NO_HOOKS_PATH))
        self.assertNotIn("GIT_CONFIG_KEY_1", environment)
        self.assertNotIn("GIT_CONFIG_VALUE_1", environment)

    @unittest.skipUnless(os.environ.get("DAODAN_WORKTRUNK_EXECUTABLE"), "Set DAODAN_WORKTRUNK_EXECUTABLE for the live native-hook boundary probe")
    def test_live_creation_disables_native_hook_without_changing_hook_policy(self):
        self.repository()
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Probe", "-c", "user.email=probe@example.invalid", "commit", "--allow-empty", "-m", "Probe"], check=True, capture_output=True)
        hooks = self.root / "native-hooks"
        hooks.mkdir()
        marker = self.root / "native-hook-was-run"
        hook = hooks / "post-checkout"
        hook.write_text("#!/bin/sh\nprintf invoked > " + shlex.quote(marker.as_posix()) + "\nexit 66\n", encoding="utf-8")
        hook.chmod(0o700)
        subprocess.run(["git", "-C", str(self.root), "config", "core.hooksPath", str(hooks)], check=True, capture_output=True)
        read_policy = ["git", "-C", str(self.root), "config", "--get", "core.hooksPath"]
        before = subprocess.run(read_policy, check=True, capture_output=True).stdout
        target = self.root / ".daodan/worktrees/no-native-hook"
        result = runtime.run_worktrunk(self.root, ["switch", "--create", "no-native-hook", "--base", "main", "--path", str(target), "--no-hooks", "--no-cd"], os.environ["DAODAN_WORKTRUNK_EXECUTABLE"])
        self.assertEqual(result["action"], "created")
        self.assertTrue(target.is_dir())
        self.assertFalse(marker.exists())
        self.assertEqual(subprocess.run(read_policy, check=True, capture_output=True).stdout, before)

    def test_upstream_check_reports_candidate_without_mutation(self):
        before = runtime.PIN_PATH.read_bytes()
        release = {"tag_name": "v0.82.0", "draft": False, "prerelease": False,
                   "html_url": "https://github.com/max-sixty/worktrunk/releases/tag/v0.82.0"}
        with patch.object(runtime.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(release).encode())):
            report = runtime.upstream_check()
        self.assertTrue(report["update_available"])
        self.assertFalse(report["pin_changed"])
        self.assertEqual(runtime.PIN_PATH.read_bytes(), before)

    def test_upstream_failure_preserves_pin(self):
        before = runtime.PIN_PATH.read_bytes()
        with patch.object(runtime.urllib.request, "urlopen", side_effect=urllib.error.URLError("offline")):
            with self.assertRaises(runtime.WorktrunkError) as error:
                runtime.upstream_check()
        self.assertEqual(error.exception.code, "upstream_unavailable")
        self.assertEqual(runtime.PIN_PATH.read_bytes(), before)

    def test_invalid_timeout_fails_before_network(self):
        with patch.object(runtime.urllib.request, "urlopen") as fetch:
            for timeout in (0, -1, float("nan"), float("inf")):
                with self.subTest(timeout=timeout), self.assertRaises(runtime.WorktrunkError):
                    runtime.upstream_check(timeout)
        fetch.assert_not_called()

    def test_oversized_output_is_not_admitted(self):
        with patch.object(runtime.subprocess, "run", return_value=self.completed("x" * (4 * 1024 * 1024 + 1))):
            with self.assertRaises(runtime.WorktrunkError) as error:
                runtime.probe(str(self.binary))
        self.assertEqual(error.exception.code, "output_too_large")

    def test_unstable_or_foreign_release_is_rejected(self):
        release = {"tag_name": "v0.82.0", "draft": False, "prerelease": True,
                   "html_url": "https://example.invalid/download"}
        with patch.object(runtime.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(release).encode())):
            with self.assertRaises(runtime.WorktrunkError):
                runtime.upstream_check()


if __name__ == "__main__":
    unittest.main()
