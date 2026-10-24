"""Impact scenarios on a copy of the frozen project, scored against a textual call-site oracle.

A signature change, a body change, a removal and a change to a heavily used function are applied to
copies. The oracle is a plain regular-expression search of call sites in the copy, an independent
mechanism from the map. The map's callers are scored for recall and precision at (file, line)
granularity. Names that collide with builtin container methods are not eligible, because a textual
oracle cannot tell them from a call on a dict or a list. Dynamic uses that no direct call reveals
must stay declared gaps, never silent independence.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve()
SCRIPTS = Path(os.environ['CODEBASE_MAP_SCRIPTS']) if os.environ.get('CODEBASE_MAP_SCRIPTS') else next(
    p / 'plugins/codebase-map/skills/map-method/scripts' for p in HERE.parents
    if (p / 'plugins/codebase-map/skills/map-method/scripts').is_dir())
sys.path.insert(0, str(SCRIPTS))
import resolve_edges
import semantic_store
import snapshot
from snapshot_store import open_snapshot

COLLIDES = set(dir(dict) + dir(list) + dir(str) + dir(set) + dir(bytes) + dir(object)) | {
    'read', 'write', 'close', 'send', 'receive', 'run', 'call', 'open', 'main', 'wait', 'start', 'stop'}
PER_KIND = 3


def definitions(store):
    names = {}
    for path, entry in store.iter_files(semantic=False):
        for name, spec in (entry.get('symbols') or {}).items():
            if spec.get('kind') in ('function', 'method') and isinstance(spec.get('start'), int):
                names.setdefault(name.rsplit('.', 1)[-1], []).append((path, name, spec['start'], spec['end']))
    return names


def call_sites(project, bare):
    pattern = re.compile(r'(?<![\w.])(?:[\w.]+\.)?' + re.escape(bare) + r'\s*\(')
    sites = set()
    for path in sorted(Path(project).rglob('*.py')):
        rel = path.relative_to(project).as_posix()
        for number, line in enumerate(path.read_text(encoding='utf8').splitlines(), 1):
            if line.strip().startswith(('def ', 'async def ', 'class ', '#')):
                continue
            if pattern.search(line):
                sites.add((rel, number))
    return sites


def pick(store, project):
    """Deterministic targets: names defined once, not colliding with builtins, with textual call sites."""
    found = []
    for bare, rows in sorted(definitions(store).items()):
        if len(rows) != 1 or bare.startswith('__') or bare in COLLIDES:
            continue
        path, name, start, end = rows[0]
        sites = call_sites(project, bare)
        if sites:
            found.append((len(sites), name, path, start, end, bare))
    found.sort()
    return found


def closing_parenthesis(lines, start):
    """(line index, column) of the parenthesis that closes the parameter list opened at `start`."""
    depth, opened = 0, False
    for number in range(start - 1, len(lines)):
        for column, char in enumerate(lines[number]):
            if char == '(':
                depth, opened = depth + 1, True
            elif char == ')' and opened:
                depth -= 1
                if depth == 0:
                    return number, column
    return None


def mutate(text, start, end, how):
    lines = text.split('\n')
    if how == 'signature':
        found = closing_parenthesis(lines, start)
        if not found:
            return None
        number, column = found
        before = lines[number][:column]
        if '**' in before.split(',')[-1] or before.rstrip().endswith('*'):
            return None
        joiner = '' if before.rstrip().endswith('(') else ', '
        lines[number] = before + joiner + '__required' + lines[number][column:]
    elif how == 'body':
        for number in range(end - 1, start - 1, -1):
            if lines[number].strip().startswith('return '):
                lines[number] += '  # body changed'
                break
        else:
            return None
    elif how == 'removal':
        lines[start - 1:end] = ['# removed']
    result = '\n'.join(lines)
    try:
        compile(result, 'mutated', 'exec')
    except SyntaxError:
        return None
    return result


def callers(store, symbol, engine):
    packet = semantic_store.build_edit_impact(store, [symbol], hops=1, include_source=False, engine_store=engine)
    rows, truncated = set(), 0
    for target in packet['targets']:
        for caller in target['callers']['listed']:
            for edge in caller.get('edges', []):
                for site in edge.get('sites', []):
                    rows.add((site['file'], site['start_line']))
        truncated += target['callers'].get('truncated', 0) if isinstance(target['callers'], dict) else 0
    return rows, packet, truncated


def score(found, oracle):
    hit = found & oracle
    return {'oracle_sites': len(oracle), 'reported_sites': len(found), 'matched': len(hit),
            'recall': (len(hit) / len(oracle)) if oracle else None,
            'precision': (len(hit) / len(found)) if found else None}


def targets(ranked):
    """Per kind, targets spread over the call-count distribution; the hub kind takes the busiest."""
    last = len(ranked) - 1
    spread = {'signature': (0.30, 0.55, 0.80), 'body': (0.20, 0.45, 0.70), 'removal': (0.25, 0.50, 0.75)}
    chosen = {kind: [ranked[int(last * q)] for q in quantiles] for kind, quantiles in spread.items()}
    chosen['hub'] = list(reversed(ranked[-PER_KIND:]))
    return chosen


def run(project, workdir, environment, output):
    if workdir.exists():
        raise ValueError('workdir must be new')
    shutil.copytree(project, workdir, ignore=shutil.ignore_patterns('.codebase-map', '.evaluation'))
    base_manifest = workdir / '.codebase-map/base.sqlite'
    base_manifest.parent.mkdir()
    snapshot.write_snapshot(workdir, base_manifest)
    subprocess.run([sys.executable, '-B', str(SCRIPTS / 'resolve_edges.py'), str(base_manifest), '--environment',
                    str(environment), '--compact'], capture_output=True, text=True)
    base_engine = resolve_edges.default_edge_store(base_manifest)
    with open_snapshot(base_manifest) as store:
        ranked = pick(store, workdir)
    if len(ranked) < 12:
        raise ValueError('not enough uniquely named called functions to build scenarios')
    results, tally = {}, {}
    for kind, chosen in targets(ranked).items():
        results[kind] = []
        for count, name, path, start, end, bare in chosen:
            how = 'signature' if kind == 'hub' else kind
            mutated = mutate((workdir / path).read_text(encoding='utf8'), start, end, how)
            symbol = f'{path}::{name}'
            if mutated is None:
                results[kind].append({'target': symbol, 'textual_call_sites': count, 'skipped': 'could not be mutated into valid source'})
                continue
            copy = workdir.parent / f'{workdir.name}-{kind}-{len(results[kind])}'
            shutil.copytree(workdir, copy, ignore=shutil.ignore_patterns('.codebase-map'))
            (copy / path).write_text(mutated, encoding='utf8', newline='\n')
            oracle = call_sites(project, bare) if kind == 'removal' else call_sites(copy, bare)
            manifest = copy / '.codebase-map/candidate.sqlite'
            manifest.parent.mkdir(exist_ok=True)
            snapshot.write_snapshot(copy, manifest)
            with open_snapshot(base_manifest) as base, open_snapshot(manifest) as candidate:
                stale = semantic_store.build_stale_callers(base, candidate, limit=1000)
                owner, engine = (base, base_engine) if kind == 'removal' else (candidate, None)
                found, packet, truncated = callers(owner, symbol, engine)
                found_with_engine = callers(base, symbol, base_engine)[0] if kind != 'removal' else found
            changed = {row.get('symbol_id') for row in stale.get('changed', [])}
            row = {'target': symbol, 'textual_call_sites': count, 'mutation': how,
                   'callers_lexical_candidate': score(found, oracle),
                   'callers_with_engine_edges_base': score(found_with_engine, oracle),
                   'caller_listing_truncated': truncated,
                   'stale_callers': {'edit_impact': stale['edit_impact']['total'], 'validation_impact': stale['validation_impact']['total'],
                                     'truncated': stale['edit_impact']['truncated']},
                   'change_detected': symbol in changed}
            results[kind].append(row)
            for label in ('callers_lexical_candidate', 'callers_with_engine_edges_base'):
                bucket = tally.setdefault((kind, label), [0, 0, 0])
                bucket[0] += row[label]['oracle_sites']
                bucket[1] += row[label]['reported_sites']
                bucket[2] += row[label]['matched']
    aggregate = {f'{kind}/{label}': {'oracle_sites': o, 'reported_sites': r, 'matched': m,
                                     'recall': (m / o) if o else None, 'precision': (m / r) if r else None}
                 for (kind, label), (o, r, m) in sorted(tally.items())}
    output.write_text(json.dumps({'schema': 'daodan/impact-holdout-result/v2', 'scenarios': results, 'aggregate': aggregate,
        'oracle': 'regular-expression call sites in the mutated copy, independent of the map',
        'limits': ['One public library; methods called through instances are matched by bare name, so the oracle may include same-named calls.',
                   'Names colliding with builtin container methods were excluded from selection.',
                   'Dynamic dispatch has no textual call site; absence of reported callers there is not independence.',
                   'Counts are per call site (file, line); a target with one site weighs as little as it should.']},
        indent=2) + '\n', encoding='utf8')
    print(json.dumps(aggregate, indent=1)[:2400])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--workdir', type=Path, required=True)
    parser.add_argument('--environment', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run(args.project.resolve(), args.workdir.resolve(), args.environment.resolve(), args.out.resolve())


if __name__ == '__main__':
    main()
