"""Deterministic prerequisite packing of verified static evidence.

No inference, index refresh or model download. The recipient input is measured
after full serialization; operational receipts and resumable residuals stay on disk.
"""
from __future__ import annotations

import copy
import itertools
import json
import math
from contextlib import ExitStack
from pathlib import Path

import retrieval
import scope_planner as scope
import semantic_store as semantics
import source_reader

POLICY = 'prerequisite-pack-v1'
SCHEMA = 'daodan/context-packet/v1'


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _recipient(value, counter):
    if not isinstance(value, dict) or not isinstance(value.get('id'), str) or not value['id']:
        raise ValueError('recipient requires a stable identity')
    result = dict(value)
    for key in ('available_tokens', 'reserve_tokens', 'max_chars', 'max_evaluations'):
        if type(value.get(key)) is not int or value[key] < 0:
            raise ValueError('recipient requires nonnegative integer ' + key)
    if not 1 <= value['max_evaluations'] <= 10000 or value['max_chars'] > 10_000_000:
        raise ValueError('recipient work or character limit is out of range')
    if counter is not None and (not callable(counter) or not value.get('tokenizer_id')):
        raise ValueError('exact token counter requires its recipient tokenizer identity')
    for key in ('prefix', 'suffix'):
        if not isinstance(value.get(key, ''), str):
            raise ValueError('recipient wrapper must be text')
        result.setdefault(key, '')
    if value.get('policy', 'ordered') not in ('ordered', 'marginal'):
        raise ValueError('unsupported packing policy')
    result.setdefault('policy', 'ordered')
    result['policy_version'] = POLICY
    result['counter_available'] = counter is not None
    return result


def pack_variants(variants, hard_support, *, recipient, token_counter=None, render=None):
    """Pack declared evidence variants, with bounded search and explicit omissions.

    Requires are variant IDs. A group admits one representation; hard support is
    independent of the fixed nonnegative surrogate features. Cyclic prerequisites
    close as a unit. A failed bounded search never proves mathematical infeasibility.
    """
    recipient = _recipient(recipient, token_counter)
    if not isinstance(variants, list) or len(variants) > 1000:
        raise ValueError('packing accepts at most 1000 variants')
    rows = {}
    for row in variants:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'] or row['id'] in rows:
            raise ValueError('variants require unique nonempty identities')
        if any(not isinstance(row.get(k), list) or any(not isinstance(v, str) for v in row[k])
               for k in ('provides', 'requires')):
            raise ValueError('variant support and prerequisites must be string lists')
        if not isinstance(row.get('group'), str) or not isinstance(row.get('features'), dict):
            raise ValueError('variant group and fixed features are required')
        if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in row['features'].values()):
            raise ValueError('features must have finite nonnegative scores')
        rows[row['id']] = row
    if not isinstance(hard_support, list) or any(not isinstance(v, str) for v in hard_support):
        raise ValueError('hard support must be a string list')
    hard = set(hard_support)
    evaluations = 0
    closure_visits = 0
    active_cap = recipient['max_evaluations']
    work_limited = False
    best_cost = None

    def close(ids):
        nonlocal closure_visits, work_limited
        if closure_visits + evaluations >= active_cap:
            work_limited = True
            return None
        closure_visits += 1
        result = set(ids)
        todo = list(ids)
        while todo:
            identity = todo.pop()
            if identity not in rows:
                return None
            for needed in rows[identity]['requires']:
                if needed not in result:
                    result.add(needed)
                    todo.append(needed)
        groups = [rows[i]['group'] for i in result]
        return result if len(groups) == len(set(groups)) else None

    def support(ids):
        return set().union(*(set(rows[i]['provides']) for i in ids)) if ids else set()

    def utility(ids):
        features = {}
        for identity in ids:
            for name, score in rows[identity]['features'].items():
                features[name] = max(features.get(name, 0), score)
        return sum(features.values())

    def measure(ids):
        nonlocal evaluations, work_limited, best_cost
        if evaluations + closure_visits >= active_cap:
            work_limited = True
            return None
        evaluations += 1
        selected = [rows[i] for i in rows if i in ids]
        text = recipient['prefix'] + (render(selected) if render else _json([r['payload'] for r in selected])) + recipient['suffix']
        tokens = None if token_counter is None else token_counter(text)
        if tokens is not None and (type(tokens) is not int or tokens < 0):
            raise ValueError('recipient token counter must return a nonnegative integer')
        cost = dict(input_chars=len(text), input_tokens=tokens,
                    available_tokens=recipient['available_tokens'], reserve_tokens=recipient['reserve_tokens'],
                    max_chars=recipient['max_chars'], measurement='actual' if tokens is not None else 'characters_only',
                    dispatch_verified=tokens is not None,
                    fits=len(text) <= recipient['max_chars'] and (tokens is None or tokens + recipient['reserve_tokens'] <= recipient['available_tokens']))
        if best_cost is None:
            best_cost = cost
        return text, cost

    # Bounded combinations of hard-support providers. Closure handles SCCs without
    # splitting their prerequisites, and support is checked after every replacement.
    choices = [[i for i in rows if predicate in rows[i]['provides']] for predicate in sorted(hard)]
    combinations = itertools.product(*choices) if hard else [()]
    core = None
    core_measured = None
    for choice in combinations:
        if evaluations + closure_visits >= recipient['max_evaluations']:
            work_limited = True
            break
        selected = close(choice)
        if selected is None:
            continue
        measured = measure(selected)
        if measured is None:
            break
        if hard <= support(selected) and measured[1]['fits']:
            core, core_measured = selected, measured
            break
    if core is None:
        if best_cost is None:
            best_cost = {'fits': False, 'measurement': 'unavailable', 'input_tokens': None,
                         'input_chars': None, 'dispatch_verified': False}
        return dict(status='needs_split', selected=[], input=None, budget=dict(best_cost, fits=False),
                    missing_support=sorted(hard), deferred=[{'id': i, 'reason': 'mandatory_core_unavailable'} for i in rows],
                    evaluations=evaluations + closure_visits, work_limited=work_limited, comparison={})

    def proposals(selected):
        nonlocal work_limited
        for identity in rows:
            if evaluations + closure_visits >= active_cap:
                work_limited = True
                break
            if identity in selected:
                continue
            group = rows[identity]['group']
            proposed = close({i for i in selected if rows[i]['group'] != group} | {identity})
            if proposed is not None and hard <= support(proposed):
                roots = {i for i in proposed if any(rows[i]['features'].values()) or set(rows[i]['provides']) & hard}
                proposed = close(roots)
            if proposed is not None and hard <= support(proposed):
                yield identity, proposed

    # Both policies start at the same mandatory core. The work cap is global;
    # allocations prevent one experiment from consuming the entire comparison.
    comparison = {}
    results = {}
    for policy in ('ordered', 'marginal'):
        selected, measured = set(core), core_measured
        used = evaluations + closure_visits
        local_cap = used + max(0, (recipient['max_evaluations'] - used) // (2 if policy == 'ordered' else 1))
        active_cap = local_cap
        single_best = (utility(selected), set(selected), measured)
        while evaluations + closure_visits < local_cap:
            feasible = []
            for identity, proposed in proposals(selected):
                if evaluations + closure_visits >= local_cap:
                    work_limited = True
                    break
                candidate = measure(proposed)
                if candidate is None:
                    break
                gain = utility(proposed) - utility(selected)
                if not candidate[1]['fits'] or gain <= 0:
                    continue
                unit = 'input_tokens' if token_counter else 'input_chars'
                delta = candidate[1][unit] - measured[1][unit]
                ratio = math.inf if delta <= 0 else gain / delta
                feasible.append((ratio, gain, identity, proposed, candidate))
                if policy == 'ordered':
                    break
            if not feasible:
                break
            picked = sorted(feasible, key=lambda v: (-v[0], -v[1], v[2]))[0]
            selected, measured = picked[3], picked[4]
        # Compare against each feasible single bundle added to the core as required
        # by the heuristic. These evaluations also count against the global cap.
        for _, proposed in proposals(core):
            if evaluations + closure_visits >= local_cap:
                work_limited = True
                break
            candidate = measure(proposed)
            if candidate and candidate[1]['fits'] and utility(proposed) > single_best[0]:
                single_best = (utility(proposed), proposed, candidate)
        if single_best[0] > utility(selected):
            selected, measured = single_best[1:]
        comparison[policy] = {'utility': utility(selected), 'input_chars': measured[1]['input_chars'],
                              'input_tokens': measured[1]['input_tokens'], 'selected': sorted(selected)}
        results[policy] = (selected, measured)
    selected, measured = results[recipient['policy']]
    return dict(status='ready', selected=[i for i in rows if i in selected], input=measured[0],
                budget=measured[1], missing_support=[],
                deferred=[{'id': i, 'reason': 'work_limit' if work_limited else 'budget_or_representation_or_no_gain'} for i in rows if i not in selected],
                evaluations=evaluations + closure_visits, work_limited=work_limited, comparison=comparison)


def _predicate(row):
    if not isinstance(row.get('predicate'), str) or not isinstance(row.get('entity_id', ''), str):
        raise ValueError('support predicate and entity identity must be text')
    return row['predicate'] + ':' + row.get('entity_id', '')


def _project(plan, request, store, paths):
    if type(request.get('slices', False)) is not bool:
        raise ValueError('slices must be an explicit boolean')
    rows, gaps = [], []
    hard = {_predicate(p) for r in request['mandatory_requirements'] for p in r.get('support', [])}
    hard.update('unsupported_requirement:' + r['id'] for r in request['mandatory_requirements'] if not r.get('support'))
    for row in plan['analysis']:
        if row.get('required_detail') == 'source':
            hard.add('current_source:' + row['entity_id'])
    entities = sorted({r['entity_id'] for r in plan['analysis']},
                      key=lambda e: (plan['priorities'].get(e, [9, 0]), e))
    selected = entities[:200]
    if len(entities) > len(selected):
        gaps.append({'kind': 'projection_limit', 'omitted_entities': entities[200:]})
    pieces = {}
    for rank, entity in enumerate(selected):
        record = plan['entities'][entity]
        path = record['anchor']['file']
        if not scope._inside(path, plan['boundaries']['read_boundary']):
            gaps.append({'kind': 'outside_read_boundary', 'entity_id': entity})
            continue
        weight = 1 / (rank + 1)
        identity = 'signature:' + entity
        rows.append(dict(id=identity, entity_id=entity, group=identity,
            representation='signature', provides=['signature:' + entity], requires=[],
            features={entity: weight}, payload={'kind': 'signature', **record}))
        symbol = entity.split('::', 1)[1]
        packet = source_reader.read_packet(store, [{'path': path, **(
            {'full_file': True} if symbol == '@file' else {'symbols': [symbol]})}])
        needed = []
        for file in packet['files']:
            for block in file['blocks']:
                piece = 'source:' + retrieval._digest([plan['candidate']['logical_digest'], file['path'], block['start'], block['end']])
                needed.append(piece)
                pieces[piece] = dict(id=piece, entity_id=entity, group=piece,
                    representation='source-piece', provides=[], requires=[], features={},
                    payload={'kind': 'source-piece', 'path': file['path'],
                             'raw_hash': file['raw_hash'], 'hash': file['hash'],
                             'parser_profile': file['parser_profile'], 'notes': file['notes'],
                             'block': block})
        rows.append(dict(id='body:' + entity, entity_id=entity, group='detail:' + entity,
            representation='body', provides=['current_source:' + entity], requires=[identity, *needed],
            features={entity: weight * 3}, payload={'kind': 'body', 'entity_id': entity,
                'anchor': record['anchor'], 'source_refs': needed}))
        if symbol == '@file':
            continue
        impact = semantics.build_edit_impact(store, [entity], cards_path=paths.get('cards'),
            engine_store=paths['engine'], include_source=False, neighbors=5, history=1,
            hops=2, include_slices=request.get('slices', False), budget_chars=120000)
        targets = impact['targets']
        if not targets:
            gaps.append({'kind': 'impact_target_unavailable', 'entity_id': entity})
            continue
        target = copy.deepcopy(targets[0])
        card = target.pop('card', None)
        if card and card.get('freshness') == 'fresh':
            rows.append(dict(id='card:' + entity, entity_id=entity, group='detail:' + entity,
                representation='card', provides=['semantic_card:' + entity], requires=[identity],
                features={entity: weight * 2}, payload={'kind': 'card', 'entity_id': entity, 'card': card,
                    'anchor': record['anchor'], 'freshness_basis': 'lexical'}))
        elif card:
            gaps.append({'kind': 'stale_card', 'entity_id': entity, 'freshness': card['freshness']})
        for group in ('callers', 'callees'):
            for neighbor in target[group]['listed']:
                neighbor_card = neighbor.get('card')
                if not isinstance(neighbor_card, dict) or neighbor_card.get('freshness') != 'fresh':
                    neighbor.pop('card', None)
        rows.append(dict(id='impact:' + entity, entity_id=entity, group='impact:' + entity,
            representation='impact', provides=['graph:' + entity], requires=[identity],
            features={'graph:' + entity: weight}, payload={'kind': 'edit-impact', 'entity_id': entity,
                'evidence': target, 'disclosure': impact['disclosure'], 'edge_view': impact['edge_view'],
                'freshness_basis': impact['freshness_basis'], 'budget': impact['budget']}))
    rows.extend(pieces.values())
    if len(rows) > 1000:
        gaps.append({'kind': 'variant_limit', 'omitted_variants': [r['id'] for r in rows[1000:]]})
        rows = rows[:1000]
    return rows, sorted(hard), gaps


def _render_blocks(selected):
    blocks, sources = [], {}
    for row in selected:
        payload = copy.deepcopy(row['payload'])
        if payload.get('kind') != 'source-piece':
            blocks.append(payload)
            continue
        path = payload['path']
        file = sources.setdefault(path, {k: payload[k] for k in ('path', 'raw_hash', 'hash', 'parser_profile', 'notes')})
        file.setdefault('source_ids', []).append(row['id'])
        reasons = file.setdefault('reasons', [])
        if payload['block']['reason'] not in reasons:
            reasons.append(payload['block']['reason'])
        lines = file.setdefault('lines', {})
        # Physical newlines preserve form feeds and identical text on other lines.
        for line in payload['block']['source'].split('\n')[:-1]:
            number, text = line.split(': ', 1)
            if int(number) in lines and lines[int(number)] != text:
                raise ValueError('inconsistent overlapping source evidence')
            lines[int(number)] = text
    for path, file in sorted(sources.items()):
        lines = file.pop('lines')
        spans = []
        for number in sorted(lines):
            if not spans or number != spans[-1][-1] + 1:
                spans.append([])
            spans[-1].append(number)
        blocks.append(dict(kind='source', **file, blocks=[{
            'start': span[0], 'end': span[-1],
            'source': ''.join(str(n) + ': ' + lines[n] + '\n' for n in span)} for span in spans]))
    return blocks


def build_packet(plan, request, *, authority, recipient, indexes=None, cursor=None, token_counter=None):
    """Project a scope checkpoint without closing its obligations or granting edits."""
    scope._verify_cursor(plan)
    recipient = _recipient(recipient, token_counter)
    plan_digest = retrieval._digest(plan)
    with ExitStack() as stack:
        stores, bindings, bound, paths, stamps, digest = scope._inputs(
            request, authority, plan['index_paths'] if indexes is None else indexes, stack)
        if digest != plan['input_digest']:
            raise ValueError('cursor_stale: scope inputs changed')
        binding = retrieval._digest([digest, plan_digest, recipient, POLICY])
        delivered = set()
        previous_tokens = 0
        if cursor is not None:
            if (not isinstance(cursor, dict) or cursor.get('schema') != 'daodan/context-cursor/v1'
                    or cursor.get('binding') != binding
                    or cursor.get('state_digest') != retrieval._digest({k: v for k, v in cursor.items() if k != 'state_digest'})):
                raise ValueError('cursor_stale: recipient, policy, inputs or checkpoint changed')
            delivered = set(cursor['delivered'])
            previous_tokens = cursor['input_tokens']
        rows, hard, projection_gaps = _project(plan, request, stores['candidate'], paths)
        required_ids = {r['id'] for r in rows if set(r['provides']) & set(hard)}
        rows = [r for r in rows if r['id'] not in delivered or r['id'] in required_ids
                or r['representation'] in ('signature', 'source-piece')]
        for row in rows:
            if row['id'] in delivered and row['representation'] == 'signature':
                row['features'] = {}
        obligations = copy.deepcopy(plan['validation_obligations'])
        gaps = copy.deepcopy(plan['unresolved']) + projection_gaps
        metadata = dict(schema=SCHEMA, task_id=plan['task_id'], input_digest=digest,
            plan_digest=plan_digest, scope_status=plan['status'], task_complete=False,
            candidate=bindings['candidate'], resolver_profile=plan['resolver_profile'], indices=stamps,
            policy_version=POLICY, coverage=plan['coverage'],
            obligations=obligations, gaps=gaps,
            engine_callee_drift=(plan.get('comparison') or {}).get('engine_callee_drift'),
            validation_complete=False, write_authorized=False)
        effective = dict(recipient)
        if token_counter is not None:
            remaining = max(0, request['budget']['max_input_tokens'] - plan['usage']['input_tokens'] - previous_tokens)
            effective['available_tokens'] = min(effective['available_tokens'], remaining + effective['reserve_tokens'])
        def render(selected):
            blocks = _render_blocks(selected)
            return _json(dict(metadata, blocks=blocks, counts={'blocks': len(blocks)}))
        result = pack_variants(rows, hard, recipient=effective, token_counter=token_counter, render=render)
        selected_ids = set(result['selected'])
        blocks = _render_blocks([r for r in rows if r['id'] in selected_ids])
        next_cursor = dict(schema='daodan/context-cursor/v1', binding=binding,
            delivered=sorted(delivered | selected_ids),
            input_tokens=previous_tokens + ((result['budget'].get('input_tokens') or 0)
                                           if result['input'] is not None else 0))
        next_cursor['state_digest'] = retrieval._digest(next_cursor)
        status = result['status']
        if status == 'ready' and not plan['localized']:
            status = 'incomplete'
        deferred = result['deferred'] + copy.deepcopy(plan['deferred']) + projection_gaps
        output = dict(metadata, status=status, blocks=blocks,
            input=result['input'], budget=result['budget'], cursor=next_cursor,
            counts={'blocks': len(blocks), 'variants': len(rows), 'deferred': len(deferred)},
            deferred=deferred, missing_support=result['missing_support'],
            comparison=result['comparison'], evaluations=result['evaluations'], work_limited=result['work_limited'],
            dispatch_gap=None if token_counter else 'Recipient tokenizer unavailable; character cap only. Verify actual available context at dispatch.',
            )
        scope._stable(stores, bindings, paths, stamps, bound['read_boundary'])
        return output


def persist_packet(packet, output, *, authority):
    """Publish one immutable JSON receipt beside its bound candidate manifest."""
    root = Path(authority['root'])
    path = scope._path(output, root)
    manifest = Path(packet['candidate']['path'])
    if not path.is_relative_to(manifest.parent) or path.suffix != '.json':
        raise ValueError('context output must be a new JSON under the manifest directory')
    import embedding_worker
    embedding_worker._publish_json(path, packet)
    from snapshot_store import artifact_digest
    return dict(path=str(path), sha256=artifact_digest(path), status=packet['status'],
                counts=packet['counts'], budget=packet['budget'], input_digest=packet['input_digest'])


def create_context(manifest, request, recipient, *, authority, out, cursor=None, indexes=None):
    """Shared explicit CLI/MCP operation. Return paths and counts, never full source."""
    from snapshot_store import artifact_digest
    import embedding_worker
    manifest = scope._path(manifest, Path(authority['root']))
    request = copy.deepcopy(request)
    expected = {'manifest': str(manifest)}
    if request.get('candidate') not in (None, expected):
        raise ValueError('request candidate differs from the independently bound manifest')
    request['candidate'] = expected
    output = scope._path(out, Path(authority['root']))
    if not output.is_relative_to(manifest.parent):
        raise ValueError('context output directory must be under the bound manifest directory')
    checkpoint = None
    if cursor is not None:
        path = scope._path(cursor, Path(authority['root']))
        if not path.is_relative_to(manifest.parent) or path.suffix != '.json':
            raise ValueError('cursor must belong to the bound manifest directory')
        checkpoint = json.loads(path.read_text(encoding='utf8'))
        if (checkpoint.get('schema') != 'daodan/context-checkpoint/v1'
                or checkpoint.get('sha256') != retrieval._digest({k: v for k, v in checkpoint.items() if k != 'sha256'})):
            raise ValueError('cursor_stale: invalid context checkpoint')
    if checkpoint:
        plan = checkpoint['plan']
    else:
        plan = scope.prepare_scope(request, authority=authority, indexes=indexes)
        plan = scope.advance_scope(plan, request, authority=authority, indexes=indexes, max_steps=100)
    packet = build_packet(plan, request, authority=authority, recipient=recipient, indexes=indexes,
                          cursor=checkpoint['cursor'] if checkpoint else None)
    import map_slice
    slice_ = map_slice.project_slice(plan, request, authority=authority, indexes=indexes)
    identity = retrieval._digest(packet)
    packet_path = output / ('context-' + identity + '.json')
    cursor_path = output / ('cursor-' + identity + '.json')
    slice_path = output / ('map-slice-' + identity + '.json')
    output.mkdir(parents=True, exist_ok=True)
    scope._path(output, Path(authority['root']))
    saved = persist_packet(packet, packet_path, authority=authority)
    checkpoint = dict(schema='daodan/context-checkpoint/v1', plan=plan, cursor=packet['cursor'])
    checkpoint['sha256'] = retrieval._digest(checkpoint)
    embedding_worker._publish_json(cursor_path, checkpoint)
    embedding_worker._publish_json(slice_path, slice_)
    return dict(saved, cursor_path=str(cursor_path), cursor_sha256=artifact_digest(cursor_path),
                map_slice_path=str(slice_path), map_slice_sha256=artifact_digest(slice_path),
                gaps=len(packet['gaps']), dispatch_gap=packet['dispatch_gap'])
