"""Metadata-only discovery and snapshot-bound knowledge inputs. Stdlib only.

All commands emit JSON to stdout and perform no writes or workflow execution.
Inventory roots must come from the host's actual available skills, not a registry.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import tomllib

CATALOG_SCHEMA = 'daodan/skill-catalog/v1'
SELECTION_SCHEMA = 'daodan/skill-selection/v1'
METADATA_SCHEMA = 'daodan/skill-metadata/v1'
KINDS = {'knowledge', 'method', 'workflow', 'unknown'}
LIST_FIELDS = ('operations', 'languages', 'frameworks', 'topics', 'dimensions')
META_FIELDS = {'schema', 'kind', *LIST_FIELDS}
ID = re.compile(r'^[a-z0-9][a-z0-9_.-]*(?::[a-z0-9][a-z0-9_.-]*)?$')
MAX_CONTENT = 2 * 1024 * 1024


class CatalogError(ValueError):
    pass


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def _strings(value, field, required=False):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() or
                                         '\n' in v or '\r' in v for v in value):
        raise CatalogError(f'{field} must be an array of nonempty single-line strings')
    if required and not value:
        raise CatalogError(f'{field} must not be empty')
    return sorted(set(v.strip().casefold() for v in value))


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f'{field} must be a nonempty string')
    return value


def _no_links(path):
    for item in (path, *path.parents):
        try:
            attributes = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(attributes.st_mode) or getattr(attributes, 'st_file_attributes', 0) & 0x400:
            raise CatalogError(f'Linked catalog content is not a bound source: {item}')


def safe_file(root, relative):
    root = Path(_text(str(root), 'root')).absolute()
    _no_links(root)
    relative = _text(relative, 'file').replace('\\', '/')
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or ':' in relative or relative.startswith('/'):
        raise CatalogError('Content path must stay inside its bound provider root')
    target = root / path
    _no_links(target)
    if not target.resolve().is_relative_to(root.resolve()):
        raise CatalogError('Content path escapes its bound provider root')
    return target


def _header(path):
    """Read only bounded frontmatter; never inspect a body during indexing."""
    try:
        with path.open('r', encoding='utf-8-sig') as handle:
            if handle.readline(2048).strip() != '---':
                return {}
            lines, length = [], 0
            for _ in range(256):
                line = handle.readline(2048)
                length += len(line)
                if line.strip() == '---':
                    break
                if not line or length > 32768:
                    raise CatalogError('Skill frontmatter is missing its bounded closing delimiter')
                lines.append(line)
            else:
                raise CatalogError('Skill frontmatter exceeds the metadata limit')
    except (OSError, UnicodeError) as error:
        raise CatalogError(f'Cannot read skill metadata: {path}') from error
    metadata, key = {}, None
    for line in lines:
        if line[:1] not in {' ', '\t'} and ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            metadata[key] = value.strip().strip('\"\'')
        elif key and line.strip():
            metadata[key] += ' ' + line.strip()
    return {key: value.lstrip('>|').strip() for key, value in metadata.items()}


def metadata_for(directory):
    directory = Path(directory)
    path = safe_file(directory, 'SKILL.toml')
    if not path.is_file():
        return dict(kind='unknown', **{field: [] for field in LIST_FIELDS},
                    metadata_sha256=None, metadata_declaration_sha256=None)
    try:
        raw = path.read_bytes()
        data = tomllib.loads(raw.decode('utf-8'))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise CatalogError(f'Invalid skill metadata: {path}') from error
    if set(data) - META_FIELDS or data.get('schema') != METADATA_SCHEMA or data.get('kind') not in KINDS:
        raise CatalogError(f'Unknown metadata fields, schema or kind: {path}')
    portable = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    result = {'kind': data['kind'], 'metadata_sha256': hashlib.sha256(raw).hexdigest(),
              'metadata_declaration_sha256': hashlib.sha256(portable).hexdigest()}
    for field in LIST_FIELDS:
        result[field] = _strings(data.get(field, []), field,
                                 required=field == 'operations' and data['kind'] == 'knowledge')
    return result


def index_inventory(declared, inventory):
    """Intersect generated declarations with resolved host/project inventory."""
    if not isinstance(declared, dict) or declared.get('schema') != CATALOG_SCHEMA:
        raise CatalogError('Invalid declared catalog schema')
    if not isinstance(inventory, list):
        raise CatalogError('Inventory must be an array of actual available skill bindings')
    declarations = {row['id']: row for row in declared.get('entries', [])}
    entries, gaps, seen = [], [], set()
    for binding in inventory:
        if not isinstance(binding, dict) or not ID.fullmatch(str(binding.get('id', ''))):
            raise CatalogError('Invalid exact skill ID in inventory')
        identity = binding['id']
        if identity in seen:
            raise CatalogError(f'Ambiguous duplicate skill ID: {identity}')
        seen.add(identity)
        provider = _text(binding.get('provider'), 'provider')
        version = _text(binding.get('version'), 'version')
        root = _text(binding.get('root'), 'root')
        relative = _text(binding.get('file'), 'file')
        try:
            body = safe_file(root, relative)
            if body.name != 'SKILL.md' or not body.is_file():
                raise CatalogError('Available skill does not resolve to an existing SKILL.md')
            header = _header(body)
            metadata = metadata_for(body.parent)
            declaration_digest = metadata.pop('metadata_declaration_sha256')
            declaration = declarations.get(identity)
            if declaration and declaration.get('provider') == provider and declaration.get('version') == version:
                if declaration.get('metadata_sha256') != declaration_digest:
                    raise CatalogError('Installed metadata differs from the same-version declaration')
            entries.append(dict(id=identity, provider=provider, version=version,
                                root=str(Path(root).absolute()), file=relative,
                                origin=binding.get('origin', 'host'), name=header.get('name', identity),
                                description=header.get('description', ''), **metadata))
        except CatalogError as error:
            gaps.append(dict(id=identity, reason='inventory-unresolved', detail=str(error)))
    return dict(schema=CATALOG_SCHEMA, entries=sorted(entries, key=lambda row: row['id']), gaps=gaps)


def _words(value):
    return set(re.findall(r'[\w+#]+', value.casefold()))


def _score(entry, query):
    labels = ' '.join([entry['id'], entry.get('name', ''), entry.get('description', ''),
                       *(tag for field in LIST_FIELDS for tag in entry.get(field, []))])
    return len(_words(query) & _words(labels))


def search(catalog, query, operation, limit=20, offset=0):
    _catalog(catalog)
    if not isinstance(limit, int) or limit < 1 or limit > 200 or not isinstance(offset, int) or offset < 0:
        raise CatalogError('Search page must have limit 1..200 and nonnegative offset')
    rows = [dict(row, score=_score(row, query)) for row in catalog['entries']
            if row['kind'] == 'unknown' or operation in row['operations']]
    rows = sorted((row for row in rows if row['score']), key=lambda row: (-row['score'], row['id']))
    return rows[offset:offset + limit]


def _catalog(catalog):
    if not isinstance(catalog, dict) or catalog.get('schema') != CATALOG_SCHEMA or not isinstance(catalog.get('entries'), list):
        raise CatalogError('Invalid available catalog')


def _request(request):
    if not isinstance(request, dict):
        raise CatalogError('Selection request must be an object')
    for key in ('run_id', 'project_id', 'snapshot_id', 'operation'):
        _text(request.get(key), key)
    scopes = request.get('scopes')
    if not isinstance(scopes, list) or not scopes:
        raise CatalogError('At least one candidate scope is required')
    seen = set()
    for scope in scopes:
        identity = _text(scope.get('id'), 'scope.id')
        if identity in seen:
            raise CatalogError('Duplicate scope identity')
        seen.add(identity)
        _strings(scope.get('paths', []), 'scope.paths', required=True)
        _strings(scope.get('evidence', []), 'scope.evidence', required=True)
        for field in ('languages', 'frameworks', 'topics'):
            _strings(scope.get(field, []), f'scope.{field}')
        workers = scope.get('workers', {})
        if not isinstance(workers, dict):
            raise CatalogError('Scope workers must map knowledge dimensions to selected delivery IDs')
        for dimension, assigned in workers.items():
            _text(dimension, 'worker.dimension')
            _strings(assigned, 'worker.assignments', required=True)


def _matches(entry, scope):
    constrained = False
    for field in ('languages', 'frameworks', 'topics'):
        expected = set(entry.get(field, []))
        if expected:
            constrained = True
            if not expected & set(_strings(scope.get(field, []), field)):
                return False
    return constrained


def select(catalog, request):
    _catalog(catalog)
    _request(request)
    selected, gaps = {}, copy.deepcopy(catalog.get('gaps', []))
    if not catalog['entries']:
        gaps.append(dict(reason='empty-inventory'))
    for scope in request['scopes']:
        query = ' '.join(tag for field in ('languages', 'frameworks', 'topics') for tag in scope.get(field, []))
        matched = False
        for entry in catalog['entries']:
            if entry['kind'] == 'unknown':
                if _score(entry, query):
                    gaps.append(dict(id=entry['id'], scope_id=scope['id'], reason='unclassified-knowledge'))
                continue
            if entry['kind'] != 'knowledge' or request['operation'] not in entry['operations'] or not _matches(entry, scope):
                continue
            matched = True
            if entry['id'] not in selected:
                selected[entry['id']] = dict(copy.deepcopy(entry), bindings=[], status='selected')
            dimensions = entry.get('dimensions') or ['correctness']
            dimension_workers = {dimension: sorted(set(scope.get('workers', {}).get(dimension, [])))
                                 for dimension in dimensions}
            workers = sorted({worker for assigned in dimension_workers.values() for worker in assigned})
            selected[entry['id']]['bindings'].append(dict(scope_id=scope['id'], paths=scope['paths'],
                                                        dimensions=dimensions, workers=workers,
                                                        dimension_workers=dimension_workers,
                                                        activation_evidence=scope['evidence']))
        if not matched:
            gaps.append(dict(scope_id=scope['id'], reason='no-applicable-knowledge'))
    return dict(schema=SELECTION_SCHEMA, **{k: request[k] for k in ('run_id', 'project_id', 'snapshot_id', 'operation')},
                catalog_sha256=fingerprint(catalog), selected=[selected[k] for k in sorted(selected)],
                gaps=gaps, status='selected')


def _read_content(root, relative):
    path = safe_file(root, relative)
    try:
        if path.stat().st_size > MAX_CONTENT:
            raise CatalogError('Knowledge content exceeds the 2 MiB read limit')
        raw = path.read_bytes()
        if len(raw) > MAX_CONTENT:
            raise CatalogError('Knowledge content exceeds the 2 MiB read limit')
        content = raw.decode('utf-8-sig')
    except (OSError, UnicodeError) as error:
        raise CatalogError(f'Cannot load selected content: {relative}') from error
    return content, hashlib.sha256(raw).hexdigest()


def _metadata_current(entry):
    path = safe_file(entry['root'], entry['file'])
    if metadata_for(path.parent)['metadata_sha256'] != entry['metadata_sha256']:
        raise CatalogError('Selected metadata changed; prepare again against the same candidate')


def prepare(catalog, request):
    result = select(catalog, request)
    failed = False
    for entry in result['selected']:
        try:
            missing = [(binding['scope_id'], dimension) for binding in entry['bindings']
                       for dimension, workers in binding['dimension_workers'].items() if not workers]
            if missing:
                raise CatalogError(f'Selected knowledge has unassigned scoped dimensions: {missing}')
            _metadata_current(entry)
            _, digest = _read_content(entry['root'], entry['file'])
            entry.update(sha256=digest, status='prepared')
        except CatalogError as error:
            failed = True
            entry.update(status='failed', failure=str(error))
    result['status'] = 'failed' if failed else 'prepared'
    result['selection_sha256'] = fingerprint(result)
    return result


def _digest(value, field):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
        raise CatalogError(f'{field} must be a SHA-256 fingerprint')


def _selection(selection):
    """Validate the whole prepared record, including empty or failed selections."""
    if not isinstance(selection, dict) or selection.get('schema') != SELECTION_SCHEMA:
        raise CatalogError('Invalid selection schema')
    for key in ('run_id', 'project_id', 'snapshot_id', 'operation'):
        _text(selection.get(key), key)
    _digest(selection.get('catalog_sha256'), 'catalog_sha256')
    if selection.get('status') not in {'prepared', 'failed'}:
        raise CatalogError('Selection must be prepared or failed')
    selected, gaps = selection.get('selected'), selection.get('gaps')
    if not isinstance(selected, list) or not isinstance(gaps, list) or any(not isinstance(gap, dict) for gap in gaps):
        raise CatalogError('Selection entries and coverage gaps must be arrays of records')
    if not selected and not gaps:
        raise CatalogError('An empty knowledge selection must declare its coverage gaps')
    payload = {key: value for key, value in selection.items() if key != 'selection_sha256'}
    if fingerprint(payload) != selection.get('selection_sha256'):
        raise CatalogError('Selection record changed after preparation')
    seen = set()
    for entry in selected:
        if not isinstance(entry, dict) or not isinstance(entry.get('id'), str) or not ID.fullmatch(entry['id']):
            raise CatalogError('Invalid selected knowledge ID')
        if entry['id'] in seen:
            raise CatalogError('Duplicate selected knowledge ID')
        seen.add(entry['id'])
        for key in ('provider', 'version', 'root', 'file'):
            _text(entry.get(key), f'knowledge.{key}')
        if entry.get('kind') != 'knowledge' or entry.get('status') not in {'prepared', 'failed'}:
            raise CatalogError('Selection entries must be prepared or failed knowledge')
        if selection['status'] == 'prepared' and entry['status'] != 'prepared':
            raise CatalogError('Prepared selection contains a failed knowledge input')
        _digest(entry.get('metadata_sha256'), 'metadata_sha256')
        if entry['status'] == 'prepared':
            _digest(entry.get('sha256'), 'sha256')
        bindings = entry.get('bindings')
        if not isinstance(bindings, list) or not bindings:
            raise CatalogError('Selected knowledge must have scoped assignments')
        scopes = set()
        for binding in bindings:
            if not isinstance(binding, dict):
                raise CatalogError('Knowledge assignment must be a record')
            scope_id = _text(binding.get('scope_id'), 'scope_id')
            if scope_id in scopes:
                raise CatalogError('Duplicate knowledge scope assignment')
            scopes.add(scope_id)
            for key in ('paths', 'activation_evidence', 'dimensions'):
                _strings(binding.get(key), f'assignment.{key}', required=True)
            _strings(binding.get('workers'), 'assignment.workers')
            mapping = binding.get('dimension_workers')
            if not isinstance(mapping, dict) or set(mapping) != set(binding['dimensions']):
                raise CatalogError('Every selected dimension must have its own worker assignment')
            for workers in mapping.values():
                _strings(workers, 'assignment.dimension_workers', required=entry['status'] == 'prepared')
            if set(binding['workers']) != {worker for workers in mapping.values() for worker in workers}:
                raise CatalogError('Scoped delivery IDs disagree with dimension assignments')


def _selected(selection, identity):
    _selection(selection)
    matches = [row for row in selection['selected'] if row['id'] == identity]
    if len(matches) != 1 or matches[0]['status'] != 'prepared' or matches[0]['kind'] != 'knowledge':
        raise CatalogError('Skill is not one prepared knowledge input')
    return matches[0]


def load_skill(selection, identity):
    entry = _selected(selection, identity)
    _metadata_current(entry)
    content, digest = _read_content(entry['root'], entry['file'])
    if digest != entry['sha256']:
        raise CatalogError('Selected content changed; review input is stale')
    return dict(id=identity, provider=entry['provider'], version=entry['version'], status='loaded',
                sha256=digest, content=content, bindings=entry['bindings'],
                selection_sha256=selection['selection_sha256'])


def read_reference(selection, identity, relative):
    entry = _selected(selection, identity)
    load_skill(selection, identity)
    relative = _text(relative, 'reference').replace('\\', '/')
    if not relative.startswith('references/'):
        raise CatalogError('Supplementary knowledge must be inside references/')
    skill_root = safe_file(entry['root'], entry['file']).parent
    content, digest = _read_content(skill_root, relative)
    return dict(id=identity, file=relative, sha256=digest, content=content, status='loaded')


def validate_usage(selection, usages):
    _selection(selection)
    if not isinstance(usages, list):
        raise CatalogError('Knowledge usage must be an array')
    failures = copy.deepcopy(selection.get('gaps', []))
    for entry in selection.get('selected', []):
        try:
            loaded = load_skill(selection, entry['id'])
            for binding in entry['bindings']:
                for worker in binding['workers']:
                    delivered = [u for u in usages if isinstance(u, dict) and u.get('id') == entry['id'] and
                                 u.get('scope_id') == binding['scope_id'] and u.get('worker') == worker and
                                 u.get('status') == 'loaded' and u.get('sha256') == loaded['sha256'] and
                                 u.get('selection_sha256') == selection['selection_sha256'] and
                                 isinstance(u.get('application'), str) and u['application'].strip() and
                                 isinstance(u.get('references'), list)]
                    if not delivered:
                        failures.append(dict(id=entry['id'], scope_id=binding['scope_id'], worker=worker,
                                             reason='knowledge-undelivered'))
                    for usage in delivered:
                        for reference in usage['references']:
                            if not isinstance(reference, dict):
                                raise CatalogError('Reference usage must identify its relative file and hash')
                            current = read_reference(selection, entry['id'], reference.get('file'))
                            if current['sha256'] != reference.get('sha256'):
                                raise CatalogError('Used reference changed; knowledge delivery is stale')
        except CatalogError as error:
            failures.append(dict(id=entry['id'], reason='knowledge-load-failed', detail=str(error)))
    return dict(complete=not failures and selection.get('status') == 'prepared', failures=failures)


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CatalogError(f'Cannot read catalog input: {path}') from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    index = commands.add_parser('index')
    index.add_argument('--declared', required=True)
    index.add_argument('--inventory', required=True)
    search_parser = commands.add_parser('search')
    search_parser.add_argument('--catalog', required=True)
    search_parser.add_argument('--query', required=True)
    search_parser.add_argument('--operation', default='review')
    search_parser.add_argument('--limit', type=int, default=20)
    search_parser.add_argument('--offset', type=int, default=0)
    for name in ('select', 'prepare'):
        command = commands.add_parser(name)
        command.add_argument('--catalog', required=True)
        command.add_argument('--request', required=True)
    for name in ('load', 'reference', 'validate-usage'):
        command = commands.add_parser(name)
        command.add_argument('--selection', required=True)
        if name == 'validate-usage':
            command.add_argument('--usage', required=True)
        else:
            command.add_argument('--id', required=True)
        if name == 'reference':
            command.add_argument('--path', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'index':
            result = index_inventory(read_json(args.declared), read_json(args.inventory))
        elif args.command == 'search':
            result = search(read_json(args.catalog), args.query, args.operation, args.limit, args.offset)
        elif args.command in {'select', 'prepare'}:
            function = prepare if args.command == 'prepare' else select
            result = function(read_json(args.catalog), read_json(args.request))
        elif args.command == 'load':
            result = load_skill(read_json(args.selection), args.id)
        elif args.command == 'reference':
            result = read_reference(read_json(args.selection), args.id, args.path)
        else:
            result = validate_usage(read_json(args.selection), read_json(args.usage))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if isinstance(result, dict) and (result.get('status') == 'failed' or result.get('complete') is False) else 0
    except CatalogError as error:
        print(json.dumps(dict(status='failed', error=str(error))))
        return 1


if __name__ == '__main__':
    sys.exit(main())
