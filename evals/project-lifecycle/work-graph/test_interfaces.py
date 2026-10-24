"""Conformance suites of the four boundary interfaces (spec section 1.3, AC21).

Every mock passes its suite. A real implementation must pass the same suite
before shadow; passing proves the contract's shape, not decision quality.
"""
import copy
import unittest

from interfaces import (InterfaceRejected, require_approved, require_fresh, validate_approved_spec,
                        validate_map_slice, validate_routing, validate_selection)
from mock_context import approved_spec, map_slice
from mock_router import MockRouter
from mock_selector import MockSelector
from routing import escalation_request, routing_request
from test_mock_selector import DATA_HUNK, ROSTER, SEC_HUNK
from test_routing import bugfix_plan
from writer import selection_request

MAP_REQ = {'candidate': 'candidate-1', 'targets': ['react-app/src/components/SearchBar.tsx'], 'hops': 1}
SPEC_REQ = {'task': 'Show /search results in the search bar', 'project': 'phazly'}


class CommonEnvelope(unittest.TestCase):
    def test_unknown_schema_version_is_rejected(self):
        response = map_slice(MAP_REQ)
        response['schema'] = 'daodan/map-slice/v2'
        with self.assertRaises(InterfaceRejected):
            validate_map_slice(response, MAP_REQ)

    def test_response_for_another_request_is_rejected(self):
        with self.assertRaises(InterfaceRejected):
            validate_approved_spec(approved_spec(SPEC_REQ), dict(SPEC_REQ, task='other'))

    def test_missing_implementation_identity_is_rejected(self):
        response = map_slice(MAP_REQ)
        response['implementation'] = {'name': 'mock-mapper'}
        with self.assertRaises(InterfaceRejected):
            validate_map_slice(response, MAP_REQ)


class MapSliceConformance(unittest.TestCase):
    def test_mock_conforms_and_can_be_frozen(self):
        response = validate_map_slice(map_slice(MAP_REQ), MAP_REQ)
        require_fresh(response)
        self.assertTrue(response['gaps'])

    def test_stale_unknown_or_unavailable_slice_returns_to_mapper(self):
        for response in (map_slice(MAP_REQ, freshness='stale'), map_slice(MAP_REQ, freshness='unknown'),
                         map_slice(MAP_REQ, status='unavailable')):
            validate_map_slice(response, MAP_REQ)
            with self.assertRaises(InterfaceRejected):
                require_fresh(response)

    def test_path_owned_by_two_components_is_rejected(self):
        response = map_slice(MAP_REQ)
        response['components'][1]['paths'].append(response['components'][0]['paths'][0])
        with self.assertRaises(InterfaceRejected):
            validate_map_slice(response, MAP_REQ)

    def test_edge_outside_slice_or_without_evidence_is_rejected(self):
        for change in ({'to': 'admin-app'}, {'evidence': ''}, {'kind': 'guess'}):
            response = map_slice(MAP_REQ)
            response['edges'][0].update(change)
            with self.assertRaises(InterfaceRejected):
                validate_map_slice(response, MAP_REQ)


class ApprovedSpecConformance(unittest.TestCase):
    def test_mock_conforms_and_compiles(self):
        require_approved(validate_approved_spec(approved_spec(SPEC_REQ), SPEC_REQ))

    def test_draft_open_questions_or_unavailable_return_to_specs_writer(self):
        for response in (approved_spec(SPEC_REQ, status='proposed'),
                         approved_spec(SPEC_REQ, open_questions=['Rank by recency or score?']),
                         approved_spec(SPEC_REQ, state='unavailable')):
            validate_approved_spec(response, SPEC_REQ)
            with self.assertRaises(InterfaceRejected):
                require_approved(response)

    def test_oracle_must_match_requirement_kind(self):
        response = approved_spec(SPEC_REQ)
        response['requirements'][0]['kind'] = 'refactor'
        with self.assertRaises(InterfaceRejected):
            validate_approved_spec(response, SPEC_REQ)

    def test_contract_outside_requirements_is_rejected(self):
        for change in ({'producer': 'R9'}, {'consumers': ['R2']}, {'consumers': []}):
            response = approved_spec(SPEC_REQ)
            response['contracts'][0].update(change)
            with self.assertRaises(InterfaceRejected):
                validate_approved_spec(response, SPEC_REQ)


class SelectionConformance(unittest.TestCase):
    def setUp(self):
        self.request = selection_request('candidate-1', [SEC_HUNK, DATA_HUNK], ROSTER)

    def test_every_mock_persona_conforms(self):
        for persona in MockSelector.PERSONAS:
            validate_selection(MockSelector(persona).select(self.request), self.request)

    def test_out_of_contract_decisions_are_rejected(self):
        changes = [{'role': 'senior-review:ghost-auditor'}, {'citation': 'H9'},
                   {'probability': 1.4}, {'selected': 'yes'}]
        for change in changes:
            response = MockSelector().select(self.request)
            response['decisions'][0].update(change)
            with self.assertRaises(InterfaceRejected, msg=change):
                validate_selection(response, self.request)

    def test_duplicate_decision_and_decisions_without_ok_are_rejected(self):
        response = MockSelector().select(self.request)
        response['decisions'].append(copy.deepcopy(response['decisions'][0]))
        with self.assertRaises(InterfaceRejected):
            validate_selection(response, self.request)
        response = MockSelector().select(self.request)
        response['status'] = 'abstain'
        with self.assertRaises(InterfaceRejected):
            validate_selection(response, self.request)

    def test_request_without_roster_floor_is_rejected(self):
        request = dict(self.request, roster={'roster': ['senior-review:code-auditor']})
        with self.assertRaises(InterfaceRejected):
            validate_selection(MockSelector().select(request), request)


class RoutingConformance(unittest.TestCase):
    def setUp(self):
        self.request = routing_request(bugfix_plan())

    def test_mock_personas_conform_except_malformed(self):
        for persona in MockRouter.PERSONAS:
            response = MockRouter(persona).route(self.request)
            if persona == 'malformed':
                with self.assertRaises(InterfaceRejected):
                    validate_routing(response, self.request)
            else:
                validate_routing(response, self.request)

    def test_request_lists_only_model_nodes_with_dag_facts(self):
        ids = [n['id'] for n in self.request['nodes']]
        self.assertEqual(ids, ['plan', 'red', 'patch'])
        self.assertEqual(self.request['nodes'][0]['facts'], {'downstream': 3, 'fanin': 0})

    def test_out_of_contract_decisions_are_rejected(self):
        for change in ({'node': 'check'}, {'node': 'ghost'}, {'effort': 'max'}):
            response = MockRouter().route(self.request)
            response['decisions'][0].update(change)
            with self.assertRaises(InterfaceRejected, msg=change):
                validate_routing(response, self.request)

    def test_escalation_response_conforms_to_its_own_request(self):
        plan = bugfix_plan()
        request = escalation_request(plan, 'red', {'tier': 'tier1'}, 'red:1')
        response = MockRouter().escalate(request)
        validate_routing(response, request)
        with self.assertRaises(InterfaceRejected):
            validate_routing(response, self.request)


if __name__ == '__main__':
    unittest.main()
