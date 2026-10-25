"""Context evaluation on a real second project: frozen corpus, blind gold, equal budget.

Machine-only. Prepare freezes a public package and its queries; evaluate compares how much of the
gold entities' source each arm delivers inside the same character budget. Results measure
localization and context delivery. They say nothing about task success or LLM token savings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve()
SCRIPTS = Path(os.environ['CODEBASE_MAP_SCRIPTS']) if os.environ.get('CODEBASE_MAP_SCRIPTS') else next(
    p / 'plugins/codebase-map/skills/map-method/scripts' for p in HERE.parents
    if (p / 'plugins/codebase-map/skills/map-method/scripts').is_dir())
sys.path.insert(0, str(SCRIPTS))
import context_packet as packets
import resolve_edges
import retrieval
import scope_planner as scope
import semantic_store
import snapshot
from snapshot_store import open_snapshot

BUDGETS = (6000, 12000, 24000)
POLICY = 'scope-v1'


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf8', newline='\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(project, source, queries, environment):
    project.mkdir(parents=True, exist_ok=False)
    package = project / source.name
    shutil.copytree(source, package, ignore=shutil.ignore_patterns('__pycache__'))
    evaluation = project / '.evaluation'
    evaluation.mkdir()
    shutil.copyfile(queries, evaluation / 'queries.json')
    files = {p.relative_to(project).as_posix(): sha(p) for p in sorted(package.rglob('*')) if p.is_file()}
    manifest = project / '.codebase-map/manifest.sqlite'
    started = time.perf_counter()
    snapshot.write_snapshot(project, manifest)
    snapshot_seconds = time.perf_counter() - started
    started = time.perf_counter()
    index = retrieval.refresh_index(manifest, manifest.with_name('retrieval.sqlite'))
    index_seconds = time.perf_counter() - started
    started = time.perf_counter()
    edges = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'resolve_edges.py'), str(manifest), '--environment',
                            str(environment), '--compact'], capture_output=True, text=True)
    edge_seconds = time.perf_counter() - started
    write(evaluation / 'frozen.json', {'source_sha256': files, 'queries_sha256': sha(evaluation / 'queries.json'),
          'snapshot_seconds': snapshot_seconds, 'index_seconds': index_seconds, 'edge_seconds': edge_seconds,
          'edge_returncode': edges.returncode, 'edge_report': edges.stdout[-1500:], 'edge_stderr': edges.stderr[-500:],
          'documents': index['documents'], 'tuning': False})
    print(json.dumps({'prepared': str(project), 'files': len(files), 'documents': index['documents'],
                      'edge_returncode': edges.returncode, 'edge_seconds': round(edge_seconds, 1)}))


def entities(store):
    found = {}
    for path, entry in store.iter_files(semantic=False):
        for name, spec in (entry.get('symbols') or {}).items():
            if name != '@file' and isinstance(spec.get('start'), int):
                found[f'{path}::{name}'] = (path, spec['start'], spec['end'])
    return found


class Corpus:
    def __init__(self, project):
        self.project = project
        self.lines = {}

    def text(self, path):
        if path not in self.lines:
            self.lines[path] = (self.project / path).read_text(encoding='utf8').replace('\r\n', '\n').split('\n')
        return self.lines[path]


def fill(order, table, corpus, budget):
    """Deliver whole entity bodies in rank order; skip one that no longer fits, keep going."""
    delivered, used = {}, 0
    for identity in order:
        if identity not in table:
            continue
        path, start, end = table[identity]
        have = delivered.setdefault(path, set())
        want = set(range(start, end + 1)) - have
        cost = sum(len(corpus.text(path)[n - 1]) + 1 for n in want)
        if used + cost <= budget:
            have |= want
            used += cost
    return delivered, used


def packet_lines(packet):
    delivered = {}
    for block in packet['blocks']:
        if block.get('kind') != 'source':
            continue
        for span in block['blocks']:
            delivered.setdefault(block['path'], set()).update(range(span['start'], span['end'] + 1))
    return delivered


def spans(lines):
    """Delivered line numbers as inclusive [start, end] runs, for claim scoring."""
    runs = []
    for number in sorted(lines):
        if runs and number == runs[-1][1] + 1:
            runs[-1][1] = number
        else:
            runs.append([number, number])
    return runs


def coverage(delivered, gold, table):
    full, partial = 0, 0.0
    for identity in gold:
        path, start, end = table[identity]
        got = len(delivered.get(path, set()) & set(range(start, end + 1))) / (end - start + 1)
        full += got == 1.0
        partial += got
    return {'full': full / len(gold), 'partial': partial / len(gold)}


def request_for(query, manifest):
    return {'schema': 'daodan/context-request/v1', 'task_id': 'eval', 'intent': 'analysis', 'query': query,
            'read_boundary': ['.'], 'write_boundary': [], 'anchors': [], 'base': None,
            'candidate': {'manifest': str(manifest)}, 'diff': [], 'proposed_edits': [],
            'mandatory_requirements': [], 'required_gates': [],
            'budget': {'max_candidates': 200, 'max_edges': 2000, 'max_rounds': 100, 'max_seconds': 120,
                       'max_input_tokens': 10 ** 9, 'max_output_tokens': 10 ** 9}, 'policy_version': POLICY}


def evaluate(project, output, limit=None, shard=None, anchor='none'):
    frozen = json.loads((project / '.evaluation/frozen.json').read_bytes())
    for name, digest in frozen['source_sha256'].items():
        if sha(project / name) != digest:
            raise ValueError('holdout source changed after preparation')
    queries = json.loads((project / '.evaluation/queries.json').read_bytes())
    if sha(project / '.evaluation/queries.json') != frozen['queries_sha256']:
        raise ValueError('queries changed after preparation')
    manifest = project / '.codebase-map/manifest.sqlite'
    lexical = manifest.with_name('retrieval.sqlite')
    edges = resolve_edges.default_edge_store(manifest)
    corpus = Corpus(project)
    authority = {'root': str(project), 'read_boundary': ['.'], 'write_boundary': []}
    rows = []
    with open_snapshot(manifest) as store:
        table = entities(store)
        project_chars = sum(len(line) + 1 for path in {p for p, _, _ in table.values()} for line in corpus.text(path))
        chosen_queries = queries['queries'][:limit]
        if shard:
            index, count = shard
            chosen_queries = [q for position, q in enumerate(chosen_queries) if position % count == index]
        for item in chosen_queries:
            gold = item['gold']
            missing = [g for g in gold if g not in table]
            if missing:
                raise ValueError(f"gold entity missing from the snapshot: {item['id']} {missing}")
            started = time.perf_counter()
            ranked = [r['entity_id'] for r in retrieval.search(lexical, item['query'], anchors=[], limit=60)['results']]
            lexical_seconds = time.perf_counter() - started
            seeds = ranked[:3]
            started = time.perf_counter()
            impact = (semantic_store.build_edit_impact(store, seeds, hops=1, include_source=False, engine_store=edges)
                      if seeds else {'targets': []})
            neighbours = []
            for target in impact['targets']:
                for side in ('callers', 'callees'):
                    neighbours += [row['symbol_id'] for row in target[side]['listed']]
            graph_order = seeds + [n for n in dict.fromkeys(neighbours) if n not in seeds] + [r for r in ranked if r not in seeds]
            graph_seconds = lexical_seconds + (time.perf_counter() - started)
            row = {'id': item['id'], 'language': item['language'], 'type': item['type'], 'gold': gold,
                   'lexical_rank': {g: (ranked.index(g) + 1 if g in ranked else None) for g in gold}, 'arms': {}}
            request = request_for(item['query'], manifest)
            # post-hoc exploratory modes: one accepted starting entity, as an interview or a diff would supply
            if anchor == 'top1' and ranked:
                request['anchors'] = [{'entity_id': ranked[0]}]
            elif anchor == 'gold1':
                request['anchors'] = [{'entity_id': gold[0]}]
            indexes = {'retrieval': str(lexical)}
            started = time.perf_counter()
            plan, plan_error = None, None
            try:
                plan = scope.prepare_scope(request, authority=authority, indexes=indexes)
                plan = scope.advance_scope(plan, request, authority=authority, indexes=indexes, max_steps=100)
            except ValueError as error:
                plan_error = str(error)[:300]
            plan_seconds = time.perf_counter() - started
            row['scope'] = {'seconds': plan_seconds, 'error': plan_error} if plan is None else {
                'seconds': plan_seconds, 'status': plan['status'], 'localized': plan['localized'],
                'analysis_entities': len({r['entity_id'] for r in plan['analysis']}),
                'gold_in_analysis': sum(g in {r['entity_id'] for r in plan['analysis']} for g in gold) / len(gold)}
            for budget in BUDGETS:
                arms = row['arms'][str(budget)] = {}
                delivered, used = fill(ranked, table, corpus, budget)
                arms['text'] = dict(coverage(delivered, gold, table), chars=used, seconds=lexical_seconds)
                delivered, used = fill(graph_order, table, corpus, budget)
                arms['text+graph'] = dict(coverage(delivered, gold, table), chars=used, seconds=graph_seconds)
                if plan is None:
                    arms['scope+packet'] = {'error': plan_error}
                    arms['scope+packet:ready'] = {'error': plan_error}
                    continue
                recipient = {'id': 'eval-recipient', 'available_tokens': budget, 'reserve_tokens': 0,
                             'max_chars': budget, 'max_evaluations': 2000}
                started = time.perf_counter()
                try:
                    packet = packets.build_packet(plan, request, authority=authority, recipient=recipient, indexes=indexes)
                    present = coverage(packet_lines(packet), gold, table)
                    packet_seconds = time.perf_counter() - started
                    # Present source counts whatever the packet holds; dispatchable coverage
                    # counts only a ready packet, every refusal or incomplete packet as zero.
                    arms['scope+packet'] = dict(present,
                        chars=len(packet['input']) if packet['input'] else 0,
                        seconds=plan_seconds + packet_seconds, plan_seconds=plan_seconds, packet_seconds=packet_seconds,
                        status=packet['status'], status_reason=packet.get('status_reason'),
                        blocks=packet['counts']['blocks'], scope_status=plan['status'], localized=plan['localized'],
                        lines={path: spans(lines) for path, lines in packet_lines(packet).items()})
                    ready = packet['status'] == 'ready'
                    arms['scope+packet:ready'] = dict(full=present['full'] if ready else 0.0,
                        partial=present['partial'] if ready else 0.0, chars=arms['scope+packet']['chars'],
                        seconds=arms['scope+packet']['seconds'], status=packet['status'])
                except ValueError as error:
                    arms['scope+packet'] = {'error': str(error)[:300]}
                    arms['scope+packet:ready'] = {'error': str(error)[:300]}
                arms['text']['lines'] = {path: spans(lines) for path, lines in fill(ranked, table, corpus, budget)[0].items()}
            rows.append(row)
    write(output, result(rows, frozen, project_chars, anchor))
    print(json.dumps({'output': str(output), 'queries': len(rows), 'anchor': anchor}))


def summarize(rows):
    summary = {}
    for budget in BUDGETS:
        summary[str(budget)] = {}
        for arm in ('text', 'text+graph', 'scope+packet', 'scope+packet:ready'):
            for language in ('all', 'en', 'it'):
                picked = [r['arms'][str(budget)][arm] for r in rows if (language == 'all' or r['language'] == language)
                          and 'error' not in r['arms'][str(budget)][arm]]
                if picked:
                    summary[str(budget)].setdefault(arm, {})[language] = {
                        'queries': len(picked), 'full_gold': statistics.mean(c['full'] for c in picked),
                        'partial_gold': statistics.mean(c['partial'] for c in picked),
                        'mean_chars': statistics.mean(c['chars'] for c in picked),
                        'mean_seconds': statistics.mean(c['seconds'] for c in picked)}
        statuses = {}
        for r in rows:
            arm = r['arms'][str(budget)]['scope+packet']
            key = arm.get('status', 'error') + ('/' + arm['status_reason'] if arm.get('status_reason') else '')
            statuses[key] = statuses.get(key, 0) + 1
        summary[str(budget)]['scope+packet_statuses'] = statuses
        delivered = [r['arms'][str(budget)]['scope+packet'] for r in rows if r['arms'][str(budget)]['scope+packet'].get('chars')]
        ready = [r['arms'][str(budget)]['scope+packet'] for r in rows if r['arms'][str(budget)]['scope+packet'].get('status') == 'ready']
        summary[str(budget)]['scope+packet_when_ready'] = {
            'queries': len(ready),
            'full_gold': statistics.mean(c['full'] for c in ready) if ready else None,
            'partial_gold': statistics.mean(c['partial'] for c in ready) if ready else None}
        summary[str(budget)]['scope+packet_when_delivered'] = {
            'queries': len(delivered),
            'full_gold': statistics.mean(c['full'] for c in delivered) if delivered else None,
            'partial_gold': statistics.mean(c['partial'] for c in delivered) if delivered else None}
    return summary


def result(rows, frozen, project_chars, anchor='none'):
    recall = {str(k): statistics.mean((1 if r['lexical_rank'][g] and r['lexical_rank'][g] <= k else 0)
                                      for r in rows for g in r['gold']) for k in (5, 10, 20)}
    scoped = [r['scope'] for r in rows if 'status' in r['scope']]
    return {'schema': 'daodan/context-holdout-result/v1', 'anchor_mode': anchor,
            'frozen': {k: frozen[k] for k in ('queries_sha256', 'tuning')},
            'project_chars': project_chars, 'full_context_fits_budget': {str(b): project_chars <= b for b in BUDGETS},
            'queries': len(rows), 'lexical_recall_at': recall,
            'scope': {'planned': len(scoped), 'localized': sum(s['localized'] for s in scoped),
                      'statuses': {s: sum(x['status'] == s for x in scoped) for s in {x['status'] for x in scoped}},
                      'mean_analysis_entities': statistics.mean(s['analysis_entities'] for s in scoped) if scoped else None,
                      'mean_gold_in_analysis': statistics.mean(s['gold_in_analysis'] for s in scoped) if scoped else None},
            'summary': summarize(rows), 'rows': sorted(rows, key=lambda r: r['id']),
            'limits': ['One public library, gold written blind by a model and checked by a second pass.',
                       'Coverage counts delivered source of gold entities; it is not task success. A packet that refuses '
                       '(needs_split) counts as zero coverage in the unconditional means and is reported separately.',
                       'Characters, not tokens: no tokenizer identity was supplied, so no token saving is claimed.']}


def merge(parts, output):
    rows, frozen, chars, anchor = [], None, None, 'none'
    for part in parts:
        data = json.loads(Path(part).read_bytes())
        rows += data['rows']
        frozen = {'queries_sha256': data['frozen']['queries_sha256'], 'tuning': data['frozen']['tuning']}
        chars = data['project_chars']
        anchor = data.get('anchor_mode', 'none')
    write(output, result(rows, frozen, chars, anchor))
    print(json.dumps({'merged': len(rows), 'output': str(output)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'evaluate', 'merge'])
    parser.add_argument('--project', type=Path)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--queries', type=Path)
    parser.add_argument('--environment', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--limit', type=int, help='first N queries only (smoke runs)')
    parser.add_argument('--anchor', choices=['none', 'top1', 'gold1'], default='none',
                        help='none: natural query only (registered protocol); top1/gold1: post-hoc exploratory anchor')
    parser.add_argument('--shard', help='K/N: evaluate every Nth query starting at K (independent processes, merged later)')
    parser.add_argument('--parts', type=Path, nargs='+', help='merge: result files of the shards')
    args = parser.parse_args()
    if args.operation == 'merge':
        merge(args.parts, args.out.resolve())
        return
    if not args.project:
        parser.error('--project is required')
    if args.operation == 'prepare':
        if not (args.source and args.queries and args.environment):
            parser.error('prepare needs --source, --queries and --environment')
        prepare(args.project.resolve(), args.source.resolve(), args.queries.resolve(), args.environment.resolve())
    else:
        if not args.out:
            parser.error('evaluate needs --out')
        evaluate(args.project.resolve(), args.out.resolve(), args.limit,
                 tuple(map(int, args.shard.split('/'))) if args.shard else None, args.anchor)


if __name__ == '__main__':
    main()
