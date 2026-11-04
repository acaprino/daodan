"""Behavioral oracles for bounded evidence selection and project-bound packets."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import subprocess

SCRIPTS = Path(__file__).resolve().parents[1] / 'plugins/codebase-map/skills/map-method/scripts'
sys.path.insert(0, str(SCRIPTS))
import context_packet as packets
import snapshot
import scope_planner as scope
import semantic_store
from snapshot_store import open_snapshot


def variant(identity, *, provides=(), requires=(), group=None, text='', features=None):
    return {'id': identity, 'entity_id': group or identity, 'group': group or identity,
            'representation': 'test-evidence', 'provides': list(provides),
            'requires': list(requires), 'features': features or {identity: 1},
            'payload': {'text': text}}


class PrerequisitePackingTests(unittest.TestCase):
    def recipient(self, **updates):
        return dict(id='test-recipient', tokenizer_id='characters-as-test-tokens',
                    available_tokens=100000, reserve_tokens=0, max_chars=100000,
                    prefix='instructions:', suffix=':response', policy='marginal',
                    max_evaluations=300, **updates)

    def pack(self, rows, hard=(), **updates):
        recipient = self.recipient()
        recipient.update(updates)
        return packets.pack_variants(rows, list(hard), recipient=recipient,
                                     token_counter=len)

    def test_obligation_cannot_be_replaced_by_semantically_similar_card(self):
        rows = [variant('source', provides=['current_source'], group='target', text='code' * 30),
                variant('card', provides=['meaning'], group='target', text='summary')]
        result = self.pack(rows, ['current_source'])
        self.assertEqual(result['selected'], ['source'])
        self.assertEqual(result['status'], 'ready')

    def test_mutually_dependent_support_is_all_or_nothing(self):
        rows = [variant('a', provides=['core'], requires=['b'], text='a' * 100),
                variant('b', requires=['a'], text='b' * 100)]
        result = self.pack(rows, ['core'], max_chars=180)
        self.assertEqual(result['status'], 'needs_split')
        self.assertEqual(result['selected'], [])
        self.assertEqual({r['id'] for r in result['deferred']}, {'a', 'b'})

    def test_complete_serialization_and_instruction_wrapper_consume_budget(self):
        result = self.pack([variant('x', provides=['core'], text='x')], ['core'],
                           max_chars=5)
        self.assertEqual(result['status'], 'needs_split')
        self.assertFalse(result['budget']['fits'])

    def test_reserve_reduces_available_tokens_and_cost_counts_actual_input(self):
        rows = [variant('x', provides=['core'], text='x' * 30)]
        reference = self.pack(rows, ['core'])
        cost = len(reference['input'])
        self.assertEqual(reference['budget']['input_tokens'], cost)
        blocked = self.pack(rows, ['core'], available_tokens=cost + 9, reserve_tokens=10)
        self.assertEqual(blocked['status'], 'needs_split')

    def test_shared_support_is_reconsidered_after_each_selection(self):
        rows = [variant('card', provides=['core'], group='target', text='c' * 150, features={'target': 1}),
                variant('b', requires=['support'], text='b' * 70, features={'b': 8}),
                variant('body', provides=['core'], group='target', requires=['support'], text='x', features={'target': 20}),
                variant('support', text='s' * 80, features={'support': 0})]
        # Core card plus b/support exceeds 250 characters. Replacing the card
        # with body/support makes b fit; a permanent rejection loses b.
        result = self.pack(rows, ['core'], max_chars=250, compare=True)
        self.assertEqual(set(result['selected']), {'support', 'body', 'b'})
        self.assertEqual(result['comparison']['ordered']['utility'], 28)

    def test_replacement_must_preserve_documentary_support(self):
        rows = [variant('card', group='entity', provides=['documentary_rule'], features={'meaning': 1}),
                variant('body', group='entity', provides=['current_source'], features={'meaning': 50})]
        result = self.pack(rows, ['documentary_rule'])
        self.assertEqual(result['selected'], ['card'])

    def test_identical_text_does_not_merge_different_entities(self):
        result = self.pack([variant('class-a', text='def same(): pass'),
                            variant('class-b', text='def same(): pass')])
        self.assertEqual(set(result['selected']), {'class-a', 'class-b'})

    def test_no_tokenizer_does_not_claim_exact_token_limit(self):
        result = packets.pack_variants([variant('x')], [], recipient=self.recipient())
        self.assertEqual(result['budget']['measurement'], 'characters_only')
        self.assertIsNone(result['budget']['input_tokens'])
        self.assertFalse(result['budget']['dispatch_verified'])

    def test_work_limit_is_explicit_and_retains_residuals(self):
        result = self.pack([variant(str(i)) for i in range(20)], max_evaluations=2)
        self.assertLessEqual(result['evaluations'], 2)
        self.assertTrue(result['work_limited'])
        self.assertEqual(len(result['selected']) + len(result['deferred']), 20)

    def test_missing_prerequisite_never_produces_ready_core(self):
        result = self.pack([variant('x', provides=['core'], requires=['absent'])], ['core'])
        self.assertEqual(result['status'], 'needs_split')
        self.assertEqual(result['missing_support'], ['core'])

    def test_invalid_token_counter_and_negative_budget_fail_closed(self):
        with self.assertRaises(ValueError):
            packets.pack_variants([variant('x')], [], recipient=self.recipient(),
                                  token_counter=lambda _: -1)
        with self.assertRaises(ValueError):
            self.pack([], available_tokens=-1)

    def test_bounded_core_search_stops_when_every_combination_conflicts(self):
        rows = [variant(str(i), provides=['one'] if i % 2 else ['two'], group='exclusive')
                for i in range(200)]
        result = self.pack(rows, ['one', 'two'], max_evaluations=3)
        self.assertEqual(result['status'], 'needs_split')
        self.assertTrue(result['work_limited'])

    def test_comparison_cannot_spend_the_requested_policy_work_share(self):
        result = self.pack([variant(str(i)) for i in range(5)], max_evaluations=30, compare=True)
        self.assertTrue(result['comparison']['ordered']['selected'])
        self.assertTrue(result['comparison']['marginal']['selected'])
        self.assertTrue(result['selected'])
        self.assertLessEqual(result['evaluations'], 30)


class ProjectPacketTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='context-packet-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        (self.root / 'core.py').write_bytes(b'OFFSET = 1\n\ndef helper(value):\n    return value + OFFSET\n\ndef run(value):\n    return helper(value)\n')
        out = self.root / '.codebase-map'
        out.mkdir()
        self.manifest = out / 'snapshot.sqlite'
        snapshot.write_snapshot(self.root, self.manifest)
        self.authority = {'root': str(self.root), 'read_boundary': ['.'], 'write_boundary': ['core.py']}
        self.request = {'schema': 'daodan/context-request/v1', 'task_id': 'packet-task',
            'intent': 'change', 'query': '', 'read_boundary': ['.'], 'write_boundary': ['core.py'],
            'anchors': [{'entity_id': 'core.py::helper'}, {'entity_id': 'core.py::run'}],
            'base': None, 'candidate': {'manifest': str(self.manifest)}, 'diff': [],
            'proposed_edits': [{'entity_id': 'core.py::helper'}],
            'mandatory_requirements': [{'id': 'source', 'support': [
                {'predicate': 'current_source', 'entity_id': 'core.py::helper'}]}],
            'required_gates': [{'id': 'tests'}],
            'budget': {'max_candidates': 100, 'max_edges': 1000, 'max_rounds': 100,
                       'max_seconds': 120, 'max_input_tokens': 1000000, 'max_output_tokens': 1000000},
            'policy_version': 'scope-v1'}
        self.recipient = dict(id='test', tokenizer_id='test-characters', available_tokens=500000,
            reserve_tokens=100, max_chars=500000, prefix='Use evidence only.\n', suffix='\nReply.',
            max_evaluations=300, policy='marginal')
        self.plan = scope.prepare_scope(self.request, authority=self.authority)

    def packet(self, **options):
        return packets.build_packet(self.plan, self.request, authority=self.authority,
            recipient=self.recipient, token_counter=len, **options)

    def test_current_source_includes_context_and_deduplicates_overlap(self):
        result = self.packet()
        self.assertEqual(result['status'], 'ready')
        payload = packets.parse_input(result['input'].removeprefix('Use evidence only.\n').removesuffix('\nReply.'))
        source = payload['sources']
        self.assertEqual({s['path'] for s in source}, {'core.py'})
        # The recipient input carries raw source sections numbered by their first line.
        lines = [f"{block['start'] + offset}: {text}" for block in source
                 for offset, text in enumerate(block['text'].split('\n')[:-1])]
        self.assertEqual(len(lines), len(set(line.split(':', 1)[0] for line in lines)))
        self.assertIn('1: OFFSET = 1', lines)
        self.assertIn('4:     return value + OFFSET', lines)
        self.assertTrue(any(b.get('entity_id') == 'core.py::run' for b in payload['blocks']))
        self.assertFalse(result['validation_complete'])
        self.assertTrue(any(r['id'] == 'tests' for r in result['obligations']))

    def test_replaying_same_cursor_has_identical_selection_and_bytes(self):
        first = self.packet()
        a = self.packet(cursor=first['cursor'])
        b = self.packet(cursor=json.loads(json.dumps(first['cursor'])))
        self.assertEqual(a, b)

    def test_cursor_rejects_recipient_request_index_and_source_changes(self):
        first = self.packet()
        self.recipient['prefix'] += ' Changed.'
        with self.assertRaisesRegex(ValueError, 'cursor_stale'):
            self.packet(cursor=first['cursor'])
        self.recipient['prefix'] = 'Use evidence only.\n'
        (self.root / 'core.py').write_bytes(b'def helper(value):\n    return 7\n')
        with self.assertRaises(ValueError):
            self.packet(cursor=first['cursor'])

    def test_tiny_packet_keeps_obligations_and_does_not_claim_ready(self):
        self.recipient['max_chars'] = 10
        result = self.packet()
        self.assertEqual(result['status'], 'needs_split')
        self.assertIsNone(result['input'])
        self.assertEqual({r['id'] for r in result['obligations']}, {'source', 'tests'})
        self.assertTrue(result['deferred'])

    def test_rejected_packet_does_not_charge_undelivered_input_on_resume(self):
        self.recipient['max_chars'] = 10
        first = self.packet()
        second = self.packet(cursor=first['cursor'])
        self.assertIsNone(first['input'])
        self.assertIsNone(second['input'])
        self.assertEqual(first['cursor']['delivered'], [])
        self.assertEqual(second['cursor']['delivered'], [])
        self.assertEqual(first['cursor']['input_tokens'], 0)
        self.assertEqual(second['cursor']['input_tokens'], 0)

    def test_input_cost_includes_bindings_provenance_and_gaps(self):
        result = self.packet()
        self.assertEqual(result['budget']['input_tokens'], len(result['input']))
        self.assertIn('engine', result['input'])
        self.assertIn('unavailable', result['input'])
        self.recipient['available_tokens'] = len(result['input']) + 99
        smaller = self.packet()
        self.assertLessEqual(smaller['budget']['input_tokens'] + 100, self.recipient['available_tokens'])
        self.assertTrue(smaller['deferred'])

    def test_artifact_is_exclusive_and_cursor_is_not_an_authorization(self):
        result = self.packet()
        output = self.manifest.parent / 'packet.json'
        saved = packets.persist_packet(result, output, authority=self.authority)
        self.assertEqual(Path(saved['path']), output)
        original = output.read_bytes()
        with self.assertRaises(ValueError):
            packets.persist_packet(result, output, authority=self.authority)
        self.assertEqual(output.read_bytes(), original)
        tampered = copy.deepcopy(result['cursor'])
        tampered['delivered'] = ['invented']
        with self.assertRaisesRegex(ValueError, 'cursor_stale'):
            self.packet(cursor=tampered)

    def test_unrecognized_hard_predicate_stays_missing(self):
        self.request['mandatory_requirements'].append({'id': 'behavior', 'support': [
            {'predicate': 'tests_passed', 'entity_id': 'core.py::helper'}]})
        self.plan = scope.prepare_scope(self.request, authority=self.authority)
        result = self.packet()
        self.assertEqual(result['status'], 'needs_split')
        self.assertIn('tests_passed:core.py::helper', result['missing_support'])

    def test_card_bytes_and_missing_index_appearance_invalidate_cursor(self):
        cards = self.manifest.parent / 'cards.sqlite'
        with open_snapshot(self.manifest) as store:
            semantic_store.upsert_meta_cards(store, cards, [{'file': 'core.py', 'symbol': 'helper',
                'purpose': 'Apply the configured offset', 'invariants': ['Preserve the input value']}])
        indexes = {'cards': str(cards), 'retrieval': str(self.manifest.parent / 'retrieval.sqlite')}
        self.plan = scope.prepare_scope(self.request, authority=self.authority, indexes=indexes)
        first = self.packet()
        with open_snapshot(self.manifest) as store:
            semantic_store.upsert_meta_cards(store, cards, [{'file': 'core.py', 'symbol': 'helper',
                'purpose': 'A revised semantic description'}])
        with self.assertRaisesRegex(ValueError, 'cursor_stale'):
            self.packet(cursor=first['cursor'])
        self.plan = scope.prepare_scope(self.request, authority=self.authority, indexes=indexes)
        first = self.packet()
        (self.manifest.parent / 'retrieval.sqlite').write_bytes(b'new index generation')
        with self.assertRaisesRegex(ValueError, 'cursor_stale'):
            self.packet(cursor=first['cursor'])

    def test_nested_method_keeps_its_closure_and_module_context(self):
        (self.root / 'core.py').write_bytes(b'class Outer:\n    def helper(self, value):\n        def nested():\n            return value\n        return nested()\n\nSECRET_CONTEXT = 4\n')
        snapshot.write_snapshot(self.root, self.manifest)
        self.request['anchors'] = [{'entity_id': 'core.py::Outer.helper.nested'}]
        self.request['proposed_edits'] = []
        self.request['mandatory_requirements'] = []
        self.plan = scope.prepare_scope(self.request, authority=self.authority)
        result = self.packet()
        source = next(b for b in result['blocks'] if b['kind'] == 'source')
        self.assertEqual(source['reasons'], ['context-and-selection'])
        self.assertIn('def helper(self, value):', result['input'])
        self.assertIn('return nested()', result['input'])
        self.assertIn('SECRET_CONTEXT = 4', result['input'])

    def test_cli_uses_shared_packet_contract_and_compact_stdout(self):
        request = self.manifest.parent / 'request.json'
        recipient = self.manifest.parent / 'recipient.json'
        authority = self.manifest.parent / 'authority.json'
        request.write_text(json.dumps(self.request), encoding='utf8')
        recipient.write_text(json.dumps(self.recipient), encoding='utf8')
        authority.write_text(json.dumps(self.authority), encoding='utf8')
        run = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'snapshot.py'), 'context',
            str(self.manifest), '--request', str(request), '--recipient', str(recipient),
            '--authority', str(authority), '--out', str(self.manifest.parent / 'context')],
            capture_output=True, text=True, encoding='utf8')
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertNotIn('blocks', result)
        self.assertNotIn('return value', run.stdout)
        packet = json.loads(Path(result['path']).read_text(encoding='utf8'))
        self.assertEqual(result['status'], packet['status'])
        self.assertIn('return value + OFFSET', packet['input'])
        self.assertFalse(packet['budget']['dispatch_verified'])


if __name__ == '__main__':
    unittest.main()
