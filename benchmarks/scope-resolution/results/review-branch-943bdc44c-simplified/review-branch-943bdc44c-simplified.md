## Code Review Report: 6dd2c2bbf..943bdc44c

Session: `.team-review/`
Context: Codebase Map run `daodan-lite-20261107-2`, bound to an earlier revision; review object in `01-context.md`, selected reviewers in `02-selection.md`
Reviewed by: local correctness, logic integrity, artifact lifecycle (3 reviewers)
Files reviewed: 1 changed; callers and benchmark artifacts read as effects
Verification: 1 verified, 0 false positives, 0 contested, 0 premise-refuted, 0 premise-contested, 3 unverified (tier)
Tier: small. Verification level: `critical-high`. Critic: not in tier.
Protocol run record: none exists for this standalone review.

**Verdict: changes required.** The commit doubles the customer discount in the order total, and the commit states no requirement for it. Reverting line 19 removes every finding below. The fixture is not shipped software, so no real money is at stake.

### Critical (0)

### High (1)

**F1. `compute_total` subtracts the customer discount twice.** `benchmarks/scope-resolution/app/packages/orders/pricing.py:19`. Sources: `jobs/job-01.md` LC-01, `jobs/job-02.md` LI-1. Verified, evidence class `reproduced`.

- The unchanged docstring on line 18 states one discount. `compute_discount` is pure, so the effective discount is exactly twice `loyalty_percent`, and VAT is computed on the reduced net.
- Path: `api.py:37`, `api.py:31`, `api.py:27`, `service.py:26`; the value goes to the ledger at `service.py:28` and is returned at `service.py:30`. No guard, clamp or correcting path exists.
- Reproduced by Lens 1 on copies from both refs, with `net` 100 and `loyalty_percent` 10: base 109.8, candidate 97.6, in the return value and in the ledger line. Without loyalty both give 122.0, so such orders hide the defect.
- Hand-computed by the reviewers, not executed: at 50% the candidate total is 0.0, at 60% it is -24.4.
- Premises: "the contract of `compute_total` applies the customer discount exactly once"; "the required formula of `compute_total` subtracts the customer discount exactly once, and no requirement establishes a second subtraction". Provenance: independent, as declared. Lens 0: HOLDS.
- Limits: the docstring is the only statement of the rule. `register_defaults`, `Dispatcher.handle` and any producer of `loyalty_percent` have no in-tree caller, so this is reachable through the fixture's public entry point, not through an in-tree run. No in-tree path carries this total to a charge, so no wrong charge is claimed.
- Fix: restore `net = order.get("net", 0) - compute_discount(order)`, and add a value test with a non-zero loyalty. No test calls `compute_total` today, so the 11 passing tests say nothing about this line.

### Medium (2)

**AL-1. The docstring states a formula the code no longer computes.** `benchmarks/scope-resolution/app/packages/orders/pricing.py:18`. Co-located with F1, same correction. Confidence 95, derived, `unverified (tier)`. Details: `jobs/job-03.md`.

**AL-2. C4 expects `clarify`, but the fixture now favours one target.** `benchmarks/scope-resolution/ground_truth.json:67`, also `CASES.md:11`. The only visible discount defect now sits in `pricing.py`, and `run_cases.py:47` would log a changed outcome under layer `spec`, blaming the spec text for a fixture effect. Predicted, not measured. Confidence 60, derived, `unverified (tier)`. Details: `jobs/job-03.md`.

### Low (1)

**AL-3. Declared measurements are not labelled as measured on an earlier fixture.** `benchmarks/scope-resolution/README.md:39-43`, also `results/model-runs/SUMMARY.md`. `README.md:32` marks only one row that way. The numbers may be unaffected, because they are file-level. Keep frozen results unchanged. Confidence 75, derived, `unverified (tier)`. Details: `jobs/job-03.md`.

### Summary

Total findings: 4 (Critical: 0, High: 1, Medium: 2, Low: 1)
Coverage gaps: below; no `97-coverage-gaps.md`, because the critic is not in this tier
Map utilization: 1 finding cites an anchor (25%, operational)
Independent premise reconstruction: not claimable, see blindness below. Declared independent: 4 of 4.
Premise challenge: 1 of 1 selected premises attacked by Lens 0
Corroborated findings: 1 (F1), limited: both reviewers take the rule from the same docstring, and `02-selection.md` pointed at the docstrings
Echoes: 0
Pipeline time, from artifact timestamps: Phase 0-1: 5m 9s, Phase 2: 13m 16s, Phase 4b: 4m 4s, total: 18:18:21 to 18:46:56

### Coverage Gaps

- **Blindness.** The coordinator's session loaded the user's auto-memory index, which names 943bdc44c as a seeded defect, and a git status snapshot listing `results/review-light-943bdc44c`. Phase 1 chose reviewers with that in context. job-03, Lens 0 and Lens 1 declared the same exposure and did not use it as evidence. job-01 and job-02 were not asked and did not say. Weigh this if this review feeds a blind measurement.
- **Tier inputs.** No candidate snapshot exists, so `stale_callers` and the digest delta are unavailable. The helper saw 0 callers and no effects change. One caller is confirmed, below the medium threshold of 5, so that input does not move the tier. If the effects digest of `compute_total` changed, the tier would be medium, adding Lens 2, Lens 3 and verification of the Medium findings. This was not determined.
- **Map.** Exact errors are listed at the end. `edit_impact` coverage is `missing_store`, so the graph is lexical only. Callers were re-derived by text search, which cannot resolve the `importlib` dispatch in `notifications.py:13-15`. Map freshness was not verified with the diff tool.
- **Baselines missing.** Python stack baseline (former python-development methods); testing specialist. Signals: target is `.py`, and the changed function has no value test. React, TypeScript, platform, dependency and structural-entropy signals are absent.
- **Knowledge.** Explicit empty selection, based only on the session's skill listing. No catalog preparation mechanism exists, so validation is unavailable.
- **Evidence pack.** ruff check, ruff format, vulture and pytest (`test_app_structures.py`) exited 0. Missing tools: mypy, pyright, complexipy, radon. Install with `python -m pip install mypy pyright complexipy radon`.
- **Not executed.** `run_cases.py`, `test_resolver.py` and model sessions were not run on the candidate, so AL-2 and AL-3 stay unmeasured.
- **Effects outside the tree** cannot be determined: charges, receipts and reports.
- **Host mechanisms.** No run record, so snapshot validation, preflight, pending-delivery records and envelope publication are unavailable. HTML rendering is unavailable; this Markdown is authoritative.
- **Procedure.** The compact plan before dispatch exists only as the Phase 0-1 files, because no reader was available. The coordinator did not load `senior-review:defect-taxonomy`; no coordinator step needed it, and reviewers load their own sections. Lens 1 ran one `ls -la` of the output root, and it read no other file there.

Worker notes, preexisting and outside the finding scope, possibly deliberate fixture shapes: `service.py:25` ignores the `False` from `reserve_stock`; `payments/gateway.py:10,15` read an `order["total"]` that nothing sets.

### Questions for the author (2)

- `pricing.py:19`: is a doubled discount intended? The commit subject names no formula. If so, what should happen above 50%?
- `ground_truth.json:67`: must the fixture keep discount defects out of C4's path while C4 measures ambiguity?

### Workspace hygiene

**Deviation: the review left files in the work tree.** The brief forbids that. The evidence-pack command `python -B -m pytest -q -p no:cacheprovider test_app_structures.py` ran `compileall.compile_dir` at `benchmarks/scope-resolution/test_app_structures.py:17`, which writes bytecode despite `-B`. Their timestamps, 18:20:35, match that run.

They are git-ignored, so the `git status --porcelain` check the method prescribes shows nothing, before and after. The "clean work tree" statements in the workers' returns have the same limit. They were not removed, because the brief also forbids deleting there. No finding depends on them, since Lens 1 ran on copies in `scratch/`.

Manifest, under `benchmarks/scope-resolution/app/packages/`, 14 files in 3 directories:

- `orders/__pycache__/`: `__init__`, `api`, `big_module`, `inventory`, `ledger`, `notifications`, `pricing`, `reporting`, `service` (`.cpython-313.pyc`)
- `payments/__pycache__/`: `__init__`, `gateway`, `refunds` (`.cpython-313.pyc`)
- `shipping/__pycache__/`: `__init__`, `rates` (`.cpython-313.pyc`)

Lens 1 created files in `scratch/` and removed them; its manifest is in `verification/F1-lens1.md`. Tracked files are unchanged, and HEAD is still the candidate.

### Learned facts

- (a) Facts used: none.
- (b) Findings declined by a learned fact: none.
- (c) Ended facts: `ledger not written (error: Cannot read the run record of run branch-943bdc44c-simplified)`; `record` exited 1, because no run record exists.
- (d) `unavailable (no discovery job in the prepared roster)`; `brief` exited 0 with 0 facts. Cause read in source, not repaired: `review_experience.py:302` requires `input_mode == "discovery"` and a key `id`, while `composition.py:143-145` writes `job_id` with default mode `independent`. So `brief` finds no job in a roster bound by `composition.py`.
- (e) Findings not persisted: all 4, because there is no ledger write.

### Tool failures, exact text

```text
codebase_map_diff: Error: result (419.620 characters across 12.377 lines) exceeds maximum allowed tokens. Output has been saved to C:\Users\alfio\.claude\projects\D--Projects-daodan\ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931\tool-results\mcp-plugin_codebase-map_codebase-map-codebase_map_diff-1794071932378.txt.
codebase_map_edit_impact, first call: Error executing tool codebase_map_edit_impact: project lock is held by another helper; retry after that invocation finishes
codebase_map_search, first call: Error executing tool codebase_map_search: project lock is held by another helper; retry after that invocation finishes
codebase_map_search, retry: index_state stale; retrieval_stale: binding differs: sqlite_version; run codebase_map_index(run_id='daodan-lite-20261107-2')
Agent, job-01 with a name: Teammates cannot spawn other teammates — the team roster is flat. To spawn a subagent instead, omit the `name` parameter.
Bash, coordinator's own command: /usr/bin/bash: eval: line 78: unexpected EOF while looking for matching `"'
Bash, coordinator's own command: /usr/bin/bash: -c: line 75: unexpected EOF while looking for matching `''
review_experience.py brief: {"facts": 0, "gaps": ["no discovery job in the prepared roster"]}
review_experience.py record: error: Cannot read the run record of run branch-943bdc44c-simplified
```

The diff output sits under `~/.claude`, which the brief forbids reading, so it was not read. The first lock errors came from parallel calls, and `edit_impact` succeeded on retry. The search index was not repaired, as the brief requires. The failed Agent call started no worker, so job-01 ran once. The two Bash errors were quoting problems in the coordinator's own shell commands, and those commands were redone.
