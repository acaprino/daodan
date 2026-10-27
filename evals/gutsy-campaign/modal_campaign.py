"""One CPU container; durable per-request evidence and conservative resume."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tarfile
import threading
import time
import urllib.error
import urllib.request

import modal

from campaign_ledger import (Ledger, MAX_SECONDS, MODEL, atomic_json, digest,
                             validate_requests, validate_response)

HERE = Path(__file__).resolve().parent
GUTSY_COMMIT = 'db5c2ec62fc81703938adbd714915b53a9fb0de1'
HF_REVISION = 'f9995fe26a337f1a4ea3f1a5ed38c9799e5a8f63'
WEIGHT = 'gutsy-0.8b-v04-q4_k_m.gguf'
CALIBRATION = 'gutsy-0.8b-v04-q4_k_m.calibration.json'
WEIGHT_SHA = 'ddf9c23b8a07c008172f1731f4dd93c464b651b9a70409f0feaf8c2d4e089152'
CALIBRATION_SHA = '4326b804cfec2e6316c9f7740e03491319a87a89dfae04a2c937176d8ba03577'
VOLUME_NAME = 'gutsy-cpu-campaign-20261026'
MOUNT = Path('/campaign')
CPU_MEMORY_RATE = 4 * 0.0000131 + 4 * 0.00000222
RSS_STOP = 3840 * 2**20

volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
image = (modal.Image.debian_slim(python_version='3.12')
         .apt_install('git', 'build-essential', 'cmake')
         .env({'CMAKE_ARGS': '-DGGML_NATIVE=OFF', 'OMP_NUM_THREADS': '4',
               'OPENBLAS_NUM_THREADS': '4', 'MKL_NUM_THREADS': '4',
               'PYTHONPATH': '/opt/campaign'})
         .pip_install('numpy==2.3.4', 'llama-cpp-python==0.3.36',
                      extra_index_url='https://abetlen.github.io/llama-cpp-python/whl/cpu')
         .pip_install(f'git+https://github.com/kouhxp/gutsy.git@{GUTSY_COMMIT}#subdirectory=gutsy-inference')
         .add_local_file(HERE / 'campaign_ledger.py', '/opt/campaign/campaign_ledger.py')
         .add_local_file(HERE / 'server_bootstrap.py', '/opt/campaign/server_bootstrap.py')
         .add_local_file(HERE / 'modal_campaign.py', '/opt/campaign/modal_campaign.py'))
app = modal.App('gutsy-q4-cpu-campaign')


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(2**20), b''):
            result.update(chunk)
    return result.hexdigest()


def http_json(url, body=None, timeout=180):
    data = None if body is None else json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
    request = urllib.request.Request(url, data=data,
                                    headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def read_optional(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


class MemorySampler:
    def __init__(self):
        self.done = threading.Event()
        self.thread = threading.Thread(target=self.sample, daemon=True)
        self.latest = self.peak = 0
        self.server = None
        self.exceeded = False

    def sample(self):
        while not self.done.is_set():
            rows = {}
            for entry in Path('/proc').iterdir():
                if not entry.name.isdigit():
                    continue
                try:
                    parent = int((entry / 'stat').read_text().rsplit(') ', 1)[1].split()[1])
                    rss = next(int(line.split()[1]) * 1024 for line in
                               (entry / 'status').read_text().splitlines() if line.startswith('VmRSS:'))
                    rows[int(entry.name)] = (parent, rss)
                except (OSError, ValueError, IndexError, StopIteration):
                    continue
            members = {os.getpid()}
            while True:
                expanded = members | {pid for pid, (parent, _) in rows.items() if parent in members}
                if expanded == members:
                    break
                members = expanded
            self.latest = sum(rows.get(pid, (0, 0))[1] for pid in members)
            self.peak = max(self.peak, self.latest)
            if self.latest >= RSS_STOP:
                self.exceeded = True
                if self.server and self.server.poll() is None:
                    self.server.terminate()
            self.done.wait(.25)

    def start(self):
        self.thread.start()

    def close(self):
        self.done.set()
        self.thread.join(timeout=2)


def environment():
    packages = {}
    for name in ['numpy', 'llama-cpp-python', 'gutsy-inference', 'modal']:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    distribution = importlib.metadata.distribution('llama-cpp-python')
    native = {str(p): file_hash(distribution.locate_file(p)) for p in distribution.files or []
              if Path(p).name in {'libllama.so', 'libggml.so', 'libggml-cpu.so'}}
    return {'packages': packages, 'native_library_hashes': native, 'python': sys.version,
            'platform': platform.platform(), 'cpuinfo': read_optional('/proc/cpuinfo'),
            'host_identity': read_optional('/proc/sys/kernel/random/boot_id'),
            'cpu_max': read_optional('/sys/fs/cgroup/cpu.max'),
            'memory_max': read_optional('/sys/fs/cgroup/memory.max')}


def ensure_models(directory, ledger):
    directory.mkdir(parents=True, exist_ok=True)
    records = {}
    for name in [WEIGHT, CALIBRATION]:
        target = directory / name
        if not target.exists():
            temporary = target.with_suffix(target.suffix + '.download')
            url = f'https://huggingface.co/kouhxp/gutsy/resolve/{HF_REVISION}/{name}'
            with urllib.request.urlopen(url, timeout=60) as source, temporary.open('wb') as out:
                for chunk in iter(lambda: source.read(2**20), b''):
                    ledger.check_budget()
                    out.write(chunk)
            temporary.replace(target)
        records[name] = {'sha256': file_hash(target), 'bytes': target.stat().st_size}
    if records[WEIGHT] != {'sha256': WEIGHT_SHA, 'bytes': 529296832}:
        raise ValueError('Downloaded weights do not match frozen Q4 artifact')
    if records[CALIBRATION] != {'sha256': CALIBRATION_SHA, 'bytes': 281}:
        raise ValueError('Calibration differs from the frozen Q4 artifact')
    json.loads((directory / CALIBRATION).read_text())
    volume.commit()
    return records


def start_server(profile, requests, work, models, ledger, sampler):
    work.mkdir(parents=True, exist_ok=True)
    config = {'default': MODEL, 'models': {MODEL: {
        'gguf': str(models / WEIGHT), 'calibration': str(models / CALIBRATION),
        'n_ctx': profile['n_ctx'], 'reject_slot': True, 'cache_tol': .02}},
        'n_threads': profile['threads'], 'n_gpu_layers': 0,
        'cache_entries': 1 if profile['cache'] == 'lru' else 0,
        'cache_mb': 128 if profile['cache'] == 'lru' else 0}
    atomic_json(work / 'models.json', config)
    atomic_json(work / 'requests.json', requests)
    preflight_path = work / 'preflight.json'
    if preflight_path.exists():
        preflight_path.unlink()
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    ledger.reserve_startup(0 if profile['cache'] == 'full' else 6)
    log = (work / 'server.log').open('ab')
    started = time.monotonic()
    process = subprocess.Popen([
        sys.executable, '/opt/campaign/server_bootstrap.py', '--config', str(work / 'models.json'),
        '--port', str(port), '--cache-mode', profile['cache'],
        '--requests', str(work / 'requests.json'), '--preflight', str(preflight_path),
        '--token-cache', str(work.parent / 'token-counts.json')],
        stdout=log, stderr=subprocess.STDOUT,
        env={**os.environ, 'OMP_NUM_THREADS': str(profile['threads']),
             'OPENBLAS_NUM_THREADS': str(profile['threads']), 'MKL_NUM_THREADS': str(profile['threads'])})
    sampler.server = process
    base = f'http://127.0.0.1:{port}'
    try:
        while True:
            ledger.check_budget()
            if process.poll() is not None or sampler.exceeded:
                raise RuntimeError('Server exited during load/token preflight: ' +
                                   (work / 'server.log').read_text(errors='replace')[-6000:])
            if time.monotonic() - started > 1200:
                raise TimeoutError('Server/token preflight exceeded 20 minutes')
            try:
                health = http_json(base + '/health', timeout=2)
                break
            except (urllib.error.URLError, TimeoutError):
                time.sleep(.3)
        if set(health.get('models', {})) != {MODEL} or not health['models'][MODEL]['loaded']:
            raise ValueError('Health must attest exactly one loaded Q4 model')
        preflight = json.loads(preflight_path.read_text())
        if profile['cache'] != 'full' and not preflight['cache_enabled']:
            raise ValueError('Requested cache path unavailable; do not mix runtime modes')
        return process, log, base, preflight, time.monotonic() - started
    except BaseException:
        stop_server(process, log)
        raise


def stop_server(process, log):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if log is not None:
        log.close()


def resolved_request(request, records):
    directive = request.get('subset')
    if not directive:
        return request
    body = dict(request['body'])
    if directive['kind'] == 'fixed':
        keys = directive['question_ids']
    elif directive['kind'] == 'family_gate':
        source = records.get(directive['source_request'])
        if source is None or source['status'] != 'delivered':
            raise ValueError('Hierarchy predecessor is not delivered')
        probabilities = source['response']['answers']
        keys = [q for q, family in directive['family_for_question'].items()
                if probabilities[family]['noul'] >= directive['threshold']]
    else:
        raise ValueError('Unknown frozen subset procedure')
    body['questions'] = {key: value for key, value in body['questions'].items() if key in keys}
    return {**request, 'body': body, 'planned_request_hash': digest(request)}


def attest_cache(profile, response, question_count):
    if question_count == 0:
        return {'called': False, 'mode': profile['cache']}
    usage = response.get('usage', {})
    expected = profile['cache'] != 'full'
    if usage.get('state_cached') is not expected:
        raise ValueError('Observed cache execution differs from the requested profile')
    if not isinstance(usage.get('state_cache_hit'), bool):
        raise ValueError('Cache hit accounting is missing')
    if profile['cache'] != 'lru' and usage['state_cache_hit']:
        raise ValueError('Unexpected inter-request cache hit in a no-LRU profile')
    return {'called': True, 'mode': profile['cache'],
            'state_cached': usage['state_cached'], 'state_cache_hit': usage['state_cache_hit']}


def parity_gate(requests, records, tolerance=.02, contract='three-path-v1'):
    if contract not in {'three-path-v1', 'cached-paths-v2'}:
        raise ValueError('Unknown preregistered parity contract')
    groups = {}
    for request in requests:
        if request['block'] != 'runtime-parity':
            continue
        record = records.get(request['id'])
        if not record or record['status'] != 'delivered':
            raise ValueError('Runtime parity block incomplete')
        groups.setdefault(request['parity_group'], {})[request['profile']] = record['response']
    maxima, cached_maxima = {}, {}
    for group, variants in groups.items():
        if set(variants) != {'main', 't4c4096', 'full'}:
            raise ValueError('Parity needs all three execution paths')
        maximum = 0.0
        for key, baseline in variants['full']['answers'].items():
            for mode in ['main', 't4c4096']:
                answer = variants[mode]['answers'][key]
                if 'noul' in baseline:
                    maximum = max(maximum, abs(baseline['noul'] - answer['noul']))
                else:
                    for label, probability in baseline['probabilities'].items():
                        maximum = max(maximum, abs(probability - answer['probabilities'][label]))
                    maximum = max(maximum, abs(baseline['reject'] - answer['reject']))
        maxima[group] = maximum
        cached_delta = 0.0
        for key, baseline in variants['main']['answers'].items():
            other = variants['t4c4096']['answers'][key]
            if 'noul' in baseline:
                cached_delta = max(cached_delta, abs(baseline['noul'] - other['noul']))
            else:
                cached_delta = max(cached_delta, abs(baseline['reject'] - other['reject']))
                for label, probability in baseline['probabilities'].items():
                    cached_delta = max(cached_delta, abs(probability - other['probabilities'][label]))
        cached_maxima[group] = cached_delta
    gated = maxima if contract == 'three-path-v1' else cached_maxima
    if not groups or any(value > tolerance for value in gated.values()):
        raise ValueError(f'Runtime parity tolerance exceeded ({contract}): {gated}')
    return {'contract': contract, 'max_probability_delta': gated, 'tolerance': tolerance,
            'full_reencoding_max_probability_delta': maxima,
            'full_reencoding_equivalence_claimed': contract == 'three-path-v1',
            'scope': 'three frozen development inputs; no universal equivalence or same-quality speedup claim'}


def forecast_gate(requests, records, tokens, profiles, elapsed, factor=1.25,
                  checkpoint_seconds_per_request=0):
    import numpy as np
    samples = []
    for request in requests:
        if request['block'] == 'development-probe':
            record = records.get(request['id'])
            if not record or record['status'] != 'delivered':
                raise ValueError('Development timing probes incomplete')
            evaluated = record['response'].get('usage', {}).get('evaluated_tokens')
            if not isinstance(evaluated, (float, int)) or evaluated <= 0:
                raise ValueError('Timing probe lacks actual evaluated token accounting')
            samples.append(([evaluated, len(request['body']['questions']), 1], record['elapsed_seconds']))
    if not samples:
        raise ValueError('No observed development workload for time estimate')
    x = np.asarray([item[0] for item in samples], dtype=float)
    y = np.asarray([item[1] for item in samples], dtype=float)
    # Nonnegative fit over seven active sets. NumPy is already a required
    # dependency of the pinned runtime; no extra estimator is installed.
    fits = []
    for mask in range(1, 8):
        columns = [i for i in range(3) if mask & (1 << i)]
        values, *_ = np.linalg.lstsq(x[:, columns], y, rcond=None)
        if np.any(values < 0):
            continue
        weights = np.zeros(3)
        weights[columns] = values
        fits.append((float(np.sum((x @ weights - y) ** 2)), weights))
    weights = min(fits, key=lambda row: row[0])[1]
    observed_ratio = max(1.0, float(np.max(y / np.maximum(x @ weights, 1e-6))))
    remaining = 0.0
    for request in requests:
        if request['id'] in records:
            continue
        info = tokens[request['id']]
        profile = profiles[request['profile']]
        count = len(request['body']['questions'])
        # Assume no inter-request prefix hit. Intra-request snapshots share it.
        evaluated = (sum(info['question_prompt_tokens'].values()) if profile['cache'] == 'full'
                     else info['state_tokens'] + sum(value - info['state_tokens']
                                                    for value in info['question_prompt_tokens'].values()))
        seconds = float(np.asarray([evaluated, count, 1]) @ weights)
        remaining += seconds * (4 / profile['threads']) + checkpoint_seconds_per_request
    estimate = elapsed + remaining * observed_ratio * factor + 1200
    if estimate > MAX_SECONDS:
        raise TimeoutError(f'Frozen campaign forecast {estimate:.0f}s exceeds {MAX_SECONDS}s; replan before verification')
    return {'seconds_coefficients_tokens_questions_request': weights.tolist(),
            'max_observed_actual_to_fit_ratio': observed_ratio, 'probe_requests': len(samples),
            'observed_checkpoint_seconds_per_request': checkpoint_seconds_per_request,
            'safety_factor': factor,
            'forecast_total_seconds': estimate, 'startup_allowance_seconds': 1200,
            'limitation': 'Development estimate; actual longer contexts and host scheduling may differ'}


@app.function(image=image, volumes={str(MOUNT): volume}, cpu=(4.0, 4.0),
              memory=(1024, 4096), timeout=23 * 3600, max_containers=1,
              retries=0, scaledown_window=2, include_source=False)
def run_campaign(run_key: str, input_hash: str, code_hash: str):
    if not run_key.replace('-', '').isalnum():
        raise ValueError('Invalid run key')
    directory = MOUNT / run_key
    source = directory / 'input.json'
    if file_hash(source) != input_hash:
        raise ValueError('Uploaded input bytes changed')
    payload = json.loads(source.read_text(encoding='utf-8'))
    actual_code_hash = digest({name: file_hash(Path('/opt/campaign') / name) for name in
                              ['modal_campaign.py', 'server_bootstrap.py', 'campaign_ledger.py']})
    if actual_code_hash != code_hash:
        raise ValueError('Remote executor files differ from local frozen source')
    validate_requests(payload['requests'])
    parent_binding = payload.get('budget_parent')
    parent_evidence = None
    if parent_binding:
        parent_key = parent_binding['run_key']
        if not parent_key.replace('-', '').isalnum() or parent_key == run_key:
            raise ValueError('Unsafe or circular budget parent')
        parent_path = MOUNT / parent_key / 'ledger.json'
        parent = json.loads(parent_path.read_text(encoding='utf-8'))
        if parent['input_hash'] != parent_binding['input_hash'] or parent.get('requests'):
            raise ValueError('Budget parent identity differs or has unresolved requests')
        if parent['status'] not in {'incomplete', 'completed'}:
            raise ValueError('Budget parent is still active')
        carried = parent['attempted_questions'] + parent['startup_question_reserve'] + parent.get('carried_questions', 0)
        parent_evidence = {'run_key': parent_key, 'ledger_sha256': file_hash(parent_path), 'ledger': parent}
        ledger = Ledger(directory, input_hash, code_hash, volume.commit,
                        budget_origin=parent['started_at'], carried_questions=carried,
                        budget_parent=parent_binding)
        atomic_json(directory / 'budget-parent.json', parent_evidence)
        volume.commit()
    else:
        ledger = Ledger(directory, input_hash, code_hash, volume.commit)
    if ledger.state['complete']:
        return {'ledger': ledger.state,
                'runtime': json.loads((directory / 'runtime-summary.json').read_text())}
    runtime = environment()
    attempt_id = str(time.time_ns())
    attempt_path = directory / f'runtime-{attempt_id}.json'
    runtime.update({'gutsy_commit': GUTSY_COMMIT, 'hf_revision': HF_REVISION,
                    'model': MODEL, 'profiles': [], 'input_hash': input_hash,
                    'code_hash': code_hash, 'resource_rate_per_second': CPU_MEMORY_RATE,
                    'attempt_id': attempt_id, 'budget_parent': parent_evidence})
    atomic_json(directory / f'environment-{attempt_id}.json', runtime)
    volume.commit()
    sampler = MemorySampler()
    sampler.start()
    server = log = None
    records = {}
    active_profile = None
    preflight = None
    try:
        runtime['model_artifacts'] = ensure_models(MOUNT / 'models', ledger)
        requests = payload['requests']
        for position, planned in enumerate(requests):
            request = resolved_request(planned, records)
            old = ledger.existing(request)
            if old is not None:
                records[request['id']] = old
                if old['status'] == 'failed':
                    raise RuntimeError('Previous failed request requires explicit reconciliation')
                continue
            ledger.check_budget()
            if sampler.exceeded:
                raise MemoryError('Combined worker/server RSS guard reached')
            profile = payload['profiles'][request['profile']]
            if active_profile != request['profile']:
                stop_server(server, log)
                server = log = None
                # Tokenize all known states using this profile before its first
                # inference; no gold or labels are uploaded to the worker.
                profile_requests = [r for r in requests if r['profile'] == request['profile']]
                server, log, base, preflight, startup = start_server(
                    profile, requests, directory / 'runtime' / request['profile'],
                    MOUNT / 'models', ledger, sampler)
                active_profile = request['profile']
                runtime['profiles'].append({'profile': active_profile, 'startup_seconds': startup,
                                            'self_check': preflight['self_check'],
                                            'cache_enabled': preflight['cache_enabled']})
                incompatible = [r['id'] for r in profile_requests
                                if preflight['requests'][r['id']]['max_prompt_tokens'] >= profile['n_ctx']
                                and not r.get('allow_input_limit')]
                if incompatible:
                    raise ValueError(f'Prerecorded profile input limits exceeded: {incompatible[:12]}')
                atomic_json(attempt_path, runtime)
                volume.commit()
            if planned['block'] != 'runtime-parity' and 'parity_gate' not in runtime:
                runtime['parity_gate'] = parity_gate(requests, records,
                                                     contract=payload.get('parity_contract', 'three-path-v1'))
                atomic_json(directory / 'parity-gate.json', runtime['parity_gate'])
                volume.commit()
            if planned['block'] not in {'runtime-parity', 'development-probe'} and 'forecast_gate' not in runtime:
                runtime['forecast_gate'] = forecast_gate(requests, records, preflight['requests'],
                                                          payload['profiles'], ledger.elapsed(),
                                                          payload['forecast_safety_factor'],
                                                          2 * ledger.write_seconds / max(1, ledger.write_count))
                atomic_json(directory / 'forecast-gate.json', runtime['forecast_gate'])
                volume.commit()
            token_info = preflight['requests'][request['id']]
            if token_info['max_prompt_tokens'] >= profile['n_ctx']:
                records[request['id']] = ledger.input_limit(request, token_info)
                continue
            ledger.begin(request)
            started = time.monotonic()
            record = {'status': 'delivered', 'profile': active_profile,
                      'attempt_id': attempt_id, 'host_identity': runtime['host_identity'],
                      'tokens': token_info, 'executed_body': request['body'] if planned.get('subset') else None}
            try:
                if request['body']['questions']:
                    response = http_json(base + '/v1/systemone', request['body'],
                                         timeout=min(600, MAX_SECONDS - ledger.elapsed()))
                else:
                    response = {'model': MODEL, 'answers': {}, 'usage': {'model_calls': 0}}
                record['response'] = response
                validate_response(request['body'], response)
                record['cache_attestation'] = attest_cache(profile, response, len(request['body']['questions']))
            except Exception as error:
                record['status'] = 'failed'
                record['error'] = {'type': type(error).__name__, 'message': str(error)}
                if isinstance(error, urllib.error.HTTPError):
                    record['error']['body'] = error.read().decode(errors='replace')[:8000]
            record['elapsed_seconds'] = time.monotonic() - started
            record['combined_rss_bytes'] = sampler.latest
            records[request['id']] = ledger.finish(request, record)
            ledger.check_budget()
            if record['status'] != 'delivered':
                raise RuntimeError('HTTP/runtime failure; no blind retry after possible live inference')
            if position % 25 == 0:
                print('CAMPAIGN_PROGRESS ' + json.dumps({'completed': position + 1, 'total': len(requests),
                      'questions': ledger.state['attempted_questions'], 'elapsed': ledger.elapsed(),
                      'profile': active_profile, 'rss': sampler.latest}), flush=True)
        ledger.check_budget()
        ledger.state['complete'] = True
        ledger.state['status'] = 'completed'
    except Exception as error:
        ledger.state['status'] = 'incomplete'
        ledger.state['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        stop_server(server, log)
        sampler.close()
        runtime['memory'] = {'sampled_peak_combined_rss_bytes': sampler.peak,
                             'rss_guard_triggered': sampler.exceeded,
                             'kernel_cgroup_peak': read_optional('/sys/fs/cgroup/memory.peak'),
                             'method': 'sum of worker and descendants VmRSS; shared pages may double count'}
        runtime['elapsed_global_seconds'] = ledger.elapsed()
        runtime['estimated_compute_usd'] = ledger.elapsed() * CPU_MEMORY_RATE
        runtime['checkpoint'] = {'write_seconds': ledger.write_seconds,
                                 'write_count': ledger.write_count,
                                 'scope': 'this worker attempt, excluding final report/archive commits'}
        atomic_json(attempt_path, runtime)
        runtime['attempt_reports'] = [p.name for p in sorted(directory.glob('runtime-*.json'))
                                      if p.name != 'runtime-summary.json']
        atomic_json(directory / 'runtime-summary.json', runtime)
        ledger.save()
        # One bounded download after completion; exclude the repeated runtime
        # input copies and the model weights. Each original record stays on Volume.
        bundle = directory / 'evidence.tar.gz'
        with tarfile.open(bundle, 'w:gz') as archive:
            evidence = list((directory / 'records').glob('*.json'))
            evidence += [directory / name for name in
                         ['ledger.json', 'runtime-summary.json', 'parity-gate.json', 'forecast-gate.json', 'budget-parent.json']]
            evidence += list(directory.glob('environment-*.json'))
            evidence += [p for p in directory.glob('runtime-*.json') if p.name != 'runtime-summary.json']
            evidence += [directory / 'runtime/token-counts.json']
            evidence += list((directory / 'runtime').glob('*/server.log'))
            for path in evidence:
                if path.is_file():
                    archive.add(path, arcname=str(path.relative_to(directory)), recursive=False)
        volume.commit()
        print('CAMPAIGN_STOP ' + json.dumps({'complete': ledger.state['complete'],
              'status': ledger.state['status'], 'error': ledger.state.get('error'),
              'questions': ledger.state['attempted_questions']}), flush=True)
    return {'ledger': ledger.state, 'runtime': runtime}


@app.local_entrypoint()
def main(input_path: str, receipt_path: str, run_key: str = 'campaign-20261026'):
    source, receipt = Path(input_path).resolve(), Path(receipt_path).resolve()
    if not receipt.is_relative_to(Path.cwd().resolve()) or receipt.exists():
        raise ValueError('Receipt must be a new workspace-owned file')
    payload = json.loads(source.read_text(encoding='utf-8'))
    validate_requests(payload['requests'])
    manifest_path = source.parent / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    workspace = HERE.parents[1]
    for relative, expected in manifest['source_hashes'].items():
        candidate = (workspace / relative).resolve()
        if not candidate.is_relative_to(workspace) or file_hash(candidate) != expected:
            raise ValueError(f'Source drift after corpus freeze: {relative}')
    code_hash = digest({name: file_hash(HERE / name) for name in
                        ['modal_campaign.py', 'server_bootstrap.py', 'campaign_ledger.py']})
    input_hash = file_hash(source)
    if input_hash != manifest['input_sha256']:
        raise ValueError('Input differs from frozen manifest')
    # Resume can reuse identical uploaded bytes, but never replace a corpus.
    remote_path = f'/{run_key}/input.json'
    try:
        remote_digest = hashlib.sha256()
        for chunk in volume.read_file(remote_path):
            remote_digest.update(chunk)
        if remote_digest.hexdigest() != input_hash:
            raise ValueError('Existing remote input differs; use a new run identity')
    except FileNotFoundError:
        with volume.batch_upload() as upload:
            upload.put_file(str(source), remote_path)
    call = run_campaign.spawn(run_key, input_hash, code_hash)
    invocation = {'app_id': app.app_id, 'function_call_id': call.object_id,
                  'volume': VOLUME_NAME, 'run_key': run_key, 'input_sha256': input_hash,
                  'code_hash': code_hash, 'started_at': time.time(),
                  'artifacts_directory': str(source.parent.relative_to(workspace)).replace('\\', '/')}
    atomic_json(receipt, invocation)
    print('CAMPAIGN_INVOCATION ' + json.dumps(invocation), flush=True)
    # Use `modal run --detach`: the paid function then survives client loss.
    # A KeyboardInterrupt does not silently cancel the authorized campaign.
    result = call.get()
    atomic_json(receipt.with_name(receipt.stem + '-completion.json'), result)
    print(json.dumps({'complete': result['ledger']['complete'],
                      'status': result['ledger']['status']}), flush=True)
