"""Review zone end to end: I3 request, writer policy, light gate, controller run."""
import copy
import tempfile
import unittest

from controller import Controller
from interfaces import InterfaceRejected, digest
from mock_selector import SECURITY, LightLlmGate, MockSelector
from writer import apply_selection, expand_review, selection_request

SEC_HUNK = {'id': 'H1', 'path': 'api/invoices.py',
            'text': '@router.get("/invoices/{invoice_id}")\n    return get(invoice_id, permission=user)'}
DATA_HUNK = {'id': 'H2', 'path': 'billing/discounts.py',
             'text': 'def apply_discount(amount, discount):\n    if discount >= 0:\n        UPDATE ledger SET balance = amount - discount'}
CODE = 'senior-review:code-auditor'
ROSTER = {'schema': 'daodan/review-roster/v1', 'roster': [CODE]}


def run_all(controller):
    while True:
        aid = controller.reserve('mock-coordinator', controller.show()['revision'])
        if aid is None:
            return controller.show()
        attempt = controller.show()['attempts'][aid]
        controller.start(aid, 'mock-coordinator', attempt['inputs'])
        node = controller.show()['plan']['nodes'][attempt['node']]
        outputs = {k: f'fixture-{k}' for k in node['produces']}
        controller.complete(f'done-{aid}', aid, 'fixture-candidate', 'pass',
                            outputs, node['writes'])


def run_review_flow(controller, hunks, selector, gate, max_reprep=1):
    """Selection, writer policy, gate, at most one re-preparation, then expansion."""
    request = selection_request('candidate-1', hunks, ROSTER)
    reps = 0
    while True:
        applied = apply_selection(request, selector.select(request, rep=reps > 0))
        verdict = gate.check(applied['roles'], hunks)
        if verdict['status'] != 'BLOCK':
            controller.init(expand_review(applied['roles']), units=100)
            run_all(controller)
            state = controller.show()
            controller.finish()
            return {'status': 'PASS', 'applied': applied, 'gate': verdict,
                    'repreps': reps, 'state': state}
        if reps >= max_reprep:
            return {'status': 'HUMAN_ESCALATION', 'applied': applied, 'gate': verdict,
                    'repreps': reps, 'state': None}
        reps += 1


class MockSelectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.c = Controller(self.temp.name)
        self.request = selection_request('candidate-1', [SEC_HUNK, DATA_HUNK], ROSTER)

    def test_selection_is_deterministic(self):
        first = MockSelector().select(self.request)
        second = MockSelector().select(self.request)
        self.assertEqual(first, second)
        roles = apply_selection(self.request, first)['roles']
        self.assertEqual(roles[0], CODE)
        for role in (SECURITY, 'senior-review:data-integrity-auditor',
                     'senior-review:premise-auditor'):
            self.assertIn(role, roles)

    def test_gate_passes_when_critical_present(self):
        applied = apply_selection(self.request, MockSelector('accurate').select(self.request))
        self.assertEqual(LightLlmGate().check(applied['roles'], [SEC_HUNK, DATA_HUNK])['status'], 'PASS')

    def test_gate_blocks_missing_critical_with_real_trigger(self):
        request = selection_request('candidate-1', [SEC_HUNK], ROSTER)
        applied = apply_selection(request, MockSelector('leaky').select(request))
        verdict = LightLlmGate().check(applied['roles'], [SEC_HUNK])
        self.assertEqual(verdict['status'], 'BLOCK')
        self.assertEqual(verdict['missing'], [SECURITY])

    def test_selection_without_citation_is_ignored_never_reassigned(self):
        request = selection_request('candidate-1', [SEC_HUNK], ROSTER)
        applied = apply_selection(request, MockSelector('uncited').select(request))
        self.assertEqual(applied['ignored'], [SECURITY])
        self.assertNotIn(SECURITY, applied['roles'])
        self.assertEqual(LightLlmGate().check(applied['roles'], [SEC_HUNK])['status'], 'BLOCK')

    def test_reprep_once_then_passes(self):
        selector = MockSelector('leaky')
        result = run_review_flow(self.c, [SEC_HUNK], selector, LightLlmGate())
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['repreps'], 1)
        self.assertEqual(selector.calls, 2)
        self.assertIsNone(result['state']['outcome'])

    def test_double_block_escalates_to_human_without_instantiating(self):
        result = run_review_flow(self.c, [SEC_HUNK], MockSelector('leaky'),
                                 LightLlmGate(), max_reprep=0)
        self.assertEqual(result['status'], 'HUMAN_ESCALATION')
        self.assertIsNone(result['state'])
        self.assertFalse(self.c.path.exists())

    def test_unavailable_selector_falls_back_to_floor_and_gate_still_blocks(self):
        selector = MockSelector('unavailable')
        result = run_review_flow(self.c, [SEC_HUNK], selector, LightLlmGate())
        self.assertEqual(result['applied']['roles'], [CODE])
        self.assertEqual(result['status'], 'HUMAN_ESCALATION')
        self.assertEqual(selector.calls, 2)

    def test_unknown_role_rejects_the_whole_response(self):
        response = MockSelector().select(self.request)
        response['decisions'].append({'role': 'senior-review:ghost-auditor', 'selected': True,
                                      'probability': 0.9, 'citation': 'H1'})
        with self.assertRaises(InterfaceRejected):
            apply_selection(self.request, response)

    def test_floor_role_cannot_be_dropped(self):
        response = MockSelector().select(self.request)
        for d in response['decisions']:
            if d['role'] == CODE:
                d.update(selected=False, citation=None)
        self.assertIn(CODE, apply_selection(self.request, response)['roles'])
        response['decisions'] = [d for d in response['decisions'] if d['role'] != CODE]
        self.assertIn(CODE, apply_selection(self.request, response)['roles'])

    def test_end_to_end_review_flow_completes(self):
        result = run_review_flow(self.c, [SEC_HUNK, DATA_HUNK],
                                 MockSelector('accurate'), LightLlmGate())
        self.assertEqual(result['status'], 'PASS')
        state = self.c.show()
        self.assertEqual((state['status'], state['outcome']), ('complete', 'VERIFIED_SUCCESS'))
        lenses = [n for n in state['plan']['nodes'].values() if n['op'] == 'REVIEW_LENS']
        self.assertEqual(len(lenses), len(result['applied']['roles']))

    def test_expansion_is_reproducible(self):
        roles = apply_selection(self.request, MockSelector().select(self.request))['roles']
        self.assertEqual(digest(expand_review(roles)), digest(expand_review(copy.deepcopy(roles))))

    def test_noisy_selector_creates_more_lenses_but_same_gate_result(self):
        request = selection_request('candidate-1', [SEC_HUNK], ROSTER)
        noisy = apply_selection(request, MockSelector('noisy').select(request))['roles']
        accurate = apply_selection(request, MockSelector('accurate').select(request))['roles']
        self.assertGreater(len(noisy), len(accurate))
        self.assertEqual(LightLlmGate().check(noisy, [SEC_HUNK])['status'], 'PASS')

    def test_budget_accounting_never_exceeds_limit(self):
        state = run_review_flow(self.c, [SEC_HUNK, DATA_HUNK],
                                MockSelector('accurate'), LightLlmGate())['state']
        self.assertGreater(state['budget']['used'], 0)
        self.assertLessEqual(state['budget']['used'], state['budget']['limit'])


if __name__ == '__main__':
    unittest.main()
