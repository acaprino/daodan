---
adr_id: ADR-0001
version: 1
title: Use an LLM prompt for Step 0 work-graph proposals
status: Proposed
author: Alfio Caprino
scope:
  paths:
    - plugins/project-lifecycle/skills/lifecycle-method/**
    - plugins/model-routing/skills/model-routing/references/task-routing.md
    - plugins/senior-review/skills/review-preparation/**
    - evals/project-lifecycle/work-graph/**
  modules:
  domains:
    - work-graph-composition
    - model-routing
    - reviewer-composition
    - offline-execution
governs_symbols:
depends_on:
created_from_task: work-graph-step0-llm-20261023
proposed_on: 2026-10-23
proposed_at_sha: 2dce83a354653f276e608cfb4817c915e69a6112
accepted_on: null
accepted_at_sha: null
last_verified_sha: null
retired_on: null
retired_reason: null
supersedes:
superseded_by: null
changes:
---

# ADR-0001: Use an LLM prompt for Step 0 work-graph proposals

<!-- adr-header:start -->
Version 1 · Proposed 2026-10-23 by Alfio Caprino
<!-- adr-header:end -->

## Context and Problem Statement

The [work-graph design](../superpowers/specs/2026-10-20-system1-work-graph-composition-design.md#11-responsabilità)
separates semantic planning, graph compilation and execution. Its S1/S2 strategy
starts with archetypes and deterministic composition. The
[experiment](../../evals/project-lifecycle/work-graph/README.md) accepts a supplied
plan and simulates execution; it does not yet compose a whole plan from context.

The user selected a simpler first implementation: "Step 0 usiamo prompt llm",
followed by "Un domani faremo tutto offline". This record changes the initial
proposal strategy and records the offline destination. It does not claim either
path is implemented.

The user extended this direction to model routing and reviewer composition:
their semantic decisions may use prompted LLMs in Step 0, with offline operation
as the shared destination. This clarification stays within graph orchestration;
it does not start a separate router or reviewer implementation.

## Decision Drivers

- Start with a prompted LLM and control the cost of the whole run.
- Reuse lifecycle planning, reviewer definitions, router and protocol contracts.
- Preserve required coverage, independent verification and existing authorization.
- Keep the graph proposal replaceable by a local implementation.
- Target a trained local decision model with CPU inference for all three components.

## Decision

**Step 0 uses a prompted LLM to propose the work graph.** The planner may produce
the structured proposal in its existing call; a second call merely to reformat an
already adequate plan is unnecessary. A complete deterministic template composer
is not a prerequisite for Step 0.

The input is a bounded packet: approved objective and requirements, scope,
relevant map evidence with gaps, declared contracts, permitted operators and
roles, mandatory gates, authorization and budget. The output names activities,
their dependencies and contract references, inputs/outputs, conditions, bounded
repair transitions and unresolved questions. Use the owning graph contract when
implemented; this decision creates no second production schema.

The model proposes semantics. Code validates the structure and policy, binds
identities, and materializes the executable graph. Structural validity does not
prove that the plan meets the requirements. Missing evidence remains a gap and
semantic approval remains with the existing planning/review process. Dependency
cycles are rejected; repair loops are explicit, bounded control transitions with
new attempts or revisions, preserving the DAG of dependencies for each attempt.

The graph proposer is an LLM job, so the coordinator routes it through the current
[per-request routing method](../../plugins/model-routing/skills/model-routing/references/task-routing.md).
Each subsequent LLM job receives its own assignment. Mechanical checks need no
model. The proposer cannot choose model identities, waive required gates or turn
its output into permission to dispatch. Existing routing confirmation and host
capability rules continue to apply; this decision grants no blanket binding.

### Shared Step 0 strategy

Graph proposals, model routing and reviewer composition share the same rollout:
prompted semantic decisions first, replaceable local implementations later.
Each retains its existing owner and validation boundary.

| Component | Prompted decision in Step 0 | Code-owned responsibility |
|---|---|---|
| Work-graph proposer | Propose activities, dependencies, conditions and bounded repair transitions from the approved objective and evidence. | Validate and materialize the graph under the declared contracts and policy. |
| Model router | Classify the individual LLM task and report its signals through the existing classifier prompt. | Select a permitted model and effort with `task_router.py`; preserve routing floors, capability checks and confirmation rules. |
| Reviewer composer | Propose applicable specialist identities, scopes and compatible groupings from requirements and evidence. | Resolve identities and assemble canonical specialist bodies, preserving required coverage and independent review. |

The router already separates prompted classification from deterministic model
selection. Canonical reviewer assembly is implemented in
[`composition.py`](../../scripts/daodan/composition.py), under the
[review binding method](../../plugins/senior-review/skills/review-preparation/references/composition.md).
That assembly does not establish the prompted semantic selection or general
graph proposal generation described here, which remain to be implemented and
verified. It also does not prove execution on installed hosts. The
[reviewer design](../superpowers/specs/2026-10-22-specialized-reviewers-design.md)
continues to own specialist content: the prompt selects and groups references;
it does not freely rewrite the specialist methods. Mandatory checks cannot be
dropped to reduce tokens, and incompatible or independent reviews stay separate.

### Conversational clarification

When an essential human decision is missing after consulting applicable evidence
and existing decisions, the coordinator opens a proportionate clarification:
a direct question, a targeted interview or an exploratory decision map. The
[conversational specification](../superpowers/specs/2026-10-24-conversational-decisions-and-work-graphs-design.md)
defines the boundary, pending consumers, response validity and plan revision.
Operational prototypes retain their methods and completion gates. The decision
map is Daodan's own method, written from Wayfinder's ideas without copying its
text, because upstream Wayfinder is user-invoked only; its provenance and an
upstream watch are recorded. Human answers and
grants remain distinct from model-generated orchestration decisions, including
in the future local CPU path. This integration remains proposed.

### Cost control

Reuse the existing plan and canonical specialist bodies. Supply only relevant
context, preserving completeness requirements and explicit gaps; return compact
structured output rather than repeated prose. Reuse a validated proposal only
while its request, candidate, context, prompt/contract and policy bindings remain
valid. Reuse model assignments only under the router's own freshness rules.
Repairs receive the relevant validation errors and context, within the run's
budget. Track planning, routing, execution, verification and retry costs together;
no fixed saving or guaranteed call count is claimed.

### Offline destination

The user clarified the destination: train a local decision model that can run
inference on CPU for graph proposals, routing classification and reviewer
selection/grouping. These three semantic decisions are intended to move from
prompted LLM calls to that learned local capability. The model family, training
method and any CLI interface remain undecided; no named technology is selected.
The CPU requirement concerns inference, not the still-undecided training setup.

Step 0 must keep task inputs and structured decision outputs independent of the
prompt provider and transport. Later local implementations use the same owner
contracts, directly or through an adapter; consumers must not require a remote
chat API or prompt transcript to interpret a decision. Code continues to enforce
graph admission, model-selection policy and canonical reviewer assembly. The
learned model cannot waive gates, coverage, independence or authorization.

The wider offline target still covers planning, routing, worker/reviewer execution
and checks for local project work without external service calls. The decision
model supplies orchestration decisions; it does not by itself provide the models
or tools needed to perform the worker tasks. Weights, catalogs and required tools
must be locally available. Local decision inference alone does not prove the
whole run is offline. Step 0 does not require training or an offline runtime.

## Verified Interview Examples

These examples express the selected requirements and existing safeguards. They
are acceptance scenarios, not evidence of an executed graph implementation.

- **EX-001** (nominal): An approved change needs editing, tests and independent review. The prompted LLM proposes those activities and justified dependencies; validation preserves every mandatory gate before dispatch.
- **EX-002** (boundary): The context lacks a producer/consumer contract needed to order two tasks. The proposal declares the missing contract and the dependent work stays open until it is resolved.
- **EX-003** (rejection): A proposal uses an unknown role, omits a required review or adds circular task prerequisites. Validation refuses that proposal; no affected worker starts from it.
- **EX-004** (future offline): A representative local run completes planning, routing, execution and verification with network access disabled and only local models/catalogs/tools. A provider lookup or remote model call fails this criterion.
- **EX-005** (composition boundary): A prompted reviewer selection proposes compatible specialists for one task. Assembly reuses their canonical bodies and preserves required coverage; unknown identities, omitted mandatory checks or a grouping that compromises independence prevent admission.
- **EX-006** (future local decisions): With network and GPU access disabled, the trained decision model handles representative graph, routing-classification and reviewer-selection inputs through the same owner contracts. Existing validators still reject invalid decisions; correctness and CPU latency/resource use are measured before adoption.

## Rejected Alternatives

- **RA-001**: Requiring a complete offline or deterministic composer before Step 0. The user selected a prompted LLM as the first implementation.
- **RA-002**: Treating model-generated JSON as executable authority. Shape validation alone proves neither coverage nor authorization.
- **RA-003**: Regenerating unchanged plans, reviewer instructions and routing bindings on every step. Reuse valid owner-bound artifacts and measure total cost instead.

## Enforceable Invariants

- **INV-001**: Every admitted proposal is bound to its actual inputs, graph contract and policy; stale bindings cannot authorize execution.
- **INV-002**: Required gates, declared scope, budget and reviewer independence survive generation, validation and repair. A missing prerequisite remains explicit.
- **INV-003**: Every LLM job, including graph proposal generation, follows the current router and host binding rules. The graph never embeds an invented model assignment.
- **INV-004**: Repair loops have recorded exit conditions and bounded attempts; circular task prerequisites never become an executable dependency graph.
- **INV-005**: An offline claim covers the whole exercised local run, including routing and worker calls. No network fallback is silent.
- **INV-006**: Replacing any of the three prompted decisions with trained local CPU inference preserves its owner contracts, model-routing safeguards, required review coverage and independence. Decision consumers do not depend on a remote provider or prompt transport.

## Consequences

Lifecycle owns the prompted proposer; protocol owns admission and run records;
senior-review owns reviewer content and coverage; host adapters own execution.
Existing reusable implementation comes first. Any new dependency requires its own
fit and compatibility decision. Later offline implementations retain the same
accepted input/output and validation boundaries rather than redesigning consumers.

This record takes precedence for the initial writer strategy over template-first
readings of S1/S2 in the earlier design. It leaves that design's remaining work and
the specialist-composition implementation separate. The record remains `Proposed`
until implementation and the repository's promotion requirements are satisfied.

## Confirmation

The user's statements above authorize recording this direction. Documentation
validation checks this record and its links. Implementation must separately
exercise EX-001 through EX-003 with real proposal generation and rejected inputs,
verify per-job routing/dispatch bindings and EX-005, and measure whole-run cost.
EX-004 and EX-006 belong to the later offline milestone. No runtime, model-quality or cost result is claimed
by this documentation change.
