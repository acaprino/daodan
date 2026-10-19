---
name: review-quality-gates
description: >
  Verification panel, completeness critic, pipeline conventions and shared-context provenance rules for multi-reviewer consolidation.
  TRIGGER WHEN: running /senior-review:team-review or /senior-review:code-review quality gates, or consolidating findings from parallel reviewers.
---


## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

# Review Quality Gates

Gates and consolidation rules shared by every review variant. This core holds
what every consumer needs; the two procedures that only one step uses are units
loaded by that step.

## Load map

| Step | Read inside this skill |
|---|---|
| Any review, any role | this file: provenance rule, reviewer conventions, evidence classes, delivery gate |
| Preparing or dispatching reviewers with shared context | `references/context-sharing.md`: context artifacts, anchor routing per dimension, metrics, raw mode |
| Consolidation | `references/verification-panel.md`: the four lenses, their gating, the cost guard and the completeness critic |
| Writing a lens, critic or reviewer brief | `references/panel-and-critic-prompts.md` |
| `/code-review` agent dispatch templates and Codebase Map context injection | `references/code-review-agents.md` |
| `/code-review` native output and optional HTML view | `references/code-review-output.md` |
| `/code-review --fix` and `--commit` remediation loop | `references/code-review-fix-loop.md` |

Lens 0 uses the declared `senior-review:premise-auditor` binding. Lenses 1 to 3,
the critic and any inline brief use only the declared
`project-protocol:isolated-worker` binding through the consuming workflow's host
harness, inheriting the session model.

## Shared-Context Provenance Rule

> **Evidence derived from a shared artifact cannot independently corroborate the claims contained in that same artifact. N reviewers agreeing on a premise they were all given is one observation, not N.**

Three consequences bind every gate below:
1. A reviewer that consumed a claim from the Codebase Map output or the interconnect map has not verified that claim. It must re-derive the claim independently before standing a finding on it.
2. Concordance between reviewers who share a premise is an **echo**. It raises no confidence and no severity. Consolidation reports it as such.
3. No metric may reward agreement with a shared artifact. Utilization of the map is an operational number, never a quality signal.

## Reviewer Pipeline Conventions

Every Phase 2 reviewer carries four rules in its system prompt:
- **Scope budget**: stop after ~15 file reads without a finding and return a "scope-off-topic" report.
- **No-findings protocol**: "examined X, Y, Z: no issues" is a valid Phase 3 input, not a failure.
- **Cross-Reviewer Notes**: observations belonging to other dimensions go in `## Cross-Reviewer Notes` for Phase 3 routing.
- **Interconnect anchor citation**: reviewers cite map anchors when applicable. Findings that cite map anchors feed the map utilization rate, an operational measure of map consumption, not a quality signal. The quality signals that matter are in `references/context-sharing.md`, section `### Metrics`.

## Evidence Classes

Every finding labels how its decisive evidence was obtained, strongest first:
- **`reproduced`**: a test or run showed the defect, passing on the base and failing on the candidate, or the reverse for a fix (state the command and the scratch path).
- **`tool-reported`**: a tool in the evidence pack reported it verbatim (`references/candidate-grounding.md` in `senior-review:review-preparation`).
- **`measured`**: obtained from a harness, simulation or real logs/metrics (state method in one line; build any harness outside the work tree and delete afterwards).
- **`derived`**: computed by reading code (a hypothesis, not a fact; an unlabeled finding defaults to `derived`).

Consequences:
1. A `derived` number alone cannot justify **Critical** severity (measure it or cap at High).
2. A finding cannot be closed as acceptable ("bounded", "low traffic") on a `derived` number alone, nor without answering **what the user or operator sees, and when** ("None (silent)" is a severity escalator, never a mitigation).
3. Lens 2 actively checks whether claimed rates/costs survive actual control flow (deduplication, caps, phase transitions).
4. Lens 1 may reproduce. When the brief grants a disposable workspace owned by the run and names a test runner, the lens writes a minimal test at the scratch path the brief names, runs it on the base and on the candidate, records both outcomes, and removes the file unless the caller adopts it as regression protection. A reproduction that fails to show the defect is counterevidence, recorded as such. Without that grant, the lens reads and reasons, and the class stays as the reviewer declared it.

## Delivery Gate

1. **Every reviewer delivers or declares:** Consolidation does not start until every spawned reviewer has produced either its findings file or an explicit no-findings report. An idle reviewer receives one nudge; if still silent, salvage partial output as `[undelivered -- collected by orchestrator]` and mark the dimension **degraded** (or **not delivered** if empty), never clean.
2. **The work tree is left as found:** Compare the complete pre-review workspace snapshot with the final state. A new file in status is not proof the review owns it. Workers keep an explicit manifest of files they created, with original absence and final hashes; foreign or changed files are preserved and reported. Keep probes inside the owned run root. Before removing an unchanged owned temporary artifact, preserve its conditions, commands, outcomes, errors and limitations in the native report and verify every remaining evidence reference still resolves. Preserve unresolved evidence and resume data. Broad cleanup or Git clean is forbidden. Persistent run retention belongs to the caller's consolidate path; the review returns the owned manifest and report, rather than deleting arbitrary repository residue on status alone.
