> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# Snapshot

Progressive analysis and intervention scopes: [scope](scope.md).

After scope confirmation, the coordinator writes the current snapshot before Phase 0.
Classic refresh ownership then transfers to the isolated analyst; team ownership
stays with the coordinator. Other workers report gaps. Preserve parent bytes and
preflight lineage; copy this snapshot's own `git` into state through the resolver.

## Incremental Update Commands

### 14. Count scope and write

```bash
python "<plugin-root>/skills/map-method/scripts/snapshot.py" scope <target>
python "<plugin-root>/skills/map-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.sqlite
```

`scope` counts languages/exclusions without parsing. Storage defaults to SQLite.
Explicit JSON:

```bash
python "<plugin-root>/skills/map-method/scripts/snapshot.py" write <target> \
  --format json --out <run-dir>/snapshot/manifest.json
```

Choose one file per run. After writing, set `state.json -> snapshot`:
`{"format":"sqlite","path":"snapshot/manifest.sqlite","storage_version":1}`,
or format `json` with `snapshot/manifest.json`.
Legacy runs without this record are JSON only; never rewrite them.

Use `snapshot.py resolve` for current, existing and parent runs:

```bash
python "<plugin-root>/skills/map-method/scripts/snapshot.py" resolve <run-dir>
```

It returns `path`, `format`, `storage_version`, `file_count` and small `metadata`
(including `git`), never the inventory. Retain `path` as `source_manifest`.
Missing, linked, ambiguous or misdeclared files fail; the mirror supplies no binding.

Resolve `parent_manifest` before same-target reuse, including selected full analysis:

```bash
python "<plugin-root>/skills/map-method/scripts/snapshot.py" write <target> \
  --format "$snapshot_format" --out "$source_manifest" --reuse "$parent_manifest"
```

New runs default to `snapshot_format=sqlite`.
Parent/child formats may differ. Resume preserves format/path; changing them requires
a new run/extraction. Same-path reuse closes its reader before Windows replacement.

Bind root, target and run. Reuse hashes every inventoried file regardless of
size/mtime and retains structure only for matching bytes/parser identity.
Root/target/fingerprint mismatch rebuilds; malformed input preserves the output.

### 15. Diff and carry

```bash
python "<plugin-root>/skills/map-method/scripts/snapshot.py" diff \
  <parent-run-dir> <target> --out <run-dir> --verify [--threshold 0.4] [--flags '{"depth":"full"}']
python "<plugin-root>/skills/map-method/scripts/snapshot.py" carry <parent-run-dir> <run-dir>
```

Require `--verify` for freshness: it hashes every file. `--threshold` is the affected
ratio recommending full analysis. Diff normalizes line endings; before reading
source, always obtain a current `write --reuse`, including `none` and LF/CRLF-only
changes. Supported parent claims do not prove current bytes. Returning supported
analysis without source reading needs no new full analysis.

Carry follows the initial current snapshot and precedes preparation. `carry.json`
records source/copied hashes and provenance. A caller-bound classic
`--stop-after 4` child may set `parent_phases: [1,2,3,4]` to carry only those files
from a verified partial/team parent. Classic never carries team `08`.

### 16. Prepare, check and publish

```bash
python "<plugin-root>/skills/map-method/scripts/snapshot.py" register $RUN_DIR
python "<plugin-root>/skills/map-method/scripts/snapshot.py" prepare $RUN_DIR \
  [--phase N] [--stop-after N]
python "<plugin-root>/skills/map-method/scripts/snapshot.py" prepare $RUN_DIR \
  --resume-from [N] --run-name <exact-id> [--mode classic|team] [--flags '<JSON>']
python "<plugin-root>/skills/map-method/scripts/snapshot.py" check $RUN_DIR --json
python "<plugin-root>/skills/map-method/scripts/snapshot.py" publish $RUN_DIR
python "<plugin-root>/skills/map-method/scripts/snapshot.py" unregister $RUN_DIR
```

Register after state initialization; unregister on cancellation, partial delivery
or failure. Only the coordinator prepares/publishes; workers read declarations and
write results. `prepare` writes `state.json -> delivery` schema 1: immutable
mode/flags, artifact declarations and `run_phases`/`stop_after`/`resume_from`.
Artifacts are produced, inherited with provenance, or skipped with reasons.
Knowledge requires both Phase 0 files. Never invent the helper's mode table.

`--phase N` accepts 1–6 and selects 0 plus N; 7 is refused. Docs-only selects 0/6.
Neither publishes. `--stop-after N` accepts 1–6, conflicts with docs/single-phase
controls and leaves later work pending; it is not a mode flag.
Resume requires the exact name, verifies earlier artifacts/current source, preserves
mode/flags, drops the stop and starts at N (1–7) or first incomplete phase.
Missing inherited provenance never becomes fresh work silently.

`check --json` reports `missing`, `empty`, `unexpected`, `invalid_inherited`,
`stale`, `undocumented_added`, `not_yet_produced`, `first_incomplete_phase`,
`complete`, `may_publish` and errors. Exit 0 means invocation delivery, including
intentional stops; 1 means gaps; 2 means invalid binding. Skipped/verified inherited
work is never missing produced work. Deferred stale markers remain pending.

Publish requires `complete`/`may_publish`, no stale markers and requested human views.
Team `08-interconnect-map.md` is required unless mode-skipped. Full-depth comments
require classic `comment_health.md` or each team's `06-documentation.md` Comment
Quality section. Publication rechecks delivery, replaces all known mirror phases/state
with locked rollback protection, updates only this registry/latest pointer and
preserves archives/unrelated files. Never hand-copy partial output.

## Prerequisites

Python >= 3.12 and stdlib suffice; below it the entry scripts refuse, because `ast`
parses with the running grammar. Optional Java/JS/TS/Rust/Go Tree-sitter parsers:

```bash
pip install -r "<plugin-root>/skills/map-method/scripts/requirements.txt"
# alternatively:
uv pip install -r "<plugin-root>/skills/map-method/scripts/requirements.txt"
```

Python uses stdlib `ast`, SQL/PL-SQL regex DDL, CSS/SCSS/LESS the tokenizer.
Parser notes name the engine or fallback; missing grammars report
`tree-sitter unavailable: <error>`. For optional offline embedding, read
`references/embeddings.md` before invoking `embedding_worker.py`.
Python engine passes write `<run-dir>/snapshot/engine-edges.sqlite` via
`resolve_edges.py <manifest> --compact --report-out <report.json>`, read by `edge_view.py`.

Tree-sitter supplies definition ends; regex ends at the next symbol. Shared
lines can require whole-file reading. Diagnosis never applies changes.
