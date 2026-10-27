# Runtime interface

Use the installed helper through the host shell binding:

`python "${CLAUDE_PLUGIN_ROOT}/skills/science-based-approach/scripts/science_runtime.py"`

Append one command below. ROOT is the caller's explicit project directory.
The helper resolves the common main checkout home for mode/checkpoints/locks
using the Work Controller contract. Research documents stay in the caller's
checkout, so branch-scoped grants are respected. No global preference or
ancestor search is used. JSON payload files
belong to the caller's owned run. Never interpolate user text into shell code.

## Mode

- `mode --project ROOT`: read only; absent configuration returns enabled true,
  revision 0, origin default. Existing state returns origin explicit.
- `mode off --project ROOT --expected-revision N --source REQUEST_REFERENCE`
  (or `on`): use the revision just read and the real user request reference.
  An already-effective request is unchanged. Mutations keep an immutable receipt
  under `.daodan/science-mode-history/`.
- Invalid input, malformed state or stale revision is a failure, not success.
  Preserve malformed bytes; don't silently replace them. Re-read on concurrency
  and reconcile the user's intent instead of blindly retrying.

For science-mode without arguments, report state, origin and project plus the
host coverage from the generated entry note: Claude/Codex register plugin hooks;
Copilot/Pi/OpenCode use method checkpoints. Installed hook trust/event delivery
is unknown unless actually probed. Never run research to obtain status.

## Checkpoint

`checkpoint --project ROOT --payload FILE` inspects without writing.
Add `--record` to claim or finish within the caller's grants.

Payload: `task_id`, `phase`, `context` (JSON object of question, constraints,
candidate/version and relevant technology), `automatic` (default true).
Set `research_maintenance: true` for the maintenance callback exclusion.
An optional `origin` label does not change the deduplication identity.
Return values include needed, claimed, duplicate, recorded, disabled and
configuration-error. A duplicate includes the prior checkpoint and its status.

To finish, send the same identity/context plus `outcome`, `reason` and
`references` (strings pinning research/revision/claims). Stored outcomes:
not-applicable, reused, updated, created, partial, unavailable.
Disabled/configuration-error return directly and cause no automatic writes.
Follow `checkpoint.md` for interrupted work and explicit retries.

## Select

`list --project ROOT` returns canonical research and unpublished recovery
journals. `select --project ROOT SELECTOR` accepts exact identity, unambiguous
topic or all/tutte. Snapshot all once before a batch. A selection error never
authorizes an arbitrary choice. List/select are archive reads: automatic callers
must check mode first.

This list covers registered identities only. Apply `reuse.md` to discover
related unindexed Markdown as well. For all/tutte, the coordinator forms one
deduplicated inventory of registered records and eligible legacy current files;
it does not treat revision/check snapshots or indexes as independent research.

## Publish

`publish --project ROOT --payload FILE` accepts:

```json
{
  "id": "cache-policy",
  "path": "docs/research/cache-policy",
  "expected_revision": 0,
  "operation_id": "caller-owned-publication-id",
  "automatic": false,
  "title": "Actual research title",
  "topics": ["cache"],
  "question": "The caller's actual question",
  "owner": "project",
  "status": "current",
  "reason": "First investigation",
  "known_consumers": [],
  "document": "Complete researched Markdown, using templates/research.md",
  "check": {
    "id": "caller-owned-check-id",
    "status": "completed-with-change",
    "summary": "Actual work completed and resulting changes",
    "coverage": ["Sources and sections actually checked"],
    "limitations": [],
    "document": "Filled check-receipt template with origin, context and detailed evidence"
  }
}
```

This is a schema example, not publishable research. Supply evidence and actual
content. Use check status partial when material evidence can be published but the
literature check remains incomplete, for example a verified retraction with
other sources inaccessible. That revision preserves limits and never advances
the last complete check. Use review-needed for unresolved applicability.
Failed/cancelled checks alone cannot justify a new scientific revision.

Use revision 0 only for a new record; otherwise supply the selected current
revision. Status is current, review-needed or superseded. Keep known consumers
and cumulative changelog in a new revision. Default automatic false represents
an explicit command; automatic callers MUST set true. The helper rechecks mode
before automatic publication and under its write lock.

The default current file is path/README.md and contains the full latest research.
For an existing legacy Markdown, supply `current_path` with its exact project-
relative path and `expected_document_digest` with the SHA-256 of bytes just read.
It must be an existing .md in the same research owner root. The helper keeps
that path, captures original bytes as revisions/r0000.md and creates no parallel
current README. The path remains bound to this research identity. Later updates
carry a freshly observed digest; a stale one cannot overwrite manual changes.
Tracking is initialized only when an actual update/check is requested, never
for simple conversational reuse. An initial archive snapshot is explicitly
labelled as such; it must not claim that historical sources were newly checked.

Supply only the authored scientific body in `document`, excluding the helper's
reserved science/science-state marker blocks. Keep superseded statements visibly
struck through, explain replacements and append the descriptive changelog. The
helper manages the separate state/check-history block in that same current file,
including no-change checks. It does not infer which scientific claim is obsolete.

Paths must be exactly docs/research/<topic> or
docs/plugins/<owner>/research/<topic>, with no links, junctions or traversal.
Files: science.json points to revisions/rNNNN.md and matching JSON metadata with
content/metadata digests. Checks have immutable JSON and readable Markdown. Optional check.document keeps
the filled receipt template verbatim after canonical metadata; use it for task
origin, context, start/end timezone, detailed queries and changes.
The helper records exact UTC timestamps; preserve execution/reading timestamps
and timezone in the supplied research. Cite the pinned revision, not README alone.

## Record a check

`check --project ROOT --payload FILE` uses id, expected_revision, automatic and
the check object above. Allowed receipt statuses: completed-no-change, partial,
failed, cancelled. completed-with-change belongs to publish; partial can accompany either an
unchanged attempted check or a new revision with material evidence.

A no-change check never creates a scientific revision. Failed/partial/cancelled
checks do not count as full successful verification. README distinguishes latest
attempt, last complete check and substantive update; all receipts remain available.

## Recovery and errors

`reindex --project ROOT` rebuilds current state views and the global index
within science marker blocks, preserving surrounding bytes and refusing to
overwrite differing manual scientific content. It is a write and
requires the caller's grant. It does not search, check papers or commit an
unpublished revision.

Publish/check/replay update only their current research file and the global
index. Only explicit reindex may rebuild other dossiers, requiring that scope.
Missing check Markdown can be reconstructed; conflicting existing immutable
receipt bytes are an error rather than silently replaced audit evidence.

Writes serialize with a project-local OS lock and optimistic revision checks.
On interruption or an error after writing, inspect list/current revision first.
Retry the exact operation ID and evidence to complete its publication/rebuild
views. A changed payload cannot overwrite an abandoned revision. Unpublished
journals are reported separately; their receipts do not advance published
freshness. Resolve conflicting partial content explicitly; never delete history
to force a retry. Changed automatic/explicit mode does not change content identity.

Success is JSON stdout and exit 0; errors are JSON stderr and exit 2.
Automatic disabled/configuration-error are non-success outcomes returned as JSON,
not permission to continue. Preserve evidence and report the reason.

`hook` reads host event JSON on stdin, emits only supported additional context
and stays silent on OFF. It never writes, searches or approves host trust.
