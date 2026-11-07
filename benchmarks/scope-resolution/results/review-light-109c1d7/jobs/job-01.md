# job-01 — senior-review:code-auditor (light review `light-109c1d7`)

```yaml
dimension: code-auditor
reviewer: senior-review:code-auditor (job-01, isolated worker; 27 members composed)
status: delivered
candidate: 109c1d7e07b5e594a1bc3310f14f20df8f926b92
base: 2889c58ebb08bb047077a01ac97f0f686fac3dab
basis: changeset
output_path: benchmarks/scope-resolution/results/review-light-109c1d7/jobs/job-01.md
knowledge_usage: []
body_sha256: a8660b6ebb23f90c457a68c1f5a100cb494f72dac33c01ecaba7e16e501bcfba
```

## Findings

### F1 — `compute_total` subtracts the customer discount twice (High, confidence 95)

```yaml
id: F1
severity: High
file: benchmarks/scope-resolution/app/packages/orders/pricing.py
line: 19
owner: senior-review:local-correctness-auditor
also_applied_by: [senior-review:logic-integrity-auditor (L1.2 unkept postcondition, L4 money rule [MAP-GAP]), senior-review:data-representation-auditor (persisted total)]
introduced_by_candidate: true
evidence_class: reproduced
confidence: 95
premise_provenance: independent
```

- **Claim.** The candidate line `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)` applies the loyalty discount twice, so every order with `loyalty_percent > 0` is totalled below the documented rule and VAT is computed on the doubly-discounted base.
- **Requirement (provenance: source read).** `pricing.py:18` docstring, unchanged by the candidate: "Totale ordine: netto - sconto cliente + IVA (VAT)" (one discount). `pricing.py:12`: the discount is "percentuale di fedeltà applicata al netto" (loyalty% of net, once). `service.py:24` and `api.py:5-6` only add that the total includes VAT. The commit message ("benchmark: aggiorna il calcolo in pricing.py") states no reason for a second subtraction.
- **Trigger.** Any `order` dict with `loyalty_percent > 0` passed to `OrderService.checkout` (`service.py:26`, the only caller found by `git grep compute_total` over `app/` and the test files).
- **Reproduced (`python3 -I` on base file via `git show 2889c58:…pricing.py` vs working-tree candidate, pure functions only).**
  - `{net: 100, loyalty_percent: 10}` → base `109.8`, candidate `97.6` (undercharge 12.20 = discount 10 + VAT 2.20).
  - `{net: 250, loyalty_percent: 5}` → base `289.75`, candidate `274.5`.
  - `{net: 100, loyalty_percent: 50}` → base `61.0`, candidate `0.0`.
  - `{net: 100, loyalty_percent: 60}` → base `48.8`, candidate `-24.4` (negative total; at base a negative total needs `loyalty_percent > 100`).
  - `loyalty_percent: 0` → unchanged `122.0`.
- **Observable consequence.** `checkout` returns the wrong total and `ledger.record(order, total)` (`service.py:28`, `ledger.py:18`) appends it to `ledger.log`; `notifications.send_via` is called after the same order. With `loyalty_percent >= 50` the persisted order total is zero or negative. No reader of `ledger.log` exists in `app/` (`git grep LEDGER_PATH`), so the wrong value is persisted, not re-read, inside this codebase.
- **Counterevidence checked.** (a) Docstrings of `compute_total`/`compute_discount` unchanged, state a single discount. (b) No other caller or alternate path computes the total differently (`git grep` for `compute_total`, `compute_discount`, `loyalty`: only `pricing.py` and `service.py:26`). (c) No test pins a numeric total: `test_app_structures.py:70-72` only asserts `def compute_discount(` exists, so the passing suite cannot see this. (d) No requirement, decision record or comment in scope motivates a doubled discount. (e) `compute_discount` is pure (reads `order` only), so the second call is not a side-effect-bearing step that could be intentional.
- **Load-bearing premise.** "The documented pricing rule in `pricing.py:18` requires the customer discount to be subtracted from the net exactly once." If a requirement for a double discount exists outside the scope, the finding collapses to a stale-docstring note.
- **Fix direction.** Restore line 19 to the base form (`net = order.get("net", 0) - compute_discount(order)`); if a second concession is intended, name it as its own function and update the docstring and a numeric test for `compute_total`.

## Gaps

- No linter, formatter, type checker or numeric test covers `compute_total`; the tool line in the evidence pack is structurally blind to this change (already recorded by the brief; not restated).
- Codebase Map, `edit-impact`, `stale-callers` and learned facts unavailable; caller set derived by `git grep` only (one caller, `service.py:26`).
- Runtime exercise limited to the pure functions of `pricing.py`; `OrderService.checkout` was not executed (filesystem lock/ledger writes and `os.environ`-driven `notifications.send_via` are side-effecting). Static inspection covered that path.
- Taxonomy loaded: `logic-integrity.md` L1/L4 and `logic-types.md` headings only; `security.md`, `distributed-integration.md`, `data-design-ops.md`, `memory-resources.md`, `concurrency-state.md` not loaded (no applicable mechanism in the changeset).
- Preexisting, not reported: `loyalty_percent` has no range validation anywhere (`git grep loyalty`), and money is `float`; no independent requirement in scope establishes either rule, and the candidate does not introduce them.

## Member results

Common perimeter for every member: changed line `pricing.py:19` inside `compute_total` (lines 17-20), base and candidate read; one hop to `service.py:23-30` (sole caller), its sinks `ledger.record` (`ledger.py:13-22`) and `notifications.send_via`, `test_app_structures.py`, `pyproject.toml`. `coverage: complete` means every causal check of the role was applied to this perimeter; the role's "DO NOT TRIGGER" condition was verified against the changeset, not assumed.

```yaml
member_results:
  - member: senior-review:ai-boundary-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no prompt, model output, retrieved document or tool invocation in pricing.py or its caller path.
  - member: senior-review:algorithmic-cost-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: the duplicated compute_discount call is constant extra work on a fixed-size dict (two .get, one multiply, one round); no evidenced throughput or latency requirement; not a finding.
  - member: senior-review:api-contract-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: signature and return type of compute_total unchanged (float, rounded to 2 decimals); no schema, serializer or client in scope; the value error is F1, not drift.
  - member: senior-review:audit-trail-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: ["no approved audit obligation supplied for ledger.log; whether it is an audit record is unknown"]
    note: the candidate changes the value ledger.record persists, not the record path, attribution or framing; routed to F1.
  - member: senior-review:authorization-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no principal, caller-supplied ID or permission check in scope.
  - member: senior-review:browser-security-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no browser-visible sink, cookie, CORS/CSP or response policy in scope.
  - member: senior-review:cache-consistency-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no cache, replica, index or derived store; compute_total is recomputed on each call.
  - member: senior-review:callback-authenticity-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no signed callback or webhook in scope; api.py dispatch is in-process and untouched.
  - member: senior-review:capacity-quota-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no queue, worker, quota or admission path in scope.
  - member: senior-review:chicken-egg-detector
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: pricing.py has no imports; service.py import chain unchanged; no startup prerequisite introduced.
  - member: senior-review:data-representation-auditor
    status: delivered
    coverage: complete
    findings: [F1]
    gaps: []
    note: persisted meaning of the ledger total changes (zero or negative order totals for loyalty_percent >= 50); same root cause as F1, no separate finding. Float money and rounding are preexisting and unchanged.
  - member: senior-review:data-retention-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: ["no approved retention policy supplied"]
    note: no deletion, expiry or copy path in the changeset.
  - member: senior-review:environment-binding-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no environment variable, endpoint or configuration layer touched; VAT_RATE constant unchanged.
  - member: senior-review:input-validation-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: order values reach only arithmetic, no interpreting sink; missing range validation of loyalty_percent is preexisting and without an independent requirement (see Gaps).
  - member: senior-review:local-concurrency-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: compute_total is pure over its argument; no shared state, lock or interleaving introduced; ledger lockfile untouched.
  - member: senior-review:local-correctness-auditor
    status: delivered
    coverage: complete
    findings: [F1]
    gaps: []
    note: arithmetic against the local documented contract; zero/negative bounds and the single caller checked; reproduced with base vs candidate.
  - member: senior-review:logic-integrity-auditor
    status: delivered
    coverage: complete
    findings: [F1]
    gaps: ["review ran without scoped semantic context; rules derived from source and marked [MAP-GAP]"]
    note: "[MAP-GAP] rule: total = net - one customer discount + VAT (pricing.py:18, :12; service.py:24; api.py:5-6). L1.2 postcondition unkept, L4 money rule violated on the single path. Multiplicity settled: one caller (service.py:26), no alternate total computation (git grep). L5-L7 not applicable: no state transitions or repeated operation introduced."
  - member: senior-review:message-delivery-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no broker, publisher or consumer in scope.
  - member: senior-review:remote-effect-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no external mutation, payment or idempotency key in the changeset; the ledger write is local and unchanged.
  - member: senior-review:resource-lifecycle-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no resource acquired in pricing.py; ledger lock/file handling (ledger.py:15-21) untouched by the candidate.
  - member: senior-review:schema-coherence-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no DDL, ORM model, SQL or persistent schema in scope.
  - member: senior-review:secret-exposure-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no credential, key or error/debug output in scope.
  - member: senior-review:service-resilience-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no cross-service call, timeout or retry in scope.
  - member: senior-review:session-delegation-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no credential issuance, session or token in scope.
  - member: senior-review:temporal-resilience-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no timer, scheduler, retry loop or background job in scope.
  - member: senior-review:transaction-integrity-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no transaction boundary, constraint or concurrent writer changed; the wrong persisted value is F1's consequence, not an atomicity defect.
  - member: senior-review:untrusted-resource-auditor
    status: delivered
    coverage: complete
    findings: []
    gaps: []
    note: no caller-controlled path, upload or outbound URL in scope.
```

Members delivered: 27/27. Findings: 1 (F1). Overall status: delivered.
