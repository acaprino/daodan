# Operations

## State ownership

SQLite stores current state and append-only events in the same immediate transaction. A claim creates the attempt before dispatch. A completion stores artifact metadata, delivery and job transition atomically. Artifact bytes are immutable in the content-addressed store.

The initial executor is sequential. A second local process cannot claim a job while another attempt is reserved or running. Parallel and distributed execution require a separate verified adapter.

The default runtime home is `.process-controller`. If only the legacy `.deadly-brain` home is present, it is used as a compatibility fallback.

## Attempt lifecycle

```text
pending → reserved → running → completing → delivered
                    │             ├────────→ failed → new attempt, if budget remains
                    │             └────────→ running after an ordinary aborted completion
reserved → revoked → pending
running/completing → unknown → blocked run → explicit failed reconciliation
```

Completion is admitted before artifact ingestion or Git effects. The admission records holder, event and request. Concurrent duplicates cannot repeat those effects. An ordinary failure appends `delivery.aborted` and permits a bounded retry; a crash leaves the attempt uncertain. Internal event IDs use a reserved namespace, so a client delivery cannot block run completion.

`resume` does not infer a result. Reserved work is revoked; running work becomes unknown and stops new admissions. `retry-attempt --confirm-stopped` records the user's reconciliation before another attempt can start.

## Completion

A run finishes only when every declared job is succeeded. Attempt exhaustion, deadline exhaustion, unknown worker state and unfinished obligations prevent completion. A supervisor's `FINISH` recommendation does not close the run; `finish` performs its own check.

A run is bound to the workspace recorded at admission. Packets, command execution, completion, resume and finish reject a different workspace instead of silently importing artifacts or running work from another directory.

## Logs and bounded output

Command stdout and stderr go to per-attempt log files, not into the journal or CLI result. Status, frontier, packets and event pages return bounded views. Artifact bodies are read through their content path only by consumers that need them.

## Git safety

Commit support requires a clean work-tree at run admission and the workspace must be the work-tree root, so scoped paths and staged paths use the same coordinates. The runtime home must be ignored by that work-tree or live outside it, otherwise the home itself makes the baseline dirty. A created SHA is recorded before final delivery, allowing an ordinary database retry to avoid a duplicate commit.

If Git succeeds but `rev-parse` or SHA persistence fails, the attempt becomes `unknown` and the run blocks instead of retrying blindly. Reconcile with `--commit-sha` after inspecting HEAD, or use `--discard-commit-outcome` only after verifying that no commit exists. The first path resumes the same completion without another commit; the second opens a new attempt. Tests use fake Git runners and do not mutate a real repository. Live Git verification, behavior with preexisting staged changes and host-specific work-tree handling remain separate operational checks. The engine never runs push, reset, rebase or clean.
