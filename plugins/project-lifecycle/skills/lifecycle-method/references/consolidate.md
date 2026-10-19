# Consolidate (phase 7, and the standalone realignment)

Consolidate closes a task: it integrates the candidate when the user merges
through the cycle, promotes the decision record, realigns the knowledge that
describes the project, and disposes of the run's own output. Run alone after
a merge made outside the cycle, it performs the same realignment on the
current head.

## Integration

1. Confirm the candidate's stage D result validates against the current
   project (`validate --current`). A changed candidate returns to verify.
2. With merge authorization: merge the task branch into the base branch with
   a merge commit, or fast-forward when the user asked for it; remove the
   worktree created in phase 1 and its branch only after the merge is
   recorded. Without authorization: leave the branch, record the exact merge
   command, and stop before the steps below until the merge exists.
3. Record the merged commit as `merged_sha`.

## Realignment, in this order

1. **Record.** Load `project-knowledge:adr-method` and run `promote` for the
   run's proposed record with `merged_sha`. Superseded records are marked by
   the helper in the same transaction. A task that produced no record skips
   this step and says so.
2. **Map.** Load `codebase-map:map-method` and run the incremental update of
   the bound run against `merged_sha`: changed files and symbols are
   re-derived, unaffected claims carried, the impact packet of the task's
   symbols refreshed. Then the concept index of `abstraction-architect`,
   through its skill, for the task's scope.
3. **Documentation.** Run `project-knowledge:project-knowledge` drift audit on
   the documents that cite the changed paths and symbols, and apply the
   authorized corrections; `project-knowledge:readme-craft` when the README
   cites them.
4. **Instructions.** Run `project-knowledge:instructions-method` to regenerate
   the loop block from the run record and the record index: commands, active
   records, workspace convention. Nothing outside the markers changes.
5. **Head.** Record `last_synced` as `merged_sha` in the run, and compare it
   with `HEAD`: a difference means another commit landed meanwhile, and the
   map update runs once more for that delta before the run closes.

A step that cannot run (a missing runner, an unauthorized edit) stays open
with its reason; the run does not close on it silently.

## Evidence

Reduce experiments and run output into verified knowledge before disposing
of data. For each attempt preserve goal, source snapshot, conditions, exact
command, inputs, outcome, errors, measurements, decision, limits and
reproduction instructions. Compare the proposed summary with the original
evidence, failed attempts included; contradictory results remain visible.
Past results do not replace executable regression tests. Durable conclusions
go through project-knowledge; temporary status stays in the run, never in
`AGENTS.md` or `CLAUDE.md`.

## Retention records

Write artifacts.json: schema daodan/artifacts/v1, run_id and artifacts entries
{path, owned_by, sha256, classification, status, reproduce}. Paths are relative to
this run and files exclusively created/owned by this run. Concluded disposable
classes are reproducible-output and completed-output; reproduction conditions are
mandatory for the former. Unknown ownership, cache, resume data and unresolved
evidence remain retained.

Write summary.json: schema daodan/evidence-summary/v1, run_id, summary,
verification {status:verified, by:<coordinator>}, retained_evidence [{path,sha256}],
required_artifacts and unresolved. Semantic verification requires reading sources;
writing a verified flag is not the verification. Keep a nonempty evidence subset.
Outstanding evidence blocks retention until explicitly resolved and retained.

Run the installed helper:
python "${CLAUDE_PLUGIN_ROOT}/skills/lifecycle-method/scripts/artifacts.py" plan --run RUN --manifest artifacts.json --report summary.json
This writes retention-plan.json. Show every proposed path/reason and potential
byte total; default planning makes no removal.

After authorization, apply quarantine with:
python "${CLAUDE_PLUGIN_ROOT}/skills/lifecycle-method/scripts/artifacts.py" apply --run RUN --plan retention-plan.json
This moves data within the run and reports zero bytes deleted.

Permanent deletion is a separate explicit --purge grant, not implied by --fix.
Write authorization.json {run_id, operation:purge, paths:[exact relative paths],
source:{kind:user,reference:<actual permission>}} and invoke apply with --purge
--authorization authorization.json. Never fabricate permission from a generic
cleanup request. Only concluded owned outputs in the original manifest are eligible.

The helper rejects traversal, symlinks/reparse points, hardlinks, changed files,
changed summary/evidence, unresolved references and quarantine collisions. It
writes a receipt before mutation and resumes prepared operations idempotently.
A stale retention lock requires proving the owning process stopped before recovery;
do not delete a live session's lock. Artifact fingerprints and confinement are
mechanical; truth of the summary and of human permission remains the coordinator's
responsibility.

repo-hygiene:repo-hygiene handles separate filesystem/Git hygiene and preserves
untracked quarantine. It does not interpret lifecycle state or purge its artifacts.
Record content bytes moved/deleted, retained evidence, result and remaining limits.
Measure filesystem free-space changes separately when needed; deleted file sizes
do not prove physical space recovered on a compressed or concurrently used volume.

