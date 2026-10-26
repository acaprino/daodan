---
name: worktree-method
description: >
  Manage Git task workspaces through the external Worktrunk CLI: create or resume
  under .daodan, list every worktree, annotate descriptions and tags, prepare safe
  lifecycle handoffs and check supported upstream releases.
  TRIGGER WHEN: starting or resuming an isolated task, listing or annotating worktrees,
  preparing their integration or cleanup, or updating Worktrunk compatibility.
  DO NOT TRIGGER WHEN: reviewing code correctness or deciding whether a task is complete;
  those decisions remain with the existing review and delivery owners.
---

# Task workspaces

Load skill `work-controller:work-record` for working discipline, task identity, grants,
questions and evidence. Git owns actual branches, commits and worktree paths;
this method owns workspace annotations and the external CLI boundary. It does
not introduce another scheduler, reviewer or completion gate owner.

Worktrunk is a separately installed executable. Its source and host plugins are
not copied into this package. Read `references/upstream.md` before provisioning
or updating it; `references/upstream.json` records the supported release.

## Entry and outputs

Interpret the caller's free text as list, annotate, create/resume, lifecycle
handoff or upstream update. A plain inventory is read-only and opens no task.
Use the owning helper with an explicit project directory:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/worktree-method/scripts/workspaces.py" --project ROOT list
python "${CLAUDE_PLUGIN_ROOT}/skills/worktree-method/scripts/workspaces.py" --project ROOT annotate --path PATH --description TEXT --tag TAG
python "${CLAUDE_PLUGIN_ROOT}/skills/worktree-method/scripts/workspaces.py" --project ROOT create --task-id ID --kind fix --slug login-timeout --base REV --prefix codex --description TEXT
```

Check the helper's help for optional arguments. Pass values as separate process
arguments; never interpolate free text into shell commands. Its JSON output is
the data contract, not text to execute. Preserve errors and incomplete creation.

Display at most the useful inventory columns: description, tags, branch, task
and path. Join the existing agenda when task phase/holder is needed; do not
infer completion from a clean checkout. Include external and detached worktrees.
Missing catalog entries remain unannotated, not hidden. Metadata for a removed
checkout remains visible as stale information rather than silently recreated.
Descriptions describe the task; a generated diff summary must not replace them.
Tags are labels, not Git tags. For additions or removals, use repeated
`--add-tag` or `--remove-tag` arguments; the helper applies those changes to the
latest set under its catalog lock. Repeated `--tag` arguments explicitly replace
the whole set; `--clear-tags` clears it. Do not combine replacement or clearing
with additions/removals. Report unavailable remote status as unknown.

## Create or resume

1. Resolve the user's task, approved workspace mode, base revision and naming
   policy. Default branch prefix is `task`; an active host or project may require
   another prefix (for example `codex`). Use a stable task ID and a short slug;
   changing a description never renames a branch or checkout.
2. Resolve the main checkout through Git's common directory. New worktrees live
   only in its `.daodan/worktrees/`; annotations live in `.daodan/worktrees.json`.
   Require `.daodan` to be ignored before creation. If it is not, prepare the
   scoped ignore change under the current task grant and recheck. Never create
   nested homes from a linked worktree. Bare repositories without a main checkout
   need a separately specified home and are unsupported by this helper.
3. Probe the supported executable before creation. The helper reserves the task
   identity and invokes Worktrunk with its lifecycle hooks and native checkout
   hooks disabled for that invocation. A retry reconciles
   the actual checkout's repository, worktree registration, branch and HEAD;
   mismatches stop without deleting or overwriting.
   Existing foreign worktrees may be listed/annotated; annotation is not ownership
   and does not authorize their reuse, mutation or removal.
4. Bind the host's actual execution directory and permitted workspace to the
   returned path before dispatch. A successful shell `cd` is not proof of session
   binding. If the host cannot use the requested checkout, keep it recoverable
   and report that capability gap. Never silently work in the main checkout.
5. Execute only the task's trusted, authorized setup. Record setup separately
   from checkout creation and wait for required setup to finish. Do not copy all
   ignored files, secrets, dependency environments or mutable caches implicitly.

The helper confines its own catalog and creation paths; it does not enforce
every later agent tool operation. Do not claim a host sandbox from this check.
Main-home discovery and Git metadata are shared; Worktrunk's internal logs and
state can live in the shared Git directory, outside `.daodan`.

## Integration and cleanup

Read `references/lifecycle.md` when the delivery owner requests these phases.
Return paths, source/target identities and metadata to the caller. The caller
keeps its existing authorizations, candidate-bound review and result protocol.
Never call bare `wt merge`, install global lifecycle hooks or remove a checkout
on agent/session exit. Preserve original task commits and the run's immutable
review receipts across squash and cleanup.

## Upstream updates

Read `references/upstream.md`. A release check is read-only; installation,
compatibility testing and adoption are distinct outcomes. Unsupported binaries
fail with an explicit recovery path rather than falling back to unrelated tools.
