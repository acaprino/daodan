"""Scope selection, lazy knowledge reads and truthful delivery accounting."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'plugins/skill-catalog/skills/skill-catalog/scripts/catalog.py'


class SkillCatalogTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(HELPER.is_file(), 'The shared catalog runtime is missing')
        spec = importlib.util.spec_from_file_location('catalog_test_runtime', HELPER)
        self.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.api)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def skill(self, identity, *, languages=(), frameworks=(), topics=(),
              operations=('review',), kind='knowledge', version='1.0.0', dimensions=('correctness',)):
        provider, _, name = identity.partition(':')
        directory = self.root / provider / 'skills' / (name or provider)
        directory.mkdir(parents=True)
        (directory / 'SKILL.md').write_text(
            f'---\nname: {name or provider}\ndescription: Patterns for {identity}\n---\n\nKnowledge body\n', encoding='utf-8')
        fields = dict(schema='daodan/skill-metadata/v1', kind=kind,
                      operations=list(operations), languages=list(languages),
                      frameworks=list(frameworks), topics=list(topics),
                      dimensions=list(dimensions))
        (directory / 'SKILL.toml').write_text(
            '\n'.join(f'{key} = {json.dumps(value)}' for key, value in fields.items()) + '\n', encoding='utf-8')
        return dict(id=identity, provider=provider, version=version,
                    root=str(self.root / provider), file=f'skills/{name or provider}/SKILL.md', origin='project')

    def request(self, scopes, operation='review'):
        return dict(run_id='review-test', project_id='project-fixture', snapshot_id='snapshot-42',
                    operation=operation, scopes=scopes)

    def scope(self, name, languages=(), frameworks=(), topics=()):
        return dict(id=name, paths=[f'{name}/source'], languages=list(languages),
                    frameworks=list(frameworks), topics=list(topics),
                    evidence=[f'Inspected {name}/source and its affected package'],
                    workers={'correctness': ['reviewer:code-auditor']})

    def index(self, inventory):
        return self.api.index_inventory({'schema': 'daodan/skill-catalog/v1', 'entries': []}, inventory)

    def test_kotlin_selection_does_not_read_2500_irrelevant_bodies(self):
        relevant = self.skill('kotlin:idioms', languages=['kotlin'])
        irrelevant = [self.skill(f'other{i}:patterns', languages=['elixir']) for i in range(2500)]
        original = Path.read_bytes
        bodies = []
        def track(path, *args, **kwargs):
            if path.name == 'SKILL.md':
                bodies.append(path)
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_bytes', track):
            catalog = self.index([relevant, *irrelevant])
            selection = self.api.select(catalog, self.request([self.scope('service', ['kotlin'])]))
            self.assertEqual([row['id'] for row in selection['selected']], ['kotlin:idioms'])
            self.assertEqual(bodies, [])
            prepared = self.api.prepare(catalog, self.request([self.scope('service', ['kotlin'])]))
        self.assertEqual(bodies, [Path(relevant['root']) / relevant['file']])
        self.assertEqual(prepared['status'], 'prepared')

    def test_mixed_stack_keeps_knowledge_in_its_affected_scope(self):
        catalog = self.index([self.skill('py:patterns', languages=['python']),
                              self.skill('react:patterns', languages=['typescript'], frameworks=['react']),
                              self.skill('sql:patterns', languages=['sql'])])
        scopes = [self.scope('api', ['python']), self.scope('web', ['typescript'], ['react']),
                  self.scope('migration', ['sql'])]
        selected = self.api.select(catalog, self.request(scopes))['selected']
        self.assertEqual({r['id']: [b['scope_id'] for b in r['bindings']] for r in selected},
                         {'py:patterns': ['api'], 'react:patterns': ['web'], 'sql:patterns': ['migration']})

    def test_new_language_requires_no_reviewer_registration(self):
        catalog = self.index([self.skill('new:patterns', languages=['gleam'])])
        rows = self.api.select(catalog, self.request([self.scope('service', ['gleam'])]))['selected']
        self.assertEqual([r['id'] for r in rows], ['new:patterns'])

    def test_methods_and_wrong_operations_never_become_review_knowledge(self):
        catalog = self.index([self.skill('py:audit', languages=['python'], kind='method'),
                              self.skill('py:scaffold', languages=['python'], operations=['develop']),
                              self.skill('py:knowledge', languages=['python'])])
        self.assertEqual([r['id'] for r in self.api.select(catalog, self.request([self.scope('api', ['python'])]))['selected']],
                         ['py:knowledge'])

    def test_framework_and_topic_constraints_prevent_unrelated_activation(self):
        catalog = self.index([self.skill('react:patterns', languages=['typescript'], frameworks=['react']),
                              self.skill('py:async', languages=['python'], topics=['asyncio'])])
        request = self.request([self.scope('api', ['python']), self.scope('lib', ['typescript'])])
        self.assertEqual(self.api.select(catalog, request)['selected'], [])

    def test_empty_inventory_is_a_coverage_gap(self):
        result = self.api.prepare(self.index([]), self.request([self.scope('api', ['python'])]))
        self.assertTrue(result['gaps'])
        self.assertNotEqual(result['status'], 'complete')
        self.assertFalse(self.api.validate_usage(result, [])['complete'])

    def test_unknown_metadata_is_searchable_but_requires_classification(self):
        row = self.skill('python:patterns', languages=['python'])
        (Path(row['root']) / row['file']).with_name('SKILL.toml').unlink()
        catalog = self.index([row])
        self.assertEqual(self.api.search(catalog, 'python', 'review')[0]['id'], row['id'])
        result = self.api.select(catalog, self.request([self.scope('api', ['python'])]))
        self.assertEqual(result['selected'], [])
        self.assertIn('unclassified', json.dumps(result['gaps']))

    def test_declared_catalog_does_not_prove_installation(self):
        declared = {'schema': 'daodan/skill-catalog/v1', 'entries': [dict(id='kotlin:idioms', provider='kotlin',
                    version='1.0.0', kind='knowledge', languages=['kotlin'], operations=['review'])]}
        self.assertEqual(self.api.index_inventory(declared, [])['entries'], [])

    def test_duplicate_ids_are_rejected_instead_of_overwritten(self):
        row = self.skill('py:patterns', languages=['python'])
        with self.assertRaises(self.api.CatalogError):
            self.index([row, row])

    def test_missing_selected_body_is_a_failed_delivery(self):
        row = self.skill('py:patterns', languages=['python'])
        catalog = self.index([row])
        (Path(row['root']) / row['file']).unlink()
        result = self.api.prepare(catalog, self.request([self.scope('api', ['python'])]))
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['selected'][0]['status'], 'failed')

    def test_changed_body_and_metadata_invalidate_the_selection(self):
        for changed in ('SKILL.md', 'SKILL.toml'):
            with self.subTest(changed=changed):
                row = self.skill(f'py{changed.lower().replace(".", "")}:patterns', languages=['python'])
                prepared = self.api.prepare(self.index([row]), self.request([self.scope('api', ['python'])]))
                path = (Path(row['root']) / row['file']).with_name(changed)
                path.write_text(path.read_text() + '\n# changed\n')
                with self.assertRaises(self.api.CatalogError):
                    self.api.load_skill(prepared, row['id'])

    def test_reference_traversal_is_rejected_and_valid_reference_is_fingerprinted(self):
        row = self.skill('py:patterns', languages=['python'])
        skill = (Path(row['root']) / row['file']).parent
        (skill / 'references').mkdir()
        (skill / 'references/rules.md').write_text('Supplementary knowledge')
        prepared = self.api.prepare(self.index([row]), self.request([self.scope('api', ['python'])]))
        result = self.api.read_reference(prepared, row['id'], 'references/rules.md')
        self.assertEqual(result['content'], 'Supplementary knowledge')
        self.assertEqual(len(result['sha256']), 64)
        for relative in ('../SKILL.md', '/outside.md', 'references/../../SKILL.md', 'scripts/run.py'):
            with self.subTest(relative=relative), self.assertRaises(self.api.CatalogError):
                self.api.read_reference(prepared, row['id'], relative)

    def test_linked_content_is_not_read(self):
        row = self.skill('py:patterns', languages=['python'])
        prepared = self.api.prepare(self.index([row]), self.request([self.scope('api', ['python'])]))
        body = Path(row['root']) / row['file']
        replacement = self.root / 'foreign.md'
        replacement.write_bytes(body.read_bytes())
        body.unlink()
        try:
            body.symlink_to(replacement)
        except OSError:
            self.skipTest('Creating symlinks requires OS privilege')
        with self.assertRaises(self.api.CatalogError):
            self.api.load_skill(prepared, row['id'])

    def test_unread_selected_knowledge_cannot_pass_delivery_accounting(self):
        row = self.skill('py:patterns', languages=['python'])
        prepared = self.api.prepare(self.index([row]), self.request([self.scope('api', ['python'])]))
        self.assertFalse(self.api.validate_usage(prepared, [])['complete'])
        loaded = self.api.load_skill(prepared, row['id'])
        usage = dict(id=row['id'], sha256=loaded['sha256'], status='loaded', scope_id='api',
                     worker='reviewer:code-auditor', selection_sha256=prepared['selection_sha256'],
                     references=[], application='Checked caller and boundary behavior')
        self.assertTrue(self.api.validate_usage(prepared, [usage])['complete'])
        usage['sha256'] = '0' * 64
        self.assertFalse(self.api.validate_usage(prepared, [usage])['complete'])

    def test_request_must_bind_snapshot_and_evidenced_scope(self):
        catalog = self.index([self.skill('py:patterns', languages=['python'])])
        request = self.request([self.scope('api', ['python'])])
        for field in ('snapshot_id', 'run_id', 'project_id'):
            broken = copy.deepcopy(request)
            del broken[field]
            with self.subTest(field=field), self.assertRaises(self.api.CatalogError):
                self.api.prepare(catalog, broken)
        request['scopes'][0]['evidence'] = []
        with self.assertRaises(self.api.CatalogError):
            self.api.select(catalog, request)

    def test_no_arbitrary_top_k_truncates_applicable_knowledge(self):
        catalog = self.index([self.skill(f'py{i}:patterns', languages=['python']) for i in range(30)])
        result = self.api.select(catalog, self.request([self.scope('api', ['python'])]))
        self.assertEqual(len(result['selected']), 30)

    def test_each_assigned_worker_must_deliver_knowledge_usage(self):
        row = self.skill('py:patterns', languages=['python'])
        scope = self.scope('api', ['python'])
        scope['workers']['correctness'].append('reviewer:independent-auditor')
        prepared = self.api.prepare(self.index([row]), self.request([scope]))
        loaded = self.api.load_skill(prepared, row['id'])
        usage = dict(id=row['id'], sha256=loaded['sha256'], status='loaded', scope_id='api',
                     worker='reviewer:code-auditor', selection_sha256=prepared['selection_sha256'],
                     references=[], application='Applied boundary rules')
        self.assertFalse(self.api.validate_usage(prepared, [usage])['complete'])
        second = dict(usage, worker='reviewer:independent-auditor')
        self.assertTrue(self.api.validate_usage(prepared, [usage, second])['complete'])

    def test_usage_from_another_selection_cannot_satisfy_a_delivery(self):
        row = self.skill('py:patterns', languages=['python'])
        prepared = self.api.prepare(self.index([row]), self.request([self.scope('api', ['python'])]))
        usage = dict(id=row['id'], sha256=prepared['selected'][0]['sha256'], status='loaded', scope_id='api',
                     worker='reviewer:code-auditor', selection_sha256='other-selection',
                     references=[], application='Applied boundary rules')
        self.assertFalse(self.api.validate_usage(prepared, [usage])['complete'])

    def test_changed_used_reference_invalidates_delivery(self):
        row = self.skill('py:patterns', languages=['python'])
        skill = (Path(row['root']) / row['file']).parent
        (skill / 'references').mkdir()
        path = skill / 'references/rules.md'
        path.write_text('Initial rules')
        prepared = self.api.prepare(self.index([row]), self.request([self.scope('api', ['python'])]))
        reference = self.api.read_reference(prepared, row['id'], 'references/rules.md')
        usage = dict(id=row['id'], sha256=prepared['selected'][0]['sha256'], status='loaded', scope_id='api',
                     worker='reviewer:code-auditor', selection_sha256=prepared['selection_sha256'],
                     references=[{'file': reference['file'], 'sha256': reference['sha256']}], application='Applied rules')
        self.assertTrue(self.api.validate_usage(prepared, [usage])['complete'])
        path.write_text('Different rules')
        self.assertFalse(self.api.validate_usage(prepared, [usage])['complete'])

    def test_unassigned_selected_knowledge_cannot_be_prepared(self):
        row = self.skill('py:patterns', languages=['python'])
        scope = self.scope('api', ['python'])
        scope.pop('workers')
        result = self.api.prepare(self.index([row]), self.request([scope]))
        self.assertEqual(result['status'], 'failed')

    def test_usage_rejects_missing_or_truncated_selection_even_without_entries(self):
        row = self.skill('py:patterns', languages=['python'])
        prepared = self.api.prepare(self.index([row]), self.request([self.scope('api', ['python'])]))
        truncated = copy.deepcopy(prepared)
        truncated['selected'] = []
        for record in ({'status': 'prepared'}, truncated):
            with self.subTest(record=record), self.assertRaises(self.api.CatalogError):
                self.api.validate_usage(record, [])

    def test_usage_rejects_malformed_sealed_selection(self):
        prepared = self.api.prepare(self.index([]), self.request([self.scope('api', ['python'])]))
        for field, value in (('selected', None), ('gaps', {}), ('snapshot_id', ''), ('status', 'selected')):
            broken = dict(prepared, **{field: value})
            broken['selection_sha256'] = self.api.fingerprint(
                {key: value for key, value in broken.items() if key != 'selection_sha256'})
            with self.subTest(field=field), self.assertRaises(self.api.CatalogError):
                self.api.validate_usage(broken, [])

    def test_partial_dimension_assignment_is_failed_coverage(self):
        row = self.skill('kotlin:idioms', languages=['kotlin'],
                         dimensions=['correctness', 'resource-lifecycle'])
        scope = self.scope('service', ['kotlin'])
        prepared = self.api.prepare(self.index([row]), self.request([scope]))
        self.assertEqual(prepared['status'], 'failed')
        binding = prepared['selected'][0]['bindings'][0]
        self.assertEqual(binding['dimension_workers'],
                         {'correctness': ['reviewer:code-auditor'], 'resource-lifecycle': []})
        self.assertFalse(self.api.validate_usage(prepared, [])['complete'])

    def test_dimension_assignments_preserve_each_delivery_and_allow_one_worker_for_several(self):
        row = self.skill('kotlin:idioms', languages=['kotlin'],
                         dimensions=['correctness', 'resource-lifecycle'])
        catalog = self.index([row])
        for lifecycle_worker in ('reviewer:ownership-auditor', 'reviewer:code-auditor'):
            with self.subTest(lifecycle_worker=lifecycle_worker):
                scope = self.scope('service', ['kotlin'])
                scope['workers']['resource-lifecycle'] = [lifecycle_worker]
                prepared = self.api.prepare(catalog, self.request([scope]))
                self.assertEqual(prepared['status'], 'prepared')
                binding = prepared['selected'][0]['bindings'][0]
                self.assertEqual(binding['dimension_workers'], scope['workers'])
                usage = dict(id=row['id'], sha256=prepared['selected'][0]['sha256'], status='loaded',
                             scope_id='service', worker='reviewer:code-auditor', references=[],
                             selection_sha256=prepared['selection_sha256'], application='Checked assigned risks')
                complete = self.api.validate_usage(prepared, [usage])['complete']
                self.assertEqual(complete, lifecycle_worker == usage['worker'])
                lifecycle_usage = dict(usage, worker=lifecycle_worker)
                self.assertTrue(self.api.validate_usage(prepared, [usage, lifecycle_usage])['complete'])


if __name__ == '__main__':
    unittest.main()
