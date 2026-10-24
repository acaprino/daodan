"""Isolated work-graph reference experiment. No worker, model or shell dispatch."""
from __future__ import annotations

import copy
from contextlib import contextmanager
import json
import os
from pathlib import Path
import time
from graphlib import TopologicalSorter

from interfaces import InterfaceRejected, digest
from routing import (ROUTER_CALL_COST, RoutingBlocked, escalate_entry, escalation_request,
                     resolve_routing)


class Rejected(ValueError):
    pass


OPS = {
    'MAP_SLICE', 'SPEC_ADR', 'ANALYZE', 'PLAN', 'ORACLE_RED', 'CODE_PATCH',
    'EDIT_ARTIFACT', 'CONTRACT_CHECK', 'REVIEW_LENS', 'VERIFY_FINDING',
    'REPAIR_PATCH', 'WAVE_BARRIER', 'INTEGRATE',
}
READ_ONLY = {'analysis_only', 'planning_only', 'review_only'}
ARCHETYPES = READ_ONLY | {
    'bugfix_repro_first', 'contract_callee_to_caller', 'db_migration_two_phase',
    'pure_refactor', 'ui_async_flow', 'artifact_edit',
}


def compile_plan(nodes, archetype='bugfix_repro_first'):
    """Compile an explicit fixture plan; never infer intent from call edges."""
    if archetype not in ARCHETYPES:
        raise Rejected('unknown archetype')
    by_id = {n['id']: copy.deepcopy(n) for n in sorted(nodes, key=lambda n: n['id'])}
    if len(by_id) != len(nodes) or not nodes:
        raise Rejected('empty plan or duplicate node')
    producers = {}
    for n in by_id.values():
        if n['op'] not in OPS or not n.get('gate'):
            raise Rejected('operator or gate missing')
        if archetype in READ_ONLY and (n.get('writes') or n['op'] in {
            'CODE_PATCH', 'REPAIR_PATCH', 'EDIT_ARTIFACT', 'INTEGRATE',
        }):
            raise Rejected('read-only scope')
        for field in ('needs', 'consumes', 'produces', 'writes', 'reads', 'locks'):
            n.setdefault(field, [])
            if len(n[field]) != len(set(n[field])):
                raise Rejected('duplicate reference')
        for artifact in n['produces']:
            if artifact in producers:
                raise Rejected('duplicate producer')
            producers[artifact] = n['id']
    edges = {}
    for nid, n in by_id.items():
        if set(n['needs']) - by_id.keys() or set(n['consumes']) - producers.keys():
            raise Rejected('unresolved dependency')
        edges[nid] = set(n['needs']) | {producers[a] for a in n['consumes']}
    try:
        order = list(TopologicalSorter({k: sorted(v) for k, v in edges.items()}).static_order())
    except ValueError as exc:
        raise Rejected('cycle') from exc
    body = {'archetype': archetype, 'nodes': by_id, 'order': order,
            'edges': {k: sorted(v) for k, v in edges.items()}}
    return body


class Controller:
    """Single JSON authority; exclusive lock fails closed on abandoned ownership.

    Gates and clock are fixture inputs, not authenticated host evidence. Filesystem
    crash durability, adversarial confinement and real process leases are not proved.
    """
    def __init__(self, root, clock=time.time):
        self.root = Path(root)
        self.path = self.root / 'work.json'
        self.lock = self.root / 'writer.lock'
        self.clock = clock

    @contextmanager
    def transaction(self):
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise Rejected('writer busy; reconcile stale lock explicitly') from exc
        try:
            os.close(fd)
            state = json.loads(self.path.read_text()) if self.path.exists() else {}
            before = copy.deepcopy(state)
            yield state
            if state != before:
                state['revision'] = before.get('revision', -1) + 1
                temp = self.root / 'work.pending'
                with temp.open('w', encoding='utf-8') as out:
                    json.dump(state, out, sort_keys=True, allow_nan=False)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(temp, self.path)
        finally:
            self.lock.unlink()

    def show(self):
        return json.loads(self.path.read_text())

    def init(self, plan, units=50, seconds=3600, max_attempts=3, max_replans=2, routing=None):
        if plan != compile_plan(list(plan['nodes'].values()), plan['archetype']):
            raise Rejected('unvalidated plan')
        if min(units, seconds, max_attempts) <= 0 or max_replans < 0:
            raise Rejected('invalid limits')
        if routing is not None:
            # Same rule as the plan: only a table the policy reproduces is admitted.
            try:
                expected = resolve_routing(plan, routing['response'], routing['probe'],
                                           routing['ceiling'], units)
            except (RoutingBlocked, KeyError, TypeError) as exc:
                raise Rejected('unvalidated routing') from exc
            if routing != expected:
                raise Rejected('unvalidated routing')
        with self.transaction() as s:
            if s:
                raise Rejected('existing run')
            s.update(schema='work-graph-experiment/v1', plan=plan,
                     graph_digest=digest(plan), graphs=[digest(plan)], status='in_progress',
                     outcome=None, nodes={n: 'pending' for n in plan['nodes']},
                     budget={'limit': units, 'used': ROUTER_CALL_COST if routing else 0,
                             'deadline': self.clock()+seconds,
                             'max_attempts': max_attempts, 'max_replans': max_replans},
                     attempts={}, counters={}, deliveries={}, artifacts={}, events={},
                     replans=0, verifications={}, failures={}, last_time=self.clock(),
                     routing=routing)

    def admit(self, s, cost):
        if s['status'] != 'in_progress':
            raise Rejected('run not active')
        now = self.clock()
        if now < s['last_time']:
            s.update(status='stopped', outcome='ENVIRONMENT_BLOCKED')
            return False
        s['last_time'] = now
        if now >= s['budget']['deadline'] or s['budget']['used']+cost > s['budget']['limit']:
            s.update(status='stopped', outcome='BUDGET_EXHAUSTED')
            return False
        s['budget']['used'] += cost
        return True

    def reserve(self, holder, expected_revision):
        with self.transaction() as s:
            if s['revision'] != expected_revision:
                raise Rejected('CAS mismatch')
            if not self.admit(s, 0):
                return None
            # This first experiment intentionally serializes all worker writes.
            if any(a['status'] in ('reserved', 'running') for a in s['attempts'].values()):
                return None
            for nid in s['plan']['order']:
                if s['nodes'][nid] not in ('pending', 'stale', 'failed'):
                    continue
                if any(s['nodes'][d] != 'succeeded' for d in s['plan']['edges'][nid]):
                    continue
                count = s['counters'].get(nid, 0)
                if count >= s['budget']['max_attempts']:
                    s.update(status='stopped', outcome='BUDGET_EXHAUSTED')
                    return None
                routing = s.get('routing')
                if not self.admit(s, routing['nodes'][nid]['cost'] if routing else 1):
                    return None
                s['counters'][nid] = count+1
                aid = f'{nid}:{count+1}'
                inputs = {k: s['artifacts'][k]['digest'] for k in s['plan']['nodes'][nid]['consumes']}
                s['attempts'][aid] = {'node': nid, 'holder': holder, 'status': 'reserved',
                                      'graph': s['graph_digest'], 'inputs': inputs,
                                      'expires': self.clock()+60}
                if routing:
                    # The tier lives in the attempt; the graph digest never changes with it.
                    s['attempts'][aid]['routing'] = {
                        k: routing['nodes'][nid][k]
                        for k in ('tier', 'effort', 'model_param', 'effort_applied', 'packet_policy')}
                s['nodes'][nid] = 'reserved'
                return aid
            return None

    def start(self, aid, holder, packet_inputs):
        with self.transaction() as s:
            a = s['attempts'][aid]
            if not self.admit(s, 0):
                return False
            if a['status'] != 'reserved' or a['holder'] != holder:
                raise Rejected('invalid reservation')
            if self.clock() >= a['expires']:
                a['status'] = 'revoked'
                s['nodes'][a['node']] = 'pending'
                return False
            current = {k: s['artifacts'][k]['digest'] for k in a['inputs']}
            if packet_inputs != a['inputs'] or current != a['inputs'] or a['graph'] != s['graph_digest']:
                raise Rejected('stale packet')
            a['status'] = 'running'
            s['nodes'][a['node']] = 'running'
            return True

    def complete(self, event_id, aid, candidate, verdict, outputs, changed_paths=()):
        payload = dict(aid=aid, candidate=candidate, verdict=verdict,
                       outputs=outputs, changed_paths=list(changed_paths))
        signature = digest(payload)
        with self.transaction() as s:
            if event_id in s['events']:
                if s['events'][event_id] != signature:
                    raise Rejected('event payload changed')
                return
            a = s['attempts'][aid]
            n = s['plan']['nodes'][a['node']]
            if a['status'] != 'running' or a['graph'] != s['graph_digest']:
                raise Rejected('inactive or stale attempt')
            if verdict not in ('pass', 'fail') or not candidate:
                raise Rejected('invalid gate fixture')
            if set(changed_paths) - set(n['writes']) or set(outputs) != set(n['produces']):
                raise Rejected('scope or output contract mismatch')
            if not self.admit(s, 1):
                return
            s['events'][event_id] = signature
            key = digest([n['gate'], candidate, a['inputs']])
            prior = s['verifications'].get(key)
            s['verifications'][key] = verdict
            if prior is not None and prior != verdict:
                s.update(status='stopped', outcome='VERIFIER_UNSTABLE')
            a['status'] = 'delivered'
            s['deliveries'][aid] = payload
            if verdict == 'fail':
                s['nodes'][a['node']] = 'failed'
                fingerprint = digest([n['gate'], a['node'], 'fixture-failure'])
                s['failures'][fingerprint] = s['failures'].get(fingerprint, 0)+1
                if s['failures'][fingerprint] >= 2 and s['status'] != 'stopped':
                    s.update(status='stopped', outcome='STALLED_SAME_FAILURE')
                return
            if s['status'] == 'stopped':
                return
            for name, content in outputs.items():
                old = s['artifacts'].get(name)
                new_hash = digest(content)
                version = old['version']+1 if old else 1
                s['artifacts'][name] = {'digest': new_hash, 'version': version, 'delivery': aid}
            s['nodes'][a['node']] = 'succeeded'

    def replan(self, plan, expected_revision):
        if plan != compile_plan(list(plan['nodes'].values()), plan['archetype']):
            raise Rejected('unvalidated plan')
        with self.transaction() as s:
            if s['revision'] != expected_revision:
                raise Rejected('CAS mismatch')
            if s['status'] != 'in_progress':
                raise Rejected('run not active')
            if any(a['status'] == 'running' for a in s['attempts'].values()):
                raise Rejected('worker in flight')
            if s['replans'] >= s['budget']['max_replans']:
                s.update(status='stopped', outcome='BUDGET_EXHAUSTED')
                return
            # Restrict this prototype to stable IDs; future lineage migrations need their own proof.
            if set(plan['nodes']) != set(s['plan']['nodes']):
                raise Rejected('node lineage change unsupported')
            if not self.admit(s, 1):
                return
            for a in s['attempts'].values():
                if a['status'] == 'reserved':
                    a['status'] = 'revoked'
            s['replans'] += 1
            s['plan'] = plan
            s['graph_digest'] = digest(plan)
            s['graphs'].append(digest(plan))
            # Conservative barrier-wide invalidation. No claim of selective read-set completeness.
            s['nodes'] = {nid: 'stale' for nid in plan['nodes']}

    def escalation_request(self, nid):
        s = self.show()
        entry = (s.get('routing') or {'nodes': {}})['nodes'].get(nid)
        if entry is None or entry['tier'] is None:
            raise Rejected('node has no model routing')
        return escalation_request(s['plan'], nid, entry, f"{nid}:{s['counters'].get(nid, 0)}")

    def escalate(self, nid, response, expected_revision):
        """Apply a router escalation to a failed node; the failure fingerprint is untouched."""
        with self.transaction() as s:
            if s['revision'] != expected_revision:
                raise Rejected('CAS mismatch')
            if s['status'] != 'in_progress':
                raise Rejected('run not active')
            routing = s.get('routing')
            if not routing or s['nodes'].get(nid) != 'failed':
                raise Rejected('escalation needs a routed failed node')
            entry = routing['nodes'][nid]
            request = escalation_request(s['plan'], nid, entry, f"{nid}:{s['counters'][nid]}")
            try:
                new = escalate_entry(entry, nid, response, request, routing['probe'],
                                     routing['ceiling'])
            except (RoutingBlocked, InterfaceRejected) as exc:
                raise Rejected(str(exc)) from exc
            if not self.admit(s, ROUTER_CALL_COST):
                return False
            routing['nodes'][nid] = new
            routing['escalations'].append({'node': nid, 'tier': new['tier'],
                                           'decision_id': response['decision_id']})
            return True

    def resume(self):
        with self.transaction() as s:
            if s['status'] != 'in_progress':
                return
            for a in s['attempts'].values():
                if a['status'] == 'running':
                    s.update(status='stopped', outcome='ENVIRONMENT_BLOCKED')
                elif a['status'] == 'reserved':
                    a['status'] = 'revoked'
                    s['nodes'][a['node']] = 'pending'

    def finish(self):
        with self.transaction() as s:
            if not self.admit(s, 0):
                return False
            if any(v != 'succeeded' for v in s['nodes'].values()):
                raise Rejected('undelivered obligations')
            s.update(status='complete', outcome='VERIFIED_SUCCESS')
            return True
