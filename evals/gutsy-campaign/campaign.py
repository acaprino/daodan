"""Prepare a frozen, gold-free remote bundle and score local evidence separately."""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

from campaign_ledger import MODEL, atomic_json, digest, encoded, validate_requests

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RUN = ROOT / '.daodan/runs/2026-10-26-gutsy-campaign'
SEED = 26102026
DOMAINS = ['routing', 'tools', 'compaction']
PROFILES = {
    'main': {'threads': 4, 'n_ctx': 4096, 'cache': 'lru'},
    't2c1536': {'threads': 2, 'n_ctx': 1536, 'cache': 'intra'},
    't4c1536': {'threads': 4, 'n_ctx': 1536, 'cache': 'intra'},
    't2c4096': {'threads': 2, 'n_ctx': 4096, 'cache': 'intra'},
    't4c4096': {'threads': 4, 'n_ctx': 4096, 'cache': 'intra'},
    'full': {'threads': 4, 'n_ctx': 4096, 'cache': 'full'},
    'long': {'threads': 1, 'n_ctx': 8192, 'cache': 'intra'},
}


def module(domain):
    return importlib.import_module(domain + '_campaign')


def frozen_json(path, value):
    if path.exists():
        if path.read_bytes() != encoded(value) + b'\n':
            raise FileExistsError(f'Frozen artifact differs: {path}; use a new artifact directory')
        return
    atomic_json(path, value)


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case_validation(cases):
    identifiers, groups = set(), {}
    for case in cases:
        if case['id'] in identifiers:
            raise ValueError('Duplicate case identity')
        identifiers.add(case['id'])
        if case['split'] not in {'development', 'calibration', 'verification'}:
            raise ValueError('Unknown split')
        if not case['provenance']['public']:
            raise ValueError('Private/unapproved source cannot enter cloud bundle')
        for kind in ['family_id', 'provenance_id'] + (['template_id'] if case.get('template_id') else []):
            group = (case['domain'], kind, case[kind])
            previous = groups.setdefault(group, case['split'])
            if previous != case['split']:
                raise ValueError(f'Group crosses split: {group}')
        arm_ids = set()
        for arm in case['arms']:
            if arm['id'] in arm_ids:
                raise ValueError('Duplicate arm identity')
            arm_ids.add(arm['id'])
            # All hidden oracle material belongs in the local case record.
            def check(value):
                if isinstance(value, dict):
                    if {'oracle', 'label_basis', 'expected_answer', 'gold_label'} & set(value):
                        raise ValueError('Hidden label field entered inference input')
                    for child in value.values():
                        check(child)
                elif isinstance(value, list):
                    for child in value:
                        check(child)
            check(arm['state'])


def request_for(case, arm, block='core', profile='main', suffix=''):
    key = digest([block, case['id'], arm['id'], suffix])[:28]
    request = {'id': key, 'body': {'model': MODEL, 'state': copy.deepcopy(arm['state']),
                                  'questions': copy.deepcopy(arm['questions'])},
               'profile': profile, 'domain': case['domain'], 'block': block}
    mapping = {'id': key, 'case_id': case['id'], 'arm_id': arm['id'],
               'domain': case['domain'], 'split': case['split'], 'block': block,
               'family_id': case['family_id'], 'provenance_id': case['provenance_id']}
    return request, mapping


def perf_workloads():
    yes = lambda text: {'type': 'noul', 'instructions': text}
    routing_state = {'task': 'Inspect a supplied local change and list substantiated defects.',
                     'phase': 'review', 'authorization': 'read only', 'candidate': 'fixed revision B'}
    route_questions = {
        'depth': {'type': 'choice', 'instructions': 'What reasoning does the job require?',
                  'criteria': {'lookup': 'Read one fact', 'local_edit': 'Apply an exact edit',
                               'multi_step': 'Perform several dependent steps',
                               'architectural': 'Design system boundaries',
                               'adversarial_review': 'Search for defects in a change'}},
        'ambiguity': {'type': 'choice', 'instructions': 'Are essential requirements missing?',
                      'criteria': {'fully_specified': 'Can proceed', 'minor_gaps': 'Small bounded gaps',
                                   'needs_interview': 'Essential decisions absent'}}}
    workloads = [('routing-review', routing_state, route_questions),
                 ('routing-edit', {'task': 'Replace Savee with Save in the one named local file.',
                                   'authorization': 'edit allowed'}, route_questions)]
    for count in [13, 31]:
        catalog = [{'id': f't{i:02}', 'description': description} for i, description in enumerate(
            (['Read local source', 'Edit local source', 'Run local tests', 'Search local files',
              'Read Git diff', 'Read PDF', 'Compute arithmetic', 'Inspect logs'] * 4)[:count])]
        workloads.append((f'tools-{count}', {'task': 'Inspect local source, patch it and run local tests.',
                                           'tools': catalog},
                          {tool['id']: yes(f"Should the available tool '{tool['description']}' be included for this job?")
                           for tool in catalog}))
    for mode in ['immutable', 'receipt']:
        state = {'goal': 'Report the recorded outcome without executing the operation again.',
                 'tool_result': 'Run completed on candidate B; 12 tests passed; receipt abc123.',
                 'source': mode}
        workloads.append((f'compaction-{mode}', state,
                          {'call': yes('Must the tool invocation be retained for this continuation?'),
                           'result': yes('Must the recorded result be retained?')}))
    return workloads


def add_performance(requests, mapping):
    profiles = ['t2c1536', 't4c1536', 't2c4096', 't4c4096']
    for repeat in range(10):
        order = profiles[repeat % 4:] + profiles[:repeat % 4]
        for profile in order:
            for name, state, questions in perf_workloads():
                for batch in (['together', 'separate'] if repeat % 2 == 0 else ['separate', 'together']):
                    decision = f'{repeat}-{profile}-{name}-{batch}'
                    parts = [questions] if batch == 'together' else [{k: v} for k, v in questions.items()]
                    for index, part in enumerate(parts):
                        key = digest(['performance', decision, index])[:28]
                        requests.append({'id': key, 'body': {'model': MODEL, 'state': state, 'questions': part},
                                         'domain': name.split('-')[0], 'block': 'performance', 'profile': profile})
                        mapping.append({'id': key, 'block': 'performance', 'decision_id': decision,
                                        'workload': name, 'profile': profile, 'batch': batch, 'repeat': repeat})


def prepare(target):
    base, auxiliary = [], []
    for domain in DOMAINS:
        owner = module(domain)
        cases = owner.build_cases(HERE / 'sources' / domain)
        base.extend(cases)
        auxiliary.extend(owner.build_auxiliary(cases))
    case_validation(base + auxiliary)
    requests, mapping = [], []
    ordered = []
    rng = random.Random(SEED)
    for split in ['development', 'calibration', 'verification']:
        group = [case for case in base if case['split'] == split]
        rng.shuffle(group)
        ordered.extend(group)
    for case in ordered + auxiliary:
        block = case.get('block', 'core')
        for arm in case['arms']:
            if arm.get('applicable', True) and arm['questions']:
                request, index = request_for(case, arm, block)
                requests.append(request)
                mapping.append(index)
    # Frozen development-only probes precede quality data; no labels are used.
    probe_cases = []
    for domain in DOMAINS:
        candidates = [c for c in base if c['domain'] == domain and c['split'] == 'development']
        candidates.sort(key=lambda c: max(len(json.dumps(a['state'])) for a in c['arms']))
        if candidates:
            probe_cases.extend([candidates[0], candidates[len(candidates)//2], candidates[-1]])
    probes, probe_map = [], []
    for case in probe_cases:
        for arm in case['arms']:
            if arm.get('applicable', True) and arm['questions']:
                req, index = request_for(case, arm, 'development-probe', suffix='probe')
                probes.append(req)
                probe_map.append(index)
    requests = probes + requests
    mapping = probe_map + mapping
    add_performance(requests, mapping)
    add_stress(requests, mapping, base)
    question_count = validate_requests(requests)
    source_hashes = {str(path.relative_to(ROOT)).replace('\\', '/'): file_hash(path)
                     for path in sorted(HERE.rglob('*')) if path.is_file()
                     and '__pycache__' not in path.parts
                     and path.name not in {'analyze_campaign.py', 'test_analyze_campaign.py'}}
    owner_inputs = [ROOT / 'plugins/model-routing/skills/model-routing/scripts/task_router.py']
    owner_inputs.append(ROOT / 'plugins/model-routing/skills/model-routing/scripts/model_capabilities.py')
    owner_inputs += sorted((ROOT / 'evals/gutsy-decision-pilot').glob('*.py'))
    owner_inputs += sorted((ROOT / 'evals/gutsy-decision-pilot').glob('*.mjs'))
    for path in owner_inputs:
        source_hashes[str(path.relative_to(ROOT)).replace('\\', '/')] = file_hash(path)
    stats = {}
    for domain in DOMAINS:
        cases = [c for c in base if c['domain'] == domain]
        stats[domain] = {'scenarios': len(cases),
                         'families': len({c['family_id'] for c in cases}),
                         'provenance_groups': len({c['provenance_id'] for c in cases}),
                         'splits': dict(collections.Counter(c['split'] for c in cases)),
                         'provenance_kinds': dict(collections.Counter(c['provenance']['kind'] for c in cases))}
    block_counts = {}
    for request in requests:
        item = block_counts.setdefault(request['block'], {'requests': 0, 'questions': 0})
        item['requests'] += 1
        item['questions'] += len(request['body']['questions'])
    payload = {'schema': 'gutsy-campaign-input/v1', 'profiles': PROFILES,
               'requests': requests, 'forecast_safety_factor': 1.25,
               'global_seconds': 22*3600, 'maximum_questions': 50000,
               'parity_contract': 'cached-paths-v2',
               'budget_parent': {'run_key': 'campaign-20261026-v1',
                                 'input_hash': '10d662094411e776687c65bfa8f9964a5d9a56370c4d500158ee52152151f443'}}
    original = RUN / 'artifacts'
    if not original.exists() or target == original:
        raise ValueError('This amended builder requires original v1 artifacts and a new output directory')
    old_input = json.loads((original / 'input.json').read_text(encoding='utf-8'))
    if encoded(requests) != encoded(old_input['requests']):
        raise ValueError('Amendment must preserve all executable request bodies and order')
    if encoded(base + auxiliary) + b'\n' != (original / 'cases.json').read_bytes():
        raise ValueError('Amendment must preserve cases and hidden oracle bytes')
    frozen_json(target / 'cases.json', base + auxiliary)
    frozen_json(target / 'request-map.json', mapping)
    frozen_json(target / 'input.json', payload)
    manifest = {'schema': 'gutsy-campaign-manifest/v1', 'seed': SEED,
                'counts': stats, 'blocks': block_counts, 'requests': len(requests),
                'questions': question_count, 'remaining_question_reserve': 50000-question_count,
                'source_hashes': source_hashes,
                'input_sha256': file_hash(target / 'input.json'),
                'cases_sha256': file_hash(target / 'cases.json'),
                'request_map_sha256': file_hash(target / 'request-map.json'),
                'authorization': 'User: ok ho aggionrato, andiamo; 22h / USD6 CPU proposal accepted',
                'analysis_binding': 'Domain scoring and policy grids frozen here; aggregate analyzer is separately versioned and must pass its report-stage checks before results are delivered.',
                'runtime_probe_required': True}
    frozen_json(target / 'manifest.json', manifest)
    print(json.dumps({'target': str(target), 'counts': stats, 'blocks': block_counts,
                      'questions': question_count}, ensure_ascii=False, indent=2))


def add_stress(requests, mapping, cases):
    # Cache-mode parity uses identical fixed development bodies.
    selected = [next(c for c in cases if c['domain'] == d and c['split'] == 'development')
                for d in DOMAINS]
    parity, parity_map = [], []
    for profile in ['main', 't4c4096', 'full']:
        for case in selected:
            arm = next(a for a in case['arms'] if a.get('applicable', True) and a['questions'])
            req, index = request_for(case, arm, 'runtime-parity', profile, suffix=profile)
            index['parity_group'] = case['domain']
            req['parity_group'] = case['domain']
            parity.append(req)
            parity_map.append(index)
    requests[:0] = parity
    mapping[:0] = parity_map
    owner = module('tools')
    for case in [c for c in cases if c['domain'] == 'tools' and c['split'] == 'verification'][:24]:
        plan = owner.tool_runtime_plan(case)
        arms = {a['id']: a for a in case['arms']}
        if plan['family_arm_id'] not in arms or plan['flat_arm_id'] not in arms:
            continue
        family, fm = request_for(case, arms[plan['family_arm_id']], 'tool-path', suffix='family')
        family['profile'] = 't4c4096'
        flat, flatmap = request_for(case, arms[plan['flat_arm_id']], 'tool-path', suffix='hierarchical')
        flat['profile'] = 't4c4096'
        flat['subset'] = {'kind': 'family_gate', 'source_request': family['id'],
                          'family_for_question': plan['family_for_question'], 'threshold': .5}
        retrieval, rm = request_for(case, arms[plan['flat_arm_id']], 'tool-path', suffix='retrieval')
        retrieval['profile'] = 't4c4096'
        retrieval['subset'] = {'kind': 'fixed', 'question_ids': plan['retrieval_question_ids']}
        for request, index, path in [(family, fm, 'family'), (flat, flatmap, 'hierarchical'),
                                      (retrieval, rm, 'retrieval')]:
            index['path'] = path
            requests.append(request)
            mapping.append(index)
    for count in [8, 16, 64, 256]:
        state = {'task': 'Read the current Git diff; no edit or network action is authorized.',
                 'tools': [{'id': f't{i:03}', 'description': 'Read current Git diff' if i == count-1
                            else f'Calculate deterministic metric category {i}'} for i in range(count)]}
        questions = {f't{i:03}': {'type': 'noul', 'instructions': f'Is tool t{i:03} needed for the task?'}
                     for i in range(count)}
        for profile in ['main', 'long']:
            keys = list(questions)
            for chunk in range(0, count, 64):
                key = digest(['catalog', count, profile, chunk])[:28]
                requests.append({'id': key, 'body': {'model': MODEL, 'state': state,
                                 'questions': {k: questions[k] for k in keys[chunk:chunk+64]}},
                                 'profile': profile, 'domain': 'tools', 'block': 'catalog-stress',
                                 'allow_input_limit': True})
                mapping.append({'id': key, 'block': 'catalog-stress', 'catalog_size': count,
                                'required_tool': f't{count-1:03}', 'profile': profile})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare'])
    parser.add_argument('--output', type=Path, default=RUN / 'artifacts-v2-final')
    arguments = parser.parse_args()
    target = arguments.output.resolve()
    if not target.is_relative_to(RUN):
        raise ValueError('Campaign artifacts must stay in the owned run')
    prepare(target)
