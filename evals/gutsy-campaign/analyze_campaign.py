"""Validate frozen campaign evidence, calibrate, then report honest denominators.

No network, inference or tool execution. Domain owners retain label and policy
semantics. Partial evidence stays partial; public positive witnesses never become
negative gold. Model quality, procedure fallback and resource measurements stay
separate in both the machine report and the human document.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import sys

from campaign_ledger import MODEL, atomic_json, digest

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / '.daodan/runs/2026-10-26-gutsy-campaign'
SEED = 26102026
BOOTSTRAP_REPLICATIONS = 10000
CONFIDENCE = 1 - .05 / 3
EXECUTORS = ('modal_campaign.py', 'server_bootstrap.py', 'campaign_ledger.py')
WEIGHT_NAME = 'gutsy-0.8b-v04-q4_k_m.gguf'
WEIGHT_SHA256 = 'ddf9c23b8a07c008172f1731f4dd93c464b651b9a70409f0feaf8c2d4e089152'
TERMINAL = {'delivered', 'failed', 'input_limit', 'skipped_inapplicable'}


class ProvenanceError(ValueError):
    """Evidence cannot be attributed to the frozen experiment."""


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as error:
        raise ProvenanceError(f'Cannot read JSON artifact {path.name}: {error}') from error


def inside(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ProvenanceError(f'Artifact path leaves its declared root: {relative}')
    return path


def frozen_module(source_root, relative, expected):
    """Execute the exact verified owner bytes, without using a live import cache."""
    path = inside(source_root, relative)
    source = path.read_bytes()
    actual = hashlib.sha256(source).hexdigest()
    if actual != expected:
        raise ProvenanceError(f'Loaded owner differs from frozen source: {relative}')
    name = 'gutsy_frozen_' + path.stem + '_' + actual[:16]
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    exec(compile(source, str(path), 'exec'), module.__dict__)
    module._campaign_source_sha256 = actual
    return module


def _core(case):
    return case.get('block', 'core') == 'core'


def _number(value, *, nonnegative=True):
    return (not isinstance(value, bool) and isinstance(value, (int, float)) and
            math.isfinite(value) and (not nonnegative or value >= 0))


def validate_case_groups(cases):
    ids, groups = set(), {}
    def no_gold(value):
        if isinstance(value, dict):
            if {'oracle', 'label_basis', 'expected_answer', 'gold_label'} & set(value):
                raise ProvenanceError('Hidden label field entered a model input')
            for child in value.values():
                no_gold(child)
        elif isinstance(value, list):
            for child in value:
                no_gold(child)
    for case in cases:
        if case['id'] in ids:
            raise ProvenanceError('Duplicate case ID')
        ids.add(case['id'])
        if case['split'] not in {'development', 'calibration', 'verification'}:
            raise ProvenanceError('Unknown corpus split')
        if not case['provenance'].get('public'):
            raise ProvenanceError('Case provenance is not approved public/synthetic')
        for field in ('family_id', 'provenance_id', 'template_id'):
            if not case.get(field):
                if field != 'template_id':
                    raise ProvenanceError('Missing family/provenance identity')
                continue
            key = case['domain'], field, case[field]
            previous = groups.setdefault(key, case['split'])
            if previous != case['split']:
                raise ProvenanceError(f'Provenance group crosses splits: {key}')
        arm_ids = set()
        for arm in case['arms']:
            if arm['id'] in arm_ids:
                raise ProvenanceError('Duplicate arm ID')
            arm_ids.add(arm['id'])
            no_gold(arm['state'])
            no_gold(arm['questions'])


def load_bundle(artifacts, source_root=ROOT, source_supplement=None):
    artifacts, source_root = Path(artifacts).resolve(), Path(source_root).resolve()
    manifest = read_json(artifacts / 'manifest.json')
    if manifest.get('schema') != 'gutsy-campaign-manifest/v1':
        raise ProvenanceError('Unsupported campaign manifest')
    names = {'input.json': 'input_sha256', 'cases.json': 'cases_sha256',
             'request-map.json': 'request_map_sha256'}
    for name, field in names.items():
        if file_hash(artifacts / name) != manifest.get(field):
            raise ProvenanceError(f'Frozen artifact hash mismatch: {name}')
    source_hashes = manifest.get('source_hashes')
    if not isinstance(source_hashes, dict) or not source_hashes:
        raise ProvenanceError('Source fingerprints are missing')
    source_hashes = dict(source_hashes)
    supplement = None
    if source_supplement is not None:
        path = Path(source_supplement).resolve()
        record = read_json(path)
        if (record.get('schema') != 'gutsy-source-supplement/v1' or
                record.get('original_manifest_sha256') != file_hash(artifacts / 'manifest.json')):
            raise ProvenanceError('Source supplement is not bound to this original manifest')
        additions = record.get('source_hashes')
        if not isinstance(additions, dict) or not additions or set(additions) & set(source_hashes):
            raise ProvenanceError('Source supplement is empty or replaces an originally frozen source')
        source_hashes.update(additions)
        supplement = {'path': str(path), 'sha256': file_hash(path), 'retrospective_dependency_closure': True,
                      'record': record}
    for name, expected in source_hashes.items():
        path = inside(source_root, name)
        if not path.is_file() or file_hash(path) != expected:
            raise ProvenanceError(f'Frozen source hash mismatch: {name}')
    executor_hashes = {}
    for name in EXECUTORS:
        key = 'evals/gutsy-campaign/' + name
        if key not in source_hashes:
            raise ProvenanceError(f'Executor hash missing from manifest: {name}')
        executor_hashes[name] = source_hashes[key]
    ledger_key = 'evals/gutsy-campaign/campaign_ledger.py'
    ledger_owner = frozen_module(source_root, ledger_key, source_hashes[ledger_key])
    payload = read_json(artifacts / 'input.json')
    cases = read_json(artifacts / 'cases.json')
    mapping = read_json(artifacts / 'request-map.json')
    try:
        questions = ledger_owner.validate_requests(payload['requests'])
        validate_case_groups(cases)
    except (KeyError, TypeError, ValueError) as error:
        raise ProvenanceError(str(error)) from error
    requests = {r['id']: r for r in payload['requests']}
    index = {row['id']: row for row in mapping}
    if len(index) != len(mapping) or set(index) != set(requests):
        raise ProvenanceError('Request map does not match the frozen request set')
    if manifest.get('requests') != len(requests) or manifest.get('questions') != questions:
        raise ProvenanceError('Expanded request/question count differs from manifest')
    case_index = {case['id']: case for case in cases}
    core_pairs = set()
    for request in payload['requests']:
        row = index[request['id']]
        if row.get('block') != request['block']:
            raise ProvenanceError('Request block differs from map')
        if row.get('case_id'):
            case = case_index.get(row['case_id'])
            if case is None or row['domain'] != case['domain'] or request['domain'] != case['domain'] or row['split'] != case['split']:
                raise ProvenanceError('Request map points to a different case/domain/split')
            arm = next((a for a in case['arms'] if a['id'] == row['arm_id']), None)
            if arm is None or digest(request['body']) != digest({'model': MODEL, 'state': arm['state'], 'questions': arm['questions']}):
                raise ProvenanceError('Request body differs from frozen case arm')
            if row['block'] == case.get('block', 'core'):
                pair = case['id'], arm['id']
                if pair in core_pairs:
                    raise ProvenanceError('Duplicate scored case/arm request')
                core_pairs.add(pair)
    for case in cases:
        for arm in case['arms']:
            expected = arm.get('applicable', True) and bool(arm['questions'])
            if expected != ((case['id'], arm['id']) in core_pairs):
                raise ProvenanceError('Frozen case arm has missing or unexpected request')
    contract = payload.get('parity_contract', 'three-path-v1')
    if contract not in {'three-path-v1', 'cached-paths-v2'}:
        raise ProvenanceError('Unknown versioned parity contract')
    if contract == 'cached-paths-v2':
        parent = payload.get('budget_parent')
        if (not isinstance(parent, dict) or set(parent) != {'run_key', 'input_hash'} or
                not isinstance(parent['run_key'], str) or not parent['run_key'].replace('-', '').isalnum() or
                not isinstance(parent['input_hash'], str) or len(parent['input_hash']) != 64 or
                set(parent['input_hash']) - set('0123456789abcdef')):
            raise ProvenanceError('Version 2 is missing its frozen parent budget identity')
    return {'artifacts': artifacts, 'source_root': source_root, 'ledger_owner': ledger_owner,
            'source_hashes': source_hashes, 'source_supplement': supplement,
            'manifest': manifest, 'input': payload, 'cases': cases,
            'case_index': case_index, 'mapping': mapping, 'index': index, 'requests': requests,
            'executor_hash': ledger_owner.digest(executor_hashes), 'manifest_sha256': file_hash(artifacts / 'manifest.json')}


def _effective_request(planned, loaded, request_digest=digest):
    directive = planned.get('subset')
    if not directive:
        return planned
    if directive['kind'] == 'fixed':
        keys = directive['question_ids']
    elif directive['kind'] == 'family_gate':
        source = loaded.get(directive['source_request'])
        if source is None or source['analysis_status'] != 'delivered':
            raise ProvenanceError('Dynamic subset has no valid delivered predecessor')
        answers = source['record']['response']['answers']
        try:
            keys = [q for q, family in directive['family_for_question'].items()
                    if answers[family]['noul'] >= directive['threshold']]
        except (KeyError, TypeError) as error:
            raise ProvenanceError('Malformed family gate evidence') from error
    else:
        raise ProvenanceError('Unknown frozen dynamic procedure')
    if not set(keys) <= set(planned['body']['questions']):
        raise ProvenanceError('Dynamic subset contains an unplanned question')
    body = copy.deepcopy(planned['body'])
    body['questions'] = {key: value for key, value in body['questions'].items() if key in keys}
    return {**planned, 'body': body, 'planned_request_hash': request_digest(planned)}


def validate_cache_record(record, effective, profiles):
    mode = profiles[effective['profile']]['cache']
    expected = {'called': bool(effective['body']['questions']), 'mode': mode}
    if expected['called']:
        usage = record['response'].get('usage', {})
        if usage.get('state_cached') is not (mode != 'full') or not isinstance(usage.get('state_cache_hit'), bool):
            raise ProvenanceError('Cache execution accounting is missing or differs from profile')
        if mode != 'lru' and usage['state_cache_hit']:
            raise ProvenanceError('Inter-request cache hit in a frozen no-LRU profile')
        expected.update(state_cached=usage['state_cached'], state_cache_hit=usage['state_cache_hit'])
    if record.get('cache_attestation') != expected:
        raise ProvenanceError('Cache attestation differs from actual response usage')


def load_evidence(bundle, evidence):
    evidence = Path(evidence).resolve()
    record_dir = evidence / 'records'
    files = {p.stem: p for p in record_dir.glob('*.json')} if record_dir.exists() else {}
    if set(files) - set(bundle['requests']):
        raise ProvenanceError('Evidence contains unplanned request IDs')
    loaded = {}
    request_digest = bundle['ledger_owner'].digest
    for planned in bundle['input']['requests']:
        key = planned['id']
        if key not in files:
            loaded[key] = {'analysis_status': 'missing', 'record': None, 'file_sha256': None,
                           'effective_request': None, 'validation_error': None}
            continue
        record = read_json(inside(evidence, str(files[key].relative_to(evidence))))
        effective = _effective_request(planned, loaded, request_digest)
        if record.get('id') != key or record.get('request_hash') != request_digest(effective):
            raise ProvenanceError(f'Request evidence hash/identity mismatch: {key}')
        if planned.get('subset'):
            if record.get('planned_request_hash', request_digest(planned)) != request_digest(planned):
                raise ProvenanceError('Dynamic record has a changed plan hash')
            if record.get('executed_body') is not None and digest(record['executed_body']) != digest(effective['body']):
                raise ProvenanceError('Executed subset differs from frozen procedure')
            if record.get('status') in {'delivered', 'failed'} and digest(record.get('executed_body')) != digest(effective['body']):
                raise ProvenanceError('Dynamic inference record omitted its executed body')
        elif record.get('executed_body') is not None and digest(record['executed_body']) != digest(planned['body']):
            raise ProvenanceError('Unexpected changed executed body')
        if record.get('profile', planned['profile']) != planned['profile']:
            raise ProvenanceError('Record profile differs from planned profile')
        status = record.get('status')
        if status not in TERMINAL:
            raise ProvenanceError(f'Unknown record terminal state: {status}')
        if status == 'input_limit':
            maximum = record.get('tokens', {}).get('max_prompt_tokens')
            context = bundle['input']['profiles'][planned['profile']]['n_ctx']
            if not planned.get('allow_input_limit') or not _number(maximum) or maximum < context:
                raise ProvenanceError('Input limit is not justified by the frozen profile')
        error = None
        if status == 'delivered':
            try:
                bundle['ledger_owner'].validate_response(effective['body'], record.get('response'))
            except (ValueError, TypeError, KeyError) as problem:
                status, error = 'invalid_response', str(problem)
            else:
                validate_cache_record(record, effective, bundle['input']['profiles'])
        if record.get('elapsed_seconds') is not None and not _number(record['elapsed_seconds']):
            raise ProvenanceError('Invalid elapsed duration in evidence')
        if record.get('combined_rss_bytes') is not None and not _number(record['combined_rss_bytes']):
            raise ProvenanceError('Invalid sampled memory in evidence')
        loaded[key] = {'analysis_status': status, 'record': record,
                       'file_sha256': file_hash(files[key]), 'effective_request': effective,
                       'validation_error': error}
    metadata = {}
    for name in ('ledger.json', 'runtime-summary.json', 'parity-gate.json', 'forecast-gate.json', 'budget-parent.json'):
        path = evidence / name
        if path.exists():
            metadata[name] = read_json(path)
    runtime_reports = []
    for path in sorted(evidence.glob('runtime-*.json')):
        if path.name != 'runtime-summary.json':
            runtime_reports.append(read_json(inside(evidence, path.name)))
    if not runtime_reports and metadata.get('runtime-summary.json'):
        runtime_reports = [metadata['runtime-summary.json']]
    by_attempt = {}
    summary = metadata.get('runtime-summary.json')
    for runtime in runtime_reports + ([summary] if summary else []):
        if runtime.get('input_hash') != bundle['manifest']['input_sha256'] or runtime.get('code_hash') != bundle['executor_hash']:
            raise ProvenanceError('Runtime report does not match input/executor fingerprints')
        identifier = runtime.get('attempt_id')
        if not identifier:
            raise ProvenanceError('Missing runtime attempt ID')
        if runtime.get('model') != MODEL:
            raise ProvenanceError('Runtime model identity differs')
        model = runtime.get('model_artifacts', {}).get(WEIGHT_NAME)
        if model and (model.get('sha256') != WEIGHT_SHA256 or model.get('bytes') != 529296832):
            raise ProvenanceError('Runtime weight identity differs from frozen Q4 artifact')
        without_index = {key: value for key, value in runtime.items() if key != 'attempt_reports'}
        if identifier in by_attempt and without_index != by_attempt[identifier]:
            raise ProvenanceError('Runtime summary or duplicate attempt differs from original report')
        by_attempt[identifier] = without_index
    ledger = metadata.get('ledger.json')
    if ledger:
        if ledger.get('input_hash') != bundle['manifest']['input_sha256'] or ledger.get('code_hash') != bundle['executor_hash']:
            raise ProvenanceError('Ledger fingerprints do not match the experiment')
        for key, entry in ledger.get('requests', {}).items():
            if key not in loaded:
                raise ProvenanceError('Ledger contains unplanned active attempt')
            effective = _effective_request(bundle['requests'][key], loaded, request_digest)
            if entry.get('request_hash') != request_digest(effective):
                raise ProvenanceError('Active ledger request differs from plan')
            if loaded[key]['record'] is None:
                loaded[key]['analysis_status'] = 'unknown' if entry.get('status') in {'running', 'unknown'} else 'missing'
    for row in loaded.values():
        record = row['record']
        if not record or not record.get('attempt_id'):
            continue
        runtime = by_attempt.get(record['attempt_id'])
        if runtime and record.get('host_identity') and record['host_identity'] != runtime.get('host_identity'):
            raise ProvenanceError('Record host differs from its runtime attempt')
    return {'directory': evidence, 'records': loaded, 'metadata': metadata,
            'runtime_attempts': by_attempt,
            'budget_parent_verification': validate_budget_parent(bundle, metadata, by_attempt),
            'metadata_hashes': {path.name: file_hash(path) for path in sorted(evidence.glob('*.json'))},
            'records_sha256': digest({key: value['file_sha256'] for key, value in loaded.items()}),
            'missing_runtime_attempts': sorted({row['record']['attempt_id'] for row in loaded.values()
                if row['record'] and row['record'].get('attempt_id') and row['record']['attempt_id'] not in by_attempt})}


def validate_budget_parent(bundle, metadata, attempts):
    binding = bundle['input'].get('budget_parent')
    if not binding:
        return {'status': 'not_applicable', 'verified': True, 'carried_questions': 0}
    archived = metadata.get('budget-parent.json')
    child = metadata.get('ledger.json')
    if not archived or not child:
        return {'status': 'missing', 'verified': False}
    parent = archived.get('ledger')
    if not isinstance(parent, dict):
        raise ProvenanceError('Archived parent ledger is absent or malformed')
    parent_hash = hashlib.sha256(bundle['ledger_owner'].encoded(parent) + b'\n').hexdigest()
    if (archived.get('run_key') != binding['run_key'] or parent.get('input_hash') != binding['input_hash'] or
            archived.get('ledger_sha256') != parent_hash):
        raise ProvenanceError('Parent budget archive differs from the frozen binding/hash')
    counts = [parent.get('attempted_questions'), parent.get('startup_question_reserve'), parent.get('carried_questions', 0)]
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts):
        raise ProvenanceError('Invalid parent budget question counters')
    carried = sum(counts)
    if (child.get('budget_parent') != binding or child.get('carried_questions') != carried or
            not _number(parent.get('started_at')) or child.get('started_at') != parent['started_at']):
        raise ProvenanceError('Child ledger reset the parent budget or deadline')
    for runtime in attempts.values():
        if runtime.get('budget_parent') is not None and digest(runtime['budget_parent']) != digest(archived):
            raise ProvenanceError('Runtime parent budget attestation differs from the archived ledger')
    verified = bool(attempts) and all(runtime.get('budget_parent') is not None for runtime in attempts.values())
    return {'status': 'verified' if verified else 'missing_runtime_attestation', 'verified': verified,
            'carried_questions': carried, 'original_started_at': parent['started_at'],
            'parent_ledger_sha256': parent_hash, 'binding': binding}


def _responses(bundle, evidence):
    responses, references = defaultdict(dict), defaultdict(dict)
    for row in bundle['mapping']:
        case = bundle['case_index'].get(row.get('case_id'))
        if not case or row['block'] != case.get('block', 'core'):
            continue
        record = evidence['records'][row['id']]
        references[case['id']][row['arm_id']] = {'request_id': row['id'], 'status': record['analysis_status']}
        if record['analysis_status'] == 'delivered':
            responses[case['id']][row['arm_id']] = record['record']['response']
    return dict(responses), dict(references)


def _freeze_json(path, value):
    if path.exists():
        if read_json(path) != value:
            raise ProvenanceError(f'Frozen analysis selection differs: {path.name}; use a new analysis directory')
        return
    atomic_json(path, value)


def select_and_freeze(bundle, evidence, responses, output, owners):
    selected, status = {}, {}
    for domain, owner in owners.items():
        calibration = [c for c in bundle['cases'] if c['domain'] == domain and c['split'] == 'calibration' and _core(c)]
        requests = [row for row in bundle['mapping'] if row.get('domain') == domain and row.get('split') == 'calibration'
                    and row['block'] == 'core']
        pending = [r['id'] for r in requests if evidence['records'][r['id']]['analysis_status'] in {'missing', 'unknown'}]
        if not calibration or pending:
            status[domain] = {'status': 'unavailable', 'reason': 'calibration missing or incomplete',
                              'calibration_cases': len(calibration), 'missing_or_unknown_requests': len(pending)}
            continue
        calibration_responses = {c['id']: responses.get(c['id'], {}) for c in calibration}
        selection = owner.select_policy(calibration, calibration_responses)
        if not isinstance(selection, dict) or not isinstance(selection.get('policy'), dict):
            raise ProvenanceError('Domain owner returned no selected policy')
        sealed = {'schema': 'gutsy-campaign-selection/v1', 'domain': domain,
                  'analysis_source_sha256': file_hash(Path(__file__)),
                  'source_supplement_sha256': bundle['source_supplement']['sha256'] if bundle['source_supplement'] else None,
                  'manifest_sha256': bundle['manifest_sha256'],
                  'calibration_cases_sha256': digest(calibration),
                  'calibration_record_hashes': {r['id']: evidence['records'][r['id']]['file_sha256'] for r in requests},
                  'selection': selection, 'selection_stage': 'before_verification_scoring'}
        _freeze_json(output / 'selections' / (domain + '.json'), sealed)
        selected[domain] = selection['policy']
        status[domain] = {'status': 'frozen', 'policy': selection['policy'],
                          'path': f'selections/{domain}.json', 'calibration_cases': len(calibration)}
    atomic_json(output / 'selection-status.json', status)
    return selected, status


def score_cases(bundle, responses, references, policies, owners):
    rows = []
    for case in bundle['cases']:
        owner = owners[case['domain']]
        diagnostic = owner.score_case(case, responses.get(case['id'], {}))
        strategies = copy.deepcopy(diagnostic['strategies'])
        if case['domain'] == 'routing':
            strategies.pop('R4', None)
        if case.get('block') == 'robustness' and case['domain'] == 'tools':
            strategies = {key: value for key, value in strategies.items() if key in {'T0', 'T1', 'T1-protected'}}
        if _core(case) and case['domain'] in policies:
            calibrated = owner.score_case(case, responses.get(case['id'], {}), policies[case['domain']])
            selected_key = {'routing': 'R4', 'compaction': 'selected'}.get(case['domain'])
            if case['domain'] == 'tools':
                selected_key = calibrated.get('selected_strategy', policies[case['domain']].get('strategy'))
            if selected_key not in calibrated['strategies']:
                raise ProvenanceError('Selected domain strategy is absent from scoring output')
            strategies['selected'] = copy.deepcopy(calibrated['strategies'][selected_key])
        for name, strategy in strategies.items():
            zero_model = name in {'R0', 'T0', 'T4-minimum', 'C-keep-all'}
            if name == 'selected':
                policy = policies[case['domain']]
                zero_model = policy.get('id') in {'R0-baseline', 'keep-all'} or policy.get('strategy') in {'T0', 'T4-minimum'}
            strategy.setdefault('model_called', not zero_model)
            strategy['zero_model_baseline'] = zero_model
            if (strategy.get('success') is not None and not isinstance(strategy.get('success'), bool)) or not isinstance(strategy.get('eligible'), bool):
                raise ProvenanceError('Invalid owner outcome schema')
            if not _number(strategy.get('critical_errors')) or not _number(strategy.get('utility_cost')):
                raise ProvenanceError('Invalid owner critical error or utility count')
        rows.append({'id': case['id'], 'domain': case['domain'], 'split': case['split'],
                     'block': case.get('block', 'core'), 'family_id': case['family_id'],
                     'base_case_id': case.get('base_case_id'), 'perturbation': case.get('perturbation'),
                     'factors': case.get('factors'), 'variant_index': case.get('variant_index'),
                     'provenance_id': case['provenance_id'], 'template_id': case.get('template_id'),
                     'provenance_kind': case['provenance']['kind'],
                     'oracle_kind': case['oracle'].get('kind', 'labelled_requirement'),
                     'request_evidence': references.get(case['id'], {}), 'strategies': strategies})
    return rows


def summarize_outcomes(outcomes):
    eligible = [row for row in outcomes if row['eligible']]
    success = sum(row.get('success') is True for row in eligible)
    failed = sum(row.get('success') is False for row in eligible)
    unknown = sum(row.get('success') is None for row in eligible)
    valid = [row for row in eligible if row.get('model_called', True) and
             row.get('raw_valid_response', row.get('valid_response', row.get('response_valid', False)))]
    return {'preregistered_cases': len(outcomes), 'eligible_cases': len(eligible),
            'ineligible_cases': len(outcomes) - len(eligible),
            'certified_successes': success, 'known_failures': failed, 'unknown_outcomes': unknown,
            'certified_success_fraction': success / len(eligible) if eligible else None,
            'known_outcome_success_fraction': success / (success + failed) if success + failed else None,
            'valid_response_cases': len(valid),
            'valid_response_successes': sum(row.get('success') is True for row in valid),
            'critical_errors': sum(row['critical_errors'] for row in eligible),
            'cases_with_critical_errors': sum(row['critical_errors'] > 0 for row in eligible),
            'fallback_cases': sum(bool(row.get('fallback')) for row in eligible),
            'fallback_successes': sum(bool(row.get('fallback')) and row.get('success') is True for row in eligible),
            'nonfallback_successes': sum(not row.get('fallback') and row.get('success') is True for row in eligible),
            'zero_model_baseline_cases': sum(row.get('zero_model_baseline', False) for row in eligible),
            'protection_applied_cases': sum(row.get('protection_applied', False) for row in eligible),
            'explicit_raw_model_success_credit': sum(row.get('model_success_credit') is True for row in eligible),
            'model_applicable_cases': sum(row.get('model_applicable', True) for row in eligible),
            'witness_retained_cases': sum(row.get('witness_coverage') is True for row in eligible),
            'witness_labelled_cases': sum('witness_coverage' in row for row in eligible),
            'correct_fields': sum(row.get('correct_fields', 0) for row in eligible),
            'labelled_fields': sum(row.get('labelled_fields', 0) for row in eligible),
            'utility_cost_all_cases': sum(row['utility_cost'] for row in outcomes),
            'utility_cost_eligible_cases': sum(row['utility_cost'] for row in eligible),
            'recovery_reads': sum(row.get('recovery_reads', 0) for row in eligible),
            'raw_missing_fact_groups': sum(len(row.get('raw_missing_groups', [])) for row in eligible),
            'final_missing_fact_groups': sum(len(row.get('final_missing_groups', [])) for row in eligible),
            'note': 'Unknown is not a negative label; certified success fraction is a lower bound on known sufficiency, not accuracy when unknowns exist.'}


def aggregate_scores(rows):
    groups = defaultdict(list)
    for case in rows:
        for strategy, outcome in case['strategies'].items():
            key = case['domain'], case['block'], case['split'], case['oracle_kind'], strategy
            groups[key].append(outcome)
    output = []
    for key, values in sorted(groups.items()):
        baseline = {'routing': 'R0', 'tools': 'T0', 'compaction': 'C-keep-all'}[key[0]]
        baseline_cost = sum(row['utility_cost'] for row in groups.get((*key[:4], baseline), []))
        cost = sum(row['utility_cost'] for row in values)
        output.append({'domain': key[0], 'block': key[1], 'split': key[2], 'oracle_kind': key[3],
                       'strategy': key[4], **summarize_outcomes(values),
                       'utility_units': {'routing': 'incorrect_labelled_fields', 'tools': 'normalized_schema_utf8_bytes',
                                         'compaction': 'retained_and_recovered_serialized_bytes'}[key[0]],
                       'baseline_utility_cost': baseline_cost,
                       'utility_reduction_fraction': (baseline_cost - cost) / baseline_cost if baseline_cost else None})
    return output


def corpus_support(cases):
    grouped = defaultdict(list)
    for case in cases:
        grouped[case['domain'], case.get('block', 'core'), case['split']].append(case)
    return [{'domain': key[0], 'block': key[1], 'split': key[2], 'cases': len(rows),
             'families': len({row['family_id'] for row in rows}),
             'provenance_groups': len({row['provenance_id'] for row in rows}),
             'templates': len({row['template_id'] for row in rows if row.get('template_id')}),
             'connected_components': len(set(connected_components(rows).values())),
             'provenance_kinds': dict(Counter(row['provenance']['kind'] for row in rows))}
            for key, rows in sorted(grouped.items())]


def robustness_report(rows):
    by_id = {row['id']: row for row in rows}
    groups = defaultdict(list)
    for case in rows:
        if case['block'] != 'robustness':
            continue
        base = by_id.get(case.get('base_case_id'))
        if not base or not case.get('perturbation'):
            raise ProvenanceError('Robustness case has no frozen base/perturbation identity')
        strategy = {'routing': 'R3', 'tools': 'T1', 'compaction': 'C1-Q1'}[case['domain']]
        groups[case['domain'], case['perturbation'], strategy].append((base, case))
    result = []
    for key, pairs in sorted(groups.items()):
        applicable = [(base['strategies'][key[2]], changed['strategies'][key[2]]) for base, changed in pairs
                      if base['strategies'][key[2]]['eligible'] and changed['strategies'][key[2]]['eligible']]
        result.append({'domain': key[0], 'perturbation': key[1], 'strategy': key[2],
                       'preregistered_pairs': len(pairs), 'eligible_pairs': len(applicable),
                       'base_certified_successes': sum(a['success'] is True for a, b in applicable),
                       'variant_certified_successes': sum(b['success'] is True for a, b in applicable),
                       'known_success_to_failure': sum(a['success'] is True and b['success'] is False for a, b in applicable),
                       'pairs_with_unknown_outcome': sum(a['success'] is None or b['success'] is None for a, b in applicable),
                       'note': 'Dependent variants; no independent sample-size claim.'})
    return result


def connected_components(cases):
    parents = {case['id']: case['id'] for case in cases}
    def find(key):
        while parents[key] != key:
            parents[key] = parents[parents[key]]
            key = parents[key]
        return key
    seen = {}
    for case in cases:
        for field in ('family_id', 'provenance_id', 'template_id'):
            if case.get(field):
                token = case['domain'], field, case[field]
                if token in seen:
                    parents[find(case['id'])] = find(seen[token])
                else:
                    seen[token] = case['id']
    groups = defaultdict(list)
    for key in parents:
        groups[find(key)].append(key)
    result = {}
    for members in groups.values():
        label = min(members)
        for key in members:
            result[key] = label
    return result


def quantile(values, probability):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _contrast(values):
    denominator = sum(row[2] for row in values)
    if not denominator:
        return None
    return (sum(row[1] for row in values) - sum(row[0] for row in values)) / denominator


def paired_cluster_bootstrap(samples, *, complete=True, seed=SEED,
                             replications=BOOTSTRAP_REPLICATIONS, confidence=CONFIDENCE):
    groups = defaultdict(lambda: [0, 0, 0])
    for sample in samples:
        for index, field in enumerate(('left', 'right', 'support')):
            groups[sample['cluster']][index] += sample[field]
    values = [tuple(value) for value in groups.values() if value[2] > 0]
    result = {'difference_right_minus_left': _contrast(values), 'support': sum(v[2] for v in values),
              'cases': len(samples), 'components': len(values), 'confidence': confidence,
              'replications': replications, 'seed': seed, 'interval': None,
              'method': 'Paired cluster bootstrap of summed numerators and denominators; Bonferroni across three primary contrasts.'}
    if not complete:
        result['interval_status'] = 'suppressed_incomplete_preregistered_evidence'
        return result
    if len(values) < 2:
        result['interval_status'] = 'suppressed_fewer_than_two_connected_components'
        return result
    rng = random.Random(seed)
    draws = []
    for _ in range(replications):
        selected = [values[rng.randrange(len(values))] for _ in values]
        draws.append(_contrast(selected))
    alpha = (1 - confidence) / 2
    result['interval'] = [quantile(draws, alpha), quantile(draws, 1 - alpha)]
    result['interval_status'] = 'approximate_small_cluster_warning' if len(values) < 10 else 'approximate'
    return result


def primary_comparisons(rows):
    definitions = [('routing', 'R1', 'R3', 'labelled_field_accuracy'),
                   ('tools', 'T1', 'T2', 'exact_oracle_sufficiency'),
                   ('compaction', 'C0-Q0', 'C1-Q1', 'raw_continuation_evidence')]
    output = []
    for domain, left, right, metric in definitions:
        cases = [row for row in rows if row['domain'] == domain and row['block'] == 'core' and row['split'] == 'verification']
        components = connected_components(cases)
        samples, witnesses = [], []
        missing = sum(any(r['status'] in {'missing', 'unknown'} for r in case['request_evidence'].values()) for case in cases)
        eligible, ineligible, unknown = 0, 0, 0
        for case in cases:
            a, b = case['strategies'][left], case['strategies'][right]
            if a['eligible'] != b['eligible']:
                raise ProvenanceError('Paired strategies disagree on preregistered metric eligibility')
            if not a['eligible']:
                ineligible += 1
                continue
            eligible += 1
            pair = {'case_id': case['id'], 'cluster': components[case['id']]}
            if domain == 'routing':
                fields = set(a['field_matches'])
                if fields != set(b['field_matches']):
                    raise ProvenanceError('Routing paired fields differ')
                pair.update(left=sum(a['field_matches'].values()), right=sum(b['field_matches'].values()), support=len(fields))
            elif domain == 'tools' and case['oracle_kind'] == 'sufficient_witness':
                pair.update(left=int(a['witness_coverage']), right=int(b['witness_coverage']), support=1)
                witnesses.append(pair)
                unknown += int(a['success'] is None or b['success'] is None)
                continue
            else:
                pair.update(left=int(a['success'] is True), right=int(b['success'] is True), support=1)
                unknown += int(a['success'] is None or b['success'] is None)
            samples.append(pair)
        result = {'domain': domain, 'left': left, 'right': right, 'metric': metric,
                  'preregistered_verification_cases': len(cases), 'eligible_cases': eligible,
                  'ineligible_cases': ineligible, 'unknown_pair_outcomes': unknown,
                  'cases_with_missing_requests': missing,
                  'primary': paired_cluster_bootstrap(samples, complete=missing == 0),
                  'public_witness_coverage': paired_cluster_bootstrap(witnesses, complete=missing == 0) if witnesses else None,
                  'sensitivity': {}}
        for field in ('provenance_id', 'template_id', 'family_id'):
            index = {case['id']: case for case in cases}
            grouped = defaultdict(list)
            for sample in samples:
                name = index[sample['case_id']].get(field)
                if name:
                    grouped[name].append(sample)
            sensitivity = []
            for group, own in sorted(grouped.items()):
                other = [sample for sample in samples if index[sample['case_id']].get(field) != group]
                values = lambda data: [(r['left'], r['right'], r['support']) for r in data]
                sensitivity.append({'group': group, 'cases': len(own), 'difference': _contrast(values(own)),
                                    'leave_one_group_out_difference': _contrast(values(other))})
            result['sensitivity'][field] = sensitivity
        output.append(result)
    return output


def _host(record):
    return record.get('host_identity') or ('unidentified-attempt:' + str(record.get('attempt_id', record.get('id'))))


def _decision(request_ids, evidence):
    entries = [evidence['records'][key] for key in request_ids]
    statuses = Counter(row['analysis_status'] for row in entries)
    hosts = sorted({_host(row['record']) for row in entries if row['record']})
    times = [row['record'].get('elapsed_seconds') for row in entries if row['record']]
    complete = (all(row['analysis_status'] == 'delivered' for row in entries) and
                len(times) == len(entries) and all(_number(value) for value in times) and len(hosts) == 1
                and all(row['record'].get('host_identity') and row['record'].get('attempt_id') in evidence['runtime_attempts']
                        for row in entries))
    return {'planned_http_parts': len(request_ids), 'status_counts': dict(statuses),
            'complete_single_host': complete, 'hosts': hosts,
            'http_elapsed_seconds': sum(times) if complete else None,
            'request_ids': request_ids,
            'executed_questions': sum(len(row['effective_request']['body']['questions']) for row in entries
                                      if row['effective_request'] and row['analysis_status'] == 'delivered')}


def _latency_groups(decisions, group_fields):
    groups = defaultdict(list)
    for row in decisions:
        if row['complete_single_host']:
            key = (row['hosts'][0],) + tuple(row[field] for field in group_fields)
            groups[key].append(row['http_elapsed_seconds'])
    return [{'host_identity': key[0], **dict(zip(group_fields, key[1:])), 'decisions': len(values),
             'p50_seconds': quantile(values, .5), 'p95_seconds': quantile(values, .95),
             'one_second_target': 1.0, 'decisions_within_one_second': sum(value <= 1 for value in values),
             'p95_within_one_second': quantile(values, .95) <= 1,
             'minimum_seconds': min(values), 'maximum_seconds': max(values)}
            for key, values in sorted(groups.items())]


def performance_report(bundle, evidence):
    grouped = defaultdict(list)
    metadata = {}
    for row in bundle['mapping']:
        if row['block'] == 'performance':
            grouped[row['decision_id']].append(row['id'])
            metadata[row['decision_id']] = row
    decisions = [{**_decision(ids, evidence), 'decision_id': key,
                  **{field: metadata[key][field] for field in ('profile', 'batch', 'workload', 'repeat')}}
                 for key, ids in grouped.items()]
    paths = defaultdict(dict)
    for row in bundle['mapping']:
        if row['block'] == 'tool-path':
            paths[row['case_id']][row['path']] = row['id']
    path_decisions = []
    for case_id, parts in paths.items():
        for name, keys in (('hierarchical', ('family', 'hierarchical')), ('retrieval', ('retrieval',))):
            if not all(key in parts for key in keys):
                continue
            ids = [parts[key] for key in keys]
            profiles = {bundle['requests'][key]['profile'] for key in ids}
            if len(profiles) != 1:
                raise ProvenanceError('One tool-path decision spans different profiles')
            path_decisions.append({**_decision(ids, evidence), 'case_id': case_id,
                                   'path': name, 'profile': next(iter(profiles))})
    quality = []
    for row in bundle['mapping']:
        if row['block'] == 'core':
            request = bundle['requests'][row['id']]
            quality.append({**_decision([row['id']], evidence), 'case_id': row['case_id'],
                            'domain': row['domain'], 'arm': row['arm_id'], 'profile': request['profile']})
    return {'planned_decisions': len(decisions), 'campaign_target_decisions': 480,
            'complete_single_host_decisions': sum(row['complete_single_host'] for row in decisions),
            'decisions': decisions,
            'groups': _latency_groups(decisions, ('profile', 'batch', 'workload')),
            'tool_path_decisions': path_decisions,
            'tool_path_groups': _latency_groups(path_decisions, ('profile', 'path')),
            'subset_probability_diagnostics': subset_probability_diagnostics(bundle, evidence),
            'core_request_groups': _latency_groups(quality, ('domain', 'arm', 'profile')),
            'measurement': 'Whole decision sums only its HTTP part durations. Server startup, checkpoints, build and downloads are separate. Hosts are never pooled. T2-families is only a family gate, not full hierarchy latency.'}


def subset_probability_diagnostics(bundle, evidence):
    full = {row['case_id']: row['id'] for row in bundle['mapping']
            if row['block'] == 'core' and row.get('domain') == 'tools' and row.get('arm_id') == 'T1'}
    output = []
    for row in bundle['mapping']:
        if row['block'] != 'tool-path' or row.get('path') not in {'hierarchical', 'retrieval'}:
            continue
        baseline_id = full.get(row['case_id'])
        partial = evidence['records'][row['id']]
        baseline = evidence['records'].get(baseline_id)
        result = {'case_id': row['case_id'], 'path': row['path'], 'baseline_request_id': baseline_id,
                  'subset_request_id': row['id'], 'status': 'incomplete', 'compared_questions': 0}
        output.append(result)
        if not baseline or any(entry['analysis_status'] != 'delivered' for entry in (baseline, partial)):
            continue
        differences = []
        changed = 0
        for key, question in partial['effective_request']['body']['questions'].items():
            reference = baseline['effective_request']['body']
            if digest(question) != digest(reference['questions'].get(key)):
                raise ProvenanceError('Subset diagnostic question differs from the full batch')
            a = baseline['record']['response']['answers'][key]['noul']
            b = partial['record']['response']['answers'][key]['noul']
            differences.append(abs(a - b))
            changed += (a >= .5) != (b >= .5)
        result.update(status='compared' if differences else 'empty_subset',
                      compared_questions=len(differences), max_absolute_probability_delta=max(differences, default=None),
                      mean_absolute_probability_delta=sum(differences) / len(differences) if differences else None,
                      decisions_changed_at_diagnostic_half=changed,
                      baseline_profile=bundle['requests'][baseline_id]['profile'], subset_profile=bundle['requests'][row['id']]['profile'],
                      baseline_host=baseline['record'].get('host_identity'), subset_host=partial['record'].get('host_identity'))
    return {'pairs': output, 'planned_pairs': len(output),
            'compared_pairs': sum(row['status'] == 'compared' for row in output),
            'empty_subsets': sum(row['status'] == 'empty_subset' for row in output),
            'incomplete_pairs': sum(row['status'] == 'incomplete' for row in output),
            'limitation': 'Matched diagnostic at threshold 0.5, not retuning. Full batches and subsets may use different cache profiles or hosts; their differences are reported with those identities.'}


def resource_report(evidence):
    attempts = list(evidence['runtime_attempts'].values())
    def positive(value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) and number > 0 else None
    peaks = defaultdict(list)
    for row in evidence['records'].values():
        record = row['record']
        if record and positive(record.get('combined_rss_bytes')):
            peaks[_host(record)].append(record['combined_rss_bytes'])
    for runtime in attempts:
        peak = positive(runtime.get('memory', {}).get('sampled_peak_combined_rss_bytes'))
        if peak:
            peaks[_host(runtime)].append(peak)
    checkpoint_rows = [r['checkpoint'] for r in attempts if isinstance(r.get('checkpoint'), dict)]
    peak = max((max(values) for values in peaks.values()), default=None)
    estimates = [r['estimated_compute_usd'] for r in attempts if _number(r.get('estimated_compute_usd'))]
    ledger = evidence['metadata'].get('ledger.json', {})
    consumed = (sum(ledger.get(key, 0) for key in ('attempted_questions', 'startup_question_reserve', 'carried_questions'))
                if all(_number(ledger.get(key, 0)) for key in ('attempted_questions', 'startup_question_reserve', 'carried_questions'))
                and ledger.get('attempted_questions') is not None else None)
    elapsed = max((r['elapsed_global_seconds'] for r in attempts if _number(r.get('elapsed_global_seconds'))), default=None)
    return {'attempts': len(attempts), 'hosts': sorted(peaks),
            'combined_rss_peak_bytes': peak,
            'combined_rss_peak_by_host': {host: max(values) for host, values in sorted(peaks.items())},
            'local_one_gib_target_met': peak <= 2**30 if peak is not None else None,
            'diagnostic_memory_limit_bytes': 4096 * 2**20,
            'startup_seconds': sum(p['startup_seconds'] for r in attempts for p in r.get('profiles', [])
                                   if _number(p.get('startup_seconds'))),
            'checkpoint_write_seconds': sum(row.get('write_seconds', 0) for row in checkpoint_rows) if checkpoint_rows else None,
            'checkpoint_write_count': sum(row.get('write_count', 0) for row in checkpoint_rows) if checkpoint_rows else None,
            'checkpoint_attempt_coverage': len(checkpoint_rows),
            'global_elapsed_seconds': elapsed, 'global_limit_seconds': 22 * 3600,
            'attempted_questions': ledger.get('attempted_questions'),
            'startup_question_reserve': ledger.get('startup_question_reserve'), 'question_limit': 50000,
            'carried_questions': ledger.get('carried_questions', 0), 'consumed_questions_total': consumed,
            'budget_parent_verification': evidence.get('budget_parent_verification', {'verified': False, 'status': 'unavailable'}),
            'operational_budget_usd': 6, 'estimated_global_compute_usd': max(estimates) if estimates else None,
            'budget_respected': (None if elapsed is None or consumed is None or not estimates else
                elapsed <= 22 * 3600 and consumed <= 50000
                and max(estimates) <= 6),
            'weight_identity_attested_attempts': sum(WEIGHT_NAME in r.get('model_artifacts', {}) for r in attempts),
            'inference_records_missing_runtime_identity': sum(
                row['analysis_status'] in {'delivered', 'failed', 'invalid_response'} and
                (not row['record'].get('host_identity') or not row['record'].get('attempt_id') or
                 row['record']['attempt_id'] not in evidence['runtime_attempts'])
                for row in evidence['records'].values()),
            'model': MODEL,
            'kernel_cgroup_peaks': [{ 'attempt_id': r['attempt_id'], 'bytes': positive(r.get('memory', {}).get('kernel_cgroup_peak'))} for r in attempts],
            'limitations': ['VmRSS sums worker and descendants and can double count shared pages.',
                           'Zero or unavailable cgroup counters are not zero memory use.',
                           'Estimated global compute is an operational estimate, not a paid invoice.',
                           'No local CPU deployment or downstream LLM task was exercised.']}


def coverage_report(bundle, evidence):
    blocks = defaultdict(Counter)
    domains = defaultdict(Counter)
    for request in bundle['input']['requests']:
        status = evidence['records'][request['id']]['analysis_status']
        blocks[request['block']]['planned'] += 1
        blocks[request['block']][status] += 1
        if request['block'] == 'core':
            domains[request['domain']]['planned'] += 1
            domains[request['domain']][status] += 1
    counts = Counter(row['analysis_status'] for row in evidence['records'].values())
    ledger = evidence['metadata'].get('ledger.json', {})
    return {'planned_requests': len(bundle['requests']), 'status_counts': dict(counts),
            'blocks': {key: dict(value) for key, value in sorted(blocks.items())},
            'core_domains': {key: dict(value) for key, value in sorted(domains.items())},
            'all_requests_terminal': not (counts['missing'] or counts['unknown']),
            'all_responses_valid_or_declared_input_limit': all(key in {'delivered', 'input_limit'} for key in counts),
            'ledger_complete': ledger.get('complete') is True,
            'ledger_status': ledger.get('status', 'unavailable'),
            'ledger_error': ledger.get('error'),
            'missing_runtime_attempts': evidence['missing_runtime_attempts']}


def runtime_gate_report(bundle, evidence):
    """Recompute parity from records; report forecast as a bounded runtime attestation."""
    planned = bundle['input']['requests']
    parity = [request for request in planned if request['block'] == 'runtime-parity']
    probes = [request for request in planned if request['block'] == 'development-probe']
    contract = bundle['input'].get('parity_contract', 'three-path-v1')
    result = {}
    for name, requests in (('parity', parity), ('forecast', probes)):
        reported = evidence['metadata'].get(name + '-gate.json')
        row = {'planned_requests': len(requests), 'reported': reported, 'status': 'not_planned'}
        if name == 'parity':
            row['contract'] = contract
            if reported and reported.get('contract', 'three-path-v1') != contract:
                raise ProvenanceError('Runtime parity contract differs from the frozen input version')
        result[name] = row
        if not requests:
            continue
        if any(evidence['records'][request['id']]['analysis_status'] != 'delivered' for request in requests):
            row['status'] = 'incomplete'
            continue
        attestations = [runtime.get(name + '_gate') for runtime in evidence['runtime_attempts'].values()]
        if name == 'forecast':
            if not reported:
                row['status'] = 'incomplete'
                continue
            if reported not in attestations:
                row['status'] = 'unbound_runtime_attestation'
                continue
            estimate = reported.get('forecast_total_seconds')
            factor = reported.get('safety_factor')
            passed = (_number(estimate) and estimate <= 22 * 3600 and
                      _number(factor) and factor == bundle['input'].get('forecast_safety_factor') and
                      reported.get('probe_requests') == len(probes))
            row.update(status='attested_within_budget' if passed else 'failed',
                       limitation='Forecast regression is not independently refitted by this stdlib analyzer; its source, runtime and input hashes are checked.')
            continue
        groups = defaultdict(dict)
        for request in parity:
            group = request.get('parity_group')
            if not group or request['profile'] in groups[group]:
                raise ProvenanceError('Invalid parity group/profile mapping')
            groups[group][request['profile']] = evidence['records'][request['id']]['record']['response']
        full_maxima, cached_maxima, full_decisions, cached_decisions = {}, {}, {}, {}
        def distance(baseline, answer):
            if baseline['type'] == 'noul':
                return abs(baseline['noul'] - answer['noul'])
            return max([abs(baseline['reject'] - answer['reject'])] +
                       [abs(value - answer['probabilities'][label]) for label, value in baseline['probabilities'].items()])
        def decisions(baseline, comparison):
            result = {'questions': len(baseline), 'noul_half_flips': 0, 'choice_flips': 0, 'native_reject_flips': 0}
            for key, first in baseline.items():
                second = comparison[key]
                if first['type'] == 'noul':
                    result['noul_half_flips'] += (first['noul'] >= .5) != (second['noul'] >= .5)
                else:
                    result['choice_flips'] += first['choice'] != second['choice']
                    reject = lambda answer: answer['reject'] >= (1 - answer['reject']) * max(answer['probabilities'].values())
                    result['native_reject_flips'] += reject(first) != reject(second)
            return result
        try:
            for group, variants in groups.items():
                if set(variants) != {'main', 't4c4096', 'full'}:
                    raise ValueError('Incomplete runtime parity profile set')
                full_distances, cached_distances = [], []
                for key, baseline in variants['full']['answers'].items():
                    for mode in ('main', 't4c4096'):
                        answer = variants[mode]['answers'][key]
                        full_distances.append(distance(baseline, answer))
                    cached_distances.append(distance(variants['main']['answers'][key], variants['t4c4096']['answers'][key]))
                full_maxima[group] = max(full_distances, default=0)
                cached_maxima[group] = max(cached_distances, default=0)
                full_decisions[group] = {mode: decisions(variants['full']['answers'], variants[mode]['answers'])
                                         for mode in ('main', 't4c4096')}
                cached_decisions[group] = decisions(variants['main']['answers'], variants['t4c4096']['answers'])
        except (ValueError, KeyError, TypeError) as error:
            raise ProvenanceError(f'Invalid parity evidence: {error}') from error
        maxima = cached_maxima if contract == 'cached-paths-v2' else full_maxima
        if reported and (reported.get('max_probability_delta') != maxima or reported.get('tolerance') != .02):
            raise ProvenanceError('Runtime parity summary differs from underlying response records')
        if reported and contract == 'cached-paths-v2' and reported.get('full_reencoding_max_probability_delta') != full_maxima:
            raise ProvenanceError('Exploratory full-reencoding summary differs from underlying records')
        if reported and contract == 'cached-paths-v2' and reported.get('full_reencoding_equivalence_claimed') is not False:
            raise ProvenanceError('Version 2 cannot claim full-reencoding equivalence')
        status = ('failed' if any(value > .02 for value in maxima.values()) else
                  'incomplete' if not reported else
                  'unbound_runtime_attestation' if reported not in attestations else 'recomputed_pass')
        row.update(status=status,
                   max_probability_delta=maxima, tolerance=.02,
                   cached_paths_max_probability_delta=cached_maxima,
                   cached_paths_decision_differences=cached_decisions,
                   full_reencoding_max_probability_delta=full_maxima,
                   full_reencoding_decision_differences=full_decisions,
                   decision_diagnostic='Noul threshold 0.5; reported choice; native reject >= (1-reject) * maximum class probability. These diagnostics do not alter gate thresholds.',
                   full_reencoding_scope=('exploratory_non_equivalent_factor' if contract == 'cached-paths-v2' else 'original_three_path_gate'),
                   limitation='Three frozen development inputs, not universal numerical equivalence. In v2 full reencoding remains exploratory; no same-quality speedup pooling is justified.')
    result['passed'] = all(result[name]['status'] in {'not_planned', 'recomputed_pass', 'attested_within_budget'} for name in ('parity', 'forecast'))
    return result


def next_steps(summaries, comparison, resources, selections, *, complete=False, performance=None):
    result = {}
    for domain in ('routing', 'tools', 'compaction'):
        rows = [r for r in summaries if r['domain'] == domain and r['block'] == 'core'
                and r['split'] == 'verification' and r['strategy'] == 'selected']
        test = next(row for row in comparison if row['domain'] == domain)
        selection = selections.get(domain, {})
        timing = [row for row in (performance or {}).get('groups', []) if row['workload'].startswith(domain + '-')]
        expected_workloads = {row['workload'] for row in (performance or {}).get('decisions', []) if row['workload'].startswith(domain + '-')}
        passing = defaultdict(set)
        for row in timing:
            if row['p95_within_one_second']:
                passing[row['host_identity'], row['profile'], row['batch']].add(row['workload'])
        passing_scopes = [dict(zip(('host', 'profile', 'batch'), scope)) for scope, workloads in passing.items()
                          if expected_workloads and workloads == expected_workloads]
        if not complete or selection.get('status') != 'frozen' or test['cases_with_missing_requests']:
            action = 'Completare o correggere il banco di prova; dati di verifica incompleti, nessuna promozione del modello.'
        elif any(row['critical_errors'] for row in rows):
            action = 'Analizzare gli errori critici prima di proporre un impiego; se provengono dalla baseline, verificare corpus e controller.'
        elif selection['policy'].get('strategy') in {'R0', 'T0', 'T4-minimum', 'keep-all'} or selection['policy'].get('id') in {'keep-all', 'R0-baseline', 'T0', 'T4-minimum'}:
            action = 'Conservare la baseline deterministica: questo confronto non dimostra un vantaggio utile di Gutsy.'
        elif not rows or any(row['known_failures'] or row['unknown_outcomes'] for row in rows):
            action = 'Analizzare i fallimenti della strategia scelta su calibrazione; non abilitarla automaticamente.'
        elif any(row['fallback_successes'] or row['protection_applied_cases'] or row['recovery_reads'] for row in rows):
            action = 'Separare il successo del fallback dalla qualità del modello; mantenere la procedura conservativa e analizzare i casi recuperati.'
        elif resources['local_one_gib_target_met'] is None or resources['budget_respected'] is not True:
            action = 'Completare o correggere le misure di memoria e budget prima di proporre un impiego locale.'
        elif resources['local_one_gib_target_met'] is False:
            action = 'Qualità candidata nel campione, ma memoria locale fuori obiettivo: ridurre stato, domande o frequenza e riprovare.'
        elif not passing_scopes:
            action = 'Il profiling non dimostra una decisione completa entro un secondo; ridurre il lavoro per chiamata e misurare la CPU locale.'
        else:
            action = 'Candidata a shadow mode su nuove sessioni del dominio; restano da verificare prestazioni locali e qualità downstream.'
        result[domain] = {'action': action,
                          'latency_passing_scopes': passing_scopes,
                          'inference_limit': test['primary']['interval_status'],
                          'production_adoption_authorized': False}
    return result


def render_markdown(report):
    coverage, resource = report['coverage'], report['resources']
    state = 'Campagna con evidenza completa' if report['status'] == 'complete_evidence' else 'Campagna con evidenza incompleta'
    lines = ['# Campagna Gutsy CPU: risultati verificati', '', f'**{state}.** Il completamento della campagna non promuove automaticamente il modello.', '',
             '## Copertura e decisioni', '',
             f"Richieste pianificate: **{coverage['planned_requests']}**. Stati osservati: `{json.dumps(coverage['status_counts'], ensure_ascii=False)}`.", '',
             '| Dominio | Confronto principale grezzo | Differenza | Supporto e limiti | Prossimo passo |',
             '|---|---|---:|---|---|']
    if report['status'] != 'complete_evidence' and coverage.get('ledger_error'):
        lines[4:4] = ['Arresto registrato dal worker (dettagli completi nel JSON):', '',
                      '    ' + json.dumps(coverage['ledger_error'], ensure_ascii=False)[:1200], '']
    for comparison in report['primary_comparisons']:
        stats = comparison['primary']
        delta = stats['difference_right_minus_left']
        value = 'n/d (copertura incompleta)' if comparison['cases_with_missing_requests'] else ('n/d' if delta is None else f'{delta * 100:+.2f} punti %')
        interval = 'IC soppresso' if stats['interval'] is None else f"IC 98,33% [{stats['interval'][0]*100:+.2f}; {stats['interval'][1]*100:+.2f}]"
        lines.append(f"| {comparison['domain']} | {comparison['right']} vs {comparison['left']} | {value} | {stats['cases']} casi; {stats['support']} osservazioni etichettate; {stats['components']} componenti; {interval} | {report['next_steps'][comparison['domain']]['action']} |")
    lines += ['', 'Le differenze includono tutti i casi preregistrati eleggibili per la metrica. Le risposte mancanti non sono successi. '
              'Per i tool, il confronto principale usa gli oracle esatti; i witness BFCL pubblici misurano copertura sufficiente e non forniscono etichette negative per ogni alternativa.', '',
              '## Policy scelte sulla calibrazione', '',
              'Le selezioni sono salvate prima dello scoring della verifica e legate agli hash di corpus e risposte di calibrazione. '
              'I confronti grezzi sopra mantengono le soglie diagnostiche originarie; non usano soglie adattate alla verifica.', '',
              '| Dominio | Policy congelata | Stato |', '|---|---|---|']
    for domain, selection in report['selections'].items():
        lines.append(f"| {domain} | `{selection.get('policy', {}).get('id', 'non disponibile')}` | {selection['status']} |")
    lines += ['', '| Dominio / oracle | Strategia selezionata: successi certificati | Fallimenti noti / sconosciuti | Fallback / errori critici |', '|---|---:|---:|---:|']
    for row in report['summaries']:
        if row['block'] == 'core' and row['split'] == 'verification' and row['strategy'] == 'selected':
            lines.append(f"| {row['domain']} / {row['oracle_kind']} | {row['certified_successes']}/{row['eligible_cases']} ({row['ineligible_cases']} inapplicabili) | {row['known_failures']} / {row['unknown_outcomes']} | {row['fallback_cases']} / {row['critical_errors']} |")
    lines += ['', 'Le procedure protette, i recuperi e le baseline hanno righe distinte nell’analisi per caso. '
              'Il loro successo non è credito per una predizione grezza errata. I token risparmiati negli schemi non sono disponibili: manca un tokenizer esplicito del modello destinatario.', '',
              '## Qualità grezza e procedure protette', '',
              '| Dominio / strategia / oracle | Successi certificati | Sconosciuti | Fallback riusciti | Errori critici | Costo / unità |',
              '|---|---:|---:|---:|---:|---|']
    visible = {'R0', 'R1', 'R3', 'T0', 'T1', 'T2', 'T1-protected', 'T2-protected',
               'C-keep-all', 'C0-Q0', 'C1-Q1', 'C1-Q1:protected'}
    for row in report['summaries']:
        if row['block'] == 'core' and row['split'] == 'verification' and row['strategy'] in visible:
            lines.append(f"| {row['domain']} / {row['strategy']} / {row['oracle_kind']} | {row['certified_successes']}/{row['eligible_cases']} | {row['unknown_outcomes']} | {row['fallback_successes']} | {row['critical_errors']} | {row['utility_cost_all_cases']} {row['utility_units']} |")
    lines += ['', 'I costi in byte non sono token. Le riduzioni rispetto alla baseline sono nell’analisi JSON, con lo stesso insieme di casi. '
              'Robustezza, episodi congiunti e provenienza sono conservati separatamente: le varianti non aumentano il numero di prove indipendenti.', '',
              '## Prestazioni e risorse', '',
              f"Decisioni di profiling complete su un singolo host: **{report['performance']['complete_single_host_decisions']}/{report['performance']['planned_decisions']}** (disegno: 480). "
              'Ogni decisione somma tutte le proprie parti HTTP. Host diversi non vengono aggregati.', '',
              '| Host / profilo | Modalità / workload | Decisioni | p50 | p95 | Entro 1 s |', '|---|---|---:|---:|---:|---:|']
    for row in report['performance']['groups']:
        lines.append(f"| `{row['host_identity'][:18]}` / {row['profile']} | {row['batch']} / {row['workload']} | {row['decisions']} | {row['p50_seconds']:.3f} s | {row['p95_seconds']:.3f} s | {row['decisions_within_one_second']}/{row['decisions']} |")
    lines += ['', 'I replay gerarchici e retrieval realmente eseguiti sono separati dalla simulazione offline di qualità:', '',
              '| Host / profilo | Percorso | Decisioni | p50 | p95 |', '|---|---|---:|---:|---:|']
    for row in report['performance']['tool_path_groups']:
        lines.append(f"| `{row['host_identity'][:18]}` / {row['profile']} | {row['path']} | {row['decisions']} | {row['p50_seconds']:.3f} s | {row['p95_seconds']:.3f} s |")
    subset = report['performance']['subset_probability_diagnostics']
    lines += ['', f"Stabilità catalogo completo/sottoinsieme: {subset['compared_pairs']}/{subset['planned_pairs']} coppie con domande confrontabili, "
              f"{subset['empty_subsets']} sottoinsiemi vuoti, {subset['incomplete_pairs']} coppie incomplete. "
              'Differenze di probabilità e cambiamenti alla soglia diagnostica 0,5 sono nel JSON, insieme a profili e host di entrambe le chiamate.', '']
    peak = 'n/d' if resource['combined_rss_peak_bytes'] is None else f"{resource['combined_rss_peak_bytes']/2**30:.3f} GiB"
    lines += ['', f"Picco RSS combinato: **{peak}**; obiettivo locale 1 GiB, limite diagnostico 4 GiB. La somma può contare pagine condivise più volte.", '',
              f"Avvii server misurati: {resource['startup_seconds']:.3f} s. Scritture checkpoint misurate: {resource['checkpoint_write_seconds'] if resource['checkpoint_write_seconds'] is not None else 'non disponibili'} s. "
              f"Tempo globale: {resource['global_elapsed_seconds']} s; limite 79.200 s. Domande tentate: {resource['attempted_questions']}; riserva startup: {resource['startup_question_reserve']}; limite 50.000.", '',
              f"Domande già consumate dalle versioni precedenti: {resource['carried_questions']}; consumo totale vincolato: {resource['consumed_questions_total']}. "
              f"Verifica del budget ereditato: {resource['budget_parent_verification']['status']}.", '',
              f"Stima operativa del calcolo: {resource['estimated_global_compute_usd']} USD, tetto 6 USD. Non è una fattura; build, download, startup e checkpoint non diventano latenza del modello.", '',
              f"Gate runtime: parità **{report['runtime_gates']['parity']['status']}**; previsione del budget **{report['runtime_gates']['forecast']['status']}**. "
              'La parità viene ricalcolata dalle risposte; la regressione temporale è un’attestazione del runtime vincolata ai suoi hash, non una nuova stima indipendente.', '',
              f"Contratto di parità: `{report['provenance']['parity_contract']}`. Nel contratto v2 la ricodifica completa resta un fattore esplorativo non equivalente; "
              'non viene aggregata come misura di velocità a qualità invariata. Il contratto v1 mantiene il confronto originale fra tutti e tre i percorsi.', '',
              '## Indipendenza e limiti', '',
              'Il bootstrap usa 10.000 ricampionamenti di componenti connessi tramite famiglia, provenienza e template, seed 26102026. '
              'Gli intervalli dei tre confronti principali sono al 98,33% ciascuno (Bonferroni, famiglia 95%). '
              'Con meno di due componenti o verifica incompleta l’intervallo viene soppresso. Le sensibilità per progetto/provenienza, famiglia e template sono nell’analisi JSON.', '',
              'Il routing misura segnali e assegnazione deterministica, non il modello minimo capace di completare il lavoro. '
              'I casi source-derived e i replay non sono automaticamente sessioni utente reali. Le verifiche di compattazione misurano evidenza per la continuazione, '
              'non una risposta di un LLM downstream. Nessuna prestazione osservata su Modal dimostra già il funzionamento sulla CPU locale.', '',
              f"Manifest analizzato: `{report['provenance']['manifest_sha256']}`. Input: `{report['provenance']['input_sha256']}`. Modello atteso: `{MODEL}`.", '',
              'Artefatti locali: `analysis.json`, `case-scores.json`, `selection-status.json` e `selections/` nella directory di analisi scelta. '
              'Risposte originali e registri del worker restano separati e immutati.', '']
    supplement = report['provenance'].get('source_supplement')
    if supplement:
        lines += ['Chiusura retrospettiva delle dipendenze: il manifest originale resta immutato. '
                  f"Sono verificati {report['provenance']['original_bound_sources']} file originali e "
                  f"{report['provenance']['total_bound_sources'] - report['provenance']['original_bound_sources']} aggiunte dichiarate nel supplemento `{supplement['sha256']}`. "
                  'Questa integrazione è distinta dal congelamento originale e non modifica input, oracle o soglie.', '']
    return '\n'.join(lines)


def analyze(artifacts, evidence_directory, output, *, source_root=ROOT, source_supplement=None, owners=None, report_path=None):
    source_root = Path(source_root).resolve()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    bundle = load_bundle(artifacts, source_root, source_supplement)
    evidence = load_evidence(bundle, evidence_directory)
    if owners is None:
        owners = {}
        for domain in sorted({c['domain'] for c in bundle['cases']}):
            key = 'evals/gutsy-campaign/' + domain + '_campaign.py'
            expected = bundle['source_hashes'].get(key)
            if expected is None:
                raise ProvenanceError('Domain scorer owner is absent from frozen source manifest')
            owners[domain] = frozen_module(source_root, key, expected)
    owner_bindings = {'ledger': {'path': str(Path(bundle['ledger_owner'].__file__).resolve()),
                                 'sha256': bundle['ledger_owner']._campaign_source_sha256}}
    for domain, owner in owners.items():
        expected_path = inside(source_root, 'evals/gutsy-campaign/' + domain + '_campaign.py')
        if getattr(owner, '__file__', None):
            actual = Path(owner.__file__).resolve()
            expected = bundle['source_hashes'].get('evals/gutsy-campaign/' + domain + '_campaign.py')
            if actual != expected_path or file_hash(actual) != expected:
                raise ProvenanceError('Actually loaded domain owner differs from the selected frozen source root')
            owner_bindings[domain] = {'path': str(actual), 'sha256': expected, 'verified': True}
            if domain == 'routing':
                required = ('evals/gutsy-decision-pilot/routing_cases.py',
                            'plugins/model-routing/skills/model-routing/scripts/task_router.py',
                            'plugins/model-routing/skills/model-routing/scripts/model_capabilities.py')
                if any(relative not in bundle['source_hashes'] for relative in required):
                    raise ProvenanceError('Routing transitive source identity is missing; bind an explicit source supplement')
                dependencies = [('routing_pilot', owner._pilot(), 'evals/gutsy-decision-pilot/routing_cases.py'),
                                ('canonical_router', owner._router(), 'plugins/model-routing/skills/model-routing/scripts/task_router.py'),
                                ('model_capabilities', sys.modules.get('model_capabilities'),
                                 'plugins/model-routing/skills/model-routing/scripts/model_capabilities.py')]
                for label, module, relative in dependencies:
                    expected_dependency = bundle['source_hashes'].get(relative)
                    actual_dependency = Path(getattr(module, '__file__', '')).resolve()
                    if (expected_dependency is None or actual_dependency != inside(source_root, relative) or
                            not actual_dependency.is_file() or file_hash(actual_dependency) != expected_dependency):
                        raise ProvenanceError('Routing transitive owner differs from frozen source; use a fresh process for this snapshot')
                    owner_bindings[label] = {'path': str(actual_dependency), 'sha256': expected_dependency, 'verified': True}
        else:
            owner_bindings[domain] = {'verified': False, 'scope': 'injected_test_owner_not_campaign_evidence'}
    responses, references = _responses(bundle, evidence)
    policies, selections = select_and_freeze(bundle, evidence, responses, output, owners)
    # This call is deliberately after on-disk calibration selections.
    scored = score_cases(bundle, responses, references, policies, owners)
    summaries = aggregate_scores(scored)
    comparisons = primary_comparisons(scored)
    coverage = coverage_report(bundle, evidence)
    resources = resource_report(evidence)
    performance = performance_report(bundle, evidence)
    gates = runtime_gate_report(bundle, evidence)
    complete = (coverage['ledger_complete'] and coverage['all_responses_valid_or_declared_input_limit']
                and not coverage['missing_runtime_attempts'] and resources['weight_identity_attested_attempts'] == resources['attempts']
                and resources['attempts'] > 0 and not resources['inference_records_missing_runtime_identity'] and gates['passed']
                and resources['budget_parent_verification']['verified']
                and all(owner_bindings[domain]['verified'] for domain in owners))
    analysis_sources = {path.name: file_hash(path) for path in
                        (Path(__file__), Path(__file__).with_name('test_analyze_campaign.py'),
                         Path(atomic_json.__code__.co_filename)) if path.is_file()}
    report = {'schema': 'gutsy-campaign-analysis/v1', 'status': 'complete_evidence' if complete else 'incomplete_evidence',
              'provenance': {'manifest_sha256': bundle['manifest_sha256'], 'input_sha256': bundle['manifest']['input_sha256'],
                             'cases_sha256': bundle['manifest']['cases_sha256'], 'executor_hash': bundle['executor_hash'],
                             'report_stage_source_hashes': analysis_sources,
                             'source_root': str(source_root), 'loaded_owner_bindings': owner_bindings,
                             'source_supplement': bundle['source_supplement'],
                             'original_bound_sources': len(bundle['manifest']['source_hashes']),
                             'total_bound_sources': len(bundle['source_hashes']),
                             'parity_contract': bundle['input'].get('parity_contract', 'three-path-v1'),
                             'budget_parent': bundle['input'].get('budget_parent'),
                             'records_sha256': evidence['records_sha256'], 'metadata_hashes': evidence['metadata_hashes']},
              'coverage': coverage, 'corpus_support': corpus_support(bundle['cases']),
              'selections': selections, 'summaries': summaries, 'robustness': robustness_report(scored),
              'primary_comparisons': comparisons, 'performance': performance,
              'resources': resources, 'runtime_gates': gates,
              'schema_token_savings': {'status': 'unavailable', 'reason': 'No destination-model tokenizer counts supplied.'}}
    report['next_steps'] = next_steps(summaries, comparisons, resources, selections, complete=complete, performance=performance)
    atomic_json(output / 'case-scores.json', scored)
    atomic_json(output / 'analysis.json', report)
    markdown = render_markdown(report)
    (output / 'REPORT.md').write_text(markdown, encoding='utf-8')
    if report_path is not None:
        path = Path(report_path).resolve()
        if not path.is_relative_to((ROOT / 'docs/gutsay').resolve()):
            raise ValueError('Human report must stay in docs/gutsay')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--artifacts', type=Path, default=RUN / 'artifacts')
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, default=ROOT,
                        help='Complete frozen source tree; required for an older version after live sources change.')
    parser.add_argument('--source-supplement', type=Path,
                        help='Explicit retrospective dependency closure bound to the original manifest; never replaces its source identities.')
    parser.add_argument('--output', type=Path, default=RUN / 'analysis')
    parser.add_argument('--report', type=Path)
    arguments = parser.parse_args()
    if not arguments.output.resolve().is_relative_to(RUN.resolve()):
        raise ValueError('Analysis output must stay in the owned campaign run')
    result = analyze(arguments.artifacts, arguments.evidence, arguments.output,
                     source_root=arguments.source_root, source_supplement=arguments.source_supplement,
                     report_path=arguments.report)
    print(json.dumps({'status': result['status'], 'coverage': result['coverage'], 'next_steps': result['next_steps']}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] == 'complete_evidence' else 2)
