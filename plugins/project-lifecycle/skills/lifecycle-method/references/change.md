# Change

A change is one task carried through seven phases, each closing before the
next opens. The run record is the source of truth at every boundary; this
unit is the overview, and each phase has its own unit.

| Phase | Outcome | Unit |
|---|---|---|
| 1. Preflight and workspace | Git state probed, baseline classified, map fresh, workspace mode chosen with the user | `references/preflight.md` |
| 2. Interview | Scope, examples, rejected alternatives and invariants fixed from real code | `references/interview.md` |
| 3. Record | A `Proposed` decision record written and reviewed as a `spec` | `references/interview.md` |
| 4. Plan | Waves of micro-tasks compiled, checked by the helper, reviewed as a `plan` | `references/waves.md` |
| 5. Execution | Each wave written by the stack's specialist, verified, reviewed with shape `light`, sealed | `references/waves.md`, `references/worker-brief.md` |
| 6. Candidate | The whole candidate reviewed with shape `branch`; blocking findings repaired in a bounded wave | `references/verify.md` |
| 7. Integration | Merge, record promotion, map and knowledge realigned, workspace closed | `references/consolidate.md` |

`--plan-only` stops after phase 4 with the record `Proposed` and the plan
approved; `--run-id RUN` on that run continues the approved plan from its
first unsealed wave. A bugfix with a reproduction test follows `references/repair.md`, which
shortens phases 2 to 4 and keeps the rest.

Rules that hold across phases:

- Discover existing code, tests, decisions and instructions before adding a
  representation. Prefer an implementation that exists.
- Conflicting requirements become concrete alternatives for the user; the
  current code is never promoted into the requirement.
- Preserve preexisting edits and other sessions' work. Recovery restores the
  owned pre-phase state, never `HEAD~1`.
- Bootstrap of a new project is phase 0 of `references/assess.md`, then this
  cycle for its first task.
- Severe evidenced defects and broken entry paths come before cosmetic work.
- A plan or a diff without verification is not completed development.
