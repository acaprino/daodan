"""MCP server declarations: a manifest where the host starts them, a note where it does not.

The motivating case is `peer-review`, whose `.mcp.json` and server lived at the kernel root
and shipped nowhere after the universal cutover: the compiler had no MCP concept, so the
package rendered cleanly and the workflow's transport calls could never connect.
"""

import json
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter, resolve_support  # noqa: E402
from scripts.daodan.catalogs import catalog_document, render_catalog  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.model import ModelError  # noqa: E402
from scripts.daodan.render import RenderError, publish_plugin  # noqa: E402
from scripts.daodan.validate import CAPABILITY_REGISTRY, validate_plugins  # noqa: E402

ADAPTERS = REPO_ROOT / "adapters"
FIXTURE = REPO_ROOT / "tests/fixtures/daodan/valid-mcp/plugins/example"
SERVER = "skills/tools/scripts/server.py"
DECLARATION = (
    '\n[[mcp.servers]]\nname = "example-tools"\ncommand = "uv"\n'
    'args = ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/skills/tools/scripts/server.py"]\n'
)
# Every kernel of this marketplace that ships an MCP server, with the server file
# and any module it needs beside it. A kernel that declares a server and is missing
# here fails `test_every_declared_server_is_pinned_here`.
SERVERS = {
    "codebase-map": ("skills/map-method/scripts", "mcp_server.py", ("mcp_service.py",)),
    "peer-review": ("skills/cross-model-peer-review/scripts", "server.py", ()),
    "moe": ("skills/multi-model-deliberation/scripts", "server.py", ()),
}
# Each server starts inside the user's project. Without these flags `uv` reads that
# project's uv.toml, pyproject.toml and .python-version, so the project would choose
# the index and interpreter of a server that may hold an API key.
ISOLATED_RUN = ("run", "--no-config", "--no-project", "--script")


def server_path(name: str) -> str:
    scripts, server, _ = SERVERS[name]
    return f"{scripts}/{server}"


class McpRenderingTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)

    def publish(self, host: str) -> Path:
        live = self.temp / host
        publish_plugin(load_plugin(FIXTURE), load_adapter(ADAPTERS, host), live)
        return live

    def test_fixture_is_valid(self):
        self.assertEqual(validate_plugins([load_plugin(FIXTURE)], CAPABILITY_REGISTRY), [])

    def test_claude_renders_the_manifest_and_the_catalog_pointer(self):
        live = self.publish("claude")
        manifest = json.loads((live / ".mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(
            manifest,
            {
                "mcpServers": {
                    "example-tools": {
                        "command": "uv",
                        "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/" + SERVER],
                    }
                }
            },
        )
        self.assertTrue((live / SERVER).is_file())
        catalog = catalog_document("claude", [load_plugin(FIXTURE)], "1.0.0", {"example": live})
        self.assertEqual(catalog["plugins"][0]["mcpServers"], "./.mcp.json")
        # The manifest is the mechanism; nothing needs telling the user on Claude.
        for path in live.rglob("*.md"):
            self.assertNotIn("register that command", path.read_text(encoding="utf-8"))

    def test_other_hosts_ship_the_server_and_a_registration_note(self):
        for host, root_reference in (("codex", "<plugin-root>"),
                                     ("copilot", "${PLUGIN_ROOT}"),
                                     ("pi", "<plugin-root>")):
            with self.subTest(host=host):
                live = self.publish(host)
                self.assertFalse((live / ".mcp.json").exists())
                self.assertTrue((live / SERVER).is_file())
                noted = [
                    path.read_text(encoding="utf-8")
                    for path in live.rglob("*.md")
                    if "register that command" in path.read_text(encoding="utf-8")
                ]
                self.assertTrue(noted, f"{host}: no workflow carries the registration note")
                for text in noted:
                    self.assertIn("`example-tools`", text)
                    self.assertIn(f"uv run --script {root_reference}/{SERVER}", text)
                    self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)
                catalog = catalog_document(
                    host, [load_plugin(FIXTURE)], "1.0.0", {"example": live}
                )
                self.assertNotIn("mcpServers", catalog["plugins"][0])
                if host == "pi":
                    self.assertTrue(all("pi-mcp-adapter" in text for text in noted))

    def test_opencode_declares_the_server_for_the_loader(self):
        live = self.publish("opencode")
        plugin = load_plugin(FIXTURE)
        catalog = json.loads(render_catalog("opencode", [plugin], "1.0.0", {plugin.name: live}))

        self.assertTrue((live / SERVER).is_file())
        self.assertEqual(catalog["daodan"]["plugins"][plugin.name]["mcp"], [{
            "name": "example-tools",
            "command": ["uv", "run", "--script", "<plugin-root>/" + SERVER],
        }])
        for path in live.rglob("*.md"):
            self.assertNotIn("register that command", path.read_text(encoding="utf-8"))

    def test_registration_note_requires_connection_before_mcp_tool_use(self):
        for host in ("codex", "copilot", "pi"):
            with self.subTest(host=host):
                live = self.publish(host)
                notes = [line for path in live.rglob("*.md")
                         for line in path.read_text(encoding="utf-8").splitlines()
                         if "This plugin declares an MCP server," in line]
                self.assertTrue(notes, f"{host}: missing MCP registration instructions")
                for note in notes:
                    self.assertIn("Before calling this server's tools, register that command", note)
                    self.assertNotIn("before running this workflow", note)


class KernelMcpRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.temp, True)
        cls.plugins = {name: load_plugin(REPO_ROOT / "plugins" / name) for name in SERVERS}
        cls.packages = {}
        for name, plugin in cls.plugins.items():
            for host in HOSTS:
                live = cls.temp / host / name
                publish_plugin(plugin, load_adapter(ADAPTERS, host), live, adapters_root=ADAPTERS)
                cls.packages[(host, name)] = live
        cls.plugin = cls.plugins["codebase-map"]

    def catalog(self, host, name):
        return json.loads(render_catalog(
            host, [self.plugins[name]], "1.0.0", {name: self.packages[(host, name)]},
        ))

    def test_every_declared_server_is_pinned_here(self):
        declared = {
            manifest.parent.name
            for manifest in (REPO_ROOT / "plugins").glob("*/plugin.toml")
            if load_plugin(manifest.parent).mcp_servers
        }
        self.assertEqual(declared, set(SERVERS))

    def test_each_kernel_requires_the_capability_and_starts_its_server_isolated(self):
        for name, plugin in self.plugins.items():
            with self.subTest(plugin=name):
                self.assertIn("mcp.servers", plugin.capabilities.required)
                self.assertEqual(
                    [(server.name, server.command, server.args) for server in plugin.mcp_servers],
                    [(name, "uv", ISOLATED_RUN + ("${CLAUDE_PLUGIN_ROOT}/" + server_path(name),))],
                )

    def test_server_modules_and_local_helpers_ship_unchanged_on_every_host(self):
        for name, (scripts, server, companions) in SERVERS.items():
            root = REPO_ROOT / "plugins" / name
            for required in (server, *companions):
                self.assertTrue((root / scripts / required).is_file(), f"{name}: {required}")
            for source in sorted((root / scripts).rglob("*.py")):
                relative = source.relative_to(root)
                for host in HOSTS:
                    with self.subTest(plugin=name, host=host, helper=relative.as_posix()):
                        rendered = self.packages[(host, name)] / relative
                        self.assertTrue(rendered.is_file(), str(rendered))
                        self.assertEqual(rendered.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))

    def test_manifest_hosts_expose_the_actual_command(self):
        for name, plugin in self.plugins.items():
            with self.subTest(plugin=name):
                manifest = json.loads((self.packages[("claude", name)] / ".mcp.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest, {"mcpServers": {name: {
                    "command": "uv",
                    "args": [*ISOLATED_RUN, "${CLAUDE_PLUGIN_ROOT}/" + server_path(name)],
                }}})
                self.assertEqual(self.catalog("claude", name)["plugins"][0]["mcpServers"], "./.mcp.json")
                self.assertEqual(self.catalog("opencode", name)["daodan"]["plugins"][name]["mcp"], [{
                    "name": name,
                    "command": ["uv", *ISOLATED_RUN, "<plugin-root>/" + server_path(name)],
                }])
                for host in ("claude", "opencode"):
                    for workflow in plugin.components.workflows:
                        path = self.packages[(host, name)] / f"commands/{workflow}.md"
                        self.assertNotIn("register that command", path.read_text(encoding="utf-8"))

    def test_registration_hosts_bind_every_entry_to_the_real_server_command(self):
        entries = {
            "codex": "skills/{workflow}-workflow/SKILL.md",
            "copilot": "prompts/{workflow}.prompt.md",
            "pi": "prompts/{plugin}-{workflow}.md",
        }
        roots = {"codex": "<plugin-root>", "copilot": "${PLUGIN_ROOT}", "pi": "<plugin-root>"}
        launch = " ".join(("uv", *ISOLATED_RUN))
        for name, plugin in self.plugins.items():
            for host, entry in entries.items():
                package = self.packages[(host, name)]
                self.assertFalse((package / ".mcp.json").exists(), f"{name} on {host}")
                # Every entry announces the server: each workflow and, because a
                # consumer reaches a provider's tools through its skill, each skill.
                paths = [package / f"skills/{skill}/SKILL.md" for skill in plugin.components.skills]
                for workflow in plugin.components.workflows:
                    paths.append(package / entry.format(plugin=name, workflow=workflow))
                    coordinator = package / f"agents/{workflow}-coordinator.agent.md"
                    if host == "copilot" and coordinator.exists():
                        paths.append(coordinator)
                self.assertTrue(paths, f"{name} on {host}: no entry to announce the server")
                for path in paths:
                    with self.subTest(plugin=name, host=host, entry=path.name):
                        text = path.read_text(encoding="utf-8")
                        self.assertIn(f"`{name}`", text)
                        self.assertIn("register that command", text)
                        self.assertIn(f"{launch} {roots[host]}/{server_path(name)}", text)
                        self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)
                        if host == "pi":
                            self.assertIn("pi-mcp-adapter", text)
                            self.assertIn("mcpServers", text)
                if host != "pi":
                    self.assertNotIn("mcpServers", self.catalog(host, name)["plugins"][0])

    def test_codebase_map_server_declares_tree_sitter_script_dependencies(self):
        script = REPO_ROOT / "plugins/codebase-map" / server_path("codebase-map")
        header = "\n".join(script.read_text(encoding="utf-8").splitlines()[:6])
        self.assertIn("tree-sitter>=0.23", header)
        self.assertIn("tree-sitter-language-pack>=1.0", header)

    def test_missing_or_unsupported_mcp_binding_blocks_publication_on_every_host(self):
        for host in HOSTS:
            for failure in ("missing", "unsupported"):
                with self.subTest(host=host, binding=failure):
                    adapter = load_adapter(ADAPTERS, host)
                    bindings = dict(adapter.bindings)
                    if failure == "missing":
                        bindings.pop("mcp.servers")
                    else:
                        bindings["mcp.servers"] = replace(bindings["mcp.servers"], state="unsupported")
                    adapter = replace(adapter, bindings=bindings)
                    support = resolve_support(self.plugin, adapter)
                    self.assertEqual(support.state, "unsupported")
                    self.assertIn("mcp.servers", support.missing_capabilities)
                    live = self.temp / f"{host}-{failure}"
                    live.mkdir()
                    previous = live / "previous.txt"
                    previous.write_bytes(b"preserve previous published output")

                    with self.assertRaisesRegex(RenderError, "missing: mcp.servers"):
                        publish_plugin(self.plugin, adapter, live, adapters_root=ADAPTERS)

                    self.assertEqual(list(live.iterdir()), [previous])
                    self.assertEqual(previous.read_bytes(), b"preserve previous published output")


class McpValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.root = self.temp / "example"
        shutil.copytree(FIXTURE, self.root)
        self.manifest = self.root / "plugin.toml"

    def rewrite(self, old: str, new: str) -> None:
        text = self.manifest.read_text(encoding="utf-8")
        self.assertIn(old, text)
        self.manifest.write_text(text.replace(old, new), encoding="utf-8")

    def codes(self) -> set[str]:
        return {issue.code for issue in validate_plugins([load_plugin(self.root)], CAPABILITY_REGISTRY)}

    def test_servers_require_the_capability(self):
        self.rewrite('"roles.dispatch", "mcp.servers"]', '"roles.dispatch"]')
        self.assertIn("mcp-capability-undeclared", self.codes())

    def test_capability_requires_a_server(self):
        self.rewrite(DECLARATION, "\n")
        self.assertIn("mcp-capability-without-servers", self.codes())

    def test_server_must_start_from_a_shipped_file(self):
        self.rewrite("${CLAUDE_PLUGIN_ROOT}/skills/tools/scripts/server.py", "${CLAUDE_PLUGIN_ROOT}/mcp/server.py")
        self.assertIn("mcp-server-file-not-shipped", self.codes())

    def test_server_must_stay_inside_the_plugin(self):
        self.rewrite("${CLAUDE_PLUGIN_ROOT}/skills/tools/scripts/server.py", "${CLAUDE_PLUGIN_ROOT}/../server.py")
        self.assertIn("path-outside-plugin", self.codes())

    def test_unknown_server_keys_are_rejected_at_load(self):
        self.rewrite('command = "uv"\n', 'command = "uv"\nenv = { KEY = "value" }\n')
        with self.assertRaises(ModelError):
            load_plugin(self.root)


if __name__ == "__main__":
    unittest.main()
