"""The catalog is generated from registered knowledge, on every host."""
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SkillCatalogCompilerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / 'scripts/daodan/skill_catalog.py').is_file(),
                        'Compiler skill metadata integration is missing')
        from scripts.daodan_build import discover_plugins
        self.registry = {p.name: p for p in discover_plugins(ROOT)}

    def test_index_contains_registered_skill_metadata_without_body_content(self):
        from scripts.daodan.skill_catalog import declared_catalog
        catalog = declared_catalog(self.registry)
        rows = {row['id']: row for row in catalog['entries']}
        self.assertEqual(len(rows), sum(len(p.components.skills) for p in self.registry.values()))
        self.assertEqual(rows['kotlin-development:kotlin-specialist']['kind'], 'knowledge')
        self.assertIn('kotlin', rows['kotlin-development:kotlin-specialist']['languages'])
        self.assertNotIn('senior-review:code-auditor', rows)
        self.assertNotIn('senior-review:code-review', rows)
        self.assertFalse(any('content' in row or 'root' in row for row in rows.values()))

    def test_invalid_sidecar_fails_semantic_validation(self):
        from scripts.daodan.load import load_plugin
        from scripts.daodan.validate import validate_plugins, CAPABILITY_REGISTRY
        import shutil
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'kotlin-development'
            shutil.copytree(ROOT / 'plugins/kotlin-development', root)
            (root / 'skills/kotlin-specialist/SKILL.toml').write_text(
                'schema = "daodan/skill-metadata/v1"\nkind = "knowledge"\noperations = ["review"]\ncommands = ["publish"]\n')
            issues = validate_plugins([load_plugin(root)], CAPABILITY_REGISTRY)
            self.assertIn('invalid-skill-metadata', [item.code for item in issues])

    def test_catalog_and_inventory_instructions_ship_deterministically_on_five_hosts(self):
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.render import render_plugin, tree_digest
        with tempfile.TemporaryDirectory() as temporary:
            for host in HOSTS:
                with self.subTest(host=host):
                    first, second = Path(temporary) / host / 'a', Path(temporary) / host / 'b'
                    adapter = load_adapter(ROOT / 'adapters', host)
                    for directory in (first, second):
                        render_plugin(self.registry['skill-catalog'], adapter, directory,
                                      adapters_root=ROOT / 'adapters', plugin_registry=self.registry)
                    self.assertEqual(tree_digest(first), tree_digest(second))
                    reference = first / 'skills/skill-catalog/references'
                    catalog = json.loads((reference / 'catalog.json').read_text())
                    self.assertEqual(catalog['schema'], 'daodan/skill-catalog/v1')
                    instructions = (reference / 'host-inventory.md').read_text()
                    self.assertIn(host, instructions)
                    self.assertIn('not installation evidence', instructions)
                    self.assertTrue((first / 'skills/skill-catalog/scripts/catalog.py').is_file())

    def test_catalog_is_a_leaf_and_review_uses_it_as_a_required_provider(self):
        self.assertEqual(self.registry['skill-catalog'].required_dependencies, ())
        self.assertIn('skill-catalog', self.registry['senior-review'].required_dependencies)

    def test_crlf_source_metadata_matches_the_rendered_lf_sidecar(self):
        from dataclasses import replace
        from scripts.daodan.adapter import load_adapter
        from scripts.daodan.render import render_plugin
        from scripts.daodan.skill_catalog import declared_catalog, runtime
        import shutil
        with tempfile.TemporaryDirectory() as temporary:
            source, output = Path(temporary) / 'source', Path(temporary) / 'output'
            shutil.copytree(ROOT / 'plugins/kotlin-development', source)
            metadata = source / 'skills/kotlin-specialist/SKILL.toml'
            metadata.write_bytes(metadata.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
            provider = replace(self.registry['kotlin-development'], root=source)
            render_plugin(provider, load_adapter(ROOT / 'adapters', 'codex'), output,
                          adapters_root=ROOT / 'adapters')
            inventory = [dict(id='kotlin-development:kotlin-specialist', provider=provider.name,
                              version=provider.version, root=str(output), file='skills/kotlin-specialist/SKILL.md')]
            actual = runtime().index_inventory(declared_catalog({provider.name: provider}), inventory)
            self.assertEqual(actual['gaps'], [])
            self.assertEqual(len(actual['entries']), 1)

    def test_windows_checkout_sidecar_matches_declaration_but_run_pins_exact_bytes(self):
        from scripts.daodan.adapter import load_adapter
        from scripts.daodan.render import render_plugin
        from scripts.daodan.skill_catalog import declared_catalog, runtime
        import hashlib
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            provider = self.registry['kotlin-development']
            render_plugin(provider, load_adapter(ROOT / 'adapters', 'codex'), output,
                          adapters_root=ROOT / 'adapters')
            metadata = output / 'skills/kotlin-specialist/SKILL.toml'
            lf = metadata.read_bytes()
            crlf = lf.replace(b'\n', b'\r\n')
            metadata.write_bytes(crlf)
            inventory = [dict(id='kotlin-development:kotlin-specialist', provider=provider.name,
                              version=provider.version, root=str(output), file='skills/kotlin-specialist/SKILL.md')]
            api = runtime()
            actual = api.index_inventory(declared_catalog({provider.name: provider}), inventory)
            self.assertEqual(actual['gaps'], [])
            self.assertEqual(actual['entries'][0]['metadata_sha256'], hashlib.sha256(crlf).hexdigest())
            request = dict(run_id='review', project_id='fixture', snapshot_id='candidate', operation='review',
                           scopes=[dict(id='service', languages=['kotlin'], paths=['service/src'],
                                        evidence=['Inspected candidate Kotlin package'],
                                        workers={dimension: ['code-auditor'] for dimension in
                                                 ('correctness', 'resource-lifecycle')})])
            prepared = api.prepare(actual, request)
            self.assertEqual(prepared['status'], 'prepared')
            metadata.write_bytes(lf)
            with self.assertRaises(api.CatalogError):
                api.load_skill(prepared, inventory[0]['id'])


if __name__ == '__main__':
    unittest.main()
