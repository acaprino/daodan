"""Executor-side routing policy (I4) with the mocked router: AC22-AC24."""
import copy
import tempfile
import unittest

from controller import Controller, Rejected, compile_plan
from interfaces import TIERS
from mock_router import MockRouter
from routing import PACKET_POLICY, TIER_COST, RoutingBlocked, resolve_routing, routing_request
from writer import expand_review

CLAUDE = {'host': 'claude', 'session_tier': 'tier3', 'bindings': {
    'tier1': {'model_param': 'haiku', 'native_effort': False},
    'tier2': {'model_param': 'sonnet', 'native_effort': False},
    'tier3': {'model_param': 'opus', 'native_effort': False}}}
OPENCODE = {'host': 'opencode', 'session_tier': 'tier2', 'bindings': {
    t: {'model_param': f'provider/model-{t}', 'native_effort': True} for t in TIERS}}
COPILOT = {'host': 'copilot', 'session_tier': None, 'bindings': {
    t: {'model_param': None, 'native_effort': False} for t in TIERS}}
SECURITY = 'senior-review:security-auditor'
CODE = 'senior-review:code-auditor'


def node(nid, op, consumes=(), produces=(), writes=()):
    return {'id': nid, 'op': op, 'gate': 'fixture-verifier/v1', 'consumes': list(consumes),
            'produces': list(produces), 'writes': list(writes)}


def bugfix_plan(with_plan=True):
    nodes = [node('red', 'ORACLE_RED', ['plan'] if with_plan else [], ['oracle'], ['tests/test_search.py']),
             node('patch', 'CODE_PATCH', ['oracle'], ['patch'], ['functions-python/search.py']),
             node('check', 'CONTRACT_CHECK', ['patch'], ['contract-report'])]
    if with_plan:
        nodes.insert(0, node('plan', 'PLAN', produces=['plan']))
    return compile_plan(nodes, 'bugfix_repro_first')


def route(plan, router, probe=CLAUDE, ceiling='tier3', units=60):
    return resolve_routing(plan, router.route(routing_request(plan)), probe, ceiling, units)


def drive(c, verdicts=None):
    """Run ready nodes until none is left or one fails; verdicts lists per-attempt results."""
    verdicts = verdicts or {}
    while True:
        aid = c.reserve('h', c.show()['revision'])
        if aid is None:
            return c.show()
        attempt = c.show()['attempts'][aid]
        c.start(aid, 'h', attempt['inputs'])
        n = c.show()['plan']['nodes'][attempt['node']]
        planned = verdicts.get(attempt['node'], [])
        index = int(aid.rsplit(':', 1)[1]) - 1
        verdict = planned[index] if index < len(planned) else 'pass'
        c.complete(f'done-{aid}', aid, f'candidate-{aid}', verdict,
                   {k: f'{k}-{aid}' for k in n['produces']}, n['writes'])
        if verdict == 'fail':
            return c.show()


class RoutingPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.c = Controller(self.temp.name)

    def tiers(self, routing):
        return {nid: e['tier'] for nid, e in routing['nodes'].items()}

    def test_one_router_call_per_plan_and_exact_charging(self):
        router = MockRouter()
        plan = bugfix_plan()
        routing = route(plan, router)
        self.c.init(plan, units=60, routing=routing)
        state = drive(self.c)
        self.c.finish()
        self.assertEqual(router.calls, 1)
        self.assertEqual(state['budget']['used'], routing['expected_cost'])
        self.assertEqual(self.c.show()['outcome'], 'VERIFIED_SUCCESS')

    def test_floor_raises_cheap_proposals(self):
        self.assertEqual(self.tiers(route(bugfix_plan(), MockRouter('cheap'))),
                         {'plan': 'tier2', 'red': 'tier1', 'patch': 'tier1', 'check': None})
        review = route(expand_review([CODE, SECURITY]), MockRouter('cheap'))
        self.assertEqual(self.tiers(review), {
            'lens-code': 'tier1', 'lens-security': 'tier2', 'verify-code': 'tier2',
            'verify-security': 'tier2', 'barrier': None})

    def test_ceiling_caps_greedy_proposals(self):
        tiers = self.tiers(route(bugfix_plan(), MockRouter('greedy'), ceiling='tier2'))
        self.assertEqual(tiers, {'plan': 'tier2', 'red': 'tier2', 'patch': 'tier2', 'check': None})

    def test_floor_above_ceiling_blocks_before_spending(self):
        with self.assertRaises(RoutingBlocked) as ctx:
            route(bugfix_plan(), MockRouter(), ceiling='tier1')
        self.assertEqual(ctx.exception.outcome, 'POLICY_BLOCKED')
        self.assertFalse(self.c.path.exists())

    def test_abstain_unavailable_and_malformed_use_the_default_never_weaker(self):
        for persona in ('abstain', 'unavailable', 'malformed'):
            routing = route(bugfix_plan(), MockRouter(persona))
            self.assertEqual(self.tiers(routing),
                             {'plan': 'tier2', 'red': 'tier2', 'patch': 'tier2', 'check': None}, persona)
            self.assertEqual(routing['rejected'] is not None, persona == 'malformed')

    def test_deterministic_nodes_take_no_model(self):
        entry = route(bugfix_plan(), MockRouter('greedy'))['nodes']['check']
        self.assertEqual((entry['tier'], entry['model_param'], entry['cost']), (None, None, 1))

    def test_host_binding_resolves_model_and_native_effort(self):
        claude = route(bugfix_plan(), MockRouter())['nodes']['plan']
        self.assertEqual((claude['model_param'], claude['effort_applied']), ('sonnet', None))
        opencode = route(bugfix_plan(), MockRouter(), probe=OPENCODE)['nodes']['plan']
        self.assertEqual((opencode['model_param'], opencode['effort_applied']),
                         ('provider/model-tier2', 'medium'))

    def test_host_without_override_inherits_and_charges_session_tier(self):
        unknown = route(bugfix_plan(), MockRouter(), probe=COPILOT)['nodes']
        self.assertEqual(unknown['plan']['model_param'], None)
        self.assertEqual(unknown['plan']['packet_policy'], PACKET_POLICY['tier2'])
        self.assertEqual(unknown['red']['cost'], TIER_COST['tier3'])
        light_session = dict(COPILOT, session_tier='tier1')
        known = route(bugfix_plan(), MockRouter(), probe=light_session)['nodes']
        # The floor guarantees the packet, not the inherited model.
        self.assertEqual((known['plan']['tier'], known['plan']['cost']), ('tier2', TIER_COST['tier1']))

    def test_budget_fit_downgrades_never_below_floor(self):
        routing = route(bugfix_plan(), MockRouter('greedy'), units=16)
        self.assertTrue(routing['downgraded'])
        self.assertLessEqual(routing['expected_cost'], 16)
        for entry in routing['nodes'].values():
            if entry['tier']:
                self.assertGreaterEqual(TIERS.index(entry['tier']), TIERS.index(entry['floor']))

    def test_budget_below_floors_blocks_before_spending(self):
        with self.assertRaises(RoutingBlocked) as ctx:
            route(bugfix_plan(), MockRouter('greedy'), units=8)
        self.assertEqual(ctx.exception.outcome, 'BUDGET_EXHAUSTED')

    def test_tampered_routing_is_rejected(self):
        plan = bugfix_plan()
        routing = route(plan, MockRouter())
        tampered = copy.deepcopy(routing)
        tampered['nodes']['plan'].update(tier='tier1', cost=TIER_COST['tier1'])
        with self.assertRaises(Rejected):
            self.c.init(plan, units=60, routing=tampered)
        with self.assertRaises(Rejected):
            self.c.init(plan, units=10, routing=routing)

    def test_escalation_then_same_failure_stalls_with_unchanged_fingerprint(self):
        router = MockRouter()
        plan = bugfix_plan()
        self.c.init(plan, units=60, routing=route(plan, router))
        drive(self.c, {'red': ['fail', 'fail']})
        before = self.c.show()
        self.assertTrue(self.c.escalate('red', router.escalate(self.c.escalation_request('red')),
                                        before['revision']))
        after_escalation = self.c.show()
        self.assertEqual(after_escalation['graph_digest'], before['graph_digest'])
        self.assertEqual(after_escalation['failures'], before['failures'])
        self.assertEqual(after_escalation['budget']['used'], before['budget']['used'] + 1)
        state = drive(self.c, {'red': ['fail', 'fail']})
        self.assertEqual((state['status'], state['outcome']), ('stopped', 'STALLED_SAME_FAILURE'))
        self.assertEqual([state['attempts'][a]['routing']['tier'] for a in ('red:1', 'red:2')],
                         ['tier1', 'tier2'])
        # init router call + plan 3+1 + red 1+1 + escalation call + red 3+1
        self.assertEqual(state['budget']['used'], 12)
        self.assertEqual(router.calls, 2)

    def test_judge_is_never_escalated(self):
        router = MockRouter()
        plan = expand_review([CODE, SECURITY])
        self.c.init(plan, units=60, routing=route(plan, router))
        state = drive(self.c, {'verify-security': ['fail']})
        self.assertEqual(state['nodes']['verify-security'], 'failed')
        response = router.escalate(self.c.escalation_request('verify-security'))
        with self.assertRaises(Rejected):
            self.c.escalate('verify-security', response, state['revision'])
        self.assertEqual(self.c.show()['revision'], state['revision'])

    def test_escalation_above_ceiling_is_unavailable_and_changes_nothing(self):
        router = MockRouter()
        plan = bugfix_plan(with_plan=False)
        self.c.init(plan, units=60, routing=route(plan, router, ceiling='tier1'))
        state = drive(self.c, {'red': ['fail']})
        with self.assertRaises(Rejected):
            self.c.escalate('red', router.escalate(self.c.escalation_request('red')), state['revision'])
        self.assertEqual(self.c.show(), state)

    def test_escalation_on_inherit_host_changes_packet_not_model(self):
        router = MockRouter()
        plan = bugfix_plan()
        self.c.init(plan, units=80, routing=route(plan, router, probe=COPILOT, units=80))
        state = drive(self.c, {'red': ['fail']})
        self.c.escalate('red', router.escalate(self.c.escalation_request('red')), state['revision'])
        entry = self.c.show()['routing']['nodes']['red']
        self.assertEqual((entry['tier'], entry['model_param'], entry['cost']),
                         ('tier2', None, TIER_COST['tier3']))
        self.assertEqual(entry['packet_policy'], PACKET_POLICY['tier2'])

    def test_escalation_response_for_another_request_is_rejected(self):
        router = MockRouter()
        plan = bugfix_plan()
        self.c.init(plan, units=60, routing=route(plan, router))
        state = drive(self.c, {'red': ['fail']})
        with self.assertRaises(Rejected):
            self.c.escalate('red', router.route(routing_request(plan)), state['revision'])
        self.assertEqual(self.c.show(), state)


if __name__ == '__main__':
    unittest.main()
