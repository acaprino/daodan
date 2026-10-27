"""Prepare immutable model inputs and score saved Modal evidence, without model calls."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = ROOT / '.daodan/runs/2026-10-26-gutsy-modal-pilot'
MODEL = 'gutsy-0.8b-v04-q4'
MODULES = {'routing': 'routing_cases', 'tools': 'tool_cases', 'compaction': 'compaction_cases'}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def confined(path):
    target = Path(path).resolve()
    if not (target.is_relative_to(RUN.resolve()) or target.is_relative_to(HERE)):
        raise ValueError('Artifact output must remain in the owned pilot or run directory')
    return target


def write(path, value, frozen=False):
    target = confined(path)
    data = encoded(value)
    if frozen and target.exists() and target.read_text(encoding='utf-8') != data:
        raise ValueError(f'Frozen artifact differs: {target}; use a new named run')
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + '.tmp')
    temporary.write_text(data, encoding='utf-8', newline='\n')
    temporary.replace(target)


def module(domain):
    os.environ.setdefault('FAST_JEV_MODULE', str(RUN / 'deps/fast-jev/dist/index.js'))
    return importlib.import_module(MODULES[domain])


def validate_cases(cases):
    ids = [case['id'] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate case identifiers')
    total = 0
    for case in cases:
        if case['domain'] not in MODULES:
            raise ValueError('Unknown case domain')
        questions = case['questions']
        if not isinstance(questions, dict) or not 1 <= len(questions) <= 64:
            raise ValueError('Question count outside the official request contract')
        for question in questions.values():
            if question.get('type') not in {'choice', 'noul'}:
                raise ValueError('Pilot supports only its declared decision types')
        state_text = json.dumps(case['state'], ensure_ascii=False)
        if '"oracle"' in state_text or case['id'] in state_text:
            raise ValueError('Case identifier or oracle key leaked into model state')
        total += len(questions)
    if total > 500:
        raise ValueError('Pilot exceeds the question budget')
    return total


def model_payload(cases):
    validate_cases(cases)
    priority = {'R01': 0, 'C01-A': 1, 'T01': 2}
    ordered = sorted(enumerate(cases), key=lambda pair: (priority.get(pair[1]['id'], 3), pair[0]))
    return {'max_questions': 500, 'max_seconds': 1800, 'requests': [
        {'id': case['id'], 'domain': case['domain'],
         'body': {'model': MODEL, 'state': case['state'], 'questions': case['questions']}}
        for _, case in ordered]}


def prepare(directory):
    target = confined(directory)
    cases = []
    for domain in MODULES:
        cases.extend(module(domain).build_cases())
    count = validate_cases(cases)
    payload = model_payload(cases)
    source_paths = sorted(HERE.glob('*.py')) + sorted(HERE.glob('*.mjs'))
    source_paths += [ROOT / 'plugins/model-routing/skills/model-routing/scripts/task_router.py']
    source_paths += [RUN / 'deps/fast-jev/dist/index.js']
    manifest = {'schema': 'gutsy-pilot-input/v1', 'model': MODEL,
                'cases': len(cases), 'questions': count,
                'by_domain': {domain: {'cases': sum(c['domain'] == domain for c in cases),
                                      'questions': sum(len(c['questions']) for c in cases if c['domain'] == domain)}
                              for domain in MODULES},
                'payload_sha256': hashlib.sha256(encoded(payload).encode()).hexdigest(),
                'case_sha256': hashlib.sha256(encoded(cases).encode()).hexdigest(),
                'sources': {str(path.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in source_paths}}
    checks = {domain: module(domain).deterministic_checks()
              for domain in ('routing', 'compaction')}
    # The upstream bridge verifies both the state collision and the pinning precondition.
    a1 = next(c for c in cases if c['id'] == 'C01-A')
    a2 = next(c for c in cases if c['id'] == 'C02-A')
    if encoded(a1['state']) != encoded(a2['state']):
        raise ValueError('C01/C02 upstream state collision does not hold')
    write(target / 'cases.json', cases, frozen=True)
    write(target / 'input.json', payload, frozen=True)
    write(target / 'manifest.json', manifest, frozen=True)
    write(target / 'deterministic-checks.json', checks, frozen=True)
    print(encoded({'directory': str(target), **{k: manifest[k] for k in ('cases', 'questions', 'by_domain', 'payload_sha256')}}))


def percentile(values, fraction):
    values = sorted(values)
    return values[max(0, math.ceil(len(values) * fraction) - 1)] if values else None


def check_invocation(remote, manifest):
    observed = remote.get('invocation', {}).get('input_sha256')
    if observed != manifest['payload_sha256']:
        raise ValueError('Remote invocation input digest differs from the frozen payload')


def score(directory, result_path):
    target = confined(directory)
    cases = json.loads((target / 'cases.json').read_text(encoding='utf-8'))
    payload = json.loads((target / 'input.json').read_text(encoding='utf-8'))
    manifest = json.loads((target / 'manifest.json').read_text(encoding='utf-8'))
    if hashlib.sha256(encoded(payload).encode()).hexdigest() != manifest['payload_sha256']:
        raise ValueError('Frozen input digest mismatch')
    if hashlib.sha256(encoded(cases).encode()).hexdigest() != manifest['case_sha256']:
        raise ValueError('Frozen case/oracle digest mismatch')
    remote = json.loads(Path(result_path).read_text(encoding='utf-8'))
    check_invocation(remote, manifest)
    records = remote.get('records', [])
    record_ids = [record['id'] for record in records]
    if len(record_ids) != len(set(record_ids)) or set(record_ids) - {case['id'] for case in cases}:
        raise ValueError('Duplicate or unknown remote response identifiers')
    by_id = {record['id']: record for record in records}
    rows = []
    for case in cases:
        record = by_id.get(case['id'])
        row = {'id': case['id'], 'domain': case['domain'], 'split': case['split']}
        if not record or not isinstance(record.get('response'), dict):
            row.update(status='unavailable', error=record.get('error') if record else 'missing remote response')
        else:
            try:
                if record['response'].get('model') != MODEL:
                    raise ValueError('Returned model does not match the explicit Q4 identity')
                row.update(module(case['domain']).score_case(case, record['response']))
                row.setdefault('status', 'ok')
                if row.get('invalid_answers'):
                    row['status'] = 'invalid'
            except (ValueError, KeyError, TypeError, RuntimeError) as exc:
                row.update(status='invalid', error=f'{type(exc).__name__}: {exc}')
        row['elapsed_seconds'] = record.get('elapsed_seconds') if record else None
        if record and record.get('error'):
            row.update(status='invalid', transport_error=record['error'])
        rows.append(row)
    timings = [row['elapsed_seconds'] for row in rows if isinstance(row['elapsed_seconds'], (int, float))]
    routing = [row for row in rows if row['domain'] == 'routing']
    tools = [row for row in rows if row['domain'] == 'tools' and row['id'] not in {'T15', 'T16'}]
    compaction = [row for row in rows if row['domain'] == 'compaction']
    summaries = {
        'routing': {'essential_hits': sum(r.get('essential_hits', 0) for r in routing),
                    'essential_support': sum(len(c['oracle']['essential']) for c in cases if c['domain'] == 'routing'),
                    'cases_all_essential_correct': sum(r.get('all_essential_correct', False) for r in routing),
                    'cases': len(routing),
                    'critical_case_ids': [r['id'] for r in routing if r.get('critical_failures')],
                    'fallback_case_ids': [r['id'] for r in routing if r.get('fallback_used')],
                    'tier_changed_by_labeled_errors_case_ids': [r['id'] for r in routing if r.get('tier_changed_by_labeled_errors')]},
        'tools': {'semantic_cases': len(tools), 'raw_sufficient': sum(r.get('sufficiency_raw') is True for r in tools),
                  'exact_sufficient': sum(r.get('exact_sufficient') is True for r in tools),
                  'policy_sufficient': sum(r.get('sufficiency_policy') is True for r in tools),
                  'raw_omission_case_ids': [r['id'] for r in tools if r.get('sufficiency_raw') is not True],
                  'superfluous_selection_case_ids': [r['id'] for r in tools if r.get('superfluous_canonical')],
                  'empty_selection_case_ids': [r['id'] for r in tools if r.get('selected_count') == 0],
                  'discovery_contracts': [r for r in rows if r['id'] in {'T15', 'T16'}],
                  'schema_bytes_before': sum(r.get('schema_bytes_before', 0) for r in tools),
                  'schema_bytes_after': sum(r.get('schema_bytes_after', 0) for r in tools),
                  'schema_bytes_minimal': sum(r.get('schema_bytes_minimal', 0) for r in tools)},
        'compaction': {arm: {'cases': len(arm_rows),
                            'decision_bearing_cases': sum(r.get('evidence_decision_bearing') is True for r in arm_rows),
                            'evidence_preserved_raw': sum(r.get('evidence_preserved_raw') is True for r in arm_rows),
                            'evidence_preserved_decision_bearing': sum(r.get('evidence_preserved_raw') is True and r.get('evidence_decision_bearing') is True for r in arm_rows),
                            'superfluous_keep_case_ids': [r['id'] for r in arm_rows if r.get('superfluous_keep')],
                            'critical_case_ids': [r['id'] for r in arm_rows if r.get('critical_failures')],
                            'reduction_bytes': sum(r.get('reduction_bytes', 0) for r in arm_rows)}
                       for arm in ('A', 'B')
                       for arm_rows in [[r for r in compaction if r['id'].endswith('-' + arm)]]},
    }
    complete = bool(remote.get('complete')) and len(records) == len(cases) and all(r['status'] == 'ok' for r in rows)
    result = {'complete': complete, 'coverage': {'expected_requests': len(cases), 'returned_requests': len(records),
                                               'scored_ok': sum(r['status'] == 'ok' for r in rows)},
              'summary': summaries, 'timing': {'p50_seconds': statistics.median(timings) if timings else None,
                                             'p95_seconds': percentile(timings, 0.95),
                                             'pooled_limit': 'Mixed request sizes; use per_domain for contract targets.',
                                             'per_domain': {
                                                 domain: {
                                                     'requests': len(values),
                                                     'p50_seconds': statistics.median(values) if values else None,
                                                     'p95_seconds': percentile(values, 0.95),
                                                 }
                                                 for domain in MODULES
                                                 for values in [[r['elapsed_seconds'] for r in rows
                                                                 if r['domain'] == domain and isinstance(r['elapsed_seconds'], (int, float))]]}},
              'runtime': remote.get('runtime'), 'stop_reason': remote.get('stop_reason'), 'cases': rows}
    write(target / 'scores.json', result)
    lines = ['# Gutsy Q4 Modal CPU pilot', '',
             f"Coverage: {len(records)}/{len(cases)} requests returned; {result['coverage']['scored_ok']} scored. Complete evidence: {complete}.", '',
             '## Results', '', '```json', encoded(summaries).strip(), '```', '',
             '## Runtime and limits', '', '```json', encoded({'runtime': result['runtime'], 'timing': result['timing'], 'stop_reason': result['stop_reason']}).strip(), '```', '',
             'These are synthetic, partially labeled preliminary cases. No downstream LLM task outcome or target-token savings was measured.',
             'A successful transport is distinct from semantic success. Raw omissions are not hidden by protection or fallback.', '',
             '## Per-case outcomes', '', '| Case | Status | Critical or missing | Seconds |', '|---|---|---|---|']
    for row in rows:
        issues = row.get('critical_failures') or row.get('required_missing') or row.get('error') or ''
        lines.append(f"| {row['id']} | {row['status']} | {str(issues).replace('|', '/')} | {row['elapsed_seconds']} |")
    (target / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    print(encoded({'complete': complete, 'coverage': result['coverage'], 'summary': summaries, 'timing': result['timing']}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--out', default=str(RUN / 'artifacts'))
    p = sub.add_parser('score')
    p.add_argument('--directory', default=str(RUN / 'artifacts'))
    p.add_argument('--result', required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.out)
    else:
        score(args.directory, args.result)


if __name__ == '__main__':
    main()
