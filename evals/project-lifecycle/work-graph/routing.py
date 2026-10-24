"""Executor-side routing policy: the router proposes a tier, this decides.

Order of application (spec section 1.3, I4): deterministic nodes take no
model; the operator floor; the authorized ceiling; the host binding from the
probe; the budget fit of one pass. Judges are routed once and never
escalated, so a changed verdict can never be explained by a changed judge.
Tier weights are versioned policy, not measurements.
"""
from __future__ import annotations

from interfaces import TIERS, InterfaceRejected, digest, validate_routing
from policy import CRITICAL_ROLES

TIER_COST = {'tier1': 1, 'tier2': 3, 'tier3': 8}
ROUTER_CALL_COST = 1
DETERMINISTIC_OPS = {'MAP_SLICE', 'CONTRACT_CHECK', 'WAVE_BARRIER', 'INTEGRATE'}
JUDGE_OPS = {'VERIFY_FINDING'}
OP_FLOOR = {'SPEC_ADR': 'tier2', 'PLAN': 'tier2', 'VERIFY_FINDING': 'tier2'}
DEFAULT_TIER = 'tier2'
DEFAULT_EFFORT = 'medium'
# Structural levers of the mother specification, applied even when the model is inherited.
PACKET_POLICY = {
    'tier1': {'hop_depth': 1, 'direct_output': True, 'invariant_table': False},
    'tier2': {'hop_depth': 1, 'direct_output': False, 'invariant_table': False},
    'tier3': {'hop_depth': 2, 'direct_output': False, 'invariant_table': True},
}
UNROUTED = {'tier': None, 'effort': None, 'model_param': None, 'effort_applied': None,
            'packet_policy': None, 'cost': 1, 'floor': None, 'proposed': None, 'judge': False}


class RoutingBlocked(ValueError):
    def __init__(self, outcome, reason):
        super().__init__(f'{outcome}: {reason}')
        self.outcome = outcome


def rank(tier):
    return TIERS.index(tier)


def floor_for(node):
    if node['op'] in DETERMINISTIC_OPS:
        return None
    if node['op'] == 'REVIEW_LENS' and node.get('role') in CRITICAL_ROLES:
        return 'tier2'
    return OP_FLOOR.get(node['op'], 'tier1')


def routing_request(plan):
    """The I4 request: one entry per model node in compiled order, with DAG facts."""
    dependents = {nid: set() for nid in plan['nodes']}
    for nid, deps in plan['edges'].items():
        for dep in deps:
            dependents[dep].add(nid)

    def downstream(nid):
        seen, stack = set(), [nid]
        while stack:
            for nxt in dependents[stack.pop()] - seen:
                seen.add(nxt)
                stack.append(nxt)
        return len(seen)

    nodes = []
    for nid in plan['order']:
        node = plan['nodes'][nid]
        if node['op'] in DETERMINISTIC_OPS:
            continue
        nodes.append({'id': nid, 'op': node['op'], 'text': node.get('text', ''),
                      'role': node.get('role'),
                      'facts': {'downstream': downstream(nid), 'fanin': len(plan['edges'][nid])}})
    return {'plan_digest': digest(plan), 'nodes': nodes}


def escalation_request(plan, nid, entry, attempt):
    nodes = [n for n in routing_request(plan)['nodes'] if n['id'] == nid]
    return {'plan_digest': digest(plan), 'nodes': nodes,
            'escalation': {'current_tier': entry['tier'], 'attempt': attempt}}


def bind(tier, effort, probe):
    """Resolve a tier through the host binding; an inherited model is charged at the session tier."""
    binding = probe['bindings'][tier]
    model = binding['model_param']
    charged = tier if model is not None else (probe.get('session_tier') or TIERS[-1])
    return {'tier': tier, 'effort': effort, 'model_param': model,
            'effort_applied': effort if binding['native_effort'] else None,
            'packet_policy': PACKET_POLICY[tier], 'cost': TIER_COST[charged]}


def resolve_routing(plan, response, probe, ceiling, units):
    if ceiling not in TIERS:
        raise RoutingBlocked('POLICY_BLOCKED', f'unknown ceiling {ceiling}')
    try:
        validate_routing(response, routing_request(plan))
        proposed, rejected = {d['node']: d for d in response['decisions']}, None
    except InterfaceRejected as exc:
        proposed, rejected = {}, str(exc)
    nodes = {}
    for nid in plan['order']:
        node = plan['nodes'][nid]
        floor = floor_for(node)
        if floor is None:
            nodes[nid] = dict(UNROUTED)
            continue
        if rank(floor) > rank(ceiling):
            raise RoutingBlocked('POLICY_BLOCKED', f'{nid} needs {floor}, authorized {ceiling}')
        decision = proposed.get(nid, {})
        wanted = decision.get('tier') or max(floor, DEFAULT_TIER, key=rank)
        tier = TIERS[min(max(rank(wanted), rank(floor)), rank(ceiling))]
        nodes[nid] = dict(bind(tier, decision.get('effort') or DEFAULT_EFFORT, probe),
                          floor=floor, proposed=decision.get('tier'),
                          judge=node['op'] in JUDGE_OPS)

    def expected():
        # One pass: every dispatch, one verification per node and the router call.
        return sum(e['cost'] for e in nodes.values()) + len(nodes) + ROUTER_CALL_COST

    downgraded = []
    while expected() > units:
        movable = [nid for nid, e in nodes.items() if e['tier'] and e['model_param'] is not None
                   and rank(e['tier']) > rank(e['floor'])]
        if not movable:
            raise RoutingBlocked('BUDGET_EXHAUSTED', f'floors need {expected()} units, limit {units}')
        nid = max(movable, key=lambda n: (nodes[n]['cost'], n))
        entry = nodes[nid]
        nodes[nid] = dict(entry, **bind(TIERS[rank(entry['tier']) - 1], entry['effort'], probe))
        downgraded.append(nid)
    return {'response': response, 'probe': probe, 'ceiling': ceiling, 'rejected': rejected,
            'nodes': nodes, 'expected_cost': expected(), 'downgraded': downgraded,
            'escalations': []}


def escalate_entry(entry, nid, response, request, probe, ceiling):
    """Apply an escalation proposal to one node; raise when policy forbids it."""
    if entry['tier'] is None or entry['judge']:
        raise RoutingBlocked('POLICY_BLOCKED', f'{nid}: judges and deterministic nodes are never escalated')
    validate_routing(response, request)
    decision = {d['node']: d for d in response['decisions']}.get(nid, {})
    tier = decision.get('tier')
    if tier is None or rank(tier) <= rank(entry['tier']) or rank(tier) > rank(ceiling):
        raise RoutingBlocked('POLICY_BLOCKED',
                             f"{nid}: no escalation above {entry['tier']} within {ceiling}")
    return dict(entry, **bind(tier, decision.get('effort') or entry['effort'], probe), proposed=tier)
