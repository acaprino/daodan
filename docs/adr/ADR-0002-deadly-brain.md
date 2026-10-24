---
adr_id: ADR-0002
title: Create deadly-brain and absorb project-protocol into it
status: Proposed
scope:
  paths:
    - plugins/project-protocol
    - plugins/deadly-brain
    - plugins/senior-review/skills
    - plugins/project-lifecycle/skills/lifecycle-method/references/interview.md
  modules:
    - project-protocol
    - deadly-brain
  domains:
    - run-state
    - clarification
    - decision-map
    - work-graph
    - model-routing
governs_symbols:
created_from_task: conversation-2026-10-24
proposed_at_sha: cab382f49e939e0c47cee969f8f046db4e69f30d
accepted_at_sha: null
last_verified_sha: null
supersedes:
superseded_by: null
---

# ADR-0002: Create deadly-brain and absorb project-protocol into it

## Context and Problem Statement

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

## Decision Drivers

- Minimalism, token consumption tending to zero, simplicity, no useless
  overengineering and no excess of zeal (user, 2026-10-24).
- One engine for Daodan and Shinatama, without a dependency cycle.
- Usable alone, without the rest of Daodan.
- Standard library only.

## Decision

Create the plugin `deadly-brain` in the daodan marketplace, with no dependencies.
It owns:

- `work-record`: what `project-protocol` owned for runs (records, agenda, gates,
  grants, recovery), the shared discipline and the `isolated-worker` role;
- the clarification contract and the question shape;
- the generic interview, while `project-lifecycle` keeps the code grounding;
- the decision map and its tickets;
- work-graph composition: deterministic from the consumer's archetypes,
  contextual through an LLM proposal only when no archetype fits, dynamic by
  replanning only the nodes a new answer or evidence invalidates. `graphlib`
  validates acyclicity and computes the frontier.

`project-protocol` is removed and its consumers declare `deadly-brain`. Model
routing moves to a plugin of its own, `model-routing`; `review_roster.py` moves to `senior-review`.
Archetypes stay with their consumers. Shinatama declares `deadly-brain@daodan`.
State stays under `.daodan/`.

Economy rules: code does the work and the model reads the result; each command
prints only what its step needs; the fewest skills, with short descriptions;
references load per step; no new schema where an existing one serves.

## Verified Interview Examples

- **EX-001** (nominal case): Input: a Shinatama office workflow lacks a
  requirement for a Word document -> Expected: it loads `deadly-brain` alone, asks
  one question in the shape of the specification's section 4 and records it under
  `.daodan/runs/<id>/`.
- **EX-002** (boundary case): Input: a user installs `deadly-brain@daodan` and no
  other Daodan plugin -> Expected: maps, tickets, questions and records work; no
  `codebase-map` is required.
- **EX-003** (rejection or error case): Input: a change makes `deadly-brain`
  depend on another plugin, from either marketplace -> Expected: the build fails.
- **EX-004** (boundary case): Input: `next` on a map of 40 tickets -> Expected:
  the output is the frontier ticket and its question, not the map.

## Rejected Alternatives

- **RA-001**: a third repository `acaprino/deadly-brain`. It costs a third copy of
  the compiler, three releases and an extra marketplace for every Daodan user on
  five hosts. Standalone use is already possible as `deadly-brain@daodan`, and the
  cycle it would avoid does not exist.
- **RA-002**: keep `project-protocol` and add `deadly-brain` above it. Four
  unrelated concerns stay under a name that says nothing, and Shinatama gains a
  dependency.
- **RA-003**: a separate run-record plugin under a new name, below `deadly-brain`.
  Two plugins for one state, and the map would reference the agenda across a
  plugin boundary.
- **RA-004**: LangGraph, Temporal or transitions as engine. Each adds a framework,
  a server or a dependency for what `graphlib` and the record already cover. Not
  verified against current sources, because no adoption is proposed.
- **RA-005**: delegating the map to upstream Wayfinder. It is user-invoked only
  and keeps its state in the checkout's `.scratch/`.

## Enforceable Invariants

- **INV-001**: `deadly-brain` declares no dependencies.
- **INV-002**: no Daodan plugin depends on a Shinatama plugin.
- **INV-003**: ticket blocks and work-graph dependencies are acyclic; a repair is
  a new attempt node.
- **INV-004**: no `deadly-brain` command prints a whole map or record; output is
  bounded to the requesting step.
- **INV-005**: only a human answer closes a ticket that needs the human; closing a
  ticket never satisfies a gate.

## Consequences

- The eight consumers switch their dependency and their `contract.shared_schemas`
  provider; `project-protocol:` references are renamed.
- `CLAUDE.md`, the dependency table, `docs/plugins/`, `docs/catalog.md` and the
  2026-10-20 and 2026-10-24 specifications are realigned.
- The `model-routing` plugin appears and `senior-review` gains `review_roster.py`.
- Removing a plugin is breaking: marketplace major version.

## Confirmation

- `scripts/lint_dependency_graph.py` fails a dependency declared by `deadly-brain`
  and any Daodan edge toward Shinatama.
- Unit tests: a cycle is rejected; the frontier follows `get_ready`/`done`; `next`
  prints only the frontier ticket.
- `python scripts/daodan_build.py --check` and
  `python scripts/sync_plugin_docs.py --check` pass.
