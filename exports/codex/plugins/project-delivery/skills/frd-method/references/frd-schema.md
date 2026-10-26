<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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

# FRD schema version 1

An FRD is one UTF-8 JSON object stored under `docs/frd/`. Version 1 uses
`FRD-NNNN-<slug>.json`; revision N uses `FRD-NNNN-vN-<slug>.json`. `FRD-NNNN`
identifies the document family, while `FRD-NNNN vN` pins one version. JSON is
rendered with sorted keys, two-space indentation and literal Unicode.

## Extraction input

`propose --data` and `merge --data` accept exactly three arrays:

```json
{
  "requirements": [
    {
      "id": "REQ-001",
      "text": "A consultant can reopen a paused task.",
      "evidence": [
        {
          "path": "docs/workflow.md",
          "document_sha256": "64 lowercase hexadecimal characters",
          "start": 20,
          "end": 66,
          "excerpt": "A consultant can reopen a paused task."
        }
      ]
    }
  ],
  "entities": [
    {
      "id": "ENT-001",
      "entity_type": "PERSON",
      "name": "Alfio",
      "evidence": []
    }
  ],
  "relationships": [
    {
      "id": "REL-001",
      "source": "ENT-001",
      "target": "ENT-002",
      "type": "WORKS_FOR",
      "evidence": []
    }
  ]
}
```

The empty evidence arrays above only illustrate item shape. Every persisted
item requires at least one valid evidence object. Input `status` is optional
and defaults to `extracted`; an extraction cannot introduce another status.
Every array may be empty except `requirements`. Item ids are unique across all
three collections and match an uppercase prefix followed by at least three
digits, such as `REQ-001`, `ENT-001` and `REL-001`.

Entity `entity_type` is exactly `PERSON`, `ORGANIZATION` or `LOCATION`.
Relationship `source` and `target` name entities in the same FRD; `type` is a
non-empty relationship label. A requirement has non-empty `text`; an entity has
a non-empty `name`.

## Evidence and Unicode spans

Each evidence object has exactly these fields:

| Field | Contract |
|---|---|
| `path` | Normalized POSIX path relative to the project root. Absolute paths, backslashes, `.` and `..` segments are refused. Resolved symlinks must remain inside the project. |
| `document_sha256` | Lowercase SHA-256 of the source file's current bytes. |
| `start` | Inclusive Unicode code-point offset in the UTF-8 decoded document. |
| `end` | Exclusive Unicode code-point offset, with `0 <= start < end <= len(document)`. |
| `excerpt` | Exact value of `document[start:end]`, including whitespace and newlines. |

Offsets are not UTF-8 byte offsets and not UTF-16 code-unit offsets. Newlines
remain exactly as decoded, including CRLF when present. Active records revalidate current evidence. Superseded records retain structural
history despite changed sources. Stale Accepted records can be revised; new or
promoted versions require fresh evidence. Unrelated stale records do not block
revision.

## Stored record

In addition to the three extraction arrays, a record contains exactly:

| Field | Meaning |
|---|---|
| `schema_version` | Integer `1`. |
| `frd_id`, `version`, `title` | Family identity, positive revision number and non-empty title. |
| `status` | `Proposed`, `Accepted` or `Superseded`. |
| `author`, `created_from_task` | Proposer and originating run or task. |
| `proposed_on`, `proposed_at_sha` | Proposal date and repository commit binding. |
| `accepted_on`, `accepted_at_sha` | Set only by `promote`. |
| `last_verified_sha` | Set only by `verify`; null again on each newly Accepted revision. |
| `superseded_by` | Pinned later Accepted version on a Superseded record, otherwise null. |
| `conflicts` | Extraction disagreements and their resolution state. |

A family has contiguous versions from 1, at most one Proposed and at most one
Accepted version. A revision starts from the Accepted version. Promotion marks
that previous version Superseded in the same locked write set.

## Review states and merge

Each item has one `status`: `extracted` (unreviewed), `verified` (confirmed),
`corrected` (manual, never overwritten) or `rejected` (never restored).

`merge` accepts only Proposed. New ids are appended as `extracted`. Unchanged
items union deduplicated evidence and retain their status. Semantic fields are
`text` for requirements, `entity_type` and `name` for entities, and `source`,
`target` and `type` for relationships. Changed items open a conflict with both
versions; they never overwrite stored content. Existing conflicts stay open and
missing incoming items are not deleted.

A conflict has `id`, `item_id`, `existing`, `incoming`, `status` (`open` or
`resolved`) and `resolution`; open conflicts block `promote`. Use
`resolve --item ID --conflict CONFLICT-NNNN` with `--status verified` or
`rejected` to retain the stored item, `--status corrected` to accept the incoming
item, or `--status corrected --data item.json` to supply a complete correction.
Without `--conflict`, resolve applies the same states directly. Correction data
keeps the item id and requires valid evidence. Review states and semantic fields
survive later merges.

## Commands and optimistic writes

Existing-record mutations require `--expect-digest`, the current file's SHA-256.
A mismatch refuses the write. Writes hold `.frd-lock`, validate future records
and render `README.md` before atomically replacing files.

- `propose`: create FRD version 1, or revise Accepted with `--revise`, `--data`, `--task`, `--sha` and the Accepted digest.
- `validate`: validate active evidence; with `--frd`, return version digests and `evidence_freshness: not-checked` for revision workflows.
- `merge`: merge a fresh extraction into Proposed.
- `resolve`: verify, correct or reject an item and optionally close its named conflict.
- `promote`: after explicit user approval, accept Proposed unless conflicts remain; supersede the previous Accepted version.
- `verify`: record a reviewer's conformance commit in `last_verified_sha` on Accepted.
- `index`: regenerate `README.md` between `frd-index` markers, preserving prose outside them.

The helper checks structure and evidence, not requirement truth or code
conformance. Those judgments belong to the reviewer.
