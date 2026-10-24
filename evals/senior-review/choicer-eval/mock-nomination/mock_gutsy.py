"""Deterministic, offline mock of the Gutsy nomination tool.

Interface: ``decide(state, questions)`` returns
``{"answers": {qid: {"type": "noul", "probabilities": {"true": p, "false": 1-p},
"noul": p}}, "decisions": [...]}``, compatible with the contract gate in
``all_reviewers_eval.decode_answers`` (replicated in nomination_policy).

Gold labels never enter through ``state``/``questions``. The ``oracle`` and
``gold-replay`` registries are constructor fixtures of the scripted mock: the
caller passes only a ``case_id`` inside ``state``; the expected set / saved
probabilities live inside the mock, exactly as a recorded fixture would.
Every answer records decision_id, state digest, qid and runtime identity.
Standard library only.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import time

RUNTIME_IDENTITY = "mock-gutsy/v1"
MODES = ("gold-replay", "oracle", "threshold-edge", "abstain", "failure")


class MockGutsyFailure(RuntimeError):
    """Scripted failure mode; callers must treat it as missing, not negative."""


def state_digest(state) -> str:
    blob = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _answer(p_true: float) -> dict:
    p = float(p_true)
    return {
        "type": "noul",
        "probabilities": {"true": p, "false": 1.0 - p},
        "noul": p,
    }


class MockGutsy:
    def __init__(
        self,
        mode: str = "oracle",
        *,
        saved_probs: dict | None = None,
        expected_by_case: dict | None = None,
        clock=None,
        counter=None,
    ):
        if mode not in MODES:
            raise ValueError(f"unknown mock mode: {mode!r} (expected {MODES})")
        self.mode = mode
        self.saved_probs = saved_probs or {}
        self.expected_by_case = expected_by_case or {}
        self.clock = clock or time.time
        # Callers fusing decisions from several instances into one artifact
        # pass one shared counter so decision_id stays unique across the
        # whole aggregate; a lone instance keeps its own counter.
        self._counter = counter if counter is not None else itertools.count(1)

    # -- internals ---------------------------------------------------------
    def _case_id(self, state) -> str | None:
        if isinstance(state, dict):
            return state.get("case_id") or state.get("id")
        return None

    def _record(self, state, qid: str) -> dict:
        return {
            "decision_id": f"mock-{next(self._counter):06d}",
            "state_digest": state_digest(state),
            "qid": qid,
            "runtime_identity": RUNTIME_IDENTITY,
            "mode": self.mode,
            "recorded_at": self.clock(),
        }

    # -- main entry --------------------------------------------------------
    def decide(self, state, questions: dict) -> dict:
        if self.mode == "failure":
            raise MockGutsyFailure("scripted mock failure (mode=failure)")
        if not isinstance(questions, dict) or not questions:
            raise ValueError("questions must be a non-empty mapping")
        qids = sorted(questions)
        case_id = self._case_id(state)
        answers: dict = {}
        decisions: list[dict] = []

        if self.mode == "gold-replay":
            probs = self.saved_probs.get(case_id or "", {})
            if not isinstance(probs, dict):
                probs = {}
            for qid in qids:
                decisions.append(self._record(state, qid))
                if qid not in probs:
                    # A missing saved probability is unknown, not a negative
                    # vote: omit the answer so the policy records ABSTAIN.
                    continue
                answers[qid] = _answer(probs[qid])
        elif self.mode == "oracle":
            expected = set(self.expected_by_case.get(case_id or "", ()))
            for qid in qids:
                answers[qid] = _answer(1.0 if qid in expected else 0.0)
                decisions.append(self._record(state, qid))
        elif self.mode == "threshold-edge":
            edge = (0.499, 0.5, 0.501)
            for i, qid in enumerate(qids):
                answers[qid] = _answer(edge[i % len(edge)])
                decisions.append(self._record(state, qid))
        elif self.mode == "abstain":
            for i, qid in enumerate(qids):
                decisions.append(self._record(state, qid))
                variant = i % 4
                if variant == 0:
                    continue  # missing option: qid omitted entirely
                if variant == 1:
                    ans = _answer(0.9)
                    ans["choice"] = "Z"  # Z: explicit abstention marker
                    answers[qid] = ans
                elif variant == 2:
                    answers[qid] = {  # malformed probabilities (sum != 1)
                        "type": "noul",
                        "probabilities": {"true": 0.7, "false": 0.7},
                        "noul": 0.7,
                    }
                else:
                    answers[qid] = {  # missing false probability
                        "type": "noul",
                        "probabilities": {"true": 0.9},
                        "noul": 0.9,
                    }
        return {"answers": answers, "decisions": decisions}


def decide(state, questions, *, mode: str = "oracle", **kwargs) -> dict:
    """Functional shortcut: ``decide(state, questions)`` per the contract."""
    return MockGutsy(mode, **kwargs).decide(state, questions)
