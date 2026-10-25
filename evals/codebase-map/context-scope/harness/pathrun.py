"""One real lifecycle path on a copy of the frozen project, through the public CLIs only.

natural request -> map and indexes -> scope and packet (preflight, task-packet) -> the task itself
(a real edit with a real oracle) -> refreshed map -> post-task delta -> verification -> map view
-> resume. The coordinator here is the script plus the model driving it; no installed host
workflow is exercised, and nothing here proves task success beyond its own oracle.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve()
ROOT = next(p for p in HERE.parents if (p / 'plugins/codebase-map/skills/map-method/scripts').is_dir())
SCRIPTS = Path(os.environ.get('CODEBASE_MAP_SCRIPTS', ROOT / 'plugins/codebase-map/skills/map-method/scripts'))
PLUGINS = Path(os.environ.get('PLUGINS_ROOT', ROOT / 'plugins'))
PROTOCOL = PLUGINS / 'work-controller/skills/work-record/scripts/run_state.py'
CYCLE = PLUGINS / 'project-lifecycle/skills/lifecycle-method/scripts/cycle_packets.py'
sys.path.insert(0, str(SCRIPTS))
import retrieval
import snapshot

REQUEST = 'Response.set_cookie lets a semicolon in the path or domain argument add extra cookie attributes such as Secure or HttpOnly to the header'
TARGET = 'starlette/responses.py::Response.set_cookie'
# Probed on Starlette 1.9.0 with Python 3.13.14 before choosing the scenario: http.cookies
# already refuses an illegal name and a control character in the value or path, so those were
# no defect. A semicolon in path or domain is copied into the header and injects attributes:
# the oracle fails before the edit. Any exception type counts as a refusal, and a valid cookie
# must still produce its Set-Cookie header.
ORACLE = (
    "import sys; sys.path.insert(0, sys.argv[1])\n"
    "from http.cookies import CookieError\n"
    "from starlette.responses import Response\n"
    "valid = Response()\n"
    "valid.set_cookie('session', 'v1', path='/app', domain='example.com')\n"
    "headers = [v.decode('latin-1') for k, v in valid.raw_headers if k == b'set-cookie']\n"
    "if not any(h.startswith('session=v1') and 'Path=/app' in h for h in headers):\n"
    "    raise SystemExit('valid cookie not emitted: ' + repr(headers))\n"
    "for options in ({'path': '/x; Secure'}, {'domain': 'example.com; HttpOnly'}):\n"
    "    try:\n"
    "        Response().set_cookie('session', 'v1', **options)\n"
    "    except (ValueError, CookieError):\n"
    "        continue\n"
    "    raise SystemExit('accepted ' + repr(options))\n"
    "print('oracle ok')\n")


def run(args, **options):
    started = time.perf_counter()
    result = subprocess.run([str(a) for a in args], capture_output=True, **options)
    return result, round(time.perf_counter() - started, 2)


def need(result, seconds, label, log):
    log.append({'step': label, 'seconds': seconds, 'exit': result.returncode,
                'stdout': result.stdout.decode('utf8', 'replace')[-600:], 'stderr': result.stderr.decode('utf8', 'replace')[-400:]})
    if result.returncode:
        raise SystemExit(f'{label} failed: ' + result.stderr.decode('utf8', 'replace')[-500:])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='frozen package directory (starlette)')
    parser.add_argument('--work', type=Path, required=True, help='new directory for the path run')
    parser.add_argument('--environment', type=Path, required=True, help='environment holding the package dependencies and Jedi')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    work, log = args.work.resolve(), []
    project = work / 'project'
    shutil.copytree(args.source, project / args.source.name, ignore=shutil.ignore_patterns('__pycache__'))
    maps = project / '.codebase-map'
    for name in ('m0', 'm1'):
        (maps / name).mkdir(parents=True)
    records = project / '.daodan'
    m0, m1 = maps / 'm0/snapshot.sqlite', maps / 'm1/snapshot.sqlite'
    python = sys.executable

    snapshot.write_snapshot(project, m0)
    started = time.perf_counter()
    retrieval.refresh_index(m0, m0.with_name('retrieval.sqlite'))
    log.append({'step': 'retrieval index', 'seconds': round(time.perf_counter() - started, 2)})
    need(*run([python, '-B', SCRIPTS / 'resolve_edges.py', m0, '--environment', args.environment, '--compact']), 'jedi edges', log)

    payload = dict(operation='change', objective='Refuse cookie attribute injection through path or domain in set_cookie',
        scope={'paths': ['starlette']}, authorizations={'fix': True}, budget={}, required_gates=['oracle'],
        waves=[{'id': 'wave-one', 'parallel': False, 'status': 'pending', 'tasks': [{
            'id': 'T1', 'status': 'pending', 'write_set': ['starlette/responses.py'],
            'requirements': [{'id': 'R1', 'text': 'set_cookie refuses a path or domain containing a semicolon and still emits valid cookies',
                'support': [{'predicate': 'current_source', 'entity_id': TARGET}]}],
            'oracle': {'command': 'python oracle.py', 'expected_failure': 'accepted'},
            'verification': {'command': 'python oracle.py'}}]}])
    init = work / 'init.json'
    init.write_text(json.dumps(payload), encoding='utf8')
    common = ['--project', project, '--run-id', 'pathrun', '--session', 'pathrun-coordinator']
    need(*run([python, '-B', PROTOCOL, 'init', *common, '--payload', init]), 'protocol init', log)

    config = dict(project=str(project), run_id='pathrun', manifest=str(m0),
                  protocol=[python, '-B', str(PROTOCOL)], provider=[python, '-B', str(SCRIPTS / 'snapshot.py')],
                  indexes={'retrieval': str(m0.with_name('retrieval.sqlite'))})
    request = dict(schema='daodan/context-request/v1', task_id='ignored-caller-id', intent='bug', query=REQUEST,
        read_boundary=['.'], write_boundary=['.'], anchors=[], base=None, candidate=None, diff=[],
        proposed_edits=[], mandatory_requirements=[], required_gates=[], policy_version='scope-v1',
        budget=dict(max_candidates=100, max_edges=1000, max_rounds=100, max_seconds=120,
                    max_input_tokens=1000000, max_output_tokens=1000000))
    recipient = dict(id='pathrun-worker', available_tokens=200000, reserve_tokens=2000, max_chars=24000, max_evaluations=2000)
    for name, value in (('config', config), ('request', request), ('recipient', recipient)):
        (work / (name + '.json')).write_text(json.dumps(value), encoding='utf8')

    def cycle(operation, *extra):
        result, seconds = run([python, '-B', CYCLE, operation, '--config', work / 'config.json', '--request', work / 'request.json',
                               '--recipient', work / 'recipient.json', *extra])
        need(result, seconds, 'cycle ' + operation, log)
        return json.loads(result.stdout)

    preflight = cycle('preflight')
    task = cycle('task-packet', '--task-id', 'T1', '--previous', preflight['path'])
    packet = json.loads(Path(json.loads(Path(task['path']).read_bytes())['packet']['path']).read_bytes())
    delivered = sorted({b['path'] for b in packet['blocks'] if b.get('kind') == 'source'})
    resumed = cycle('task-packet', '--task-id', 'T1', '--previous', preflight['path'])
    verify = lambda receipt: json.loads(need(*run([python, '-B', CYCLE, 'verify', '--config', work / 'config.json', '--receipt', receipt]), 'cycle verify', log).stdout)
    checked = verify(task['path'])

    (work / 'oracle.py').write_text(ORACLE, encoding='utf8')
    before, _ = run([python, work / 'oracle.py', project], env={**os.environ, 'PYTHONPATH': str(args.environment / 'Lib/site-packages')})
    target = project / 'starlette/responses.py'
    text = target.read_text(encoding='utf8')
    marker = '    def set_cookie('
    start = text.index(marker)
    signature_end = text.index(':\n', start) + 2
    guard = ("        if ';' in (path or '') or ';' in (domain or ''):\n"
             "            raise ValueError('Cookie path and domain must not contain a semicolon')\n")
    target.write_text(text[:signature_end] + guard + text[signature_end:], encoding='utf8', newline='\n')
    after, _ = run([python, work / 'oracle.py', project], env={**os.environ, 'PYTHONPATH': str(args.environment / 'Lib/site-packages')})

    need(*run([python, '-B', PROTOCOL, 'update', *common, '--expected-revision', json.loads(Path(records / 'runs/pathrun/work.json').read_bytes())['revision'],
               '--payload', _write(work / 'barrier.json', {'barrier': 'task T1 applied'})]), 'protocol barrier', log)
    snapshot.write_snapshot(project, m1)
    # The indexes belong to one candidate: the refreshed manifest needs its own retrieval index and edges.
    started = time.perf_counter()
    retrieval.refresh_index(m1, m1.with_name('retrieval.sqlite'))
    log.append({'step': 'retrieval index m1', 'seconds': round(time.perf_counter() - started, 2)})
    need(*run([python, '-B', SCRIPTS / 'resolve_edges.py', m1, '--environment', args.environment, '--compact']), 'jedi edges m1', log)
    config['manifest'] = str(m1)
    config['indexes'] = {'retrieval': str(m1.with_name('retrieval.sqlite'))}
    (work / 'config.json').write_text(json.dumps(config), encoding='utf8')
    post = cycle('post-task', '--task-id', 'T1', '--previous', task['path'])
    post_receipt = json.loads(Path(post['path']).read_bytes())
    map_view, seconds = run([python, '-B', SCRIPTS / 'semantic_map.py', m1, '--path', 'starlette/responses.py'])
    need(map_view, seconds, 'semantic map', log)
    old_still_stale = run([python, '-B', CYCLE, 'verify', '--config', work / 'config.json', '--receipt', task['path']])[0].returncode

    report = {'schema': 'daodan/pathrun/v1', 'request': REQUEST, 'target': TARGET,
        'preflight': preflight, 'task_packet': {**task, 'delivered_source_files': delivered,
            'target_in_packet': any(TARGET.split('::')[0] == p for p in delivered)},
        'resume_returns_same_receipt': resumed['path'] == task['path'] and resumed['sha256'] == task['sha256'],
        'verify_task_packet': checked,
        'oracle': {'before_edit_exit': before.returncode, 'after_edit_exit': after.returncode,
                   'before': before.stderr.decode()[-120:] + before.stdout.decode()[-80:], 'after': after.stdout.decode()[-60:]},
        'post_task': {**post, 'residual_obligations': [{k: o.get(k) for k in ('id', 'kind', 'status')} for o in post_receipt['residual_obligations']],
                      'write_authorized': post_receipt['write_authorized'], 'task_complete': post_receipt['task_complete']},
        'old_receipt_refused_after_refresh_exit': old_still_stale,
        'semantic_map': json.loads(map_view.stdout)['coverage'], 'steps': log,
        'limits': ['The edit is made by the script; no LLM worker was dispatched.',
                   'The coordinator is a script, not an installed host workflow.',
                   'The oracle is a behaviour check (a semicolon in path or domain refused with any exception, a valid cookie emitted), not the library test suite.']}
    args.out.write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({k: report[k] for k in ('resume_returns_same_receipt', 'oracle', 'old_receipt_refused_after_refresh_exit')}, indent=1))
    print(json.dumps(report['task_packet'], indent=1)[:600])


def _write(path, value):
    Path(path).write_text(json.dumps(value), encoding='utf8')
    return path


if __name__ == '__main__':
    main()
