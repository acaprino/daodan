# job-01 report: senior-review:code-auditor

```yaml
dimension: code
reviewer: senior-review:code-auditor
status: delivered
output_path: D:/Projects/_review-tmp/review-light-f38ceeb9f/jobs/job-01.md
knowledge_usage: []
job_binding:
  job_id: job-01
  role: senior-review:code-auditor
  scope: f38ceeb9f
  candidate: f38ceeb9f3b74b4fefe6979275976b989777c598
  base: 6dd2c2bbf
  body_sha256: afcda6f14b8471f3f1c38cda61c350403dbce52c10bef2abbbfc733a773d2fa8
  reviewer_common_sha256: 67ee0a0efa2513d11fcbc1d1a100700f5df5fd45aaf937d620d07a95fb51dabc
findings: [CA-01, CA-02]
```

Base policy read at 6dd2c2bbf:AGENTS.md. No formatter is configured, so the `ruff format` result in TOOLS.md is not a finding. The README and the commit message say the defect is seeded on purpose. That is a statement of intent written in the candidate. It grants no exemption, so CA-01 stands.

## Findings

### CA-01: High. Customer discount subtracted twice in `compute_total`

- file:line: benchmarks/scope-resolution/app/packages/orders/pricing.py:19
- evidence: `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`. `compute_discount` (pricing.py:11-14) is pure and reads `order["net"]` both times, so it returns the same discount twice. TOOLS.md: `test_pricing_oracle.py::test_total_applies_loyalty_discount_once` fails with `assert 97.6 == 109.8`. I ran base and candidate `pricing.py` in memory (`python -B -I -c`, exec of `git show 6dd2c2bbf:...` and of the worktree file; no files written):
  - `{net:100, loyalty_percent:10}`: base 109.8, candidate 97.6.
  - `{net:19.99, loyalty_percent:15}`: base 20.73, candidate 17.07.
  - `{net:100, loyalty_percent:60}`: base 48.8, candidate -24.4.
  - No loyalty, or no net: unchanged (122.0 / 0.0).

  The oracle is green on the base logic (`109.8 == 109.8` → True).
- effect on the order total: every order with `loyalty_percent > 0` is undercharged by `discount × 1.22`. Above 50% loyalty the total turns negative; on the base that happens only above 100%. The only caller is `OrderService.checkout` (service.py:26), found by text search over benchmarks/scope-resolution. It returns this total and writes it to `ledger.log` via `ledger.record` (ledger.py:13-18). VAT is also computed on the wrong net (`vat_amount(net)`, pricing.py:20). `reporting.py` uses only `pricing.VAT_RATE` and is unaffected. Severity is calibrated to the fixture app's own contract: a wrong amount on the checkout path, persisted to the ledger.
- confidence: 97
- fix direction: subtract the discount once. Compute it once (`discount = compute_discount(order)`; `net = order.get("net", 0) - discount`), which restores the base line 19 and makes the oracle green.
- premise: `compute_total` must subtract the customer discount exactly once from the net before VAT.
- premise_provenance: independent. It comes from the docstring at pricing.py:18 ("netto - sconto cliente + IVA"), the base line 19, the oracle's stated expectation, and an in-memory run. The Codebase Map symbols-at locator was used only to locate the symbol.
- trigger: any order dict with `net > 0` and `loyalty_percent > 0` reaching `compute_total`, directly or through `OrderService.checkout`.
- counterevidence_checked:
  - Searched for a caller that pre-halves or compensates the discount: none.
  - Checked whether `compute_discount` changes `order` so the second call returns 0: it does not.
  - Searched for a requirement stating a cumulative double discount: none. The docstring and oracle say once.
  - Searched for other callers of `compute_total`/`compute_discount` in benchmarks/scope-resolution (`big_module.py` included): none besides service.py:26.
  - Checked whether existing tests cover the total value: only the new oracle does. test_app_structures.py:71 checks only that `def compute_discount(` exists.
- introduced_by_candidate: true
- evidence_class: tool-reported (the oracle is red in TOOLS.md). Also reproduced by the in-memory base/candidate run above.

### CA-02: Low. README command reference still says the suite ends with only the declared xfail

- file:line: benchmarks/scope-resolution/README.md:8
- evidence: line 8 documents `python -B -m pytest -q  # strutture, protocollo, resolver (1 xfail dichiarato)`. On the candidate the same command ends `1 failed, 27 passed, 1 xfailed` (TOOLS.md). The new section at README.md:27 says the suite "resta rosso", but the command reference at line 8 still states the old expected outcome.
- confidence: 70
- fix direction: update the line 8 comment to name the deliberate red oracle (for example "1 xfail dichiarato; rosso finché il difetto seminato resta"), or point to the section at line 24.
- premise: the comment at README.md:8 describes the expected outcome of that command on this commit.
- premise_provenance: independent (README text plus the TOOLS.md run).
- trigger: a reader runs the documented command from line 8 and sees an unexpected failure. The line does not say the failure is expected.
- counterevidence_checked: README.md:27 states the red outcome, which lowers the impact. No other place lists the expected pytest result.
- introduced_by_candidate: true. The base README was accurate before the candidate made the suite red; the candidate leaves line 8 stale.
- evidence_class: tool-reported

## Preexisting (not eligible, listed separately)

None reported in the conclusion paths.

- `loyalty_percent` has no range check (pricing.py:13). It is preexisting, and no requirement for a range was found. The candidate only moves the negative-total threshold from 100% to 50%, which is part of CA-01's consequence.
- Float money with `round` (pricing.py:8, :14, :20) is also preexisting. No rounding requirement exists, and I found no value whose meaning changes. This is a lead, not a finding.

## Questions for the author

- benchmarks/scope-resolution/README.md:27: is `bench-seed-discount` meant to stay unmerged? If it reaches `main`, two things follow:
  - The benchmark command at README.md:8, and any repository-root `pytest` run (no repo-level pytest config limits collection), stay red.
  - Case C4 ("C'è un bug nello sconto: rivedi lo sconto", ground_truth.json expects `clarify` because "l'intent non dà segnali disambiguanti") now has a real discount bug in pricing.py. Later model sessions could read that as a disambiguating signal.

## Gaps

- Graph edit-impact, graph queries and stale-callers were unavailable (brief: `ModuleNotFoundError: No module named 'edge_view'` / `'store_graph'`; no candidate map run). Callers are text-search verified only.
- Runtime exercise was limited to the in-memory pricing comparison above. Everything else is static inspection. `checkout` was not exercised end to end, because it needs `ORDER_NOTIFY_HANDLERS` and writes `ledger.log`/`ledger.lock` in the CWD.

## member_results

| specialist | status | coverage | findings | gaps / reason |
|---|---|---|---|---|
| local-correctness-auditor | delivered | complete | CA-01, CA-02 | arithmetic at pricing.py:19, caller service.py:26, oracle values verified |
| local-concurrency-auditor | delivered | complete | none | candidate adds a second call to a pure function; no shared state or interleaving touched |
| input-validation-auditor | delivered | complete | none | no parser or interpreting sink; unbounded `loyalty_percent` is preexisting and its new consequence is under CA-01 |
| resource-lifecycle-auditor | delivered | complete | none | candidate acquires no resource; the oracle's `sys.path` insert is undone in `finally` (test_pricing_oracle.py:13-16) |
| algorithmic-cost-auditor | delivered | complete | none | one extra O(1) call per total; no input-dependent cost |
| authorization-auditor | delivered | complete | none | no principal, resource grant or route in the change |
| session-delegation-auditor | delivered | complete | none | no credentials or sessions in scope |
| secret-exposure-auditor | delivered | complete | none | no secrets, keys or crypto in the changed files |
| untrusted-resource-auditor | delivered | complete | none | no caller-controlled path or URL in the change; the oracle path is derived from `__file__` |
| browser-security-auditor | delivered | complete | none | no browser-facing surface |
| callback-authenticity-auditor | delivered | complete | none | in-process `EVENT_REGISTRY` dispatch (api.py) is unchanged and has no signed callbacks |
| ai-boundary-auditor | delivered | complete | none | no model, prompt or tool invocation in the changed code |
| audit-trail-auditor | delivered | complete | none | no approved audit obligation; ledger.log records the wrong total as a consequence of CA-01 |
| capacity-quota-auditor | delivered | complete | none | no admission, queue or quota mechanism touched |
| transaction-integrity-auditor | delivered | complete | none | ledger write atomicity is unchanged; the wrong persisted value is CA-01 (arithmetic owner) |
| schema-coherence-auditor | delivered | complete | none | no schema, ORM or SQL in scope |
| cache-consistency-auditor | delivered | complete | none | no cache or derived store |
| data-representation-auditor | delivered | complete | none | no conversion or rounding change; the persisted total's wrong meaning comes from CA-01 arithmetic; float rounding is a preexisting lead only |
| data-retention-auditor | delivered | complete | none | no retention policy or deletion path |
| chicken-egg-detector | delivered | complete | none | no startup or initialization ordering change; the oracle import mirrors test_app_structures.py:20-27 with the same path |
| temporal-resilience-auditor | delivered | complete | none | no timers, retries or background work |
| message-delivery-auditor | delivered | complete | none | no broker; dispatch is in-process |
| remote-effect-auditor | delivered | complete | none | `notifications.send_via` is unchanged and receives the order, not the total |
| service-resilience-auditor | delivered | complete | none | no cross-service calls changed |
| environment-binding-auditor | delivered | complete | none | `ORDER_NOTIFY_HANDLERS` binding unchanged and not exposed by the candidate |
| api-contract-auditor | delivered | complete | none (CA-01, CA-02 routed to local-correctness) | the documented `compute_total`/`checkout` promise ("netto - sconto cliente + IVA") is broken by CA-01; no wire schema |
