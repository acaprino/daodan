"""Compile declarative skill metadata through the catalog owner's parser."""
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import stat
import tomllib
import types

CATALOG_SCHEMA = 'daodan/skill-catalog/v1'
METADATA_SCHEMA = 'daodan/skill-metadata/v1'
KINDS = {'knowledge', 'method', 'workflow', 'unknown'}
LIST_FIELDS = ('operations', 'languages', 'frameworks', 'topics', 'dimensions')
META_FIELDS = {'schema', 'kind', *LIST_FIELDS}


class CatalogError(ValueError):
    pass


def _strings(value, field, required=False):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() or
                                         '\n' in v or '\r' in v for v in value):
        raise CatalogError(f'{field} must be an array of nonempty single-line strings')
    if required and not value:
        raise CatalogError(f'{field} must not be empty')
    return sorted(set(v.strip().casefold() for v in value))


def _no_links(path):
    for item in (path, *path.parents):
        try:
            attributes = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(attributes.st_mode) or getattr(attributes, 'st_file_attributes', 0) & 0x400:
            raise CatalogError(f'Linked catalog content is not a bound source: {item}')


def _header(path):
    try:
        with Path(path).open('r', encoding='utf-8-sig') as handle:
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
    directory = Path(directory).absolute()
    _no_links(directory)
    path = directory / 'SKILL.toml'
    _no_links(path)
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


@lru_cache(maxsize=1)
def runtime():
    source = Path(__file__).resolve().parents[2] / 'plugins/skill-catalog/skills/skill-catalog/scripts/catalog.py'
    if source.is_file():
        spec = importlib.util.spec_from_file_location('daodan_skill_catalog_runtime', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return types.SimpleNamespace(
        CATALOG_SCHEMA=CATALOG_SCHEMA,
        CatalogError=CatalogError,
        _header=_header,
        metadata_for=metadata_for,
    )


def validate_skill_metadata(plugin):
    from .validate import ValidationIssue
    issues = []
    api = runtime()
    for skill in plugin.components.skills:
        directory = plugin.root / 'skills' / skill
        try:
            api.metadata_for(directory)
        except api.CatalogError as error:
            issues.append(ValidationIssue('invalid-skill-metadata', directory / 'SKILL.toml', str(error)))
    return issues


def declared_catalog(registry):
    api = runtime()
    entries = []
    for name, plugin in sorted(registry.items()):
        for skill in sorted(plugin.components.skills):
            directory = plugin.root / 'skills' / skill
            metadata = api.metadata_for(directory)
            metadata['metadata_sha256'] = metadata.pop('metadata_declaration_sha256')
            header = api._header(directory / 'SKILL.md')
            entries.append(dict(id=f'{name}:{skill}', provider=name, version=plugin.version,
                                file=f'skills/{skill}/SKILL.md', name=header.get('name', skill),
                                description=header.get('description', ''), **metadata))
    return dict(schema=api.CATALOG_SCHEMA, entries=entries, installation_evidence=False)
