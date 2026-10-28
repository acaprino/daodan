"""Adapter-contract retest: corrected state, one choice question, frozen evidence.

The cycle follows the approved plan: correct the adapter contract and prove the
answer mapping offline, then run the frozen minimal cases once on local CPU with
the official positive control, then analyze under the predeclared verdict rule.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import adapter
import cases as cases_mod
import harness

base = harness.load_base()
ROOT = harness.ROOT
HERE = harness.HERE
RUN = harness.RUN
PRIOR = harness.PRIOR
read = harness.read
sha = harness.sha
encoded = harness.encoded
write_path = harness.write_path

MAXIMUM_LENGTH = 2048
HEAD_LENGTH = 512


# --------------------------------------------------------------------------- prepare


def prepare():
    old, owner = base.dependencies()
    if (RUN / 'cases.json').exists() or (RUN / 'input.json').exists():
        raise RuntimeError('Frozen inputs already exist; do not overwrite')
    specs = cases_mod.build_specs()
    cases_mod.validate_specs(specs)
    requests, private = [], {}
    for index, spec in enumerate(specs):
        prepared = owner._bridge({'action': 'prepare', 'messages': spec['messages'],
                                  'options': adapter.spec_options(spec), 'arm': 'A'})
        candidate, pinned = adapter.split_calls(prepared, spec)
        applied = adapter.apply_answer(owner, spec, candidate['id'], 'drop_result')
        prefix_text = adapter.result_text(applied['raw']['messages'], candidate['tool_use_id'])
        state = adapter.build_state(prepared['state'], spec, prefix_text, candidate, pinned)
        order = adapter.option_order(index)
        question = {'type': 'choice', 'instructions': adapter.INSTRUCTION,
                    'criteria': {label: adapter.OPTIONS[label] for label in order}}
        requests.append({'id': spec['id'], 'kind': 'semantic', 'case_id': spec['id'],
                         'option_order': order,
                         'body': {'state': state, 'questions': {'action': question}}})
        private[spec['id']] = {'id': spec['id'], 'language': spec['language'], 'family': spec['family'],
                               'goal': spec['goal'], 'messages': spec['messages'],
                               'candidate': spec['candidate'], 'recent': spec['recent'],
                               'recovery': spec['recovery'], 'oracle': spec['oracle'],
                               'option_order': order}
    write_path(RUN / 'cases.json', private, frozen=True)
    write_path(RUN / 'input.json', requests, frozen=True)
    print(json.dumps({'cases': len(private), 'requests': len(requests),
                      'cases_sha256': sha(RUN / 'cases.json'), 'input_sha256': sha(RUN / 'input.json')}))


# --------------------------------------------------------------------------- token audit


def token_audit():
    old = read(PRIOR / 'manifest.json')
    sys.path.insert(0, old['checkpoint'])
    from transformers import AutoTokenizer
    from julia.data import sequence
    tokenizer = AutoTokenizer.from_pretrained(Path(old['checkpoint']) / 'tokenizer', trust_remote_code=False)
    rows = []
    for request in read(RUN / 'input.json'):
        body = request['body']
        state = body['state'] if isinstance(body['state'], str) else encoded(body['state']).decode('utf-8')
        for qid, question in body['questions'].items():
            row = {'state': state, 'question': question['instructions'],
                   'type': question['type'], 'options': list(question['criteria'].values())}
            try:
                result = sequence(tokenizer, row, MAXIMUM_LENGTH, HEAD_LENGTH, strict=True)
                rows.append({'id': request['id'], 'question': qid, 'state': 'accepted',
                             'tokens': len(result['ids']), 'option_tokens': result['option_tokens']})
            except ValueError as error:
                rows.append({'id': request['id'], 'question': qid, 'state': 'rejected', 'reason': str(error)})
    passed = all(entry['state'] == 'accepted' for entry in rows)
    write_path(RUN / 'token-audit.json', {'schema': 'julia-adapter-retest/token-audit/v1',
                                          'max_length': MAXIMUM_LENGTH, 'head_length': HEAD_LENGTH,
                                          'rows': rows, 'pass': passed}, frozen=True)
    print(json.dumps({'rows': len(rows), 'pass': passed}))
    if not passed:
        raise SystemExit(1)


# --------------------------------------------------------------------------- seal and verify


def seal():
    old, owner = base.dependencies()
    for name in ('cases.json', 'input.json', 'offline-verification.json', 'token-audit.json'):
        if not (RUN / name).exists():
            raise RuntimeError('Missing frozen artifact before seal: ' + name)
    owner_root = Path(old['scoring_owner_root'])
    owner_hashes = {}
    for relative in ('evals/gutsy-decision-pilot/compaction_cases.py',
                     'evals/gutsy-decision-pilot/compaction_bridge.mjs'):
        frozen = owner_root / relative
        owner_hashes[frozen.relative_to(ROOT).as_posix()] = old['scoring_owner_hashes'][relative]
    manifest = {
        'schema': 'julia-adapter-retest/v1',
        'created_at': time.time(),
        'model': old['model'], 'revision': old['revision'], 'weight_sha256': old['weight_sha256'],
        'checkpoint': old['checkpoint'], 'python': old['python'],
        'runtime_hashes': old['runtime_hashes'], 'fast_jev_hashes': old['fast_jev_hashes'],
        'fast_jev_revision': old['fast_jev_revision'],
        'owner_hashes': owner_hashes,
        'configuration': dict(base.CONFIG, max_length=MAXIMUM_LENGTH),
        'threads': 4,
        'source_hashes': {path.relative_to(ROOT).as_posix(): sha(path)
                          for path in sorted(HERE.iterdir()) if path.is_file()},
        'prior_manifest_sha256': sha(PRIOR / 'manifest.json'),
        'cases_sha256': sha(RUN / 'cases.json'),
        'input_sha256': sha(RUN / 'input.json'),
        'offline_sha256': sha(RUN / 'offline-verification.json'),
        'token_audit_sha256': sha(RUN / 'token-audit.json'),
        'semantic_cases': 8, 'requests': 8, 'control_evaluations': 4, 'measured_questions': 8,
        'maximum_questions': 20,
        'limits': {'seconds': 420, 'request_seconds': 45, 'rss_bytes': 2 * 2 ** 30},
        'interpretation': (
            'Eight corrected development screening cases with one question each, plus the official Billing '
            'control with head parity. Success criterion: every case answered with its declared minimal action '
            'and the control correct, with every input accepted without truncation. The offline proof maps every '
            'possible label to exactly one library action. This screening is not held-out generalization evidence.'),
    }
    write_path(RUN / 'manifest.json', manifest, frozen=True)
    print(json.dumps({'manifest_sha256': sha(RUN / 'manifest.json')}))


def verify():
    base.dependencies()
    manifest = read(RUN / 'manifest.json')
    for relative, expected in manifest['source_hashes'].items():
        if sha(ROOT / relative) != expected:
            raise ValueError('Frozen source changed: ' + relative)
    for relative, expected in manifest['owner_hashes'].items():
        if sha(ROOT / relative) != expected:
            raise ValueError('Frozen owner changed: ' + relative)
    for relative, expected in manifest['fast_jev_hashes'].items():
        if sha(ROOT / relative) != expected:
            raise ValueError('Frozen fast-jev changed: ' + relative)
    for relative, expected in manifest['runtime_hashes'].items():
        if sha(Path(manifest['checkpoint']) / relative) != expected:
            raise ValueError('Julia runtime changed: ' + relative)
    for name, filename in (('input', 'input.json'), ('cases', 'cases.json'),
                           ('offline', 'offline-verification.json'), ('token_audit', 'token-audit.json')):
        if sha(RUN / filename) != manifest[name + '_sha256']:
            raise ValueError('Frozen artifact changed: ' + filename)
    if sha(PRIOR / 'manifest.json') != manifest['prior_manifest_sha256']:
        raise ValueError('Prior pilot manifest changed')
    return manifest


# --------------------------------------------------------------------------- run and worker


def run():
    manifest = verify()
    if (RUN / 'execution/resources.json').exists():
        raise RuntimeError('Attempt evidence already exists; inspect it instead of rewriting')
    offline = read(RUN / 'offline-verification.json')
    audit = read(RUN / 'token-audit.json')
    preflight = {'manifest_sha256': sha(RUN / 'manifest.json'),
                 'offline_pass': offline['pass'], 'token_audit_pass': audit['pass'],
                 'offline_sha256': manifest['offline_sha256'], 'token_audit_sha256': manifest['token_audit_sha256'],
                 'input_sha256': manifest['input_sha256'], 'cases_sha256': manifest['cases_sha256'],
                 'prior_manifest_sha256': manifest['prior_manifest_sha256'],
                 'checkpoint': manifest['checkpoint'], 'python': manifest['python'],
                 'weight_sha256': manifest['weight_sha256'], 'limits': manifest['limits'],
                 'maximum_questions': manifest['maximum_questions']}
    if not preflight['offline_pass'] or not preflight['token_audit_pass']:
        raise RuntimeError('Preflight failed: offline proof or token audit did not pass')
    write_path(RUN / 'preflight-checks.json', preflight, frozen=True)
    import psutil
    write_path(RUN / 'execution/start.json',
               {'at': time.time(), 'manifest_sha256': preflight['manifest_sha256'],
                'cpu': platform.processor(), 'physical_cpus': psutil.cpu_count(logical=False),
                'logical_cpus': psutil.cpu_count(), 'physical_memory_bytes': psutil.virtual_memory().total},
               frozen=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    started = time.monotonic()
    peak = 0
    reason = None
    with (RUN / 'execution/worker.log').open('x', encoding='utf-8') as log:
        process = subprocess.Popen([manifest['python'], '-B', str(Path(__file__).resolve()), 'worker'],
                                   cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        observed = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                children = observed.children(recursive=True)
                rss = sum(p.memory_info().rss for p in [observed, *children] if p.is_running()) \
                    + psutil.Process().memory_info().rss
                peak = max(peak, rss)
                progress_path = RUN / 'execution/progress.json'
                progress = read(progress_path) if progress_path.exists() else {}
                reason = base.guard_reason(time.monotonic() - started, rss, progress.get('phase'),
                                           time.time() - progress.get('at', time.time()), manifest['limits'])
                if reason:
                    for child in reversed(children):
                        if child.is_running():
                            child.kill()
                    process.kill()
                    break
            except psutil.NoSuchProcess:
                pass
            time.sleep(.1)
        code = process.wait(timeout=15)
    write_path(RUN / 'execution/resources.json',
               {'exit_code': code, 'guard': reason, 'wall_seconds': time.monotonic() - started,
                'combined_peak_rss_bytes': peak, 'sampling_seconds': .1}, frozen=True)
    print(json.dumps(read(RUN / 'execution/resources.json')))
    if code or reason:
        raise RuntimeError('Retest incomplete; inspect preserved evidence without automatic retry')
    analyze()


def worker():
    manifest = verify()
    os.environ.update(JULIA_CPU_THREADS='4', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4',
                      HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
    sys.path.insert(0, manifest['checkpoint'])
    write_path(RUN / 'execution/progress.json', {'phase': 'loading', 'at': time.time()})
    import importlib.metadata
    import torch
    from julia import load_model
    torch.set_num_threads(4)
    started = time.perf_counter()
    engine = load_model(manifest['checkpoint'], device='cpu', **manifest['configuration'])
    write_path(RUN / 'execution/runtime.json',
               {'load_seconds': time.perf_counter() - started, 'device': str(engine.device),
                'torch': torch.__version__,
                'versions': {name: importlib.metadata.version(name)
                             for name in ('torch', 'transformers', 'numpy', 'safetensors')},
                'platform': platform.platform(), 'python': sys.version}, frozen=True)

    state = 'I was charged twice for the same order.'
    question = {'type': 'choice', 'instructions': 'Which team should handle this request?',
                'criteria': {'billing': 'Billing and payment disputes',
                             'shipping': 'Shipping and delivery',
                             'access': 'Account access and login'}}
    row = {'state': state, 'question': question['instructions'],
           'options': list(question['criteria'].values()), 'type': 'choice'}
    write_path(RUN / 'execution/progress.json', {'phase': 'parity', 'at': time.time()})
    start = time.perf_counter()
    typed = engine.predict(state=state, questions={'team': question})
    cold = time.perf_counter() - start
    optimized = engine.logits([row])[0]
    engine.model.marker_only_head = False
    try:
        original = engine.logits([row])[0]
    finally:
        engine.model.marker_only_head = True
    start = time.perf_counter()
    repeated = engine.predict(state=state, questions={'team': question})
    warm = time.perf_counter() - start
    control = {'source': 'https://huggingface.co/SupersonicLabs/Julia-1#start-here',
               'expected': 'billing', 'typed': typed, 'optimized_logits': optimized,
               'original_logits': original, 'repeated': repeated, 'cold_seconds': cold,
               'warm_seconds': warm, 'tokens': engine.encoding_info([row]),
               'passed': typed['answers']['team']['choice'] == 'billing'
                   and repeated['answers']['team']['choice'] == 'billing'
                   and optimized.index(max(optimized)) == 0 and original.index(max(original)) == 0
                   and max(abs(a - b) for a, b in zip(optimized, original)) <= 0.02}
    write_path(RUN / 'execution/positive-control.json', control, frozen=True)
    if not control['passed']:
        raise RuntimeError('Official positive control failed; stop before the retest cases')

    ledger = {'control_evaluations': 4, 'measured_questions': 0, 'records': 0,
              'budget': manifest['maximum_questions'], 'complete': False}
    write_path(RUN / 'execution/ledger.json', ledger)
    for request in read(RUN / 'input.json'):
        body = request['body']
        model_state = body['state'] if isinstance(body['state'], str) else encoded(body['state']).decode('utf-8')
        rows = [{'state': model_state, 'question': item['instructions'],
                 'type': item['type'], 'options': list(item['criteria'].values())}
                for item in body['questions'].values()]
        record = {'id': request['id'], 'kind': request.get('kind', 'semantic'),
                  'input_sha256': hashlib.sha256(encoded(body)).hexdigest()}
        try:
            audit = engine.encoding_info(rows)
        except ValueError as error:
            record.update(status='input_rejected', reason=str(error))
            write_path(RUN / 'execution/records' / (request['id'] + '.json'), record, frozen=True)
            ledger['records'] += 1
            write_path(RUN / 'execution/ledger.json', ledger)
            continue
        ledger['measured_questions'] += len(rows)
        if ledger['control_evaluations'] + ledger['measured_questions'] > ledger['budget']:
            raise ValueError('Question budget exceeded')
        write_path(RUN / 'execution/ledger.json', ledger)
        write_path(RUN / 'execution/progress.json',
                   {'phase': 'inference', 'id': request['id'], 'at': time.time()})
        engine.clear_cache()
        start = time.perf_counter()
        response = engine.predict(state=model_state, questions=body['questions'])
        elapsed = time.perf_counter() - start
        for qid, item in body['questions'].items():
            answer = response['answers'].get(qid)
            if not isinstance(answer, dict) or answer.get('type') != item['type'] \
                    or answer.get('choice') not in item['criteria'] \
                    or set(answer.get('probabilities', {})) != set(item['criteria']):
                raise ValueError(f"Malformed answer for {request['id']}/{qid}")
        record.update(status='ok', response=response, audit=audit, seconds=elapsed)
        write_path(RUN / 'execution/records' / (request['id'] + '.json'), record, frozen=True)
        ledger['records'] += 1
        write_path(RUN / 'execution/ledger.json', ledger)
    ledger['complete'] = True
    write_path(RUN / 'execution/ledger.json', ledger)
    write_path(RUN / 'execution/progress.json', {'phase': 'finished', 'at': time.time()})


# --------------------------------------------------------------------------- analyze


def analyze():
    manifest = verify()
    specs = read(RUN / 'cases.json')
    offline = read(RUN / 'offline-verification.json')
    rows = []
    for request in read(RUN / 'input.json'):
        record = read(RUN / 'execution/records' / (request['id'] + '.json'))
        if record['input_sha256'] != hashlib.sha256(encoded(request['body'])).hexdigest():
            raise ValueError('Record does not match its frozen request: ' + request['id'])
        if record.get('status') == 'input_rejected':
            rows.append({'id': request['id'], 'kind': 'semantic', 'status': 'input_rejected',
                         'reason': record.get('reason')})
            continue
        spec = specs[request['id']]
        entry = offline['cases'][request['id']]
        answer = record['response']['answers']['action']
        chosen = answer['choice']
        expected = spec['oracle']['expected_action']
        lost = entry['labels'][chosen]['lost_facts']
        rows.append({'id': request['id'], 'kind': 'semantic', 'status': 'ok',
                     'language': spec['language'], 'family': spec['family'],
                     'expected_action': expected, 'chosen_action': chosen,
                     'correct': chosen == expected, 'safe': not lost,
                     'lost_facts_if_applied': lost,
                     'probabilities': answer['probabilities'], 'seconds': record['seconds'],
                     'tokens': [item['tokens'] for item in record['audit']],
                     'option_order': request['option_order']})
    control = read(RUN / 'execution/positive-control.json')
    accepted = [row for row in rows if row.get('status') == 'ok']
    summary = {'semantic_correct': sum(1 for row in accepted if row['correct']),
               'semantic_total': len(rows),
               'control_passed': bool(control['passed']),
               'all_inputs_accepted': len(accepted) == len(rows),
               'green': len(rows) == 8 and len(accepted) == len(rows)
                        and all(row['correct'] for row in accepted) and bool(control['passed'])}
    write_path(RUN / 'results.json',
               {'schema': 'julia-adapter-retest/results/v1', 'rows': rows, 'summary': summary,
                'positive_control': control, 'resources': read(RUN / 'execution/resources.json'),
                'ledger': read(RUN / 'execution/ledger.json'),
                'manifest_sha256': sha(RUN / 'manifest.json')})
    print(json.dumps(summary, indent=2))
    return summary


# --------------------------------------------------------------------------- main


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'token-audit', 'seal', 'verify', 'run', 'worker', 'analyze'))
    command = parser.parse_args(argv).command
    {'prepare': prepare, 'token-audit': token_audit, 'seal': seal, 'verify': verify,
     'run': run, 'worker': worker, 'analyze': analyze}[command]()


if __name__ == '__main__':
    main()
