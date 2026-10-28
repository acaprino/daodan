> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Runtime interface

Use the installed helper through shell execution:

`python "<plugin-root>/skills/science-based-approach/scripts/science_runtime.py"`

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
OpenCode adapts callbacks in its loader; Copilot/Pi use method checkpoints.
Installed hook trust/event delivery is unknown unless actually probed.
Never run research to obtain status.

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
