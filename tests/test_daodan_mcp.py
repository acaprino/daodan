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
MAP_ROOT = REPO_ROOT / "plugins/codebase-map"
MAP_SCRIPTS = Path("skills/map-method/scripts")
MAP_SERVER = (MAP_SCRIPTS / "mcp_server.py").as_posix()
MAP_SERVICE = (MAP_SCRIPTS / "mcp_service.py").as_posix()


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


class CodebaseMapMcpRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.temp, True)
        cls.plugin = load_plugin(MAP_ROOT)
        cls.packages = {}
        for host in HOSTS:
            live = cls.temp / host / cls.plugin.name
            publish_plugin(cls.plugin, load_adapter(ADAPTERS, host), live, adapters_root=ADAPTERS)
            cls.packages[host] = live

    def catalog(self, host):
        return json.loads(render_catalog(
            host, [self.plugin], "1.0.0", {self.plugin.name: self.packages[host]},
        ))

    def test_real_kernel_declares_the_shipped_server_as_a_required_capability(self):
        self.assertIn("mcp.servers", self.plugin.capabilities.required)
        self.assertEqual(
            [(server.name, server.command, server.args) for server in self.plugin.mcp_servers],
            [("codebase-map", "uv", ("run", "--script", "${CLAUDE_PLUGIN_ROOT}/" + MAP_SERVER))],
        )

    def test_server_service_and_local_helpers_ship_unchanged_on_every_host(self):
        for required in (MAP_SERVER, MAP_SERVICE):
            self.assertTrue((MAP_ROOT / required).is_file(), required)
        helpers = sorted((MAP_ROOT / MAP_SCRIPTS).rglob("*.py"))
        for host, package in self.packages.items():
            for source in helpers:
                relative = source.relative_to(MAP_ROOT)
                with self.subTest(host=host, helper=relative.as_posix()):
                    rendered = package / relative
                    self.assertTrue(rendered.is_file(), str(rendered))
                    self.assertEqual(rendered.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))

    def test_manifest_hosts_expose_the_actual_codebase_map_command(self):
        manifest = json.loads((self.packages["claude"] / ".mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest, {"mcpServers": {"codebase-map": {
            "command": "uv",
            "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/" + MAP_SERVER],
        }}})
        self.assertEqual(self.catalog("claude")["plugins"][0]["mcpServers"], "./.mcp.json")
        self.assertEqual(self.catalog("opencode")["daodan"]["plugins"]["codebase-map"]["mcp"], [{
            "name": "codebase-map",
            "command": ["uv", "run", "--script", "<plugin-root>/" + MAP_SERVER],
        }])
        for host in ("claude", "opencode"):
            for workflow in self.plugin.components.workflows:
                with self.subTest(host=host, workflow=workflow):
                    path = self.packages[host] / f"commands/{workflow}.md"
                    self.assertNotIn("register that command", path.read_text(encoding="utf-8"))

    def test_registration_hosts_bind_every_workflow_to_the_real_server_command(self):
        entries = {
            "codex": "skills/{workflow}-workflow/SKILL.md",
            "copilot": "prompts/{workflow}.prompt.md",
            "pi": "prompts/codebase-map-{workflow}.md",
        }
        roots = {"codex": "<plugin-root>", "copilot": "${PLUGIN_ROOT}", "pi": "<plugin-root>"}
        for host, entry in entries.items():
            package = self.packages[host]
            self.assertFalse((package / ".mcp.json").exists(), host)
            for workflow in self.plugin.components.workflows:
                paths = [package / entry.format(workflow=workflow)]
                if host == "copilot":
                    paths.append(package / f"agents/{workflow}-coordinator.agent.md")
                for path in paths:
                    with self.subTest(host=host, workflow=workflow, entry=path.name):
                        text = path.read_text(encoding="utf-8")
                        self.assertIn("`codebase-map`", text)
                        self.assertIn("register that command", text)
                        self.assertIn(f"uv run --script {roots[host]}/{MAP_SERVER}", text)
                        self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)
                        if host == "pi":
                            self.assertIn("pi-mcp-adapter", text)
                            self.assertIn("mcpServers", text)
            if host != "pi":
                self.assertNotIn("mcpServers", self.catalog(host)["plugins"][0])

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
