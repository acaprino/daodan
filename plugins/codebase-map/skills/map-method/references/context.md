# Bounded context packets

`context_packet.py` projects a verified `ScopePlan` into recipient input, without
LLM calls, index refresh, encoder startup or downloads. Prepare existing indices
explicitly. The owning process retains its requirements and gates.

## Inputs and entry points

```text
snapshot.py context MANIFEST --request REQUEST.json --recipient RECIPIENT.json --authority AUTHORITY.json --out OUTPUT_DIR [--cursor CURSOR.json] [--indexes INDEXES.json]
```

Use the request and independent authority from `scope.md`. An authority may add
`source_root`, a related coordinate directory, when a non-Git subtarget has its
own root or a Git subproject uses its enclosing repository's coordinates. Every
granted prefix and snapshot target must resolve inside the artifact project
`root`; coordinates grant no additional reads. Requests never choose this root.
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

## Planner projection (I1)

The same context CLI/MCP operation publishes `daodan/map-slice/v1`, returned as
`map_slice_path` and `map_slice_sha256`. `map_slice.project_slice` projects the
verified frozen scope: disjoint file components, cited confirmed calls, snapshot
freshness, gaps and open obligations. Its envelope binds the original request;
`scope_input_digest` and `plan_digest` bind the packet. Empty localization abstains.
The projection caps 200 localized entities, proposed edit sites first, and 1000 calls,
each file pair cited once before repeats, with explicit omissions.
Unsupported imports/contracts, unresolved calls and partial discovery stay gaps.
I1 supplies evidence to planners; approved requirements and contracts determine
task precedence. It grants no edits and closes no validation. The owning lifecycle
method consumes these artifacts through public CLI/MCP, never provider-private
imports, and rechecks the candidate immediately before dependent dispatch.
