"""Requirements checks for set-level preservation, owner integration and leakage."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from unittest.mock import patch
import unittest

import compaction_campaign as c


def response(case, arm='C1-Q1', call=0.0, result=0.0):
    questions = next(a['questions'] for a in case['arms'] if a['id'] == arm)
    return {'model': c.MODEL, 'answers': {
        key: {'type': 'noul', 'noul': call if key.startswith('call_') else result}
        for key in questions}}


class CompactionCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = c.build_cases()
        cls.aux = c.build_auxiliary(cls.cases)

    def find(self, family='message-receipt', position='middle', needed=True,
             duplicate=False, recovery=False):
        return next(x for x in self.cases if x['family_id'] == 'compaction-' + family
                    and x['factors']['position'] == position and x['factors']['active_task'] == needed
                    and x['factors']['surviving_copy'] == duplicate and x['factors']['exact_archive'] == recovery)

    def test_exact_corpus_dimensions_and_honest_groups(self):
        summary = c.corpus_summary(self.cases)
        self.assertEqual(summary['cases'], 600)
        self.assertEqual(summary['families'], 25)
        self.assertEqual(summary['provenance_clusters'], 16)
        self.assertEqual(summary['questions'], 7200)
        self.assertEqual(summary['public_source_derived'], 240)
        self.assertEqual(summary['observed_real_sessions'], 0)
        self.assertEqual(summary['splits'], {'development': 120, 'calibration': 120, 'verification': 360})

    def test_families_and_public_project_do_not_cross_splits(self):
        for field in ('family_id', 'provenance_id'):
            groups = {}
            for case in self.cases + self.aux:
                groups.setdefault(case[field], set()).add(case['split'])
            self.assertTrue(all(len(splits) == 1 for splits in groups.values()))

    def test_six_arms_change_only_declared_dimensions(self):
        for case in self.cases[::37]:
            arms = {a['id']: a for a in case['arms']}
            self.assertEqual(set(arms), set(c.ARMS))
            for representation in range(3):
                self.assertEqual(arms[f'C{representation}-Q0']['state'], arms[f'C{representation}-Q1']['state'])
                self.assertNotEqual(arms[f'C{representation}-Q0']['questions'], arms[f'C{representation}-Q1']['questions'])
            for wording in range(2):
                self.assertEqual(arms[f'C0-Q{wording}']['questions'], arms[f'C1-Q{wording}']['questions'])
                self.assertEqual(arms[f'C0-Q{wording}']['questions'], arms[f'C2-Q{wording}']['questions'])

    def test_input_excludes_oracle_and_case_identity(self):
        prohibited = ('required_groups', 'allowed_actions', 'outcomes', 'family_definition', 'selection_evidence')
        for case in self.cases:
            for arm in case['arms']:
                encoded = json.dumps({'state': arm['state'], 'questions': arm['questions']})
                self.assertNotIn(case['id'], encoded)
                self.assertTrue(all(key not in encoded for key in prohibited))

    def test_head_truncation_and_total_removal_have_different_consequences(self):
        head = self.find(position='head')
        middle = self.find(position='middle')
        tail = self.find(position='tail')
        self.assertTrue(c._outcome_score(head, ['drop_result'])['success'])
        self.assertFalse(c._outcome_score(head, ['drop_call'])['success'])
        self.assertFalse(c._outcome_score(middle, ['drop_result'])['success'])
        self.assertFalse(c._outcome_score(tail, ['drop_result'])['success'])
        for case in (head, middle, tail):
            self.assertTrue(c._outcome_score(case, ['keep'])['success'])

    def test_duplicate_or_ended_task_permits_total_removal(self):
        duplicate = self.find(duplicate=True)
        ended = self.find(needed=False)
        self.assertTrue(c._outcome_score(duplicate, ['drop_call'])['success'])
        self.assertTrue(c._outcome_score(ended, ['drop_call'])['success'])
        self.assertEqual(c._outcome_score(ended, ['drop_call'])['critical_errors'], 0)

    def test_recovery_requires_matching_hash_locator_and_permission(self):
        case = self.find(recovery=True)
        raw = c._outcome_score(case, ['drop_call'])
        recovered = c._outcome_score(case, ['drop_call'], recover=True)
        self.assertFalse(raw['success'])
        self.assertTrue(recovered['success'])
        self.assertEqual(recovered['recovery_reads'], 1)
        self.assertGreater(recovered['recovery_bytes'], 0)
        for change in ('content', 'locator', 'authorized'):
            broken = copy.deepcopy(case)
            item = broken['oracle']['recovery'][0]
            item[change] = False if change == 'authorized' else 'CHANGED'
            self.assertFalse(c._outcome_score(broken, ['drop_call'], recover=True)['success'])

    def test_protection_cannot_disguise_raw_loss(self):
        case = self.find()
        responses = {'C1-Q1': response(case)}
        scores = c.score_case(case, responses)['strategies']
        self.assertFalse(scores['C1-Q1']['success'])
        self.assertTrue(scores['C1-Q1:protected']['success'])
        self.assertFalse(scores['C1-Q1:protected']['model_success_credit'])

    def test_missing_invalid_or_wrong_model_response_is_not_success(self):
        case = self.find()
        invalid = [None, {}, {'model': 'wrong', 'answers': {}}, response(case)]
        for value in (-0.1, 1.1, float('nan'), True, None):
            item = response(case)
            item['answers']['call_t1']['noul'] = value
            invalid.append(item)
        invalid[-6]['answers'].pop('result_t1')
        wrong_type = response(case)
        wrong_type['answers']['call_t1']['type'] = 'choice'
        invalid.append(wrong_type)
        for item in invalid:
            score = c.score_case(case, {'C1-Q1': item})['strategies']['C1-Q1']
            self.assertFalse(score['success'])
            if item is not None and c._response_valid(case, 'C1-Q1', item):
                continue
            self.assertTrue(score['fallback'])
            self.assertFalse(score['model_success_credit'])

    def test_actual_owner_outcomes_preserve_pairing_text_order_and_input(self):
        for case in self.cases + self.aux:
            self.assertEqual(case['oracle']['upstream_commit'], c.UPSTREAM_COMMIT)
            self.assertEqual(len(case['oracle']['outcomes']), 3 ** len(case['oracle']['candidates']))
            for outcome in case['oracle']['outcomes'].values():
                self.assertTrue(all(outcome['invariants'].values()))
            self.assertTrue(c.score_case(case, {})['strategies']['C-keep-all']['success'])

    def test_joint_duplicate_loss_requires_set_level_oracle(self):
        case = next(x for x in self.aux if x['id'] == 'compaction-joint-02')
        self.assertFalse(c._outcome_score(case, ['drop_call', 'drop_call'])['success'])
        self.assertTrue(c._outcome_score(case, ['keep', 'drop_call'])['success'])
        self.assertTrue(c._outcome_score(case, ['drop_call', 'keep'])['success'])
        self.assertFalse(c._outcome_score(case, ['drop_result', 'drop_result'])['success'])

    def test_joint_complementary_and_candidate_bindings(self):
        complementary = next(x for x in self.aux if x['id'] == 'compaction-joint-06')
        self.assertFalse(c._outcome_score(complementary, ['keep', 'drop_call'])['success'])
        self.assertTrue(c._outcome_score(complementary, ['keep', 'keep'])['success'])
        stale = next(x for x in self.aux if x['id'] == 'compaction-joint-10')
        self.assertFalse(c._outcome_score(stale, ['keep', 'drop_call'])['success'])
        self.assertTrue(c._outcome_score(stale, ['drop_call', 'keep'])['success'])

    def test_joint_receipt_and_status_have_explicit_shared_job_binding(self):
        case = next(x for x in self.aux if x['id'] == 'compaction-joint-18')
        self.assertEqual(case['oracle']['required_groups'],
                         [['job=J81; receipt=ACK-81'], ['job=J81; state=accepted']])
        self.assertTrue(c._outcome_score(case, ['keep', 'drop_call', 'keep', 'drop_call'])['success'])
        self.assertFalse(c._outcome_score(case, ['drop_call', 'drop_call', 'keep', 'keep'])['success'])

    def test_mechanical_card_does_not_know_middle_fact(self):
        case = self.find(position='middle')
        visibility = case['oracle']['representation_fact_visibility']
        self.assertFalse(visibility['C0-Q1'])
        self.assertTrue(visibility['C1-Q1'])
        self.assertFalse(visibility['C2-Q1'])
        tail = self.find(position='tail')
        self.assertTrue(tail['oracle']['representation_fact_visibility']['C2-Q1'])

    def test_public_excerpts_have_verified_bytes_and_license(self):
        manifest, sources = c._sources(c.SOURCE_DIR)
        self.assertEqual(manifest['license'], 'MIT')
        for case in self.cases:
            if case['provenance']['kind'] != 'public_source_derived_simulation':
                continue
            matching = [row for row in sources.values() if row['sha256'] == case['provenance']['artifact_sha256']]
            self.assertEqual(len(matching), 1)
            self.assertIn(case['oracle']['source_fact'], matching[0]['content'])
            self.assertFalse(case['provenance']['observed_session'])

    def test_auxiliary_counts_and_honest_language_scope(self):
        robust = [x for x in self.aux if x['block'] == 'robustness']
        joint = [x for x in self.aux if x['block'] == 'joint_compaction']
        self.assertEqual(len(robust), 480)
        self.assertEqual(len(joint), 24)
        self.assertTrue(all([a['id'] for a in x['arms']] == ['C1-Q1'] for x in robust))
        self.assertTrue(all(len(x['oracle']['candidates']) <= 4 for x in joint))
        self.assertEqual(len({x['base_case_id'] for x in robust}), 120)

    def test_policy_grid_and_no_verification_label_tuning(self):
        candidates = c.policy_candidates()
        self.assertEqual(len(candidates), 253)
        responses = {case['id']: {arm['id']: response(case, arm['id']) for arm in case['arms']}
                     for case in self.cases if case['split'] == 'calibration'}
        selected = c.select_policy(self.cases, responses)
        self.assertEqual(len(selected['selection_cases']), 120)
        self.assertTrue(all(identifier in responses for identifier in selected['selection_cases']))
        changed = copy.deepcopy([x for x in self.cases if x['split'] == 'verification'])
        for case in changed:
            case['oracle']['required_groups'] = [['IMPOSSIBLE']]
        unchanged = [x for x in self.cases if x['split'] != 'verification']
        self.assertEqual(selected['policy'], c.select_policy(unchanged + changed, responses)['policy'])

    def test_scoring_is_pure_and_threshold_equality_is_keep(self):
        case = self.find()
        before = json.dumps(case, sort_keys=True)
        value = response(case, call=0.5, result=0.5)
        encoded = json.dumps(value, sort_keys=True)
        row = c.score_case(case, {'C1-Q1': value})['strategies']['C1-Q1']
        self.assertEqual(row['actions'], ['keep'])
        self.assertTrue(row['success'])
        self.assertEqual(json.dumps(case, sort_keys=True), before)
        self.assertEqual(json.dumps(value, sort_keys=True), encoded)

    def test_pending_pinned_and_incomplete_batches_use_actual_owner(self):
        checks = c.deterministic_checks()
        self.assertTrue(checks['pass'])
        self.assertEqual(checks['model_queries'], 0)
        self.assertEqual(set(checks['checks']), {'pending', 'recent-pair', 'first-message-call',
                                               'timeout', 'missing-answer'})
        self.assertEqual(checks['runtime_identity']['revision'], c.UPSTREAM_COMMIT)
        self.assertEqual(len(checks['runtime_identity']['verified_files']), 16)

    def test_unpinned_override_is_rejected_before_library_import(self):
        with patch.dict(os.environ, {'FAST_JEV_MODULE': str(Path(__file__).resolve())}):
            with self.assertRaisesRegex(RuntimeError, 'does not identify the pinned dependency'):
                c.deterministic_checks()


if __name__ == '__main__':
    unittest.main()
