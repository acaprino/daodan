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
