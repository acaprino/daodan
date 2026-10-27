"""Hook declaration-to-execution contract (filesystem/subprocess integration).

This behavior spans the compiler loader, validation and rendering boundaries.
Search-before-write found no suite for native hook registration or execution;
the existing host-probe fixture is not a compiler regression test. Tests use
owned temporary packages, not installed plugin or user configuration. Target
runtime: under 30 seconds, with bounded subprocesses and no network.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter, resolve_support  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.model import ModelError  # noqa: E402
from scripts.daodan.overrides import OverrideSpec, source_digest, validate_override  # noqa: E402
from scripts.daodan.render import RenderError, publish_plugin  # noqa: E402
from scripts.daodan.validate import CAPABILITY_REGISTRY, validate_plugins  # noqa: E402

ADAPTERS = REPO_ROOT / "adapters"
FIXTURE = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"
SCRIPT = "skills/science/scripts/handler.py"
HANDLER = """import json
import sys
from pathlib import Path
print(json.dumps({"args": sys.argv[1:], "payload": json.load(sys.stdin),
                  "script": str(Path(__file__).resolve())}, ensure_ascii=True))
"""


class HookContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="daodan hooks "))
        self.addCleanup(self.remove_owned_temp)
        self.kernel = self.temp / "kernel" / "example"
        shutil.copytree(FIXTURE, self.kernel)
        skill = self.kernel / "skills/science"
        (skill / "scripts").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: science\ndescription: Hook fixture\n---\n\n# Science\n",
            encoding="utf-8",
        )
        (self.kernel / SCRIPT).write_text(HANDLER, encoding="utf-8")
        self.base = (self.kernel / "plugin.toml").read_text(encoding="utf-8")
        self.base = self.base.replace('skills = []', 'skills = ["science"]')

    def remove_owned_temp(self):
        root = self.temp.resolve()
        self.assertTrue(root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        shutil.rmtree(root)

    def declare(self, hooks=None, capability="optional"):
        if hooks is None:
            hooks = [{"name": "science-session", "event": "session-start",
                      "script": SCRIPT, "args": ["literal argument"], "timeout": 10}]
        text = self.base
        if capability == "optional":
            text = text.replace('optional = ["execution.parallel"]',
                                'optional = ["execution.parallel", "hooks.lifecycle"]')
        elif capability == "required":
            text = text.replace('"roles.dispatch"]',
                                '"roles.dispatch", "hooks.lifecycle"]')
        for hook in hooks:
            text += "\n[[hooks]]\n"
            text += "".join(f"{key} = {json.dumps(value, ensure_ascii=True)}\n"
                            for key, value in hook.items())
        (self.kernel / "plugin.toml").write_text(text, encoding="utf-8")

    def publish(self, host, suffix=""):
        destination = self.temp / f"package {host}{suffix}"
        publish_plugin(load_plugin(self.kernel), load_adapter(ADAPTERS, host),
                       destination, adapters_root=ADAPTERS)
        return destination

    def test_declared_hook_is_a_valid_plugin_contract(self):
        self.declare()

        issues = validate_plugins([load_plugin(self.kernel)], CAPABILITY_REGISTRY)

        self.assertEqual(issues, [])

    def assert_contract_rejected(self):
        try:
            plugin = load_plugin(self.kernel)
        except ModelError:
            return
        self.assertTrue(validate_plugins([plugin], CAPABILITY_REGISTRY),
                        "Invalid hook input was accepted as a valid plugin")

    def test_declaration_rejects_unknown_fields_and_malformed_values(self):
        valid = {"name": "science-session", "event": "session-start",
                 "script": SCRIPT, "args": [], "timeout": 10}
        invalid = (
            {**valid, "command": "arbitrary shell command"},
            {**valid, "args": "not an array"},
            {**valid, "args": ["allowed", 3]},
            {**valid, "args": ["invalid\x00argument"]},
            {**valid, "timeout": True},
            {**valid, "timeout": 0},
            {**valid, "timeout": 61},
            {**valid, "event": "unregistered-event"},
            {**valid, "name": ""},
            {key: value for key, value in valid.items() if key != "script"},
        )
        for hook in invalid:
            with self.subTest(hook=hook):
                self.declare([hook])

                self.assert_contract_rejected()

    def test_duplicate_hook_names_cannot_hide_a_second_handler(self):
        self.declare([
            {"name": "same-name", "event": "session-start", "script": SCRIPT},
            {"name": "same-name", "event": "user-prompt-submit", "script": SCRIPT},
        ])

        self.assert_contract_rejected()

    def test_native_registration_cannot_bypass_neutral_declarations(self):
        self.declare()
        raw_manifest = self.kernel / "hooks/hooks.json"
        raw_manifest.parent.mkdir()
        raw_manifest.write_text('{"hooks":{"SessionStart":[]}}', encoding="utf-8")

        self.assert_contract_rejected()

        raw_manifest.unlink()
        skill = self.kernel / "skills/science/SKILL.md"
        skill.write_text('---\nname: science\ndescription: Hook fixture\n'
                         'hooks:\n  SessionStart: []\n---\n# Science\n',
                         encoding="utf-8")

        self.assert_contract_rejected()

    def test_fingerprinted_override_cannot_add_native_hook_frontmatter(self):
        source = self.kernel / "workflows/review.md"
        override_root = self.temp / "override"
        override_root.mkdir()
        replacement = override_root / "review.md"
        replacement.write_text("---\ndescription: Reviewed workflow\n---\n# Review\n",
                               encoding="utf-8")
        override = OverrideSpec(
            root=override_root, source="workflow:review",
            source_paths=(source.relative_to(self.temp),), reason="test contract",
            strategy="single-agent", reviewed_against=source_digest([source]),
            contracts_preserved=(), capabilities_affected=("repository.read",),
            replacement=Path("review.md"),
        )
        self.assertEqual(validate_override(override, {"repository.read"},
                                           repository_root=self.temp), [])
        replacement.write_text("---\ndescription: Reviewed workflow\n"
                               "hooks:\n  SessionStart: []\n---\n# Review\n",
                               encoding="utf-8")

        issues = validate_override(override, {"repository.read", "hooks.lifecycle"},
                                   repository_root=self.temp)

        self.assertTrue(issues, "A fingerprint must not authorize raw hook registration")

    def test_hook_capability_and_declaration_must_agree(self):
        self.declare(capability=None)

        self.assert_contract_rejected()

        for capability in ("required", "optional"):
            with self.subTest(capability=capability):
                self.declare(hooks=[], capability=capability)

                self.assert_contract_rejected()

    def test_missing_unshipped_and_escaping_handler_paths_are_rejected(self):
        for path in ("scripts/handler.py", "skills/undeclared/scripts/handler.py"):
            unshipped = self.kernel / path
            unshipped.parent.mkdir(parents=True, exist_ok=True)
            unshipped.write_text(HANDLER, encoding="utf-8")
        outside = self.temp / "outside.py"
        outside.write_text(HANDLER, encoding="utf-8")
        paths = (
            "skills/science/scripts/missing.py",
            "scripts/handler.py",
            "skills/undeclared/scripts/handler.py",
            "skills/science/scripts/../../../../outside.py",
            str(outside.resolve()),
            "skills/science/scripts/handler.sh",
        )
        for path in paths:
            with self.subTest(path=path):
                self.declare([{"name": "science-session", "event": "session-start",
                               "script": path}])

                self.assert_contract_rejected()

    def test_linked_handler_outside_the_kernel_is_rejected(self):
        external = self.temp / "external.py"
        external.write_text(HANDLER, encoding="utf-8")
        linked = self.kernel / "skills/science/scripts/linked.py"
        linked.symlink_to(external)
        self.declare([{"name": "science-session", "event": "session-start",
                       "script": "skills/science/scripts/linked.py"}])

        self.assert_contract_rejected()

    def test_optional_hooks_register_natively_only_on_supported_hosts(self):
        self.declare([
            {"name": "science-session", "event": "session-start", "script": SCRIPT},
            {"name": "science-prompt", "event": "user-prompt-submit", "script": SCRIPT,
             "timeout": 23},
        ])

        for host in HOSTS:
            with self.subTest(host=host):
                package = self.publish(host)

                self.assertTrue((package / SCRIPT).is_file())
                hook_manifest = package / "hooks/hooks.json"
                if host in {"claude", "codex"}:
                    self.assertTrue(hook_manifest.is_file(),
                                    "Default-discovery manifest must be shipped")
                    manifest = json.loads(hook_manifest.read_text(encoding="utf-8"))
                    self.assertEqual(set(manifest["hooks"]),
                                     {"SessionStart", "UserPromptSubmit"})
                    for event, timeout in (("SessionStart", 10), ("UserPromptSubmit", 23)):
                        entries = manifest["hooks"][event]
                        self.assertEqual(len(entries), 1)
                        commands = entries[0]["hooks"]
                        self.assertEqual(len(commands), 1)
                        self.assertEqual(commands[0]["type"], "command")
                        self.assertEqual(commands[0]["timeout"], timeout)
                        self.assertTrue(commands[0]["command"])
                else:
                    self.assertFalse(hook_manifest.exists(),
                                     "Unsupported hosts must not claim native registration")

    def test_required_unsupported_hook_capability_preserves_live_package(self):
        self.declare(capability="required")
        plugin = load_plugin(self.kernel)

        for host in ("copilot", "pi"):
            with self.subTest(host=host):
                adapter = load_adapter(ADAPTERS, host)
                live = self.temp / f"existing {host}"
                live.mkdir()
                sentinel = live / "sentinel.txt"
                sentinel.write_bytes(b"previous package must survive")

                support = resolve_support(plugin, adapter)
                with self.assertRaises(RenderError):
                    publish_plugin(plugin, adapter, live, adapters_root=ADAPTERS)

                self.assertIn("hooks.lifecycle", support.missing_capabilities)
                self.assertEqual(sentinel.read_bytes(), b"previous package must survive")
                self.assertEqual([path.name for path in live.iterdir()], ["sentinel.txt"])

    def test_required_hook_capability_is_supported_on_opencode_as_adapted(self):
        self.declare(capability="required")
        plugin = load_plugin(self.kernel)
        adapter = load_adapter(ADAPTERS, "opencode")
        support = resolve_support(plugin, adapter)
        self.assertNotIn("hooks.lifecycle", support.missing_capabilities)
        self.assertEqual(support.state, "adapted")

    def test_generated_command_preserves_literal_arguments_payload_and_spaced_root(self):
        args = ["", "with spaces", "apostrophe's", 'double "quotes"',
                "$HOME", "$(Write-Output injected)", "`quoted`; & | >", "Ω"]
        self.declare([{"name": "science-prompt", "event": "user-prompt-submit",
                       "script": SCRIPT, "args": args}])
        payload = {"hook_event_name": "UserPromptSubmit", "prompt": "test payload"}

        for host in ("claude", "codex"):
            with self.subTest(host=host):
                package = self.publish(host, " O'Brien & Ω")
                manifest = json.loads((package / "hooks/hooks.json").read_text(encoding="utf-8"))
                command = manifest["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
                env = {key: value for key, value in os.environ.items()
                       if key not in {"CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT"}}
                env["CLAUDE_PLUGIN_ROOT" if host == "claude" else "PLUGIN_ROOT"] = str(package)
                env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
                shell = (["powershell", "-NoProfile", "-NonInteractive", "-Command"]
                         if os.name == "nt" else ["/bin/sh", "-c"])

                result = subprocess.run(shell + [command], input=json.dumps(payload),
                                        capture_output=True, text=True, env=env,
                                        cwd=self.temp, timeout=15, check=False)

                self.assertEqual(result.returncode, 0, result.stderr)
                observed = json.loads(result.stdout)
                self.assertEqual(observed["args"], args)
                self.assertEqual(observed["payload"], payload)
                self.assertEqual(Path(observed["script"]), (package / SCRIPT).resolve())

    def test_generated_command_without_host_root_does_not_run_from_cwd(self):
        self.declare()
        package = self.publish("codex")
        manifest = json.loads((package / "hooks/hooks.json").read_text(encoding="utf-8"))
        command = manifest["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        env = {key: value for key, value in os.environ.items()
               if key not in {"CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT"}}
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
        shell = (["powershell", "-NoProfile", "-NonInteractive", "-Command"]
                 if os.name == "nt" else ["/bin/sh", "-c"])

        result = subprocess.run(shell + [command], input='{}', capture_output=True,
                                text=True, env=env, cwd=package, timeout=15, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertIn("root", result.stderr.lower())

    def test_no_declared_hooks_does_not_register_a_global_policy_guard(self):
        plugin = load_plugin(REPO_ROOT / "plugins/codebase-map")
        package = self.temp / "codebase map copilot"

        publish_plugin(plugin, load_adapter(ADAPTERS, "copilot"), package,
                       adapters_root=ADAPTERS)

        # The policy's own invocation declares this neutral package path.
        self.assertTrue((package / "policies/write-confinement/xray_guard.py").is_file())
        self.assertFalse((package / "hooks/hooks.json").exists())
        manifest = json.loads((package / "plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("hooks", manifest)


if __name__ == "__main__":
    unittest.main()
