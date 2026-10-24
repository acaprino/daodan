# Project Lifecycle

Five operations coordinate the same canonical owners used by standalone specialists:
assess, repair, change, verify and consolidate. Their entry points load
`project-lifecycle:lifecycle-method`, which prepares inputs, dispatches existing
roles and builds the plan. Specialist methods retain detection and remediation
ownership; lifecycle does not maintain parallel auditor prompts.

## The task cycle

`change` carries one task through seven phases, each a short unit of the method
loaded only when its phase starts:

| Phase | What happens | Unit |
|---|---|---|
| 1. Preflight | Git state, upstream distance, test baseline (`GREEN`, `KNOWN_RED`, `UNKNOWN_RED`), migrations and map freshness are probed; the user chooses `WORKTREE`, `BRANCH` or `IN_PLACE` | `preflight.md` |
| 2. Interview | One question per turn, anchored to a file and line, with real input and output from the code, until scope, examples, rejected alternatives and invariants are fixed | `interview.md` |
| 3. Record | A `Proposed` decision record under `docs/adr/`, whose claims about the code the premise auditor checks (a light review of kind `spec`) | `interview.md` |
| 4. Plan | Waves of micro-tasks with a `write_set` of at most four files, an oracle that must fail first and a verification command; the protocol helper's `plan-check` refuses overlapping waves; the premise auditor checks every path, symbol and oracle the plan cites | `waves.md` |
| 5. Execution | The stack's specialist writes each task from a closed brief and returns `OK`, `NEEDS_REPLAN` or `ORACLE_INVALID`; each wave is reviewed with shape `light` and sealed | `waves.md`, `worker-brief.md` |
| 6. Candidate | The whole candidate is reviewed with shape `branch`; blocking findings get at most two repair waves | `verify.md` |
| 7. Integration | Merge, promotion of the record to `Accepted`, incremental map update, documentation and the instruction loop block realigned, worktree removed and agenda row released | `finish.md`, `realign.md` |

`--plan-only` stops after phase 4; `--run-id` with that run continues the approved
plan from its first unsealed wave.
Initialization (`references/init.md`, run by `/daodan:init-project`) brings a project into the cycle: map, decision index, instruction
loop block and test baseline. `consolidate` alone realigns after a merge made
outside the cycle.

Four more units serve the steps around a task. `brainstorm.md` explores an idea
with the user, grounded in the map and the records, and ends in a brief for the
cycle, a note under `docs/ideas/` or nothing. `sync.md` brings other people's
commits in: fetch, a report of what arrived and whether it touches an open task,
fast-forward only, then the same realignment as a finish (`realign.md`), which
also promotes the records of tasks merged elsewhere. `retention.md` disposes of a
concluded run's own output. A bug fix without a known cause starts from
senior-review's `investigation-method`, whose reproduction test becomes the
fix's oracle. Every phase is also reachable through its own entry:
`/daodan:record-decision` for records, `/daodan:review-changes` for a review of a
changeset, a plan, a specification or a document, `/daodan:review-branch` for the
whole branch, and the other `/daodan:` commands. The density of each unit, and of what each phase holds in
one context, is capped by `tests/test_skill_load_budget.py`.

The design and its reasons are in
[the closed-loop harness design](../superpowers/specs/2026-10-18-closed-loop-harness-design.md).

Two separate entries serve project takeover and subsequent maintenance,
`/daodan:onboard-project` and `/daodan:run-maintenance`.
`handover` loads `handover-method` and produces an incoming consultant's dossier
inside an owned assess run. It explains purpose, modules and critical flows,
setup and test procedures, constraints, evidenced risks, real unknowns and a first
scoped work plan. It uses project-knowledge's explorer, onboarding writer and
guide reviewer, with semantic mapping only when needed. No project files or durable
guides are changed. `--checks=none` is the default; explicitly selected local checks
retain their environment, authorization and exact-candidate gates.

`maintain` loads `maintainer-method` and coordinates the complete Senior Maintainer
campaign: baseline team review, coherence assessment and roadmap, product
corrections, rationalization, final verification and consolidation. Defaults are
focus all, depth deep, guided pace and dry-run. Guided pace waits at the initial
brief and roadmap; dry-run ends at that roadmap. Fix and commit retain every
canonical owner's scope, acceptance, recovery and verification requirements.

Handover never starts maintain automatically. An explicit maintain request can
name `--from-handover RUN_ID`; that dossier must match its current project and
scope before its evidence is reused, and transfers no permission to edit.
Maintain records its resolved request and chain in each active stage run, carries
exact run IDs forward and resumes only named identities. Earlier completed stages
validate historically; the final verify result must validate against the current
project. Neither new entry adds a protocol operation or a TOML workflow executor.
Their coordinators and specialist bindings render through every host adapter.

assess produces evidence and a dependency-aware plan across knowledge, structure,
tests and workspace artifacts. repair validates an exact run/plan and applies only
authorized compatible remedies. change covers bootstrap, feature, bugfix, refactor
and migration. verify binds checks to the actual candidate. consolidate preserves
verified experiment conclusions before retaining or disposing of owned output.

A requested project-wide architectural rationalization starts with full static
Codebase Map context, or a validated matching run. Suite rationalization uses the testing
owner across the declared layers; instruction consequences use project-knowledge
for canonical updates, regeneration and loading evidence. Severe evidenced defects
take priority over cosmetic cleanup. Small scoped changes retain proportional
checks, and static context never establishes runtime behavior.

Use --focus=knowledge|structure|tests|artifacts|all and
--depth=quick|standard|deep. Default assessment is one initial quick pass.
The plan discloses expensive context steps, unavailable dimensions and commit-only
cleanup before application. Unknown token consumption stays unknown.

State belongs in .daodan/runs/<id>/ of the main checkout, beside the agenda. Resume the branch's task; alternative dedicated
roots must stay inside the project. The work-controller helper validates identity,
snapshots, revisions, deliveries and required gates. No arbitrary workflow executor
or automatic optional-specialist registry is introduced.

--fix permits scoped edits, --commit additionally permits commits; application
subtraction retains its commit-only prerequisite. Structural findings that require
a design choice stay open until that choice has an accepted implementation plan.
--purge requires a separate explicit grant for concluded owned artifacts. Retention is confined, fingerprinted
and resumable, preserving necessary evidence and rejecting links or changed paths.

Native specialist reports remain intact and are referenced by the common work
record and result envelope. A failed delivery or unavailable mandatory check
prevents a successful completion claim. Default quick assessment selects at most
five workers, including workers from reused documentation methods, and declares
what it did not examine.

change, repair and verify review their exact candidates through the same
senior-review engine, including applicable React, TypeScript and platform workers.
The preparation receives this run's scope, baseline and candidate before dispatch,
including new untracked files. The assessment's quick worker cap does not silently
remove required correctness dimensions from a candidate gate. Mandatory providers
and their installation closure are listed in the generated reference below.

### Context adapter usage

`skills/lifecycle-method/scripts/cycle_packets.py` turns one task of the run into a
revision-bound receipt of codebase context. It calls only the public protocol and
map command lines, makes no model call and writes no source. The coordinator owns
dispatch, refresh and the run update.

```text
cycle_packets.py preflight    --config C.json --request R.json --recipient P.json
cycle_packets.py task-packet  --config C.json --request R.json --recipient P.json --task-id T1 --previous PREFLIGHT_RECEIPT
cycle_packets.py post-task    --config C.json --request R.json --recipient P.json --task-id T1 --previous TASK_RECEIPT
cycle_packets.py verify       --config C.json --receipt RECEIPT
```

- **Config:** `project`, `records_root`, `run_id`, `manifest`; `protocol` and
  `provider` as argument arrays (the work-record helper and `snapshot.py`);
  optional `indexes` (retrieval index path), `source_root`, `base_manifest`.
- **Request and recipient:** `daodan/context-request/v1` and the recipient fields
  of `references/context.md`. The adapter fills `task_id`, boundaries, candidate
  and base from the record, so a task's `write_set` and requirements bind the
  request.
- **Order:** `preflight` before the first wave, one `task-packet` per task,
  `post-task` at each barrier. Refresh the map into a new manifest and rebuild its
  retrieval index and edges before `post-task`.
- **Output:** one JSON receipt per stage under the run's `context/` directory, each
  with the packet, the map slice, residual obligations and a digest. Re-running
  the same stage returns the same receipt; changed inputs start a new attempt.
- **Exit status:** 0 prepared; 1 a refused operation (a stale receipt, a provider
  error, a timeout), with a one-line reason; 2 an unreadable or invalid input
  document.
- **Verify:** `verify` reports `needs_recipient_check` because the command line
  cannot count the recipient's tokens; the dispatcher calls `verify_cycle(...,
  token_counter=...)` with its own counter before sending.
- **Time:** the provider call may run for the request's `max_seconds`, at least 120
  seconds. A `needs_split` packet is a valid receipt: narrow the task's scope or
  anchors and prepare it again.

Static evidence, runtime exercise and installed-host probes are distinct.
Read [the migration](../migration-to-coherent-harness.md) and
[architecture](../superpowers/specs/2026-10-07-daodan-coherent-harness-design.md).

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `2.3.0`. **Source:** [plugin.toml](<../../plugins/project-lifecycle/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [abstraction-architect](<abstraction-architect.md>), [clean-code](<clean-code.md>), [codebase-map](<codebase-map.md>), [dependency-audit](<dependency-audit.md>), [model-routing](<model-routing.md>), [moe](<moe.md>), [peer-review](<peer-review.md>), [platform-engineering](<platform-engineering.md>), [project-knowledge](<project-knowledge.md>), [python-development](<python-development.md>), [react-development](<react-development.md>), [repo-hygiene](<repo-hygiene.md>), [report-rendering](<report-rendering.md>), [senior-review](<senior-review.md>), [skill-catalog](<skill-catalog.md>), [testing](<testing.md>), [typescript-development](<typescript-development.md>), [work-controller](<work-controller.md>) |
| Direct external | None |
| Local closure (20) | [abstraction-architect](<abstraction-architect.md>), [clean-code](<clean-code.md>), [codebase-map](<codebase-map.md>), [dependency-audit](<dependency-audit.md>), [model-routing](<model-routing.md>), [moe](<moe.md>), [peer-review](<peer-review.md>), [platform-engineering](<platform-engineering.md>), [project-knowledge](<project-knowledge.md>), [project-lifecycle](<project-lifecycle.md>), [python-development](<python-development.md>), [react-development](<react-development.md>), [repo-hygiene](<repo-hygiene.md>), [report-rendering](<report-rendering.md>), [senior-review](<senior-review.md>), [skill-catalog](<skill-catalog.md>), [testing](<testing.md>), [text-humanizer](<text-humanizer.md>), [typescript-development](<typescript-development.md>), [work-controller](<work-controller.md>) |
| External closure (2) | `developer-essentials@claude-code-workflows`, `mattpocock-skills@mattpocock` |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `repository.write`, `shell.execute`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `project-lifecycle:lifecycle-method` | Coordinate complete AI development work across code, tests, project knowledge and artifacts. TRIGGER WHEN: the user wants to brainstorm or explore an idea before building, initialize or set up a project, diagnose project health or technical debt, build a feature, fix a bug, refactor code, check task status, continue an open task, finish and merge a task, sync upstream, or run a daodan lifecycle command. DO NOT TRIGGER WHEN: the user requests code explanation without investigation or changes, wants an isolated specialist audit (use senior-review, codebase-map or testing directly), or only needs a problem investigated without fixing it (use senior-review:investigation-method). | [lifecycle-method](<../../plugins/project-lifecycle/skills/lifecycle-method/SKILL.md>) |
| Skill | `project-lifecycle:maintainer-method` | Coordinate the complete Senior Maintainer rationalization campaign. TRIGGER WHEN: the user wants a whole project brought back into good shape through a coordinated multistage campaign, or runs /daodan:run-maintenance. DO NOT TRIGGER WHEN: an intake dossier is sufficient (use handover-method), or an individual diagnosis or change covers the request (use lifecycle-method). | [maintainer-method](<../../plugins/project-lifecycle/skills/maintainer-method/SKILL.md>) |
| Skill | `project-lifecycle:handover-method` | Coordinate an evidence-based consultant intake dossier. TRIGGER WHEN: the user asks to be onboarded, walked through an unfamiliar codebase, given a project takeover or intake dossier, or runs /daodan:onboard-project. DO NOT TRIGGER WHEN: being new to a project is only background for a code change (use lifecycle-method), correcting and rationalizing the project (use maintainer-method), or writing durable repository documentation (use project-knowledge:project-knowledge). | [handover-method](<../../plugins/project-lifecycle/skills/handover-method/SKILL.md>) |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/project-lifecycle](<../../exports/claude/plugins/project-lifecycle>) | `native` | No workflow entry points |
| copilot | [exports/copilot/plugins/project-lifecycle](<../../exports/copilot/plugins/project-lifecycle>) | `native` | No workflow entry points |
| codex | [exports/codex/plugins/project-lifecycle](<../../exports/codex/plugins/project-lifecycle>) | `adapted` | No workflow entry points |
| pi | [exports/pi/plugins/project-lifecycle](<../../exports/pi/plugins/project-lifecycle>) | `adapted` | No workflow entry points |
| opencode | [exports/opencode/plugins/project-lifecycle](<../../exports/opencode/plugins/project-lifecycle>) | `native` | No workflow entry points |

### Additional shipped contracts and mechanisms

- Neutral policy: [run-write-confinement](<../../plugins/project-lifecycle/policies/run-write-confinement.toml>). Enforcement is documented in the policy and host reference.

<!-- daodan:reference:end -->
