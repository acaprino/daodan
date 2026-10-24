"""Graph plan writer, review zone: build the I3 request, apply policy, expand.

The selector proposes roles; the writer applies the roster floor and the
citation rule, then expands the review zone through the compiler.
Composition of a whole plan from I1 and I2 is the next step, not here yet.
"""
from __future__ import annotations

from controller import compile_plan
from interfaces import digest, validate_selection
from policy import ROLE_CATALOG


def selection_request(candidate, hunks, roster, purpose='review'):
    return {'purpose': purpose, 'candidate': candidate,
            'hunks': [{'id': h['id'], 'path': h['path'], 'text': h['text']} for h in hunks],
            'catalog': {'digest': digest(ROLE_CATALOG), 'roles': sorted(ROLE_CATALOG)},
            'roster': roster}


def apply_selection(request, response):
    """Roster floor plus every role selected with a valid citation."""
    validate_selection(response, request)
    floor = list(request['roster']['roster'])
    decisions = response['decisions']
    cited = [d['role'] for d in decisions if d['selected'] and d['citation']]
    return {'roles': floor + [r for r in cited if r not in floor],
            'ignored': [d['role'] for d in decisions if d['selected'] and not d['citation']],
            'decision_id': response['decision_id']}


def expand_review(roles):
    """One sealed lens and one verification per applied role, joined at a barrier."""
    lenses, verifies, verdicts = [], [], []
    for role in roles:
        short = role.split(':')[-1].replace('-auditor', '')
        lenses.append({'id': f'lens-{short}', 'op': 'REVIEW_LENS', 'gate': 'fixture-lens/v1',
                       'role': role, 'produces': [f'findings:{short}']})
        verifies.append({'id': f'verify-{short}', 'op': 'VERIFY_FINDING', 'gate': 'fixture-verify/v1',
                         'role': role, 'needs': [f'lens-{short}'], 'consumes': [f'findings:{short}'],
                         'produces': [f'verdict:{short}']})
        verdicts.append(f'verdict:{short}')
    barrier = {'id': 'barrier', 'op': 'WAVE_BARRIER', 'gate': 'fixture-barrier/v1',
               'needs': [v['id'] for v in verifies], 'consumes': verdicts, 'produces': ['report']}
    return compile_plan(lenses + verifies + [barrier], 'review_only')
