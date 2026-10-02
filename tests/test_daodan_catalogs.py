"""Cross-host identity tests for the generated catalogs."""

import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS  # noqa: E402
from scripts.daodan.catalogs import CatalogError, assert_cross_host_identity, render_catalog  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402

VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"


def build_fixture_catalogs():
    plugins = [load_plugin(VALID)]
    return {
        host: json.loads(render_catalog(host, plugins, "1.0.0").decode("utf-8")) for host in HOSTS
    }


class CatalogTests(unittest.TestCase):
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

    def test_entries_are_sorted_by_plugin_name(self):
        catalog = build_fixture_catalogs()["claude"]
        names = [entry["name"] for entry in catalog["plugins"]]
        self.assertEqual(names, sorted(names))

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
        entry = live_opencode_manifest()["daodan"]["plugins"]["senior-review"]
        self.assertIn("senior-review:code-auditor", [a["id"] for a in entry["agents"]])
        self.assertIn("senior-review:code-review", [c["name"] for c in entry["commands"]])
        self.assertIn(
            "senior-review:review-quality-gates", [s["id"] for s in entry["skills"]]
        )

    def test_dependencies_are_local_only(self):
        plugins = live_opencode_manifest()["daodan"]["plugins"]
        self.assertIn("codebase-xray", plugins["senior-review"]["dependencies"])
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

    def test_peer_review_declares_its_server(self):
        mcp = live_opencode_manifest()["daodan"]["plugins"]["peer-review"]["mcp"]
        self.assertEqual(mcp[0]["name"], "peer-review")
        self.assertTrue(any("<plugin-root>" in part for part in mcp[0]["command"]))
        self.assertFalse(any("CLAUDE_PLUGIN_ROOT" in part for part in mcp[0]["command"]))

    def test_loader_is_the_adapter_template_byte_for_byte(self):
        self.assertEqual(
            (OPENCODE / "index.js").read_bytes(),
            (REPO_ROOT / "adapters/opencode/templates/index.js").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
