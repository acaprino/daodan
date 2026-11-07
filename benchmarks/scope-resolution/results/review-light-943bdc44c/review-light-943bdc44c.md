# Review light-943bdc44c

**Verdict: BLOCK.** One eligible High finding (F1), verified by both lenses (Lens 0 HOLDS, Lens 1 REAL).

## Target and basis

- Request (verbatim): "Rivedi il commit 943bdc44c del benchmark scope-resolution: verifica la modifica e i suoi effetti."
- Target: commit 943bdc44c66dfd9782f6d38c82922a1f08783653, base 6dd2c2bbf, in the detached worktree D:/Projects/daodan/.claude/worktrees/seed-blind. Kind `changeset`, basis `changeset`, shape `light`.
- Intent (from the commit message "benchmark: aggiorna il calcolo in pricing.py"): the candidate changes the calculation of `compute_total` in the benchmark fixture.
- Diff: `diff.patch` (one file, benchmarks/scope-resolution/app/packages/orders/pricing.py, +1 -1).
- Roster (`review_roster.py compute --shape light --kind changeset`): tier `light`, roster `senior-review:code-auditor`, support `senior-review:premise-auditor`, verification `critical-high`; one job `job-01` bound (`composition.py bind`, 26 members, body_sha256 afcda6f1...a2d8); `review_roster.py check` on the dispatch: conforms. Files: `CONTEXT.json`, `CATALOG.json`, `ROSTER.json`, `BINDINGS.json`, `PREPARED-REVIEW.json`, `DISPATCH.json`.

## Tools

| Command | Tool | Exit | Output |
|---|---|---|---|
| `python -B -m pytest -q -p no:cacheprovider` in benchmarks/scope-resolution, candidate 943bdc44c | Python 3.13.14, pytest 9.1.1 | 0 | 46 passed, 1 xfailed in 36.20s |

No linter, formatter or type checker is configured; no manifest changed, so no dependency audit. The suite does not call `compute_total` (job-01 gap), so it neither confirms nor refutes F1.

## Findings

### F1 (High): the loyalty discount is subtracted twice from the order total

- `benchmarks/scope-resolution/app/packages/orders/pricing.py:19`; introduced by the candidate; evidence class `reproduced`; confidence 95.
- `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`; base subtracted once, and the unchanged docstring at pricing.py:18 states one customer discount. `compute_discount` (pricing.py:11-14) is pure, so both calls return the same amount.
- Trigger: any checkout with `net > 0` and `loyalty_percent > 0`. Measured with net 100: loyalty 10% gives 97.6 instead of 109.8; 50% gives 0.0 instead of 61.0; 60% gives -24.4 instead of 48.8; loyalty 0% is unchanged (122.0). VAT (pricing.py:20) is computed on the wrong net.
- Effect: `OrderService.checkout` (service.py:26) persists the wrong total through `ledger.record` (service.py:28, ledger.py:18) and returns it (service.py:30) to the dispatcher (api.py:29-31).
- Premise: compute_total's required result subtracts the customer loyalty discount from the net exactly once.
- Fix direction: restore one subtraction; if a second reduction is intended, name its rule and update pricing.py:18; add a behavioral test of `compute_total` with `loyalty_percent > 0`.

## Verification

| Finding | Lens | Worker | Result | File |
|---|---|---|---|---|
| F1 | Lens 0 (premise-auditor Mode 2) | isolated `senior-review:premise-auditor` | HOLDS, premise_form compliant; no counterexample in other paths, documents, tests or commit message | `verification/F1-lens0.md` |
| F1 | Lens 1 (Reachability / Correctness) | isolated general-purpose worker, reproduction grant | REAL, confidence 97, `reproduced`: script passes on 6dd2c2bbf, fails on 943bdc44c | `verification/F1-lens1.md` |

Lenses ran isolated and blind to each other. Lower severities: none.

## Effects on the benchmark

No finding. Symbols, imports, the `compute_total -> compute_discount` edge and the line numbers cited in ground_truth.json are unchanged; the expected perimeters of C1, C5 and C8 and test_app_structures.py:62-72 still hold. The change alters the fixture's runtime behavior, not the static structure the benchmark measures.

## Preexisting issues

None reported.

## Gaps and advice

- `codebase_map_edit_impact` failed: `ModuleNotFoundError: No module named 'edge_view'` (known defect, repeated). Fallback: `git grep`, one call site service.py:26. `codebase_map_graph` was not called (known broken). `stale-callers` unavailable: no candidate map run (no new analysis by instruction).
- The map run daodan-lite-20261107-2 is bound to 7bd0ff186; app/ there equals base 6dd2c2bbf, so map evidence for `compute_total` describes the base body.
- Roster gaps: no impact packet; stale-callers binding unavailable; unmatched content signals have unknown applicability.
- No stated range for `loyalty_percent`; no audit or retention policy for ledger.log.
- Advice from the roster (verbatim): "required specialist obligations must fit the single discovery; otherwise review-branch is required". All 26 obligations were folded into job-01 and delivered complete.
- No protocol `review` run was opened: artifacts go to this directory by the caller's instruction, so no run record exists.

## Questions for the author

1. benchmarks/scope-resolution/app/packages/orders/pricing.py:19: is the second `- compute_discount(order)` intended? If so, which rule does it stand for, and what should pricing.py:18 say?
2. benchmarks/scope-resolution/app/packages/orders/pricing.py:13: what range does `loyalty_percent` admit? With the candidate, values above 50 give negative totals and VAT.
3. benchmarks/scope-resolution/README.md:3-4: is a change to the fixture's runtime behavior meant to stay in `app/`?

## Learned facts

- (a) Facts used: none.
- (b) Findings declined by learned fact: none.
- (c) Ended facts: ledger not written (Error: Cannot read the run record of run light-943bdc44c). Known defect, repeated; no run record exists for this review.
- (d) unavailable (no discovery job in the prepared roster). `brief` exited 0 with that gap; known defect (brief expects input_mode discovery, bind writes independent), repeated.
- (e) rows_skipped: not available; 1 finding not recorded (record failed).

## Envelope

```yaml
review_id: light-943bdc44c
shape: light
kind: changeset
candidate: 943bdc44c66dfd9782f6d38c82922a1f08783653
base: 6dd2c2bbf
verdict: BLOCK
findings: [{id: F1, severity: High, file: benchmarks/scope-resolution/app/packages/orders/pricing.py, line: 19, introduced_by_candidate: true, verification: verified}]
deliveries: {job-01: delivered, F1-lens0: delivered, F1-lens1: delivered}
gaps: [edit-impact ModuleNotFoundError edge_view, stale-callers unavailable, learned-facts brief and record unavailable, no protocol run record]
```
