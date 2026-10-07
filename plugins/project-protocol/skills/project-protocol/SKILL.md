---
name: project-protocol
description: >
  Canonical run identity, snapshot bindings, delivery and verification accounting,
  authorization continuity and safe phase recovery for coordinated project work.
  Load before recording, resuming or closing a project intervention.
---

# Project protocol

## Ownership

A workflow may declare `[dispatch]` independently of its phase graph: `roles`
lists exact local or `provider/role` identities, `isolated` requires a separate
context, and boolean `inline_workers` binds only this plugin's canonical
`isolated-worker`. That binding requires a hard provider dependency and isolation.
It accepts a concrete task and report contract without exposing other registry
roles. Loaded methods retain their domain prompts; metadata carries no prompt.

This leaf owns operational records and their validation. Canonical contracts are
`${CLAUDE_PLUGIN_ROOT}/contracts/work.toml` and
`${CLAUDE_PLUGIN_ROOT}/contracts/project-result.toml`. Consumers declare those
exports by provider/path in `contract.shared_schemas`; they never copy them.
Review findings, severity and native dispositions remain the domain owner's
payload. A common result references the original report, its hash, its author,
its input snapshot and the adapter that interpreted it.

Keep operational state under a dedicated root inside the project, default
`.daodan/runs/<id>/`. The root sentinel is `.daodan-root`. A coordinator owns
`work.json` and `result.json`; each dispatched worker owns one declared report.
Never place run state, temporary paths or task progress in durable instructions.

## Run-state interface

Use `python "${CLAUDE_PLUGIN_ROOT}/skills/project-protocol/scripts/run_state.py"`:

```text
init --project ROOT --payload INPUT.json [--out INTERNAL_ROOT] [--run-id ID]
show --project ROOT --run-id ID [--out INTERNAL_ROOT]
update --project ROOT --run-id ID --expected-revision N --payload PATCH.json
validate --project ROOT --run-id ID [--out INTERNAL_ROOT] [--current] [--result RUN_RESULT.json]
resume --project ROOT --run-id ID --payload CONTEXT.json [--out INTERNAL_ROOT]
snapshot --project ROOT --payload CONTEXT.json [--out INTERNAL_ROOT]
```

Pass `--out` consistently after a custom root is selected. Init requires
`operation`, `objective`, `scope` (`paths` and optional `focus`/`excluded`),
`authorizations` and `budget`. It defaults phases, plan, deliveries and gates to
empty containers. Declare every expected worker in `deliveries` before dispatch
and every known mandatory check in `required_gates` before execution. Add newly
discovered checks before executing them; required gate identifiers are append-only.
Snapshot hashes
include dirty and untracked scoped inputs, never the run's own output root.

Update recursively merges objects and replaces arrays. Identity, original scope,
authorizations and baseline project binding are immutable. Completed runs are immutable.
A revision mismatch writes nothing. The helper captures the current `candidate`
binding on each update. `snapshot` returns a candidate project binding for a gate
after source changes. A gate carries `status`, the candidate snapshot digest,
candidate `head` when present, and evidence identifying the command or remote job.
Remote evidence also identifies the exact source revision and job attempt. A green
job for an earlier candidate is not the gate for this one.
Remote-only checks require a nonempty Git revision and `head_matches_snapshot`
true in the captured candidate. The helper compares scoped bytes with actual
HEAD blobs and detects untracked inputs, including ignored input files. Index
flags cannot hide a content change from that comparison. A job for
HEAD cannot verify uncommitted edits. Without this binding, run a check against
the actual local candidate or record the remote check as unavailable.
The comparison is byte-exact. A checkout with transformed line endings needs
local verification. Snapshots include regular-file kind and executable state
where the filesystem supports it; HEAD symlink blobs cannot attest a regular file.

Init, show and update emit the full JSON record. Validate emits validity and
identity. `validate --result` also checks the canonical envelope against this exact
work revision, candidate snapshot, delivery ledger and required check statuses.
Plain validation checks a historical record. Add `--current` before accepting a
result as verification of the present project; it rejects changed scoped inputs
or workspace identity.
Resume requires current `authorizations`; an optional supplied scope must
equal the recorded scope. It verifies project/worktree/HEAD and current candidate
snapshot, returns the record plus pending phases and deliveries, and changes no
file. New input or a broader authorization requires a new run, never rebinding a
completed report. Record interruption reason and phase immediately when possible.

## State and completion

Read the values and allowed transitions from the canonical work contract. Run
states are `in_progress`, `complete`; phase states are `pending`, `in_progress`,
`complete`, `skipped`; worker deliveries are `pending`, `running`, `delivered`,
`failed`. A failed worker may be retried with the failure retained in its attempt
history. Record why a phase is skipped. Complete means every declared phase is
closed, every expected delivery is delivered, no interruption remains and every
required gate passed for the current candidate with evidence. Failed or unavailable
checks remain explicit; a partial report does not authorize marking the run complete.
Every delivered worker requires an `output` naming an existing report inside
its owned run, including workers with no findings. Coordinator records and locks
do not count as worker reports.

Worker status and test outcome are different facts. A worker that honestly reports
a product defect can deliver successfully. Accounting for a worker failure does
not turn it into a successful delivery. Report the uncovered dimension.

## Baseline, gate and recovery

Before a mutating phase, verify exclusive ownership of the working tree, including
its other active sessions. Bulk removal requires an isolated owned worktree; a clean
status alone is insufficient. Record the authorized paths, starting HEAD, full scoped
snapshot, preexisting tracked edits and untracked files. Resolve build and test gates
from the project's instructions. If the baseline is failing, unavailable or forbidden
locally without a correlated remote alternative, leave the phase open.

Record `pre_phase_sha` immediately before each phase. Save enough pre-phase file
state to recover precisely that phase's owned edits. Apply, capture candidate,
execute the declared gates, then commit only when authorized. Record the commit and
the candidate it verifies. Do not derive a rollback target from `HEAD~1`.

On failure before commit, restore only the phase's owned edits to their captured
pre-phase values. Preserve the preceding successful phase and all preexisting or
foreign files. A reset to `pre_phase_sha` is allowed only in an exclusively owned,
isolated worktree with a proven clean pre-phase baseline and no foreign changes;
otherwise use path-scoped restoration or leave recovery to the user with the exact
conflict. Never run `git clean`, broad checkout or hard reset in a shared checkout.
An already published phase is undone by an authorized revert, never history rewrite.

The run-state helper records and validates the procedure; it does not execute Git
rollback, dispatch workers, enforce their token limits or confine their other tools.
Its own writes are confined mechanically. Tool confinement elsewhere is an explicit
prompt obligation until an adapter has a measured runtime mechanism.

## Compiler dispatch resources

Cross-plugin role bindings resolve against the kernel registry and mandatory
dependencies. Named-agent hosts receive the owner-qualified native identity. Inline
adapters receive only the external bodies actually declared in the phase graph,
under generated `contracts/dispatch/<owner>/<role>.md`. Each resource identifies its
canonical owner, version and source hash; these are unregistered compiler output,
not hand-authored copies or new roles. Host drift checks cover canonical edits.
Resolve any owner-relative helper from that owner's installed skill, rather than
mistaking the coordinator's root for the role's root.
