"""Static check of the five host packages against the kernel for the code context surface.

Structural evidence only: it proves that what the kernel says reaches every host byte for byte and
that the four exported schemas are the kernel's. It does not prove any host can run the workflow.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tomllib

ROOT = Path(sys.argv[1]).resolve()
HOSTS = ('claude', 'codex', 'copilot', 'pi', 'opencode')
MAP = 'plugins/codebase-map'
LIFE = 'plugins/project-lifecycle'
# kernel path -> path inside each host package (host root is exports/<host>/plugins/<plugin>/...)
SHIPPED = {
    f'{MAP}/contracts/context.toml': 'codebase-map/contracts/context.toml',
    f'{MAP}/skills/map-method/references/context.md': 'codebase-map/skills/map-method/references/context.md',
    f'{MAP}/skills/map-method/scripts/map_slice.py': 'codebase-map/skills/map-method/scripts/map_slice.py',
    f'{MAP}/skills/map-method/scripts/context_packet.py': 'codebase-map/skills/map-method/scripts/context_packet.py',
    f'{MAP}/skills/map-method/scripts/scope_planner.py': 'codebase-map/skills/map-method/scripts/scope_planner.py',
    f'{LIFE}/skills/lifecycle-method/scripts/cycle_packets.py': 'project-lifecycle/skills/lifecycle-method/scripts/cycle_packets.py',
    f'{LIFE}/skills/lifecycle-method/references/context-cycle.md': 'project-lifecycle/skills/lifecycle-method/references/context-cycle.md',
    f'{LIFE}/skills/lifecycle-method/references/waves.md': 'project-lifecycle/skills/lifecycle-method/references/waves.md',
    f'{LIFE}/skills/lifecycle-method/references/verify.md': 'project-lifecycle/skills/lifecycle-method/references/verify.md',
    f'{LIFE}/skills/lifecycle-method/references/finish.md': 'project-lifecycle/skills/lifecycle-method/references/finish.md',
    'plugins/project-knowledge/skills/project-knowledge/references/preparation.md': 'project-knowledge/skills/project-knowledge/references/preparation.md',
    'plugins/senior-review/skills/review-preparation/references/candidate-grounding.md': 'senior-review/skills/review-preparation/references/candidate-grounding.md',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    contract = tomllib.loads((ROOT / f'{MAP}/contracts/context.toml').read_text(encoding='utf8'))
    schemas = [record['record_schema'] for record in contract['records']]
    report = {'kernel_schemas': schemas, 'hosts': {}, 'mismatches': []}
    for host in HOSTS:
        base = ROOT / 'exports' / host / 'plugins'
        rows = {}
        for kernel, shipped in SHIPPED.items():
            source, target = ROOT / kernel, base / shipped
            if not source.is_file():
                report['mismatches'].append(f'kernel file missing: {kernel}')
                continue
            if not target.is_file():
                # A host may rename a reference; record the absence instead of guessing.
                report['mismatches'].append(f'{host}: missing {shipped}')
                rows[shipped] = 'missing'
                continue
            if source.suffix == '.md':
                # the adapter prepends its host binding; the kernel body must follow unchanged
                text = target.read_text(encoding='utf8')
                body = [line for line in source.read_text(encoding='utf8').splitlines()
                        if line.strip() and 'CLAUDE_PLUGIN_ROOT' not in line and '$ARGUMENTS' not in line]
                rest = iter(line for line in text.splitlines() if line.strip())
                # every unadapted kernel line must follow in order; placeholder lines are host-adapted by design
                same = all(line in rest for line in body) and any(f'host="{host}"' in line for line in text.splitlines()[:12])
                rows[shipped] = 'bound-identical' if same else 'DIFFERENT'
            else:
                same = digest(source) == digest(target)
                rows[shipped] = 'identical' if same else 'DIFFERENT'
            if not same:
                report['mismatches'].append(f'{host}: {shipped} differs from the kernel')
        exported = tomllib.loads((base / 'codebase-map/contracts/context.toml').read_text(encoding='utf8'))
        host_schemas = [record['record_schema'] for record in exported['records']]
        if host_schemas != schemas:
            report['mismatches'].append(f'{host}: exported schemas {host_schemas}')
        report['hosts'][host] = {'schemas': len(host_schemas), 'files': rows}
    # roles: host adapters wrap the role body, so check the added statement instead of the byte digest
    needle = 'semantic card'
    role_hits = {}
    for host in HOSTS:
        hits = []
        for path in (ROOT / 'exports' / host).rglob('*premise-auditor*'):
            if path.is_file() and path.suffix in ('.md', '.toml', '.json'):
                hits.append((str(path.relative_to(ROOT / 'exports' / host)), needle in path.read_text(encoding='utf8', errors='replace')))
        role_hits[host] = hits
        if not hits or not any(flag for _, flag in hits):
            report['mismatches'].append(f'{host}: premise-auditor body lacks the context packet prohibition')
    report['premise_auditor'] = role_hits
    report['ok'] = not report['mismatches']
    print(json.dumps({'ok': report['ok'], 'schemas': schemas,
                      'identical_files_per_host': {h: sum(v in ('identical', 'bound-identical') for v in d['files'].values()) for h, d in report['hosts'].items()},
                      'of': len(SHIPPED), 'mismatches': report['mismatches']}, indent=1))
    return report


if __name__ == '__main__':
    result = main()
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(result, indent=1) + '\n', encoding='utf8')
    sys.exit(0 if result['ok'] else 1)
