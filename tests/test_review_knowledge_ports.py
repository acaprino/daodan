"""Required catalog inputs survive the review's native contracts and exports."""
from pathlib import Path
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReviewKnowledgePortTests(unittest.TestCase):
    def test_review_records_account_for_selection_and_usage(self):
        expected = {'reviewer-selection': 'knowledge_selection', 'review-brief': 'knowledge_selection',
                    'reviewer-binding': 'knowledge_ids', 'reviewer-result': 'knowledge_usage',
                    'final-report': 'knowledge_coverage'}
        for name, field in expected.items():
            with self.subTest(contract=name):
                record = tomllib.loads((ROOT / f'plugins/senior-review/contracts/{name}.toml').read_text())
                self.assertIn(field, record['required'])

    def test_all_entry_variants_import_the_required_catalog_contracts(self):
        from scripts.daodan.load import load_plugin
        plugin = load_plugin(ROOT / 'plugins/senior-review')
        for workflow in plugin.workflows:
            with self.subTest(variant=workflow.name):
                self.assertIn('skill-catalog/contracts/knowledge-selection.toml', workflow.contract.shared_schemas)
                self.assertIn('skill-catalog/contracts/knowledge-usage.toml', workflow.contract.shared_schemas)

    def test_catalog_bindings_are_available_in_compiled_review_on_every_host(self):
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.load import load_plugin
        from scripts.daodan.render import render_plugin
        registry = {p.parent.name: load_plugin(p.parent) for p in (ROOT / 'plugins').glob('*/plugin.toml')}
        with tempfile.TemporaryDirectory() as temporary:
            for host in HOSTS:
                with self.subTest(host=host):
                    root = Path(temporary) / host
                    render_plugin(registry['senior-review'], load_adapter(ROOT / 'adapters', host), root,
                                  adapters_root=ROOT / 'adapters', plugin_registry=registry)
                    preparation = (root / 'skills/review-preparation/SKILL.md').read_text()
                    self.assertIn('skill-catalog:skill-catalog', preparation)
                    self.assertIn('knowledge-bindings.md', preparation)
                    reference = root / 'skills/review-preparation/references/knowledge-bindings.md'
                    self.assertTrue(reference.is_file())
                    self.assertIn('same candidate snapshot', reference.read_text())
                    method = (root / 'skills/review-method/SKILL.md').read_text()
                    self.assertIn('knowledge_selection', method)
                    consolidation = (root / 'skills/review-consolidation/SKILL.md').read_text()
                    self.assertIn('validate-usage', consolidation)


if __name__ == '__main__':
    unittest.main()
