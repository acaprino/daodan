---
adr_id: ADR-0002
version: 1
title: Keep the complete Work Controller engine in Daodan
status: Proposed
author: Alfio Caprino
scope:
  paths:
    - plugins/project-protocol
    - plugins/work-controller
    - plugins/model-routing
    - plugins/senior-review/skills
    - plugins/project-lifecycle/skills/lifecycle-method/references/interview.md
  modules:
    - project-protocol
    - work-controller
    - model-routing
  domains:
    - run-state
    - clarification
    - decision-map
    - work-graph
    - model-routing
    - orchestration
    - runtime-input
    - usage-ledger
governs_symbols:
depends_on:
created_from_task: conversation-2026-10-24
proposed_on: 2026-10-24
proposed_at_sha: cab382f49e939e0c47cee969f8f046db4e69f30d
accepted_on: null
accepted_at_sha: null
last_verified_sha: null
retired_on: null
retired_reason: null
supersedes:
superseded_by: null
changes:
---

# ADR-0002: Keep the complete Work Controller engine in Daodan

<!-- adr-header:start -->
Version 1 · Proposed 2026-10-24 by Alfio Caprino
<!-- adr-header:end -->

## Context and Problem Statement

The source paths and measurements in this section describe the pre-migration
`project-protocol` at the recorded proposal revision. That plugin is retired by
this decision; its successor is `work-controller`.

`plugins/project-protocol/plugin.toml:1-21` ships one skill, one role and two
contracts, and eight plugins depend on it. Its content is four unrelated things:

- the run record: `skills/project-protocol/scripts/run_state.py` (1187 lines) and
  `contracts/work.toml` (126 lines), with the agenda and the pending questions
  (`contracts/work.toml:111`);
- model routing: `tier_router.py` (2806), `task_router.py` (1358), four more
  scripts (1926) and `references/model-catalog.json` (53928);
- the review roster, `scripts/review_roster.py` (745), which
  `docs/superpowers/specs/2026-10-20-system1-work-graph-composition-design.md:99-123`
  assigns to `senior-review`;
- shared working discipline and the `isolated-worker` role.

The name says none of this. Meanwhile
`docs/superpowers/specs/2026-10-24-conversational-decisions-and-work-graphs-design.md`
adds clarifications, a decision map with tickets and the composition of work
graphs. Shinatama needs the same capability for documents and presentations; three
of its plugins already depend on Daodan plugins (`business`, `digital-marketing`,
`frontend-review`) and no Daodan plugin depends on Shinatama.

Where do run state, clarifications, the decision map and graph composition live,
under a name that means something, usable by Daodan and Shinatama at minimal cost?

The shipped first split (`09156a0c1`) gives run ownership to
`work-controller@daodan`, routing to `model-routing@daodan` and the review roster
to `senior-review`. On 2026-10-24 the user chose an external Deadly Brain engine
with an internal router and mandatory YAML input. On 2026-10-25 the user instead
requested the complete engine only in Daodan, followed by retirement of the
separate repository. That reintegration direction supersedes the external
repository packaging; it does not authorize deletion before a verified transfer
and a separate scoped retirement grant. Model routing retains its existing local
owner rather than adding a second provider migration. The broader capability
contract remains [the conversational decisions specification, section 13](../superpowers/specs/2026-10-24-conversational-decisions-and-work-graphs-design.md#13-deadly-brain-il-motore-condiviso).

## Decision Drivers

- Minimalism, token consumption tending to zero, simplicity, no useless
  overengineering and no excess of zeal (user, 2026-10-24).
- One general-purpose engine for Daodan, Shinatama, Mukade and other consumers,
  without a dependency on those consumers.
- Usable alone, with the same runtime contract for a conversation, a template or
  an authored file.
- Standard-library core, with the narrowly scoped YAML parsing exception required
  by the runtime input decision. Reintegration retains the source engine's
  restricted PyYAML loader; the compiler remains standard-library only.

## Decision

Keep the complete process engine in `work-controller@daodan`, with no separate
Deadly Brain repository dependency or engine installation. Shinatama, Mukade and
other projects consume this provider; the engine requires none of their plugins.
Repository ownership does not introduce an engine-to-consumer dependency.
A process may require registered components supplied by its consumer,
which its own contract declares and the controller verifies. Consumer archetypes
and domain rules stay with their owners. Branches, worktrees, ADRs, commits,
code-specific operation names and mandatory software review are not universal
runtime assumptions.

The controller retains `work-record`, the shared working discipline and
`work-controller:isolated-worker` as their canonical owner. Runtime modules and
console assets live under `skills/work-record/scripts/work_controller/`; the
skill-owned `controller.py` is the CLI and MCP launcher. These are shipped by the
same five-host compiler as the rest of the plugin. Preserve the original license
and provenance.

### Implementation boundary

The transferred engine supplies immutable YAML graph admission, sequential
execution, SQLite attempts and journal, content-addressed artifacts, decision
tickets, conservative resume, a loopback console and read-only MCP. It is not
evidence that every capability below exists. Registered component discovery,
installed-host dispatch and stop handles, observed per-job models, semantic
memory, bounded loops, parallel execution and selective replan remain explicit
capability requirements with separate verification.

New definitions use `work-controller/process/v1`. The original
`process-controller/process/v1` and `deadly-brain/process/v1` definitions remain
accepted without rewriting their normalized identities or recorded digests.

Work Controller owns:

- **Composition or integrity-only validation.** It can build a complete process
  from context, an interview and consumer templates, or validate supplied process
  data without redesigning it or starting execution. Reuse a suitable archetype;
  an LLM proposes composition only when one is insufficient. Validation checks
  registered identities, capabilities, input/output contracts, dependencies and
  bounds. `graphlib` checks the acyclic dependency graph and computes its frontier.
  A public composition entry starts the interview from a free-text objective
  without requiring YAML first, and resumes an identified existing process.
  The coordinator can call the same method; both paths share questions and memory.
  The proposed functional entry name is `compose-process`; host registration and
  invocation syntax remain implementation work.
  The composer searches the actual harness inventory by component kind and
  verified interface, reusing suitable tools and specialists first. If the
  process contract permits it, it may define ad hoc jobs and prompts for a real
  permitted executor, or produce versioned scripts and tool/API call descriptions
  with input/output contracts and checks. These do not fabricate registered
  roles, tools or grants, replace mandatory specialists, or execute proposed work
  during composition or integrity-only validation. Section 13 of the canonical
  specification owns discovery, artifact checks and the distinction between
  generated task data and registered executors.
- **Runtime input.** YAML is mandatory for a single job, a graph or a bounded
  loop; conversations and templates produce the same YAML input. Admission binds
  an immutable YAML version and source digest to its validated normalized representation.
  Changes create a new revision and revalidation. A bounded loop has explicit
  limits and a stopping condition; iterations retain distinct attempts rather
  than introducing a cycle into the dependency graph. Internal records may
  remain JSON. YAML parsing is a narrow dependency exception, with safe data-only
  loading and resource bounds. The reintegrated runtime retains PyYAML through
  its isolated launcher; its dependency evidence and verification limits are
  recorded in the 2026-10-25 reintegration design.
- **Orchestration and continuity.** Runs, agenda, grants, gates, deliveries,
  recovery, checkpoints and resume; clarification questions, the generic interview,
  decision maps and tickets; durable context and evidence memory, session handover
  and addressed communication between agents. Memory retains source, scope and
  revision. Handover preserves open questions, active attempts and host handles.
  Communication or a stopped turn never substitutes for a delivered result.
- **Per-job model routing.** The existing `model-routing@daodan` owner supplies
  model selection and pricing; reintegration does not duplicate its policy or
  absorb that provider. Coordinators receive a concrete binding for every job
  that calls an LLM. Deterministic jobs need no model.
  Selection respects task capability, context, complexity, risk, host availability
  and the declared quality/cost policy. A binding is revalidated before dispatch
  and resume; the model actually applied remains an execution fact to verify.
- **Execution and accounting.** Actual execution uses verified host adapters that
  bind component identities, tools, model and effort to supported host mechanisms.
  The controller preserves per-job attempts, handles, results and a cost ledger,
  using the normalized usage and pricing work behind ADR-0003. Failed attempts,
  retries and orchestration costs count; missing usage is not zero. List-price
  comparisons, estimates and reported host costs remain distinct. Budget checks
  govern admission of new work and require an applicable spend grant to exceed a
  ceiling; they do not prove a hard billing cap or the ability to stop an active job.

The adapter must demonstrate dispatch, observation, interruption and recovery
capabilities before a process relies on them. A missing capability remains
explicit and prevents the affected operation; registration alone proves no
execution. Deployment as a standalone service or daemon has not been selected.

The existing routing method still requires human confirmation of each concrete
model proposal, with reuse only of an unchanged confirmed binding. This ADR does
not grant blanket approval or introduce an automatic run-wide policy. Any future
policy-based authorization needs an explicit contract and user authorization.

State stays under `.daodan/` of the main checkout, with the process store in
`.daodan/processes`. Existing `daodan/work/v1` records and the agenda preserve
their identities and evidence. An explicit record/process binding preserves
holder ownership, grants, questions, required deliveries and current-candidate
gates. A graph's terminal success cannot bypass those domain checks. This ADR
does not mark a transfer, runtime check or installed-host probe as verified.

Economy rules: code does the work and the model reads the result; each command
prints only what its step needs; the fewest skills, with short descriptions;
references load per step; no new schema where an existing one serves.

## Verified Interview Examples

These are acceptance scenarios, not evidence that the target runtime exists.

- **EX-001** (composition): A user invokes the composition entry with a document
  objective and no YAML. The interview reads context, searches the harness's
  actual capabilities, records missing requirements and real human answers, then
  produces YAML for the same admission path as a supplied file. A permitted ad
  hoc task uses a real executor. Resuming an existing process reuses its identity,
  evidence and questions. No coding lifecycle is imposed or proposed job started.
- **EX-002** (standalone and validation): With no Daodan, Shinatama or Mukade plugin
  installed, Work Controller validates a job, graph or bounded loop whose declared
  components are available. Integrity-only mode returns diagnostics without
  redesign or dispatch; execution requires its own admission and authorization.
- **EX-003** (rejection): A graph contains a cycle, a missing producer, an unknown
  component or an unbounded loop. Admission fails. Editing YAML after admission
  cannot alter an active revision; a new revision must pass validation.
- **EX-004** (routing and costs): Two jobs have different capability and risk
  requirements. Each receives its own confirmed model/effort binding. A retry has
  a new attempt and keeps both costs; missing host usage remains explicit.
- **EX-005** (continuity): A session stops with a worker active and a human question
  open. Handover and resume reconcile the host handle and checkpoint before any
  new dispatch, preserve the question and evidence, and do not duplicate effects
  or infer delivery. On a map of 40 tickets, `next` returns the relevant frontier
  ticket and question rather than the whole map.

## Rejected Alternatives

- **RA-001**: a third repository for the engine adds another release and
  installation boundary while the plugin can be consumed from Daodan. The
  original rejection was reversed by the external Deadly Brain direction on
  2026-10-24, then restored by the complete reintegration request on 2026-10-25.
  The historical external packaging does not govern this target.
- **RA-002**: keep `project-protocol` and add `work-controller` above it. Four
  unrelated concerns stay under a name that says nothing, and Shinatama gains a
  dependency.
- **RA-003**: a separate run-record plugin under a new name, below `work-controller`.
  Two plugins for one state, and the map would reference the agenda across a
  plugin boundary.
- **RA-004**: LangGraph, Temporal or transitions as engine. Each adds a framework,
  a server or a dependency for what `graphlib` and the record already cover. Not
  verified against current sources, because no adoption is proposed.
- **RA-005**: delegating the map to upstream Wayfinder. It is user-invoked only
  and keeps its state in the checkout's `.scratch/`.

The existing local `model-routing` provider remains the routing and pricing
owner. Reintegrating the external engine does not discard, copy or reimplement
that policy and does not require an external engine provider.

## Enforceable Invariants

- **INV-001**: the engine has no dependency on Daodan, Shinatama, Mukade or other
  consumer plugins and is owned only by `work-controller@daodan`. Routing retains
  its local provider; no external engine provider is required. The
  standard-library core permits only the separately reviewed YAML parser
  exception; this invariant does not prohibit that runtime dependency.
- **INV-002**: no Daodan plugin depends on a Shinatama plugin.
- **INV-003**: ticket blocks and work-graph dependencies are acyclic; every
  admitted YAML input has an immutable version and digest. Loops are bounded;
  repairs and iterations preserve distinct attempts and historical evidence.
- **INV-004**: no `work-controller` command prints a whole map or record; output is
  bounded to the requesting step.
- **INV-005**: only a human answer closes a ticket that needs the human; closing a
  ticket never satisfies a gate. Validation, model selection, communication and
  cost accounting likewise grant no authorization or completion on their own.

## Consequences

- The completed first split is retained as transition evidence. Its rename and
  routing/roster moves must not be mistaken for the target orchestrator being
  delivered. The review roster remains owned by `senior-review`.
- Keep the engine in the existing plugin and compiler. Consumers require
  `work-controller@daodan`; no marketplace extraction, third compiler copy or
  external engine registration is needed. Model-routing keeps its identity.
  Retiring the separate repository follows transfer verification and its own
  scoped authorization; source transfer does not remove runtime archives.
- Generalize run contracts and operation identity without embedding each
  consumer's lifecycle. Preserve record provenance, context, checkpoints, grants
  and evidence through migration. Admit YAML through one parser/validation path.
- Implement node-to-binding dispatch, verified host execution and the per-attempt
  usage ledger; verify installation and recovery on supported hosts before
  migrating them. Claims of isolation, model application or budget enforcement
  require runtime evidence separate from compiler checks.
- Realign consumer dependency documentation, contracts and the affected
  specifications with this ownership decision. Parser adoption, deployment
  evidence and any change to routing authorization remain explicit checks.

## Confirmation

The following are future verification obligations, not results of this ADR edit:

- Dependency/build checks reject engine-to-consumer edges and a required external
  routing plugin, preserve the Daodan-to-Shinatama prohibition and verify the
  narrow parser exception. Compiler and generated-document checks stay required.
- Contract checks cover conversation/template/file convergence on YAML, both
  operating modes (compose, integrity-only, execute/resume), immutable admission,
  missing producers, cycles, loop bounds
  and frontier output. Parsing rejects executable YAML constructs and oversized
  or unsupported input through the selected parser's verified data-only contract.
- Routing checks cover per-job model and effort, required human confirmation,
  stale bindings, unavailable capabilities and observed-model discrepancies.
  Registry/compiler tests and installed-host probes report separate evidence.
- Continuity checks cover checkpoint recovery, session handover, addressed agent
  communication, duplicate answers, interruption, unknown worker state and retries
  without duplicate effects. Migration includes resuming a pre-split record.
- Ledger and budget checks cover idempotent attribution to job attempts, failed
  work and orchestration overhead, missing/approximate usage, price provenance
  and refusal to admit new work without an applicable spend grant at the ceiling.
  Completion still requires the process's own deliveries and gates.
