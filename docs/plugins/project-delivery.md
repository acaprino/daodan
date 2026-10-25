# Project Delivery

Project Delivery coordinates analysis, debugging, fixes, features and complete
project documentation. It owns decision records and the delivery cycle:
grounded specifications, bit-sized implementation plans, adversarial plan review,
Deadly Brain graph execution and model routing, verified atomic commits, safe
continuation, candidate review, authorized merge and realignment. It can be used
without the `daodan` command umbrella. Specialist methods retain detection,
documentation and remediation ownership.

## Decision records and project documentation

`adr-method` creates, resolves, validates, approves, versions and verifies records
under `docs/adr/`. The interview specification contains observable examples,
rejected alternatives and enforceable invariants. Projects without an ADR index
use the run's `intent.md`; the delivery gates are identical. [Decision records](../decision-records.md)
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
| 3. Specification | A light `spec` review checks the ADR or run intent; an ADR remains `Proposed` until the user approves its exact text | `interview.md` |
| 4. Plan | Bit-sized tasks carry bounded write sets, base-failing oracles and verification commands. An adversarial `plan` review must be delivered with PASS on the exact plan digest and current bytes before any task enters `running` | `waves.md` |
| 5. Execution | A specialist writes each task. The coordinator reruns verification and a light changeset review on the uncommitted candidate, then commits atomically only after PASS and authorization. Snapshot, verification, review and commit SHA must match; later edits invalidate the evidence | `waves.md`, `worker-brief.md` |
| 6. Candidate | The whole candidate receives a branch review; blocking findings get at most two remediation waves | `verify.md` |
| 7. Integration | After current-candidate validation and merge authorization, the branch is merged, the ADR verified, map and documentation realigned, and the workspace closed | `finish.md`, `realign.md` |

`--plan-only` stops after phase 4; `--run-id` resumes the approved plan from its
first unsealed wave. An interrupted commit is reconciled from HEAD and scoped
bytes, never retried blindly or rolled back through `HEAD~1`.

Initialization brings a project into the cycle with its map, optional decision
index, instruction loop block and test baseline. `brainstorm` explores an idea;
`sync` fast-forwards and realigns; `retention` handles only concluded run output.
The density of every unit and phase context is capped by
`tests/test_skill_load_budget.py`.

The original cycle design is in
[the closed-loop harness design](../superpowers/specs/2026-10-18-closed-loop-harness-design.md);
[ADR-0006](../adr/ADR-0006-adr-project-delivery.md) records the extraction and
pre-commit evidence contract; [ADR-0007](../adr/ADR-0007-griffin-drkerr-evolution.md)
records the broader delivery, FRD and Deadly Brain boundaries.

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
Static evidence, runtime exercise and installed-host probes remain distinct.

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.0.0`. **Source:** [plugin.toml](<../../plugins/project-delivery/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [abstraction-architect](<abstraction-architect.md>), [clean-code](<clean-code.md>), [codebase-map](<codebase-map.md>), [model-routing](<model-routing.md>), [moe](<moe.md>), [peer-review](<peer-review.md>), [project-knowledge](<project-knowledge.md>), [python-development](<python-development.md>), [repo-hygiene](<repo-hygiene.md>), [report-rendering](<report-rendering.md>), [senior-review](<senior-review.md>), [skill-catalog](<skill-catalog.md>), [testing](<testing.md>), [typescript-development](<typescript-development.md>), [work-controller](<work-controller.md>) |
| Direct external | None |
| Local closure (19) | [abstraction-architect](<abstraction-architect.md>), [clean-code](<clean-code.md>), [codebase-map](<codebase-map.md>), [dependency-audit](<dependency-audit.md>), [model-routing](<model-routing.md>), [moe](<moe.md>), [peer-review](<peer-review.md>), [platform-engineering](<platform-engineering.md>), [project-delivery](<project-delivery.md>), [project-knowledge](<project-knowledge.md>), [python-development](<python-development.md>), [react-development](<react-development.md>), [repo-hygiene](<repo-hygiene.md>), [report-rendering](<report-rendering.md>), [senior-review](<senior-review.md>), [skill-catalog](<skill-catalog.md>), [testing](<testing.md>), [typescript-development](<typescript-development.md>), [work-controller](<work-controller.md>) |
| External closure (3) | `developer-essentials@claude-code-workflows`, `mattpocock-skills@mattpocock`, `text-humanizer@shinatama` |

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
| Skill | `project-delivery:delivery-method` | Coordinate analysis, debugging, features and complete documentation through grounded specifications, adversarial plans, verified commits and authorized merge. TRIGGER WHEN: the user wants to investigate or debug a problem, build or refactor code, produce complete project documentation, define specifications or implementation plans, resume work, or finish and merge a delivery. DO NOT TRIGGER WHEN: diagnosing project health without implementing (use project-lifecycle:assess-method), requesting code explanation, or requesting one isolated specialist audit without delivery coordination. | [delivery-method](<../../plugins/project-delivery/skills/delivery-method/SKILL.md>) |
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
