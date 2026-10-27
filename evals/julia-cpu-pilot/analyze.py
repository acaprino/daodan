"""Score preserved Julia answers without changing the frozen pilot oracles."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import statistics
import sys

from pilot import ROOT, RUN, OWNERS, read, sha, verify, write


def owner(name):
    path = OWNERS / 'evals/gutsy-decision-pilot' / (name + '_cases.py')
    spec = importlib.util.spec_from_file_location('julia_pilot_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def routing_score(module, case, response):
    router = module._router()
    answers = response['answers']
    classification = {}
    for name, allowed in router.SIGNALS.items():
        answer = answers[name]
        if isinstance(allowed[0], bool):
            classification[name] = answer['noul'] >= 0.5
        else:
            if set(answer['probabilities']) != set(allowed) or answer['choice'] not in allowed:
                raise ValueError('Routing label identity differs from frozen owner')
            classification[name] = answer['choice']
    expected = case['oracle']['essential']
    matches = {key: module._accepts(value, classification[key]) for key, value in expected.items()}
    failures = [key for key in case['oracle'].get('critical_signals', []) if not matches[key]]
    tier = router.resolve_tier(classification)[2]
    minimum = case['oracle'].get('minimum_tier')
    if minimum and ['tier1', 'tier2', 'tier3'].index(tier) < ['tier1', 'tier2', 'tier3'].index(minimum):
        failures.append('below_minimum_tier')
    return {'essential_hits': sum(matches.values()), 'essential_support': len(matches),
            'all_essential_correct': all(matches.values()), 'essential_matches': matches,
            'classification': classification, 'resolved_tier': tier, 'critical_failures': failures,
            'native_reject': 'unavailable_in_julia_not_fabricated'}


def percentile(values, fraction):
    if not values:
        return None
    import math
    return sorted(values)[max(0, math.ceil(fraction * len(values)) - 1)]


def analyze():
    manifest = verify()
    for relative, expected in manifest['scoring_owner_hashes'].items():
        if sha(OWNERS / relative) != expected:
            raise ValueError('Scoring owner drift: ' + relative)
    os.environ['FAST_JEV_MODULE'] = str(ROOT / '.daodan/runs/2026-10-26-gutsy-modal-pilot/deps/fast-jev/dist/index.js')
    modules = {name: owner(name) for name in ['routing', 'tool', 'compaction']}
    cases = read(RUN / 'cases.json')
    requests = {r['id']: r for r in read(RUN / 'input.json')}
    import hashlib
    from pilot import encoded
    records = {}
    for path in sorted((RUN / 'execution/records').glob('*.json')):
        record = read(path)
        case_id = record['id']
        if case_id in records or case_id not in requests:
            raise ValueError('Duplicate or unknown result')
        if record['request_sha256'] != hashlib.sha256(encoded(requests[case_id])).hexdigest():
            raise ValueError('Response/input binding differs')
        records[case_id] = record
    scored = []
    for case in cases:
        record = records.get(case['id'])
        item = {'id': case['id'], 'domain': case['domain'], 'status': 'missing' if record is None else record['status']}
        if record and record['status'] == 'delivered':
            if case['domain'] == 'routing':
                item.update(routing_score(modules['routing'], case, record['response']))
            else:
                item.update(modules['tool' if case['domain'] == 'tools' else 'compaction'].score_case(case, record['response']))
            item['status'] = 'scored'
            item['elapsed_seconds'] = record['elapsed_seconds']
            item['questions'] = record['questions']
        elif record:
            item['error'] = record['input_audit'].get('error')
        scored.append(item)
    rows = [x for x in scored if x['status'] == 'scored']
    routing = [x for x in rows if x['domain'] == 'routing']
    tools = [x for x in rows if x['domain'] == 'tools' and x['id'] not in {'T15', 'T16'}]
    compaction = {arm: [x for x in rows if x['domain'] == 'compaction' and x['id'].endswith('-' + arm)]
                  for arm in ['A', 'B']}
    first = next((r['id'] for r in requests.values() if r['id'] in records and records[r['id']]['status'] == 'delivered'), None)
    timing = {}
    for domain in ['routing', 'tools', 'compaction']:
        values = [x['elapsed_seconds'] for x in rows if x['domain'] == domain]
        timing[domain] = {'warm_requests': len(values), 'p50_seconds': statistics.median(values) if values else None,
                          'p95_seconds': percentile(values, .95),
                          'questions_per_request': sorted({x['questions'] for x in rows if x['domain'] == domain}),
                          'within_one_second': sum(v <= 1 for v in values),
                          'scope': 'whole named-question predict call including tokenization; resident warmed model, '
                                   'encoding/token caches cleared, batch size one; diagnostic small sample'}
    resources = read(RUN / 'execution/resources.json')
    runtime = read(RUN / 'execution/runtime.json') if (RUN / 'execution/runtime.json').exists() else None
    ledger = read(RUN / 'execution/ledger.json') if (RUN / 'execution/ledger.json').exists() else None
    parity = read(RUN / 'execution/parity.json') if (RUN / 'execution/parity.json').exists() else None
    complete = len(rows) == 47 and resources['exit_code'] == 0 and bool(ledger and ledger['complete'])
    result = {'schema': 'julia-cpu-pilot-results/v1', 'complete_quality_coverage': complete,
              'manifest_sha256': sha(RUN / 'manifest.json'),
              'coverage': {'planned_requests': 47, 'planned_questions': 314,
                           'states': dict(Counter(x['status'] for x in scored)),
                           'by_domain': {d: dict(Counter(x['status'] for x in scored if x['domain'] == d))
                                         for d in ['routing', 'tools', 'compaction']}},
              'routing': {'scored_cases': len(routing), 'planned_cases': 15,
                          'labelled_hits': sum(x['essential_hits'] for x in routing),
                          'observed_labelled_support': sum(x['essential_support'] for x in routing),
                          'planned_labelled_support': sum(len(c['oracle']['essential']) for c in cases if c['domain'] == 'routing'),
                          'all_essential_correct_cases': sum(x['all_essential_correct'] for x in routing),
                          'critical_case_ids': [x['id'] for x in routing if x['critical_failures']]},
              'tools': {'scored_semantic_cases': len(tools), 'planned_semantic_cases': 14,
                        'raw_sufficient': sum(x['sufficiency_raw'] is True for x in tools),
                        'protected_sufficient': sum(x['sufficiency_policy'] is True for x in tools),
                        'omission_case_ids': [x['id'] for x in tools if x['sufficiency_raw'] is not True],
                        'schema_bytes_before': sum(x['schema_bytes_before'] for x in tools),
                        'schema_bytes_after': sum(x['schema_bytes_after'] for x in tools)},
              'compaction': {arm: {'scored_cases': len(values), 'planned_cases': 8,
                                   'raw_preserved': sum(x['evidence_preserved_raw'] is True for x in values),
                                   'decision_bearing_cases': sum(x['evidence_decision_bearing'] is True for x in values),
                                   'decision_bearing_preserved': sum(x['evidence_decision_bearing'] is True and x['evidence_preserved_raw'] is True for x in values),
                                   'critical_case_ids': [x['id'] for x in values if x['critical_failures']]}
                             for arm, values in compaction.items()},
              'timing': timing, 'first_inference_case': first, 'runtime': runtime, 'resources': resources,
              'ledger': ledger, 'parity': parity, 'case_results': scored,
              'limitations': ['Small synthetic, partially labelled pilot; no inferential confidence interval.',
                              'No downstream LLM task or target-token savings measured.',
                              'No training, threshold tuning or native reject/confidence invented.',
                              'Gutsy Modal and Julia local CPU timings are not hardware-matched.',
                              'Input rejections and missing responses are coverage loss, never model success.'],
              'production_adoption_authorized': False}
    write(RUN / 'results.json', result)
    summary = {key: result[key] for key in ['coverage', 'routing', 'tools', 'compaction', 'timing', 'resources']}
    text = '# Julia: pilot su CPU locale\n\n'
    text += ('Copertura qualitativa completa.\n\n' if complete else 'Evidenza incompleta: usare i denominatori osservati e le lacune dichiarate.\n\n')
    text += '```json\n' + json.dumps(summary, ensure_ascii=False, indent=2) + '\n```\n\n'
    text += '\n'.join('- ' + x for x in result['limitations']) + '\n'
    (RUN / 'execution-report.md').write_text(text, encoding='utf-8')
    print(json.dumps({'coverage': result['coverage'], 'resources': resources}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    analyze()
