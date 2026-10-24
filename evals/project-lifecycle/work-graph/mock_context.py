"""Deterministic mocks of the codebase mapper (I1) and of the specs writer (I2).

Fixtures follow the Phazly search example of spec section 1.0: a React search
bar and a Python search endpoint linked by a declared contract.
"""
from __future__ import annotations

from interfaces import digest


def _envelope(schema, name, request, status):
    return {'schema': schema, 'implementation': {'name': name, 'version': '1'},
            'input_digest': digest(request), 'status': status, 'gaps': []}


def map_slice(request, freshness='fresh', status='ok'):
    response = _envelope('daodan/map-slice/v1', 'mock-mapper', request, status)
    if status != 'ok':
        return response
    response.update(
        snapshot={'run_id': 'map-fixture', 'digest': digest(request['targets']),
                  'freshness': freshness},
        components=[{'id': 'react-app', 'paths': ['react-app/src/components/SearchBar.tsx']},
                    {'id': 'functions-python', 'paths': ['functions-python/search.py']}],
        edges=[{'from': 'react-app', 'to': 'functions-python', 'kind': 'contract',
                'evidence': 'react-app/src/api/search.ts:12'}],
        gaps=['dynamic import in react-app/src/routes.tsx not resolved'])
    return response


def approved_spec(request, status='approved', open_questions=(), state='ok'):
    response = _envelope('daodan/approved-spec/v1', 'mock-specs-writer', request, state)
    if state != 'ok':
        return response
    response.update(
        spec={'id': 'SPEC-search', 'path': 'docs/adr/0042-search.md', 'digest': digest(request),
              'status': status},
        adr_refs=[{'id': 'ADR-0042', 'status': 'Proposed'}],
        requirements=[
            {'id': 'R1', 'text': 'The search bar shows the results of /search', 'kind': 'behavior',
             'oracle': {'type': 'test', 'ref': 'react-app/src/components/SearchBar.test.tsx'}},
            {'id': 'R2', 'text': '/search returns ranked matches', 'kind': 'behavior',
             'oracle': {'type': 'test', 'ref': 'functions-python/test_search.py'}}],
        scope={'in': ['react-app/src/components/', 'functions-python/'], 'out': ['admin-app/']},
        contracts=[{'id': 'C1', 'producer': 'R2', 'consumers': ['R1'], 'artifact': 'contract:/search'}],
        open_questions=list(open_questions), authorizations=['fix'])
    return response
