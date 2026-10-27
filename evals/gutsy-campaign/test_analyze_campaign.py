"""Adversarial evidence fixtures: no remote service or model answers are used."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import analyze_campaign as a
from campaign_ledger import MODEL, atomic_json, digest


class ToolOwner:
    def __init__(self, output):
        self.output = output
        self.calibration_seen = []
        self.verification_calls = 0

    def select_policy(self, cases, responses):
        if any(c['split'] != 'calibration' for c in cases):
            raise AssertionError('Holdout reached policy selection')
        self.calibration_seen = [c['id'] for c in cases]
        return {'policy': {'id': 'calibration-fixed', 'strategy': 'T1', 'threshold': .6},
                'selection_evidence': {'case_ids': self.calibration_seen}}

    def score_case(self, case, responses, policy=None):
        if case['split'] == 'verification':
            self.verification_calls += 1
            # The aggregate analyzer must persist selection status before any
            # verification scoring, even when calibration is incomplete.
            assert (self.output / 'selection-status.json').is_file()
        threshold = (policy or {}).get('threshold', .5)
        observed = responses.get('T1', {}).get('answers', {}).get('q', {}).get('noul')
        gate = responses.get('T2-families', {}).get('answers', {}).get('f', {}).get('noul')
        valid = observed is not None
        included = bool(valid and observed >= threshold)
        eligible = case['oracle'].get('eligible', True)
        witness = case['oracle']['kind'] == 'sufficient_witness'
        def outcome(selected, is_valid=True, fallback=False):
            success = (True if selected and is_valid else None) if witness else bool(selected and is_valid)
            if not eligible:
                success = None
            return {'eligible': eligible, 'success': success, 'critical_errors': int(not selected) if eligible and not witness else 0,
                    'fallback': fallback, 'valid_response': is_valid, 'utility_cost': 100 if selected else 2,
                    'witness_coverage': bool(selected and is_valid), 'sufficiency_unknown': success is None}
        return {'strategies': {'T0': outcome(True), 'T1': outcome(included, valid),
                               'T2': outcome(included and gate is not None and gate >= threshold, valid and gate is not None),
                               'T1-protected': outcome(included if valid else True, True, not valid)},
                'selected_strategy': (policy or {}).get('strategy', 'T1')}


class Fixture:
    def __init__(self, root, *, missing=(), invalid=(), dynamic=False, performance=False):
        self.root = root
        self.artifacts, self.evidence, self.output = root / 'artifacts', root / 'evidence', root / 'analysis'
        self.artifacts.mkdir(); self.evidence.mkdir(); (self.evidence / 'records').mkdir()
        self.cases = []
        for identifier, split, kind, eligible in [
            ('cal-1', 'calibration', 'exact', True), ('cal-2', 'calibration', 'exact', True),
            ('verify-1', 'verification', 'exact', True), ('verify-2', 'verification', 'exact', True),
            ('verify-source', 'verification', 'sufficient_witness', True),
            ('verify-ineligible', 'verification', 'exact', False),
        ]:
            state = {'objective': 'Read the recorded value.', 'facts': {'candidate': identifier}}
            self.cases.append({'id': identifier, 'domain': 'tools', 'split': split,
                               'family_id': identifier, 'provenance_id': identifier,
                               'provenance': {'public': True, 'kind': 'controlled_synthetic'},
                               'arms': [{'id': 'T1', 'state': state, 'questions': {'q': {'type': 'noul', 'instructions': 'Retain read?'}}},
                                        {'id': 'T2-families', 'state': state, 'questions': {'f': {'type': 'noul', 'instructions': 'Retain family?'}}}],
                               'oracle': {'kind': kind, 'eligible': eligible}})
        self.requests, self.mapping = [], []
        for number, case in enumerate(self.cases):
            for index, arm in enumerate(case['arms']):
                key = f'c{number}a{index}'
                request = {'id': key, 'body': {'model': MODEL, 'state': arm['state'], 'questions': arm['questions']},
                           'profile': 'main', 'domain': 'tools', 'block': 'core'}
                self.requests.append(request)
                self.mapping.append({'id': key, 'case_id': case['id'], 'arm_id': arm['id'], 'domain': 'tools',
                                     'split': case['split'], 'block': 'core'})
        if dynamic:
            case = self.cases[2]
            for key, arm_id, path in [('dynfamily', 'T2-families', 'family'), ('dynflat', 'T1', 'hierarchical'),
                                      ('dynretrieve', 'T1', 'retrieval')]:
                arm = next(x for x in case['arms'] if x['id'] == arm_id)
                request = {'id': key, 'body': {'model': MODEL, 'state': arm['state'], 'questions': arm['questions']},
                           'profile': 'main', 'domain': 'tools', 'block': 'tool-path'}
                if path == 'hierarchical':
                    request['subset'] = {'kind': 'family_gate', 'source_request': 'dynfamily',
                                         'family_for_question': {'q': 'f'}, 'threshold': .5}
                if path == 'retrieval':
                    request['subset'] = {'kind': 'fixed', 'question_ids': []}
                self.requests.append(request)
                self.mapping.append({'id': key, 'case_id': case['id'], 'arm_id': arm_id, 'domain': 'tools',
                                     'split': case['split'], 'block': 'tool-path', 'path': path})
        if performance:
            for index in range(2):
                key = 'perf' + str(index)
                self.requests.append({'id': key, 'body': {'model': MODEL, 'state': 'performance fixture',
                    'questions': {'q' + str(index): {'type': 'noul', 'instructions': 'Need capability?'}}},
                    'profile': 'main', 'domain': 'tools', 'block': 'performance'})
                self.mapping.append({'id': key, 'block': 'performance', 'decision_id': 'one-decision',
                                     'profile': 'main', 'batch': 'separate', 'workload': 'tools-2', 'repeat': 0})
        self.payload = {'schema': 'gutsy-campaign-input/v1', 'profiles': {'main': {'threads': 4, 'n_ctx': 4096, 'cache': 'lru'}},
                        'requests': self.requests}
        self.refresh_bundle()
        self.records = {}
        for request in self.requests:
            if request['id'] in missing:
                continue
            effective = copy.deepcopy(request)
            if request.get('subset'):
                effective['planned_request_hash'] = digest(request)
                if request['subset']['kind'] == 'fixed':
                    effective['body']['questions'] = {}
            value = .2 if self.map(request['id']).get('case_id') == 'verify-source' else .8
            response = {'model': MODEL, 'answers': {key: {'type': 'noul', 'noul': value} for key in effective['body']['questions']},
                        'usage': {'state_cached': True, 'state_cache_hit': False}}
            if request['id'] in invalid:
                response['model'] = 'wrong-model'
            elapsed = .3 if request['id'] == 'perf0' else .8 if request['id'] == 'perf1' else .1
            record = {'id': request['id'], 'request_hash': digest(effective), 'status': 'delivered', 'response': response,
                      'elapsed_seconds': elapsed, 'combined_rss_bytes': 900 * 2**20, 'profile': request['profile'],
                      'attempt_id': 'attempt1', 'host_identity': 'host1',
                      'cache_attestation': {'called': bool(effective['body']['questions']), 'mode': 'lru',
                                            **({'state_cached': True, 'state_cache_hit': False} if effective['body']['questions'] else {})},
                      'executed_body': effective['body'] if request.get('subset') else None}
            self.records[request['id']] = record
            atomic_json(self.evidence / 'records' / (request['id'] + '.json'), record)
        self.runtime = {'attempt_id': 'attempt1', 'host_identity': 'host1', 'model': MODEL,
                        'input_hash': self.manifest['input_sha256'], 'code_hash': self.executor_hash,
                        'model_artifacts': {a.WEIGHT_NAME: {'sha256': a.WEIGHT_SHA256, 'bytes': 529296832}},
                        'profiles': [{'profile': 'main', 'startup_seconds': 2}],
                        'checkpoint': {'write_seconds': .4, 'write_count': 7},
                        'elapsed_global_seconds': 10, 'estimated_compute_usd': .001,
                        'memory': {'sampled_peak_combined_rss_bytes': 950 * 2**20, 'kernel_cgroup_peak': '0'}}
        atomic_json(self.evidence / 'runtime-attempt1.json', self.runtime)
        atomic_json(self.evidence / 'runtime-summary.json', self.runtime)
        self.ledger = {'schema': 'gutsy-campaign-ledger/v1', 'input_hash': self.manifest['input_sha256'],
                       'code_hash': self.executor_hash, 'complete': True, 'status': 'completed',
                       'attempted_questions': sum(len(r['body']['questions']) for r in self.requests),
                       'startup_question_reserve': 6, 'requests': {}, 'completed_requests': len(self.records)}
        atomic_json(self.evidence / 'ledger.json', self.ledger)

    def map(self, key):
        return next(row for row in self.mapping if row['id'] == key)

    def refresh_bundle(self):
        source_hashes = {}
        for name in a.EXECUTORS:
            path = self.root / 'evals/gutsy-campaign' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name == 'campaign_ledger.py':
                path.write_bytes((a.ROOT / 'evals/gutsy-campaign/campaign_ledger.py').read_bytes())
            else:
                path.write_text('fixture source ' + name, encoding='utf-8')
            source_hashes[str(path.relative_to(self.root)).replace('\\', '/')] = a.file_hash(path)
        owner = self.root / 'plugins/model-routing/task_router.py'
        owner.parent.mkdir(parents=True, exist_ok=True)
        owner.write_text('read-only owner fixture', encoding='utf-8')
        source_hashes[str(owner.relative_to(self.root)).replace('\\', '/')] = a.file_hash(owner)
        atomic_json(self.artifacts / 'cases.json', self.cases)
        atomic_json(self.artifacts / 'input.json', self.payload)
        atomic_json(self.artifacts / 'request-map.json', self.mapping)
        self.manifest = {'schema': 'gutsy-campaign-manifest/v1', 'requests': len(self.requests),
                         'questions': sum(len(r['body']['questions']) for r in self.requests),
                         'source_hashes': source_hashes,
                         'cases_sha256': a.file_hash(self.artifacts / 'cases.json'),
                         'input_sha256': a.file_hash(self.artifacts / 'input.json'),
                         'request_map_sha256': a.file_hash(self.artifacts / 'request-map.json')}
        atomic_json(self.artifacts / 'manifest.json', self.manifest)
        self.executor_hash = digest({name: source_hashes['evals/gutsy-campaign/' + name] for name in a.EXECUTORS})

    def load(self):
        bundle = a.load_bundle(self.artifacts, self.root)
        return bundle, a.load_evidence(bundle, self.evidence)


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        a.RUN.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='analysis-test-', dir=a.RUN)
        self.root = Path(self.temporary.name).resolve()
        self.assertTrue(self.root.is_relative_to(a.RUN.resolve()))

    def tearDown(self):
        self.assertTrue(self.root.is_relative_to(a.RUN.resolve()))
        self.temporary.cleanup()

    def run_analysis(self, fixture):
        owner = ToolOwner(fixture.output)
        report = a.analyze(fixture.artifacts, fixture.evidence, fixture.output, source_root=fixture.root,
                           owners={'tools': owner})
        return report, owner

    def test_all_input_and_external_owner_hashes_are_validated(self):
        fixture = Fixture(self.root)
        a.load_bundle(fixture.artifacts, self.root)
        (self.root / 'plugins/model-routing/task_router.py').write_text('changed', encoding='utf-8')
        with self.assertRaisesRegex(a.ProvenanceError, 'source hash mismatch'):
            a.load_bundle(fixture.artifacts, self.root)

    def test_case_hash_and_remote_body_binding_are_independent_checks(self):
        fixture = Fixture(self.root)
        fixture.cases[0]['oracle']['eligible'] = False
        atomic_json(fixture.artifacts / 'cases.json', fixture.cases)
        with self.assertRaisesRegex(a.ProvenanceError, 'artifact hash mismatch'):
            a.load_bundle(fixture.artifacts, self.root)
        fixture.refresh_bundle()
        fixture.requests[0]['body']['state'] = {'different': 'state'}
        fixture.refresh_bundle()
        with self.assertRaisesRegex(a.ProvenanceError, 'body differs'):
            a.load_bundle(fixture.artifacts, self.root)

    def test_group_leakage_and_hidden_oracle_are_rejected(self):
        fixture = Fixture(self.root)
        fixture.cases[2]['provenance_id'] = fixture.cases[0]['provenance_id']
        fixture.refresh_bundle()
        with self.assertRaisesRegex(a.ProvenanceError, 'crosses splits'):
            a.load_bundle(fixture.artifacts, self.root)
        fixture.cases[2]['provenance_id'] = 'separate'
        fixture.cases[0]['arms'][0]['state']['oracle'] = {'answer': True}
        fixture.refresh_bundle()
        with self.assertRaisesRegex(a.ProvenanceError, 'Hidden label'):
            a.load_bundle(fixture.artifacts, self.root)

    def test_missing_holdout_remains_in_denominator_and_suppresses_interval(self):
        fixture = Fixture(self.root, missing=('c2a0',))
        report, owner = self.run_analysis(fixture)
        self.assertEqual(owner.calibration_seen, ['cal-1', 'cal-2'])
        rows = [r for r in report['summaries'] if r['strategy'] == 'T1' and r['split'] == 'verification' and r['oracle_kind'] == 'exact']
        self.assertEqual(rows[0]['preregistered_cases'], 3)
        self.assertEqual(rows[0]['eligible_cases'], 2)
        self.assertEqual(rows[0]['known_failures'], 1)
        self.assertEqual(rows[0]['ineligible_cases'], 1)
        compare = next(c for c in report['primary_comparisons'] if c['domain'] == 'tools')
        self.assertEqual(compare['primary']['interval_status'], 'suppressed_incomplete_preregistered_evidence')
        self.assertEqual(report['status'], 'incomplete_evidence')

    def test_partial_positive_witness_is_unknown_not_negative_gold(self):
        fixture = Fixture(self.root)
        report, _ = self.run_analysis(fixture)
        row = next(r for r in report['summaries'] if r['strategy'] == 'T1' and r['split'] == 'verification' and r['oracle_kind'] == 'sufficient_witness')
        self.assertEqual(row['unknown_outcomes'], 1)
        self.assertEqual(row['known_failures'], 0)
        self.assertEqual(row['critical_errors'], 0)
        comparison = next(c for c in report['primary_comparisons'] if c['domain'] == 'tools')
        self.assertEqual(comparison['primary']['cases'], 2)
        self.assertEqual(comparison['public_witness_coverage']['cases'], 1)

    def test_selection_is_saved_before_holdout_and_cannot_be_retuned(self):
        fixture = Fixture(self.root)
        report, owner = self.run_analysis(fixture)
        self.assertGreater(owner.verification_calls, 0)
        before = a.file_hash(fixture.output / 'selections/tools.json')
        changed = fixture.records['c2a0']
        changed['response']['answers']['q']['noul'] = .0
        atomic_json(fixture.evidence / 'records/c2a0.json', changed)
        self.run_analysis(fixture)
        self.assertEqual(before, a.file_hash(fixture.output / 'selections/tools.json'))
        self.assertEqual(report['selections']['tools']['policy']['threshold'], .6)
        changed = fixture.records['c0a0']
        changed['response']['answers']['q']['noul'] = .0
        atomic_json(fixture.evidence / 'records/c0a0.json', changed)
        with self.assertRaisesRegex(a.ProvenanceError, 'Frozen analysis selection differs'):
            self.run_analysis(fixture)

    def test_incomplete_calibration_does_not_choose_from_holdout(self):
        fixture = Fixture(self.root, missing=('c0a0',))
        report, owner = self.run_analysis(fixture)
        self.assertEqual(owner.calibration_seen, [])
        self.assertEqual(report['selections']['tools']['status'], 'unavailable')
        self.assertFalse((fixture.output / 'selections/tools.json').exists())

    def test_wrong_model_response_cannot_gain_raw_credit(self):
        fixture = Fixture(self.root, invalid=('c2a0',))
        report, _ = self.run_analysis(fixture)
        self.assertEqual(report['coverage']['status_counts']['invalid_response'], 1)
        rows = a.read_json(fixture.output / 'case-scores.json')
        row = next(r for r in rows if r['id'] == 'verify-1')
        self.assertFalse(row['strategies']['T1']['success'])
        self.assertTrue(row['strategies']['T1-protected']['success'])
        self.assertTrue(row['strategies']['T1-protected']['fallback'])

    def test_response_request_hash_mismatch_is_fatal(self):
        fixture = Fixture(self.root)
        fixture.records['c2a0']['request_hash'] = '0' * 64
        atomic_json(fixture.evidence / 'records/c2a0.json', fixture.records['c2a0'])
        with self.assertRaisesRegex(a.ProvenanceError, 'hash/identity mismatch'):
            fixture.load()

    def test_dynamic_subset_is_reconstructed_not_trusted(self):
        fixture = Fixture(self.root, dynamic=True)
        bundle, evidence = fixture.load()
        self.assertEqual(evidence['records']['dynretrieve']['effective_request']['body']['questions'], {})
        altered = fixture.records['dynflat']
        altered['executed_body']['questions'] = {}
        actual = {**next(r for r in fixture.requests if r['id'] == 'dynflat'),
                  'body': altered['executed_body'], 'planned_request_hash': digest(next(r for r in fixture.requests if r['id'] == 'dynflat'))}
        altered['request_hash'] = digest(actual)
        atomic_json(fixture.evidence / 'records/dynflat.json', altered)
        with self.assertRaisesRegex(a.ProvenanceError, 'hash/identity mismatch'):
            fixture.load()

    def test_dynamic_paths_and_whole_decision_times(self):
        fixture = Fixture(self.root, dynamic=True, performance=True)
        bundle, evidence = fixture.load()
        performance = a.performance_report(bundle, evidence)
        self.assertEqual(performance['planned_decisions'], 1)
        self.assertEqual(performance['complete_single_host_decisions'], 1)
        self.assertAlmostEqual(performance['groups'][0]['p50_seconds'], 1.1)
        paths = {row['path']: row for row in performance['tool_path_decisions']}
        self.assertAlmostEqual(paths['hierarchical']['http_elapsed_seconds'], .2)
        self.assertAlmostEqual(paths['retrieval']['http_elapsed_seconds'], .1)
        self.assertEqual(paths['retrieval']['executed_questions'], 0)

    def test_host_mixing_is_not_a_latency_sample(self):
        fixture = Fixture(self.root, performance=True)
        record = fixture.records['perf1']
        record['host_identity'] = 'host2'; record['attempt_id'] = 'attempt2'
        atomic_json(fixture.evidence / 'records/perf1.json', record)
        runtime = {**fixture.runtime, 'host_identity': 'host2', 'attempt_id': 'attempt2'}
        atomic_json(fixture.evidence / 'runtime-attempt2.json', runtime)
        bundle, evidence = fixture.load()
        result = a.performance_report(bundle, evidence)
        self.assertEqual(result['complete_single_host_decisions'], 0)
        self.assertEqual(result['groups'], [])

    def test_memory_zero_is_unknown_and_startup_checkpoint_are_separate(self):
        fixture = Fixture(self.root, performance=True)
        _, evidence = fixture.load()
        resource = a.resource_report(evidence)
        self.assertIsNone(resource['kernel_cgroup_peaks'][0]['bytes'])
        self.assertEqual(resource['startup_seconds'], 2)
        self.assertEqual(resource['checkpoint_write_seconds'], .4)
        self.assertEqual(resource['combined_rss_peak_bytes'], 950 * 2**20)
        self.assertTrue(resource['local_one_gib_target_met'])

    def test_components_union_all_dependency_axes_and_suppress_single_group(self):
        cases = [dict(id='a', domain='routing', family_id='f1', provenance_id='p1', template_id='t1'),
                 dict(id='b', domain='routing', family_id='f2', provenance_id='p2', template_id='t1'),
                 dict(id='c', domain='routing', family_id='f2', provenance_id='p3', template_id='t2')]
        groups = a.connected_components(cases)
        self.assertEqual(len(set(groups.values())), 1)
        samples = [{'cluster': groups[c['id']], 'left': 0, 'right': 1, 'support': 1} for c in cases]
        result = a.paired_cluster_bootstrap(samples)
        self.assertIsNone(result['interval'])
        self.assertEqual(result['components'], 1)
        self.assertEqual(result['support'], 3)

    def test_cluster_bootstrap_counts_clusters_not_rows_and_is_reproducible(self):
        samples = [{'cluster': 'one', 'left': 0, 'right': 1, 'support': 1} for _ in range(30)]
        samples += [{'cluster': 'two', 'left': 1, 'right': 0, 'support': 1}]
        one = a.paired_cluster_bootstrap(samples)
        two = a.paired_cluster_bootstrap(samples)
        self.assertEqual(one, two)
        self.assertEqual(one['components'], 2)
        self.assertEqual(one['replications'], 10000)
        self.assertAlmostEqual(one['confidence'], 1 - .05 / 3)
        self.assertEqual(one['interval'], [-1, 1])

    def test_order_sensitive_request_hash_is_preserved(self):
        left = {'body': {'questions': {'first': 1, 'second': 2}}}
        right = {'body': {'questions': {'second': 2, 'first': 1}}}
        self.assertNotEqual(digest(left), digest(right))

    def test_order_sensitive_case_binding_and_executed_body_are_checked(self):
        fixture = Fixture(self.root, dynamic=True)
        original = fixture.requests[0]['body']
        fixture.requests[0]['body'] = dict(reversed(list(original.items())))
        fixture.refresh_bundle()
        with self.assertRaisesRegex(a.ProvenanceError, 'body differs'):
            a.load_bundle(fixture.artifacts, self.root)
        fixture.requests[0]['body'] = original
        fixture.refresh_bundle()
        record = fixture.records['dynflat']
        record['executed_body'] = dict(reversed(list(record['executed_body'].items())))
        atomic_json(fixture.evidence / 'records/dynflat.json', record)
        with self.assertRaisesRegex(a.ProvenanceError, 'Executed subset'):
            fixture.load()

    def test_diagnostic_scores_are_not_replaced_by_selected_threshold(self):
        fixture = Fixture(self.root)
        fixture.records['c2a0']['response']['answers']['q']['noul'] = .55
        atomic_json(fixture.evidence / 'records/c2a0.json', fixture.records['c2a0'])
        report, _ = self.run_analysis(fixture)
        row = next(r for r in a.read_json(fixture.output / 'case-scores.json') if r['id'] == 'verify-1')
        self.assertTrue(row['strategies']['T1']['success'])
        self.assertFalse(row['strategies']['selected']['success'])
        self.assertIn('analyze_campaign.py', report['provenance']['report_stage_source_hashes'])

    def test_runtime_summary_cannot_disagree_with_attempt(self):
        fixture = Fixture(self.root)
        changed = {**fixture.runtime, 'estimated_compute_usd': 100}
        atomic_json(fixture.evidence / 'runtime-summary.json', changed)
        with self.assertRaisesRegex(a.ProvenanceError, 'summary or duplicate'):
            fixture.load()

    def test_unknown_ledger_attempt_stays_unknown_without_a_response(self):
        fixture = Fixture(self.root, missing=('c2a0',))
        request = next(r for r in fixture.requests if r['id'] == 'c2a0')
        fixture.ledger['requests']['c2a0'] = {'status': 'running', 'request_hash': digest(request)}
        atomic_json(fixture.evidence / 'ledger.json', fixture.ledger)
        report, _ = self.run_analysis(fixture)
        self.assertEqual(report['coverage']['status_counts']['unknown'], 1)
        self.assertEqual(report['status'], 'incomplete_evidence')

    def test_cache_usage_and_attestation_must_match_frozen_profile(self):
        fixture = Fixture(self.root)
        fixture.records['c2a0']['response']['usage']['state_cached'] = False
        atomic_json(fixture.evidence / 'records/c2a0.json', fixture.records['c2a0'])
        with self.assertRaisesRegex(a.ProvenanceError, 'Cache execution'):
            fixture.load()

    def test_missing_attempt_or_host_prevents_complete_attribution(self):
        fixture = Fixture(self.root, performance=True)
        fixture.records['perf0'].pop('attempt_id')
        fixture.records['perf1'].pop('host_identity')
        for key in ('perf0', 'perf1'):
            atomic_json(fixture.evidence / 'records' / (key + '.json'), fixture.records[key])
        report, _ = self.run_analysis(fixture)
        self.assertEqual(report['resources']['inference_records_missing_runtime_identity'], 2)
        self.assertEqual(report['performance']['complete_single_host_decisions'], 0)
        self.assertEqual(report['status'], 'incomplete_evidence')

    def test_unplanned_input_limit_is_rejected_and_skip_is_incomplete(self):
        fixture = Fixture(self.root)
        fixture.records['c2a0'].update(status='input_limit', tokens={'max_prompt_tokens': 5000})
        atomic_json(fixture.evidence / 'records/c2a0.json', fixture.records['c2a0'])
        with self.assertRaisesRegex(a.ProvenanceError, 'Input limit'):
            fixture.load()
        fixture.records['c2a0']['status'] = 'skipped_inapplicable'
        atomic_json(fixture.evidence / 'records/c2a0.json', fixture.records['c2a0'])
        report, _ = self.run_analysis(fixture)
        self.assertEqual(report['status'], 'incomplete_evidence')

    def test_subset_probability_changes_are_observed_not_assumed_equal(self):
        fixture = Fixture(self.root, dynamic=True)
        fixture.records['dynflat']['response']['answers']['q']['noul'] = .3
        atomic_json(fixture.evidence / 'records/dynflat.json', fixture.records['dynflat'])
        bundle, evidence = fixture.load()
        result = a.subset_probability_diagnostics(bundle, evidence)
        row = next(row for row in result['pairs'] if row['path'] == 'hierarchical')
        self.assertAlmostEqual(row['max_absolute_probability_delta'], .5)
        self.assertEqual(row['decisions_changed_at_diagnostic_half'], 1)
        self.assertEqual(result['empty_subsets'], 1)
        self.assertEqual(row['baseline_host'], 'host1')

    def test_fallback_does_not_inflate_valid_response_denominator(self):
        rows = [{'eligible': True, 'success': True, 'critical_errors': 0, 'utility_cost': 10,
                 'fallback': True, 'valid_response': True, 'raw_valid_response': False, 'model_called': True},
                {'eligible': True, 'success': True, 'critical_errors': 0, 'utility_cost': 10,
                 'fallback': False, 'valid_response': True, 'model_called': False, 'zero_model_baseline': True}]
        result = a.summarize_outcomes(rows)
        self.assertEqual(result['valid_response_cases'], 0)
        self.assertEqual(result['fallback_successes'], 1)
        self.assertEqual(result['zero_model_baseline_cases'], 1)

    def test_missing_cost_is_unknown_not_budget_pass(self):
        fixture = Fixture(self.root)
        _, evidence = fixture.load()
        evidence['runtime_attempts']['attempt1'].pop('estimated_compute_usd')
        self.assertIsNone(a.resource_report(evidence)['budget_respected'])

    def test_runtime_parity_recomputed_and_forecast_bound_to_attempt(self):
        requests = [{'id': profile, 'profile': profile, 'block': 'runtime-parity', 'parity_group': 'g'}
                    for profile in ('main', 't4c4096', 'full')]
        requests.append({'id': 'probe', 'block': 'development-probe'})
        records = {request['id']: {'analysis_status': 'delivered', 'record': {'response': {'answers': {'q': {'type': 'noul', 'noul': .6}}}}}
                   for request in requests}
        parity = {'max_probability_delta': {'g': 0.0}, 'tolerance': .02}
        forecast = {'forecast_total_seconds': 400, 'safety_factor': 1.25, 'probe_requests': 1}
        evidence = {'records': records, 'metadata': {'parity-gate.json': parity, 'forecast-gate.json': forecast},
                    'runtime_attempts': {'attempt1': {'parity_gate': parity, 'forecast_gate': forecast}}}
        bundle = {'input': {'requests': requests, 'forecast_safety_factor': 1.25}}
        self.assertTrue(a.runtime_gate_report(bundle, evidence)['passed'])
        records['main']['record']['response']['answers']['q']['noul'] = .7
        with self.assertRaisesRegex(a.ProvenanceError, 'underlying response'):
            a.runtime_gate_report(bundle, evidence)
        records['main']['record']['response']['answers']['q']['noul'] = .6
        del evidence['runtime_attempts']['attempt1']['forecast_gate']
        result = a.runtime_gate_report(bundle, evidence)
        self.assertFalse(result['passed'])
        self.assertEqual(result['forecast']['status'], 'unbound_runtime_attestation')

    def test_failing_parity_records_do_not_require_a_success_gate_artifact(self):
        requests = [{'id': p, 'profile': p, 'block': 'runtime-parity', 'parity_group': 'g'}
                    for p in ('main', 't4c4096', 'full')]
        records = {request['id']: {'analysis_status': 'delivered', 'record': {'response': {
            'answers': {'q': {'type': 'noul', 'noul': .7 if request['id'] == 'full' else .6}}}}}
            for request in requests}
        evidence = {'records': records, 'metadata': {}, 'runtime_attempts': {'attempt1': {}}}
        bundle = {'input': {'requests': requests}}
        result = a.runtime_gate_report(bundle, evidence)
        self.assertEqual(result['parity']['status'], 'failed')
        self.assertFalse(result['passed'])
        records['full']['record']['response']['answers']['q']['noul'] = .6
        self.assertEqual(a.runtime_gate_report(bundle, evidence)['parity']['status'], 'incomplete')

    def test_partial_human_report_shows_recorded_stop_cause(self):
        fixture = Fixture(self.root, missing=('c2a0',))
        fixture.ledger.update(complete=False, status='incomplete', error={'type': 'ValueError', 'message': 'Runtime parity tolerance exceeded'})
        atomic_json(fixture.evidence / 'ledger.json', fixture.ledger)
        self.run_analysis(fixture)
        text = (fixture.output / 'REPORT.md').read_text(encoding='utf-8')
        self.assertIn('Runtime parity tolerance exceeded', text.split('## Copertura')[0])

    def test_v2_cached_contract_never_reinterprets_v1_full_path_failure(self):
        requests = [{'id': p, 'profile': p, 'block': 'runtime-parity', 'parity_group': 'g'}
                    for p in ('main', 't4c4096', 'full')]
        records = {request['id']: {'analysis_status': 'delivered', 'record': {'response': {
            'answers': {'q': {'type': 'noul', 'noul': .4 if request['id'] == 'full' else .6}}}}}
            for request in requests}
        bundle = {'input': {'requests': requests}}
        evidence = {'records': records, 'metadata': {}, 'runtime_attempts': {'attempt': {}}}
        self.assertEqual(a.runtime_gate_report(bundle, evidence)['parity']['status'], 'failed')
        bundle['input']['parity_contract'] = 'cached-paths-v2'
        diagnostic = a.runtime_gate_report(bundle, evidence)['parity']
        gate = {'contract': 'cached-paths-v2', 'max_probability_delta': {'g': 0.0}, 'tolerance': .02,
                'full_reencoding_max_probability_delta': diagnostic['full_reencoding_max_probability_delta'],
                'full_reencoding_equivalence_claimed': False}
        evidence['metadata']['parity-gate.json'] = gate
        evidence['runtime_attempts']['attempt']['parity_gate'] = gate
        result = a.runtime_gate_report(bundle, evidence)
        self.assertTrue(result['passed'])
        self.assertEqual(result['parity']['full_reencoding_scope'], 'exploratory_non_equivalent_factor')
        self.assertEqual(result['parity']['full_reencoding_decision_differences']['g']['main']['noul_half_flips'], 1)
        bundle['input'].pop('parity_contract')
        with self.assertRaisesRegex(a.ProvenanceError, 'contract differs'):
            a.runtime_gate_report(bundle, evidence)

    def test_parent_budget_archive_preserves_spent_questions_and_original_deadline(self):
        fixture = Fixture(self.root)
        bundle, evidence = fixture.load()
        parent = {'input_hash': 'a' * 64, 'attempted_questions': 75, 'startup_question_reserve': 18, 'started_at': 1234}
        binding = {'run_key': 'campaign-20261026-v1', 'input_hash': parent['input_hash']}
        archived = {'run_key': binding['run_key'], 'ledger_sha256': hashlib.sha256(bundle['ledger_owner'].encoded(parent) + b'\n').hexdigest(), 'ledger': parent}
        bundle['input']['budget_parent'] = binding
        evidence['metadata']['budget-parent.json'] = archived
        evidence['metadata']['ledger.json'].update(budget_parent=binding, carried_questions=93, started_at=1234, attempted_questions=49902)
        evidence['runtime_attempts']['attempt1']['budget_parent'] = archived
        verified = a.validate_budget_parent(bundle, evidence['metadata'], evidence['runtime_attempts'])
        self.assertTrue(verified['verified'])
        self.assertEqual(verified['carried_questions'], 93)
        resource = a.resource_report(evidence)
        self.assertEqual(resource['consumed_questions_total'], 50001)
        self.assertFalse(resource['budget_respected'])
        evidence['metadata']['ledger.json']['started_at'] = 9999
        with self.assertRaisesRegex(a.ProvenanceError, 'reset the parent budget'):
            a.validate_budget_parent(bundle, evidence['metadata'], evidence['runtime_attempts'])
        evidence['metadata']['ledger.json']['started_at'] = 1234
        archived['ledger_sha256'] = '0' * 64
        with self.assertRaisesRegex(a.ProvenanceError, 'binding/hash'):
            a.validate_budget_parent(bundle, evidence['metadata'], evidence['runtime_attempts'])

    def test_snapshot_loads_its_exact_ledger_and_rejects_a_live_owner(self):
        fixture = Fixture(self.root)
        bundle, _ = fixture.load()
        expected = self.root / 'evals/gutsy-campaign/campaign_ledger.py'
        self.assertEqual(Path(bundle['ledger_owner'].__file__).resolve(), expected.resolve())
        self.assertEqual(Path(bundle['ledger_owner'].digest.__code__.co_filename).resolve(), expected.resolve())
        self.assertEqual(bundle['ledger_owner']._campaign_source_sha256, a.file_hash(expected))
        import types
        owner = types.SimpleNamespace(__file__=str(a.ROOT / 'evals/gutsy-campaign/tools_campaign.py'))
        with self.assertRaisesRegex(a.ProvenanceError, 'Actually loaded domain owner'):
            a.analyze(fixture.artifacts, fixture.evidence, fixture.output, source_root=self.root, owners={'tools': owner})
        with self.assertRaisesRegex(a.ProvenanceError, 'Loaded owner differs'):
            a.frozen_module(self.root, 'evals/gutsy-campaign/campaign_ledger.py', '0' * 64)

    def test_v2_input_requires_explicit_version_and_parent_identity(self):
        fixture = Fixture(self.root)
        fixture.payload['parity_contract'] = 'cached-paths-v2'
        fixture.refresh_bundle()
        with self.assertRaisesRegex(a.ProvenanceError, 'parent budget identity'):
            a.load_bundle(fixture.artifacts, self.root)
        fixture.payload['budget_parent'] = {'run_key': 'campaign-20261026-v1', 'input_hash': 'a' * 64}
        fixture.refresh_bundle()
        a.load_bundle(fixture.artifacts, self.root)
        fixture.payload['parity_contract'] = 'silently-relaxed'
        fixture.refresh_bundle()
        with self.assertRaisesRegex(a.ProvenanceError, 'Unknown versioned'):
            a.load_bundle(fixture.artifacts, self.root)

    def test_retrospective_source_supplement_is_explicit_bound_and_additive(self):
        fixture = Fixture(self.root)
        relative = 'plugins/model-routing/model_capabilities.py'
        extra = self.root / relative
        extra.write_text('VOCABULARY = ("tool_call",)\n', encoding='utf-8')
        supplement = {'schema': 'gutsy-source-supplement/v1',
                      'original_manifest_sha256': a.file_hash(fixture.artifacts / 'manifest.json'),
                      'source_hashes': {relative: a.file_hash(extra)}, 'reason': 'retrospective dependency closure'}
        path = self.root / 'source-supplement.json'
        atomic_json(path, supplement)
        plain = a.load_bundle(fixture.artifacts, self.root)
        self.assertNotIn(relative, plain['source_hashes'])
        bound = a.load_bundle(fixture.artifacts, self.root, path)
        self.assertEqual(bound['source_hashes'][relative], a.file_hash(extra))
        self.assertTrue(bound['source_supplement']['retrospective_dependency_closure'])
        self.assertNotIn(relative, bound['manifest']['source_hashes'])
        supplement['source_hashes'] = {'evals/gutsy-campaign/campaign_ledger.py': '0' * 64}
        atomic_json(path, supplement)
        with self.assertRaisesRegex(a.ProvenanceError, 'replaces an originally frozen'):
            a.load_bundle(fixture.artifacts, self.root, path)
        supplement['original_manifest_sha256'] = '0' * 64
        atomic_json(path, supplement)
        with self.assertRaisesRegex(a.ProvenanceError, 'not bound to this original'):
            a.load_bundle(fixture.artifacts, self.root, path)

    def test_decision_requires_complete_evidence_and_coherent_latency_scope(self):
        summary = {'domain': 'tools', 'block': 'core', 'split': 'verification', 'strategy': 'selected',
                   'critical_errors': 0, 'known_failures': 0, 'unknown_outcomes': 0,
                   'fallback_successes': 0, 'protection_applied_cases': 0, 'recovery_reads': 0}
        comparisons = [{'domain': d, 'cases_with_missing_requests': 0, 'primary': {'interval_status': 'test'}}
                       for d in ('routing', 'tools', 'compaction')]
        resources = {'local_one_gib_target_met': True, 'budget_respected': True}
        selections = {'tools': {'status': 'frozen', 'policy': {'id': 'T1', 'strategy': 'T1'}}}
        performance = {'decisions': [{'workload': 'tools-2'}, {'workload': 'tools-8'}],
                       'groups': [{'host_identity': 'h', 'profile': 'p', 'batch': 'batch', 'workload': w,
                                   'p95_within_one_second': w == 'tools-2'} for w in ('tools-2', 'tools-8')]}
        def decision(complete=True):
            return a.next_steps([summary], comparisons, resources, selections,
                                complete=complete, performance=performance)['tools']
        self.assertIn('incompleti', decision(False)['action'])
        self.assertEqual(decision()['latency_passing_scopes'], [])
        performance['groups'][1]['p95_within_one_second'] = True
        self.assertIn('shadow mode', decision()['action'])
        summary['fallback_successes'] = 1
        self.assertIn('conservativa', decision()['action'])
        selections['tools']['policy'] = {'id': 'T0', 'strategy': 'T0'}
        summary['known_failures'] = 1
        self.assertIn('baseline deterministica', decision()['action'])


if __name__ == '__main__':
    unittest.main()
