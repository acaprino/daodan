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
    merge_into_legacy,
    render_catalog,
)
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import render_plugin  # noqa: E402

VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"


def build_fixture_catalogs():
    plugins = [load_plugin(VALID)]
    return {
        host: json.loads(render_catalog(host, plugins, "1.0.0").decode("utf-8")) for host in HOSTS
    }


class CatalogTests(unittest.TestCase):
    def test_legacy_merge_replaces_compiled_entries_and_preserves_foreign_entries(self):
        """O01 migration keeps unrelated legacy registrations byte-equivalent."""
        base = load_plugin(VALID)
        newcomer = replace(base, name="newcomer", version="2.0.0")
        foreign = {"name": "foreign", "version": "7.0.0",
                   "source": {"source": "github", "repo": "someone/foreign"},
                   "agents": ["./old/worker.md"], "custom": {"keep": True}}
        existing = {"name": "legacy", "metadata": {"version": "9.0.0"},
                    "plugins": [foreign, {"name": "example", "version": "0.0.1",
                                          "source": "./old/example",
                                          "agents": ["./old/agent.md"],
                                          "skills": ["./old/skill"],
                                          "commands": ["./old/command.md"],
                                          "mcpServers": "./old/.mcp.json"}]}
        before = json.dumps(existing, sort_keys=True)
        with tempfile.TemporaryDirectory(prefix="daodan-legacy-catalog-") as holder:
            packages = {name: Path(holder) / name for name in ("example", "newcomer")}
            for package in packages.values():
                (package / "skills/tools").mkdir(parents=True)
                (package / "skills/tools/SKILL.md").write_text("fixture", encoding="utf-8")

            for host in ("claude", "copilot", "codex"):
                with self.subTest(host=host):
                    merged = merge_into_legacy(existing, [base, newcomer], host, packages)

                    self.assertEqual(merged["metadata"], {"version": "9.0.0"})
                    self.assertEqual(merged["plugins"][0], foreign)
                    self.assertEqual([item["name"] for item in merged["plugins"]],
                                     ["foreign", "example", "newcomer"])
                    for entry, version in zip(merged["plugins"][1:], ("1.2.3", "2.0.0")):
                        self.assertEqual(entry["version"], version)
                        self.assertEqual(entry["source"],
                                         f"./exports/{host}/plugins/{entry['name']}")
                        self.assertEqual(entry["skills"], ["./skills/tools"])
                        for stale in ("agents", "commands", "mcpServers"):
                            self.assertNotIn(stale, entry)
                    self.assertEqual(json.dumps(existing, sort_keys=True), before)

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
        entry = live_opencode_manifest()["daodan"]["plugins"]["peer-review"]
        self.assertIn("peer-review:respondent", [a["id"] for a in entry["agents"]])
        self.assertIn("peer-review:review", [c["name"] for c in entry["commands"]])
        self.assertIn(
            "peer-review:cross-model-peer-review", [s["id"] for s in entry["skills"]]
        )

    def test_dependencies_are_local_only(self):
        plugins = live_opencode_manifest()["daodan"]["plugins"]
        self.assertIn("peer-review", plugins["moe"]["dependencies"])
        for name, entry in plugins.items():
            for dependency in entry.get("dependencies", []):
                self.assertNotIn("@", dependency, name)
                self.assertIn(dependency, plugins, name)

    def test_agents_carry_their_permission_list(self):
        entry = live_opencode_manifest()["daodan"]["plugins"]["research"]
        agent = next(a for a in entry["agents"] if a["id"] == "research:quick-searcher")
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
