"""Routing delivery: the rendered routing file and the host entry that delivers it.

Claude and Codex register one more session-start entry whose launcher prints the
file as additional context and, once started, ends silently with 0 on any
error. OpenCode receives the file only; Copilot and Pi receive nothing. Tests
use owned temporary packages and bounded subprocesses, no network.
"""

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import publish_plugin  # noqa: E402
from scripts.daodan.routing import routing_text  # noqa: E402

ADAPTERS = REPO_ROOT / "adapters"
FIXTURE = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"
SCRIPT = "skills/science/scripts/handler.py"
TEXT = "hooks/entry-routing.md"
MANIFEST = "hooks/hooks.json"
ROOTS = {"claude": "CLAUDE_PLUGIN_ROOT", "codex": "PLUGIN_ROOT"}
ROUTING = ('\n[routing]\nworkflows = true\n\n[[routing.keywords]]\n'
           'words = ["experiment"]\ntarget = "science"\n')
SESSION_HOOK = (f'\n[[hooks]]\nname = "science-session"\nevent = "session-start"\n'
                f'script = "{SCRIPT}"\ntimeout = 10\n')
#: A phrase every `[[hooks]]` entry note carries on every host.
NOTE = "lifecycle callback"
HANDLER = "import sys\nsys.stdout.write('handler')\n"
INSPECT = "TRIGGER WHEN: the user asks for an inspection."


def launcher_source(command):
    """The Python source a generated base64 launcher executes, or an empty string."""
    match = re.search(r"b64decode\('([A-Za-z0-9+/=]+)'\)", command)
    return base64.b64decode(match.group(1)).decode("utf-8") if match else ""


def routing_entries(manifest):
    return [entry for entry in manifest["hooks"].get("SessionStart", [])
            if TEXT in launcher_source(entry["hooks"][0]["command"])]


class OwnedTemp(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="daodan routing render "))
        self.addCleanup(self.remove_owned_temp)

    def remove_owned_temp(self):
        root = self.temp.resolve()
        self.assertTrue(root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        shutil.rmtree(root)


class RoutingDeliveryTests(OwnedTemp):
    """An example kernel with a `science` skill, published per host."""

    def setUp(self):
        super().setUp()
        self.kernel = self.temp / "kernel" / "example"
        shutil.copytree(FIXTURE, self.kernel)
        skill = self.kernel / "skills/science"
        (skill / "scripts").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: science\ndescription: Routing fixture\n---\n\n# Science\n", encoding="utf-8")
        (self.kernel / SCRIPT).write_text(HANDLER, encoding="utf-8")
        self.base = (self.kernel / "plugin.toml").read_text(encoding="utf-8").replace(
            'skills = []', 'skills = ["science"]').replace(
            'optional = ["execution.parallel"]', 'optional = ["execution.parallel", "hooks.lifecycle"]')

    def declare(self, tables):
        (self.kernel / "plugin.toml").write_text(self.base + tables, encoding="utf-8")
        return load_plugin(self.kernel)

    def publish(self, host, suffix=""):
        destination = self.temp / f"package {host}{suffix}"
        publish_plugin(load_plugin(self.kernel), load_adapter(ADAPTERS, host),
                       destination, adapters_root=ADAPTERS)
        return destination

    def manifest(self, package):
        return json.loads((package / MANIFEST).read_text(encoding="utf-8"))

    def run_launcher(self, command, host, root):
        env = {key: value for key, value in os.environ.items() if key not in set(ROOTS.values())}
        if root is not None:
            env[ROOTS[host]] = str(root)
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
        shell = (["powershell", "-NoProfile", "-NonInteractive", "-Command"]
                 if os.name == "nt" else ["/bin/sh", "-c"])
        return subprocess.run(shell + [command], input="{}", capture_output=True, text=True,
                              env=env, cwd=self.temp, timeout=30, check=False)

    def routing_command(self, package):
        entries = routing_entries(self.manifest(package))
        self.assertEqual(len(entries), 1)
        return entries[0]["hooks"][0]["command"]

    def test_claude_and_codex_ship_the_text_and_an_entry_that_prints_it(self):
        plugin = self.declare(ROUTING)

        for host in ("claude", "codex"):
            with self.subTest(host=host):
                package = self.publish(host, " O'Brien & Ω")
                text = (package / TEXT).read_bytes().decode("utf-8")
                expected = routing_text(plugin, load_adapter(ADAPTERS, host), {plugin.name: plugin})
                self.assertEqual(text, expected)
                manifest = self.manifest(package)
                self.assertEqual(set(manifest["hooks"]), {"SessionStart"})
                self.assertEqual(len(manifest["hooks"]["SessionStart"]), 1)
                handler = routing_entries(manifest)[0]["hooks"][0]
                self.assertEqual((handler["type"], handler["timeout"]), ("command", 5))
                self.assertNotIn("$", handler["command"])

                result = self.run_launcher(handler["command"], host, package)

                self.assertEqual((result.returncode, result.stderr), (0, ""))
                self.assertEqual(json.loads(result.stdout), {"hookSpecificOutput": {
                    "hookEventName": "SessionStart", "additionalContext": text}})

    def test_opencode_ships_the_text_without_a_hook_manifest(self):
        plugin = self.declare(ROUTING)

        package = self.publish("opencode")

        expected = routing_text(plugin, load_adapter(ADAPTERS, "opencode"), {plugin.name: plugin})
        self.assertEqual((package / TEXT).read_bytes().decode("utf-8"), expected)
        self.assertFalse((package / MANIFEST).exists())

    def test_copilot_and_pi_ship_no_text_and_no_hook(self):
        self.declare(ROUTING)

        for host in ("copilot", "pi"):
            with self.subTest(host=host):
                package = self.publish(host)

                self.assertEqual(list(package.rglob(Path(TEXT).name)), [])
                self.assertFalse((package / MANIFEST).exists())

    def test_hooks_and_routing_share_one_manifest_and_keep_the_hook_entry(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.declare(SESSION_HOOK)
                hooks_only = self.manifest(self.publish(host, " hooks"))
                self.declare(ROUTING + SESSION_HOOK)
                combined = self.manifest(self.publish(host, " both"))

                entries = combined["hooks"]["SessionStart"]
                routing = routing_entries(combined)
                self.assertEqual(len(entries), 2)
                self.assertEqual(len(routing), 1)
                self.assertEqual([entry for entry in entries if entry not in routing],
                                 hooks_only["hooks"]["SessionStart"])
                self.assertEqual(routing_entries(hooks_only), [])

    def test_launcher_without_its_root_or_text_ends_silently(self):
        self.declare(ROUTING)

        for host in ("claude", "codex"):
            package = self.publish(host)
            command = self.routing_command(package)
            text = package / TEXT
            cases = (
                ("root unset", None, None),
                ("root missing", self.temp / "missing package", None),
                ("text not UTF-8", package, lambda: text.write_bytes(b"\xff\xfe\x00broken")),
                ("text deleted", package, text.unlink),
            )
            for case, root, prepare in cases:
                with self.subTest(host=host, case=case):
                    if prepare is not None:
                        prepare()

                    result = self.run_launcher(command, host, root)

                    self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_launcher_does_not_read_text_outside_its_root(self):
        self.declare(ROUTING)
        package = self.publish("claude")
        command = self.routing_command(package)
        outside = self.temp / "outside.md"
        outside.write_text("outside the package\n", encoding="utf-8")
        (package / TEXT).unlink()
        try:
            (package / TEXT).symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symbolic links unavailable: {error}")

        result = self.run_launcher(command, "claude", package)

        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_routing_only_plugin_adds_no_hook_note_to_any_body(self):
        for tables, noted in ((ROUTING + SESSION_HOOK, True), (ROUTING, False)):
            self.declare(tables)
            for host in HOSTS:
                with self.subTest(host=host, hooks=noted):
                    package = self.publish(host, " hooks" if noted else "")
                    bodies = [path for path in package.rglob("*.md")
                              if path.relative_to(package).as_posix() != TEXT]
                    self.assertTrue(bodies)
                    carrying = [path for path in bodies if NOTE in path.read_text(encoding="utf-8")]

                    if noted:
                        self.assertTrue(carrying, "the note marker must reach a [[hooks]] body")
                    else:
                        self.assertEqual(carrying, [])


class RoutingPointerTests(OwnedTemp):
    """Ruling R-3: pointers in DO NOT TRIGGER WHEN clauses, through `routing_text`."""

    def kernel(self, name, workflow="review", description="", required=()):
        root = self.temp / "kernel" / f"{name}-{len(list(self.temp.glob('kernel/*')))}"
        shutil.copytree(FIXTURE, root)
        manifest = root / "plugin.toml"
        text = manifest.read_text(encoding="utf-8").replace('name = "example"', f'name = "{name}"')
        text = text.replace("required = []", f"required = {json.dumps(list(required))}")
        text = text.replace('optional = ["execution.parallel"]',
                            'optional = ["execution.parallel", "hooks.lifecycle"]')
        workflows = root / "workflows"
        if workflow != "review":
            text = text.replace('workflows = ["review"]', f'workflows = ["{workflow}"]')
            sidecar = (workflows / "review.toml").read_text(encoding="utf-8")
            (workflows / f"{workflow}.toml").write_text(
                sidecar.replace('name = "review"', f'name = "{workflow}"').replace(
                    'entrypoint = "review.md"', f'entrypoint = "{workflow}.md"'), encoding="utf-8")
            (workflows / "review.toml").unlink()
            (workflows / "review.md").rename(workflows / f"{workflow}.md")
        if description:
            body = workflows / f"{workflow}.md"
            body.write_text(f"---\ndescription: >\n  {description}\n---\n\n"
                            + body.read_text(encoding="utf-8"), encoding="utf-8")
        manifest.write_text(text + "\n[routing]\nworkflows = true\n", encoding="utf-8")
        return load_plugin(root)

    def consumer_line(self, exclusion, host):
        consumer = self.kernel("consumer", description=f"Inspect the scope. {INSPECT} "
                               f"DO NOT TRIGGER WHEN: the user wants a delivery {exclusion}.",
                               required=["provider"])
        plugins = {"consumer": consumer, "provider": self.kernel("provider", "deliver", "Deliver."),
                   "other": self.kernel("other", "deliver", "Deliver elsewhere.")}
        text = routing_text(consumer, load_adapter(ADAPTERS, host), plugins)
        identity = "`review-workflow`" if host == "codex" else "`/consumer:review`"
        lines = [line for line in text.split("\n") if line.startswith(f"- {identity}")]
        self.assertEqual(len(lines), 1, text)
        return lines[0], identity

    def test_pointer_to_a_required_plugin_workflow_is_rewritten_per_host(self):
        cases = (
            ("(use /provider:deliver)",
             {"claude": "(use /provider:deliver)", "opencode": "(use /provider:deliver)",
              "codex": "(use deliver-workflow)"}),
            ("(use review or /provider:deliver)",
             {"claude": "(use /consumer:review or /provider:deliver)",
              "opencode": "(use /consumer:review or /provider:deliver)",
              "codex": "(use review-workflow or deliver-workflow)"}),
        )
        for exclusion, rewritten in cases:
            for host, pointer in rewritten.items():
                with self.subTest(exclusion=exclusion, host=host):
                    line, identity = self.consumer_line(exclusion, host)

                    self.assertEqual(line, f"- {identity}: {INSPECT} DO NOT TRIGGER WHEN: "
                                           f"the user wants a delivery {pointer}.")

    def test_or_clause_with_an_unresolved_name_is_dropped_whole(self):
        for exclusion in ("(use /provider:deliver or /provider:missing)",
                          "(use /provider:deliver or /other:deliver)",
                          "(use review or missing)"):
            for host in ("claude", "codex"):
                with self.subTest(exclusion=exclusion, host=host):
                    line, identity = self.consumer_line(exclusion, host)

                    self.assertEqual(line, f"- {identity}: {INSPECT}")


if __name__ == "__main__":
    unittest.main()
