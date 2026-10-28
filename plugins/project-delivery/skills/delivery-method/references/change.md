# Change

Seven phases close in order. The run record governs boundaries; each phase
has its own unit.

| Phase | Outcome | Unit |
|---|---|---|
| 1. Preflight and workspace | Git state probed, baseline classified, map fresh, workspace mode chosen with the user | `references/preflight.md` |
| 2. Interview | Scope, examples, rejected alternatives and invariants fixed from real code | `references/interview.md` |
| 3. Specification | Project design reviewed and approved; where the project keeps decision records, every settled decision a `Proposed` record citing it | `references/interview.md` |
| 4. Plan | Waves of micro-tasks compiled, checked by the helper, reviewed as a `plan` | `references/waves.md` |
| 5. Execution | Tasks specialist-written, verified and light-reviewed before atomic commit; waves reviewed and sealed | `references/waves.md`, `references/worker-brief.md` |
| 6. Candidate | The whole candidate reviewed with shape `branch`; blocking findings repaired in a bounded wave | `references/verify.md` |
| 7. Integration | Merge, record verified, map and knowledge realigned, workspace closed | `references/finish.md`, `references/realign.md` |

When the user wants only the plan, the cycle stops after phase 4 with the
plan approved; `/daodan:continue-task` resumes it
from its first unsealed wave. A bugfix with a reproduction test follows `references/repair.md`, which
shortens phases 2 to 4 and keeps the rest.

Rules that hold across phases:

- Discover existing code, tests, decisions and instructions before adding a
  representation. Prefer an implementation that exists.
- Conflicting requirements become concrete alternatives for the user; the
  current code is never promoted into the requirement.
- Preserve preexisting edits and other sessions' work. Recovery restores the
  owned pre-phase state, never `HEAD~1`.
- Before scaffolding a project without application code, approve its specification through
  `references/brainstorm.md`. Initialize a missing loop through `references/init.md`.
- Severe evidenced defects and broken entry paths come before cosmetic work.
- A plan or a diff without verification is not completed development.
