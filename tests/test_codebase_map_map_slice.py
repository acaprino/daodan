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
