"""Frozen P5 fixture evaluation. Prepare with map Python; evaluate in an optional runtime.

This synthetic second project is separate from the development corpus. Results
measure retrieval only; no task success, LLM token savings or default adoption
can be inferred from this small fixture.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time

SCRIPTS = Path(__file__).resolve().parents[3] / 'plugins/codebase-map/skills/map-method/scripts'
sys.path.insert(0, str(SCRIPTS))
import embedding_worker
import retrieval
import snapshot


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf8', newline='\n')


def inventory(index):
    with closing(sqlite3.connect(index)) as db:
        documents = list(db.execute('SELECT entity_id,input_digest FROM documents ORDER BY entity_id'))
        vectors = [(digest, hashlib.sha256(payload).hexdigest()) for digest, payload in
                   db.execute('SELECT input_digest,vector FROM vectors ORDER BY input_digest')]
    return {'documents': documents, 'vectors': vectors}


def verify_incremental(directory, provider, payload):
    target = "def read_config(path):\n    import json\n    return json.loads(path.read_text())"
    other = "def unrelated_matrix(values):\n    return [[x * x for x in row] for row in values]\n" * 30
    alone = embedding_worker._pack(provider.encode([target])[0], provider.profile['dimensions'])
    paired = embedding_worker._pack(provider.encode([target, other])[0], provider.profile['dimensions'])
    if alone != paired:
        raise ValueError('encoder output depends on unrelated batch inputs; cache reuse is invalid')
    project = directory / '.evaluation/incremental'
    project.mkdir(exist_ok=False)
    for name, text in payload['files'].items():
        (project / name).write_text(text, encoding='utf8', newline='\n')
    manifest = project / '.codebase-map/manifest.sqlite'
    index = manifest.with_name('embeddings.sqlite')
    snapshot.write_snapshot(project, manifest)
    first = embedding_worker.refresh_index(manifest, index, provider=provider)
    billing = project / 'billing.py'
    billing.write_text(billing.read_text(encoding='utf8').replace(
        "not item['paid']", "not item.get('paid', False)"), encoding='utf8', newline='\n')
    (project / 'cache.py').rename(project / 'memo.py')
    (project / 'transport.py').unlink()
    snapshot.write_snapshot(project, manifest)
    incremental = embedding_worker.refresh_index(manifest, index, provider=provider)
    clean = manifest.with_name('embeddings-full.sqlite')
    rebuilt = embedding_worker.refresh_index(manifest, clean, provider=provider)
    same = inventory(index) == inventory(clean)
    query = 'Recover stored JSON settings from disk'
    actual = embedding_worker.search(manifest, index, query, provider=provider, limit=1000)
    expected = embedding_worker.search(manifest, clean, query, provider=provider, limit=1000)
    replay = actual['results'] == expected['results']
    if not same or not replay or not incremental['encoded'] or not incremental['reused']:
        raise ValueError('changed-input incremental generation differs from a clean rebuild')
    return {'batch_independent': True, 'single_vector_sha256': hashlib.sha256(alone).hexdigest(),
            'changes': ['same-identity body change', 'file rename', 'file deletion'],
            'first_index': first, 'incremental_index': incremental, 'full_index': rebuilt,
            'complete_inventory_equal': same, 'complete_query_replay_equal': replay}


def prepare(directory):
    fixture = Path(__file__).with_name('p5_holdout.json')
    raw = fixture.read_bytes()
    payload = json.loads(raw)
    directory.mkdir(parents=True, exist_ok=False)
    evaluation = directory / '.evaluation'
    evaluation.mkdir()
    for name, text in payload['files'].items():
        target = directory / name
        if target.parent != directory or target.suffix != '.py':
            raise ValueError('fixture file escapes its dedicated project')
        target.write_text(text, encoding='utf8', newline='\n')
    (evaluation / 'fixture.json').write_bytes(raw)
    snapshot.write_snapshot(directory, directory / '.codebase-map/manifest.sqlite')
    retrieval.refresh_index(directory / '.codebase-map/manifest.sqlite', directory / '.codebase-map/retrieval.sqlite')
    write(evaluation / 'frozen.json', {'fixture_sha256': hashlib.sha256(raw).hexdigest(),
          'source_sha256': {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in payload['files']},
          'policy': 'exact-rrf75-25-k60-v1', 'tuning': False, 'query_count': len(payload['queries'])})
    print(json.dumps({'prepared': str(directory), 'queries': len(payload['queries']), 'fixture_sha256': hashlib.sha256(raw).hexdigest()}))


def evaluate(directory, model_dir, output, runtime_python):
    frozen = json.loads((directory / '.evaluation/frozen.json').read_bytes())
    raw = (directory / '.evaluation/fixture.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != frozen['fixture_sha256']:
        raise ValueError('holdout fixture changed after preparation')
    payload = json.loads(raw)
    for name, digest in frozen['source_sha256'].items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError('holdout source changed after preparation')
    manifest = directory / '.codebase-map/manifest.sqlite'
    loaded_at = time.perf_counter()
    with embedding_worker.ProcessProvider(runtime_python, model_dir, manifest.parent) as provider:
        return _evaluate_provider(directory, output, provider, frozen, payload, time.perf_counter() - loaded_at)


def _evaluate_provider(directory, output, provider, frozen, payload, load_seconds):
    manifest = directory / '.codebase-map/manifest.sqlite'
    lexical, index = manifest.with_name('retrieval.sqlite'), manifest.with_name('embeddings.sqlite')
    first = embedding_worker.refresh_index(manifest, index, provider=provider)
    reused = embedding_worker.refresh_index(manifest, index, provider=provider)
    clean = manifest.with_name('embeddings-full.sqlite')
    full = embedding_worker.refresh_index(manifest, clean, provider=provider)
    same_inventory = inventory(index) == inventory(clean)
    rows, exact_regressions = [], []
    for query in payload['queries']:
        started = time.perf_counter()
        base = retrieval.search(lexical, query['query'], anchors=[], limit=24)
        base_seconds = time.perf_counter() - started
        started = time.perf_counter()
        dense = embedding_worker.search(manifest, index, query['query'], provider=provider, limit=24)
        fused = retrieval.search(lexical, query['query'], anchors=[], limit=24, embedding_result=dense)
        fused_seconds = time.perf_counter() - started
        replay = embedding_worker.search(manifest, clean, query['query'], provider=provider, limit=24)
        if dense['results'] != replay['results']:
            raise ValueError('clean rebuild query replay differs')
        ids = {name: [r['entity_id'] for r in result['results']] for name, result in [('lexical', base), ('embedding', fused)]}
        row = {'id': query['id'], 'language': query['language'], 'gold': query['gold'],
               'lexical_seconds': base_seconds, 'embedding_seconds': fused_seconds,
               'ranks': {name: {gold: ranked.index(gold) + 1 if gold in ranked else None for gold in query['gold']} for name, ranked in ids.items()}}
        if query['language'] == 'exact' and ids['lexical'][:1] != ids['embedding'][:1]:
            exact_regressions.append(query['id'])
        rows.append(row)
    summaries = {}
    for language in ('all', 'en', 'it', 'exact'):
        selected = [r for r in rows if language == 'all' or r['language'] == language]
        summaries[language] = {}
        for name in ('lexical', 'embedding'):
            ranks = [list(r['ranks'][name].values()) for r in selected]
            summaries[language][name] = {'recall_at_5': sum(sum(rank is not None and rank <= 5 for rank in values) / len(values) for values in ranks) / len(ranks),
                'mrr_at_10': sum(max((1 / rank if rank is not None and rank <= 10 else 0) for rank in values) for values in ranks) / len(ranks),
                'mean_seconds': sum(r[name + '_seconds'] for r in selected) / len(selected)}
    if not same_inventory or reused['encoded'] != 0 or exact_regressions:
        raise ValueError('holdout cache, inventory or exact-anchor regression')
    changed_inputs = verify_incremental(directory, provider, payload)
    write(output, {'schema': 'daodan/p5-holdout-result/v1', 'status': 'complete', 'frozen': frozen,
          'provider': provider.profile, 'provider_load_seconds': load_seconds, 'first_index': first, 'reused_index': reused, 'full_index': full,
          'complete_inventory_equal': same_inventory, 'all_query_replays_equal': True,
           'changed_inputs': changed_inputs,
          'exact_regressions': exact_regressions, 'summary': summaries, 'queries': rows,
          'adoption': {'default': False, 'availability': 'opt_in', 'reason': 'Synthetic retrieval holdout only; representative real-task quality and whole-flow tokens remain unmeasured.'},
          'cost': {'paid_llm_calls_in_pipeline': 0, 'whole_flow_llm_tokens': 'unavailable', 'downloads': 0},
          'limits': ['Synthetic project, 20 queries; independent gold review required.',
                     'Windows CPU execution only; Linux compatibility is structural, not a live probe.',
                     'Query timing includes validation with a warm persistent encoder; startup and index times are separate. No task correctness claim.']})
    print(json.dumps({'status': 'complete', 'report': str(output), 'summary': summaries,
                      'inventory_equal': same_inventory, 'cache_reencoded': reused['encoded'], 'default': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'evaluate'])
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--runtime-python', type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    if args.operation == 'prepare':
        prepare(args.project.resolve())
    else:
        if args.model_dir is None or args.out is None:
            parser.error('evaluate needs --model-dir and --out')
        evaluate(args.project.resolve(), args.model_dir, args.out, args.runtime_python)


if __name__ == '__main__':
    main()
