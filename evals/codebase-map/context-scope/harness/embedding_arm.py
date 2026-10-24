"""Embedding arm on the frozen holdout: the shipped fusion policy, no tuning.

Run it on a project prepared by evaluate.py. The pinned CodeRankEmbed model must already sit in the
shared model directory (the retrieval code never downloads weights). Four orderings are compared on
the same 24 natural queries and the same character budgets: lexical (FTS5), dense only, the fused
ranking the plugin ships (reciprocal rank fusion 0.75 dense, 0.25 lexical, k 60), and the fused
ranking seeding the Jedi call graph. With --packets it also runs the planner and the packet builder
at one budget with the dense result as their lead source.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as base
import embedding_worker
import resolve_edges
import retrieval
import scope_planner as scope
import semantic_store
import context_packet as packets
from snapshot_store import open_snapshot

K_VALUES = (5, 10, 20, 60)


class MemoryProbe(threading.Thread):
    """Sample the working set of one process; the largest sample approximates its peak."""

    def __init__(self, pid):
        super().__init__(daemon=True)
        self.pid, self.peak_kib, self.stop = pid, 0, threading.Event()

    def run(self):
        while not self.stop.is_set():
            out = subprocess.run(['tasklist', '/FI', f'PID eq {self.pid}', '/FO', 'CSV', '/NH'],
                                 capture_output=True, text=True).stdout.strip().split('","')
            try:
                self.peak_kib = max(self.peak_kib, int(out[-1].strip('"').replace(' K', '').replace(',', '').replace('.', '')))
            except ValueError:
                pass
            self.stop.wait(0.25)


def rank_row(order, gold):
    return {str(k): statistics.mean(1 if g in order[:k] else 0 for g in gold) for k in K_VALUES}


def graph_order(store, edges, ranked):
    seeds = ranked[:3]
    impact = (semantic_store.build_edit_impact(store, seeds, hops=1, include_source=False, engine_store=edges)
              if seeds else {'targets': []})
    neighbours = []
    for target in impact['targets']:
        for side in ('callers', 'callees'):
            neighbours += [row['symbol_id'] for row in target[side]['listed']]
    return seeds + [n for n in dict.fromkeys(neighbours) if n not in seeds] + [r for r in ranked if r not in seeds]


def summarize(rows, arm, budget):
    def part(selected):
        picked = [r['arms'][arm][str(budget)] for r in selected]
        return {'queries': len(picked), 'full_gold': statistics.mean(c['full'] for c in picked),
                'partial_gold': statistics.mean(c['partial'] for c in picked)} if picked else None
    return {'all': part(rows), 'en': part([r for r in rows if r['language'] == 'en']),
            'it': part([r for r in rows if r['language'] == 'it']),
            **{kind: part([r for r in rows if r['type'] == kind]) for kind in sorted({r['type'] for r in rows})}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--encoder-python', type=Path, default=Path(sys.executable),
                        help='interpreter with numpy, onnxruntime and tokenizers; it runs only the encoder process')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--packets', type=int, metavar='BUDGET',
                        help='also run the planner and the packet builder at this budget with dense leads')
    parser.add_argument('--cold-index', action='store_true',
                        help='delete the embedding index first, so its build time and memory are measured cold')
    parser.add_argument('--reuse-index', action='store_true',
                        help='skip the index refresh when an index exists (parallel shards share one index)')
    parser.add_argument('--shard', help='K/N: every Nth query starting at K (packet runs only; merge by hand)')
    args = parser.parse_args()
    project = args.project.resolve()
    frozen = json.loads((project / '.evaluation/frozen.json').read_bytes())
    for name, digest in frozen['source_sha256'].items():
        if base.sha(project / name) != digest:
            raise ValueError('holdout source changed after preparation')
    if base.sha(project / '.evaluation/queries.json') != frozen['queries_sha256']:
        raise ValueError('queries changed after preparation')
    queries = json.loads((project / '.evaluation/queries.json').read_bytes())['queries'][:args.limit]
    if args.shard:
        index, count = map(int, args.shard.split('/'))
        queries = [q for position, q in enumerate(queries) if position % count == index]
    manifest = project / '.codebase-map/manifest.sqlite'
    lexical = manifest.with_name('retrieval.sqlite')
    dense_index = manifest.with_name('embedding.sqlite')
    edges = resolve_edges.default_edge_store(manifest)
    corpus = base.Corpus(project)
    authority = {'root': str(project), 'read_boundary': ['.'], 'write_boundary': []}
    rows, receipt = [], {}
    with embedding_worker.ProcessProvider(args.encoder_python, None, manifest.parent) as provider, open_snapshot(manifest) as store:
        table = base.entities(store)
        probe = MemoryProbe(provider.process.pid)
        probe.start()
        if args.cold_index:
            dense_index.unlink(missing_ok=True)
        started = time.perf_counter()
        if args.reuse_index and dense_index.exists():
            built = {}
        else:
            built = embedding_worker.refresh_index(manifest, dense_index, provider=provider)
        receipt['index_seconds'] = time.perf_counter() - started
        receipt['index_cold'] = bool(args.cold_index)
        receipt['documents'] = built.get('documents')
        receipt['index_bytes'] = dense_index.stat().st_size
        receipt['provider'] = {k: v for k, v in provider.profile.items() if k != 'runtime'}
        receipt['runtime'] = provider.profile.get('runtime')
        for item in queries:
            gold = item['gold']
            query = item['query']
            started = time.perf_counter()
            lex = [r['entity_id'] for r in retrieval.search(lexical, query, anchors=[], limit=60)['results']]
            lexical_seconds = time.perf_counter() - started
            started = time.perf_counter()
            dense = embedding_worker.search(manifest, dense_index, query, provider=provider, limit=500)
            dense_seconds = time.perf_counter() - started
            started = time.perf_counter()
            fused_result = retrieval.search(lexical, query, anchors=[], limit=60, embedding_result=dense)
            fused_seconds = time.perf_counter() - started
            if fused_result['capabilities']['embedding'] != 'available':
                raise ValueError(f"embedding lead not consumed for {item['id']}: {fused_result['gaps']}")
            fused = [r['entity_id'] for r in fused_result['results']]
            dense_ids = [r['entity_id'] for r in dense['results']]
            started = time.perf_counter()
            fused_graph = graph_order(store, edges, fused)
            graph_seconds = time.perf_counter() - started
            orders = {'lexical': lex, 'dense': dense_ids, 'fused': fused, 'fused+graph': fused_graph}
            row = {'id': item['id'], 'language': item['language'], 'type': item['type'], 'gold': gold,
                   'recall': {name: rank_row(order, gold) for name, order in orders.items() if name != 'fused+graph'},
                   'gold_rank': {name: {g: (order.index(g) + 1 if g in order else None) for g in gold}
                                 for name, order in (('lexical', lex), ('dense', dense_ids), ('fused', fused))},
                   'seconds': {'lexical': lexical_seconds, 'dense': dense_seconds, 'fused': fused_seconds,
                               'graph': graph_seconds},
                   'arms': {}}
            for name, order in orders.items():
                row['arms'][name] = {}
                for budget in base.BUDGETS:
                    delivered, used = base.fill(order, table, corpus, budget)
                    row['arms'][name][str(budget)] = dict(base.coverage(delivered, gold, table), chars=used)
            if args.packets:
                request = base.request_for(query, manifest)
                receipt_path = Path(dense['receipt']['path'])
                result_path = receipt_path.with_name(f"dense-lead-{item['id']}.json")
                result_path.write_text(json.dumps(dense), encoding='utf8')
                indexes = {'retrieval': str(lexical), 'embedding_result': str(result_path)}
                started = time.perf_counter()
                outcome = {}
                try:
                    plan = scope.prepare_scope(request, authority=authority, indexes=indexes)
                    plan = scope.advance_scope(plan, request, authority=authority, indexes=indexes, max_steps=100)
                    outcome.update(plan_status=plan['status'], localized=plan['localized'],
                                   analysis_entities=len({r['entity_id'] for r in plan['analysis']}),
                                   gold_in_analysis=sum(g in {r['entity_id'] for r in plan['analysis']} for g in gold) / len(gold))
                    recipient = {'id': 'eval-recipient', 'available_tokens': args.packets, 'reserve_tokens': 0,
                                 'max_chars': args.packets, 'max_evaluations': 2000}
                    packet = packets.build_packet(plan, request, authority=authority, recipient=recipient, indexes=indexes)
                    outcome.update(base.coverage(base.packet_lines(packet), gold, table), status=packet['status'],
                                   chars=len(packet['input']) if packet['input'] else 0)
                except ValueError as error:
                    outcome['error'] = str(error)[:300]
                outcome['seconds'] = time.perf_counter() - started
                row['packet'] = {str(args.packets): outcome}
            rows.append(row)
        probe.stop.set()
        probe.join()
        receipt['encoder_peak_working_set_mb'] = round(probe.peak_kib / 1024) or None
    summary = {name: {str(b): summarize(rows, name, b) for b in base.BUDGETS} for name in ('lexical', 'dense', 'fused', 'fused+graph')}
    recall = {name: {str(k): statistics.mean(r['recall'][name][str(k)] for r in rows) for k in K_VALUES}
              for name in ('lexical', 'dense', 'fused')}
    never = {name: sum(1 for r in rows for rank in r['gold_rank'][name].values() if rank is None)
             / sum(len(r['gold']) for r in rows) for name in ('lexical', 'dense', 'fused')}
    out = {'schema': 'daodan/embedding-arm-result/v1', 'queries': len(rows), 'tuning': False,
           'frozen_queries_sha256': frozen['queries_sha256'], 'receipt': receipt, 'recall_at': recall,
           'gold_never_in_top60': never,
           'mean_seconds': {key: statistics.mean(r['seconds'][key] for r in rows) for key in rows[0]['seconds']},
           'summary': summary, 'rows': rows,
           'limits': ['One public library; gold written blind by a model and checked by a second pass.',
                      'Pinned community INT8 ONNX export of CodeRankEmbed on CPU; queries use the shipped prefix.',
                      'Coverage counts delivered source of gold entities; it is not task success.']}
    if args.packets:
        statuses = {}
        for r in rows:
            key = r['packet'][str(args.packets)].get('status', 'error')
            statuses[key] = statuses.get(key, 0) + 1
        out['packet'] = {'budget': args.packets, 'statuses': statuses,
                         'localized': sum(bool(r['packet'][str(args.packets)].get('localized')) for r in rows),
                         'mean_full_gold': statistics.mean(r['packet'][str(args.packets)].get('full', 0.0) for r in rows)}
    base.write(args.out, out)
    line = {name: {str(b): round(summary[name][str(b)]['all']['full_gold'], 3) for b in base.BUDGETS} for name in summary}
    print(json.dumps({'output': str(args.out), 'queries': len(rows), 'full_gold': line,
                      'recall_at': {n: {k: round(v, 3) for k, v in d.items()} for n, d in recall.items()}}))


if __name__ == '__main__':
    main()
