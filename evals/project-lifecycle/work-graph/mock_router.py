"""Deterministic mock of the model router (I4).

Answers a daodan/routing/v1 request without a model. Personas: accurate
(the operator floors), cheap (tier1 everywhere), greedy (tier3 everywhere),
abstain, unavailable and malformed (an option outside the closed set).
"""
from __future__ import annotations

from interfaces import TIERS, digest
from policy import CRITICAL_ROLES

ACCURATE = {'SPEC_ADR': 'tier2', 'PLAN': 'tier2', 'VERIFY_FINDING': 'tier2'}
FIXED = {'cheap': 'tier1', 'greedy': 'tier3', 'malformed': 'tier9'}


class MockRouter:
    PERSONAS = ('accurate', 'cheap', 'greedy', 'abstain', 'unavailable', 'malformed')

    def __init__(self, persona='accurate'):
        if persona not in self.PERSONAS:
            raise ValueError(f'unknown persona: {persona}')
        self.persona = persona
        self.calls = 0

    def _response(self, request, decisions):
        self.calls += 1
        silent = self.persona in ('abstain', 'unavailable')
        return {'schema': 'daodan/routing/v1',
                'implementation': {'name': 'mock-router', 'version': self.persona},
                'input_digest': digest(request), 'status': self.persona if silent else 'ok',
                'gaps': [], 'decision_id': f'route-{digest(request)[:12]}-{self.calls}',
                'decisions': [] if silent else decisions}

    def _accurate(self, node):
        if node['op'] == 'REVIEW_LENS' and node['role'] in CRITICAL_ROLES:
            return 'tier2'
        return ACCURATE.get(node['op'], 'tier1')

    def route(self, request):
        return self._response(request, [
            {'node': n['id'], 'tier': FIXED.get(self.persona) or self._accurate(n), 'effort': 'medium'}
            for n in request['nodes']])

    def escalate(self, request):
        """Propose one tier above the current one; greedy jumps to the top tier."""
        current = TIERS.index(request['escalation']['current_tier'])
        up = TIERS[-1] if self.persona == 'greedy' else TIERS[min(current + 1, len(TIERS) - 1)]
        return self._response(request, [{'node': n['id'], 'tier': up, 'effort': 'high'}
                                        for n in request['nodes']])
