---
adr_id: ADR-0008
version: 1
title: Decision records by default during brainstorming
status: Accepted
author: Alfio Caprino
scope:
  paths:
    - plugins/project-delivery/**
    - plugins/work-controller/skills/work-record/scripts/run_state.py
    - plugins/daodan/workflows/record-decision.md
  modules:
  domains:
    - decision-records
    - project-delivery
governs_symbols:
depends_on:
created_from_task: adr-brainstorm
proposed_on: 2026-10-28
proposed_at_sha: b52dc32e479631e7b18ac235134db924213b713b
accepted_on: 2026-10-28
accepted_at_sha: 8839c75223d45d16fae2331f985526827959e319
last_verified_sha: null
retired_on: null
retired_reason: null
supersedes:
superseded_by: null
changes:
---

# ADR-0008: Decision records by default during brainstorming

<!-- adr-header:start -->
Version 1 · Accepted 2026-10-28 at 8839c75 · proposed 2026-10-28 by Alfio Caprino
<!-- adr-header:end -->

## Context and Problem Statement

ADR-0005 made decision records opt-in, chosen once at a project's first Daodan
use. On 2026-10-28 the owner reported that the mode never activated: the
brainstorm only ran `resolve` (`delivery-method/references/brainstorm.md:10-11`),
the interview proposed a record only "when a separate technical decision needs an
ADR" (`interview.md:34`), adr-method's description excluded brainstorming
(`adr-method/SKILL.md:6`), records were off by default (`first-use.md:12`), and on
Claude and OpenCode the work-controller MCP server created `.daodan/` at session
start (`work_controller/cli.py:24`), so the first-use probe never asked. The
design is `docs/specs/2026-10-28-adr-brainstorm-method-design.md`.

## Decision Drivers

- The owner's decision of 2026-10-28: records work automatically while
  brainstorming products or features, with no map, run or other Daodan state.
- On by default, one question per project, a no never asked again.
- ADR and FRD are the only record kinds.
- It works whatever brainstorming method runs.

## Decision

`adr_tool.py state` classifies a project as `active` (Daodan ADR index, FRD
index, or foreign ADRs in any directory), `declined` (local Git config
`daodan.decisionRecords=declined`, or `.daodan/adr-declined` outside Git) or
`undecided`. An optional session-start hook of project-delivery adds context:
`active` records each settled product or feature decision as a `Proposed` record
in `docs/adr/`; `undecided` asks once, at the first settled decision, yes by
default; `declined` adds nothing. A no tells the user that
`/daodan:record-decision` turns records back on. First use keeps only the
analysis question, and the probe counts `.daodan/runs/`, not a bare `.daodan/`.

## Verified Interview Examples

- **EX-001** (nominal case): Input: new Git project without records, a brainstorm settles "store sessions in Redis", the user answers yes -> Expected: `docs/adr/README.md` and `ADR-0001-store-sessions-in-redis.md` (`Proposed`) exist and are shown.
- **EX-002** (boundary case): Input: project with `doc/adr/0001-use-postgres.md` only -> Expected: no question; the next settled decision creates `docs/adr/ADR-0001-<slug>.md` and `0001` is untouched.
- **EX-003** (rejection or error case): Input: the user answers no -> Expected: `daodan.decisionRecords=declined` in the local Git config, the reply names `/daodan:record-decision`, later sessions ask nothing.

## Rejected Alternatives

- **RA-001**: Off by default, chosen at first use (ADR-0005): it never ran.
- **RA-002**: Recording only in the Daodan brainstorm: other brainstorming methods take free conversations.
- **RA-003**: Writing new records into a foreign ADR directory: it would rewrite foreign files and break every caller of `docs/adr/README.md`.

## Enforceable Invariants

- **INV-001**: The question is asked at most once per project checkout.
- **INV-002**: The hook and `state` write nothing.
- **INV-003**: Capture requires no map, run, first-use probe or research checkpoint.
- **INV-004**: Foreign record files are never written; new records live only in `docs/adr/`.

## Consequences

- ADR-0005 is retired as superseded by this decision.
- Copilot and Pi have no session hook; there only Daodan's own brainstorm and interview apply the rule.
- Reviews read only `docs/adr/`, so foreign records constrain brainstorming and interviews, not reviews.

## Confirmation

- `tests/test_adr_method.py` covers `state`, `decline` and records without a commit.
- The hook tests cover the context per state; `tests/test_work_record.py` covers the probe.
- `evals/project-lifecycle/cases.md` case `records-in-brainstorm` covers the examples.
