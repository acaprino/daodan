"""Compile declarative skill metadata through the catalog owner's parser."""
from functools import lru_cache
import importlib.util
from pathlib import Path


@lru_cache(maxsize=1)
def runtime():
    source = Path(__file__).resolve().parents[2] / 'plugins/skill-catalog/skills/skill-catalog/scripts/catalog.py'
    spec = importlib.util.spec_from_file_location('daodan_skill_catalog_runtime', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
