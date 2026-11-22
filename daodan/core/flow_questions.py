"""Bounded questions on the still-unclassified forms of a snapshot."""
from __future__ import annotations

import hashlib
import json

import entries
from system_brief import LIMIT


def page(manifest, rules, offset, limit, *, budget=LIMIT - 256):
    rows = entries.shape_questions(entries.cached_syntax(manifest), rules)
    # A row number is only meaningful in the inventory the model actually saw.
    identity = hashlib.sha256(json.dumps(rows, ensure_ascii=True, sort_keys=True).encode()).hexdigest()
    shown = []
    answer = {"id": identity, "offset": offset, "count": len(rows), "next_offset": None,
              "allowed": [*entries.ENTRY_KINDS, entries.NO_ENTRY], "questions": shown,
              "prompt": "Classify the numbered shapes with shape_answers={id,answers:{row:kind}}."}
    size = len(json.dumps(answer)) + 128
    for row in rows[offset:offset + limit]:
        # Keep the identifier bound to the full row even if its display text is shortened.
        width = 600
        while True:
            visible = {**row, "shape": row["shape"][:width],
                       "example": {k: v[:width] if isinstance(v, str) else v for k, v in row["example"].items()}}
            length = len(json.dumps(visible)) + 2
            if shown or size + length <= budget or width == 0:
                break
            width //= 2
        if shown and size + length > budget:
            break
        shown.append(visible)
        size += length
    if offset + len(shown) < len(rows):
        answer["next_offset"] = offset + len(shown)
    return answer, rows


def answered(manifest, rules, decision):
    if not isinstance(decision, dict) or set(decision) != {"id", "answers"}:
        raise ValueError("shape_answers must contain a question id and answers by row")
    question, rows = page(manifest, rules, 0, 1)
    if decision["id"] != question["id"]:
        raise ValueError("shape question changed; read shape_offset=0 again")
    if not isinstance(decision["answers"], dict) or not 1 <= len(decision["answers"]) <= 1000:
        raise ValueError("give one to 1000 answers to numbered shapes")
    return entries.shape_rules(rows, decision["answers"])


class Review:
    """One closed question per independent engine turn. Decisions and evidence belong to the run store."""

    def __init__(self, service, run):
        self.service, self.run = service, run
        self.current = None
        self.shape = None
        self.shapes_done = False
        self.counts = {}

    def prompt(self, *, forms=None, queue=None):
        previous = self.current
        if not self.shapes_done:
            if forms is None:
                forms = self.service.flows(self.run, shape_offset=0, limit=1)
            if "questions" not in forms:
                raise ValueError(forms.get("reason", "entry forms unavailable"))
            if forms["questions"]:
                row = forms["questions"][0]
                self.shape = (forms["id"], str(row["row"]))
                self.current = f"shape:{forms['id']}:{row['row']}"
                self.counts = {"remaining_shapes": forms["count"]}
                if previous == self.current:
                    raise ValueError("entry form still unanswered")
                return (f"Run {self.run}. Classify this code shape. Its example is evidence from the snapshot.\n"
                        f"{json.dumps(row, ensure_ascii=False)}\nAllowed answers: {', '.join(forms['allowed'])}. "
                        'Which kind of entry does this shape declare? Answer only with {"kind":"..."}.')

            self.shape = None
            self.shapes_done = True
        if queue is None:
            queue = self.service.flows(self.run, next_question=True)
        if queue.get("status") not in ("pending", "complete"):
            raise ValueError(queue.get("reason", "entry evidence unavailable"))
        self.counts = {k: queue[k] for k in ("count", "remaining", "reviewed")}
        if "effect_coverage" in queue:
            self.counts["effect_coverage"] = queue["effect_coverage"]
        self.current = queue["question"]["card_id"] if queue.get("question") else None
        if self.current is None:
            return None
        if self.current == previous:
            raise ValueError("the current entry is still unanswered")
        import system_map
        evidence = self.service.flows(self.run, trace_id=self.current, limit=12)
        return (f"Run {self.run}. Each numbered step belongs to this event's snapshot. "
                "A lacuna is where the proof stops. Follow the direction from the handler to an effect. "
                f"Use trace_id={self.current} and trace_offset=next_offset for more steps if needed. "
                f"Areas: {', '.join(system_map.AREAS)}. Types: {', '.join(system_map.FLOW_TYPES)}.\n"
                f"{json.dumps(evidence, ensure_ascii=False)}\n"
                "What behavior is proved? Return one JSON object with name, area, types, steps (numbers) and data "
                "(one short label per step). If proof stops, return disposition: unresolved and reason. "
                "Use disposition: excluded with a reason for a non-entry.")

    def advance(self, outcome):
        if self.current is None:
            return None
        try:
            decision = json.loads(outcome.get("text") or "")
        except ValueError:
            decision = None
        if isinstance(decision, dict):
            if self.shape:
                question_id, row = self.shape
                # The tool-capable engine can write its answer before it returns
                # the same JSON. Only apply the text to the still-open question.
                forms = self.service.flows(self.run, shape_offset=0, limit=1)
                if forms.get("id") != question_id:
                    return self.prompt(forms=forms)
                self.service.flows(self.run, shape_offset=0, limit=1,
                                   shape_answers={"id": question_id, "answers": {row: decision.get("kind")}})
            else:
                queue = self.service.flows(self.run, next_question=True)
                if (queue.get("question") or {}).get("card_id") != self.current:
                    return self.prompt(queue=queue)
                result = self.service.flows(self.run, trace_decision={**decision, "card_id": self.current})
                if result["status"] not in ("accepted", "excluded", "unresolved"):
                    raise ValueError(result.get("reason", "entry decision refused"))
        # A tool-capable model may already have recorded the decision in this turn.
        return self.prompt()
