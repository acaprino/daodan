"""Cross-host identity tests for the generated catalogs."""

import json
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


if __name__ == "__main__":
    unittest.main()
