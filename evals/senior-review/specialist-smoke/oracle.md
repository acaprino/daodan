# Evaluator-only oracle

Do not supply this file to the workers. Three narrow smoke cases each contain one
defect and one equivalent protected path. They check use of the new role bodies,
source evidence and avoidance of an obvious false positive, not broad efficacy.

| Role | Required finding | Protected path |
|---|---|---|
| accessibility | view-a.html has a focusable ARIA button with mouse click only; keyboard activation has no handler/native semantics | view-b.html native button supports keyboard activation |
| performance | page_a performs 1+N network queries, exceeding two per page for N>1 | page_b performs one join query |
| operability | migration-a removes v1's name column before v1 drains | migration-b preserves name during overlap/rollback and backfills display_name under declared no-write conditions |

All three workers must distinguish static reasoning from execution and avoid
inventing measured latency, browser results, deployment success or compliance.
