import copy
import unittest

import pilot


class BundleIntegrity(unittest.TestCase):
    def case(self):
        return {'id': 'X1', 'domain': 'tools', 'split': 'verification',
                'state': {'objective': 'Read the supplied source'},
                'questions': {'read': {'type': 'noul', 'instructions': 'Is reading needed?'}},
                'oracle': {'private': 'not sent'}}

    def test_payload_does_not_send_hidden_oracle(self):
        case = self.case()
        payload = pilot.model_payload([case])
        self.assertEqual(set(payload['requests'][0]['body']), {'model', 'state', 'questions'})
        self.assertNotIn('oracle', pilot.encoded(payload))

    def test_duplicate_case_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            pilot.validate_cases([self.case(), self.case()])

    def test_leaked_case_id_or_oracle_key_is_rejected(self):
        for state in ({'oracle': 'wrong'}, 'X1 is the case'):
            case = self.case()
            case['state'] = state
            with self.assertRaises(ValueError):
                pilot.validate_cases([case])

    def test_question_budget_is_enforced(self):
        cases = []
        for i in range(8):
            case = copy.deepcopy(self.case())
            case['id'] = f'case-{i}'
            case['questions'] = {str(j): {'type': 'noul'} for j in range(64)}
            cases.append(case)
        with self.assertRaises(ValueError):
            pilot.validate_cases(cases)

    def test_output_cannot_escape_owned_scope(self):
        with self.assertRaises(ValueError):
            pilot.confined(pilot.ROOT / 'README.md')

    def test_remote_input_provenance_is_required(self):
        manifest = {'payload_sha256': 'frozen-input'}
        pilot.check_invocation({'invocation': {'input_sha256': 'frozen-input'}}, manifest)
        for remote in ({}, {'invocation': {'input_sha256': 'different-input'}}):
            with self.assertRaises(ValueError):
                pilot.check_invocation(remote, manifest)


if __name__ == '__main__':
    unittest.main()
