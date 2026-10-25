"""Minimum evidence core: anchors are mandatory, retrieval leads never block a packet.

Contract: docs/superpowers/specs/2026-10-25-context-packet-redesign.md.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'plugins/codebase-map/skills/map-method/scripts'
sys.path.insert(0, str(SCRIPTS))
import context_packet as packets
import map_slice
import retrieval
import scope_planner as scope
import snapshot
from snapshot_store import open_snapshot


LEAD = '''def offset_value_{i}(value):
    """Offset the value by a fixed amount, variant {i}."""
    total = value
    total = total + {i}
    total = total * 1
    total = total - 0
    if total < 0:
        total = -total
    total = total + 0
    total = total * 1
    return total

'''


def recipient(max_chars, **extra):
    return dict(id='core-test', tokenizer_id='test-characters', available_tokens=10 ** 7,
                reserve_tokens=0, max_chars=max_chars, prefix='', suffix='', max_evaluations=4000, **extra)


class MinimumCoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='minimum-core-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / 'core.py').write_bytes(
            b'OFFSET = 1\n\ndef helper(value):\n    return value + OFFSET\n\ndef run(value):\n    return helper(value)\n')
        (self.root / 'leads.py').write_text('LEAD_HEADER = 1\n\n' + ''.join(LEAD.format(i=i) for i in range(30)),
                                            encoding='utf8')
        out = self.root / '.codebase-map'
        out.mkdir()
        self.manifest = out / 'snapshot.sqlite'
        snapshot.write_snapshot(self.root, self.manifest)
        self.index = out / 'retrieval.sqlite'
        retrieval.refresh_index(self.manifest, self.index)
        self.indexes = {'retrieval': str(self.index)}
        self.authority = {'root': str(self.root), 'read_boundary': ['.'], 'write_boundary': ['core.py']}

    def request(self, *, intent='analysis', query='offset the value', anchors=(), requirements=()):
        return {'schema': 'daodan/context-request/v1', 'task_id': 'core-task', 'intent': intent,
                'query': query, 'read_boundary': ['.'], 'write_boundary': ['core.py'],
                'anchors': [{'entity_id': a} for a in anchors], 'base': None,
                'candidate': {'manifest': str(self.manifest)}, 'diff': [], 'proposed_edits': [],
                'mandatory_requirements': list(requirements), 'required_gates': [{'id': 'tests'}],
                'budget': {'max_candidates': 200, 'max_edges': 2000, 'max_rounds': 100, 'max_seconds': 120,
                           'max_input_tokens': 10 ** 9, 'max_output_tokens': 10 ** 9},
                'policy_version': 'scope-v1'}

    def plan(self, request, evidence=None):
        plan = scope.prepare_scope(request, authority=self.authority, indexes=self.indexes)
        return scope.advance_scope(plan, request, authority=self.authority, indexes=self.indexes,
                                   evidence=evidence, max_steps=100)

    def packet(self, plan, request, max_chars, **extra):
        return packets.build_packet(plan, request, authority=self.authority, recipient=recipient(max_chars, **extra),
                                    indexes=self.indexes, token_counter=len)

    def detail(self, plan, entity):
        return next(r['required_detail'] for r in plan['analysis'] if r['entity_id'] == entity)

    def test_retrieval_leads_are_not_mandatory_source(self):
        request = self.request()
        plan = self.plan(request)
        leads = [r for r in plan['analysis'] if 'retrieval lead' in r['reason']]
        self.assertGreater(len(leads), 10)
        self.assertTrue(all(r['required_detail'] == 'lead' for r in leads))
        result = self.packet(plan, request, 10 ** 6)
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['status_reason'], 'not_localized')
        self.assertTrue(any(b['kind'] == 'source' for b in result['blocks']))

    def test_lead_bodies_omit_file_context_that_core_bodies_keep(self):
        request = self.request(anchors=['core.py::helper'])
        plan = self.plan(request)

        def pieces(entity, core):
            with open_snapshot(self.manifest) as store:
                rows, added = packets._bundle(plan, request, store, {'engine': None}, entity, 0, {},
                                              core=core, impact=False, gaps=[])
            return [p['payload']['block'] for p in added.values()], rows

        lead, rows = pieces('leads.py::offset_value_0', False)
        self.assertEqual({b['reason'] for b in lead}, {'selection'})
        self.assertNotIn('LEAD_HEADER', ''.join(b['source'] for b in lead))
        self.assertNotIn('signature', {r['representation'] for r in rows})
        core, rows = pieces('leads.py::offset_value_0', True)
        self.assertEqual({b['reason'] for b in core}, {'context-and-selection'})
        self.assertIn('LEAD_HEADER = 1', ''.join(b['source'] for b in core))
        self.assertIn('signature', {r['representation'] for r in rows})
        module, _ = pieces('leads.py::@file', False)
        self.assertIn('LEAD_HEADER = 1', ''.join(b['source'] for b in module))
        self.assertNotIn('return total', ''.join(b['source'] for b in module))

    def test_many_irrelevant_leads_do_not_block_the_anchor_core(self):
        request = self.request(anchors=['core.py::helper'])
        plan = self.plan(request)
        result = self.packet(plan, request, 9000)
        self.assertEqual(result['status'], 'ready', result.get('status_reason'))
        self.assertIn('return value + OFFSET', result['input'])
        self.assertLessEqual(len(result['input']), 9000)

    def test_exact_query_match_is_mandatory_like_an_anchor(self):
        request = self.request(query='helper')
        plan = self.plan(request)
        self.assertTrue(plan['localized'])
        self.assertEqual(self.detail(plan, 'core.py::helper'), 'source')
        result = self.packet(plan, request, 10 ** 6)
        self.assertEqual(result['status'], 'ready')
        self.assertIn('return value + OFFSET', result['input'])

    def test_a_lead_never_weakens_a_later_anchor(self):
        request = self.request(query='', anchors=['core.py::helper'])
        plan = self.plan(request, evidence={'leads': [{'entity_id': 'core.py::run'}],
                                            'anchors': [{'entity_id': 'core.py::run'}]})
        self.assertEqual(self.detail(plan, 'core.py::run'), 'source')

    def test_snapshot_change_detail_follows_the_intent(self):
        for intent, expected in (('change', 'source'), ('analysis', 'lead')):
            plan = {'intent': intent, 'entities': {'core.py::run': {'anchor': {'file': 'core.py'}}},
                    'boundaries': {'read_boundary': ['.']}, 'priorities': {}, 'analysis': [],
                    'visited': [], 'frontier': [], 'active': None, 'unresolved': []}
            scope._candidate(plan, 'core.py::run', 'snapshot diff', {}, priority=1,
                             detail=scope._diff_detail(intent))
            self.assertEqual(plan['analysis'][0]['required_detail'], expected, intent)

    def test_localized_plan_without_mandatory_core_is_never_ready(self):
        request = self.request(query='', anchors=['core.py::helper'])
        plan = self.plan(request)
        for row in plan['analysis']:
            row['required_detail'] = 'lead'
        plan['cursor']['state_digest'] = retrieval._digest({k: v for k, v in plan.items() if k != 'cursor'})
        result = self.packet(plan, request, 10 ** 6)
        self.assertNotEqual(result['status'], 'ready')
        self.assertEqual(result['status_reason'], 'empty_core')

    def test_overflow_is_core_too_large_not_missing_support(self):
        request = self.request(anchors=['core.py::helper'])
        result = self.packet(self.plan(request), request, 50)
        self.assertEqual(result['status'], 'needs_split')
        self.assertEqual(result['status_reason'], 'core_too_large')
        self.assertEqual(result['missing_support'], [])

    def test_missing_support_names_only_the_unsupported_predicate(self):
        request = self.request(anchors=['core.py::helper'], requirements=[
            {'id': 'behavior', 'support': [{'predicate': 'tests_passed', 'entity_id': 'core.py::helper'}]}])
        result = self.packet(self.plan(request), request, 10 ** 6)
        self.assertEqual(result['status'], 'needs_split')
        self.assertEqual(result['status_reason'], 'missing_support')
        self.assertEqual(result['missing_support'], ['tests_passed:core.py::helper'])

    def test_variant_limit_drops_whole_lead_bundles_and_keeps_core_prerequisites(self):
        request = self.request(anchors=['core.py::helper'])
        plan = self.plan(request)
        with mock.patch.object(packets, 'VARIANT_LIMIT', 12, create=True):
            result = self.packet(plan, request, 10 ** 6)
        self.assertEqual(result['status'], 'ready', result.get('status_reason'))
        self.assertIn('return value + OFFSET', result['input'])
        gap = next(g for g in result['gaps'] if g['kind'] == 'variant_limit')
        self.assertTrue(gap['omitted_entities'])
        self.assertNotIn('core.py::helper', gap['omitted_entities'])
        self.assertLessEqual(result['counts']['variants'], 12)

    def test_rendered_input_carries_a_resolver_profile_reference(self):
        request = self.request(query='', anchors=['core.py::helper'])
        result = self.packet(self.plan(request), request, 10 ** 6)
        rendered = packets.parse_input(result['input'])
        self.assertNotIn('profile', rendered['resolver_profile'])
        self.assertEqual(rendered['resolver_profile']['digest'], retrieval._digest(result['resolver_profile']))
        self.assertIn('profile', result['resolver_profile'])

    def test_input_is_compact_while_the_receipt_keeps_every_omission(self):
        request = self.request(anchors=['core.py::helper'])
        plan = self.plan(request)
        with mock.patch.object(packets, 'LEAD_LIMIT', 2):
            result = self.packet(plan, request, 10 ** 6)
        rendered = packets.parse_input(result['input'])
        self.assertNotIn(str(self.root), json.dumps(rendered))
        self.assertNotIn(self.root.as_posix(), result['input'])
        compact = next(g for g in rendered['gaps'] if g['kind'] == 'projection_limit')
        self.assertEqual(set(compact['omitted_entities']), {'count', 'first'})
        full = next(g for g in result['gaps'] if g['kind'] == 'projection_limit')
        self.assertEqual(len(full['omitted_entities']), compact['omitted_entities']['count'])
        self.assertFalse([b for b in rendered['blocks'] if b['kind'] in ('source', 'body')])
        receipt = {b['path']: b for b in result['blocks'] if b['kind'] == 'source'}
        for section in rendered['sources']:
            block = next(x for x in receipt[section['path']]['blocks'] if x['start'] == section['start'])
            numbered = ''.join(f"{section['start'] + i}: {line}\n"
                               for i, line in enumerate(section['text'].split('\n')[:-1]))
            self.assertEqual(numbered, block['source'])
            self.assertTrue(receipt[section['path']]['raw_hash'].startswith(section['raw']))
        self.assertIn('helper', [name for section in rendered['sources'] for name in section['bodies']])

    def test_source_sections_are_raw_text_and_survive_a_marker_lookalike(self):
        (self.root / 'core.py').write_bytes(
            b'OFFSET = 1\n\ndef helper(value):\n    """Quote "this" and a \\\\ backslash."""\n'
            b'    marker = "@@ end S1"\n    return value + OFFSET\n\ndef run(value):\n    return helper(value)\n')
        snapshot.write_snapshot(self.root, self.manifest)
        retrieval.refresh_index(self.manifest, self.index)
        request = self.request(query='', anchors=['core.py::helper'])
        result = self.packet(self.plan(request), request, 10 ** 6)
        self.assertIn('    """Quote "this" and a \\\\ backslash."""\n', result['input'])
        self.assertNotIn('\\"this\\"', result['input'])
        rendered = packets.parse_input(result['input'])
        text = ''.join(section['text'] for section in rendered['sources'])
        self.assertIn('    marker = "@@ end S1"\n', text)
        self.assertEqual(rendered['counts']['sources'], len(rendered['sources']))

    def test_obligations_stay_open_in_the_input_without_their_provenance(self):
        base = self.manifest.with_name('base.sqlite')
        snapshot.write_snapshot(self.root, base)
        (self.root / 'core.py').write_bytes(
            b'OFFSET = 1\n\ndef helper(value):\n    return value + OFFSET + 1\n\ndef run(value):\n    return helper(value)\n')
        snapshot.write_snapshot(self.root, self.manifest)
        retrieval.refresh_index(self.manifest, self.index)
        request = self.request(intent='bug', query='', requirements=[
            {'id': 'R1', 'support': [{'predicate': 'current_source', 'entity_id': 'core.py::helper'}]}])
        request['base'] = {'manifest': str(base)}
        result = self.packet(self.plan(request), request, 10 ** 6)
        impact = [o for o in result['obligations'] if o['kind'] == 'impact']
        self.assertTrue(impact)
        self.assertTrue(all(o['provenance'] for o in impact))
        rendered = packets.parse_input(result['input'])['obligations']
        self.assertEqual({o['id'] for o in rendered if o['kind'] != 'impact'},
                         {o['id'] for o in result['obligations'] if o['kind'] != 'impact'})
        grouped = [o for o in rendered if o['kind'] == 'impact']
        self.assertEqual(sorted(e for o in grouped for e in o['entities']), sorted(o['entity_id'] for o in impact))
        self.assertTrue(all(o['status'] == 'open' for o in grouped))
        self.assertFalse([o for o in rendered if 'provenance' in o])

    def test_impact_is_built_only_for_core_entities_of_intents_that_need_it(self):
        analysis = self.request(anchors=['core.py::helper'])
        result = self.packet(self.plan(analysis), analysis, 10 ** 6)
        self.assertFalse([b for b in result['blocks'] if b.get('kind') == 'edit-impact'])
        change = self.request(intent='change', anchors=['core.py::helper'])
        result = self.packet(self.plan(change), change, 10 ** 6)
        impacted = {b['entity_id'] for b in result['blocks'] if b.get('kind') == 'edit-impact'}
        self.assertEqual(impacted, {'core.py::helper'})

    def test_policy_comparison_runs_only_on_request(self):
        rows = [{'id': 'a', 'group': 'a', 'provides': ['core'], 'requires': [], 'features': {'a': 1},
                 'payload': {'text': 'a'}},
                {'id': 'b', 'group': 'b', 'provides': [], 'requires': [], 'features': {'b': 1},
                 'payload': {'text': 'b'}}]
        plain = packets.pack_variants(rows, ['core'], recipient=recipient(1000), token_counter=len)
        self.assertEqual(plain['comparison'], {})
        compared = packets.pack_variants(rows, ['core'], recipient=recipient(1000, compare=True), token_counter=len)
        self.assertEqual(set(compared['comparison']), {'ordered', 'marginal'})

    def test_map_slice_separates_core_entities_from_leads(self):
        request = self.request(anchors=['core.py::helper'])
        plan = self.plan(request)
        result = map_slice.project_slice(plan, request, authority=self.authority, indexes=self.indexes)
        core = next(c for c in result['components'] if c['paths'] == ['core.py'])
        self.assertIn('core.py::helper', core['entities'])
        leads = next(c for c in result['components'] if c['paths'] == ['leads.py'])
        self.assertEqual(leads['entities'], [])
        self.assertTrue(leads['leads'])


if __name__ == '__main__':
    unittest.main()
