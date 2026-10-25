"""Revision-bound lifecycle receipts over the public protocol and map CLIs.

This adapter prepares evidence. The coordinator owns refresh, dispatch, run
updates, authorizations and completion. No cross-plugin imports or LLM calls.

Documents (JSON objects):
  config     project, run_id, manifest (text); protocol, provider
             (argument arrays). Optional: source_root, base_manifest (text),
             indexes (name to path). base_manifest binds an existing map revision
             for the first stage and is refused when it conflicts with the
             previous receipt.
  request    schema, intent, query, policy_version (text); anchors, diff,
             proposed_edits (record lists); mandatory_requirements,
             required_gates (record lists with unique text `id`); budget with the
             caps max_candidates, max_edges, max_rounds, max_seconds,
             max_input_tokens, max_output_tokens (contract:
             codebase-map/contracts/context.toml, daodan/context-request/v1).
             The adapter sets task_id, candidate, base and both boundaries. The
             provider may run for max_seconds, at least 120 s, before it is
             refused with status 1; a rerun repeats the call in the same attempt.
  recipient  id (text); available_tokens, reserve_tokens, max_chars,
             max_evaluations (integers). Optional: prefix, suffix, tokenizer_id, policy
             (ordered or marginal).

Each stage's candidate manifest is a new file; the previous candidate stays
unchanged as the next stage's base. A map refreshed in place is refused.
The CLI cannot count recipient tokens, so `verify` reports needs_recipient_check;
the dispatcher calls `verify_cycle(config, receipt, token_counter=..., tokenizer_id=...)`.
A missing, unreadable or malformed input document exits with status 2; a
refused lifecycle operation exits with status 1.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

SCHEMA = 'daodan/cycle-context/v1'
STAGES = ('preflight', 'task-packet', 'post-task')
ATTEMPTS = 8
CONFIG = ({'project': 'text', 'run_id': 'text', 'manifest': 'text',
           'protocol': 'strs', 'provider': 'strs'},
          {'source_root': 'text', 'base_manifest': 'text', 'indexes': 'paths'})
REQUEST = ({'schema': 'text', 'intent': 'text', 'query': 'string', 'policy_version': 'text',
            'anchors': 'records', 'diff': 'records', 'proposed_edits': 'records',
            'mandatory_requirements': 'identified', 'required_gates': 'identified', 'budget': 'object'}, {})
RECIPIENT = ({'id': 'text', 'available_tokens': 'count', 'reserve_tokens': 'count', 'max_chars': 'count',
              'max_evaluations': 'count'}, {'prefix': 'string', 'suffix': 'string', 'tokenizer_id': 'text', 'policy': 'text'})
OBJECT = ({}, {})
RECORD_KEYS = ('run_id', 'revision', 'status', 'candidate', 'output_root', 'scope', 'authorizations')
PROVIDER_KEYS = ('path', 'sha256', 'map_slice_path', 'map_slice_sha256', 'cursor_path', 'cursor_sha256')


class Collision(ValueError):
    """Different bytes already hold this evidence name: another preparation won it."""


class StaleInputs(ValueError):
    """Provider inputs moved after evidence was prepared; the same intent can be prepared again."""


def _is(kind, value):
    if kind == 'text':
        return isinstance(value, str) and bool(value)
    if kind == 'string':
        return isinstance(value, str)
    if kind == 'count':
        return type(value) is int and value >= 0
    if kind == 'strs':
        return isinstance(value, list) and bool(value) and all(isinstance(v, str) and v for v in value)
    if kind == 'object':
        return isinstance(value, dict)
    if kind == 'records':
        return isinstance(value, list) and all(isinstance(v, dict) for v in value)
    if kind == 'identified':
        if not _is('records', value):
            return False
        names = [v.get('id') for v in value]
        return all(isinstance(n, str) and n for n in names) and len(set(names)) == len(names)
    if kind == 'paths':
        return isinstance(value, dict) and all(isinstance(k, str) and isinstance(v, str) and v for k, v in value.items())
    return False


def _strict(token):
    raise ValueError('not JSON: ' + token)


def _document(name, value, contract):
    """Name the first field of a JSON document that does not hold what the contract says."""
    required, optional = contract
    if not isinstance(value, dict):
        raise ValueError(name + ' must be a JSON object')
    for key, kind in {**required, **optional}.items():
        if key in value or key in required:
            if key not in value or not _is(kind, value[key]):
                raise ValueError(f'{name} needs {key} as {kind}')
    return value


def _delivery(value, owner, keys):
    if not isinstance(value, dict) or any(key not in value for key in keys):
        raise ValueError(owner + ' returned an incomplete delivery')
    return value


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
            raise Collision('Lifecycle evidence collision')
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
                raise Collision('Lifecycle evidence collision')
    finally:
        temporary.unlink()


def _invoke(config, owner, args, timeout=120):
    command = config[owner]
    if not isinstance(command, list) or not command or any(not isinstance(v, str) or not v for v in command):
        raise ValueError('Provider commands must be explicit argument arrays')
    result = subprocess.run([*command, *args], cwd=config['project'], stdin=subprocess.DEVNULL,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise ValueError(owner + ' rejected the operation: ' + result.stderr.decode('utf8', 'replace')[-2000:])
    try:
        return json.loads(result.stdout)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(owner + ' returned an invalid JSON delivery') from error


def _record(config):
    project = _path(config['project'])
    common = ['--project', str(project), '--run-id', config['run_id']]
    record = _delivery(_invoke(config, 'protocol', ['show', *common]), 'protocol', RECORD_KEYS)
    candidate = record['candidate']
    if (not isinstance(candidate, dict) or not isinstance(candidate.get('root'), str)
            or not isinstance(candidate.get('snapshot'), dict) or not isinstance(candidate['snapshot'].get('files'), dict)
            or not isinstance(candidate['snapshot'].get('digest'), str) or not isinstance(record['output_root'], str)
            or not isinstance(record['scope'], dict) or not isinstance(record['scope'].get('paths'), list)):
        raise ValueError('protocol returned an incomplete delivery')
    check = _delivery(_invoke(config, 'protocol', ['validate', *common, '--current']), 'protocol', ('valid', 'revision'))
    if (not check.get('valid') or check.get('revision') != record['revision']
            or record['run_id'] != config['run_id'] or record['status'] != 'in_progress'
            or _path(record['candidate']['root']) != project):
        raise ValueError('Lifecycle record changed or belongs to another project')
    records = _path(record['output_root'])
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
    if config.get('base_manifest') is not None:
        declared = str(_path(config['base_manifest'], project))
        if base is not None and base['manifest'] != declared:
            raise ValueError('base_manifest conflicts with the previous lifecycle receipt')
        base = base or {'manifest': declared}
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


def _claim(path, value):
    """First writer wins: a concurrent preparation adopts the value already stored."""
    try:
        _publish(path, value)
    except Collision:
        stored = json.loads(_path(path).read_bytes())
        if not isinstance(stored, dict):
            raise
        return stored
    return value


def _attempt(stage, config, request, authority, recipient, binding, prior, previous, writes, task_id, record, project, home, name):
    """One journaled preparation. A receipt or provider result whose inputs moved ends the attempt."""
    directory = _path(home / 'context' / name, home)
    directory.mkdir(parents=True, exist_ok=True)
    _path(directory, home)
    intent = dict(stage=stage, config=config, request=request, authority=authority,
                  recipient=recipient, run_binding=binding, previous=str(previous) if previous else None)
    _publish(directory / 'intent.json', intent)
    receipt_path = directory / 'receipt.json'
    if receipt_path.exists():
        try:
            verify_cycle(config, receipt_path)
        except StaleInputs:
            return None
        existing = _read_receipt(receipt_path, home)
        return dict(path=str(receipt_path), sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(), status=existing['status'])
    base = None
    if request['base']:
        # The stamp is taken before the provider reads the manifest, so a base rewritten
        # while the packet is built cannot be stamped as the revision the packet used.
        base = _stamp(request['base']['manifest'], project)
        if prior is not None and base != prior['input_stamps']['candidate']:
            raise ValueError('Base map revision changed since the previous receipt; refresh the map into a new manifest')
        stored = _claim(directory / 'base-stamp.json', base)
        if stored != base:
            return None
    result_path = directory / 'provider-result.json'
    if result_path.exists():
        result = json.loads(_path(result_path).read_bytes())
    else:
        for label, value in [('request', request), ('authority', authority), ('recipient', recipient), ('indexes', config.get('indexes', {}))]:
            _publish(directory / (label + '.json'), value)
        output = Path(request['candidate']['manifest']).parent / 'context' / directory.name
        result = _delivery(_invoke(config, 'provider', ['context', request['candidate']['manifest'],
            '--request', str(directory / 'request.json'), '--authority', str(directory / 'authority.json'),
            '--recipient', str(directory / 'recipient.json'), '--indexes', str(directory / 'indexes.json'), '--out', str(output)],
            timeout=max(120, request['budget']['max_seconds'])), 'provider', PROVIDER_KEYS)
        result = _claim(result_path, result)
    _delivery(result, 'provider', PROVIDER_KEYS)
    packet, slice_ = _provider_artifacts(result, request, project)
    current, _, _ = _record(config)
    if _binding(current, _task(current, stage, task_id)) != binding:
        raise ValueError('Lifecycle execution inputs changed during preparation')
    stamps = dict(packet['indices'])
    stamps['candidate'] = {k: packet['candidate'][k] for k in ('path', 'sha256', 'sidecars')}
    if base is not None:
        stamps['base'] = base
    for stamp in stamps.values():
        if stamp != _stamp(stamp['path'], project):
            return None
    obligations = [*packet['obligations'], *(prior['residual_obligations'] if prior else [])]
    residual = {_digest(dict(row, status='open')): dict(row, status='open') for row in obligations}
    receipt = dict(schema=SCHEMA, stage=stage, task_id=request['task_id'],
        run_binding=binding, config_digest=_digest(config), request=request, recipient=recipient, write_set=writes,
        previous=str(previous) if previous else None, provider=result, input_stamps=stamps,
        packet={'path': result['path'], 'sha256': result['sha256']},
        map_slice={'path': result['map_slice_path'], 'sha256': result['map_slice_sha256']},
        residual_obligations=[residual[k] for k in sorted(residual)],
        status=packet['status'], task_complete=False, validation_complete=False, write_authorized=False)
    receipt['digest'] = _digest(receipt)
    _publish(receipt_path, receipt)
    return dict(path=str(receipt_path), sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(), status=receipt['status'])


def prepare_cycle(stage, config, supplied, recipient, *, task_id=None, previous=None):
    """Prepare one recoverable packet without updating the operational ledger.

    The intent names a journal. When the inputs a receipt was built from move, that
    attempt stays as evidence and the same intent is prepared again in the next one.
    """
    record, project, home = _record(config)
    task = _task(record, stage, task_id)
    binding = _binding(record, task)
    prior = _prior(previous, home, binding, stage, task_id)
    request, authority, writes = _request(record, config, supplied, stage, task, prior)
    intent = dict(stage=stage, config=config, request=request, authority=authority,
                  recipient=recipient, run_binding=binding, previous=str(previous) if previous else None)
    prefix = stage + '-' + _digest(intent)
    generations = [int(m.group(1)) for item in (home / 'context').glob(prefix + '-a*')
                   if (m := re.fullmatch(re.escape(prefix) + r'-a(\d+)', item.name))]
    first = max([1, *generations])
    for number in range(first, first + ATTEMPTS):
        done = _attempt(stage, config, request, authority, recipient, binding, prior, previous, writes, task_id,
                        record, project, home, prefix if number == 1 else f'{prefix}-a{number}')
        if done is not None:
            return done
    raise ValueError('Lifecycle context inputs kept changing during preparation')


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
            raise StaleInputs('Lifecycle provider inputs are stale')
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
    if ready:
        status = 'ready' if allowed else 'needs_recipient_check' if cost is None else 'needs_split'
    else:
        status = receipt['status'] if receipt['status'] != 'ready' else 'incomplete'
    return dict(status=status,
        preparation_ready=ready, dispatch_allowed=allowed,
        input_tokens=cost, recipient_check_required=cost is None, residual_obligations=receipt['residual_obligations'],
        task_complete=False, validation_complete=False, write_authorized=False)


REQUIRED_OPTIONS = {'preflight': ('request', 'recipient'),
                    'task-packet': ('task-id', 'request', 'recipient'),
                    'post-task': ('task-id', 'request', 'recipient', 'previous'),
                    'verify': ('receipt',)}
REFUSED = (ValueError, OSError, subprocess.TimeoutExpired, KeyError, TypeError, AttributeError, RecursionError)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('operation', choices=(*STAGES, 'verify'))
    parser.add_argument('--config', required=True)
    parser.add_argument('--request')
    parser.add_argument('--recipient')
    parser.add_argument('--task-id')
    parser.add_argument('--previous', help='receipt of the previous stage')
    parser.add_argument('--receipt', help='receipt to verify')
    args = parser.parse_args()
    missing = [name for name in REQUIRED_OPTIONS[args.operation]
               if getattr(args, name.replace('-', '_')) is None]
    if missing:
        parser.error('missing required arguments: ' + ', '.join('--' + name for name in missing))

    def load(option, contract):
        """Read one input document; anything but a document of its kind is an invocation error."""
        try:
            value = json.loads(Path(getattr(args, option.replace('-', '_'))).read_bytes(), parse_constant=_strict)
            _document('--' + option, value, contract)
        except (OSError, ValueError, UnicodeError, RecursionError) as error:
            parser.exit(2, f'cannot use --{option}: {error}\n')
        return value

    config = load('config', CONFIG)
    try:
        if args.operation == 'verify':
            load('receipt', OBJECT)
            result = verify_cycle(config, args.receipt)
        else:
            request = load('request', REQUEST)
            recipient = load('recipient', RECIPIENT)
            if args.previous is not None:
                load('previous', OBJECT)
            result = prepare_cycle(args.operation, config, request, recipient,
                                   task_id=args.task_id, previous=args.previous)
    except REFUSED as error:
        parser.exit(1, (str(error) if isinstance(error, ValueError) else f'{type(error).__name__}: {error}') + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
