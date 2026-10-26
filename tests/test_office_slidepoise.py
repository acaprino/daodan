"""External runtime discovery and argument confinement for SlidePoise."""

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SOURCE = (Path(__file__).resolve().parents[1] /
          "plugins/office/skills/slidepoise/scripts/slidepoise_bridge.py")
SPEC = importlib.util.spec_from_file_location("office_slidepoise_bridge", SOURCE)
bridge = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bridge
SPEC.loader.exec_module(bridge)


class RuntimeFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="slidepoise test ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.home = self.root / "runtime home"
        self.skill = self.root / "installed skill"
        self.config = self.root / "framework config.json"
        self.python = bridge.managed_python(self.home)
        self.python.parent.mkdir(parents=True)
        self.python.touch()
        (self.skill / "scripts").mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("# External skill", encoding="utf-8")
        self.reconstruction = self.skill / "scripts/slidepoise_runtime.py"
        self.reconstruction.write_text("pass\n", encoding="utf-8")
        self.config.write_text("{}", encoding="utf-8")
        self.payload = {
            "skill_root": str(self.skill), "config": str(self.config),
            "data_home": str(self.home),
        }
        self.runtime = bridge.Runtime(self.python, self.skill, self.config, self.home)

    def completed_probe(self, **updates):
        payload = {**self.payload, **updates}
        return subprocess.CompletedProcess([], 0, json.dumps(payload), "")

    def discover(self):
        return bridge.discover(environ={"SLIDEPOISE_HOME": str(self.home)})

    def test_environment_home_and_default_home(self):
        self.assertEqual(bridge.runtime_home({"SLIDEPOISE_HOME": str(self.home)}), self.home)
        self.assertEqual(bridge.runtime_home({}, self.root), self.root / ".slidepoise")

    def test_windows_and_unix_python_locations(self):
        self.assertEqual(bridge.managed_python(self.home, "nt"),
                         self.home / "python/Scripts/python.exe")
        self.assertEqual(bridge.managed_python(self.home, "posix"),
                         self.home / "python/bin/python")

    def test_discovery_uses_managed_python_and_real_framework_paths(self):
        with mock.patch.object(bridge.subprocess, "run", return_value=self.completed_probe()) as run:
            actual = self.discover()
        self.assertEqual(actual, self.runtime)
        argv = run.call_args.args[0]
        self.assertEqual(argv[:2], [str(self.python), "-c"])
        self.assertIn("from framework.paths import", argv[2])
        self.assertNotIn("cwd", run.call_args.kwargs)
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_discovery_overrides_home_without_losing_process_environment(self):
        with mock.patch.dict(os.environ, {"BRIDGE_TEST_BASELINE": "preserved"}, clear=True):
            with mock.patch.object(bridge.subprocess, "run", return_value=self.completed_probe()) as run:
                self.discover()
        self.assertEqual(run.call_args.kwargs["env"], {
            "BRIDGE_TEST_BASELINE": "preserved", "SLIDEPOISE_HOME": str(self.home),
        })

    def test_windows_discovery_uses_windows_managed_python(self):
        windows_python = bridge.managed_python(self.home, "nt")
        windows_python.parent.mkdir(parents=True, exist_ok=True)
        windows_python.touch()
        with mock.patch.object(bridge.subprocess, "run", return_value=self.completed_probe()) as run:
            actual = bridge.discover({"SLIDEPOISE_HOME": str(self.home)}, platform="nt")
        self.assertEqual(actual.python, windows_python)
        self.assertEqual(run.call_args.args[0][0], str(windows_python))

    def test_standalone_skill_without_managed_python_reports_missing_runtime(self):
        self.python.unlink()
        with mock.patch.object(bridge.subprocess, "run") as run:
            with self.assertRaisesRegex(bridge.BridgeError, "standalone skill installation"):
                self.discover()
        run.assert_not_called()

    def test_import_failure_keeps_the_actual_runtime_error(self):
        failure = subprocess.CompletedProcess([], 8, "", "ModuleNotFoundError: framework")
        with mock.patch.object(bridge.subprocess, "run", return_value=failure):
            with self.assertRaisesRegex(bridge.BridgeError, "ModuleNotFoundError: framework"):
                self.discover()

    def test_malformed_probe_and_relative_paths_are_rejected(self):
        for output in ("not json", "[]", json.dumps({**self.payload, "skill_root": "relative"})):
            with self.subTest(output=output):
                result = subprocess.CompletedProcess([], 0, output, "")
                with mock.patch.object(bridge.subprocess, "run", return_value=result):
                    with self.assertRaises(bridge.BridgeError):
                        self.discover()

    def test_missing_skill_and_reconstruction_script_are_reported(self):
        for path in (self.skill / "SKILL.md", self.reconstruction):
            with self.subTest(path=path):
                content = path.read_text(encoding="utf-8")
                path.unlink()
                with mock.patch.object(bridge.subprocess, "run", return_value=self.completed_probe()):
                    with self.assertRaisesRegex(bridge.BridgeError, "skill is missing"):
                        self.discover()
                path.write_text(content, encoding="utf-8")

    def test_missing_config_is_reported(self):
        self.config.unlink()
        with mock.patch.object(bridge.subprocess, "run", return_value=self.completed_probe()):
            with self.assertRaisesRegex(bridge.BridgeError, "framework config is missing"):
                self.discover()

    def test_cli_preserves_argument_boundaries_cwd_and_exit_code(self):
        arguments = ["profile", "show", "--name", "name with spaces", "$(no shell)"]
        with mock.patch.object(bridge.subprocess, "run", return_value=subprocess.CompletedProcess([], 23)) as run:
            self.assertEqual(bridge.run_cli(self.runtime, arguments), 23)
        run.assert_called_once_with([str(self.python), "-m", "framework.cli", *arguments],
                                    env={**os.environ, "SLIDEPOISE_HOME": str(self.home)})

    def test_script_accepts_bare_prefixed_and_nested_names(self):
        nested = self.skill / "scripts/nested/measure.py"
        nested.parent.mkdir()
        nested.write_text("pass\n", encoding="utf-8")
        for name in ("slidepoise_runtime.py", "scripts/slidepoise_runtime.py",
                     "scripts\\slidepoise_runtime.py"):
            with self.subTest(name=name):
                self.assertEqual(bridge.installed_script(self.runtime, name), self.reconstruction)
        self.assertEqual(bridge.installed_script(self.runtime, "nested/measure.py"), nested)

    def test_script_rejects_traversal_absolute_paths_and_non_python_files(self):
        for name in ("", "../outside.py", "scripts/../../outside.py", "/tmp/outside.py",
                     "C:\\outside.py", "C:outside.py", "\\\\server\\share\\outside.py",
                     "script.sh", "scripts/", "bad\x00.py"):
            with self.subTest(name=name):
                with self.assertRaises(bridge.BridgeError):
                    bridge.installed_script(self.runtime, name)

    def test_script_rejects_symlink_escape(self):
        outside = self.root / "outside.py"
        outside.write_text("pass\n", encoding="utf-8")
        linked = self.skill / "scripts/linked.py"
        try:
            linked.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"Symlink creation unavailable: {error}")
        with self.assertRaisesRegex(bridge.BridgeError, "escapes its root"):
            bridge.installed_script(self.runtime, "linked.py")

    def test_script_rejects_symlink_into_other_skill_directories(self):
        outside_scripts = self.skill / "references/helper.py"
        outside_scripts.parent.mkdir()
        outside_scripts.write_text("pass\n", encoding="utf-8")
        linked = self.skill / "scripts/linked.py"
        try:
            linked.symlink_to(outside_scripts)
        except OSError as error:
            self.skipTest(f"Symlink creation unavailable: {error}")
        with self.assertRaisesRegex(bridge.BridgeError, "escapes its root"):
            bridge.installed_script(self.runtime, "linked.py")

    def test_script_forwards_exact_argv_and_return_code(self):
        arguments = ["--output", "deck with spaces.pptx", "--config", str(self.config)]
        with mock.patch.object(bridge.subprocess, "run", return_value=subprocess.CompletedProcess([], 7)) as run:
            self.assertEqual(bridge.run_script(self.runtime, "slidepoise_runtime.py", arguments), 7)
        run.assert_called_once_with([str(self.python), str(self.reconstruction), *arguments],
                                    env={**os.environ, "SLIDEPOISE_HOME": str(self.home)})

    def test_discover_command_emits_paths_and_cli_separator_is_not_forwarded(self):
        with mock.patch.object(bridge, "discover", return_value=self.runtime):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                self.assertEqual(bridge.main(["discover"]), 0)
            self.assertEqual(json.loads(stream.getvalue()), self.runtime.as_dict())
            with mock.patch.object(bridge, "run_cli", return_value=3) as run:
                self.assertEqual(bridge.main(["cli", "--", "doctor", "--json"]), 3)
            run.assert_called_once_with(self.runtime, ["doctor", "--json"])

    def test_cli_owns_leading_options_including_help(self):
        for arguments in (["--help"], ["--version"], ["--", "--help"]):
            with self.subTest(arguments=arguments):
                with mock.patch.object(bridge, "discover", return_value=self.runtime):
                    with mock.patch.object(bridge, "run_cli", return_value=0) as run:
                        self.assertEqual(bridge.main(["cli", *arguments]), 0)
                run.assert_called_once_with(self.runtime, arguments[-1:])

    def test_global_home_discovery_reports_the_selected_runtime(self):
        stream = io.StringIO()
        with mock.patch.dict(os.environ, {"BRIDGE_TEST_BASELINE": "preserved"}, clear=True):
            with mock.patch.object(bridge.subprocess, "run", return_value=self.completed_probe()) as run:
                with contextlib.redirect_stdout(stream):
                    self.assertEqual(bridge.main(["--home", str(self.home), "discover"]), 0)
        self.assertEqual(json.loads(stream.getvalue()), self.runtime.as_dict())
        self.assertEqual(run.call_args.args[0][0], str(self.python))
        self.assertEqual(run.call_args.kwargs["env"], {
            "BRIDGE_TEST_BASELINE": "preserved", "SLIDEPOISE_HOME": str(self.home),
        })

    def test_global_home_reaches_cli_script_children_and_preserves_help(self):
        cases = [
            (["cli", "--help"], ["-m", "framework.cli", "--help"]),
            (["script", "slidepoise_runtime.py", "--help"],
             [str(self.reconstruction), "--help"]),
        ]
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                with mock.patch.dict(os.environ, {"BRIDGE_TEST_BASELINE": "preserved"}, clear=True):
                    with mock.patch.object(bridge.subprocess, "run", side_effect=[
                        self.completed_probe(), subprocess.CompletedProcess([], 19),
                    ]) as run:
                        self.assertEqual(bridge.main(["--home", str(self.home), *arguments]), 19)
                self.assertEqual(run.call_args.args[0], [str(self.python), *expected])
                for call in run.call_args_list:
                    self.assertEqual(call.kwargs["env"], {
                        "BRIDGE_TEST_BASELINE": "preserved", "SLIDEPOISE_HOME": str(self.home),
                    })
                    self.assertNotIn("cwd", call.kwargs)

    def test_cli_home_option_after_verb_belongs_to_upstream(self):
        with mock.patch.object(bridge, "discover", return_value=self.runtime):
            with mock.patch.object(bridge, "run_cli", return_value=0) as run:
                self.assertEqual(bridge.main(["cli", "--home", "upstream value"]), 0)
        run.assert_called_once_with(self.runtime, ["--home", "upstream value"])

    def test_main_reports_discovery_error_without_traceback(self):
        with mock.patch.object(bridge, "discover", side_effect=bridge.BridgeError("missing runtime")):
            stream = io.StringIO()
            with contextlib.redirect_stderr(stream):
                self.assertEqual(bridge.main(["discover"]), 1)
            self.assertEqual(stream.getvalue(), "slidepoise-bridge: missing runtime\n")


if __name__ == "__main__":
    unittest.main()
