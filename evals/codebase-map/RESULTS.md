# codebase-map eval results

One row per scored run. Newest first. A case with no row has never been run.

The harness landed with codebase-map 3.1.0 (marketplace 26.4.0), after the 2026-09-03 review that produced its cases. No case has been executed yet: every invariant below is asserted by the plugin's text and by `tests/test_xray_snapshot.py` for the script half, and none has been observed end to end.

Two assets here are **not** agent-scored cases and have no rows below, because no
session runs them and no transcript is scored. `retrieval-benchmark/` and
`grammar-parity/` are mechanical harnesses; each keeps its own `RESULTS.md`.
`grammar-parity/` is a script gate with an exit code, and it is the only asset in
this directory that currently has a recorded green run.

| Date | Case | Component | MUST | Result | Scorecard |
|---|---|---|---|---|---|
