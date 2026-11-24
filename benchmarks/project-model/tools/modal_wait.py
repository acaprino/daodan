"""Waits for the Modal calls a `spawn` printed: `python modal_wait.py SPAWN_OUTPUT`.

A driver of `benchmarks/project-model` starts its batches with `Function.spawn` and prints each call's id as the last
word of a line; `fetch` reads what they stored, so the workflow waits for them in between. A batch that fails is said
and does not stop the others: `fetch` then reports its fixtures as having no stored record.
"""
import sys
from pathlib import Path

import modal

LIMIT = 3 * 60 * 60  # seconds for one batch: the drivers' own limit is lower


def main(path: str) -> int:
    calls = [line.split()[-1] for line in Path(path).read_text(encoding="utf-8").splitlines()
             if line.split() and line.split()[-1].startswith("fc-")]  # a call id, text with no grammar
    failed = 0
    for number, call in enumerate(calls, 1):
        try:
            answer = modal.FunctionCall.from_id(call).get(timeout=LIMIT)
            print(f"{number}/{len(calls)} {call} done", (answer or {}).get("seconds"), flush=True)
        except Exception as error:  # noqa: BLE001 - whatever ended the batch is its message
            failed += 1
            print(f"{number}/{len(calls)} {call} FAILED {type(error).__name__}: {error}", flush=True)
    print(len(calls), "batches,", failed, "failed")
    return 0 if calls else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
