# Code Review Report: commit 943bdc44c (benchmark scope-resolution, pricing.py)

**Verdict: changes requested.** The commit introduces one verified High defect: `compute_total` now subtracts the loyalty discount twice, so every order with a loyalty discount gets a lower total and lower VAT, recorded in the ledger without any error. A second, Medium consequence of the same line makes zero and negative totals reachable for loyalty discounts of 50% to 100%. Both were reproduced on the candidate and not on the base.

Request (verbatim): "Rivedi il commit 943bdc44c del benchmark scope-resolution: verifica la modifica e i suoi effetti."

```
Session: OUT/.team-review/
Context: Codebase Map run daodan-lite-20261107-2 + 4 questions in 02-selection.md
Reviewed by: correctness (senior-review:code-auditor, member local-correctness-auditor) (1 reviewer)
Files reviewed: 1 in conclusion scope (pricing.py); read scope adds service.py, ledger.py, api.py, notifications.py, inventory.py, reporting.py, payments/gateway.py, payments/refunds.py, shipping/rates.py
Verification: 2 verified, 0 false positives, 0 contested, 0 premise-refuted, 0 premise-contested
```

`OUT` = `D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/review-branch-943bdc44c`. Shape `branch`, variant `team-review` (no PR), kind `changeset`, basis `changeset`. Base 6dd2c2bbf, candidate 943bdc44c66dfd9782f6d38c82922a1f08783653, diff `OUT/diff.patch` (1 file, +1/-1). Intent: changes the order-total calculation in `compute_total`; the reason is unknown (`intent: unknown`).

## Protocol envelope

No protocol run record exists for this standalone review. The host run-record mechanism is absent, so preflight, snapshot validation through a run record, the append to the run's `reviews`, and publication of the envelope are unavailable. The envelope below is the native record only.

```yaml
final_report:            # contracts/final-report.toml
  output_path: OUT/review-branch-943bdc44c.md
  retained_findings:
    - {id: J01-F1, severity: High, file: benchmarks/scope-resolution/app/packages/orders/pricing.py, line: 19, flag: verified, evidence_class: reproduced, introduced_by_candidate: true, source: job-01/senior-review:local-correctness-auditor}
    - {id: J01-F2, severity: Medium, file: benchmarks/scope-resolution/app/packages/orders/pricing.py, line: 19, flag: verified, evidence_class: reproduced, introduced_by_candidate: true (50<=p<=100), source: job-01/senior-review:local-correctness-auditor}
  filtered_findings: []          # 0 filtered, 0 premise-refuted, 0 unverified (cost-guard)
  coverage:
    roster: {id: branch-943bdc44c, tier: small, roster: [senior-review:code-auditor], support: [senior-review:premise-auditor], verification: high-and-above, critic: false}
    questions: {Q1: answered (J01-F1), Q2: answered (J01-F1), Q3: answered (J01-F2), Q4: answered (no finding; out-of-tree consumers unknown)}
    members: 26/26 accounted (1 complete, 25 not-applicable per 02-selection.md)
  degraded_dimensions:
    - logic-integrity: applicable to Q1/Q4, outside the computed roster (selection gap, not dispatched)
    - python stack baseline: missing in the catalog
    - testing: unavailable in the two-owner base
    - completeness critic: not in tier (skipped, optional)
  knowledge_coverage:
    selection: OUT/knowledge/selection.json (fingerprint af96a6fdd282cd2ad38586a7a9c30fafbe748ec8f0df4238c5dbd5cf0a38a97c)
    selected: [senior-review:defect-taxonomy -> job-01 (correctness, security)]
    usage: job-01 loaded SKILL.md, SKILL.toml, references/review-frameworks.md, references/logic-types.md; hashes equal the selection
    gaps: [canonical catalog validation unavailable (no host catalog mechanism); host skills without daodan metadata unclassified]
delivery_ledger:         # contracts/delivery-ledger.toml
  expected: 1 discovery job + 8 lens checks
  delivered: 9
  failed: 0
  barrier_satisfied: true
  jobs: [{job_id: job-01, role: senior-review:code-auditor, worker: general-purpose, body_sha256: afcda6f14b8471f3..., output: OUT/jobs/job-01.md, status: delivered}]
  checks: [J01-F1 lens0..3, J01-F2 lens0..3 -> OUT/verification/<finding>-lens<n>.md, all delivered]
```

## Critical (0)

## High (1)

**J01-F1: `compute_total` subtracts the loyalty discount twice.** `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` @943bdc44c. Category: local correctness, CWE-682 (incorrect calculation). Co-located with J01-F2.
- The candidate line is `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`. The unchanged docstring at `:18` states "Totale ordine: netto - sconto cliente + IVA (VAT)", and base `:19` subtracts the discount once.
- `compute_discount` (`:11-14`) only reads `order`, so both calls return the same amount. VAT (`:20`) is then computed on the lowered net.
- The lowered total is recorded by `ledger.record` (`benchmarks/scope-resolution/app/packages/orders/ledger.py:18`) and returned by `OrderService.checkout` (`benchmarks/scope-resolution/app/packages/orders/service.py:26-30`) through the `checkout` event (`benchmarks/scope-resolution/app/packages/orders/api.py:25-37`).
- Reproduced by Lens 1 through `Dispatcher.handle("checkout", ...)` with net 100 and loyalty 10:

| Ref | Returned total | Ledger line |
|---|---|---|
| base 6dd2c2bbf | 109.8 | `o1\t109.8` |
| candidate 943bdc44c | 97.6 | `o1\t97.6` |

- Premise (independent, Lens 0 HOLDS, form compliant): "for an order with net ≠ 0 and loyalty_percent ≠ 0, `compute_total` @943bdc44c computes its taxable net as net − 2·compute_discount(order), and no repository source specifies more than the single "sconto cliente" term of `pricing.py:18`."
- Panel: Lens 1 REAL (97, reproduced), Lens 2 REAL (92), Lens 3 High (75). Reviewer confidence 85.
- Fix direction: restore `net = order.get("net", 0) - compute_discount(order)`. If a second discount is intended, model it as its own rule, update the docstring and add a numeric test for `compute_total`.
- Led to by **Q1** (and Q2), citing **H1** of `01-context.md` (with S8, D1-D3, D6; `pricing.py:18-19`).

## Medium (1)

**J01-F2: zero and negative totals become reachable for loyalty discounts of 50% to 100%.** `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` @943bdc44c, with effects at `service.py:26-30` and `ledger.py:18`. Category: boundary condition, CWE-682. Co-located with J01-F1.
- For net > 0 the taxable net is about net·(1 − 2p/100), which reaches zero at p 50 instead of p 100 on base. No code on the dispatch path rejects or clamps it, and `ledger.record` writes any value.
- Reproduced by Lens 1 with net 100:

| loyalty_percent | Base total | Candidate total |
|---|---|---|
| 50 | 61.0 | 0.0 |
| 60 | 48.8 | −24.4 |
| 75 | 30.5 | −61.0 |
| 99 | 1.22 | −119.56 |
| 100 | 0.0 | −122.0 |

- The missing range check and negative totals above 100% are preexisting; the candidate introduces the 50% to 100% range. The defect remains even if a double discount turns out to be intended.
- Premise (independent): Lens 0 found the stated form non-compliant. "Returns a negative value for every net > 0" is false by cent rounding: net 0.02 at p 60 gives 0.0. Lens 0 re-derived a minimal premise, "some reachable order with net > 0 and 50 ≤ p ≤ 100 gets a total ≤ 0 while base gives > 0, and nothing on the default dispatch path rejects or clamps it", and that premise HOLDS.
- Panel: Lens 1 REAL (97, reproduced), Lens 2 REAL (88), Lens 3 Medium (75). Reviewer confidence 75.
- Fix direction: fixing J01-F1 restores the base threshold. Add a range check on `loyalty_percent` or on the taxable net before `ledger.record` if non-positive totals are never valid.
- Led to by **Q3**, citing **H3** of `01-context.md` (with D1, D4; `pricing.py:13-14,19-20`, `service.py:26-28`).

## Low (0)

## Summary

Total findings: 2 (Critical 0, High 1, Medium 1, Low 0). Q4 (consumers of the total) raised no finding: in the tree only `OrderService.checkout` consumes the value. Out-of-tree consumers are not visible: the notification handlers configured by environment variable, and whoever writes the `order["total"]` that `payments/gateway.py:10,15` reads.

| Metric | Value |
|---|---|
| Coverage gaps | listed below (critic not in tier, `97-coverage-gaps.md` not produced; no follow-up round) |
| Map utilization | 0 findings cite an interconnect anchor (no interconnect map; operational) |
| Independent premise reconstruction | 2 of 2 findings |
| Premise challenge | 2 of 2 eligible premises attacked by Lens 0 |
| Corroborated findings | 0 (one independent reviewer) |
| Echoes | 0 |
| Pipeline time | Phase 0-1: about 9 min; Phase 2: about 7 min; Phase 4b: about 15 min; total about 33 min |

## Coverage Gaps

The completeness critic is not in the small tier, so no `97-coverage-gaps.md` exists. The coordinator records these gaps:

- **Logic integrity:** the "one loyalty discount" rule across documents, and whether the amount payments charge matches the ledger, are not covered by a domain-rule reviewer. The role is applicable but outside the computed roster.
- **Python baseline:** no Python stack baseline exists in the catalog. mypy, pyright and complexipy are not installed (`pip install mypy`, `pip install pyright`, `pip install complexipy`).
- **Testing:** no testing specialist exists in the two-owner base. No test exercises `compute_total`, `compute_discount` or `vat_amount` numerically. `benchmarks/scope-resolution/test_app_structures.py` passed 11 of 11 on both refs because it only checks text and compilation, so it cannot detect J01-F1.
- **Map:** `codebase_map_graph` failed, and a text search replaced it. Stale-callers is unavailable because only a base-side run exists. The map freshness step `snapshot.py diff --verify` was not run: the run is bound to the main checkout, not to the candidate, and a refresh is not authorized. A scoped hash check replaced it. The map content of `pricing.py` and `service.py` equals the base blobs.
- **Out-of-tree consumers:** `notifications.send_via` targets loaded by `importlib`, and writers of `order["total"]`, are not visible.
- **Composition:** `composition.py bind` bound all 26 leaf members of `senior-review:code-auditor` and does not read the Step 3 selection. The worker accounted for the 25 non-selected members as not applicable.

## Questions for the author (2)

- `benchmarks/scope-resolution/app/packages/orders/pricing.py:19`: is the second subtraction of the loyalty discount intended? If so, what is the second discount, and should the docstring at `pricing.py:18` change?
- `benchmarks/scope-resolution/app/packages/orders/pricing.py:13`: is `loyalty_percent` bounded, for example to 0 through 100 or below 50? No document states a range.

## Cross-reviewer notes (preexisting, not findings)

- `benchmarks/scope-resolution/app/packages/orders/service.py:25` ignores the `False` returned by `reserve_stock`, so checkout records a ledger line even with insufficient stock.
- `benchmarks/scope-resolution/app/packages/orders/ledger.py:9-10,15` opens the lock with `O_EXCL`. It raises `FileExistsError` when `ledger.lock` exists, after stock was already reserved.
- Lens 1 found that checkout raises `KeyError: 'ORDER_NOTIFY_HANDLERS'` at `notifications.py:13` without that environment variable, on both refs. The error comes after the ledger write.

## Learned facts

- (a) Facts used: none. `FACTS.json` has no jobs.
- (b) Findings declined by a learned fact: none. job-01 returned `declined: []`.
- (c) Facts ended in this review: ledger not written (`error: Cannot read the run record of run branch-943bdc44c`, exit 1). `record` ran once with `--run-id branch-943bdc44c --review-id branch-943bdc44c --form-after 3`, and no run record exists.
- (d) Brief: unavailable (`no discovery job in the prepared roster`). `brief` exited 0. Its predicate looks for jobs with `input_mode == "discovery"` and an `id` key, while `composition.py bind` writes `input_mode: independent` and `job_id`. This is a schema mismatch between the two helpers; nothing was repaired.
- (e) Not persisted: 2 findings, because the ledger was not written. Both rows reduce to `benchmarks/scope-resolution/app/packages/orders/pricing.py`, line 19, and are kept in `.team-review/state.json`.

## Method deviations and tool failures

- The Codebase Map MCP tools are not exposed in this session. The coordinator called the same read-only backend, `plugins/codebase-map/skills/map/scripts/mcp_service.py` `MapService`, through `OUT/tools/map_call.py` with `python -B`. It started no run, resume, publish or stop.
- `graph(paths=["benchmarks/scope-resolution/app/packages/orders/pricing.py"], hops=1)` failed with the error below. The run inventory still lists the pre-rename `skills/map-method/` paths. `edit_impact` worked but reported `edge_view.coverage.status: missing_store`, so it gave lexical edges only. No `ModuleNotFoundError` occurred.

```text
ValueError: path is missing or inaccessible: D:\Projects\daodan\plugins\codebase-map\skills\map-method\SKILL.md
```

- In the evidence pack, `python -B -m radon` printed `No module named radon`, so the `radon` CLI was used instead. `python -B -m mypy`, `pyright` and `complexipy` each printed `No module named <tool>`.
- The intent's reason was not asked before dispatch, because this one-round run has no caller channel. It is recorded as `intent: unknown` and carried as a question for the author.
- Report rendering: HTML is unavailable, and this Markdown file is authoritative.

## Workspace hygiene

- **Work tree:** `git status --porcelain` was empty before the review and is empty after it.
- **Main checkout:** no file under `D:/Projects/daodan/.codebase-map` and no `__pycache__` under `D:/Projects/daodan/plugins` changed during the review.
- **Owned artifacts:** everything is under `OUT`: `.team-review/` (state.json, 00-scope.md, 01a-review-knowledge-leads.md, 01-context.md, 02-selection.md, 99-consolidated.md, 98-verification.md), the root JSON files (CATALOG, CONTEXT, ROSTER, BINDINGS, PREPARED-REVIEW, DISPATCH, FACTS), `diff.patch`, `knowledge/selection.json`, `jobs/job-01.md`, `verification/` (8 files), `tools/` and `scratch/`.
- **Scratch:** the Lens 1 directories are empty, because the lenses removed their tests and copies. `scratch/evidence-pack/` (434K) keeps the `git archive` copies used for the structure tests. It is a retention candidate for the caller and was not deleted.
