"""Public I1 projection of verified map evidence, without task precedences."""
from __future__ import annotations

import copy
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path

import edge_view
import retrieval
import scope_planner as scope

SCHEMA = 'daodan/map-slice/v1'
PROJECTION_LIMIT = 200
EDGE_LIMIT = 1000


def project_slice(plan, request, *, authority, indexes=None):
    """Project the frozen scope for an I1 consumer; reverify all input bindings."""
    scope._verify_cursor(plan)
    with ExitStack() as stack:
        stores, bindings, bound, paths, stamps, digest = scope._inputs(
            request, authority, plan['index_paths'] if indexes is None else indexes, stack)
        if digest != plan['input_digest']:
            raise ValueError('cursor_stale: map-slice inputs changed')
        sites = {row['entity_id'] for row in plan['edit_candidates']}
        core = {row['entity_id'] for row in plan['analysis'] if row.get('required_detail') == 'source'}
        # Proposed intervention sites, then the mandatory core, survive the cap before leads.
        selected = sorted({row['entity_id'] for row in plan['analysis']},
                          key=lambda entity: (entity not in sites, entity not in core,
                                              plan['priorities'].get(entity, [9, 0]), entity))
        projected = selected[:PROJECTION_LIMIT]
        by_file = {}
        for identity in projected:
            record = plan['entities'][identity]
            path = record['anchor']['file']
            if not scope._inside(path, bound['read_boundary']):
                raise ValueError('map-slice component outside the read boundary')
            by_file.setdefault(path, []).append(identity)
        components = [dict(id='file:' + path, paths=[path],
                           entities=[i for i in identities if i in core or i in sites],
                           leads=[i for i in identities if i not in core and i not in sites])
                      for path, identities in sorted(by_file.items())]
        view = edge_view.load_edge_view(stores['candidate'], engine_store=paths['engine'])
        calls = []
        for ref in view['references']:
            target = (ref.get('target_id') or '').split('::', 1)[0]
            source = ref['file']
            if ref.get('resolution') == 'resolved' and source in by_file and target in by_file:
                calls.append((source, target, ref))
        # Each distinct file pair is cited once before any pair is cited twice, so repeated
        # calls on one pair cannot use the cap that other relations need.
        first, seen = [], set()
        for index, (source, target, _) in enumerate(calls):
            if (source, target) not in seen:
                seen.add((source, target))
                first.append(index)
        chosen = set(first[:EDGE_LIMIT])
        chosen.update([i for i in range(len(calls)) if i not in chosen][:max(0, EDGE_LIMIT - len(chosen))])
        omitted = len(calls) - len(chosen)
        edges = [{'from': 'file:' + source, 'to': 'file:' + target, 'kind': 'call', 'evidence': {
                    'reference_id': ref['id'], 'file': source, 'span': ref.get('span'),
                    'caller': ref.get('caller'), 'target_id': ref['target_id'],
                    'resolver': ref['resolver'], 'provenance': ref['provenance']}}
                 for index, (source, target, ref) in enumerate(calls) if index in chosen]
        gaps = copy.deepcopy(plan['unresolved'])
        if len(selected) > len(projected) or omitted:
            gaps.append(dict(kind='projection_limit', entities=len(selected) - len(projected),
                             omitted_entities=selected[PROJECTION_LIMIT:], edges=omitted,
                             edge_pairs=len(seen) - len([i for i in first[:EDGE_LIMIT]])))
        if plan['deferred']:
            gaps.append(dict(kind='scope_frontier', deferred=copy.deepcopy(plan['deferred'])))
        if not components:
            gaps.append(dict(kind='localization', reason='No localized component is available'))
        manifest = Path(bindings['candidate']['path'])
        result = dict(schema=SCHEMA, implementation={'name': 'codebase-map', 'version': 'map-slice-v1'},
            input_digest=hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':'),
                                                  allow_nan=False).encode()).hexdigest(),
            scope_input_digest=digest, plan_digest=retrieval._digest(plan),
            status='ok' if components else 'abstain', gaps=gaps,
            snapshot={'run_id': manifest.parent.relative_to(Path(bound['root'])).as_posix(),
                'digest': bindings['candidate']['logical_digest'], 'freshness': 'fresh',
                'manifest': str(manifest), 'artifact_sha256': bindings['candidate']['sha256'],
                'read_boundary': bound['read_boundary']},
            components=components, edges=edges, coverage=copy.deepcopy(plan['coverage']),
            edit_candidates=copy.deepcopy(plan['edit_candidates']),
            outside_boundary=copy.deepcopy(plan['outside_boundary']),
            validation_obligations=copy.deepcopy(plan['validation_obligations']),
            task_complete=False, validation_complete=False, write_authorized=False)
        scope._stable(stores, bindings, paths, stamps, bound['read_boundary'])
        return result
