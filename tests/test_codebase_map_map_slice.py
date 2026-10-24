"""Public I1 projection: source-bound evidence never becomes a work DAG."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'plugins/codebase-map/skills/map-method/scripts'))
import context_packet
import scope_planner
import snapshot
try:
    import map_slice
except ModuleNotFoundError:
    map_slice = None


class MapSliceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(map_slice, 'The public I1 provider is not implemented')
        temporary = tempfile.TemporaryDirectory(prefix='map-slice-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / 'service.py').write_bytes(b'def calculate(value):\n    return value + 1\n')
        (self.root / 'client.py').write_bytes(b'from service import calculate\n\ndef run(value):\n    return calculate(value)\n')
        out = self.root / '.codebase-map/run-one'
        out.mkdir(parents=True)
        self.manifest = out / 'snapshot.sqlite'
        snapshot.write_snapshot(self.root, self.manifest)
        self.authority = dict(root=str(self.root), read_boundary=['.'], write_boundary=['service.py'])
        self.request = dict(schema='daodan/context-request/v1', task_id='T1', intent='bug', query='',
            read_boundary=['.'], write_boundary=['service.py'],
            anchors=[{'entity_id': 'service.py::calculate'}, {'entity_id': 'client.py::run'}],
            base=None, candidate={'manifest': str(self.manifest)}, diff=[],
            proposed_edits=[{'entity_id': 'service.py::calculate'}],
            mandatory_requirements=[{'id': 'R1', 'support': []}], required_gates=[{'id': 'tests'}],
            policy_version='scope-v1', budget=dict(max_candidates=100, max_edges=100,
                max_rounds=10, max_seconds=120, max_input_tokens=100000, max_output_tokens=100000))
        self.plan = scope_planner.prepare_scope(self.request, authority=self.authority)

    def project(self):
        return map_slice.project_slice(self.plan, self.request, authority=self.authority)

    def test_real_call_is_cited_between_disjoint_file_components(self):
        result = self.project()
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['snapshot']['freshness'], 'fresh')
        self.assertEqual({c['id']: c['paths'] for c in result['components']},
            {'file:client.py': ['client.py'], 'file:service.py': ['service.py']})
        calls = [e for e in result['edges'] if e['from'] == 'file:client.py' and e['to'] == 'file:service.py']
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['kind'], 'call')
        self.assertEqual(calls[0]['evidence']['file'], 'client.py')
        self.assertTrue(calls[0]['evidence']['reference_id'])
        self.assertTrue(result['gaps'])
        self.assertNotIn('precedences', result)
        self.assertEqual({o['id'] for o in result['validation_obligations']}, {'R1', 'tests'})

    def test_public_I1_envelope_is_bound_to_its_request(self):
        result = self.project()
        expected = hashlib.sha256(json.dumps(self.request, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        self.assertEqual(result['schema'], 'daodan/map-slice/v1')
        self.assertEqual(result['input_digest'], expected)
        self.assertTrue(result['implementation']['name'])
        self.assertTrue(result['implementation']['version'])
        self.assertTrue(result['snapshot']['run_id'])
        self.assertTrue(result['snapshot']['digest'])
        self.request['query'] = 'a different question'
        with self.assertRaises(ValueError):
            self.project()

    def test_intervention_sites_do_not_expand_the_read_or_write_boundary(self):
        self.authority.update(read_boundary=['service.py'], write_boundary=[])
        self.request.update(read_boundary=['service.py'], write_boundary=[])
        self.plan = scope_planner.prepare_scope(self.request, authority=self.authority)
        result = self.project()
        self.assertEqual([c['paths'] for c in result['components']], [['service.py']])
        self.assertEqual(result['edit_candidates'], [])
        self.assertTrue(result['outside_boundary'])
        self.assertFalse(result['write_authorized'])

    def test_no_localized_component_produces_an_explicit_abstention(self):
        self.request.update(anchors=[], proposed_edits=[])
        self.plan = scope_planner.prepare_scope(self.request, authority=self.authority)
        result = self.project()
        self.assertEqual(result['status'], 'abstain')
        self.assertEqual(result['components'], [])
        self.assertEqual(result['edges'], [])
        self.assertTrue(result['gaps'])

    def test_changed_source_is_rejected_before_freshness_is_claimed(self):
        (self.root / 'service.py').write_bytes(b'def calculate(value):\n    return 7\n')
        with self.assertRaises(ValueError):
            self.project()

    def test_modified_checkpoint_or_new_engine_store_is_rejected(self):
        self.plan['analysis'].clear()
        with self.assertRaises(ValueError):
            self.project()
        self.plan = scope_planner.prepare_scope(self.request, authority=self.authority)
        Path(self.plan['index_paths']['engine']).write_bytes(b'changed after planning')
        with self.assertRaises(ValueError):
            self.project()

    def test_projection_limit_keeps_priority_order_and_names_omissions(self):
        original = map_slice.PROJECTION_LIMIT
        map_slice.PROJECTION_LIMIT = 1
        self.addCleanup(setattr, map_slice, 'PROJECTION_LIMIT', original)
        result = self.project()
        sites = {row['entity_id'] for row in self.plan['edit_candidates']}
        selected = sorted({row['entity_id'] for row in self.plan['analysis']},
                          key=lambda entity: (entity not in sites, self.plan['priorities'].get(entity, [9, 0]), entity))
        kept = [entity for component in result['components'] for entity in component['entities']]
        limits = [gap for gap in result['gaps'] if gap['kind'] == 'projection_limit']
        self.assertEqual(kept, selected[:1])
        self.assertEqual(limits[0]['omitted_entities'], selected[1:])
        self.assertEqual(limits[0]['entities'], len(selected) - 1)
        self.assertEqual(result['status'], 'ok')

    def test_proposed_edit_site_survives_the_entity_cap_before_alphabetical_peers(self):
        original = map_slice.PROJECTION_LIMIT
        map_slice.PROJECTION_LIMIT = 1
        self.addCleanup(setattr, map_slice, 'PROJECTION_LIMIT', original)
        result = self.project()
        kept = [entity for component in result['components'] for entity in component['entities']]
        limits = [gap for gap in result['gaps'] if gap['kind'] == 'projection_limit']
        self.assertEqual(kept, ['service.py::calculate'])
        self.assertIn('client.py::run', limits[0]['omitted_entities'])

    def test_repeated_calls_on_one_file_pair_do_not_starve_other_relations(self):
        root = self.root / 'many'
        root.mkdir()
        (root / 'b.py').write_bytes(b'def target():\n    return 1\n')
        (root / 'd.py').write_bytes(b'def other():\n    return 2\n')
        (root / 'a.py').write_bytes(b'from b import target\n\ndef one():\n    return target()\n\n'
                                     b'def two():\n    return target()\n\ndef three():\n    return target()\n')
        (root / 'c.py').write_bytes(b'from d import other\n\ndef run():\n    return other()\n')
        out = root / '.codebase-map/run'
        out.mkdir(parents=True)
        manifest = out / 'snapshot.sqlite'
        snapshot.write_snapshot(root, manifest)
        authority = dict(root=str(root), read_boundary=['.'], write_boundary=[])
        request = dict(self.request, anchors=[{'entity_id': e} for e in (
            'a.py::one', 'a.py::two', 'a.py::three', 'b.py::target', 'c.py::run', 'd.py::other')],
            proposed_edits=[], write_boundary=[], candidate={'manifest': str(manifest)})
        plan = scope_planner.prepare_scope(request, authority=authority)
        original = map_slice.EDGE_LIMIT
        map_slice.EDGE_LIMIT = 2
        self.addCleanup(setattr, map_slice, 'EDGE_LIMIT', original)
        result = map_slice.project_slice(plan, request, authority=authority)
        self.assertEqual({(e['from'], e['to']) for e in result['edges']},
                         {('file:a.py', 'file:b.py'), ('file:c.py', 'file:d.py')})
        limits = [gap for gap in result['gaps'] if gap['kind'] == 'projection_limit']
        self.assertEqual(limits[0]['edges'], 2)
        self.assertEqual(limits[0]['edge_pairs'], 0)

    def test_shared_context_operation_publishes_a_digest_bound_I1_artifact(self):
        recipient = dict(id='test', available_tokens=100000, reserve_tokens=0,
                         max_chars=100000, max_evaluations=300)
        result = context_packet.create_context(self.manifest, self.request, recipient,
            authority=self.authority, out=self.manifest.parent / 'context')
        path = Path(result['map_slice_path'])
        self.assertTrue(path.is_relative_to(self.manifest.parent))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), result['map_slice_sha256'])
        slice_ = json.loads(path.read_bytes())
        packet = json.loads(Path(result['path']).read_bytes())
        self.assertEqual(slice_['snapshot']['digest'], packet['candidate']['logical_digest'])
        self.assertEqual(slice_['plan_digest'], packet['plan_digest'])


if __name__ == '__main__':
    unittest.main()
