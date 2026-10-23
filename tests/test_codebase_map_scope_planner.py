"""Scope selection keeps evidence, intervention and validation independent."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'plugins/codebase-map/skills/map-method/scripts'
sys.path.insert(0, str(SCRIPTS))
import snapshot
import source_reader
import retrieval
import scope_planner as scope
import resolve_edges
import semantic_store
from snapshot_store import open_snapshot


FILES = {
    'pkg/__init__.py': '',
    'pkg/core.py': 'def helper(value):\n    return value + 1\n\ndef unrelated():\n    return 99\n',
    'pkg/outer.py': 'from .core import helper\n\ndef run(value):\n    return helper(value)\n',
    'pkg/top.py': 'from .outer import run\n\ndef top(value):\n    return run(value)\n',
    'tests/test_flow.py': 'from pkg.top import top\n\ndef test_flow():\n    assert top(1) == 2\n',
}
TARGET = 'pkg/core.py::helper'


def ids(plan, section):
    return {row['entity_id'] for row in plan[section] if row.get('entity_id')}


class ScopePlannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='map-scope-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        for rel, text in FILES.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf8')
        self.out = self.root / '.codebase-map'
        self.out.mkdir()
        self.base = self.out / 'base.sqlite'
        snapshot.write_snapshot(self.root, self.base)
        self.current = self.out / 'candidate.sqlite'
        self.authority = {'root': str(self.root), 'read_boundary': ['.'], 'write_boundary': ['pkg/core.py']}

    def request(self, change='body', **updates):
        if change == 'body':
            (self.root / 'pkg/core.py').write_text(FILES['pkg/core.py'].replace('+ 1', '+ 2'), encoding='utf8')
        elif change == 'signature':
            (self.root / 'pkg/core.py').write_text('def helper(value, offset=1):\n    return value + offset\n', encoding='utf8')
        elif change == 'removed':
            (self.root / 'pkg/core.py').write_text('def unrelated():\n    return 99\n', encoding='utf8')
        snapshot.write_snapshot(self.root, self.current)
        request = {'schema': 'daodan/context-request/v1', 'task_id': 'task-1', 'intent': 'change',
            'query': '', 'read_boundary': ['.'], 'write_boundary': ['pkg/core.py'],
            'anchors': [{'entity_id': TARGET}], 'base': {'manifest': str(self.base)},
            'candidate': {'manifest': str(self.current)}, 'diff': [],
            'proposed_edits': [{'entity_id': TARGET}],
            'mandatory_requirements': [{'id': 'REQ-1', 'description': 'Understand the current implementation',
                'support': [{'predicate': 'current_source', 'entity_id': TARGET}]}],
            'required_gates': [{'id': 'unit-tests', 'description': 'Exercise the changed behavior'}],
            'budget': {'max_candidates': 100, 'max_edges': 1000, 'max_rounds': 100,
                'max_seconds': 120, 'max_input_tokens': 10000, 'max_output_tokens': 10000},
            'policy_version': 'scope-v1'}
        request.update(updates)
        return request

    def prepare(self, request, **kwargs):
        return scope.prepare_scope(request, authority=self.authority, **kwargs)

    def advance(self, plan, request, **kwargs):
        return scope.advance_scope(plan, request, authority=self.authority, **kwargs)

    def drain(self, plan, request, **kwargs):
        for _ in range(40):
            plan = self.advance(plan, request, max_steps=1000, **kwargs)
            if not plan['frontier'] and plan['active'] is None:
                return plan
            if plan['status'] == 'needs_split':
                return plan
        self.fail('frontier failed to converge')

    def packet(self, path='pkg/core.py'):
        with open_snapshot(self.current) as store:
            return source_reader.read_packet(store, [{'path': path, 'full_file': True}])

    def test_impacted_caller_is_not_automatically_an_edit(self):
        request = self.request('signature')
        plan = self.prepare(request)
        self.assertEqual(ids(plan, 'edit_candidates'), {TARGET})
        self.assertIn('pkg/outer.py::run', ids(plan, 'potential_impact'))
        self.assertNotIn('pkg/top.py::top', ids(plan, 'edit_candidates'))
        self.assertFalse(plan['write_authorized'])

    def test_body_only_callers_retain_validation_without_edits(self):
        plan = self.prepare(self.request())
        impacted = ids(plan, 'validation_obligations')
        self.assertTrue({'pkg/outer.py::run', 'pkg/top.py::top', 'tests/test_flow.py::test_flow'} <= impacted)
        self.assertEqual(ids(plan, 'edit_candidates'), {TARGET})
        self.assertEqual({x['id'] for x in plan['validation_obligations'] if x['kind'] == 'gate'}, {'unit-tests'})

    def test_obligations_precede_zero_work_budget(self):
        request = self.request()
        request['budget'].update(max_candidates=0, max_edges=0)
        plan = self.advance(self.prepare(request), request)
        self.assertEqual(plan['status'], 'needs_split')
        self.assertIn('REQ-1', {r['id'] for r in plan['validation_obligations']})
        self.assertIn('pkg/outer.py::run', ids(plan, 'validation_obligations'))
        self.assertTrue(plan['deferred'])
        self.assertEqual(plan['usage']['candidates'], 0)

    def test_outside_write_site_stays_an_obligation(self):
        request = self.request()
        request['proposed_edits'].append({'entity_id': 'pkg/outer.py::run'})
        plan = self.prepare(request)
        self.assertEqual(ids(plan, 'edit_candidates'), {TARGET})
        self.assertIn('pkg/outer.py::run', ids(plan, 'outside_boundary'))
        self.assertIn('pkg/outer.py::run', ids(plan, 'validation_obligations'))

    def test_removed_callee_retains_base_edge_witness(self):
        request = self.request('removed', anchors=[], proposed_edits=[], mandatory_requirements=[])
        plan = self.prepare(request)
        caller = next(x for x in plan['potential_impact'] if x.get('entity_id') == 'pkg/outer.py::run')
        self.assertIn('base', json.dumps(caller['provenance']))
        self.assertIn(TARGET, {x['symbol_id'] for x in plan['comparison']['changed']})

    def test_similarity_cannot_satisfy_hard_support(self):
        request = self.request()
        plan = self.advance(self.prepare(request), request,
            evidence={'leads': [{'entity_id': TARGET, 'kind': 'semantic_card', 'text': 'relevant body'}]})
        req = next(x for x in plan['validation_obligations'] if x['id'] == 'REQ-1')
        self.assertEqual(req['support_status'], 'missing')
        self.assertNotEqual(plan['status'], 'ready_for_attempt')
        plan = self.advance(plan, request, evidence={'source_packets': [self.packet()]})
        req = next(x for x in plan['validation_obligations'] if x['id'] == 'REQ-1')
        self.assertEqual(req['support_status'], 'source_provided')
        self.assertEqual(req['status'], 'open')
        self.assertFalse(plan['task_complete'])
        self.assertFalse(plan['validation_complete'])

    def test_source_evidence_is_verified_and_never_closes_gate(self):
        request = self.request()
        plan = self.prepare(request)
        fake = self.packet()
        fake['files'][0]['blocks'][0]['source'] = '1: fake\n'
        with self.assertRaisesRegex(ValueError, 'source evidence'):
            self.advance(plan, request, evidence={'source_packets': [fake]})
        plan = self.drain(self.advance(plan, request, evidence={'source_packets': [self.packet()]}), request)
        self.assertEqual(plan['status'], 'ready_for_attempt')
        self.assertTrue(all(x['status'] == 'open' for x in plan['validation_obligations']))
        self.assertEqual(plan['stop_calibration'], 'uncalibrated')

    def test_request_cannot_widen_independent_authority(self):
        request = self.request(write_boundary=['.'])
        with self.assertRaisesRegex(ValueError, 'boundary'):
            self.prepare(request)
        request['write_boundary'] = ['pkg/../core.py']
        with self.assertRaises(ValueError):
            self.prepare(request)

    def test_partial_read_boundary_does_not_read_other_source(self):
        request = self.request(read_boundary=['pkg/core.py'])
        index = self.out / 'retrieval.sqlite'
        retrieval.refresh_index(self.current, index)
        request['query'] = 'helper'
        original = source_reader.read_packet
        seen = []
        def observe(store, requests):
            seen.extend(item['path'] for item in requests)
            return original(store, requests)
        with mock.patch.object(source_reader, 'read_packet', side_effect=observe):
            plan = self.prepare(request, indexes={'retrieval': str(index)})
            plan = self.drain(plan, request, indexes={'retrieval': str(index)})
        self.assertEqual(set(seen), {'pkg/core.py'})
        self.assertIn('retrieval_boundary', {x['kind'] for x in plan['unresolved']})
        self.assertIn('pkg/outer.py::run', ids(plan, 'outside_boundary'))

    def test_italian_query_without_anchor_stays_exploratory_when_unmatched(self):
        request = self.request(None, base=None, intent='bug', query='fatture scadute senza addebito',
            anchors=[], proposed_edits=[], mandatory_requirements=[])
        index = self.out / 'retrieval.sqlite'
        retrieval.refresh_index(self.current, index)
        plan = self.drain(self.prepare(request, indexes={'retrieval': str(index)}), request,
            indexes={'retrieval': str(index)})
        self.assertEqual(plan['status'], 'needs_localization')
        self.assertFalse(plan['task_complete'])
        self.assertTrue(plan['coverage']['provisional'])

    def test_hub_checkpoint_and_json_resume_equal_continuous_work(self):
        for n in range(12):
            (self.root / f'pkg/caller{n:02}.py').write_text(
                f'from .core import helper\n\ndef call{n}(x):\n    return helper(x)\n', encoding='utf8')
        request = self.request()
        start = self.prepare(request)
        first = self.advance(start, request, max_steps=2)
        self.assertTrue(first['frontier'] or first['active'])
        self.assertLessEqual(first['usage']['edges'], 2)
        roundtrip = json.loads(json.dumps(first))
        left, right = self.drain(first, request), self.drain(roundtrip, request)
        for key in ('analysis', 'potential_impact', 'validation_obligations', 'frontier', 'active', 'visited', 'actions'):
            self.assertEqual(left[key], right[key], key)
        expected = {f'pkg/caller{n:02}.py::call{n}' for n in range(12)}
        self.assertTrue(expected <= ids(left, 'analysis'))
        self.assertEqual(len(left['visited']), len(set(left['visited'])))

    def test_each_cumulative_budget_survives_resume(self):
        for field, limit, expected in [('max_candidates', 1, 'candidates'), ('max_edges', 1, 'edges'), ('max_rounds', 1, 'rounds')]:
            with self.subTest(field=field):
                request = self.request()
                request['budget'][field] = limit
                plan = self.advance(self.prepare(request), request, max_steps=2)
                plan = self.advance(json.loads(json.dumps(plan)), request, max_steps=100)
                self.assertEqual(plan['usage'][expected], limit)
                self.assertEqual(plan['status'], 'needs_split')
        request = self.request()
        request['budget']['max_seconds'] = 0
        self.assertEqual(self.advance(self.prepare(request), request)['status'], 'needs_split')

    def test_input_and_output_tokens_count_independently_and_once(self):
        request = self.request()
        request['budget']['max_input_tokens'] = 10
        request['budget']['max_output_tokens'] = 5
        observation = {'id': 'call-1', 'input_tokens': 10, 'output_tokens': 2, 'measurement': 'actual'}
        plan = self.advance(self.prepare(request), request, evidence={'usage': [observation]})
        plan = self.advance(plan, request, evidence={'usage': [observation]})
        self.assertEqual(plan['usage']['input_tokens'], 10)
        self.assertEqual(plan['usage']['output_tokens'], 2)
        self.assertEqual(plan['status'], 'needs_split')
        altered = dict(observation, output_tokens=3)
        with self.assertRaisesRegex(ValueError, 'usage'):
            self.advance(plan, request, evidence={'usage': [altered]})

    def test_unproductive_gap_action_is_not_retried(self):
        request = self.request()
        plan = self.drain(self.prepare(request), request)
        action = next(a for a in plan['actions'] if a['kind'] == 'read_source' and a['status'] == 'available')
        evidence = {'attempted_actions': [action['id']]}
        plan = self.advance(plan, request, evidence=evidence)
        plan = self.advance(plan, request, evidence=evidence)
        same = [a for a in plan['actions'] if a['id'] == action['id']]
        self.assertEqual(len(same), 1)
        self.assertEqual(same[0]['status'], 'exhausted')
        self.assertEqual(plan['status'], 'needs_localization')

    def test_stale_request_snapshot_source_index_and_plan_are_rejected(self):
        request = self.request()
        plan = self.prepare(request)
        changed = copy.deepcopy(request)
        changed['query'] = 'different'
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.advance(plan, changed)
        tampered = copy.deepcopy(plan)
        tampered['validation_obligations'] = []
        with self.assertRaisesRegex(ValueError, 'cursor'):
            self.advance(tampered, request)
        (self.root / 'pkg/core.py').write_text(FILES['pkg/core.py'], encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'stale|changed|refresh'):
            self.advance(plan, request)

    def test_new_engine_store_invalidates_negative_binding(self):
        request = self.request()
        plan = self.prepare(request)
        engine_path = Path(plan['indices']['engine']['path'])
        engine_path.write_bytes(b'new-store')
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.advance(plan, request)

    def test_output_is_exclusive_confined_and_manifest_unchanged(self):
        request = self.request()
        plan = self.prepare(request)
        before = self.current.read_bytes()
        path = self.out / 'scope-1.json'
        ref = scope.persist_scope(plan, path, authority=self.authority)
        self.assertEqual(json.loads(path.read_text())['input_digest'], plan['input_digest'])
        self.assertEqual(ref['path'], str(path))
        with self.assertRaises(ValueError):
            scope.persist_scope(plan, path, authority=self.authority)
        with self.assertRaises(ValueError):
            scope.persist_scope(plan, self.current, authority=self.authority)
        self.assertEqual(self.current.read_bytes(), before)

    def test_canonical_impact_cap_keeps_every_component_as_an_obligation(self):
        for n in range(6):
            (self.root / f'pkg/c{n}.py').write_text(
                f'from .core import helper\n\ndef invoke{n}(x):\n    return helper(x)\n', encoding='utf8')
        snapshot.write_snapshot(self.root, self.base)
        request = self.request()
        with mock.patch.object(semantic_store, 'MAX_STALE_CALLERS', 2):
            plan = self.prepare(request)
        expected = {f'pkg/c{n}.py::invoke{n}' for n in range(6)}
        self.assertTrue(expected <= ids(plan, 'validation_obligations'))
        self.assertTrue(expected <= ids(plan, 'analysis'))
        self.assertEqual(plan['status'], 'needs_split')

    def test_cycle_has_no_fixed_hop_completion_or_duplicate_visits(self):
        (self.root / 'pkg/cycle.py').write_text(
            'def first(x):\n    return second(x)\n\ndef second(x):\n    return third(x)\n'
            '\ndef third(x):\n    return first(x)\n', encoding='utf8')
        request = self.request(None, base=None, anchors=[{'entity_id': 'pkg/cycle.py::first'}],
            proposed_edits=[], mandatory_requirements=[])
        plan = self.drain(self.prepare(request), request)
        self.assertTrue({'pkg/cycle.py::first', 'pkg/cycle.py::second', 'pkg/cycle.py::third'} <= ids(plan, 'analysis'))
        self.assertEqual(len(plan['visited']), 3)
        self.assertFalse(plan['validation_complete'])

    def test_current_source_handles_physical_form_feed_lines(self):
        (self.root / 'pkg/core.py').write_text('def helper(value):\n    text = "first\fsecond"\n    return value\n', encoding='utf8')
        request = self.request(None, base=None)
        plan = self.advance(self.prepare(request), request, evidence={'source_packets': [self.packet()]})
        req = next(r for r in plan['validation_obligations'] if r['id'] == 'REQ-1')
        self.assertEqual(req['support_status'], 'source_provided')

    def test_verified_empty_engine_is_distinct_from_missing_and_keeps_static_gaps(self):
        for path in ('pkg/outer.py', 'pkg/top.py', 'tests/test_flow.py'):
            (self.root / path).write_text('', encoding='utf8')
        request = self.request(None, base=None)
        missing = self.prepare(request)
        self.assertFalse(missing['resolver_profile']['profile']['engine_available'])
        class EmptyEngine:
            name = 'empty-test-engine'
            def probe(self): return True, ''
            def identity(self): return 'empty@1'
            def definitions(self, *args): raise AssertionError('no calls were inventoried')
        resolve_edges.resolve_edges(self.current, engine=EmptyEngine(), limit=None, stride=1)
        empty = self.prepare(request)
        self.assertTrue(empty['resolver_profile']['profile']['engine_available'])
        self.assertEqual(empty['coverage']['engine']['status'], 'completed_empty')
        self.assertTrue(empty['unresolved'])
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.advance(missing, request)

    def test_index_generation_and_allowed_new_file_invalidate_resume(self):
        request = self.request()
        index = self.out / 'retrieval.sqlite'
        retrieval.refresh_index(self.current, index)
        plan = self.prepare(request, indexes={'retrieval': str(index)})
        with index.open('ab') as handle:
            handle.write(b'changed-generation')
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.advance(plan, request)
        plan = self.prepare(request)
        (self.root / 'new.py').write_text('def added():\n    return 1\n', encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.advance(plan, request)

    def test_explicit_localization_can_refine_search_without_granting_edits(self):
        request = self.request(None, base=None, query='natural language question', anchors=[],
            proposed_edits=[], mandatory_requirements=[])
        plan = self.prepare(request)
        self.assertEqual(plan['status'], 'needs_localization')
        plan = self.advance(plan, request, evidence={'anchors': [{'entity_id': TARGET}]})
        plan = self.drain(plan, request)
        self.assertEqual(plan['status'], 'ready_for_attempt')
        self.assertEqual(plan['edit_candidates'], [])

    def test_foreign_retrieval_is_rejected_before_foreign_source_is_read(self):
        other = self.root / '.foreign-project'
        other.mkdir()
        (other / 'foreign.py').write_text('def external():\n    return 7\n', encoding='utf8')
        manifest = other / '.codebase-map/map.sqlite'
        snapshot.write_snapshot(other, manifest)
        index = manifest.with_name('retrieval.sqlite')
        retrieval.refresh_index(manifest, index)
        request = self.request(query='helper')
        original = source_reader.read_packet
        seen = []
        def observe(store, requests):
            seen.append(Path(store.get('root')).resolve())
            return original(store, requests)
        with mock.patch.object(source_reader, 'read_packet', side_effect=observe):
            with self.assertRaisesRegex(ValueError, 'candidate'):
                self.prepare(request, indexes={'retrieval': str(index)})
        self.assertNotIn(other.resolve(), seen)

    def test_ambiguous_proposal_cannot_overlap_authorized_edit_and_outside_boundary(self):
        (self.root / 'other.py').write_text('def helper(value):\n    return value\n', encoding='utf8')
        request = self.request(proposed_edits=[{'symbol': 'helper'}, {'entity_id': TARGET}])
        plan = self.prepare(request)
        self.assertEqual(ids(plan, 'edit_candidates'), {TARGET})
        self.assertFalse(ids(plan, 'edit_candidates') & ids(plan, 'outside_boundary'))

    def test_unrelated_diff_cannot_localize_a_bug_query(self):
        request = self.request(intent='bug', query='fatture scadute senza addebito',
            anchors=[], proposed_edits=[], mandatory_requirements=[])
        plan = self.drain(self.prepare(request), request)
        self.assertEqual(plan['status'], 'needs_localization')

    def test_uncertain_structure_cannot_bypass_canonical_full_file_fallback(self):
        (self.root / 'pkg/core.py').write_text(
            'def helper(value):\n    def nested():\n        return value\n    return nested()\n'
            '\ndef unrelated():\n    return 99\n', encoding='utf8')
        request = self.request(None, base=None)
        packet = self.packet()
        block = packet['files'][0]['blocks'][0]
        block['end'] = 4
        block['source'] = ''.join(block['source'].splitlines(keepends=True)[:4])
        with self.assertRaisesRegex(ValueError, 'source evidence.*fallback'):
            self.advance(self.prepare(request), request, evidence={'source_packets': [packet]})

    def test_mandatory_exact_target_precedes_lexically_earlier_retrieval_lead(self):
        (self.root / 'aaa.py').write_text('def irrelevant():\n    invoice = 7\n    return invoice\n', encoding='utf8')
        request = self.request(None, base=None, query='invoice')
        request['budget']['max_candidates'] = 1
        index = self.out / 'retrieval.sqlite'
        retrieval.refresh_index(self.current, index)
        plan = self.prepare(request, indexes={'retrieval': str(index)})
        plan = self.advance(plan, request, max_steps=1)
        self.assertEqual(plan['visited'], [TARGET])
        self.assertIn('aaa.py::irrelevant', plan['frontier'])

    def test_outside_only_anchor_never_localizes_an_empty_analysis(self):
        request = self.request(None, base=None, intent='bug', read_boundary=['pkg/core.py'],
            anchors=[{'entity_id': 'pkg/outer.py::run'}], proposed_edits=[], mandatory_requirements=[])
        plan = self.prepare(request)
        self.assertEqual(plan['analysis'], [])
        self.assertIn('pkg/outer.py::run', ids(plan, 'outside_boundary'))
        self.assertEqual(plan['status'], 'needs_localization')
        self.assertFalse(plan['localized'])
        self.assertTrue(any(a['kind'] == 'localize' for a in plan['actions']))

    def test_retrieval_seed_order_preserves_the_producers_relevance_ranking(self):
        (self.root / 'aaa.py').write_text('def irrelevant():\n    invoice = 7\n    return invoice\n', encoding='utf8')
        (self.root / 'zzz.py').write_text('def invoice_total(value):\n    return value\n', encoding='utf8')
        request = self.request(None, base=None, intent='bug', query='invoice', anchors=[],
            proposed_edits=[], mandatory_requirements=[])
        request['budget']['max_candidates'] = 1
        index = self.out / 'retrieval.sqlite'
        retrieval.refresh_index(self.current, index)
        ranked = retrieval.search(index, 'invoice', anchors=[], limit=10)
        self.assertEqual(ranked['results'][0]['entity_id'], 'zzz.py::invoice_total')
        plan = self.advance(self.prepare(request, indexes={'retrieval': str(index)}), request, max_steps=1)
        self.assertEqual(plan['visited'], ['zzz.py::invoice_total'])

    def test_shared_source_gap_offers_one_action_and_exhausts_equivalent_retries(self):
        request = self.request()
        request['mandatory_requirements'].append({'id': 'REQ-2', 'support': [
            {'predicate': 'current_source', 'entity_id': TARGET}]})
        plan = self.prepare(request)
        actions = [a for a in plan['actions'] if a['kind'] == 'read_source' and a['entity_id'] == TARGET]
        self.assertEqual(len(actions), 1)
        self.assertEqual(set(actions[0]['gaps']), {'REQ-1', 'REQ-2'})
        plan = self.advance(plan, request, evidence={'attempted_actions': [actions[0]['id']]})
        self.assertFalse(any(a['kind'] == 'read_source' and a['status'] == 'available' for a in plan['actions']))
        plan = self.advance(plan, request, evidence={'source_packets': [self.packet()]})
        self.assertTrue(all(r['support_status'] == 'source_provided' for r in plan['validation_obligations']
            if r['kind'] == 'requirement'))


if __name__ == '__main__':
    unittest.main()
