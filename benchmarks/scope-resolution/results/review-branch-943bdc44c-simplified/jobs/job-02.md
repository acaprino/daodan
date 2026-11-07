# job-02: logic integrity, branch-943bdc44c-simplified

- dimension: logic-integrity
- reviewer: senior-review:logic-integrity-auditor
- status: delivered
- findings: [LI-1]
- gaps: [G1, G2, G3, G4]
- output_path: OUT/jobs/job-02.md
- knowledge_usage: []
- basis: changeset `6dd2c2bbf..943bdc44c`, one file changed (confirmed with `git diff --stat`); static reading, no execution

## member_results

| specialist | delivery | coverage | findings | gaps |
|---|---|---|---|---|
| senior-review:logic-integrity-auditor | delivered | complete | LI-1 | G1, G2, G3, G4 |

## Findings

### LI-1 (High, L4 domain rule, L1.2 postcondition): customer discount subtracted twice

- file: `benchmarks/scope-resolution/app/packages/orders/pricing.py`
- line: 19
- severity: High
- confidence: 92
- evidence: line 19 is `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`. The unchanged docstring on line 18 states the rule, `Totale ordine: netto - sconto cliente + IVA (VAT).`, with one customer discount. Line 12 defines that discount as the loyalty percentage applied to the net. `compute_discount` (lines 11-14) reads only the order's original `net` and `loyalty_percent` and mutates nothing, so both calls return the same value and the effective discount is exactly twice `loyalty_percent`. Line 20 then computes VAT on the reduced net, so VAT is understated as well.
- path: `register_defaults` (`benchmarks/scope-resolution/app/packages/orders/api.py:37`) wires `service.checkout`; `Dispatcher.handle` and `_invoke` (`api.py:29-31`, `api.py:25-27`) call it; `OrderService.checkout` gets the total (`service.py:26`), appends it to the ledger (`service.py:28`, `ledger.py:18`) and returns it (`service.py:30`). All in `benchmarks/scope-resolution/app/packages/orders/`. Map anchor: `tools/edit-impact-summary.json`, target `compute_total`, one caller and two callees; re-derived by text search in the work tree.
- trigger: `checkout` with a non-zero `net` and a non-zero `loyalty_percent`. Payloads pass through unchanged (`api.py:4`, `api.py:27`).
- observable symptom (hand-computed, `net` = 100, not executed):

| `loyalty_percent` | base total | candidate total | effect |
|---|---|---|---|
| 0 or absent | 122.0 | 122.0 | none, so orders without loyalty hide the defect |
| 10 | 109.8 | 97.6 | 12.2 short: net 80 instead of 90, VAT 17.6 instead of 19.8 |
| 50 | 61.0 | 0.0 | order total becomes zero |
| 60 | 48.8 | -24.4 | negative total; in the base this needs `loyalty_percent` above 100 |

  The wrong value is appended to the ledger and returned to the caller, with no error.
- premise: the required formula of `compute_total` subtracts the customer discount exactly once, and no requirement establishes a second subtraction.
- premise_provenance: independent. `02-selection.md` pointed to the docstrings; the rule and its violation were re-read from source.
- counterevidence_checked:
  - A distinct second discount the extra term could stand for: none in `pricing.py`. `volume_discount` (`benchmarks/scope-resolution/app/packages/shipping/rates.py:15`) is a shipping discount, used only by `quote` (`rates.py:27`).
  - A stated reason: the commit body has only trailers, and the docstrings were not updated. `README.md`, `CASES.md` and `ground_truth.json` of the benchmark declare no double discount; the `ground_truth.json` C1 rationale cites `pricing.py:19` for the call relation only.
  - A guard or correction: nothing between `service.py:26` and `service.py:28`. `DefaultPipeline.step` (`service.py:13-15`) only sets `validated` and runs after the total. `pricing.py` has no clamp on the percent or the net.
  - A test that would refute it: none runs this code. `benchmarks/scope-resolution/test_app_structures.py:70-72` checks symbol text only, so the 11 passed in the evidence pack say nothing about the value. The packet's `related_tests_total: 0` agrees.
  - A cancelling path: `compute_total` has no other caller, and no in-tree code reads `LEDGER_PATH` outside `ledger.py`, so nothing reconciles the entry.
- introduced_by_candidate: true
- evidence_class: derived
- fix direction: remove the second subtraction, so that line 19 reads `net = order.get("net", 0) - compute_discount(order)`, and add a value test with a non-zero loyalty. If a doubled discount really is the new rule, state that requirement, express it in `compute_discount` and its docstrings rather than through a repeated call, and define the behaviour above 50 percent.
- severity note: the taxonomy's "silent financial error" reads Critical. It is held at High because the evidence is derived and the app is a benchmark fixture, not shipped software, and because no in-tree path carries this total to a charge (G3). High is relative to the fixture's own domain.

## Checks by category

| Category | Result |
|---|---|
| L1 contracts | Violated postcondition, LI-1. `compute_total` has one definition and one static caller (`service.py:26`); no admin, batch, retry or migration path exists in the tree. |
| L2 invariants, multiplicity | Ledger total equals returned total: holds on the checkout path, the same value is passed (`service.py:26-30`). The second `VAT_RATE` (`payments/refunds.py:7`) is preexisting and unchanged, and is not an effect of this change. |
| L3 assumptions | Tested whether the second call could differ or compound: it cannot, the function is pure and reads the original net. Part of LI-1. |
| L4 domain rules | LI-1. No feature-flag branch exists. Payment and refund paths are not connected to this total in the tree (G3). |
| L5 ordering, reentrancy | Pricing holds no state and has no callback, so the change creates no forbidden intermediate state. The pipeline running after the total (`service.py:26-27`) is preexisting, and no non-default pipeline exists in the tree. |
| L6 idempotency | `compute_total` is deterministic. Ledger repetition behaviour is untouched by the candidate. |
| L7 state machines | Not applicable: the change touches no transition. |
| L8 representations | The ledger format is unchanged (`ledger.py:18`). Zero and negative totals become easier to reach, and that is an effect of LI-1, not a second defect. |

Preexisting, no finding: `pricing.py` does not bound `loyalty_percent`, but no requirement in scope sets a bound, and the candidate's contribution is already in LI-1.

Outside the finding scope, for the coordinator only: `service.py:25` ignores the `False` that `reserve_stock` returns on insufficient stock (`inventory.py:18`, `inventory.py:22`), so checkout still records a total. It is preexisting and not an effect of this change.

## Gaps

- G1: no execution was granted. All values above are hand-computed; none was reproduced.
- G2: map tools were not available. The packet is bound to an earlier revision (`7bd0ff186c50`, dirty) and reports `edge_view_coverage: missing_store`, and there is no interconnect map. Callers and consumers were re-derived by text search, which cannot resolve the `importlib` dispatch in `notifications.py:13-15`.
- G3: effects outside the tree are undeterminable. Nothing in the tree writes `order["total"]`, which `payments/gateway.py:10` and `gateway.py:15` read; `issue_refund`, `format_daily_summary` and `Dispatcher.handle` have no in-tree caller; receipt handlers come from `ORDER_NOTIFY_HANDLERS` and receive the order, not the total (`service.py:29`). So this report claims a wrong ledger entry and return value, and does not claim a wrong card charge, receipt or report.
- G4: the rule's only source is the docstrings. No requirement document or domain-rules record exists for this fixture. A requirement outside the admitted scope that asks for a doubled discount would collapse LI-1's premise. Effects on benchmark artifacts belong to the artifact-lifecycle reviewer.
