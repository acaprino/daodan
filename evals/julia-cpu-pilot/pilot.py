"""Bounded offline evaluation of the unmodified, pinned Julia CPU runtime."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / '.daodan/runs/2026-10-27-julia-cpu-pilot'
PRIOR = ROOT / '.daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts'
OWNERS = ROOT / '.daodan/runs/2026-10-26-gutsy-campaign/frozen-sources-v2'
REVISION = 'a85b127321d580d65176c89ced8273f305745d85'
CACHE = ROOT / 'evals/senior-review/choicer-eval/.cache'
CHECKPOINT = CACHE / 'huggingface/hub/models--SupersonicLabs--Julia-1/snapshots' / REVISION
PYTHON = CACHE / 'uv/environments-v2/run-eval-47cf6a5eba080dac/Scripts/python.exe'
WEIGHT_SHA = 'df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(2**20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value, *, frozen=False):
    path = Path(path).resolve()
    if not path.is_relative_to(RUN.resolve()):
        raise ValueError('Output outside the owned run')
    path.parent.mkdir(parents=True, exist_ok=True)
    data = encoded(value)
    if frozen and path.exists():
        if path.read_bytes() != data:
            raise FileExistsError('Refusing to replace frozen input: ' + str(path))
        return
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def rows_for(body):
    state = body['state'] if isinstance(body['state'], str) else encoded(body['state']).decode('utf-8')
    rows = []
    for question in body['questions'].values():
        criteria = question.get('criteria')
        if question['type'] == 'noul':
            options = ['false', 'true'] if criteria is None else [criteria['false'], criteria['true']]
        else:
            options = list(criteria.values())
        rows.append({'state': state, 'question': question['instructions'],
                     'type': question['type'], 'options': options})
    return rows


def prepare():
    if sha(CHECKPOINT / 'model.safetensors') != WEIGHT_SHA:
        raise ValueError('Julia weight identity differs')
    original = read(PRIOR / 'input.json')
    cases = read(PRIOR / 'cases.json')
    requests = [{'id': item['id'], 'domain': item['domain'],
                 'body': {'state': item['body']['state'], 'questions': item['body']['questions']}}
                for item in original['requests']]
    assert len(requests) == 47 and sum(len(x['body']['questions']) for x in requests) == 314
    assert all(set(x['body']) == {'state', 'questions'} for x in requests)
    for item in requests:
        rows_for(item['body'])
    write(RUN / 'input.json', requests, frozen=True)
    write(RUN / 'cases.json', cases, frozen=True)
    sources = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p)
               for p in sorted(Path(__file__).parent.glob('*.py'))}
    old_manifest = read(ROOT / '.daodan/runs/2026-10-26-gutsy-campaign/artifacts-v2-final/manifest.json')
    owner_sources = {}
    for relative, expected in old_manifest['source_hashes'].items():
        if relative.startswith('evals/gutsy-decision-pilot/') or relative.startswith('plugins/model-routing/'):
            actual = sha(OWNERS / relative)
            if actual != expected:
                raise ValueError('Frozen scoring owner changed: ' + relative)
            owner_sources[relative] = actual
    runtime_sources = {p.relative_to(CHECKPOINT).as_posix(): sha(p)
                       for p in CHECKPOINT.rglob('*') if p.is_file() and p.suffix != '.pyc'}
    fast_manifest_relative = 'evals/gutsy-campaign/sources/compaction/runtime-manifest.json'
    fast_manifest_path = OWNERS / fast_manifest_relative
    if sha(fast_manifest_path) != old_manifest['source_hashes'][fast_manifest_relative]:
        raise ValueError('Frozen fast-jev dependency manifest changed')
    fast_manifest = read(fast_manifest_path)
    fast_hashes = {}
    for entry in fast_manifest['files']:
        relative = fast_manifest['upstream_relative_path'] + '/' + entry['path']
        if sha(ROOT / relative) != entry['sha256']:
            raise ValueError('Actual fast-jev dependency changed: ' + relative)
        fast_hashes[relative] = entry['sha256']
    manifest = {'schema': 'julia-cpu-pilot/v1', 'created_at': time.time(),
                'model': 'SupersonicLabs/Julia-1', 'revision': REVISION, 'weight_sha256': WEIGHT_SHA,
                'weight_bytes': (CHECKPOINT / 'model.safetensors').stat().st_size,
                'checkpoint': str(CHECKPOINT), 'python': str(PYTHON), 'source_hashes': sources,
                'runtime_hashes': runtime_sources, 'scoring_owner_root': str(OWNERS),
                'scoring_owner_hashes': owner_sources, 'input_sha256': sha(RUN / 'input.json'),
                'fast_jev_revision': fast_manifest['revision'], 'fast_jev_hashes': fast_hashes,
                'fast_jev_manifest_sha256': sha(fast_manifest_path),
                'cases_sha256': sha(RUN / 'cases.json'),
                'prior_input_sha256': sha(PRIOR / 'input.json'), 'prior_cases_sha256': sha(PRIOR / 'cases.json'),
                'requests': 47, 'questions': 314,
                'configuration': {'threads': 4, 'batch_size': 1, 'max_length': 1024,
                                  'head_length': 512, 'strict_encoding': True,
                                  'marker_only_head': True, 'compile_model': False, 'backend': 'torch'},
                'limits': {'max_seconds': 900, 'per_request_seconds': 60,
                           'hard_rss_bytes': 2 * 2**30, 'target_rss_bytes': 2**30, 'max_questions': 500},
                'protocol': 'Same frozen pilot facts/questions/oracles; JSON states serialized as compact UTF-8. '
                            'No native reject is invented. No thresholds are fitted. Strict input rejection remains coverage loss. '
                            'All measured requests use a resident model warmed by parity; encoding/token caches '
                            'are cleared before every timed predict call, so tokenization is included. No cold-inference or long-context claim. '
                            'Two fixed rows compare optimized and original head before the pilot.'}
    write(RUN / 'manifest.json', manifest, frozen=True)
    preparation = RUN / ('preparation-amendment.md' if (RUN / 'preparation.md').exists() else 'preparation.md')
    preparation.write_text(
        '# Preparazione Julia CPU\n\n47 richieste e 314 domande del pilot precedente, con oracle immutati.\n\n'
        'Runtime Julia e pesi ufficiali locali verificati; nessuna installazione, rete, addestramento o cloud. '
        'Batch 1, quattro thread, contesto 1024, encoding rigoroso; limite 900 secondi e 2 GiB combinati. '
        'Il target di leggerezza è 1 GiB e 1 secondo per richiesta, con numero di domande sempre visibile.\n\n'
        'Il modello è già scaldato dalla parità; cache di encoding e token svuotate prima di ogni predict cronometrato, '
        'così i tempi includono la tokenizzazione. Le 16 dipendenze fast-jev sono verificate byte per byte.\n\n'
        'Gli input non contengono oracle. Il confronto precedente non è una prova appaiata di velocità: '
        'hardware, runtime e serializzazione differiscono. Lo scoring non inventa reject/confidence di Julia.\n\n'
        f'Manifest SHA256: `{sha(RUN / "manifest.json")}`.\n', encoding='utf-8')
    print(json.dumps({'requests': 47, 'questions': 314, 'manifest_sha256': sha(RUN / 'manifest.json')}))


def verify():
    manifest = read(RUN / 'manifest.json')
    for relative, expected in manifest['source_hashes'].items():
        if sha(ROOT / relative) != expected:
            raise ValueError('Pilot source changed: ' + relative)
    for relative, expected in manifest['runtime_hashes'].items():
        if sha(CHECKPOINT / relative) != expected:
            raise ValueError('Julia source/checkpoint changed: ' + relative)
    for relative, expected in manifest['fast_jev_hashes'].items():
        if sha(ROOT / relative) != expected:
            raise ValueError('fast-jev dependency changed: ' + relative)
    for name in ['input', 'cases']:
        if sha(RUN / (name + '.json')) != manifest[name + '_sha256']:
            raise ValueError('Frozen input changed: ' + name)
    return manifest


def worker():
    manifest = verify()
    os.environ.update(JULIA_CPU_THREADS='4', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4',
                      HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
    sys.path.insert(0, str(CHECKPOINT))
    started = time.monotonic()
    write(RUN / 'execution/progress.json', {'phase': 'loading', 'at': time.time()})
    import torch
    from julia import load_model
    torch.set_num_threads(4)
    engine = load_model(str(CHECKPOINT), device='cpu',
                        **{k: v for k, v in manifest['configuration'].items() if k != 'threads'})
    runtime = {'model': manifest['model'], 'revision': REVISION, 'weight_sha256': WEIGHT_SHA,
               'device': str(engine.device), 'configuration': manifest['configuration'],
               'versions': {n: importlib.metadata.version(n) for n in ['torch', 'transformers', 'numpy', 'safetensors', 'tokenizers']},
               'load_seconds': time.monotonic() - started, 'python': sys.version,
               'platform': platform.platform(), 'cpu': platform.processor()}
    write(RUN / 'execution/runtime.json', runtime)
    requests = read(RUN / 'input.json')
    # Audit the complete input batch atomically before any question in it is inferred.
    eligibility = {}
    for request in requests:
        try:
            eligibility[request['id']] = {'status': 'accepted', 'rows': engine.encoding_info(rows_for(request['body']))}
        except ValueError as error:
            eligibility[request['id']] = {'status': 'input_rejected', 'error': str(error)}
    write(RUN / 'execution/input-audit.json', eligibility)
    parity_rows = [rows_for(next(r for r in requests if r['id'] == case_id)['body'])[0]
                   for case_id in ['R01', 'C01-A']]
    write(RUN / 'execution/progress.json', {'phase': 'parity', 'at': time.time()})
    optimized = engine.logits(parity_rows)
    engine.model.marker_only_head = False
    try:
        original = engine.logits(parity_rows)
    finally:
        engine.model.marker_only_head = True
    deltas = [max(abs(a - b) for a, b in zip(x, y)) for x, y in zip(optimized, original)]
    same = [max(range(len(x)), key=x.__getitem__) == max(range(len(y)), key=y.__getitem__)
            for x, y in zip(optimized, original)]
    parity = {'rows': parity_rows, 'optimized_logits': optimized, 'original_logits': original,
              'max_logit_deltas': deltas, 'same_argmax': same, 'tolerance': 0.02,
              'scope': 'two fixed rows, without oracle data; not universal equivalence'}
    parity['passed'] = all(same) and max(deltas) <= 0.02
    write(RUN / 'execution/parity.json', parity)
    if not parity['passed']:
        raise ValueError('Optimized/original head parity failed before pilot')
    ledger = {'started_at': time.time(), 'attempted_questions': 4, 'completed': 0,
              'current': None, 'complete': False}
    write(RUN / 'execution/ledger.json', ledger)
    for request in requests:
        case_id = request['id']
        target = RUN / 'execution/records' / (case_id + '.json')
        if target.exists():
            raise FileExistsError('No blind repetition of an existing pilot record')
        record = {'id': case_id, 'domain': request['domain'], 'request_sha256': hashlib.sha256(encoded(request)).hexdigest(),
                  'questions': len(request['body']['questions']), 'input_audit': eligibility[case_id]}
        if eligibility[case_id]['status'] == 'input_rejected':
            record.update(status='input_rejected', elapsed_seconds=0)
        else:
            if ledger['attempted_questions'] + record['questions'] > 500:
                raise ValueError('Question budget exceeded')
            ledger['current'] = case_id
            ledger['attempted_questions'] += record['questions']
            write(RUN / 'execution/ledger.json', ledger)
            write(RUN / 'execution/progress.json', {'phase': 'inference', 'id': case_id, 'at': time.time()})
            engine.clear_cache()
            before = time.perf_counter()
            body = request['body']
            state = rows_for(body)[0]['state']
            response = engine.predict(state=state, questions=body['questions'])
            elapsed = time.perf_counter() - before
            if set(response.get('answers', {})) != set(body['questions']):
                raise ValueError('Missing or extra named answers')
            for answer in response['answers'].values():
                probabilities = answer['probabilities']
                if not all(math.isfinite(v) and 0 <= v <= 1 for v in probabilities.values()):
                    raise ValueError('Invalid answer probabilities')
                if abs(sum(probabilities.values()) - 1) > 1e-6:
                    raise ValueError('Invalid probability normalization')
            record.update(status='delivered', elapsed_seconds=elapsed, response=response)
        write(target, record, frozen=True)
        ledger['completed'] += 1
        ledger['current'] = None
        write(RUN / 'execution/ledger.json', ledger)
        print(json.dumps({'completed': ledger['completed'], 'total': 47, 'id': case_id,
                          'status': record['status'], 'seconds': record['elapsed_seconds']}), flush=True)
    ledger['complete'] = True
    write(RUN / 'execution/ledger.json', ledger)
    write(RUN / 'execution/progress.json', {'phase': 'finished', 'at': time.time()})


def run():
    manifest = verify()
    import psutil
    execution = RUN / 'execution'
    execution.mkdir(exist_ok=True)
    if (execution / 'start.json').exists():
        raise FileExistsError('Inference attempt already exists; inspect it instead of retrying')
    write(execution / 'start.json', {'at': time.time(), 'manifest_sha256': sha(RUN / 'manifest.json'),
                                     'host_cpu': platform.processor(), 'logical_cpus': psutil.cpu_count(),
                                     'physical_cpus': psutil.cpu_count(logical=False),
                                     'available_memory_bytes': psutil.virtual_memory().available}, frozen=True)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1',
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
    peak_child = peak_combined = 0
    samples = 0
    stop_reason = None
    started = time.monotonic()
    with (execution / 'worker.log').open('w', encoding='utf-8') as log:
        process = subprocess.Popen([str(PYTHON), '-B', str(Path(__file__).resolve()), 'worker'],
                                   cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        observed = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                child_rss = sum(p.memory_info().rss for p in [observed, *observed.children(recursive=True)]
                                if p.is_running())
                combined = child_rss + psutil.Process().memory_info().rss
                peak_child = max(peak_child, child_rss)
                peak_combined = max(peak_combined, combined)
                samples += 1
                progress = read(execution / 'progress.json') if (execution / 'progress.json').exists() else {}
                if combined > manifest['limits']['hard_rss_bytes']:
                    stop_reason = 'hard_rss_limit'
                elif time.monotonic() - started > 900:
                    stop_reason = 'global_inference_timeout'
                elif progress.get('phase') in {'inference', 'parity'} and time.time() - progress['at'] > 60:
                    stop_reason = 'per_request_timeout'
                if stop_reason:
                    process.kill()
                    break
            except psutil.NoSuchProcess:
                pass
            time.sleep(0.1)
        code = process.wait(timeout=15)
    memory = {'sampled_peak_worker_rss_bytes': peak_child, 'sampled_peak_combined_rss_bytes': peak_combined,
              'sampling_interval_seconds': 0.1, 'samples': samples,
              'target_one_gib_met': peak_combined <= 2**30,
              'hard_limit_bytes': 2 * 2**30, 'guard_stop': stop_reason,
              'exit_code': code, 'wall_seconds': time.monotonic() - started,
              'scope': 'worker and descendants plus monitoring parent; shared pages may be counted twice'}
    write(execution / 'resources.json', memory)
    from analyze import analyze
    analyze()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'run', 'worker'])
    command = parser.parse_args().command
    {'prepare': prepare, 'run': run, 'worker': worker}[command]()
