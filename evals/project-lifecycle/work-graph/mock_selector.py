"""Deterministic mock of the reviewer selector (I3) and of the light gate.

No model, no HTTP. MockSelector answers a daodan/selection/v1 request from
keyword signals in the hunks; its personas exercise golden, leaky, uncited,
noisy and unavailable answers. LightLlmGate stands in for the ultra-light
model that blocks only when a critical lens with a real trigger is missing
from the applied roles.
"""
from __future__ import annotations

from interfaces import digest
from policy import CRITICAL_ROLES

THRESHOLD = 0.40
SECURITY = 'senior-review:security-auditor'

# Signals mapping hunk text to reviewer lenses with fixed deterministic scores.
SIGNAL_RULES = [
    (('permission', 'auth', 'token', 'session'), SECURITY, 0.83),
    (('INSERT', 'UPDATE', 'DELETE', 'balance', 'payment', 'transaction'),
     'senior-review:data-integrity-auditor', 0.79),
    (('discount >=', '>= 0', 'credit note', 'boundary'), 'senior-review:premise-auditor', 0.71),
    (('retry', 'timeout', 'backoff', 'setTimeout'), 'senior-review:temporal-resilience-auditor', 0.66),
    (('useEffect', 'render', '.tsx'), 'senior-review:ui-race-auditor', 0.61),
    (('status', 'transition', 'state'), 'senior-review:logic-integrity-auditor', 0.58),
    (('queue', 'webhook', 'publish'), 'senior-review:distributed-flow-auditor', 0.64),
]


def signals_for(hunks):
    """Return {role: (score, hunk_id, signal)} from the hunk text."""
    found = {}
    for hunk in hunks:
        low = (hunk['path'] + '\n' + hunk['text']).lower()
        for keywords, role, score in SIGNAL_RULES:
            for kw in keywords:
                if kw.lower() in low and role not in found:
                    found[role] = (score, hunk['id'], kw)
    return found


class MockSelector:
    PERSONAS = ('accurate', 'leaky', 'uncited', 'noisy', 'unavailable')

    def __init__(self, persona='accurate'):
        if persona not in self.PERSONAS:
            raise ValueError(f'unknown persona: {persona}')
        self.persona = persona
        self.calls = 0

    def select(self, request, rep=False):
        """Answer one I3 request; rep marks the single re-preparation after a gate block."""
        self.calls += 1
        response = {'schema': 'daodan/selection/v1',
                    'implementation': {'name': 'mock-selector', 'version': self.persona},
                    'input_digest': digest(request), 'status': 'ok', 'gaps': [],
                    'decision_id': f'sel-{digest(request)[:12]}-{self.calls}', 'decisions': []}
        if self.persona == 'unavailable':
            response['status'] = 'unavailable'
            return response
        signals = signals_for(request['hunks'])
        first = request['hunks'][0]['id']
        for role in request['catalog']['roles']:
            score, hunk, _ = signals.get(role, (0.05, None, None))
            selected = hunk is not None
            if role == SECURITY and not rep and self.persona == 'leaky':
                selected, score, hunk = False, 0.1, None
            if role == SECURITY and not rep and self.persona == 'uncited':
                hunk = None
            if self.persona == 'noisy' and not selected:
                selected, score, hunk = True, 0.45, first
            response['decisions'].append({'role': role, 'selected': selected,
                                          'probability': score, 'citation': hunk})
        return response


class LightLlmGate:
    """Blocking gate: BLOCK only when a critical lens has a real trigger
    (score >= THRESHOLD) in the hunks but is absent from the applied roles."""

    def __init__(self):
        self.checks = 0

    def check(self, roles, hunks):
        self.checks += 1
        missing = sorted(role for role, (score, _, _) in signals_for(hunks).items()
                         if role in CRITICAL_ROLES and score >= THRESHOLD and role not in roles)
        if missing:
            return {'status': 'BLOCK', 'risk': 'high', 'missing': missing}
        return {'status': 'PASS', 'missing': []}
