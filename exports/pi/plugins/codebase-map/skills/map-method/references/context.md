<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
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

# Bounded context packets

`context_packet.py` projects a verified `ScopePlan` into recipient input, without
LLM calls, index refresh, encoder startup or downloads. Prepare existing indices
explicitly. The owning process retains its requirements and gates.

## Inputs and entry points

```text
snapshot.py context MANIFEST --request REQUEST.json --recipient RECIPIENT.json --authority AUTHORITY.json --out OUTPUT_DIR [--cursor CURSOR.json] [--indexes INDEXES.json]
```

Use the request and independent authority from `scope.md`. An authority may add
`source_root`, an existing directory within its artifact project `root`, when a
non-Git subtarget has its own source coordinates. Requests never choose this root.
The CLI authority is an explicit caller input, separate from the request. Output
is a directory under the manifest directory. JSON inputs and path chains reject
links; artifact names are content addressed and published exclusively.

`RECIPIENT.json` declares `id`, `available_tokens` (space remaining after existing
instructions and conversation), `reserve_tokens`, `max_chars`, `max_evaluations`
(1–10000), optional `prefix`, `suffix`, `tokenizer_id` and `policy`
(`ordered`, default, or experimental `marginal`). Include every additional dispatch
wrapper in prefix/suffix. Maximum projection: 200 entities and 1000 variants.

Python callers use `build_packet(plan, request, authority=..., recipient=...,
indexes=..., cursor=..., token_counter=...)`. The explicit counter must match
`tokenizer_id` and count the exact recipient input, including its wrapper. No
tokenizer is imported from a project or loaded by name. A missing counter reports
`characters_only`, null tokens and a dispatch gap. It never converts characters
to tokens or certifies model context capacity. CLI/MCP use this character mode.
The dispatch owner must verify available model context before sending input.

`codebase_map_context` accepts `run_id`, request, recipient, optional `out`
(manifest-relative directory), `cursor` (run-relative checkpoint) and
`base_run_id`, and explicit `embedding_result` (run-relative producer receipt
inside `snapshot/`). The service resolves manifests and optional base from those bound
runs; supplied descriptors must match. It grants read access only to the run's
target, no source writes. Request boundaries use the snapshot's source coordinates.
The server's project boundary contains its artifacts even for non-Git subtargets.
An existing retrieval index and shared cards are read explicitly; missing inputs
remain bound missing inputs. The tool writes artifacts, so its annotation is not
read-only. It returns compact paths, digests, counts, gaps and cost.

## Selection and evidence

Mandatory current source and exact anchors precede peripheral material. Each body
requires its verified signature and `source_reader` context blocks, including
canonical full-file fallback. Serialization merges physical source lines by
snapshot/file/interval. Identical text in different entities keeps both identities.
Body, fresh card and signature have distinct capabilities; semantic similarity
never satisfies current-source support. A card/body replacement must preserve all
hard predicates. Stale cards are excluded. Card freshness remains lexical;
canonical `engine_callee_drift` remains separate evidence.

L1 callers/callees and callsites, L2 summaries and L4 obligations come from
`build_edit_impact`; request `slices: true` adds its existing lazy L3 Python slice.
Markdown references in fresh cards retain their source anchors. Graph omissions,
engine coverage and source uncertainty remain explicit. This projection adds no
second impact classifier and never turns a related test into passed validation.

The packer closes prerequisite cycles as a unit, checks representation conflicts
and hard support, and reserializes each proposal. It compares ordered selection
with a fixed nonnegative feature surrogate, `sum(max(score))`, by marginal gain
over marginal serialized cost; zero/negative additional cost comes first. Shared
prerequisites are reconsidered after selection. A bounded core search and
single-bundle comparison consume explicit work limits. This is a deterministic
heuristic with no optimality, infeasibility or `1-1/e` guarantee.

Every omitted variant has a reason on disk. If the mandatory core, including all
metadata and recipient wrapper, does not fit or bounded search cannot find it,
status is `needs_split`, never `ready`. `incomplete` records missing localization.
Ready means evidence for an attempt; task, validation and write authorization stay
false. An empty packet/frontier never closes a process gate.

## Cost and resumption

The artifact's `input` string is the complete measured recipient input. Send that
string without adding uncounted wrappers. Its operational receipt, comparisons,
full residuals and cursor remain on disk. Measured input tokens are not billed
usage. Cumulative tokenized input is checked separately against the scope cap;
output usage remains the owning process's observation, not an inferred result.

The checkpoint preserves the scope plan and delivered representation IDs. It
starts with at most 100 discovery steps through the canonical scope planner.
Packet resumption projects that frozen plan to preserve deterministic replay;
the owning process advances any remaining scope frontier explicitly and starts
a new packet checkpoint. Discovery caps never prove completeness. The checkpoint
binds request, effective authority, manifest bytes/logical identity, parser,
resolver/edge coverage, retrieval and card bytes, missing inputs, recipient,
packing policy and prior deliveries. A changed binding returns `cursor_stale`;
refresh explicitly and start a new checkpoint. The same cursor and unchanged
inputs produce the same selection. Mandatory evidence may recur because each
new packet must remain self-supporting; peripheral deliveries are not repeated.
Hashes detect stale/altered records and do not grant authority. A collision never
replaces evidence. A partial publication is recoverable evidence, not success.
