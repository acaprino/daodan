"""Revision-bound lifecycle receipts over the public protocol and map CLIs.

This adapter prepares evidence. The coordinator owns refresh, dispatch, run
updates, authorizations and completion. No cross-plugin imports or LLM calls.
Exit status is 2 for an incomplete or unreadable invocation and 1 for a refused
lifecycle operation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile

SCHEMA = 'daodan/cycle-context/v1'
STAGES = ('preflight', 'task-packet', 'post-task')


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def _digest(value):
    return hashlib.sha256(_bytes(value).rstrip(b'\n')).hexdigest()


def _path(value, root=None):
    path = Path(value)
    if not path.is_absolute():
        raise ValueError('Lifecycle paths must be absolute')
    for item in (path, *path.parents):
        if item.is_symlink() or item.is_junction():
            raise ValueError('Lifecycle paths must not traverse links')
    path = path.resolve()
    if root is not None and not path.is_relative_to(root):
        raise ValueError('Lifecycle artifact escapes its owner')
    return path


def _relative(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError('Expected a project-relative POSIX path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Project path escapes its scope')
    return path.as_posix()


def _inside(path, boundaries):
    return any(b == '.' or path == b or path.startswith(b + '/') for b in boundaries)


def _publish(path, value):
    """Exclusive atomic publication; identical journal replay is harmless."""
    path = _path(path)
    data = _bytes(value)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Lifecycle evidence collision')
        return
    descriptor, name = tempfile.mkstemp(prefix='.cycle-', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        _path(path)
        try:
            os.link(temporary, path)
        except FileExistsError:
            if _path(path).read_bytes() != data:
                raise ValueError('Lifecycle evidence collision')
    finally:
        temporary.unlink()


def _invoke(config, owner, args):
    command = config[owner]
    if not isinstance(command, list) or not command or any(not isinstance(v, str) or not v for v in command):
        raise ValueError('Provider commands must be explicit argument arrays')
    result = subprocess.run([*command, *args], cwd=config['project'], stdin=subprocess.DEVNULL,
                            capture_output=True, timeout=120)
    if result.returncode:
        raise ValueError(owner + ' rejected the operation: ' + result.stderr.decode('utf8', 'replace')[-2000:])
    try:
        return json.loads(result.stdout)
    except (ValueError, UnicodeError) as error:
        raise ValueError(owner + ' returned an invalid JSON delivery') from error


def _record(config):
    project = _path(config['project'])
    records = _path(config['records_root'])
    common = ['--project', str(project), '--out', str(records), '--run-id', config['run_id']]
    record = _invoke(config, 'protocol', ['show', *common])
    check = _invoke(config, 'protocol', ['validate', *common, '--current'])
    if (not check.get('valid') or check.get('revision') != record['revision']
            or record['run_id'] != config['run_id'] or record['status'] != 'in_progress'
            or _path(record['candidate']['root']) != project or _path(record['output_root']) != records):
        raise ValueError('Lifecycle record changed or belongs to another project')
    home = _path(records / 'runs' / record['run_id'], records / 'runs')
    return record, project, home


def _task(record, stage, identity):
    if stage not in STAGES:
        raise ValueError('Unknown lifecycle context stage')
    if stage == 'preflight':
        if identity is not None:
            raise ValueError('Preflight has no task assignment')
        return None
    matches = [t for w in record.get('waves', []) for t in w['tasks'] if t['id'] == identity]
    if len(matches) != 1:
        raise ValueError('Task identity is unknown or ambiguous')
    return matches[0]


def _binding(record, task):
    candidate = record['candidate']
    return dict(run_id=record['run_id'], scope=record['scope'],
        candidate={k: candidate.get(k) for k in ('root', 'worktree', 'git_dir', 'head')},
        snapshot=candidate['snapshot']['digest'], required_gates=record.get('required_gates', []),
        authorizations=record['authorizations'], grants=record.get('grants', []), adr=record.get('adr'),
        task={k: v for k, v in task.items() if k not in ('status', 'commit', 'delivery', 'context_packets')}
             if task is not None else None)


def _read_receipt(path, home):
    path = _path(path, home / 'context')
    value = json.loads(path.read_bytes())
    if value.get('schema') != SCHEMA or value.get('digest') != _digest({k: v for k, v in value.items() if k != 'digest'}):
        raise ValueError('Invalid lifecycle receipt')
    return value


def _merge(rows, additions):
    result = copy.deepcopy(rows)
    known = {r['id']: r for r in result}
    for row in additions:
        if row['id'] in known and known[row['id']] != row:
            raise ValueError('Requirement or gate identity changed')
        if row['id'] not in known:
            result.append(copy.deepcopy(row))
            known[row['id']] = row
    return result


def _request(record, config, supplied, stage, task, prior):
    project = _path(config['project'])
    source = _path(config.get('source_root', project))
    if not (source.is_relative_to(project) or project.is_relative_to(source)):
        raise ValueError('Source coordinates are unrelated to the project')
    scope = record['scope']
    allowed = [_relative(p) for p in scope['paths']]
    excluded = [_relative(p) for p in scope.get('excluded', [])]
    writes = [_relative(p) for p in task['write_set']] if task is not None else []
    for path in writes:
        absolute = _path(project / path, project)
        if (not _inside(path, allowed) or _inside(path, excluded) or '.git' in PurePosixPath(path).parts
                or absolute.is_relative_to(Path(record['output_root'])) or absolute.is_dir()):
            raise ValueError('Task write set exceeds its recorded scope')
    # The protocol already applied exclusions and output-root filtering. Exact
    # files preserve holes that a prefix-only provider boundary cannot express.
    reads = set(record['candidate']['snapshot']['files']) | set(writes)
    if not reads:
        raise ValueError('The recorded scope has no representable source paths')
    def coordinate(path):
        absolute = _path(project / _relative(path), project)
        if not absolute.is_relative_to(source):
            raise ValueError('Recorded scope is outside the source coordinate root')
        return absolute.relative_to(source).as_posix()
    request = copy.deepcopy(supplied)
    candidate = {'manifest': str(_path(config['manifest'], project))}
    base = {'manifest': prior['request']['candidate']['manifest']} if prior is not None else None
    if config.get('base_manifest') is not None and prior is None:
        base = {'manifest': str(_path(config['base_manifest'], project))}
    if request.get('candidate') not in (None, candidate) or request.get('base') not in (None, base):
        raise ValueError('Request names an independently unbound map revision')
    request.update(task_id=task['id'] if task else record['run_id'] + ':preflight',
        candidate=candidate, base=base, read_boundary=sorted(coordinate(p) for p in reads),
        write_boundary=sorted(coordinate(p) for p in writes))
    request['mandatory_requirements'] = _merge(request['mandatory_requirements'], task.get('requirements', []) if task else [])
    gates = [{'id': 'record:' + name} for name in record.get('required_gates', [])]
    if task:
        gates.append({'id': 'task:' + task['id'] + ':verification', 'verification': task['verification']})
    request['required_gates'] = _merge(request['required_gates'], gates)
    authority = dict(root=str(project), source_root=str(source),
                     read_boundary=request['read_boundary'], write_boundary=request['write_boundary'])
    return request, authority, writes


def _stamp(path, project):
    path = _path(path, project)
    sidecars = {}
    for suffix in ('-wal', '-journal'):
        other = _path(str(path) + suffix, project)
        if other.exists():
            sidecars[suffix] = hashlib.sha256(other.read_bytes()).hexdigest()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None,
                sidecars=sidecars)


def _artifact(path, digest, root):
    path = _path(path, root)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError('Lifecycle artifact changed')
    return json.loads(path.read_bytes())


def _provider_artifacts(result, request, project):
    root = _path(request['candidate']['manifest'], project).parent
    packet = _artifact(result['path'], result['sha256'], root)
    slice_ = _artifact(result['map_slice_path'], result['map_slice_sha256'], root)
    checkpoint = _artifact(result['cursor_path'], result['cursor_sha256'], root)
    if (packet.get('schema') != 'daodan/context-packet/v1' or packet['task_id'] != request['task_id']
            or slice_.get('schema') != 'daodan/map-slice/v1' or slice_['input_digest'] != _digest(request)
            or slice_['scope_input_digest'] != packet['input_digest'] or slice_['plan_digest'] != packet['plan_digest']
            or slice_['snapshot']['digest'] != packet['candidate']['logical_digest']
            or slice_['snapshot']['freshness'] != 'fresh' or checkpoint.get('schema') != 'daodan/context-checkpoint/v1'):
        raise ValueError('Provider artifacts belong to different requests or revisions')
    return packet, slice_


def _prior(previous, home, binding, stage, task_id):
    if previous is None:
        if stage == 'post-task':
            raise ValueError('Post-task requires the previous task receipt')
        return None
    prior = _read_receipt(previous, home)
    if (stage == 'preflight' or prior['run_binding']['run_id'] != binding['run_id']
            or prior['run_binding']['scope'] != binding['scope']
            or (prior['stage'] != 'preflight' and prior['task_id'] != task_id)
            or (stage == 'post-task' and prior['stage'] == 'preflight')):
        raise ValueError('Previous receipt belongs to another lifecycle context')
    return prior


def prepare_cycle(stage, config, supplied, recipient, *, task_id=None, previous=None):
    """Prepare one recoverable packet without updating the operational ledger."""
    record, project, home = _record(config)
    task = _task(record, stage, task_id)
    binding = _binding(record, task)
    prior = _prior(previous, home, binding, stage, task_id)
    request, authority, writes = _request(record, config, supplied, stage, task, prior)
    intent = dict(stage=stage, config=config, request=request, authority=authority,
                  recipient=recipient, run_binding=binding, previous=str(previous) if previous else None)
    directory = _path(home / 'context' / (stage + '-' + _digest(intent)), home)
    directory.mkdir(parents=True, exist_ok=True)
    _path(directory, home)
    _publish(directory / 'intent.json', intent)
    receipt_path = directory / 'receipt.json'
    if receipt_path.exists():
        verify_cycle(config, receipt_path)
        existing = _read_receipt(receipt_path, home)
        return dict(path=str(receipt_path), sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(), status=existing['status'])
    result_path = directory / 'provider-result.json'
    if result_path.exists():
        result = json.loads(result_path.read_bytes())
    else:
        for name, value in [('request', request), ('authority', authority), ('recipient', recipient), ('indexes', config.get('indexes', {}))]:
            _publish(directory / (name + '.json'), value)
        output = Path(request['candidate']['manifest']).parent / 'context' / directory.name
        result = _invoke(config, 'provider', ['context', request['candidate']['manifest'],
            '--request', str(directory / 'request.json'), '--authority', str(directory / 'authority.json'),
            '--recipient', str(directory / 'recipient.json'), '--indexes', str(directory / 'indexes.json'), '--out', str(output)])
        _publish(result_path, result)
    packet, slice_ = _provider_artifacts(result, request, project)
    current, _, _ = _record(config)
    if _binding(current, _task(current, stage, task_id)) != binding:
        raise ValueError('Lifecycle execution inputs changed during preparation')
    stamps = dict(packet['indices'])
    stamps['candidate'] = {k: packet['candidate'][k] for k in ('path', 'sha256', 'sidecars')}
    if request['base']:
        stamps['base'] = _stamp(request['base']['manifest'], project)
    for stamp in stamps.values():
        if stamp != _stamp(stamp['path'], project):
            raise ValueError('Provider inputs changed during preparation')
    obligations = [*packet['obligations'], *(prior['residual_obligations'] if prior else [])]
    residual = {_digest(dict(row, status='open')): dict(row, status='open') for row in obligations}
    receipt = dict(schema=SCHEMA, stage=stage, task_id=request['task_id'], origin_revision=record['revision'],
        run_binding=binding, config_digest=_digest(config), request=request, recipient=recipient, write_set=writes,
        previous=str(previous) if previous else None, provider=result, input_stamps=stamps,
        packet={'path': result['path'], 'sha256': result['sha256']},
        map_slice={'path': result['map_slice_path'], 'sha256': result['map_slice_sha256']},
        residual_obligations=[residual[k] for k in sorted(residual)],
        status=packet['status'], task_complete=False, validation_complete=False, write_authorized=False)
    receipt['digest'] = _digest(receipt)
    _publish(receipt_path, receipt)
    return dict(path=str(receipt_path), sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(), status=receipt['status'])


def verify_cycle(config, receipt_path, *, token_counter=None, tokenizer_id=None):
    """Reverify immediately before dispatch; bookkeeping alone is not a revision."""
    record, project, home = _record(config)
    receipt = _read_receipt(receipt_path, home)
    task_id = None if receipt['stage'] == 'preflight' else receipt['task_id']
    task = _task(record, receipt['stage'], task_id)
    binding = _binding(record, task)
    if receipt['run_binding'] != binding or receipt['config_digest'] != _digest(config):
        raise ValueError('Lifecycle packet is stale for this task or candidate')
    prior = _prior(receipt['previous'], home, binding, receipt['stage'], task_id)
    request, _, writes = _request(record, config, receipt['request'], receipt['stage'], task, prior)
    if request != receipt['request'] or writes != receipt['write_set']:
        raise ValueError('Lifecycle request exceeds its current authority')
    packet, slice_ = _provider_artifacts(receipt['provider'], request, project)
    for stamp in receipt['input_stamps'].values():
        if stamp != _stamp(stamp['path'], project):
            raise ValueError('Lifecycle provider inputs are stale')
    ready = packet['status'] == 'ready' and slice_['status'] == 'ok'
    cost = None
    if token_counter is not None:
        if not callable(token_counter) or not tokenizer_id or tokenizer_id != receipt['recipient'].get('tokenizer_id'):
            raise ValueError('Recipient token counter identity does not match')
        if packet['input'] is not None:
            cost = token_counter(packet['input'])
            if type(cost) is not int or cost < 0:
                raise ValueError('Recipient counter returned an invalid cost')
    available = min(receipt['recipient']['available_tokens'] - receipt['recipient']['reserve_tokens'],
                    request['budget']['max_input_tokens'])
    current, _, _ = _record(config)
    if _binding(current, _task(current, receipt['stage'], task_id)) != binding:
        raise ValueError('Lifecycle execution inputs changed during recipient verification')
    allowed = ready and cost is not None and cost <= available
    status = ('ready' if allowed else 'needs_recipient_check' if cost is None else 'needs_split') if ready else receipt['status']
    return dict(status=status,
        preparation_ready=ready, dispatch_allowed=allowed,
        input_tokens=cost, recipient_check_required=cost is None, residual_obligations=receipt['residual_obligations'],
        task_complete=False, validation_complete=False, write_authorized=False)


REQUIRED_OPTIONS = {'preflight': ('request', 'recipient'),
                    'task-packet': ('task-id', 'request', 'recipient'),
                    'post-task': ('task-id', 'request', 'recipient', 'previous'),
                    'verify': ('receipt',)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=(*STAGES, 'verify'))
    parser.add_argument('--config', required=True)
    parser.add_argument('--request')
    parser.add_argument('--recipient')
    parser.add_argument('--task-id')
    parser.add_argument('--previous')
    parser.add_argument('--receipt')
    args = parser.parse_args()
    missing = [name for name in REQUIRED_OPTIONS[args.operation]
               if getattr(args, name.replace('-', '_')) is None]
    if missing:
        parser.error('missing required arguments: ' + ', '.join('--' + name for name in missing))

    def load(option):
        try:
            return json.loads(Path(getattr(args, option.replace('-', '_'))).read_bytes())
        except (OSError, ValueError, UnicodeError) as error:
            parser.exit(2, 'cannot read --' + option + ': ' + str(error) + '\n')

    config = load('config')
    try:
        if args.operation == 'verify':
            result = verify_cycle(config, args.receipt)
        else:
            result = prepare_cycle(args.operation, config, load('request'), load('recipient'),
                                   task_id=args.task_id, previous=args.previous)
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
