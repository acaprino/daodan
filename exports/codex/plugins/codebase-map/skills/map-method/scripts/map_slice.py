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


def project_slice(plan, request, *, authority, indexes=None):
    """Project the frozen scope for an I1 consumer; reverify all input bindings."""
    scope._verify_cursor(plan)
    with ExitStack() as stack:
        stores, bindings, bound, paths, stamps, digest = scope._inputs(
            request, authority, plan['index_paths'] if indexes is None else indexes, stack)
        if digest != plan['input_digest']:
            raise ValueError('cursor_stale: map-slice inputs changed')
        selected = sorted({row['entity_id'] for row in plan['analysis']})
        projected = selected[:200]
        by_file = {}
        for identity in projected:
            record = plan['entities'][identity]
            path = record['anchor']['file']
            if not scope._inside(path, bound['read_boundary']):
                raise ValueError('map-slice component outside the read boundary')
            by_file.setdefault(path, []).append(identity)
        components = [dict(id='file:' + path, paths=[path], entities=identities)
                      for path, identities in sorted(by_file.items())]
        view = edge_view.load_edge_view(stores['candidate'], engine_store=paths['engine'])
        edges, omitted = [], 0
        for ref in view['references']:
            target = (ref.get('target_id') or '').split('::', 1)[0]
            source = ref['file']
            if ref.get('resolution') != 'resolved' or source not in by_file or target not in by_file:
                continue
            if len(edges) >= 1000:
                omitted += 1
                continue
            edges.append(dict(from_=source, to=target, kind='call', evidence={
                'reference_id': ref['id'], 'file': source, 'span': ref.get('span'),
                'caller': ref.get('caller'), 'target_id': ref['target_id'],
                'resolver': ref['resolver'], 'provenance': ref['provenance']}))
        edges = [{'from': 'file:' + row['from_'], 'to': 'file:' + row['to'],
                  'kind': row['kind'], 'evidence': row['evidence']} for row in edges]
        gaps = copy.deepcopy(plan['unresolved'])
        if len(selected) > len(projected) or omitted:
            gaps.append(dict(kind='projection_limit', entities=len(selected) - len(projected), edges=omitted))
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
