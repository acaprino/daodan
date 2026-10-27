import copy
import json
from pathlib import Path
import tempfile
import unittest

from campaign_ledger import Ledger, MAX_SECONDS, MODEL, digest, validate_response


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = 1000
        self.commits = 0
        self.request = {'id': 'abc123', 'body': {'model': MODEL, 'state': 'data',
                        'questions': {'q': {'type': 'noul', 'instructions': 'Keep?'}}}}
        self.response = {'model': MODEL, 'answers': {'q': {'type': 'noul', 'noul': 0.4}}}

    def ledger(self, **kwargs):
        def commit():
            self.commits += 1
        return Ledger(self.root, kwargs.get('input_hash', 'input'), 'code',
                      commit=commit, clock=lambda: self.now)

    def test_commit_precedes_dispatch_and_finished_request_is_not_retried(self):
        ledger = self.ledger()
        ledger.begin(self.request)
        durable = json.loads((self.root / 'ledger.json').read_text())
        self.assertEqual(durable['attempted_questions'], 1)
        self.assertEqual(durable['requests']['abc123']['status'], 'running')
        self.assertEqual(self.commits, 2)
        ledger.finish(self.request, {'status': 'delivered', 'response': self.response})
        resumed = self.ledger()
        self.assertEqual(resumed.existing(self.request)['response'], self.response)
        with self.assertRaises(ValueError):
            resumed.begin(self.request)
        self.assertEqual(resumed.state['attempted_questions'], 1)
        self.assertEqual(resumed.state['completed_requests'], 1)
        self.assertEqual(resumed.state['requests'], {})

    def test_crash_does_not_silently_repeat_unknown_paid_inference(self):
        self.ledger().begin(self.request)
        resumed = self.ledger()
        with self.assertRaisesRegex(RuntimeError, 'Unresolved inference'):
            resumed.existing(self.request)
        self.assertEqual(resumed.state['requests']['abc123']['status'], 'unknown')

    def test_deadline_and_question_reserve_survive_restart(self):
        self.ledger().reserve_startup(50000)
        with self.assertRaisesRegex(RuntimeError, 'question budget'):
            self.ledger().begin(self.request)
        self.now += MAX_SECONDS
        with self.assertRaises(TimeoutError):
            self.ledger().check_budget()

    def test_resume_refuses_changed_input_or_response_provenance(self):
        ledger = self.ledger()
        with self.assertRaises(ValueError):
            self.ledger(input_hash='different')
        ledger.begin(self.request)
        ledger.finish(self.request, {'status': 'delivered', 'response': self.response})
        changed = copy.deepcopy(self.request)
        changed['body']['state'] = 'changed'
        with self.assertRaises(ValueError):
            ledger.existing(changed)

    def test_invalid_probability_and_model_never_become_negative_decisions(self):
        for value in [None, True, -0.1, 1.1, float('nan')]:
            bad = copy.deepcopy(self.response)
            bad['answers']['q']['noul'] = value
            with self.assertRaises(ValueError):
                validate_response(self.request['body'], bad)
        bad = {**self.response, 'model': 'default-q8'}
        with self.assertRaises(ValueError):
            validate_response(self.request['body'], bad)

    def test_path_traversal_refused(self):
        with self.assertRaises(ValueError):
            self.ledger().record_path('../another-run')


if __name__ == '__main__':
    unittest.main()
