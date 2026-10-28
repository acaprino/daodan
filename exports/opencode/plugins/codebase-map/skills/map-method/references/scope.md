<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# Progressive code scope

`scripts/scope_planner.py` selects evidence for an analysis or intervention using
existing snapshots, verified lexical/Jedi edges and optional local retrieval.
It performs machine computation only. It never starts an encoder, calls an LLM,
refreshes an index, edits project source or closes a process gate. The complete
checkpoint stays on disk; P7 owns recipient packets, tokenization and CLI/MCP.

## Inputs and authority

Use the exported `contracts/context.toml` request and plan records. The owning
process supplies a separate trusted `authority` argument, derived from its run:

```python
authority = {"root": str(project.resolve()),
             "read_boundary": ["."], "write_boundary": ["pkg/core.py"]}
request = {
    "schema": "daodan/context-request/v1", "task_id": "change-1",
    "intent": "change", "query": "", "policy_version": "scope-v1",
    "read_boundary": ["."], "write_boundary": ["pkg/core.py"],
    "candidate": {"manifest": str(candidate.resolve())},
    "base": {"manifest": str(base.resolve())},
    "anchors": [{"entity_id": "pkg/core.py::helper"}], "diff": [],
    "proposed_edits": [{"entity_id": "pkg/core.py::helper"}],
    "mandatory_requirements": [{"id": "REQ-1", "support": [
        {"predicate": "current_source", "entity_id": "pkg/core.py::helper"}]}],
    "required_gates": [{"id": "unit-tests"}, {"id": "review"}],
    "budget": {"max_candidates": 100, "max_edges": 1000, "max_rounds": 20,
               "max_seconds": 60, "max_input_tokens": 20000,
               "max_output_tokens": 5000},
}
plan = prepare_scope(request, authority=authority,
                     indexes={"retrieval": str(text_index.resolve())})
plan = advance_scope(plan, request, authority=authority, max_steps=50)
reference = persist_scope(plan, candidate.parent / "scope-1.json",
                          authority=authority)
```

Paths in boundaries are exact project-relative POSIX prefixes. `.` covers the
project; an empty write list permits no edits. Requests may narrow authority,
never enlarge it. Inventory exclusions still apply. Artifact paths are absolute,
inside the project, and reject symlinks and Windows reparse ancestors.
The publisher accepts a new JSON sibling of the candidate manifest and preserves
existing destinations. Filesystems without exclusive hard-link publication fail
closed. The coordinator records the artifact reference in its existing run.

SQLite snapshot descriptors contain only `manifest`; `base: null` is exploratory.
`anchors` and `proposed_edits` use the retrieval owner's exact entity/path/symbol
or line anchors. `diff` accepts these anchors or `{path, ranges: [{start, end}]}`.
The snapshot comparison remains the canonical source of changed symbols and
caller obligations, even when the supplied diff is narrower.

Optional `indexes` keys are `retrieval`, `engine`, `base_engine`, `cards` and
`embedding_result`. Dense results must already have been produced and receipted
by the embedding worker. Default engine paths are bound even when absent. A
missing, sampled, conflicting or valid empty engine pass stays distinguishable.
Text search verifies its entire inventory; a narrower read boundary suppresses
that search with an explicit gap. Graph metadata can report pointers outside the
read boundary, but source bytes outside it are never read by this planner.

## Evidence, intervention and validation

`analysis` holds read candidates with anchors, reasons and provenance.
`edit_candidates` contains only unambiguous explicitly proposed sites inside the
write boundary. `potential_impact` holds canonical caller/contract leads.
Body-only changes retain caller validation obligations without prescribing edits.
Removed and rewritten bindings retain base witnesses. Unsupported edge kinds,
unresolved references and incompatible profiles remain gaps, never independence.

Requirements, gates and canonical impact obligations are registered before
discovery limits. If the impact producer caps its detailed list, its uncapped
component inventory supplies conservative inspection obligations for the tail.
Those items retain an unknown classification and force `needs_split`.
Outside-write proposals and outside-read pointers remain reported obligations.
Neither semantic similarity nor a test-shaped filename proves requirement coverage.

Supply incremental evidence through `advance_scope(..., evidence=...)`:

- `source_packets`: actual `source_reader.read_packet` results. Bindings, current
  hashes, numbered source bytes and complete required spans are reverified.
  This establishes `source_provided`, not that a model understood the code.
- `anchors`: explicit localization using the same exact anchor representation.
- `leads`: unverified discovery records with `entity_id`; these satisfy no support.
- `usage`: records with unique `id`, nonnegative `input_tokens`, `output_tokens`
  and `measurement: actual|estimated`. Replaying identical IDs adds no cost;
  changing an existing observation is rejected. Missing counts stay unobserved.
- `attempted_actions`: IDs from `actions`; an unproductive equivalent action is
  exhausted for these inputs. Fresh source evidence can satisfy its source gap.
  Requirements sharing a source predicate share one action and retry key.

Only `current_source` support is mechanically recognized. Other predicates and
requirements with no supplied support remain missing for their owner to resolve.
Gate status always remains open, including after its test source is supplied.

## Budgets and recovery

`max_steps` is a per-call checkpoint quota. Candidate, edge, round, wall-time,
input-token and output-token caps are independent and cumulative. Prep and
freshness checks count as machine time. Time limits are cooperative, so an
individual provider query or filesystem call can finish after the cap; no hard
preemption is promised. Counts record supplied actual/estimated observations;
they do not include unobserved future calls or guarantee a recipient context
window. P7 owns packet costs including wrappers and tokenizer results.

The frontier orders mandatory source targets, exact/diff/proposed sites, canonical
impact, retrieval leads and indirect neighbors. Retrieval keeps its producer's
relevance rank; remaining ties use entity identity. Each analysis row carries
`required_detail`: `source` for requirement targets and anchors (exact anchors,
exact or traceback retrieval matches, diffs, proposed sites, localization
evidence) and for changed symbols under `change`, `test` and `finish`; `lead`
for every other origin. Detail only strengthens; a lead never weakens an anchor.
Deduplication keeps the strongest priority. Outside-read targets cannot establish
localization or a ready attempt. It stores a partially expanded neighbor list and
offset, visited identities, all discovered obligations, usage observations and
exhausted action keys. Cycles terminate by deduplication, without a hop-based
completeness claim. A JSON round trip preserves the next deterministic action.
Wall-clock stopping positions may differ between runs.

`incomplete` retains work; `needs_localization` needs precise evidence;
`needs_split` retains residual work or oversized obligations at a cumulative cap.
`ready_for_attempt` permits a localized attempt only. All plans retain
`task_complete: false`, `validation_complete: false`, `write_authorized: false`
and `stop_calibration: uncalibrated`. An empty frontier closes no task.

Resume requires the original request and fresh independent authority. The cursor
binds full state, both snapshots, resolver/parser, indexes including absent inputs,
effective boundaries and policy. Allowed source is checked before and after
advancement; changed artifacts reject the checkpoint. This is an optimistic
concurrency check, not a lock or proof against edits after return. Re-prepare after
a changed input, retaining open obligations in the owning process. Raising a
cumulative cap changes the request and requires an explicit new preparation.
An integrity digest is not a substitute for run authorization or a secret signature.
