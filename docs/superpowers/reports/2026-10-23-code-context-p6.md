# P6 progressive scope planner

The planner registers requirements, gates, proposed sites and canonical
cross-revision impact before discovery budgets. It produces separate analysis,
edit-candidate, potential-impact, validation, deferred, unresolved and outside-
boundary inventories, with reasons and source/edge provenance.

`prepare_scope` and `advance_scope` require independent authority from the owning
run. Snapshot descriptors live in the request; authority is supplied again on
resume. This refines the proposed API so a serialized request or checkpoint
cannot enlarge permissions. `persist_scope` publishes an exclusive immutable
JSON artifact beside the candidate snapshot. Operational state stays in the
existing project-protocol run. The [API reference](../../../plugins/codebase-map/skills/map-method/references/scope.md)
documents inputs, evidence and recovery.

The implementation reuses the canonical stale-callers classifier, exact/FTS/dense
retrieval, effective lexical/Jedi references and verified source reader. A capped
impact result retains its uncapped component inventory as conservative inspection
obligations. Missing detailed classifications force `needs_split`; no second
impact classifier guesses them. A narrow read boundary suppresses whole-index
search, and a foreign retrieval binding is rejected before its source is read.

The checkpoint retains stable frontier order, an active neighbor offset, visited
identities, cumulative budgets, usage observations and exhausted action keys.
Cycles use deduplication rather than fixed hops. Input changes and altered cursor
state are rejected. Source evidence must match current bytes and preserve the
reader's full-file fallback. Similarity supplies leads only. Neither source
availability nor `ready_for_attempt` closes validation or authorizes edits.

Independent review reproduced two medium defects. The final planner retains the
strongest seed priority so mandatory/exact targets precede peripheral retrieval
leads under a small cap, and only readable accepted targets establish localization.
Both cases have independent real-provider RED/GREEN regressions. Original review
evidence and the coordinator's fix disposition remain separate in the run.

Machine execution makes no model/network calls and starts no embedding runtime.
Repeated per-file setup was measured and replaced by one verified batch per
pre/post check, retaining freshness checks. Token usage observations remain
actual/estimated and independent for input/output; absent observations do not
prove zero whole-workflow token use. Time caps are cooperative, and stopping
remains `uncalibrated`.

Verification, immutable review inputs, RED/GREEN logs, exact candidate hashes,
owned commit and remote workflow results belong to the linked run
`.tritech/daodan/runs/code-context-p6-20261023/`. The delivery record distinguishes
the isolated owned candidate from concurrent shared-checkout changes. It records
unavailable optional dependencies and any independent review dispositions.

P7 still owns recipient packet packing, prerequisite closure and actual tokenizer
budgets including wrappers, plus CLI/MCP endpoints. P8/P9 connect those packets to
process consumers; P10 measures task quality and whole-flow context/token savings.
P6 makes no installed-host execution, runtime application coverage or measured
whole-flow savings claim.
