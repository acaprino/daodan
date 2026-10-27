"""Frozen paired metrics, including actual fast-jev transcript reconstruction."""
from __future__ import annotations

from collections import Counter
import hashlib
import statistics

from experiment import RUN, dependencies, encoded, read, verify, write


def metrics(rows):
    n = len(rows)
    counts = Counter()
    for row in rows:
        counts['tp' if row['expected'] and row['predicted'] else
               'fn' if row['expected'] else 'fp' if row['predicted'] else 'tn'] += 1
    positive, negative = counts['tp'] + counts['fn'], counts['tn'] + counts['fp']
    recall = counts['tp'] / positive if positive else None
    specificity = counts['tn'] / negative if negative else None
    times = sorted(row['elapsed_seconds'] for row in rows)
    return {'n': n, **{key: counts[key] for key in ['tp','fn','fp','tn']},
            'correct': counts['tp'] + counts['tn'],
            'accuracy': (counts['tp'] + counts['tn']) / n if n else None,
            'required_recall': recall, 'dispensable_specificity': specificity,
            'balanced_accuracy': (recall+specificity)/2 if positive and negative else None,
            'critical_fact_loss_cases': sum(bool(r['critical_failures']) for r in rows),
            'raw_fact_loss_cases': sum(bool(r['missing_facts_raw']) for r in rows),
            'after_recovery_loss_cases': sum(not r['evidence_preserved_after_recovery'] for r in rows),
            'factual_cases': sum(bool(r['required_tokens']) for r in rows),
            'critical_factual_cases': sum(r['critical'] and bool(r['required_tokens']) for r in rows),
            'unnecessary_full_output_keeps': counts['fp'],
            'actions': dict(Counter(r['action'] for r in rows)),
            'serialized_bytes_before': sum(r['serialized_bytes_before'] for r in rows),
            'serialized_bytes_after': sum(r['serialized_bytes_after'] for r in rows),
            'timing': {'p50_seconds': statistics.median(times) if times else None,
                       'p95_seconds': times[max(0, __import__('math').ceil(.95*n)-1)] if n else None,
                       'within_one_second': sum(t<=1 for t in times)}}


def analyze():
    manifest = verify()
    _, owner = dependencies()
    cases = {c['id']: c for c in read(RUN / 'cases.json')}
    requests = read(RUN / 'input.json')
    rows, missing, rejected = [], [], []
    for request in requests:
        path = RUN / 'execution/records' / (request['id'] + '.json')
        if not path.exists():
            missing.append(request['id'])
            continue
        record = read(path)
        assert record['input_sha256'] == hashlib.sha256(encoded(request['body'])).hexdigest()
        if record['status'] != 'ok':
            rejected.append(request['id'])
            continue
        case = cases[record['case_id']]
        private = case['oracle']
        oracle = {**private, 'messages': case['messages'], 'options': case['options'],
                  'recoverable': 'recovery' in private, 'dispensable': not private['result_required']}
        score = owner.score_case({'questions':case['questions'],'oracle':oracle},record['response'])
        value = record['response']['answers']['result_t1']['noul']
        assert score['action'] == ('keep' if value >= .5 else
                                  'drop_result' if record['response']['answers']['call_t1']['noul'] >= .5 else 'drop_call')
        rows.append({'id':record['id'],'case_id':record['case_id'],'variant':record['variant'],
                     'family':case['family'],'language':case['language'],'expected':private['result_required'],
                     'predicted':value>=.5,'result_probability':value,
                     'call_probability':record['response']['answers']['call_t1']['noul'],
                     'critical':private['critical'],'required_tokens':private['required_tokens'],
                     'elapsed_seconds':record['elapsed_seconds'],**score})
    by_variant = {v:[r for r in rows if r['variant']==v] for v in ['literal','descriptive']}
    common = sorted(set(r['case_id'] for r in by_variant['literal']) & set(r['case_id'] for r in by_variant['descriptive']))
    paired = {v:{r['case_id']:r for r in values if r['case_id'] in common} for v,values in by_variant.items()}
    improvement, regression = [], []
    for case_id in common:
        old,new = paired['literal'][case_id],paired['descriptive'][case_id]
        a,b = old['expected']==old['predicted'],new['expected']==new['predicted']
        if b and not a: improvement.append(case_id)
        if a and not b: regression.append(case_id)
    summary = {v:metrics(list(paired[v].values())) for v in paired}
    delta = (summary['descriptive']['accuracy']-summary['literal']['accuracy']) if common else None
    result = {'schema':manifest['schema'],'manifest_sha256':hashlib.sha256((RUN/'manifest.json').read_bytes()).hexdigest(),
              'coverage':{'planned_cases':32,'planned_requests':64,'scored_requests':len(rows),
                          'paired_cases':len(common),'missing_requests':missing,'rejected_requests':rejected},
              'variants':summary,'paired':{'improved':improvement,'regressed':regression,'accuracy_delta':delta,
                                          'unchanged':len(common)-len(improvement)-len(regression)},
              'by_language':{lang:{v:metrics([r for r in paired[v].values() if r['language']==lang]) for v in paired}
                             for lang in ['en','it']},
              'by_family':{family:{v:metrics([r for r in paired[v].values() if r['family']==family]) for v in paired}
                           for family in sorted({c['family'] for c in cases.values()})},
              'resources':read(RUN/'execution/resources.json'), 'ledger':read(RUN/'execution/ledger.json'),
              'parity':read(RUN/'execution/parity.json'),'runtime':read(RUN/'execution/runtime.json'),
              'all_transcript_invariants_pass':all(all(r['invariants'].values()) for r in rows),
              'rows':rows}
    result['promising_quality_signal'] = bool(common and delta >= .10 and
        summary['descriptive']['critical_fact_loss_cases'] <= summary['literal']['critical_fact_loss_cases'])
    result['autonomous_compaction_supported'] = False
    write('results.json',result)
    print(__import__('json').dumps({k:result[k] for k in ['coverage','variants','paired','resources','promising_quality_signal']},indent=2))


if __name__=='__main__':
    analyze()
