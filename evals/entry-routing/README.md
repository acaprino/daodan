# Entry-routing activation eval

Development asset for `docs/specs/2026-10-28-chat-entry-routing-design.md`,
section S-6. Not shipped, not registered in `marketplace.json`.

This directory builds and validates the eval harness and its fixed case set.
It does **not** run the measured eval: launching headless sessions against a
disposable Claude configuration, with and without the routing hooks, is a
later, separately authorized step (closing gate G-2), carried out by the
coordinator against a disposable configuration, never the user's own
installation.

## Case set (`cases.json`)

A JSON array of exactly 65 objects, each:

```json
{
  "id": "task-007",
  "lang": "it",
  "prompt": "c'è un bug nel login, risolviamolo",
  "kind": "task",
  "expected_entry": "/daodan:fix-bug"
}
```

- `id`: unique string.
- `lang`: `"it"` or `"en"`.
- `prompt`: the text sent to the model.
- `kind`: `"task"` (a core `daodan` workflow), `"vertical"` or `"keyword"`
  (a vertical plugin workflow or a keyword-routed knowledge target), or
  `"non-task"` (must not start any workflow).
- `expected_entry`: the entry identity expected to be invoked first (a
  `/plugin:workflow` command, or a `plugin:target` identity for a keyword
  target that has no slash command), or `null` for a `"non-task"` case.

The split is fixed at 40 `"task"` / 10 `"vertical"`+`"keyword"` / 15
`"non-task"`, matching S-6. The spec's own worked examples (EX-1 to EX-6) are
included verbatim.

## Commands

```bash
python evals/entry-routing/run_eval.py --check
```

Loads `cases.json` and validates its schema: exactly 65 objects matching the
shape above, the 40/10/15 split, every `id` unique, every non-`"non-task"`
case carrying a non-null `expected_entry`, every `"non-task"` case carrying a
null one. Exits 0 on success, nonzero with a message naming the problem
otherwise. Calls no model and makes no network request.

```bash
python evals/entry-routing/run_eval.py --verify-results results.json
```

Loads a results file produced by the later measured-eval step:

```json
{
  "with_hooks": {"task-007": "/daodan:fix-bug", "nontask-001": null},
  "without_hooks": {"task-007": null, "nontask-001": null}
}
```

and reports the S-6 targets: with the hooks, at least 85% of
`"task"`/`"vertical"`/`"keyword"` cases invoke their expected entry first, at
most 10% of `"non-task"` cases invoke any entry, and both figures improve on
the run without the hooks. This is read-only scoring tooling; it does not
launch any session itself.

Both commands accept `--cases PATH` to point at a different case file (used
by the test suite's fixtures; the default is `cases.json` beside this
script).

## Tests

`tests/test_entry_routing_eval.py` (repository root) covers `run_eval.py`'s
own logic: schema validation on the shipped `cases.json` and on synthetic
defective fixtures, and the `--verify-results` scoring arithmetic on small
synthetic results, both the pass and the fail case.
