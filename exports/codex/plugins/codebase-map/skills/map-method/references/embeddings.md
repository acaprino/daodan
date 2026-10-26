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

# Optional local embeddings

Use embeddings only when explicitly selected. The textual index works alone.
Indexing, ranking and graph navigation make no LLM calls. Semantic cards retain
their separate reading cost. This provider is opt-in; retrieval scores do not
establish correctness, independence or permission to edit.

## Runtime and artifacts

Keep the map's original Python interpreter and parser environment for snapshot
and source validation. `embedding_worker.py` starts the explicit optional Python
with `-I` and runs only its own encoding entry. The backend never imports the
project or the map/parser modules. Its private protocol carries status/counts;
numeric output stays in temporary files beside the derived index. The parent
sends an explicit stop and closes or kills the process on failure/timeout.

Provisioning is a separate, explicitly chosen operation. The script metadata pins
NumPy 2.4.6, ONNX Runtime 1.31.0 and tokenizers 0.23.3. Reuse an existing isolated
environment when available; no installation or model download happens in a
query. An unavailable runtime or local artifact produces a failure, not a
fabricated empty result. Windows CPU inference is exercised; Linux has upstream
runtime support but requires its own live probe.

Share weights across projects in `%LOCALAPPDATA%/Daodan/models/CodeRankEmbed/REVISION/`
on Windows, or `$XDG_CACHE_HOME/daodan/models/CodeRankEmbed/REVISION/` on Linux
(default `~/.cache`). Omitting `model_dir` selects that per-user revision folder.
An explicit model folder remains supported. Only each project's derived vectors
are project-specific. The graph is 138,619,279 bytes (132.2 MiB), plus tokenizer
files. This avoids repeated disk copies/downloads; RAM loading happens once per
provider process, retained for its session. No global background daemon is installed.

The supported artifact is the community INT8 conversion of CodeRankEmbed at
revision `e74f446dc6e67e29fcee77213472c142f73a6bbb`. The helper verifies graph
SHA-256 `4eae31d09b1843103a1ebd5e2b2e24b5a5cad441a33906b35b12b1e2ed91d1db`
and tokenizer SHA-256
`91f1def9b9391fdabe028cd3f3fcc4efd34e5d1f08c3bf2de513ebb5911a1854`
before native loading. It executes no custom model Python or custom operators.
The model uses a 512-token input limit; this is an encoder limit, not an LLM
context or billing measurement.

Encoder version 2 runs one input per native inference. Dynamic INT8 scales
depend on other inputs in a batch, so independent encoding is required for
content-addressed reuse. The provider fingerprint invalidates version 1 vectors.

## File request interface

Read a `daodan/embedding-request/v1` JSON file. Required fields are `schema`,
`operation` (`index` or `query`), `manifest` and `index`; `model_dir` is optional. `query`
also requires text and accepts `limit` (1..1000, default 500). Paths below are
illustrative; use the caller-bound run and an explicitly prepared model folder.

```json
{
  "schema": "daodan/embedding-request/v1",
  "operation": "index",
  "manifest": "/project/.codebase-map/runs/run-id/snapshot/manifest.sqlite",
  "index": "/project/.codebase-map/runs/run-id/snapshot/embeddings.sqlite",
  "model_dir": "/prepared-models/CodeRankEmbed"
}
```

Run with the map interpreter:

```bash
python "<plugin-root>/skills/map-method/scripts/embedding_worker.py" \
  --request REQUEST.json --runtime-python /explicit/optional-environment/python \
  --report-out SNAPSHOT_DIRECTORY/embedding-report.json
```

The index and report stay beside the manifest. Existing reports are never
replaced. Atomic exclusive publication requires same-directory hard links;
unsupported filesystems fail closed. Linked paths, escapes and canonical
store collisions are refused. The manifest
is never rewritten. Stdout contains status, counts and a report path; detailed
results stay on disk. A query never refreshes an index implicitly.

## Cache and consumption

`refresh_index(manifest, index, provider=...)` publishes a complete SQLite
generation atomically. Cache identity includes the exact encoded text (path,
name, signature and source), model, tokenizer, runtime, encoder and document
versions. Rename/content changes invalidate affected inputs; deleted entities
and unused vectors disappear from the new generation. An interrupted refresh
retains the previous generation. A stale generation cannot serve a current
query. Locks prevent concurrent publishers; vector checksums, dimensions and
finite nonzero norms are validated before use.

Use `ProcessProvider(optional_python, model_dir, manifest.parent)` as a context
manager. `search(manifest, index, query, provider=..., limit=...)` returns a
`daodan/embedding-result/v1` with snapshot/document/provider/artifact/query
bindings, bounded entity ranks, counts and elapsed time. No vectors enter this
result. Search also publishes an immutable `embedding-query-<digest>.json`
receipt beside the index, covering query, ranks, counts and artifact binding.
An identical receipt can be reused. Pass the result explicitly as
`retrieval.search(..., embedding_result=result)`. The consumer reads the actual
artifact, inventory and receipt; it starts no encoder. Relabeled queries or
changed ranks fail validation. A stale result falls
back to textual ranking with an explicit gap; malformed results are rejected.

Verified exact anchors retain precedence. Remaining ranks use the benchmark's
versioned policy `exact-rrf75-25-k60-v1`: dense weight 0.75, lexical weight 0.25,
rank offset 60. No similarity threshold can close an impact or validation gap.
The provider remains optional until independent quality and whole-flow cost
measurements justify another decision.
