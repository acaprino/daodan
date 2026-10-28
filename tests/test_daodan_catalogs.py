"""Cross-host identity tests for the generated catalogs."""

import json
import re
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.catalogs import (  # noqa: E402
    CatalogError,
    assert_cross_host_identity,
    catalog_document,
    render_catalog,
)
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import render_plugin  # noqa: E402
from scripts.daodan_build import _render_host_catalog  # noqa: E402

VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"


def build_fixture_catalogs():
    plugins = [load_plugin(VALID)]
    return {
        host: json.loads(render_catalog(host, plugins, "1.0.0").decode("utf-8")) for host in HOSTS
    }


class CatalogTests(unittest.TestCase):
    def test_publication_factory_rebuilds_stale_catalogs_from_current_authority(self):
        """Saved registrations are generated output, never a second owner."""
        base = load_plugin(REPO_ROOT / "tests/fixtures/daodan/valid-mcp/plugins/example")
        base = replace(base, required_dependencies=("current-tool@current-marketplace",))
        newcomer = replace(base, name="newcomer", version="2.0.0")
        plugins = [newcomer, base]
        with tempfile.TemporaryDirectory(prefix="daodan-current-catalog-") as holder:
            root = Path(holder)
            for host in HOSTS:
                with self.subTest(host=host):
                    adapter = load_adapter(REPO_ROOT / "adapters", host)
                    catalog_path = root / adapter.layout["marketplace"]
                    catalog_path.parent.mkdir(parents=True, exist_ok=True)
                    stale = {"name": "old-marketplace", "metadata": {"version": "0.0.1",
                             "description": "Old description"}, "version": "0.0.1",
                             "allowCrossMarketplaceDependenciesOn": ["old-marketplace"],
                             "plugins": [
                                 {"name": "example", "version": "0.0.1", "source": "./old/example",
                                  "agents": ["./old/worker.md"], "skills": ["./old/skill"],
                                  "commands": ["./old/command.md"], "mcpServers": "./old/.mcp.json"},
                                 {"name": "ghost", "version": "7.0.0",
                                  "source": f"./exports/{host}/plugins/ghost"},
                                 {"name": "ghost", "version": "7.0.0",
                                  "source": f"./exports/{host}/plugins/ghost"},
                                 {"name": "foreign", "version": "8.0.0",
                                  "source": {"source": "github", "repo": "someone/foreign"}}]}
                    saved = (json.dumps(stale, indent=3) + "\n").encode("utf-8")
                    catalog_path.write_bytes(saved)
                    ghost = root / adapter.layout["root"] / "plugins/ghost/owned-note.txt"
                    ghost.parent.mkdir(parents=True, exist_ok=True)
                    ghost.write_bytes(b"preserve physical output pending retirement")
                    packages = {plugin.name: root / host / plugin.name for plugin in plugins}
                    for plugin in plugins:
                        render_plugin(plugin, adapter, packages[plugin.name],
                                      adapters_root=REPO_ROOT / "adapters")

                    rendered = _render_host_catalog(
                        root, adapter, host, plugins, "4.5.6", catalog_path, packages,
                        name="current-marketplace", description="Current description")
                    expected = render_catalog(
                        host, plugins, "4.5.6", packages, layout=adapter.layout,
                        name="current-marketplace", description="Current description")
                    self.assertEqual(rendered, expected)
                    self.assertEqual(catalog_path.read_bytes(), saved)
                    self.assertEqual(ghost.read_bytes(), b"preserve physical output pending retirement")
                    current = json.loads(rendered)
                    self.assertEqual(current["name"], "current-marketplace")
                    self.assertNotIn("./old/", rendered.decode("utf-8"))
                    if host in {"claude", "copilot", "codex"}:
                        self.assertEqual(current["metadata"]["version"], "4.5.6")
                        self.assertEqual([(item["name"], item["version"]) for item in current["plugins"]],
                                         [("example", "1.2.3"), ("newcomer", "2.0.0")])
                        self.assertEqual(current["allowCrossMarketplaceDependenciesOn"], ["current-marketplace"])
                        for entry in current["plugins"]:
                            self.assertEqual(entry["source"], f"./exports/{host}/plugins/{entry['name']}")
                            expected_skills = ["./skills/tools"]
                            if host == "codex":
                                expected_skills.insert(0, "./skills/review-workflow")
                            self.assertEqual(entry["skills"], expected_skills)
                            self.assertEqual(entry["dependencies"], ["current-tool@current-marketplace"])
                    else:
                        self.assertEqual(current["version"], "4.5.6")
                        self.assertNotIn("plugins", current)
                        if host == "opencode":
                            self.assertEqual(list(current["daodan"]["plugins"]), ["example", "newcomer"])
                            entry = current["daodan"]["plugins"]["example"]
                            self.assertEqual(entry["skills"][0]["id"], "example:tools")
                            self.assertEqual(entry["commands"][0]["name"], "example:review")

    def test_catalogs_share_identity_names_and_versions(self):
        catalogs = build_fixture_catalogs()
        self.assertEqual({catalog["name"] for catalog in catalogs.values()}, {"daodan"})
        listings = {host: item for host, item in catalogs.items() if "plugins" in item}
        versions = {entry["name"]: entry["version"] for entry in listings["claude"]["plugins"]}
        for catalog in listings.values():
            self.assertEqual(
                {entry["name"]: entry["version"] for entry in catalog["plugins"]}, versions
            )
        # Pi's catalog is a package manifest and names no plugin, so the identity
        # it can carry is the marketplace version the others carry in metadata.
        self.assertEqual(catalogs["pi"]["version"], listings["claude"]["metadata"]["version"])

    def test_pi_catalog_is_an_npm_manifest_that_globs_the_rendered_tree(self):
        catalog = build_fixture_catalogs()["pi"]
        self.assertNotIn("plugins", catalog)
        self.assertEqual(catalog["keywords"], ["pi-package"])
        self.assertEqual(catalog["license"], "MIT")
        self.assertIs(catalog["private"], True)
        self.assertEqual(catalog["pi"]["skills"], ["./exports/pi/plugins/*/skills"])
        self.assertEqual(catalog["pi"]["prompts"], ["./exports/pi/plugins/*/prompts"])

    def test_opencode_catalog_is_a_v2_plugin_package(self):
        catalog = build_fixture_catalogs()["opencode"]
        self.assertNotIn("plugins", catalog)
        self.assertEqual(catalog["name"], "daodan")
        self.assertEqual(catalog["version"], "1.0.0")
        self.assertEqual(catalog["main"], "index.js")
        self.assertEqual(catalog["type"], "module")
        self.assertEqual(catalog["keywords"], ["opencode-plugin"])
        self.assertIs(catalog["private"], True)
        self.assertEqual(catalog["daodan"]["schema"], 1)
        entry = catalog["daodan"]["plugins"]["example"]
        self.assertEqual(entry["root"], "plugins/example")

    def test_each_host_gets_its_native_source_shape(self):
        catalogs = build_fixture_catalogs()
        self.assertEqual(
            catalogs["claude"]["plugins"][0]["source"], "./exports/claude/plugins/example"
        )
        self.assertEqual(
            catalogs["copilot"]["plugins"][0]["source"], "./exports/copilot/plugins/example"
        )
        # Codex takes a path string like the others. The `{"source": "local",
        # "path": ...}` shape the design specified registers the marketplace and
        # then reports every plugin in it as not found.
        self.assertEqual(
            catalogs["codex"]["plugins"][0]["source"], "./exports/codex/plugins/example"
        )
        self.assertNotIn("path", catalogs["codex"]["plugins"][0])

    def test_rendering_is_byte_stable(self):
        plugins = [load_plugin(VALID)]
        self.assertEqual(
            render_catalog("claude", plugins, "1.0.0"),
            render_catalog("claude", plugins, "1.0.0"),
        )

    def test_each_catalog_entry_rejects_identical_version_duplicate_identity(self):
        with tempfile.TemporaryDirectory(prefix="daodan-duplicate-catalog-") as holder:
            roots = [Path(holder) / origin / "example" for origin in ("first", "second")]
            for root in roots:
                shutil.copytree(VALID, root)
            plugins = [load_plugin(root) for root in roots]

            for host in HOSTS:
                for entrypoint in (catalog_document, render_catalog):
                    with self.subTest(host=host, entrypoint=entrypoint.__name__):
                        diagnoses = []
                        for _ in range(2):
                            with self.assertRaises(CatalogError) as caught:
                                entrypoint(host, plugins, "1.0.0")
                            diagnoses.append(str(caught.exception))

                        self.assertEqual(diagnoses[0], diagnoses[1])
                        self.assertIn("duplicate", diagnoses[0].lower())
                        self.assertIn("example", diagnoses[0])
                        for root in roots:
                            self.assertIn(str(root), diagnoses[0])

    def test_entries_are_sorted_by_plugin_name(self):
        base = load_plugin(VALID)
        plugins = [replace(base, name="zeta", version="3.0.0"),
                   replace(base, name="mu", version="2.0.0"),
                   replace(base, name="alpha", version="1.0.0")]
        # These three literal names establish alpha < mu < zeta independently.
        expected_names = ["alpha", "mu", "zeta"]
        expected_versions = {"alpha": "1.0.0", "mu": "2.0.0", "zeta": "3.0.0"}

        for host in HOSTS:
            with self.subTest(host=host):
                neutral = catalog_document(host, plugins, "4.0.0")
                rendered = json.loads(render_catalog(host, plugins, "4.0.0"))

                self.assertEqual([entry["name"] for entry in neutral["plugins"]], expected_names)
                self.assertEqual({entry["name"]: entry["version"]
                                  for entry in neutral["plugins"]}, expected_versions)
                if host in ("claude", "codex", "copilot"):
                    self.assertEqual([entry["name"] for entry in rendered["plugins"]], expected_names)
                elif host == "opencode":
                    self.assertEqual(list(rendered["daodan"]["plugins"]), expected_names)
                else:
                    self.assertEqual(rendered["name"], "daodan")
                    self.assertEqual(rendered["version"], "4.0.0")


    def test_opencode_catalog_uses_the_rendered_custom_component_layout(self):
        plugin = load_plugin(REPO_ROOT / "tests/fixtures/daodan/valid-mcp/plugins/example")
        original = load_adapter(REPO_ROOT / "adapters", "opencode")
        adapter = replace(original, layout={**original.layout,
                          "skills": "${host}/${version}/knowledge/${skill}/SKILL.md",
                          "roles": "${host}/${license}/workers/${role}.md",
                          "workflows": "${host}/${version}/entries/${workflow}.md"})
        with tempfile.TemporaryDirectory(prefix="daodan-opencode-layout-") as holder:
            package = Path(holder) / "example"
            render_plugin(plugin, adapter, package, adapters_root=REPO_ROOT / "adapters")
            self.assertTrue((package / "opencode/1.2.3/knowledge/tools/SKILL.md").is_file())
            self.assertTrue((package / "opencode/MIT/workers/inspector.md").is_file())
            self.assertTrue((package / "opencode/1.2.3/entries/review.md").is_file())

            catalog = json.loads(render_catalog("opencode", [plugin], "1.0.0",
                                               {"example": package}, layout=adapter.layout))
            entry = catalog["daodan"]["plugins"]["example"]

            self.assertEqual([item["file"] for item in entry["skills"]], ["opencode/1.2.3/knowledge/tools/SKILL.md"])
            self.assertEqual([item["file"] for item in entry["agents"]], ["opencode/MIT/workers/inspector.md"])
            self.assertEqual([item["file"] for item in entry["commands"]], ["opencode/1.2.3/entries/review.md"])
            self.assertEqual(entry["agents"][0]["id"], "example:inspector")
            self.assertEqual(entry["skills"][0]["id"], "example:tools")
            self.assertEqual(entry["commands"][0]["name"], "example:review")
            for kind in ("skills", "agents", "commands"):
                for item in entry[kind]:
                    self.assertTrue((package / item["file"]).is_file(), item["file"])

    def test_opencode_catalog_names_the_routing_file_when_rendered(self):
        adapter = load_adapter(REPO_ROOT / "adapters", "opencode")
        with tempfile.TemporaryDirectory(prefix="daodan-opencode-routing-") as holder:
            kernel = Path(holder) / "kernel" / "example"
            shutil.copytree(VALID, kernel)
            manifest = kernel / "plugin.toml"
            text = manifest.read_text(encoding="utf-8").replace(
                'optional = ["execution.parallel"]',
                'optional = ["execution.parallel", "hooks.lifecycle"]')
            manifest.write_text(text + "\n[routing]\nworkflows = true\n", encoding="utf-8")
            routed_plugin = load_plugin(kernel)

            routed = Path(holder) / "routed"
            render_plugin(routed_plugin, adapter, routed, adapters_root=REPO_ROOT / "adapters")
            self.assertTrue((routed / "hooks/entry-routing.md").is_file())
            routed_catalog = json.loads(render_catalog(
                "opencode", [routed_plugin], "1.0.0", {"example": routed}, layout=adapter.layout))
            self.assertEqual(
                routed_catalog["daodan"]["plugins"]["example"]["routing"], "hooks/entry-routing.md")

            plain_plugin = load_plugin(VALID)
            plain = Path(holder) / "plain"
            render_plugin(plain_plugin, adapter, plain, adapters_root=REPO_ROOT / "adapters")
            self.assertFalse((plain / "hooks/entry-routing.md").exists())
            plain_catalog = json.loads(render_catalog(
                "opencode", [plain_plugin], "1.0.0", {"example": plain}, layout=adapter.layout))
            self.assertNotIn("routing", plain_catalog["daodan"]["plugins"]["example"])

    def test_identity_check_rejects_a_divergent_host(self):
        catalogs = build_fixture_catalogs()
        catalogs["codex"]["plugins"][0]["version"] = "9.9.9"
        with self.assertRaises(CatalogError):
            assert_cross_host_identity(catalogs)


OPENCODE = REPO_ROOT / "exports/opencode"


def live_opencode_manifest() -> dict:
    return json.loads((OPENCODE / "package.json").read_text(encoding="utf-8"))


class OpenCodeManifestTests(unittest.TestCase):
    """The published manifest is what the loader reads, so it is read as the loader would."""

    def test_ids_carry_the_plugin_prefix(self):
        plugins = live_opencode_manifest()["daodan"]["plugins"]
        entry = plugins["senior-review"]
        self.assertIn("senior-review:code-auditor", [a["id"] for a in entry["agents"]])
        broker = plugins["trading-broker-integration"]
        self.assertIn("trading-broker-integration:ibkr-architect", [a["id"] for a in broker["agents"]])
        self.assertIn("trading-broker-integration:ibkr-audit", [c["name"] for c in broker["commands"]])
        self.assertIn(
            "trading-broker-integration:broker-vocabulary", [s["id"] for s in broker["skills"]]
        )
        # Core harness commands live in the `daodan` entry plugin; core specialists register none.
        self.assertIn("daodan:review-branch", [c["name"] for c in plugins["daodan"]["commands"]])
        self.assertNotIn("commands", entry)

    def test_dependencies_are_local_only(self):
        plugins = live_opencode_manifest()["daodan"]["plugins"]
        self.assertIn("research", plugins["business"]["dependencies"])
        for name, entry in plugins.items():
            for dependency in entry.get("dependencies", []):
                self.assertNotIn("@", dependency, name)
                self.assertIn(dependency, plugins, name)

    def test_agents_carry_their_permission_list(self):
        entry = live_opencode_manifest()["daodan"]["plugins"]["senior-review"]
        agent = next(a for a in entry["agents"] if a["id"] == "senior-review:code-auditor")
        self.assertEqual(agent["permissions"][0], {"action": "*", "resource": "*", "effect": "deny"})
        self.assertEqual(agent["permissions"][-1]["resource"], "<package-root>/**")

    def test_every_file_exists_and_no_command_uses_shell_syntax(self):
        for name, entry in live_opencode_manifest()["daodan"]["plugins"].items():
            for kind in ("skills", "agents", "commands"):
                for item in entry.get(kind, []):
                    path = OPENCODE / entry["root"] / item["file"]
                    self.assertTrue(path.is_file(), path)
                    if kind == "commands":
                        text = path.read_text(encoding="utf-8")
                        self.assertIsNone(re.search(r"(?m)^!`", text), path)

    def test_descriptions_are_present_for_every_agent_and_skill(self):
        for name, entry in live_opencode_manifest()["daodan"]["plugins"].items():
            for kind in ("skills", "agents"):
                for item in entry.get(kind, []):
                    self.assertTrue(item["description"].strip(), f"{name}: {item}")

    def test_every_published_server_is_portable_and_isolated_from_the_project(self):
        servers = {
            name: entry["mcp"]
            for name, entry in live_opencode_manifest()["daodan"]["plugins"].items()
            if entry.get("mcp")
        }
        self.assertEqual(set(servers), {"codebase-map", "peer-review", "moe", "work-controller"})
        for name, mcp in servers.items():
            with self.subTest(plugin=name):
                self.assertEqual(mcp[0]["name"], name)
                command = mcp[0]["command"]
                self.assertTrue(any("<plugin-root>" in part for part in command))
                self.assertFalse(any("CLAUDE_PLUGIN_ROOT" in part for part in command))
                self.assertEqual(command[:5], ["uv", "run", "--no-config", "--no-project", "--script"])

    def test_loader_is_the_adapter_template_byte_for_byte(self):
        self.assertEqual(
            (OPENCODE / "index.js").read_bytes(),
            (REPO_ROOT / "adapters/opencode/templates/index.js").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
