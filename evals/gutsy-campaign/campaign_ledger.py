"""Durable, hash-bound request accounting; no inference or network dependencies."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import time

MODEL = 'gutsy-0.8b-v04-q4'
MAX_QUESTIONS = 50000
MAX_SECONDS = 22 * 3600


def encoded(value):
    # Gutsy assigns option letters and renders state in insertion order. Sorting
    # keys would erase order perturbations and change the actual model input.
    return json.dumps(value, ensure_ascii=False, sort_keys=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('wb') as target:
        target.write(encoded(value) + b'\n')
        target.flush()
        os.fsync(target.fileno())
    temporary.replace(path)


def bounded(value):
    return (not isinstance(value, bool) and isinstance(value, (float, int))
            and math.isfinite(value) and 0 <= value <= 1)


def validate_response(body, response):
    if not isinstance(response, dict) or response.get('model') != MODEL:
        raise ValueError('Answering model differs from frozen Q4 identity')
    answers = response.get('answers')
    if not isinstance(answers, dict) or set(answers) != set(body['questions']):
        raise ValueError('Response question identities differ')
    for key, question in body['questions'].items():
        answer = answers[key]
        if not isinstance(answer, dict):
            raise ValueError(f'Invalid answer object: {key}')
        if answer.get('type') != question['type']:
            raise ValueError(f'Answer type differs from question: {key}')
        if question['type'] == 'noul':
            if not bounded(answer.get('noul')):
                raise ValueError(f'Invalid noul probability: {key}')
        elif question['type'] == 'choice':
            probabilities = answer.get('probabilities', {})
            expected = set(question['criteria'])
            if (set(probabilities) != expected or
                    not all(bounded(p) for p in probabilities.values()) or
                    abs(sum(probabilities.values()) - 1) > 1e-4 or
                    answer.get('choice') not in expected or
                    not bounded(answer.get('reject'))):
                raise ValueError(f'Invalid choice distribution: {key}')
        else:
            raise ValueError(f'Unsupported question type: {question["type"]}')


def validate_requests(requests):
    ids = set()
    for request in requests:
        key = request['id']
        if not isinstance(key, str) or not key.isalnum() or key in ids:
            raise ValueError('Request IDs must be unique opaque alphanumeric strings')
        ids.add(key)
        body = request['body']
        if set(body) != {'model', 'state', 'questions'} or body['model'] != MODEL:
            raise ValueError('Only model, state and questions enter inference')
        questions = body['questions']
        if not isinstance(questions, dict) or not 0 < len(questions) <= 64:
            raise ValueError('Each request needs 1..64 questions')
        if len(encoded(body)) > 8 * 2**20:
            raise ValueError('Request exceeds official server body limit')
    count = sum(len(r['body']['questions']) for r in requests)
    if count > MAX_QUESTIONS:
        raise ValueError('Expanded manifest exceeds question budget')
    return count


class Ledger:
    def __init__(self, directory: Path, input_hash: str, code_hash: str,
                 commit=lambda: None, clock=time.time, budget_origin=None,
                 carried_questions=0, budget_parent=None):
        self.directory, self.commit, self.clock = directory, commit, clock
        self.write_seconds = 0.0
        self.write_count = 0
        self.path = directory / 'ledger.json'
        if (isinstance(carried_questions, bool) or not isinstance(carried_questions, int)
                or not 0 <= carried_questions <= MAX_QUESTIONS):
            raise ValueError('Invalid inherited question accounting')
        if budget_origin is not None and (not math.isfinite(budget_origin)
                                           or not 0 < budget_origin <= clock()):
            raise ValueError('Invalid inherited global start time')
        directory.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding='utf-8'))
            if (self.state['input_hash'], self.state['code_hash']) != (input_hash, code_hash):
                raise ValueError('Resume refuses changed input or executor')
            if (self.state.get('carried_questions', 0) != carried_questions or
                    self.state.get('budget_parent') != budget_parent or
                    (budget_origin is not None and self.state['started_at'] != budget_origin)):
                raise ValueError('Resume refuses changed inherited authorization budget')
        else:
            self.state = {'schema': 'gutsy-campaign-ledger/v1',
                          'input_hash': input_hash, 'code_hash': code_hash,
                          'started_at': clock() if budget_origin is None else budget_origin,
                          'carried_questions': carried_questions, 'budget_parent': budget_parent,
                          'attempted_questions': 0,
                          'startup_question_reserve': 0, 'requests': {},
                          'completed_requests': 0,
                          'complete': False, 'status': 'preparing'}
            self.save()

    def save(self):
        started = time.monotonic()
        atomic_json(self.path, self.state)
        self.commit()
        self.write_seconds += time.monotonic() - started
        self.write_count += 1

    def elapsed(self):
        return max(0, self.clock() - self.state['started_at'])

    def check_budget(self, questions=0):
        if self.elapsed() >= MAX_SECONDS:
            raise TimeoutError('Persistent global deadline reached')
        if (self.state['attempted_questions'] + self.state['startup_question_reserve']
                + self.state.get('carried_questions', 0) + questions > MAX_QUESTIONS):
            raise RuntimeError('Persistent question budget reached')

    def reserve_startup(self, questions):
        self.check_budget(questions)
        self.state['startup_question_reserve'] += questions
        self.save()

    def record_path(self, key):
        if not isinstance(key, str) or not key.isalnum():
            raise ValueError('Unsafe record identifier')
        return self.directory / 'records' / (key + '.json')

    def existing(self, request):
        key, request_hash = request['id'], digest(request)
        previous = self.state['requests'].get(key)
        if previous and previous['request_hash'] != request_hash:
            raise ValueError('Changed request under an existing identity')
        path = self.record_path(key)
        if path.exists():
            record = json.loads(path.read_text(encoding='utf-8'))
            if record.get('request_hash') != request_hash:
                raise ValueError('Saved response provenance mismatch')
            if record.get('status') == 'delivered':
                validate_response(request['body'], record.get('response'))
            elif record.get('status') not in {'failed', 'input_limit', 'skipped_inapplicable'}:
                raise ValueError('Invalid saved terminal record')
            if previous:
                # Immutable record files are the completed index. Keep only
                # active attempts in the small ledger, avoiding an O(N^2)
                # rewrite of every previous result on a long campaign.
                del self.state['requests'][key]
                self.state['completed_requests'] += 1
                self.save()
            return record
        if not previous:
            return None
        if previous['status'] in {'running', 'unknown'}:
            previous['status'] = 'unknown'
            self.state['status'] = 'unresolved_request'
            self.save()
            raise RuntimeError(f'Unresolved inference {key}; reconcile before resubmitting')
        raise ValueError('Terminal ledger entry has no response artifact')

    def begin(self, request):
        if self.existing(request) is not None:
            raise ValueError('Cannot begin an already completed request')
        count = len(request['body']['questions'])
        self.check_budget(count)
        self.state['attempted_questions'] += count
        self.state['requests'][request['id']] = {
            'request_hash': digest(request), 'status': 'running',
            'started_at': self.clock(), 'questions': count}
        self.state['status'] = 'running'
        self.save()  # Durable before the request can leave the worker.

    def finish(self, request, record):
        key = request['id']
        entry = self.state['requests'].get(key)
        if not entry or entry['status'] != 'running':
            raise ValueError('No admitted running attempt')
        if record['status'] == 'delivered':
            validate_response(request['body'], record['response'])
        elif record['status'] != 'failed':
            raise ValueError('Invalid inference terminal state')
        complete = {**record, 'id': key, 'request_hash': digest(request)}
        target = self.record_path(key)
        if target.exists():
            raise FileExistsError('Never overwrite response evidence')
        atomic_json(target, complete)
        del self.state['requests'][key]
        self.state['completed_requests'] += 1
        self.save()
        return complete

    def input_limit(self, request, token_info):
        if self.existing(request) is not None:
            raise ValueError('Cannot replace an existing request')
        record = {'id': request['id'], 'request_hash': digest(request),
                  'status': 'input_limit', 'tokens': token_info}
        atomic_json(self.record_path(request['id']), record)
        self.state['completed_requests'] += 1
        self.save()
        return record
