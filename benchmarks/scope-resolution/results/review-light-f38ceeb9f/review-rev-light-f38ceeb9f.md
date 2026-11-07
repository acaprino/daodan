# Review rev-light-f38ceeb9f — light, changeset

**Verdict: BLOCK.** CA-01 (High) was verified: Lens 0 found the premise HOLDS, and Lens 1 returned REAL with a `reproduced` result.

## Target and basis

- Candidate: commit f38ceeb9f3b74b4fefe6979275976b989777c598 on branch bench-seed-discount, in worktree D:/Projects/daodan-seed. The worktree was clean before the review and is still clean after it.
- Base: 6dd2c2bbf. Scope `f38ceeb9f`, the actual diff, saved in DIFF.patch.
- Basis: changeset. Policy is the base AGENTS.md.
- Conclusion paths:
  - benchmarks/scope-resolution/README.md
  - benchmarks/scope-resolution/app/packages/orders/pricing.py
  - benchmarks/scope-resolution/test_pricing_oracle.py
- Intent, from the user's words, given to the reviewer verbatim: "Rivedi l'ultimo commit (f38ceeb9f) del benchmark scope-resolution: verifica la modifica e i suoi effetti sul calcolo del totale ordine."

## Roster

- `review_roster.py compute --shape light --kind changeset` gave tier `light`, roster `senior-review:code-auditor`, reason "no raising signal" and verification `critical-high`.
- `composition.py bind` produced one job, job-01, with 26 leaf members and status bound.
- Body digest: afcda6f14b8471f3f1c38cda61c350403dbce52c10bef2abbbfc733a773d2fa8.
- Advice, returned verbatim: "required specialist obligations must fit the single discovery; otherwise review-branch is required". They fit: one job covers all 26 members.

## Tools (TOOLS.md)

| Check | Command | Exit | Result |
|---|---|---|---|
| Tests | `python -B -m pytest -q -p no:cacheprovider` on test_pricing_oracle.py, test_app_structures.py and test_resolver.py (pytest 9.1.1, Python 3.13.14) | 1 | 1 failed, 27 passed, 1 xfailed. `assert 97.6 == 109.8` at test_pricing_oracle.py:18 |
| Lint | `ruff check` (0.15.20) | 0 | No findings |
| Format | `ruff format --check` | 1 | Would reformat test_pricing_oracle.py. No formatter is configured, so this is informational |

There is no type checker, and no manifest changed.

## Findings

1. **CA-01, High.** benchmarks/scope-resolution/app/packages/orders/pricing.py:19
   - What: `compute_total` subtracts `compute_discount(order)` twice. Any order with `loyalty_percent > 0` is undercharged by discount × 1.22, and above 50% loyalty the total goes negative.
   - Where the wrong total goes: it is returned by `OrderService.checkout` (service.py:26) and persisted by `ledger.record` (ledger.py:13-18).
   - Introduced by the candidate: yes.
   - Evidence class: tool-reported plus reproduced.
   - Verification:
     - Lens 0 (premise-auditor Mode 2): HOLDS, no counterexample (jobs/lens0-CA-01.md).
     - Lens 1 (isolated worker): REAL, confidence 97, reproduced. The scratch test passes on the base and fails on the candidate (jobs/lens1-CA-01.md).
2. **CA-02, Low.** benchmarks/scope-resolution/README.md:8
   - What: the command reference still says the suite ends with only "1 xfail dichiarato". On this commit it ends with 1 failed.
   - Verification: none. Severities below High stay unverified.

## Preexisting issues (not eligible)

None were reported as findings. Two leads only:

- `loyalty_percent` has no range check (pricing.py:13).
- Money is held as float and rounded (pricing.py:8, 14, 20).

## Gaps and advice

- **Map.** The worktree has no Codebase Map, so the prerequisite was met only by the complete map `daodan-lite-20261107-2` of the main checkout at 7bd0ff186. That is the same repository, but an older snapshot.
- **Graph tools.** `symbols-at` worked. `edit-impact` and `graph` failed with `ModuleNotFoundError: No module named 'edge_view'` and `'store_graph'`. `stale-callers` was unavailable because there is no candidate run. Callers were confirmed by text search only.
- **Protocol run.** No review run was opened, because no host run-record mechanism exists. Artifacts live under D:/Projects/_review-tmp/review-light-f38ceeb9f/ instead.
- **Disclosure.** The diff itself discloses the defect, through the README section at lines 24-27 and the oracle docstring. Measuring whether "the review finds the defect in the diff" is therefore not blind.

## Questions for the author

- benchmarks/scope-resolution/README.md:27: is bench-seed-discount meant to stay unmerged? If it is merged:
  - the documented command and any root pytest run stay red;
  - the C4 case gets a real discount bug, which may act as a disambiguating signal.

## Learned facts

- (a) Unavailable. `brief` reported: "no discovery job in the prepared roster". The helper expects `input_mode: discovery` and a job `id`, while bind writes `independent` and `job_id`.
- (b) None.
- (c) Ledger not written. `record` reported: "Cannot read the run record of run review-f38ceeb9f".
- (e) Not applicable.

## Envelope

```yaml
review_id: rev-light-f38ceeb9f
shape: light
kind: changeset
verdict: BLOCK
candidate: f38ceeb9f3b74b4fefe6979275976b989777c598
base: 6dd2c2bbf
findings: [{id: CA-01, severity: High, verified: REAL}, {id: CA-02, severity: Low, verified: false}]
deliveries: [jobs/job-01.md, jobs/lens0-CA-01.md, jobs/lens1-CA-01.md]
gaps: [no-candidate-map, edit-impact-broken, graph-broken, stale-callers-unavailable, no-protocol-run, learned-facts-unavailable]
```
