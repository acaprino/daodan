"""Boundary contracts the writer and the executor accept from the other components.

The four interfaces of spec section 1.3: map slice (I1), approved spec (I2),
selection (I3) and routing (I4). A validator checks version, request binding,
closed options and references only. Passing one proves that an implementation
speaks the contract, not that its decisions are good.
"""
from __future__ import annotations

import hashlib
import json

STATUSES = ('ok', 'abstain', 'unavailable')
FRESHNESS = ('fresh', 'stale', 'unknown')
EDGE_KINDS = ('call', 'import', 'contract')
SPEC_STATUSES = ('draft', 'proposed', 'approved')
ORACLE_FOR_KIND = {'behavior': 'test', 'refactor': 'equivalence',
                   'artifact': 'artifact', 'analysis': 'review'}
PURPOSES = ('review', 'worker')
ROSTER_SCHEMA = 'daodan/review-roster/v1'
TIERS = ('tier1', 'tier2', 'tier3')
EFFORTS = ('low', 'medium', 'high')


class InterfaceRejected(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def _require(condition, reason):
    if not condition:
        raise InterfaceRejected(reason)


def _envelope(response, schema, request, decision=False):
    """Check the common envelope; True when the response carries a payload."""
    _require(isinstance(response, dict) and response.get('schema') == schema, 'unknown schema')
    impl = response.get('implementation')
    _require(isinstance(impl, dict) and impl.get('name') and impl.get('version'),
             'implementation identity missing')
    _require(response.get('input_digest') == digest(request), 'response bound to another request')
    _require(response.get('status') in STATUSES, 'unknown status')
    _require(isinstance(response.get('gaps'), list), 'gaps missing')
    if decision:
        _require(isinstance(response.get('decision_id'), str) and response['decision_id'],
                 'decision_id missing')
        _require(isinstance(response.get('decisions'), list), 'decisions missing')
        _require(response['status'] == 'ok' or not response['decisions'],
                 'decisions without status ok')
    return response['status'] == 'ok'


def validate_map_slice(response, request):
    if not _envelope(response, 'daodan/map-slice/v1', request):
        return response
    snap = response.get('snapshot')
    _require(isinstance(snap, dict) and snap.get('run_id') and snap.get('digest')
             and snap.get('freshness') in FRESHNESS, 'snapshot identity or freshness missing')
    components = response.get('components')
    _require(isinstance(components, list) and components, 'components missing')
    ids, owned = set(), set()
    for comp in components:
        _require(comp.get('id') and comp['id'] not in ids, 'component id missing or duplicate')
        ids.add(comp['id'])
        paths = set(comp.get('paths') or [])
        _require(paths, f"component {comp['id']} has no paths")
        _require(not owned & paths, f'path owned by two components: {sorted(owned & paths)}')
        owned |= paths
    _require(isinstance(response.get('edges'), list), 'edges missing')
    for edge in response['edges']:
        _require(edge.get('from') in ids and edge.get('to') in ids, 'edge outside the slice')
        _require(edge.get('kind') in EDGE_KINDS, 'unknown edge kind')
        _require(edge.get('evidence'), 'edge without evidence')
    return response


def require_fresh(slice_):
    """The writer freezes only on a slice fresh against the candidate."""
    _require(slice_['status'] == 'ok' and slice_['snapshot']['freshness'] == 'fresh',
             'map slice not fresh: return to the mapper')


def validate_approved_spec(response, request):
    if not _envelope(response, 'daodan/approved-spec/v1', request):
        return response
    spec = response.get('spec')
    _require(isinstance(spec, dict) and spec.get('id') and spec.get('path') and spec.get('digest')
             and spec.get('status') in SPEC_STATUSES, 'spec identity or status missing')
    requirements = response.get('requirements')
    _require(isinstance(requirements, list) and requirements, 'requirements missing')
    ids = set()
    for req in requirements:
        _require(req.get('id') and req['id'] not in ids, 'requirement id missing or duplicate')
        ids.add(req['id'])
        _require(req.get('text') and req.get('kind') in ORACLE_FOR_KIND,
                 f"{req['id']}: text or kind missing")
        oracle = req.get('oracle') or {}
        _require(oracle.get('type') == ORACLE_FOR_KIND[req['kind']] and oracle.get('ref'),
                 f"{req['id']}: oracle does not match kind {req['kind']}")
    _require(isinstance(response.get('contracts'), list), 'contracts missing')
    for contract in response['contracts']:
        consumers = set(contract.get('consumers') or [])
        _require(contract.get('id') and contract.get('artifact'), 'contract id or artifact missing')
        _require(contract.get('producer') in ids and consumers and consumers <= ids
                 and contract['producer'] not in consumers,
                 f"{contract['id']}: contract outside the requirements")
    scope = response.get('scope')
    _require(isinstance(scope, dict) and isinstance(scope.get('in'), list)
             and isinstance(scope.get('out'), list), 'scope missing')
    for field in ('adr_refs', 'open_questions', 'authorizations'):
        _require(isinstance(response.get(field), list), f'{field} missing')
    return response


def require_approved(spec):
    _require(spec['status'] == 'ok' and spec['spec']['status'] == 'approved'
             and not spec['open_questions'],
             'spec not approved or questions open: return to the specs writer')


def validate_selection(response, request):
    _require(request.get('purpose') in PURPOSES, 'unknown purpose')
    _require(request.get('roster', {}).get('schema') == ROSTER_SCHEMA, 'roster floor missing')
    if not _envelope(response, 'daodan/selection/v1', request, decision=True):
        return response
    roles = set(request['catalog']['roles'])
    hunks = {h['id'] for h in request['hunks']}
    seen = set()
    for d in response['decisions']:
        _require(d.get('role') in roles, f"role not in catalog: {d.get('role')}")
        _require(d['role'] not in seen, f"duplicate decision: {d['role']}")
        seen.add(d['role'])
        _require(isinstance(d.get('selected'), bool), 'selected must be boolean')
        p = d.get('probability')
        _require(p is None or (isinstance(p, (int, float)) and 0 <= p <= 1),
                 'probability outside [0, 1]')
        _require(d.get('citation') is None or d['citation'] in hunks,
                 f"citation outside the request: {d.get('citation')}")
    return response


def validate_routing(response, request):
    if not _envelope(response, 'daodan/routing/v1', request, decision=True):
        return response
    nodes = {n['id'] for n in request['nodes']}
    seen = set()
    for d in response['decisions']:
        _require(d.get('node') in nodes, f"node outside the request: {d.get('node')}")
        _require(d['node'] not in seen, f"duplicate decision: {d['node']}")
        seen.add(d['node'])
        _require(d.get('tier') is None or d['tier'] in TIERS,
                 f"tier outside the options: {d.get('tier')}")
        _require(d.get('effort') is None or d['effort'] in EFFORTS,
                 f"effort outside the options: {d.get('effort')}")
    return response
