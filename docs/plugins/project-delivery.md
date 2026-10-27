# Project Delivery

Project Delivery coordinates analysis, debugging, fixes, features and complete
project documentation. It owns decision records and the delivery cycle:
grounded specifications, bit-sized implementation plans, adversarial plan review,
Work Controller graph execution, model-routing bindings, verified atomic commits, safe
continuation, candidate review, authorized merge and realignment. It can be used
without the `daodan` command umbrella. Specialist methods retain detection,
documentation and remediation ownership.

## Decision records and project documentation

Brainstorming turns the chosen approach into a project specification in
`docs/specs/YYYY-MM-DD-<slug>-design.md`, unless the user or project explicitly
chooses another destination. It records intent, users, scope, constraints,
alternatives, observable examples and invariants, separating user decisions from
assumptions and open questions. Existing specifications, including historical
branded paths, are reused without implicit moves or duplicate interviews.

The specification is reviewed and its exact bytes approved before planning or
scaffolding, also on projects without ADRs. The run's `intent.md` links its path,
SHA-256 and recorded approval; plans and worker briefs carry that binding.
Changed bytes reopen approval and dependent plans. Resume and final review
recheck the binding. These are coordinator obligations, not a new mechanical gate.

Standalone initialization uses that same approval prerequisite before every
scaffolder. Missing or stale approval returns through brainstorming only until
the specification is approved, then resumes initialization. Existing approval and
answers are reused; initialization does not start feature execution. Documents
and run records can already exist in the caller's scaffold root and are preserved.

`adr-method` creates, resolves, validates, approves, versions and verifies separate
technical decisions under `docs/adr/`, citing the specification instead of copying it. [Decision records](../decision-records.md)
describes states, versioning and drift. `frd-method` manages requirements,
people, organizations, locations, relations, exact evidence spans and manual
corrections. `project-bootstrap` drafts missing ADR/FRD from verified sources;
generated artifacts remain Proposed until explicit approval.

## The task cycle

`change` carries one task through seven phases, each a short unit of `delivery-method`
loaded only when its phase starts:

| Phase | What happens | Unit |
|---|---|---|
| 1. Preflight | Git state, upstream distance, test baseline, migrations and map freshness are probed; the user chooses `WORKTREE`, `BRANCH` or `IN_PLACE` | `preflight.md` |
| 2. Interview | One question per turn, anchored to code evidence, until scope, examples, rejected alternatives and invariants are fixed | `interview.md` |
| 3. Specification | A light `spec` review checks the project specification; its exact bytes need approval before planning. Separate ADRs retain their own approval | `interview.md` |
| 4. Plan | Bit-sized tasks carry bounded write sets, base-failing oracles and verification commands. An adversarial `plan` review must be delivered with PASS on the exact plan digest and current bytes before any task enters `running` | `waves.md` |
| 5. Execution | A specialist writes each task. The coordinator reruns verification and a light changeset review on the uncommitted candidate, then commits atomically only after PASS and authorization. Snapshot, verification, review and commit SHA must match; later edits invalidate the evidence | `waves.md`, `worker-brief.md` |
| 6. Candidate | The whole candidate receives a branch review; blocking findings get at most two remediation waves | `verify.md` |
| 7. Integration | After current-candidate validation and merge authorization, the branch is merged, the ADR verified, map and documentation realigned, and the workspace closed | `finish.md`, `realign.md` |

`--plan-only` stops after phase 4; `--run-id` resumes the approved plan from its
first unsealed wave. An interrupted commit is reconciled from HEAD and scoped
bytes, never retried blindly or rolled back through `HEAD~1`.

Initialization brings a project into the cycle with its map, optional decision
index, instruction loop block and test baseline. `brainstorm` writes and reviews the design, then offers build, keep or drop;
`sync` fast-forwards and realigns; `retention` handles only concluded run output.
The density of every unit and phase context is capped by
`tests/test_skill_load_budget.py`.

The original cycle design is in
[the closed-loop harness design](../superpowers/specs/2026-10-18-closed-loop-harness-design.md);
[ADR-0006](../adr/ADR-0006-adr-project-delivery.md) records the extraction and
pre-commit evidence contract; [ADR-0007](../adr/ADR-0007-griffin-drkerr-evolution.md)
records the broader delivery, FRD and Work Controller boundaries.

### Context adapter usage

`skills/delivery-method/scripts/cycle_packets.py` turns one task into a
revision-bound receipt of codebase context. It calls only public protocol and map
command lines, makes no model call and writes no source. The coordinator owns
dispatch, refresh and run updates.

```text
cycle_packets.py preflight    --config C.json --request R.json --recipient P.json
cycle_packets.py task-packet  --config C.json --request R.json --recipient P.json --task-id T1 --previous PREFLIGHT_RECEIPT
cycle_packets.py post-task    --config C.json --request R.json --recipient P.json --task-id T1 --previous TASK_RECEIPT
cycle_packets.py verify       --config C.json --receipt RECEIPT
```

Each receipt lives under the run's `context/` directory with packet, map slice,
residual obligations and digest. Repeating identical input returns the same
receipt; changed input starts a new attempt. `verify` reports
`needs_recipient_check` because the CLI cannot count recipient tokens. A
`needs_split` packet requires a narrower task, not a bypass.

State belongs in `.daodan/runs/<id>/` of the main checkout. The work-controller
validates identity, snapshots, revisions, deliveries, review evidence and gates.
The process runtime is supplied by `work-controller@daodan` and shares the main
checkout's `.daodan` home. Its explicit work-record binding preserves those
domain checks; a graph result cannot grant authorization or close a task whose
required evidence is missing. `model-routing@daodan` remains the model selection
and pricing owner. No external Deadly Brain engine provider is required.
Static evidence, runtime exercise and installed-host probes remain distinct.

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.3.0`. **Source:** [plugin.toml](<../../plugins/project-delivery/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [abstraction-architect](<abstraction-architect.md>), [clean-code](<clean-code.md>), [codebase-map](<codebase-map.md>), [model-routing](<model-routing.md>), [moe](<moe.md>), [peer-review](<peer-review.md>), [project-knowledge](<project-knowledge.md>), [python-development](<python-development.md>), [repo-hygiene](<repo-hygiene.md>), [report-rendering](<report-rendering.md>), [research](<research.md>), [senior-review](<senior-review.md>), [skill-catalog](<skill-catalog.md>), [testing](<testing.md>), [typescript-development](<typescript-development.md>), [work-controller](<work-controller.md>), [worktree-manager](<worktree-manager.md>) |
| Direct external | None |
| Local closure (22) | [abstraction-architect](<abstraction-architect.md>), [clean-code](<clean-code.md>), [codebase-map](<codebase-map.md>), [dependency-audit](<dependency-audit.md>), [model-routing](<model-routing.md>), [moe](<moe.md>), [peer-review](<peer-review.md>), [platform-engineering](<platform-engineering.md>), [project-delivery](<project-delivery.md>), [project-knowledge](<project-knowledge.md>), [python-development](<python-development.md>), [react-development](<react-development.md>), [repo-hygiene](<repo-hygiene.md>), [report-rendering](<report-rendering.md>), [research](<research.md>), [senior-review](<senior-review.md>), [skill-catalog](<skill-catalog.md>), [testing](<testing.md>), [text-humanizer](<text-humanizer.md>), [typescript-development](<typescript-development.md>), [work-controller](<work-controller.md>), [worktree-manager](<worktree-manager.md>) |
| External closure (3) | `developer-essentials@claude-code-workflows`, `diagram-design@diagram-design`, `mattpocock-skills@mattpocock` |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `network.fetch`, `repository.read`, `repository.write`, `shell.execute`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `project-delivery:delivery-method` | Coordinate analysis, debugging, features and complete documentation through grounded specifications, adversarial plans, verified commits and authorized merge. TRIGGER WHEN: the user wants to brainstorm or design a project, define specifications or implementation plans, investigate or debug, build or refactor code, produce project documentation, resume work, or finish a delivery. Route design conversations to the owned brainstorm without requiring an explicit command. DO NOT TRIGGER WHEN: diagnosing project health without implementing (use project-lifecycle:assess-method), requesting code explanation, or requesting one isolated specialist audit without delivery coordination. | [delivery-method](<../../plugins/project-delivery/skills/delivery-method/SKILL.md>) |
| Skill | `project-delivery:adr-method` | Create, resolve, validate, approve, version and verify canonical architecture decision records in docs/adr/. TRIGGER WHEN: the user explicitly asks to record or write down an architecture or technical decision, an interview settles a design, contract or domain decision, a task needs the decisions governing its scope, the user approves, revises or abandons a record, or a reviewed change verifies records or lists their drift. DO NOT TRIGGER WHEN: the user only wants brainstorming or advice without recording a decision, the change needs no decision beyond existing records, or the request is project documentation (use project-knowledge:project-knowledge). | [adr-method](<../../plugins/project-delivery/skills/adr-method/SKILL.md>) |
| Skill | `project-delivery:frd-method` | Extract, validate, reconcile, approve, version and verify evidence-bound functional requirements documents in docs/frd/. TRIGGER WHEN: the user asks for an evidence-bound FRD, requirements and domain references must be extracted from project sources, a fresh extraction must be reconciled with manual review, or an FRD needs approval, revision or verification. DO NOT TRIGGER WHEN: recording an architecture or technical decision (use project-delivery:adr-method), writing general project documentation without evidence spans, or treating current implementation as an automatically approved requirement. | [frd-method](<../../plugins/project-delivery/skills/frd-method/SKILL.md>) |
| Skill | `project-delivery:project-bootstrap` | Draft missing ADR and FRD from verified project evidence without turning legacy behavior or stale documentation into approved requirements. TRIGGER WHEN: a project has no ADR or FRD, existing project knowledge must be bootstrapped from code, documentation or Codebase Map, or /daodan:init-project needs initial requirement records. DO NOT TRIGGER WHEN: recording one already understood decision (use adr-method), editing an existing FRD (use frd-method), or running the implementation cycle (use delivery-method). | [project-bootstrap](<../../plugins/project-delivery/skills/project-bootstrap/SKILL.md>) |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/project-delivery](<../../exports/claude/plugins/project-delivery>) | `native` | No workflow entry points |
| copilot | [exports/copilot/plugins/project-delivery](<../../exports/copilot/plugins/project-delivery>) | `native` | No workflow entry points |
| codex | [exports/codex/plugins/project-delivery](<../../exports/codex/plugins/project-delivery>) | `adapted` | No workflow entry points |
| pi | [exports/pi/plugins/project-delivery](<../../exports/pi/plugins/project-delivery>) | `adapted` | No workflow entry points |
| opencode | [exports/opencode/plugins/project-delivery](<../../exports/opencode/plugins/project-delivery>) | `native` | No workflow entry points |

### Additional shipped contracts and mechanisms

- Neutral policy: [run-write-confinement](<../../plugins/project-delivery/policies/run-write-confinement.toml>). Enforcement is documented in the policy and host reference.

<!-- daodan:reference:end -->
