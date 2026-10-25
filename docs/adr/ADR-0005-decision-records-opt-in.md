---
adr_id: ADR-0005
version: 1
title: "Make decision records opt-in, chosen once at a project's first Daodan use"
status: Proposed
author: Alfio Caprino
scope:
  paths:
    - plugins/project-lifecycle/skills/lifecycle-method/**
    - plugins/project-lifecycle/skills/handover-method/SKILL.md
    - plugins/work-controller/contracts/work.toml
    - plugins/work-controller/skills/work-record/**
    - plugins/daodan/workflows/**
    - plugins/project-knowledge/skills/instructions-method/SKILL.md
    - plugins/senior-review/skills/review-preparation/references/candidate-grounding.md
    - tests/test_work_record.py
    - tests/test_skill_load_budget.py
    - evals/project-lifecycle/**
    - docs/decision-records.md
    - CLAUDE.md
    - README.md
  modules:
    - lifecycle-method
    - adr-method
    - work-record
  domains:
    - decision-records
    - initialization
governs_symbols:
depends_on:
created_from_task: session-674d0b20-adr-opt-in
proposed_on: 2026-10-24
proposed_at_sha: 09156a0c15abaa7407daf2f37ca29c836546a3c3
accepted_on: null
accepted_at_sha: null
last_verified_sha: null
retired_on: null
retired_reason: null
supersedes:
superseded_by: null
changes:
---

# ADR-0005: Make decision records opt-in, chosen once at a project's first Daodan use

<!-- adr-header:start -->
Version 1 · Proposed 2026-10-24 by Alfio Caprino
<!-- adr-header:end -->

## Context and Problem Statement

The task cycle of `project-lifecycle` uses decision records on every project,
whether or not the user wants them:

1. `plugins/project-lifecycle/skills/lifecycle-method/references/init.md:22`
   always runs `init-index`, and `change.md:30` initializes any project that
   lacks a record index before a task.
2. `change.md:11` and `interview.md:44-49` end every interview by writing a
   `Proposed` record.
3. The plan, the worker briefs, the wave reviews and `verify.md:14` read the
   examples and invariants from that record, so they have no other source.
4. `finish.md:4` and `realign.md:7-11` always promote it.

The user stated on 2026-10-24 that decision records are an optional feature
and must never be forced on a user, that the choice is per project, and that
it is asked at a project's first use of Daodan. The same first use asks
whether to analyze the project now and, if so, at lite or deep depth. Today
`init.md:18` always maps at lite depth without asking.

The question: how does the cycle run on a project without records, where is
the choice made and kept, and what does the first use do?

## Decision Drivers

- No user is made to adopt decision records to use the task cycle.
- The choices are asked once per project and never again.
- Analysis spends tokens in proportion to the project; the user decides
  whether and how deep it runs at first use.
- One fact has one owner: the switch is something the project already shows,
  not a second flag that can disagree with it.
- The interview's agreed examples, rejected alternatives and invariants keep
  their role as oracles and constraints with or without records.
- The dependency policy holds: the switch is the project's choice, never a
  condition on whether a plugin is installed.

## Decision

- **The switch.** Decision records are enabled for a project exactly when its
  index `docs/adr/README.md` exists in the project's main checkout or in the
  checkout the command runs in. Without it
  they are disabled: no command writes under `docs/adr/`, runs `resolve`,
  `propose` or `promote`, or mentions records in a question, brief or report.
  The one exception is `/daodan:record-decision`, which is the user's explicit
  request: on a disabled project it creates the index and then the record, and
  says so in its output. From then on the project is enabled. No command
  deletes `docs/adr/` or a record to disable the feature.
- **First use.** A project is at its first Daodan use when its main checkout
  has neither `.daodan/` nor `.codebase-map/` (nor a `.codebase-xray/` awaiting
  migration). The first command that would create either one starts with the
  first-use step, before that write. It asks two questions once: whether the
  project will use decision records, and whether to analyze it now, with three
  answers: no, lite, or deep (the map's `full` depth, every phase). Yes to
  records runs `init-index` and commits the new index alone on the current
  branch, so a task worktree branches with it. No creates nothing under `docs/adr/`. The chosen
  analysis then runs at that depth. No analysis writes no `.codebase-map/`; a
  later command that needs the map builds it when it needs it, at lite depth on
  its scope, as it does today, without asking again. Because the first use leaves
  `.daodan/` or `.codebase-map/` behind, the question is never asked again.
  `/daodan:init-project` performs the step, and so does every command that
  initializes a project before its own work. `/daodan:map-code` as the first
  command asks the records question and only the depth, because the user
  already asked for an analysis; a depth the user named is not asked.
  `/daodan:record-decision` asks only about the analysis, because it is itself
  the choice of records. An empty folder is asked after its scaffold. A host
  without a question tool opens the command's run holding only the two
  questions and applies the answers on resume. Read-only entries (the reviews,
  investigation, onboarding) run the same step first; what the answers create
  is not their write. `/daodan:show-status` asks nothing and says the project
  has not used Daodan. A command that writes neither directory never asks.
- **Projects already in use.** A project that already has `.daodan/` or
  `.codebase-map/` is not at its first use: it keeps records when its index
  exists and runs without them otherwise, with no question. A later
  initialization on such a project updates the existing map as today.
- **The interview's intent.** Scope, examples (`EX-*`), rejected alternatives
  (`RA-*`) and invariants (`INV-*`) are fixed by the interview in every case.
  With records disabled, the run keeps them in its own `intent.md`, and the plan, worker briefs, wave
  reviews and verification cite them from there;
  finish promotes nothing. A fix or refactor that needs no record keeps them
  in its plan, on any project. With records enabled, the record holds them and the
  run references it by identity and version, never by copy. Each task's intent
  has exactly one owner.
- **Relation to ADR-0004.** Versions, approval, drift and dependencies of
  records apply only to projects with records enabled.

## Verified Interview Examples

- **EX-001** (nominal case): Input: a project with no `.daodan/`, `.codebase-map/` or `docs/adr/`; the user runs `/daodan:new-feature`; at the first-use questions the user answers no to records and deep to the analysis -> Expected: the analysis runs at `full` depth, nothing is created under `docs/adr/`, the interview's `EX-*`, `RA-*` and `INV-*` go into the run's `intent.md`, the plan and verification cite them from the run, and finish promotes nothing.
- **EX-002** (nominal case): Input: the same project; the user answers yes to records and lite to the analysis -> Expected: the analysis runs at `lite` depth, `init-index` creates `docs/adr/README.md` and commits it alone, and the interview ends with `propose` as today.
- **EX-003** (boundary case): Input: a project initialized before this decision, with `.daodan/` and no `docs/adr/` -> Expected: no question; the cycle runs with records disabled and never mentions them.
- **EX-004** (boundary case): Input: on a never-used project the first command is `/daodan:map-code`; the user answers no to records and lite to the depth; later the user runs `/daodan:new-feature` -> Expected: `map-code` asks the records question and the depth, never whether to analyze, before writing `.codebase-map/`; `new-feature` does not ask again and runs without records.
- **EX-005** (nominal case): Input: a disabled project; the user runs `/daodan:record-decision` -> Expected: the index and the record are created, the output states that the project now uses decision records, and later tasks `resolve` and `propose` as on any enabled project.
- **EX-006** (boundary case): Input: `/daodan:show-status` on a never-used project -> Expected: no question and no write; the status reports that Daodan has not been used on this project.
- **EX-007** (rejection case): Input: on a disabled project a review or a worker brief would load active records -> Expected: `resolve` does not run, the inputs come from the run's `intent.md`, and nothing fails or warns because `docs/adr/` is absent.
- **EX-008** (boundary case): Input: a never-used project; `/daodan:new-feature`; the user answers no to the analysis -> Expected: no `.codebase-map/` is written at the first-use step; the change preflight then builds the map at lite depth on the task's scope without asking again, and the next command asks nothing.

## Rejected Alternatives

- **RA-001**: asking at the end of every interview whether to record the decision; rejected by the user in favour of a per-project choice, because it costs a question on every task.
- **RA-002**: records always on, the current behaviour; rejected because it forces a feature on users who do not want it.
- **RA-003**: a settings flag or file holding the choice; rejected because the index's presence already states it, and a second fact would drift from it.
- **RA-004**: asking on every command that finds no `docs/adr/`; rejected because a declined question would come back forever.
- **RA-005**: making `project-knowledge` an optional dependency of `project-lifecycle` to switch records off; rejected by the dependency policy: the switch is the project's choice, not an installation state.
- **RA-006**: a fixed depth at first use, always lite as `init.md:18` does today or always full; rejected by the user, because whether to analyze and how deep is the user's choice of cost.
- **RA-007**: analyzing a never-used project without asking; rejected for the same reason.

## Enforceable Invariants

- **INV-001**: decision records are enabled for a project if and only if `docs/adr/README.md` exists in its main checkout or in the checkout the command runs in; no other flag, setting or plugin state decides it.
- **INV-002**: with records disabled, no command except `/daodan:record-decision` writes under `docs/adr/`, runs `resolve`, `propose` or `promote`, or mentions records to the user or a worker.
- **INV-003**: the first-use questions are asked at most once per project, before any write other than a run that holds only those questions on a host without a question tool; a command that writes neither `.daodan/` nor `.codebase-map/` never asks.
- **INV-004**: the first use analyzes only as the user answered: not at all, at `lite` depth or at `full` depth; the answer is recorded in the run and a depth the user already named is not asked again.
- **INV-005**: a task's examples, rejected alternatives and invariants have exactly one owner: the record when the task proposes one, the run's `intent.md` or its plan otherwise; plan, briefs, reviews and verification cite that owner.
- **INV-006**: no command deletes `docs/adr/` or a record to change the switch.

## Consequences

- `lifecycle-method`: its `SKILL.md` states the switch once (without the index,
  no `adr_tool.py` command but `template` runs, records are never mentioned and
  every unit's "record" is the run's `intent.md`), so the units keep their text;
  `first-use.md` holds the step; `init.md` maps at the chosen depth, validates
  existing records instead of creating the index and runs when the loop block
  is missing; `change.md` stops requiring a record index; `interview.md` writes
  `intent.md` when records are off; the preflight builds a missing map on the
  task's scope.
- `work-controller`: `run_state.py` gains the read-only `first-use` probe;
  the run keeps no copy of the answers and no digest of `intent.md`.
- `daodan`: every entry that may write Daodan state starts with the first-use
  probe; `record-decision` turns records on; `show-status` reports a never-used
  project; descriptions name the optional record.
- `senior-review`: `review-preparation` binds active records only when the
  project keeps them.
- `project-knowledge`: `instructions-method` writes active records into the
  loop block only when the project keeps them.
- `project-lifecycle`'s `handover-method` treats the entry's first-use writes
  as outside its write boundary.
- The repository instructions, `README.md`, the plugin pages and
  `docs/decision-records.md` describe the opt-in.
- A deep analysis at first use spends more tokens than a lite one on large
  projects; the question says so, and later commands update the analysis
  incrementally.
- Versions bump `project-lifecycle`, `work-controller`, `daodan`,
  `project-knowledge` and `senior-review`, and the marketplace.

## Confirmation

- Run-contract tests cover the read-only probe.
- The lifecycle evals `first-use-choices` and `records-off-cycle` cover
  EX-001 to EX-008: the questions asked once, the three analysis answers, a
  disabled project that never mentions records, and `record-decision` as the
  opt-in.
- `tests/test_skill_load_budget.py` caps `first-use.md` and the first-use step;
  no existing cap is raised.
- `python scripts/lint_dependency_graph.py` passes with `project-knowledge`
  still required by `project-lifecycle` (RA-005).
