"""Exercise lifecycle preparation through the real public protocol/provider CLIs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / 'plugins/work-controller/skills/work-record/scripts/run_state.py'
PROVIDER = ROOT / 'plugins/codebase-map/skills/map-method/scripts/snapshot.py'
CYCLE = ROOT / 'plugins/project-delivery/skills/delivery-method/scripts/cycle_packets.py'
sys.path.insert(0, str(PROVIDER.parent))
import snapshot
if CYCLE.is_file():
    spec = importlib.util.spec_from_file_location('cycle_packets', CYCLE)
    cycle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cycle)
else:
    cycle = None


class CycleContextTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(cycle, 'The lifecycle context adapter is not implemented')
        temp = tempfile.TemporaryDirectory(prefix='cycle-context-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        (self.root / 'service.py').write_bytes(b'def calculate(value):\n    return value + 1\n')
        (self.root / 'client.py').write_bytes(b'from service import calculate\n\ndef run(value):\n    return calculate(value)\n')
        (self.root / 'tests.py').write_bytes(b'def test_value():\n    assert 2 == 1 + 1\n')
        (self.root / 'README.md').write_bytes(b'Explain the calculation.\n')
        (self.root / 'secret.py').write_bytes(b'PRIVATE = "never pass this source"\n')
        self.manifest = self.map_snapshot('initial')
        self.config = dict(project=str(self.root),
            run_id='workflow-fixture', protocol=[sys.executable, '-B', str(PROTOCOL)],
            provider=[sys.executable, '-B', str(PROVIDER)], manifest=str(self.manifest), indexes={})
        payload = dict(operation='change', objective='Repair the calculation',
            scope={'paths': ['service.py', 'client.py', 'README.md', 'tests.py', 'secret.py'], 'excluded': ['secret.py']},
            authorizations={'fix': True}, budget={}, required_gates=['tests'],
            waves=[{'id': 'wave-one', 'parallel': False, 'status': 'pending', 'tasks': [{
                'id': 'T1', 'status': 'pending', 'write_set': ['service.py'],
                'requirements': [{'id': 'R1', 'text': 'Calculation must preserve the result',
                    'support': [{'predicate': 'current_source', 'entity_id': 'service.py::calculate'}]}],
                'oracle': {'command': 'python -m unittest', 'expected_failure': 'wrong result'},
                'verification': {'command': 'python -m unittest'}}]}])
        self.protocol('init', payload=payload)
        self.request = dict(schema='daodan/context-request/v1', task_id='ignored-caller-id',
            intent='bug', query='', read_boundary=['.'], write_boundary=['.'],
            anchors=[{'entity_id': 'service.py::calculate'}], base=None, candidate=None,
            diff=[], proposed_edits=[{'entity_id': 'service.py::calculate'}],
            mandatory_requirements=[], required_gates=[], policy_version='scope-v1',
            budget=dict(max_candidates=100, max_edges=100, max_rounds=10,
                max_seconds=120, max_input_tokens=100000, max_output_tokens=100000))
        self.recipient = dict(id='fixture-worker', tokenizer_id='fixture-characters',
            available_tokens=300000, reserve_tokens=100, max_chars=300000, max_evaluations=300)

    def map_snapshot(self, identity):
        path = self.root / '.codebase-map' / identity / 'snapshot.sqlite'
        path.parent.mkdir(parents=True)
        snapshot.write_snapshot(self.root, path)
        return path

    def protocol(self, action, payload=None):
        args = [sys.executable, '-B', str(PROTOCOL), action, '--project', str(self.root),
                '--run-id', 'workflow-fixture', '--session', 'fixture']
        if payload is not None:
            path = self.root / 'protocol-input.json'
            path.write_bytes(json.dumps(payload).encode())
            args.extend(['--payload', str(path)])
            if action == 'update':
                work = json.loads((self.root / '.daodan/runs/workflow-fixture/work.json').read_bytes())
                args.extend(['--expected-revision', str(work['revision'])])
        result = subprocess.run(args, capture_output=True)
        if result.returncode:
            self.fail((result.stdout + result.stderr).decode('utf8', 'replace'))
        return json.loads(result.stdout)

    def prepare(self, stage='task-packet', **options):
        return cycle.prepare_cycle(stage, self.config, self.request, self.recipient,
            task_id=None if stage == 'preflight' else 'T1', **options)

    def receipt(self, result):
        return json.loads(Path(result['path']).read_bytes())

    def test_bug_without_diff_binds_task_requirements_and_exact_scope(self):
        result = self.prepare()
        receipt = self.receipt(result)
        self.assertEqual(receipt['write_set'], ['service.py'])
        self.assertEqual(receipt['request']['read_boundary'], ['README.md', 'client.py', 'service.py', 'tests.py'])
        self.assertEqual(receipt['request']['write_boundary'], ['service.py'])
        self.assertEqual(receipt['task_id'], 'T1')
        self.assertIn('R1', {o['id'] for o in receipt['residual_obligations']})
        self.assertIn('record:tests', {o['id'] for o in receipt['residual_obligations']})
        self.assertEqual(receipt['map_slice']['sha256'], hashlib.sha256(Path(receipt['map_slice']['path']).read_bytes()).hexdigest())
        packet = json.loads(Path(receipt['packet']['path']).read_bytes())
        self.assertNotIn('never pass this source', packet['input'])
        unchecked = cycle.verify_cycle(self.config, result['path'])
        self.assertFalse(unchecked['dispatch_allowed'])
        self.assertEqual(unchecked['status'], 'needs_recipient_check')
        checked = cycle.verify_cycle(self.config, result['path'], token_counter=len, tokenizer_id='fixture-characters')
        self.assertTrue(checked['dispatch_allowed'])
        self.assertFalse(receipt['task_complete'])
        self.assertFalse(receipt['validation_complete'])

    def test_own_ledger_registration_does_not_invalidate_execution_inputs(self):
        result = self.prepare()
        self.protocol('update', {'deliveries': {'context': {'status': 'delivered', 'output': str(Path(result['path']).relative_to(self.root / '.daodan/runs/workflow-fixture'))}}})
        checked = cycle.verify_cycle(self.config, result['path'], token_counter=len, tokenizer_id='fixture-characters')
        self.assertTrue(checked['dispatch_allowed'])

    def test_source_mutation_blocks_dispatch_even_before_ledger_update(self):
        result = self.prepare()
        (self.root / 'service.py').write_bytes(b'def calculate(value):\n    return 0\n')
        with self.assertRaises(ValueError):
            cycle.verify_cycle(self.config, result['path'], token_counter=len, tokenizer_id='fixture-characters')

    def test_new_candidate_and_signature_leave_old_packet_stale_and_obligations_open(self):
        initial = self.prepare('preflight')
        task = self.prepare(previous=initial['path'])
        (self.root / 'service.py').write_bytes(b'def calculate(value, required):\n    return value + required\n')
        self.protocol('update', {'barrier': 'source changed'})
        self.config['manifest'] = str(self.map_snapshot('changed'))
        with self.assertRaises(ValueError):
            cycle.verify_cycle(self.config, task['path'])
        after = self.receipt(self.prepare('post-task', previous=task['path']))
        self.assertEqual(after['request']['base']['manifest'], str(self.manifest))
        self.assertIn('R1', {o['id'] for o in after['residual_obligations']})
        self.assertTrue(any(o.get('kind') == 'impact' for o in after['residual_obligations']))
        self.assertFalse(after['validation_complete'])

    def test_changed_task_plan_blocks_dependent_dispatch(self):
        result = self.prepare()
        work = self.protocol('show')
        work['waves'][0]['tasks'][0]['write_set'] = ['tests.py']
        self.protocol('update', {'waves': work['waves']})
        with self.assertRaises(ValueError):
            cycle.verify_cycle(self.config, result['path'])

    def test_unknown_task_and_out_of_scope_write_set_are_rejected(self):
        with self.assertRaises(ValueError):
            cycle.prepare_cycle('task-packet', self.config, self.request, self.recipient, task_id='foreign')
        work = self.protocol('show')
        work['waves'][0]['tasks'][0]['write_set'] = ['secret.py']
        self.protocol('update', {'waves': work['waves']})
        with self.assertRaises(ValueError):
            self.prepare()

    def test_document_and_test_obligations_survive_tiny_budget(self):
        self.request['intent'] = 'docs'
        self.request['mandatory_requirements'] = [{'id': 'documentation', 'support': [{'predicate': 'fresh_documentation'}]}]
        self.request['required_gates'] = [{'id': 'owner-test-oracle'}]
        self.recipient['max_chars'] = 10
        result = self.prepare()
        receipt = self.receipt(result)
        self.assertEqual(result['status'], 'needs_split')
        self.assertTrue({'documentation', 'R1', 'owner-test-oracle'} <= {o['id'] for o in receipt['residual_obligations']})
        self.assertFalse(cycle.verify_cycle(self.config, result['path'])['dispatch_allowed'])

    def test_interruption_before_and_after_publication_is_resumable(self):
        publish = cycle._publish
        def interrupt_receipt(path, value):
            if Path(path).name == 'receipt.json':
                raise KeyboardInterrupt()
            return publish(path, value)
        with patch.object(cycle, '_publish', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.prepare()
        with patch.object(cycle, '_publish', side_effect=interrupt_receipt):
            with self.assertRaises(KeyboardInterrupt):
                self.prepare()
        stored = next((self.root / '.daodan/runs/workflow-fixture/context').glob('*/provider-result.json'))
        before = stored.read_bytes()
        result = self.prepare()
        self.assertEqual(stored.read_bytes(), before)
        self.assertTrue(cycle.verify_cycle(self.config, result['path'], token_counter=len, tokenizer_id='fixture-characters')['dispatch_allowed'])

    def test_changed_index_bytes_cannot_reuse_a_ready_packet(self):
        result = self.prepare()
        Path(self.manifest.parent / 'engine-edges.sqlite').write_bytes(b'appeared after preparation')
        with self.assertRaises(ValueError):
            cycle.verify_cycle(self.config, result['path'])

    def test_prepare_cannot_mutate_shared_snapshot_or_source(self):
        paths = [self.manifest, self.root / 'service.py', self.root / 'client.py']
        before = {str(p): p.read_bytes() for p in paths}
        result = self.prepare()
        self.assertEqual({str(p): p.read_bytes() for p in paths}, before)
        self.assertTrue(Path(result['path']).is_relative_to(self.root / '.daodan/runs/workflow-fixture'))

    def test_request_token_budget_is_checked_by_the_actual_recipient_counter(self):
        result = self.prepare()
        checked = cycle.verify_cycle(self.config, result['path'],
            token_counter=lambda _: 100001, tokenizer_id='fixture-characters')
        self.assertFalse(checked['dispatch_allowed'])
        self.assertEqual(checked['status'], 'needs_split')

    def test_source_mutation_during_recipient_verification_blocks_dispatch(self):
        result = self.prepare()
        def concurrent_edit(text):
            (self.root / 'service.py').write_bytes(b'def calculate(value):\n    return 9\n')
            return len(text)
        with self.assertRaises(ValueError):
            cycle.verify_cycle(self.config, result['path'], token_counter=concurrent_edit,
                               tokenizer_id='fixture-characters')

    def test_source_mutation_during_provider_preparation_has_no_delivery(self):
        invoke = cycle._invoke
        def concurrent_edit(config, owner, args, **options):
            result = invoke(config, owner, args, **options)
            if owner == 'provider':
                (self.root / 'service.py').write_bytes(b'def calculate(value):\n    return 9\n')
            return result
        with patch.object(cycle, '_invoke', side_effect=concurrent_edit):
            with self.assertRaises(ValueError):
                self.prepare()
        self.assertEqual(list((self.root / '.daodan/runs/workflow-fixture/context').glob('*/receipt.json')), [])

    def test_git_subproject_translates_scope_coordinates_without_widening_them(self):
        old = self.protocol('show')
        outer = self.root / 'outer'
        nested = outer / 'package'
        nested.mkdir(parents=True)
        for name in ['service.py', 'client.py', 'tests.py', 'README.md', 'secret.py']:
            (nested / name).write_bytes((self.root / name).read_bytes())
        subprocess.run(['git', 'init', '-q', str(outer)], capture_output=True, check=True)
        self.root = nested
        self.manifest = self.map_snapshot('nested')
        self.config.update(project=str(nested),
                           manifest=str(self.manifest), source_root=str(outer))
        payload = {k: old[k] for k in ['operation', 'objective', 'scope', 'authorizations', 'budget', 'waves', 'required_gates']}
        payload['waves'][0]['tasks'][0]['requirements'][0]['support'][0]['entity_id'] = 'package/service.py::calculate'
        self.protocol('init', payload)
        self.request['anchors'] = [{'entity_id': 'package/service.py::calculate'}]
        self.request['proposed_edits'] = [{'entity_id': 'package/service.py::calculate'}]
        result = self.prepare()
        receipt = self.receipt(result)
        self.assertEqual(receipt['write_set'], ['service.py'])
        self.assertEqual(receipt['request']['write_boundary'], ['package/service.py'])
        self.assertEqual(receipt['request']['read_boundary'],
            ['package/README.md', 'package/client.py', 'package/service.py', 'package/tests.py'])

    def test_adapter_cli_prepares_and_verifies_a_compact_receipt(self):
        args = [sys.executable, '-B', str(CYCLE), 'task-packet', '--task-id', 'T1']
        for name, value in [('config', self.config), ('request', self.request), ('recipient', self.recipient)]:
            path = self.root / (name + '.json')
            path.write_bytes(json.dumps(value).encode())
            args.extend(['--' + name, str(path)])
        prepared = subprocess.run(args, capture_output=True)
        self.assertEqual(prepared.returncode, 0, prepared.stderr.decode('utf8', 'replace'))
        result = json.loads(prepared.stdout)
        self.assertLess(len(prepared.stdout), 1000)
        checked = subprocess.run([sys.executable, '-B', str(CYCLE), 'verify',
            '--config', str(self.root / 'config.json'), '--receipt', result['path']], capture_output=True)
        self.assertEqual(checked.returncode, 0, checked.stderr.decode('utf8', 'replace'))
        self.assertEqual(json.loads(checked.stdout)['status'], 'needs_recipient_check')

    def test_adapter_cli_reports_missing_inputs_as_an_invocation_error(self):
        path = self.root / 'config.json'
        path.write_bytes(json.dumps(self.config).encode())
        result = subprocess.run([sys.executable, '-B', str(CYCLE), 'task-packet', '--config', str(path)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b'Traceback', result.stderr)

    def test_adapter_cli_reports_malformed_documents_as_an_invocation_error(self):
        config = self.root / 'config.json'
        request = self.root / 'request.json'
        recipient = self.root / 'recipient.json'
        request.write_bytes(b'[]')
        recipient.write_bytes(json.dumps(self.recipient).encode())
        config.write_bytes(b'[1, 2]')
        result = subprocess.run([sys.executable, '-B', str(CYCLE), 'task-packet', '--config', str(config),
            '--task-id', 'T1', '--request', str(request), '--recipient', str(recipient)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b'Traceback', result.stderr)
        config.write_bytes(json.dumps(self.config).encode())
        result = subprocess.run([sys.executable, '-B', str(CYCLE), 'task-packet', '--config', str(config),
            '--task-id', 'T1', '--request', str(request), '--recipient', str(recipient)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b'Traceback', result.stderr)

    def test_adapter_cli_reports_unreadable_receipt_as_an_invocation_error(self):
        path = self.root / 'config.json'
        path.write_bytes(json.dumps(self.config).encode())
        result = subprocess.run([sys.executable, '-B', str(CYCLE), 'verify', '--config', str(path),
            '--receipt', str(self.root / 'absent-receipt.json')], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b'Traceback', result.stderr)
        broken = self.root / 'broken-receipt.json'
        broken.write_bytes(b'{not json')
        result = subprocess.run([sys.executable, '-B', str(CYCLE), 'verify', '--config', str(path),
            '--receipt', str(broken)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b'Traceback', result.stderr)

    def test_base_manifest_conflicting_with_the_previous_receipt_is_refused(self):
        result = self.prepare()
        record, project, home = cycle._record(self.config)
        task = cycle._task(record, 'task-packet', 'T1')
        prior = cycle._read_receipt(result['path'], home)
        agreeing = dict(self.config, base_manifest=str(self.manifest))
        request, _, _ = cycle._request(record, agreeing, self.request, 'post-task', task, prior)
        self.assertEqual(request['base']['manifest'], str(self.manifest))
        conflict = dict(self.config, base_manifest=str(self.root / 'other-manifest.json'))
        with self.assertRaises(ValueError):
            cycle._request(record, conflict, self.request, 'post-task', task, prior)

    def test_exclusive_publication_refuses_different_evidence_bytes(self):
        path = self.root / 'evidence.json'
        cycle._publish(path, {'a': 1})
        cycle._publish(path, {'a': 1})
        path.write_bytes(b'{"a": 2}\n')
        with self.assertRaises(ValueError):
            cycle._publish(path, {'a': 1})

    def test_verify_never_reports_ready_when_the_slice_abstains(self):
        result = self.prepare()
        read = cycle._provider_artifacts
        def abstained(provider, request, project):
            packet, slice_ = read(provider, request, project)
            return packet, dict(slice_, status='abstain')
        with patch.object(cycle, '_provider_artifacts', side_effect=abstained):
            checked = cycle.verify_cycle(self.config, result['path'])
        self.assertFalse(checked['dispatch_allowed'])
        self.assertNotEqual(checked['status'], 'ready')

    def test_adapter_cli_reports_unreadable_inputs_as_an_invocation_error(self):
        path = self.root / 'config.json'
        path.write_bytes(json.dumps(self.config).encode())
        result = subprocess.run([sys.executable, '-B', str(CYCLE), 'task-packet', '--config', str(path),
            '--task-id', 'T1', '--request', str(self.root / 'absent.json'),
            '--recipient', str(self.root / 'absent-recipient.json')], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b'Traceback', result.stderr)


    def cli(self, operation, config=None, request=None, recipient=None, **extra):
        files = {'config': self.config if config is None else config,
                 'request': self.request if request is None else request,
                 'recipient': self.recipient if recipient is None else recipient}
        args = [sys.executable, '-B', str(CYCLE), operation]
        for name, value in {**files, **extra}.items():
            path = self.root / ('cli-' + name + '.json')
            path.write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())
            args.extend(['--' + name.replace('_', '-'), str(path)])
        return subprocess.run(args + ['--task-id', 'T1'] if operation != 'preflight' else args, capture_output=True)

    def test_wrong_element_types_are_invocation_errors_without_a_traceback(self):
        def request(**changes):
            return dict(self.request, **changes)
        def config(**changes):
            return dict(self.config, **changes)
        def recipient(**changes):
            return dict(self.recipient, **changes)
        cases = {
            'requirement is a number': dict(request=request(mandatory_requirements=[1])),
            'requirement is null': dict(request=request(mandatory_requirements=[None])),
            'requirement has no id': dict(request=request(mandatory_requirements=[{}])),
            'requirement id is a list': dict(request=request(mandatory_requirements=[{'id': [1]}])),
            'requirement id repeats': dict(request=request(required_gates=[{'id': 'g'}, {'id': 'g'}])),
            'gate is text': dict(request=request(required_gates=['a'])),
            'anchors hold text': dict(request=request(anchors=['x'])),
            'budget is a list': dict(request=request(budget=[])),
            'source_root is a number': dict(config=config(source_root=5)),
            'base_manifest is a list': dict(config=config(base_manifest=[1])),
            'protocol holds a number': dict(config=config(protocol=['python', 1])),
            'provider is empty': dict(config=config(provider=[])),
            'indexes is a list': dict(config=config(indexes=[])),
            'index path is a number': dict(config=config(indexes={'retrieval': 1})),
            'run_id is a number': dict(config=config(run_id=5)),
            'tokens are text': dict(recipient=recipient(available_tokens='5')),
            'reserve is negative': dict(recipient=recipient(reserve_tokens=-1)),
            'recipient has no id': dict(recipient={k: v for k, v in self.recipient.items() if k != 'id'}),
            'config nests without end': dict(config=b'[' * 200000),
        }
        for name, documents in cases.items():
            with self.subTest(name):
                result = self.cli('task-packet', **documents)
                self.assertEqual(result.returncode, 2, result.stderr.decode('utf8', 'replace')[-300:])
                self.assertNotIn(b'Traceback', result.stderr)

    def test_previous_receipt_that_is_unreadable_or_not_an_object_is_an_invocation_error(self):
        for name, content in {'text': b'{not json', 'array': b'[1]', 'number': b'5'}.items():
            with self.subTest(name):
                result = self.cli('post-task', previous=content)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn(b'Traceback', result.stderr)
        absent = subprocess.run([sys.executable, '-B', str(CYCLE), 'post-task', '--config', str(self.root / 'cli-config.json'),
            '--request', str(self.root / 'cli-request.json'), '--recipient', str(self.root / 'cli-recipient.json'),
            '--task-id', 'T1', '--previous', str(self.root / 'absent.json')], capture_output=True)
        self.assertEqual(absent.returncode, 2)

    def test_incomplete_deliveries_from_the_protocol_or_provider_are_refused_cleanly(self):
        for owner in ('provider', 'protocol'):
            for printed in ('[]', '{}', 'not json'):
                with self.subTest(owner=owner, printed=printed):
                    config = dict(self.config, **{owner: [sys.executable, '-c', 'print(' + repr(printed) + ')']})
                    result = self.cli('task-packet', config=config)
                    self.assertEqual(result.returncode, 1)
                    self.assertNotIn(b'Traceback', result.stderr)
                    self.assertIn(owner.encode(), result.stderr)

    def test_help_documents_every_input_the_cli_reads(self):
        text = subprocess.run([sys.executable, '-B', str(CYCLE), '--help'], capture_output=True).stdout.decode()
        for fragment in ('base_manifest', 'indexes', 'mandatory_requirements', 'policy_version',
                         'max_evaluations', 'tokenizer_id', 'needs_recipient_check', 'status 2',
                         'max_input_tokens', 'max_output_tokens', 'context.toml', 'ordered or marginal'):
            self.assertIn(fragment, text)

    def test_next_stage_refuses_a_map_refreshed_in_place_as_its_base(self):
        task = self.prepare()
        (self.root / 'service.py').write_bytes(b'def calculate(value, required):\n    return value + required\n')
        self.protocol('update', {'barrier': 'source changed'})
        snapshot.write_snapshot(self.root, self.manifest)
        with self.assertRaisesRegex(ValueError, 'Base map revision changed'):
            self.prepare('post-task', previous=task['path'])

    def test_base_rewritten_while_the_provider_runs_is_never_stamped_as_the_revision_used(self):
        task = self.prepare()
        (self.root / 'service.py').write_bytes(b'def calculate(value, required):\n    return value + required\n')
        self.protocol('update', {'barrier': 'source changed'})
        self.config['manifest'] = str(self.map_snapshot('changed'))
        invoke = cycle._invoke
        def rewrite_base(config, owner, args, **options):
            result = invoke(config, owner, args, **options)
            if owner == 'provider':
                self.manifest.write_bytes(self.manifest.read_bytes() + b'rewritten after the provider read it')
            return result
        with patch.object(cycle, '_invoke', side_effect=rewrite_base):
            with self.assertRaisesRegex(ValueError, 'Base map revision changed'):
                self.prepare('post-task', previous=task['path'])

    def test_moved_provider_inputs_start_a_new_attempt_and_keep_the_old_evidence(self):
        first = self.prepare()
        Path(self.manifest.parent / 'engine-edges.sqlite').write_bytes(b'appeared after preparation')
        with self.assertRaises(cycle.StaleInputs):
            cycle.verify_cycle(self.config, first['path'])
        second = self.prepare()
        self.assertNotEqual(second['path'], first['path'])
        self.assertTrue(Path(second['path']).parent.name.endswith('-a2'))
        self.assertTrue(Path(first['path']).is_file())
        self.assertEqual(self.prepare()['path'], second['path'])
        self.assertEqual(cycle.verify_cycle(self.config, second['path'])['status'], 'needs_recipient_check')

    def test_the_attempt_bound_applies_to_one_call_not_to_the_life_of_an_intent(self):
        engine = Path(self.manifest.parent / 'engine-edges.sqlite')
        paths = [self.prepare()['path']]
        with patch.object(cycle, 'ATTEMPTS', 2):
            for generation in (b'first change', b'second change', b'third change'):
                engine.write_bytes(generation)
                paths.append(self.prepare()['path'])
        self.assertEqual(len(set(paths)), 4)
        self.assertTrue(paths[-1].endswith('receipt.json') and '-a4' in Path(paths[-1]).parent.name)
        self.assertEqual(self.prepare()['path'], paths[-1])

    def test_a_receipt_is_identical_across_ledger_revisions(self):
        first = self.prepare()
        original = Path(first['path']).read_bytes()
        self.assertNotIn('origin_revision', json.loads(original))
        note = self.root / '.daodan/runs/workflow-fixture/note.txt'
        note.write_bytes(b'bookkeeping')
        self.protocol('update', {'deliveries': {'context': {'status': 'delivered', 'output': 'note.txt'}}})
        Path(first['path']).unlink()
        again = self.prepare()
        self.assertEqual((again['path'], Path(again['path']).read_bytes()), (first['path'], original))

    def test_claim_adopts_only_a_lost_race_and_propagates_other_refusals(self):
        with patch.object(cycle, '_publish', side_effect=ValueError('Out of range float values are not JSON compliant')):
            with self.assertRaisesRegex(ValueError, 'not JSON compliant'):
                cycle._claim(self.root / 'never.json', {'a': float('nan')})

    def test_non_json_constants_in_an_input_document_are_an_invocation_error(self):
        text = json.dumps(self.request).replace('"anchors": [', '"anchors": [{"x": NaN}, ', 1).encode()
        for name, documents in {'request': dict(request=text), 'recipient': dict(recipient=b'{"id": "x", "available_tokens": Infinity}')}.items():
            with self.subTest(name):
                result = self.cli('task-packet', **documents)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn(b'Traceback', result.stderr)

    def test_the_provider_call_may_run_for_the_requests_own_time_cap(self):
        real, limits = subprocess.run, {}

        def spy(command, *args, **options):
            limits['provider' if 'context' in command else 'protocol'] = options.get('timeout')
            return real(command, *args, **options)

        for seconds, expected in ((10, 120), (300, 300)):
            with self.subTest(max_seconds=seconds):
                self.request['budget']['max_seconds'] = seconds
                self.config['manifest'] = str(self.map_snapshot(f'cap-{seconds}'))
                limits.clear()
                with patch.object(cycle.subprocess, 'run', spy):
                    self.prepare('preflight')
                self.assertEqual(limits, {'protocol': 120, 'provider': expected})

    def test_concurrent_identical_preparations_converge_on_one_receipt(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda _: self.prepare(), range(3)))
        self.assertEqual(len({(r['path'], r['sha256']) for r in results}), 1)

    def test_first_writer_wins_and_a_conflict_with_no_stored_object_still_refuses(self):
        path = self.root / 'claimed.json'
        self.assertEqual(cycle._claim(path, {'a': 1}), {'a': 1})
        self.assertEqual(cycle._claim(path, {'a': 2}), {'a': 1})
        path.write_bytes(b'[1]\n')
        with self.assertRaises(ValueError):
            cycle._claim(path, {'a': 3})

    def test_a_publication_race_refuses_different_bytes_and_accepts_identical_ones(self):
        value = {'a': 1}
        for stored, accepted in ((b'{"a":2}\n', False), (cycle._bytes(value), True)):
            with self.subTest(accepted=accepted):
                path = self.root / ('race-%s.json' % accepted)
                def link(source, destination, stored=stored):
                    Path(destination).write_bytes(stored)
                    raise FileExistsError()
                with patch.object(cycle.os, 'link', side_effect=link):
                    if accepted:
                        cycle._publish(path, value)
                    else:
                        with self.assertRaises(ValueError):
                            cycle._publish(path, value)
                self.assertEqual(path.read_bytes(), stored)


if __name__ == '__main__':
    unittest.main()
