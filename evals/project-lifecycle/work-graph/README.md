# Isolated work-graph controller experiment

This is a standard-library reference experiment, not a production runtime,
plugin or implementation of the proposed `daodan/work/v2` contract. Its distinct
schema is `work-graph-experiment/v1`. No installed workflow imports it.

It compiles an explicitly supplied plan and persists reservations, attempts,
deliveries, versioned artifact digests, budgets and terminal outcomes in one
JSON record. A writer lock plus revision checks protect concurrent API writers.
All execution is sequential; replan conservatively invalidates every node.
Node identity changes are refused rather than inventing lineage.

The experiment builds the graph plan writer and the graph plan executor. The
other four components of spec section 1.3 are boundary interfaces with
deterministic mocks:

| File | Role |
|---|---|
| `controller.py` | Executor: compiler, `work.json`, budget, gates, recovery, routed dispatch cost and escalation |
| `writer.py` | Writer, review zone only: I3 request, roster floor and citation rule, review expansion |
| `interfaces.py` | Validators of I1 map slice, I2 approved spec, I3 selection, I4 routing |
| `routing.py` | Executor policy over I4: floor, ceiling, host binding, budget fit, judges never escalated |
| `policy.py` | Stand-in for the senior-review role catalog and critical lenses |
| `mock_context.py`, `mock_selector.py`, `mock_router.py` | Mocks of mapper and specs writer, selector and light gate, router |

Whole-plan composition from I1 and I2 is not implemented yet; the conformance
suites only fix the shape the writer will consume.

## Run

From the repository root, using the host-approved Python:

```powershell
python -B -m unittest discover -s evals/project-lifecycle/work-graph -p test_*.py -v
python -B evals/project-lifecycle/work-graph/demo.py evals/project-lifecycle/work-graph/runs/my-new-smoke
```

The demo refuses an existing directory. It writes `work.json` and `trace.json`
for an editing/review/barrier scenario. Every output and verdict is a fixture:
`VERIFIED_SUCCESS` means the simulated graph completed, not that a real document
or application passed a review. No shell command, model or worker is dispatched.

## Observed verification (2026-10-21)

Two independent readers passed the amended design for an isolated prototype.
They did not approve installed-host integration or classifier promotion.
The mother specification still needs the packet-ownership wording aligned
before integration; lifecycle and senior-review remain the packet producers.

The first test run exposed a wrong test oracle: a stopped run rejects `finish`
rather than returning false. The assertion now checks that explicit rejection.
A focused independent source review then found two real defects: serialized
dictionary order could reject a valid replan, and resume could overwrite a
budget-exhaustion outcome. Canonical ordering and terminal-preserving resume
were added with targeted regressions.

Final candidate check: **26 tests passed** in 0.818 seconds with the command
above. The final smoke run completed all three simulated nodes using six units.
No hosted or local inference call was made.

Interfaces and routing pass, same day: **74 tests passed** in 1.1 seconds
(26 controller, 13 review zone, 16 routing, 19 interface conformance). A
mutation check on a scratch copy broke 18 policy rules one at a time (floor,
ceiling, judge escalation, inherited cost, budget fit, tampered routing, free
escalation call, uncited selection, droppable floor, request binding, unknown
role, out-of-range tier, stale slice, open questions, gate) and the suite
failed on all 18. The budget-fit mutant failed by a 60 second timeout rather
than an assertion. Every selector, router, mapper and specs-writer answer is a
mock: no Gutsy, local or hosted model was called.

`runs/20261021-smoke/` is the initial three-node simulation trace. It records
six consumed units and explicit `real_workers=false`, `real_gate_commands=false`.
The later `runs/20261021-verified-smoke/` is the final-candidate replay in a new
directory; prior evidence is retained.

## Acceptance coverage and remaining gates

| Spec criteria | Coverage in this experiment |
|---|---|
| AC01, AC02 | Two-thread/API reservation race, CAS rejection, idempotent completion and changed-payload refusal |
| AC03, AC04 | Budget and attempt carry-over, replan cap, identity-change refusal, new deliveries preserving history |
| AC05 | Not implemented: selective multi-output invalidation; replan invalidates conservatively |
| AC06 | Reserved packets revoked on replan; input mismatch rejected; no real in-flight cancellation |
| AC07 | Pre-dispatch revocation, uncertain running attempt blocks; injected atomic-replace failure preserves old record |
| AC08 | Sequential execution only; no parallel worktree or database isolation claim |
| AC09, AC10 | Simulated inconsistent verifier and repeated failure stop; fingerprint has fixed fixture failure class |
| AC11, AC12 | Not implemented: sidecar, health, identity, restart and timeout adapters |
| AC13 | Missing operator/gate/dependency rejected; roster floor never dropped; no installed-provider or model-encoding checks |
| AC14 | Public experiment API has no budget update/reset; no host filesystem confinement claim |
| AC15 | Terminal preservation verified; production v1/v2 migration and consumer compatibility not implemented |
| AC16 | Nine archetype IDs accepted and read-only mutation rejected; full archetype-specific template semantics not implemented |
| AC17 | Selection citations must name a request hunk; uncited selections are ignored, never reassigned; no semantic citation check |
| AC18 | Not implemented: shadow/active model policy |
| AC19 | Cycle/unresolved-edge rejection on explicit plans; no code graph or semantic planner integration |
| AC20 | Demo refuses existing run directory; historical classifier outputs are not read or rewritten |
| AC21 | Conformance suites of I1-I4: unknown schema, foreign request digest, options and references outside the request rejected |
| AC22 | Floor, ceiling, abstain/unavailable/malformed default, `POLICY_BLOCKED` and `BUDGET_EXHAUSTED` before any spend |
| AC23 | Fixture host probes only: inherit binding, packet policy, session or maximum tier charged; no live host probe |
| AC24 | Judge escalation refused; escalation then same failure stops with unchanged fingerprint and graph digest |
| AC25 | Floor kept when omitted or deselected; uncited selection ignored and recorded; light gate with one re-preparation |

This table is not full acceptance of AC01-AC20. Verification is limited to the
experiment's admission API and simulated evidence. Tests do not prove crash
durability under power loss, multi-process race behavior, adversarial filesystem
confinement, real worker handle reconciliation, active-time clocks, all runtime
caps, or authentic post-patch gate evidence. The API accepts fixture candidate
identities and verdicts and must never be exposed as a production trust boundary.

Next implementation gate: whole-plan composition in the writer from I2
requirements and contracts plus I1 components, then typed gate evidence,
selective invalidation and the missing admission policies, verified before
writing an installed-host adapter. Real implementations of I1-I4 enter only
after passing the same conformance suites. Gutsy remains a separate offline
experiment; a functioning graph controller does not validate its routing.
