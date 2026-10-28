# Lock-free work ownership

Date: 2026-10-28. Status: draft for approval, revision 4 (after reviews
spec-review-1 to spec-review-3; revision 4 fixes the Medium and Low findings of spec-review-3, which passed revision 3).

## Intent

A session that crashes, is compacted or forgets its identity must never leave work
that other sessions cannot continue. Today Daodan binds work to the identity of
the session that last touched it, with no expiry and no liveness check, so a dead
session blocks every other session until the user confirms by hand that it closed.

User decisions (2026-10-28, chat):

- UD-1: tasks carry **no lock**. Any session may resume any task. Safety comes
  from mechanisms that already exist: the record revision refuses a write based
  on stale data, and a short operating-system lock serializes each single write
  and is released by the OS when its process exits.
- UD-2: worktree-manager keeps a **registry of worktrees** with state, history
  and cleanup, so isolation lives where files are edited (one task, one
  worktree) instead of in a session lock.
- UD-3: one specification, **two stages**. Stage 1 removes the locks (S-1 to
  S-5) and can be committed alone. Stage 2 builds the registry (S-6 to S-8).
- UD-4: history is **dates only**, so the local catalog stays small: each entry
  keeps its creation and removal dates, and cleanup can drop a removed entry
  30 days after removal. Who did what stays in the agenda and the work records.
- UD-5: the uncommitted "workspace reservation" code in the working tree
  (`run_state.py`, `work.toml`, `tests/test_work_record.py`, about 400 lines,
  `release-workspace`/`acquire-workspace`) belongs to another author and stays
  untouched. Its owner decides its future in the light of UD-1. Implementation
  starts from the last commit, in a separate checkout.

Line numbers in `run_state.py` cite the last commit (`5c282c279`), because the
working tree also holds that uncommitted work.

## Defects this replaces

| ID | Where | Behaviour today |
|---|---|---|
| D-1 | `plugins/work-controller/skills/work-record/scripts/run_state.py:1526-1556` (`plan_agenda`) | A task is writable only by the session in `holder` (`:1539-1540`). Every other session gets `Task X is held by session Y ... pass --take-over once the user confirms it is closed`. The session ID is free text chosen by the agent (`:1623`), so a session that picks a new ID after compaction is locked out of its own task. |
| D-2 | withdrawn in revision 3 (UD-5) | |
| D-3 | `work_controller/store.py:1153-1176` | A ticket in progress closes only for its holder (`ticket is not held by this session`); the frontier offers only pending tickets (`store.py:1137`), so a dead holder freezes the ticket and every ticket blocked by it. |
| D-4 | `work_controller/store.py:397-402`, `store.py:443-447` | `frontier` and `claim` return nothing while any attempt is reserved, including one whose lease (`expires_at`) has passed, and say nothing about why. Any session can recover with the process `resume` (`store.py:833`), but nothing points the coordinator to it. |
| D-5 | `codebase-map/.../retrieval.py:122`, `semantic_map.py:285`, `embedding_worker.py:174`, `worktree-manager/.../workspaces.py:199`, `project-delivery/.../frd_tool.py:105`, `adr_tool.py:258`, `delivery-method/scripts/artifacts.py:288` | The lock is the existence of a file created with `O_EXCL`. A crash leaves the file and every later run fails until someone deletes it (retrieval offers `break_lock`, `retrieval.py:288-290`; the others need a hand deletion). |

## Principle

1. Work is never owned by a session identity. A session identity is recorded only
   as information: who acted last, where, and when.
2. Mutual exclusion lasts only for one write, through an OS lock that the OS
   releases when the process exits. The existence of a file is never a lock.
3. Concurrent writers are reconciled by revision (compare and swap), never by
   refusing a session.
4. A time lease exists only where a worker may be running with side effects (the
   process runtime's attempts). Its recovery stays explicit, because only the
   coordinator knows whether a worker was dispatched.
5. Every on-disk format stays readable and writable by the previous release,
   because one agenda and one catalog are shared by sessions on five hosts that
   update at different times (Pi and OpenCode follow the release tag).

## Scope

### S-1 Work records and agenda (D-1)

- `plan_agenda` no longer refuses a write because another session acted on the task.
- Each agenda row gains `last_activity: {session, host, at}`, written on every
  write that carries `--session`. The schema stays `daodan/agenda/v1`.
- The row keeps `holder` and the new code always writes it as `null`. A previous
  release refuses a write only when `holder` names another session
  (`run_state.py:1540`), so a `null` holder never blocks it, and a holder that an
  older session sets is cleared by the next write of the new code. A previous
  release rebuilds the row without `last_activity` (`:1504-1523`); a row without
  it simply has no recent activity to report.
- `--session` is optional and informational. `--take-over` is accepted and
  ignored, with or without `--session` (the refusal at `run_state.py:1634-1635`
  goes), so bodies of the previous release keep working; it leaves the
  documentation.
- `resume` reads the agenda before any write and returns
  `recent_activity: {session, host, minutes_ago}` when the last activity came
  from a different session less than 15 minutes ago. The agent tells the user in
  one line; it neither blocks nor asks.
- The rule "one open loop task per branch" stays: it binds work to a branch, not
  to a session, and any session can now resume the open task.

### S-2 withdrawn in revision 3 (UD-5)

### S-3 Tickets (D-3)

- `ticket_close` drops the holder check. The evidence gates by kind stay unchanged
  (decision needs the user's answer, research needs evidence, execution needs a
  completed run).
- `ticket_claim` on a ticket in progress under another holder reassigns it
  without the frontier check (it passed that check when first claimed) and
  records `ticket.reassigned` with the previous holder, event ID
  `ticket-reassigned:<ticket>:<n>`, where `n` counts that ticket's
  reassignments, so the `UNIQUE (map_id, event_id)` constraint (`store.py:123`)
  holds.
- `map_status` (today counts and `next`, `store.py:1214-1217`) also lists the
  tickets in progress with holder and last update, so a coordinator can find a
  ticket left by a dead session without knowing its ID.

### S-4 Process attempts (D-4)

- No automatic revocation: `frontier` stays read-only (it backs the read-only
  MCP tool `process_frontier`, `mcp.py:98-102`, and the console), and a reserved
  attempt may already have a dispatched worker (`process-runtime.md:49-53`).
- `claim` and `drive`, when an attempt in `reserved`, `running` or `completing`
  is what blocks them (`store.py:443-447`), return
  `blocking_attempts: [{id, status, holder, expired}]`: `claim` beside its null
  packet (`cli.py:286`), `drive` beside its `active` result (`engine.py:315-316`).
  `expired` uses the rule of `supervision.py:49`. `frontier` keeps its return
  shape; the read-only `process_supervise` view already reports expiry.
- `references/process-runtime.md` tells the coordinator: when the reported
  attempt's worker is known to be gone, any session runs the process `resume`,
  which revokes reserved attempts and conservatively marks started ones
  `unknown` (`store.py:833-871`); `resolve_unknown` follows with confirmation.
- The attempt's holder check (`store.py:515`, `engine.py:111`) stays: it binds one
  attempt to the worker that started it, not a task to a session.

### S-5 Short write locks (D-5)

- No lock is the existence of a file, and no lock creates a file in a tracked
  directory.
- Sites whose state sits in a dot directory (`retrieval.py`, `semantic_map.py`,
  `embedding_worker.py` in `.codebase-map/`; `workspaces.py`, `artifacts.py` in
  `.daodan/`) take an OS lock on one byte at offset 0 of a sidecar named
  `<old lock name>.oslock`, never deleted, the pattern of `run_state.py:1560`
  (`writer_lock`): `msvcrt.locking(LK_NBLCK)` on Windows, `fcntl.flock` on POSIX
  (not `lockf`, whose locks any `close()` of the file cancels), polled in the
  script's own loop with a deadline, then a clear "retry" error. The data file
  is never locked, so readers are not blocked [R-1, R-2]. The holder touches the
  sidecar's modification time on acquire. `.retention.oslock` joins `CONTROL`
  (`artifacts.py:17`), so retention never selects it.
- Sites whose data lives in a tracked directory (`adr_tool.py` in `docs/adr/`,
  `frd_tool.py` in `docs/frd/`) lock without creating a file, the pattern of
  `codebase-map/.../confinement.py:26-82`: a Windows named mutex keyed by the
  SHA-256 of the directory's canonical path, `fcntl.flock` on the directory's
  descriptor on POSIX, the key being the `normcase` path as in
  `confinement.py:45`. Under that lock each tool deletes its own temporaries
  (`.<name>.<uuid>.tmp`, `adr_tool.py:274-284`, `frd_tool.py:119-129`) whose
  modification time is more than one hour old: a live writer's temporary lasts
  milliseconds, so only a killed writer's is old enough, and a file still open
  on Windows is skipped and retried on the next write. Apart from that sweep, a
  refused write leaves the directory unchanged.
- A lock file of the previous release (old name) is never read as held and never
  deleted. The user may delete leftovers.
- Retrieval keeps its contract (`index_state` `lock`, `lock_age_s`;
  `ensure_index(break_lock)`, exposed as MCP `codebase_map_index` and on the CLI).
  `index_state` probes only an existing sidecar, never creating one, and reports
  `lock` with `lock_age_s` only when the non-blocking probe finds it held.
  `break_lock` never removes a lock: it takes the lock, removes leftover
  `.retrieval-*.sqlite` temporaries while holding it (also when the index is
  fresh, so the early return at `retrieval.py:282-283` no longer skips it), and
  reports `held` when the lock is taken by a live process.
- `atomic_write` and the other `os.replace` sites retry a Windows
  `PermissionError` (target briefly open by a reader) with bounded backoff
  before failing [R-3].
- `workspaces.py:207-208` ("A stale lock is never stolen") is reversed by this
  decision: with an OS lock there is nothing to steal.
- No dependency is added: the standard library covers exclusive locking on one
  host. `filelock` (MIT, no dependencies, release 4.2.4 of 2026-10-19) is the
  option if leases or shared locks are ever needed [R-4]. Plugins cannot import
  each other's scripts, so each owning skill carries its own copy of the lock
  function; a repository test asserts that the copies stay identical.
- Supported on local filesystems only; OS locks do not exclude across NFS or
  SMB clients [R-1].

### S-6 Registry state, derived at read time (stage 2)

The registry stays `.daodan/worktrees.json`, owned by worktree-manager
(`workspaces.py`), schema `daodan/worktrees/v1`. Git stays the inventory
(`workspaces.py:66-90`); the catalog keeps only facts Git cannot derive (task
link, description, tags, dates) [W-1]. `list` adds a `state` block per
worktree, computed on every read and never stored, because a stored state goes
stale exactly as the lock did:

| Field | Source |
|---|---|
| `presence`: `present`, `missing`, `prunable` | Git inventory (`prunable`, `workspaces.py:82-83`) and the filesystem |
| `changes`: staged, modified, untracked, conflicted counts | `git -C <path> status --porcelain=v2 -z` |
| `locked` | Git inventory (`locked`, set by `git worktree lock`) |
| `integration`: a reason, `not_integrated` or `unknown` | the pinned Worktrunk `list --format=json`, schema 2, admitted by `worktrunk_runtime.py:173-197`: `default_branch.integration.reason` (`same_commit`, `ancestor`, `no_added_changes`, `trees_match`, `merge_adds_nothing`, `patch_id_match`), squash merges included [W-2]. `unknown` when Worktrunk is missing or unsupported; `list` still works on Git alone |
| `task`: `open`, `complete`, `unlinked` | agenda rows with `loop: true` (`run_state.py:1514`) whose `worktree` (`:1516`), normalized with the catalog's `key()` (`workspaces.py:46-47`), equals the entry's key, or whose `branch` equals the entry's branch: `open` if any of them is open, `complete` if all are complete, `unlinked` if none exists. Review, map and other non-loop runs never count |
| `last_activity` | the latest `last_activity` among those rows |
| `label` | `active` (open task, activity in the last 15 minutes), `idle` (open task, older or no recorded activity), `concluded` (task complete and an integration reason, `same_commit` included, so an analysis task without commits concludes), `unintegrated` (task complete, `not_integrated`), `unknown` (task complete, integration `unknown`), `unlinked`, `missing` (entry without checkout and without `removed_at`), `removed` (entry with `removed_at`), `foreign` (not managed) |

Preflight chooses the run ID before creating the worktree and passes it as
`--task-id`, so new entries also carry the link by identity; the agenda join
stays the authority.

### S-7 Dates (stage 2)

- Each entry gains optional `created_at` (written by `create`) and `removed_at`
  (written by `cleanup --apply`). Entries created before this change show
  `created_at` as unknown.
- The schema stays `v1`: the previous release validates only named fields
  (`workspaces.py:163-179`) and writes back the loaded entries, so it preserves
  added keys.
- An entry with `removed_at` stays listed with label `removed`, so a recent
  removal is visible. After 30 days `cleanup` lists it as `expire` (S-8).
- `create` refuses a task whose entry carries `removed_at`
  (`removed_workspace`), whatever the branch state, so a removed entry is never
  silently reused (`workspaces.py:315-337` would otherwise accept it once the
  branch is gone).
- Session activity is not copied into the catalog: the agenda owns it, the
  registry reads it.

### S-8 Cleanup (stage 2)

- `cleanup` without `--apply` is read-only and lists every managed worktree
  with one named outcome: `candidate`, or the first reason it is kept, in this
  order: `kept_main`, `kept_open_task`, `kept_unlinked`, `kept_unknown`,
  `kept_unintegrated`, `kept_dirty`, `kept_locked`, `kept_nested` [W-3, W-4].
  A candidate is managed, `concluded`, without changes, not locked, without a
  nested worktree and not the main checkout.
- Ignored files inside a candidate are listed by path, because removal deletes
  them.
- Entries labelled `missing` are listed as `forget` candidates; entries
  `removed` more than 30 days ago are listed as `expire`. Both drop only catalog
  metadata and touch no file.
- `cleanup --apply --authorization REF` takes `--path P` (repeatable) for the
  named `candidate` and `forget` entries, and `--expire` for every `expire`
  entry at that moment; it acts on nothing else.
- For each named candidate, `--apply` rechecks every condition at that moment
  (an outcome changed since the listing becomes `kept_raced`), runs
  `wt remove <branch> --no-delete-branch --no-hooks --foreground --format=json`,
  then verifies the Git inventory and the filesystem before writing
  `removed_at` [W-5]. `worktrunk_runtime.py` admits exactly that form in
  addition to `list` and `switch`; `-f`, `-D` and `--reap` stay refused. Without
  a supported Worktrunk, `--apply` refuses removals; `forget` and `expire` still
  apply.
- Branches stay. Deleting a branch is a separate choice and never forced.
- The agent shows the list once and records the user's choice as `REF`,
  following `lifecycle.md:69-87`.

### Documentation

Update every body that describes the old behaviour:

- work-controller: `work-record/SKILL.md:68` (writes require `--session`) and
  `:93-95`; `references/process-runtime.md:49-53` (expired reservations and
  `resume`).
- project-delivery: `delivery-method/references/continue.md:6-19`, `finish.md:7`,
  `preflight.md:37` (holder reuse rule) and `:45-46` (run ID before creation),
  `retention.md:52`, `status.md:8-10`, `sync.md:18`;
  `frd-method/references/frd-schema.md:123` and the docstrings at
  `adr_tool.py:35-36` and `frd_tool.py:20-21` (`.adr-lock`, `.frd-lock`).
- worktree-manager: `worktree-method/SKILL.md:40-51`,
  `references/lifecycle.md:75-80` (holder and "no active session" become
  `last_activity` and the 15-minute window).
- codebase-map: `map-method/references/mcp.md:83`, `references/locate.md:20`,
  the `break_lock` descriptions at `mcp_server.py:109` and `snapshot.py:3416`,
  and at `retrieval.py:230` ("without touching it"), `:277-279` and `:306`.
- daodan: `workflows/show-status.md:3` ("holder").
- Repository: `CLAUDE.md:98` ("branch and holder"), then
  `scripts/sync_codex_instructions.py` for `AGENTS.md`, and the generated docs
  through `scripts/sync_plugin_docs.py`.

## Non-goals

- No lock replaces the removed one: no lease, heartbeat or PID check on tasks.
- No change to grants, approvals, gates, questions or the revision rule.
- No change to `confinement.py`, `writer_lock`, `science_storage.py` or the
  codebase-map registry lock: they already use OS locks.
- No schema version change for agenda, catalog or work records.
- No change to the uncommitted workspace reservation work (UD-5).
- No restore of a removed worktree: `create` for its task keeps today's refusal.
- No abandon status for open tasks (see O-1).

## Invariants

- INV-1: No write to a work record, the agenda or a ticket is refused because of
  the identity of the session making it. Process attempts keep their per-attempt
  holder (S-4).
- INV-2: A write computed from a stale record revision never lands (existing
  `--expected-revision` rule, unchanged).
- INV-3: Two simultaneous writes of the new release to the same record, catalog,
  index or decision directory are serialized; neither is lost or interleaved.
  Mixed releases: A-5.
- INV-4: No lock left by a killed process blocks a later process. An interrupted
  worktree creation keeps its existing recovery: a retry reconciles, a mismatch
  stops without deleting (`workspaces.py:316-336`).
- INV-5: Grants, approvals, gates, questions and run history stay append-only and
  unchanged by this redesign.
- INV-6: Existing records, agendas, catalogs and tickets stay readable and
  resumable, and files written by the new code stay readable and writable by the
  previous release.
- INV-7: Registry state is never stored. With the same Git state, agenda and
  clock, two reads return the same state.
- INV-8: Cleanup never removes the main checkout, a checkout of an open or
  unlinked task, a checkout with any change, a checkout whose branch is not
  integrated or whose integration is unknown, a foreign checkout or a worktree
  locked with `git worktree lock` (a lock the user set on purpose, which Git
  never expires [R-6]), and never deletes a branch.
- INV-9: Only `cleanup --apply` drops catalog entries, and only `missing` entries named
  by the user or entries removed more than 30 days ago.

## Examples

- EX-1 (nominal): session A works on task T, then crashes. Session B runs
  `resume` on T with its own `--session`: it succeeds, and the agenda shows B as
  last activity.
- EX-2 (boundary): A wrote T 5 minutes ago and B resumes T. `resume` succeeds and
  returns `recent_activity` with A and `minutes_ago: 5`; B tells the user once.
- EX-3 (rejection): A and B both read T at revision 7. A updates to revision 8. B's
  update with `--expected-revision 7` is refused with the existing
  `Record revision changed` error; B rereads and retries.
- EX-4 (compaction): session A continues after compaction with a new ID A2. Its
  writes succeed; nothing asks for confirmation.
- EX-5 (mixed releases): a session on the new release writes T. A session on the
  previous release then writes T with another session ID and succeeds, because
  the row's `holder` is `null`.
- EX-6 (crash): `adr_tool.py` is killed while writing and leaves a temporary.
  The next write succeeds, and afterwards `git status` shows no new file in
  `docs/adr/` besides the intended record.
- EX-7 (ticket): A claims ticket K and dies. B claims K (event
  `ticket.reassigned`) and closes it with the required evidence.
- EX-8 (attempt): session A starts an attempt and crashes. B's `claim` returns
  no packet and `blocking_attempts` with that attempt, `running` and, once its
  lease passed, `expired: true`. After the process `resume` and
  `resolve_unknown`, the next `claim` reserves a new attempt when the job has
  attempts left (`store.py:464-466`). `frontier` changes nothing.
- EX-9 (state): a worktree whose task is complete and whose branch is
  integrated lists as `concluded` with zero changes; one whose task was written
  3 minutes ago lists as `active`; one with no loop row lists as `unlinked`; a
  completed review run in an open task's worktree leaves it `idle`.
- EX-10 (cleanup, rejection): a `concluded` worktree with one untracked file is
  `kept_dirty`; `cleanup --apply` naming it refuses and removes nothing.
- EX-11 (cleanup, nominal): a clean `concluded` worktree is removed after
  authorization; Git no longer lists it, its branch still exists, and its entry
  carries `removed_at` and the label `removed`.
- EX-12 (expiry): 31 days later, `cleanup` lists that entry as `expire`, and the
  apply drops it from the catalog.
- EX-13 (missing): a catalog entry whose folder was deleted by hand is listed as
  `missing`; `forget` drops the entry without touching files.

## Rejected alternatives

- RA-1, lease that expires after N minutes without writes: a long phase without
  writes loses the lease, and the free-text session ID still locks a compacted
  session out of its own task. A lease also gives no safety by itself: a paused
  holder keeps writing after expiry unless the storage checks an increasing
  fencing token [R-5]. The record revision already is that token, so the lease
  adds nothing.
- RA-2, lock bound to the agent's process: not portable to the five hosts; Codex,
  OpenCode and Pi expose no stable process that `run_state.py` can observe.
- RA-3, keep `--take-over` and only improve its message: the user still has to
  confirm by hand, which is the clumsiness being removed.
- RA-4, new schema versions (`agenda/v2`, `worktrees/v2`): the previous release
  refuses any other schema (`run_state.py:1536`, `workspaces.py:161-162`), so one
  upgraded session would lock every older session out.
- RA-5, an append-only event history per worktree: it grows without bound and
  duplicates what the agenda and the work records already hold (UD-4).
- RA-6, automatic revocation of expired reservations in `frontier` or `claim`:
  it writes behind a read-only surface, and another session could reclaim a job
  whose dispatched worker is still running.

## Assumptions (agent, not user decisions)

- A-1: Two live sessions on the same task in the same checkout may edit the same
  files; the user accepted this risk with UD-1. One task per worktree (UD-2)
  makes it rare, and the `recent_activity` notice plus the `active` label are
  the signals.
- A-2: The activity window is 15 minutes, one constant used by `resume` and
  `list`.
- A-3: No contract a consumer reads is removed (`holder` stays, `--take-over` is
  accepted, schemas stay `v1`, the retrieval fields stay), so every touched
  plugin takes a minor version.
- A-4: "Integrated" means integrated into Worktrunk's default branch. A task
  merged elsewhere stays `kept_unintegrated`.
- A-5: Until the next release reaches every host, a writer of the previous
  release and a writer of the new release do not exclude each other on the D-5
  sites, because they use different lock mechanisms. The worst cases, each
  requiring both releases to write the same file at the same moment:
  - one index rebuilt twice (index builds publish whole generations atomically);
  - two ADRs or FRDs given the same number;
  - a catalog entry lost when an old-release write overlaps a `create`, which
    holds the catalog lock for seconds across the Worktrunk switch
    (`workspaces.py:310-355`). The checkout and branch survive, but the
    checkout then lists as `foreign` and its `create` retry refuses with
    `foreign_worktree` (`workspaces.py:322-324`) until the entry is restored by
    hand.
  The one-hour age rule of S-5 keeps a new writer from deleting an old writer's
  live temporary.
- A-6: The stages are integrated after the uncommitted reservation work is
  committed or discarded by its owner. That work touches `commit_change` and
  `validate_transitions` (HEAD lines 1250-1251 and 1477-1499), and stage 1
  changes how `commit_change` passes the session, so that integration needs its
  own conflict resolution.

## Success criteria

- EX-1 to EX-8 (stage 1) and EX-9 to EX-13 (stage 2) are automated tests and pass.
- These committed tests are rewritten for the new behaviour and pass: the holder
  tests of `tests/test_work_record.py` (`test_ask_respects_the_task_holder` and
  the agenda holder checks), `test_worktree_recovery.py:175,216`; lock-file
  absent checks in `test_codebase_map_embeddings.py:131`,
  `test_codebase_map_index_cli.py:41`, `test_codebase_map_mcp.py:542`,
  `test_worktree_catalog.py:167,303`; stale-lock checks in
  `test_adr_method.py:357-365`, `test_frd_method.py:313-318`,
  `test_worktree_catalog.py:396-401`, `test_codebase_map_retrieval.py:334-345`,
  `test_codebase_map_index_cli.py:61-68`, `test_codebase_map_mcp.py:599-606`;
  `test_worktrunk_runtime.py:320-328` for the new `remove` form.
- `python -m unittest discover -s tests` passes on the candidate.
- No Markdown body under `plugins/` mentions `--take-over` or "held by session";
  `rg --type md` is the check.
- `python scripts/daodan_build.py --check --support`, the linters,
  `sync_plugin_docs.py --check` and `sync_codex_instructions.py --check` pass.

## Open questions

- O-1: Should an open task be abandonable (a status that frees its branch without
  integration)? Today it can only be completed. Not needed for this redesign,
  because any session can now resume it.

## Sources

Read on 2026-10-28 by two research runs and a direct check of the Worktrunk
reference.

- R-1: filelock concepts, https://py-filelock.readthedocs.io/en/latest/_sources/concepts.rst.txt
  (OS locks released on process exit; NFS and SMB caveats; PID reuse).
- R-2: Python `msvcrt`, https://docs.python.org/3/library/msvcrt.html, and
  SQLite "How To Corrupt", https://www.sqlite.org/howtocorrupt.html (POSIX
  record locks cancelled by any `close()`).
- R-3: bpo-26362, https://bugs.python.org/msg292662 (`os.replace` denied while
  the target is open on Windows).
- R-4: PyPI metadata, https://pypi.org/pypi/filelock/json.
- R-5: Kleppmann, "How to do distributed locking",
  https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html.
- R-6: git-worktree 2.56.0, https://git-scm.com/docs/git-worktree; Git
  `lockfile.c`, https://raw.githubusercontent.com/git/git/master/lockfile.c
  (Git never deletes a stale `index.lock` by itself).
- W-1: Worktrunk keeps per-branch state in Git config with a timestamp and
  derives listing state from Git,
  https://github.com/max-sixty/worktrunk/blob/main/docs/src/content/docs/claude-code.md;
  Claude Code and Codex keep the directory disposable and durable state
  elsewhere, https://code.claude.com/docs/en/worktrees.md,
  https://learn.chatgpt.com/docs/environments/git-worktrees.
- W-2: `wt list` JSON schema 2 fields, https://worktrunk.dev/list/.
- W-3: Worktrunk `step prune` skips locked, dirty and main worktrees,
  https://github.com/max-sixty/worktrunk/blob/main/docs/src/content/docs/step.md.
- W-4: named removal outcomes (`retained_unmerged` and others),
  https://worktrunk.dev/remove/.
- W-5: `wt remove` flags `--no-delete-branch`, `--no-hooks`, `--foreground`,
  `--format=json`; without `-f` it refuses a worktree with uncommitted changes,
  https://worktrunk.dev/remove/. A teardown in unsynchronized steps raced
  `index.lock` in Claude Squad,
  https://github.com/smtg-ai/claude-squad/issues/284; an expiry cleanup that
  deleted rows made workspaces vanish in Vibe Kanban,
  https://github.com/BloopAI/vibe-kanban/issues/3329.
