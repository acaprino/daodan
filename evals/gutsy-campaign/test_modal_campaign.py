"""LOCAL control-flow evidence; Modal, hardware and inference are explicitly fake.

The ledger, request records, atomic writes, resume checks and evidence archive use
real temporary files. Passing these checks is not a live Modal capability probe.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

from campaign_ledger import Ledger, MAX_SECONDS, MODEL, atomic_json, digest

HERE = Path(__file__).resolve().parent
TEMP_ROOT = HERE.parents[1] / '.daodan/runs/2026-10-26-gutsy-campaign/test-tmp'


class FakeImage:
    @classmethod
    def debian_slim(cls, **_kwargs):
        return cls()

    def __getattr__(self, _name):
        return lambda *_args, **_kwargs: self


class FakeVolume:
    commits = 0

    @classmethod
    def from_name(cls, *_args, **_kwargs):
        return cls()

    def commit(self):
        self.commits += 1


class FakeApp:
    def __init__(self, *_args, **_kwargs):
        pass

    def function(self, **_kwargs):
        return lambda function: function

    def local_entrypoint(self, **_kwargs):
        return lambda function: function


def load_local_executor():
    fake_modal = types.ModuleType('modal')
    fake_modal.Image, fake_modal.Volume, fake_modal.App = FakeImage, FakeVolume, FakeApp
    spec = importlib.util.spec_from_file_location('explicitly_fake_modal_campaign', HERE / 'modal_campaign.py')
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {'modal': fake_modal}):
        spec.loader.exec_module(module)
    return module


subject = load_local_executor()


class FakeSampler:
    latest = 4096
    peak = 8192
    exceeded = False
    server = None

    def start(self):
        pass

    def close(self):
        pass


class FakeProcess:
    stopped = False

    def poll(self):
        return 0 if self.stopped else None

    def terminate(self):
        self.stopped = True

    def wait(self, **_kwargs):
        return 0


PROFILES = {
    'main': {'cache': 'lru', 'threads': 4, 'n_ctx': 4096},
    't4c4096': {'cache': 'intra', 'threads': 4, 'n_ctx': 4096},
    'full': {'cache': 'full', 'threads': 4, 'n_ctx': 4096},
}


def request(identifier, block='core', profile='main', count=1):
    result = {'id': identifier, 'block': block, 'profile': profile, 'domain': 'routing',
              'body': {'model': MODEL, 'state': {'local_fixture': identifier},
                       'questions': {f'q{i}': {'type': 'noul', 'instructions': 'Keep this fact?'} for i in range(count)}}}
    if block == 'runtime-parity':
        result['parity_group'] = 'same-input'
        result['body']['state'] = {'local_fixture': 'identical-parity-input'}
    return result


def fixtures():
    parity = [request('parity' + name, 'runtime-parity', name) for name in PROFILES]
    probes = [request('probe' + str(i), 'development-probe', count=i + 1) for i in range(3)]
    return parity + probes + [request('pendingcore')]


def answer(body, profile='main', probability=.5):
    return {'model': MODEL,
            'answers': {key: {'type': 'noul', 'noul': probability} for key in body['questions']},
            'usage': {'model_calls': len(body['questions']), 'evaluated_tokens': 100 + 28 * len(body['questions']),
                      'state_cached': PROFILES[profile]['cache'] != 'full', 'state_cache_hit': False}}


def tokens(requests):
    return {row['id']: {'max_prompt_tokens': 128, 'state_tokens': 100,
                        'question_prompt_tokens': {key: 128 for key in row['body']['questions']}}
            for row in requests}


class LocalExecutorTests(unittest.TestCase):
    def setUp(self):
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='fake-executor-', dir=TEMP_ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.mount = Path(self.temporary.name)
        self.directory = self.mount / 'localtest'
        self.requests = fixtures()
        self.code_files = {name: hashlib.sha256(('FAKE-LOCAL-' + name).encode()).hexdigest()
                           for name in ('modal_campaign.py', 'server_bootstrap.py', 'campaign_ledger.py')}
        self.code_hash = digest(self.code_files)
        self.payload = {'requests': self.requests, 'profiles': copy.deepcopy(PROFILES), 'forecast_safety_factor': 1.25}
        atomic_json(self.directory / 'input.json', self.payload)
        self.input_hash = subject.file_hash(self.directory / 'input.json')
        self.http_calls = []
        self.server_calls = []
        self.active_profile = 'main'

    def seed(self, requests, probability=.5, **budget):
        ledger = Ledger(self.directory, self.input_hash, self.code_hash, **budget)
        records = {}
        for row in requests:
            ledger.begin(row)
            records[row['id']] = ledger.finish(row, {
                'status': 'delivered', 'response': answer(row['body'], row['profile'], probability),
                'elapsed_seconds': .05 * len(row['body']['questions']),
                'profile': row['profile'], 'host_identity': 'local-fake-host'})
        return ledger, records

    def configure_parent(self, *, started_at=None, attempted=75, reserved=18):
        parent = {
            'schema': 'gutsy-campaign-ledger/v1', 'input_hash': 'frozen-v1-input',
            'code_hash': 'frozen-v1-executor', 'started_at': started_at or time.time() - 600,
            'attempted_questions': attempted, 'startup_question_reserve': reserved,
            'carried_questions': 0, 'status': 'incomplete', 'complete': False, 'requests': {},
        }
        binding = {'run_key': 'parentv1', 'input_hash': parent['input_hash']}
        atomic_json(self.mount / 'parentv1/ledger.json', parent)
        self.payload.update(parity_contract='cached-paths-v2', budget_parent=binding)
        atomic_json(self.directory / 'input.json', self.payload)
        self.input_hash = subject.file_hash(self.directory / 'input.json')
        return parent, binding

    def invoke(self, response_mutator=None, input_hash=None, code_hash=None):
        original_hash = subject.file_hash

        def fake_hash(path):
            if '/opt/campaign/' in str(path).replace('\\', '/'):
                return self.code_files[Path(path).name]
            return original_hash(path)

        def start(profile, requests, work, _models, _ledger, sampler):
            self.server_calls.append(copy.deepcopy(profile))
            self.active_profile = next(name for name, item in PROFILES.items() if item == profile)
            work.mkdir(parents=True, exist_ok=True)
            process, log = FakeProcess(), io.BytesIO()
            sampler.server = process
            return process, log, 'http://explicitly-fake.local', {
                'self_check': {'explicitly_fake': True}, 'cache_enabled': profile['cache'] != 'full',
                'requests': tokens(requests)}, .001

        def http(_url, body, timeout):
            self.assertGreater(timeout, 0)
            self.http_calls.append(copy.deepcopy(body))
            response = answer(body, self.active_profile)
            return response_mutator(response) if response_mutator else response

        with contextlib.ExitStack() as stack:
            for name, value in [('MOUNT', self.mount), ('file_hash', fake_hash), ('start_server', start),
                                ('ensure_models', lambda *_args: {'explicitly_fake': True}),
                                ('environment', lambda: {'host_identity': 'local-fake-host'}),
                                ('MemorySampler', FakeSampler), ('http_json', http),
                                ('read_optional', lambda _path: None), ('volume', FakeVolume())]:
                stack.enter_context(mock.patch.object(subject, name, value))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            return subject.run_campaign('localtest', input_hash or self.input_hash, code_hash or self.code_hash)

    def test_completed_parity_and_probes_resume_without_paid_repetition(self):
        ledger, _ = self.seed(self.requests[:-1])
        previous_questions = ledger.state['attempted_questions']
        previous_bytes = {p.name: p.read_bytes() for p in (self.directory / 'records').glob('*.json')}
        result = self.invoke()
        self.assertTrue(result['ledger']['complete'])
        self.assertEqual(['pendingcore'], [body['state']['local_fixture'] for body in self.http_calls])
        self.assertEqual(previous_questions + 1, result['ledger']['attempted_questions'])
        self.assertIn('parity_gate', result['runtime'])
        self.assertIn('forecast_gate', result['runtime'])
        self.assertTrue((self.directory / 'evidence.tar.gz').is_file())
        for name, data in previous_bytes.items():
            self.assertEqual(data, (self.directory / 'records' / name).read_bytes())

    def test_unknown_attempt_stops_instead_of_resubmitting(self):
        ledger, _ = self.seed(self.requests[:-1])
        ledger.begin(self.requests[-1])
        prior_questions = ledger.state['attempted_questions']
        result = self.invoke()
        self.assertFalse(result['ledger']['complete'])
        self.assertEqual([], self.http_calls)
        self.assertEqual([], self.server_calls)
        self.assertEqual(prior_questions, result['ledger']['attempted_questions'])
        self.assertEqual('unknown', result['ledger']['requests']['pendingcore']['status'])
        self.assertIn('Unresolved inference', result['ledger']['error']['message'])

    def test_uploaded_input_and_executor_identity_are_checked_before_execution(self):
        for kwargs in ({'input_hash': 'changed'}, {'code_hash': 'changed'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.invoke(**kwargs)
        self.assertEqual([], self.http_calls)
        self.assertFalse((self.directory / 'ledger.json').exists())

    def test_model_identity_type_and_cache_violations_leave_failed_evidence(self):
        mutations = {
            'identity': lambda r: {**r, 'model': 'wrong-model'},
            'answer-type': lambda r: {**r, 'answers': {'q0': {'type': 'choice', 'noul': .5}}},
            'cache-mode': lambda r: {**r, 'usage': {**r['usage'], 'state_cached': False}},
        }
        # Each failed attempt has its own immutable request directory.
        for name, mutate in mutations.items():
            with self.subTest(violation=name):
                # run_campaign's run key is fixed in invoke; give each subtest its own mount.
                self.mount = self.mount / name
                self.directory = self.mount / 'localtest'
                atomic_json(self.directory / 'input.json', self.payload)
                self.seed(self.requests[:-1])
                result = self.invoke(mutate)
                self.assertFalse(result['ledger']['complete'])
                record = json.loads((self.directory / 'records/pendingcore.json').read_text())
                self.assertEqual('failed', record['status'])
                self.assertEqual('ValueError', record['error']['type'])
                self.assertIn('response', record)
        self.assertEqual(3, len(self.http_calls))

    def test_cache_contract_distinguishes_full_intra_and_lru(self):
        for name, profile in PROFILES.items():
            response = answer(request('x')['body'], name)
            self.assertTrue(subject.attest_cache(profile, response, 1)['called'])
            response['usage']['state_cache_hit'] = True
            if name == 'main':
                self.assertTrue(subject.attest_cache(profile, response, 1)['state_cache_hit'])
            else:
                with self.assertRaises(ValueError):
                    subject.attest_cache(profile, response, 1)
        self.assertFalse(subject.attest_cache(PROFILES['full'], {'usage': {'model_calls': 0}}, 0)['called'])
        for bad in ({}, {'usage': {'state_cached': True}},
                    {'usage': {'state_cached': 1, 'state_cache_hit': False}}):
            with self.assertRaises(ValueError):
                subject.attest_cache(PROFILES['main'], bad, 1)

    def test_family_subset_requires_a_delivered_predecessor(self):
        planned = request('subset', count=2)
        planned['subset'] = {'kind': 'family_gate', 'source_request': 'families',
                             'family_for_question': {'q0': 'read', 'q1': 'write'}, 'threshold': .5}
        for records in ({}, {'families': {'status': 'running'}}, {'families': {'status': 'failed'}}):
            with self.assertRaises(ValueError):
                subject.resolved_request(planned, records)
        records = {'families': {'status': 'delivered', 'response': {'answers': {
            'read': {'type': 'noul', 'noul': .8}, 'write': {'type': 'noul', 'noul': .2}}}}}
        resolved = subject.resolved_request(planned, records)
        self.assertEqual(['q0'], list(resolved['body']['questions']))
        self.assertEqual(['q0', 'q1'], list(planned['body']['questions']))
        self.assertEqual(digest(planned), resolved['planned_request_hash'])

    def test_foreground_deadline_blocks_pending_work_before_server_start(self):
        ledger, _ = self.seed(self.requests[:-1])
        ledger.state['started_at'] = time.time() - MAX_SECONDS - 1
        ledger.save()
        result = self.invoke()
        self.assertFalse(result['ledger']['complete'])
        self.assertEqual('TimeoutError', result['ledger']['error']['type'])
        self.assertEqual([], self.http_calls)
        self.assertEqual([], self.server_calls)

    def test_deadline_exhausted_by_last_response_cannot_mark_campaign_complete(self):
        self.seed(self.requests[:-1])
        clock = {'now': time.time()}

        class ControlledClockLedger(Ledger):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs, clock=lambda: clock['now'])

        def response_after_deadline(response):
            clock['now'] += MAX_SECONDS + 1
            return response

        with mock.patch.object(subject, 'Ledger', ControlledClockLedger):
            result = self.invoke(response_after_deadline)
        self.assertFalse(result['ledger']['complete'])
        self.assertEqual('TimeoutError', result['ledger']['error']['type'])
        self.assertTrue((self.directory / 'records/pendingcore.json').is_file())

    def test_parity_failure_blocks_pending_core(self):
        _ledger, _ = self.seed(self.requests[:-1])
        path = self.directory / 'records/parityfull.json'
        altered = json.loads(path.read_text())
        altered['response']['answers']['q0']['noul'] = .9
        atomic_json(path, altered)
        result = self.invoke()
        self.assertFalse(result['ledger']['complete'])
        self.assertEqual([], self.http_calls)
        self.assertIn('parity tolerance', result['ledger']['error']['message'])

    def test_v1_failure_remains_while_v2_reports_full_path_difference(self):
        for question_type in ('noul', 'choice'):
            with self.subTest(question_type=question_type):
                rows = copy.deepcopy(self.requests[:3])
                records = {}
                for row in rows:
                    if question_type == 'choice':
                        row['body']['questions']['q0'] = {
                            'type': 'choice', 'instructions': 'Choose a disposition.',
                            'criteria': {'keep': 'Retain', 'drop': 'Remove'}}
                    value = answer(row['body'], row['profile'])
                    if question_type == 'noul':
                        value['answers']['q0']['noul'] = .8 if row['profile'] == 'full' else .5
                    else:
                        probability = .8 if row['profile'] == 'full' else .7
                        value['answers']['q0'] = {'type': 'choice', 'choice': 'keep', 'reject': .1,
                                                  'probabilities': {'keep': probability, 'drop': 1 - probability}}
                    records[row['id']] = {'status': 'delivered', 'response': value}
                before = copy.deepcopy(records)
                with self.assertRaisesRegex(ValueError, 'three-path-v1'):
                    subject.parity_gate(rows, records, contract='three-path-v1')
                result = subject.parity_gate(rows, records, contract='cached-paths-v2')
                self.assertEqual(.02, result['tolerance'])
                self.assertEqual(0, result['max_probability_delta']['same-input'])
                self.assertGreater(result['full_reencoding_max_probability_delta']['same-input'], .02)
                self.assertFalse(result['full_reencoding_equivalence_claimed'])
                self.assertEqual(before, records)

    def test_v2_still_rejects_cached_disagreement_and_missing_paths(self):
        rows = self.requests[:3]
        records = {row['id']: {'status': 'delivered', 'response': answer(row['body'], row['profile'])} for row in rows}
        records['parityt4c4096']['response']['answers']['q0']['noul'] = .519
        result = subject.parity_gate(rows, records, contract='cached-paths-v2')
        self.assertAlmostEqual(.019, result['max_probability_delta']['same-input'])
        records['parityt4c4096']['response']['answers']['q0']['noul'] = .521
        with self.assertRaisesRegex(ValueError, 'cached-paths-v2'):
            subject.parity_gate(rows, records, contract='cached-paths-v2')
        with self.assertRaisesRegex(ValueError, 'Unknown preregistered'):
            subject.parity_gate(rows, records, contract='unregistered-contract')
        with self.assertRaisesRegex(ValueError, 'all three'):
            subject.parity_gate(rows[:-1], records, contract='cached-paths-v2')

    def test_v2_remote_parent_carry_is_durable_and_does_not_reset_on_resume(self):
        parent, binding = self.configure_parent()
        budget = {'budget_origin': parent['started_at'], 'carried_questions': 93, 'budget_parent': binding}
        self.seed(self.requests[:-1], **budget)
        path = self.directory / 'records/parityfull.json'
        full = json.loads(path.read_text())
        full['response']['answers']['q0']['noul'] = .8
        atomic_json(path, full)
        parent_path = self.mount / 'parentv1/ledger.json'
        original_parent = parent_path.read_bytes()
        result = self.invoke()
        self.assertTrue(result['ledger']['complete'])
        self.assertEqual('cached-paths-v2', result['runtime']['parity_gate']['contract'])
        self.assertFalse(result['runtime']['parity_gate']['full_reencoding_equivalence_claimed'])
        self.assertEqual(parent['started_at'], result['ledger']['started_at'])
        self.assertEqual(93, result['ledger']['carried_questions'])
        self.assertEqual(10, result['ledger']['attempted_questions'])
        self.assertEqual(binding, result['ledger']['budget_parent'])
        saved = json.loads((self.directory / 'budget-parent.json').read_text())
        self.assertEqual(parent, saved['ledger'])
        self.assertEqual(subject.file_hash(parent_path), saved['ledger_sha256'])
        self.assertEqual(original_parent, parent_path.read_bytes())
        self.assertEqual(1, len(self.http_calls))
        self.assertEqual(result['ledger'], self.invoke()['ledger'])
        self.assertEqual(1, len(self.http_calls))
        # Exercise inherited authorization binding directly without changing the input identity.
        for changed in ({'carried_questions': 94}, {'budget_origin': parent['started_at'] + 1},
                        {'budget_parent': {**binding, 'input_hash': 'other-parent-input'}}):
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, 'inherited authorization budget'):
                Ledger(self.directory, self.input_hash, self.code_hash, **{**budget, **changed})

    def test_inherited_global_deadline_blocks_a_new_run(self):
        parent, _binding = self.configure_parent(started_at=time.time() - MAX_SECONDS - 1)
        result = self.invoke()
        self.assertFalse(result['ledger']['complete'])
        self.assertEqual(parent['started_at'], result['ledger']['started_at'])
        self.assertEqual(93, result['ledger']['carried_questions'])
        self.assertEqual('TimeoutError', result['ledger']['error']['type'])
        self.assertEqual([], self.http_calls)
        self.assertEqual([], self.server_calls)

    def test_inherited_question_budget_blocks_fresh_inference(self):
        self.configure_parent(attempted=50000, reserved=0)
        result = self.invoke()
        self.assertFalse(result['ledger']['complete'])
        self.assertEqual(50000, result['ledger']['carried_questions'])
        self.assertEqual(0, result['ledger']['attempted_questions'])
        self.assertIn('question budget', result['ledger']['error']['message'])
        self.assertEqual([], self.http_calls)

    def test_remote_parent_identity_and_active_parent_are_rejected_before_admission(self):
        parent, _binding = self.configure_parent()
        variants = {
            'wrong-parent-input': {**parent, 'input_hash': 'different-input'},
            'active-parent': {**parent, 'status': 'running'},
            'unresolved-parent': {**parent, 'requests': {'request1': {'status': 'unknown'}}},
        }
        for name, changed in variants.items():
            with self.subTest(parent=name):
                atomic_json(self.mount / 'parentv1/ledger.json', changed)
                with self.assertRaises(ValueError):
                    self.invoke()
                self.assertFalse((self.directory / 'ledger.json').exists())
        self.assertEqual([], self.http_calls)
        self.assertEqual([], self.server_calls)

    def test_unsafe_or_self_referencing_budget_parent_is_rejected(self):
        self.configure_parent()
        for parent_key in ('../outside', 'localtest'):
            with self.subTest(parent=parent_key):
                self.payload['budget_parent']['run_key'] = parent_key
                atomic_json(self.directory / 'input.json', self.payload)
                self.input_hash = subject.file_hash(self.directory / 'input.json')
                with self.assertRaisesRegex(ValueError, 'Unsafe or circular'):
                    self.invoke()
                self.assertFalse((self.directory / 'ledger.json').exists())
        self.assertEqual([], self.http_calls)

    def test_forecast_coefficients_use_probes_not_holdout_measurements(self):
        probes = self.requests[3:6]
        heldout, pending = request('heldout'), request('later')
        rows = probes + [heldout, pending]
        records = {row['id']: {'status': 'delivered', 'response': answer(row['body']),
                               'elapsed_seconds': .1 * len(row['body']['questions'])} for row in probes + [heldout]}
        first = subject.forecast_gate(rows, records, tokens(rows), PROFILES, elapsed=1)
        records['heldout']['elapsed_seconds'] = 100000
        records['heldout']['response']['usage']['evaluated_tokens'] = 999999
        second = subject.forecast_gate(rows, records, tokens(rows), PROFILES, elapsed=1)
        self.assertEqual(first, second)
        self.assertEqual(3, first['probe_requests'])
        del records[probes[0]['id']]
        with self.assertRaisesRegex(ValueError, 'probes incomplete'):
            subject.forecast_gate(rows, records, tokens(rows), PROFILES, elapsed=1)

    def test_executable_json_preserves_option_order(self):
        path = self.mount / 'ordered-input.json'
        body = {'model': MODEL, 'state': {}, 'questions': {'operation': {
            'type': 'choice', 'instructions': 'Pick one.',
            'criteria': {'z-last-lexically': 'First presented', 'a-first-lexically': 'Second presented'}}}}
        atomic_json(path, body)
        restored = json.loads(path.read_text())
        self.assertEqual(list(body['questions']['operation']['criteria']),
                         list(restored['questions']['operation']['criteria']))
        reversed_body = copy.deepcopy(body)
        reversed_body['questions']['operation']['criteria'] = dict(reversed(list(body['questions']['operation']['criteria'].items())))
        self.assertNotEqual(digest(body), digest(reversed_body))
        import campaign as preparation
        preparation.frozen_json(path, body)
        with self.assertRaises(FileExistsError):
            preparation.frozen_json(path, reversed_body)


if __name__ == '__main__':
    unittest.main()
