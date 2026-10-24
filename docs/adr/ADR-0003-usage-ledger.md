---
adr_id: ADR-0003
title: "Measure each run's tokens and cost from local host logs"
status: Proposed
scope:
  paths:
    - plugins/project-protocol/contracts/work.toml
    - plugins/project-protocol/skills/project-protocol/scripts/**
    - plugins/project-lifecycle/skills/lifecycle-method/references/waves.md
    - plugins/project-lifecycle/skills/lifecycle-method/references/finish.md
  modules:
    - project-protocol
    - project-lifecycle
  domains:
    - run-state
    - usage-ledger
    - budget
    - model-routing
governs_symbols:
created_from_task: conversation-2026-10-24
proposed_at_sha: bed96a170503e2d2e76bd7682e152e01a8e649a9
accepted_at_sha: null
last_verified_sha: null
supersedes:
superseded_by: null
---

# ADR-0003: Measure each run's tokens and cost from local host logs

## Context and Problem Statement

Daodan's stated aim is to save tokens and to get the most out of an economical
model, and nothing in the harness measures either. The run record requires a
`budget` (`plugins/project-protocol/contracts/work.toml:4`, enforced at
`skills/project-protocol/scripts/run_state.py:1109`) whose only known content is
`{"max_workers": N}`. Deliveries carry a status and an `output`
(`contracts/work.toml:27-33`) and no usage. The protocol says the helper does not
enforce worker token limits (`skills/project-protocol/SKILL.md:186`). The router
prices models only a priori, from `cost_usd_per_million_tokens` in the model
catalog (`tier_router.py:389`, `tier_router.py:827`). The one measured figure the
project has, 30.90 USD for the closed-loop probe of 2026-10-19, was read by hand.

Every host Daodan ships to, except one, already writes usage on the user's machine.
Probed on 2026-10-24:

- Claude Code 2.1.310: `~/.claude/projects/<project>/<session>.jsonl`, one
  `message.usage` per assistant response with `input_tokens`,
  `cache_read_input_tokens`, `cache_creation.ephemeral_5m_input_tokens`,
  `ephemeral_1h_input_tokens`, `output_tokens`, `output_tokens_details.thinking_tokens`,
  `message.model`, `message.id`, `requestId`. A worker's transcript is
  `<session>/subagents/agent-<agentId>.jsonl` beside `agent-<agentId>.meta.json`,
  which carries the `toolUseId` of the dispatching Agent call. No cost is logged.
  Transcripts are purged by the host (67 left locally).
- Codex 0.163: rollout jsonl with `token_usage_record` per response
  (`thread_id`, `turn_id`, `response_id`, `usage`), where `cached_input_tokens` is a
  subset of `input_tokens`. No cost is logged.
- OpenCode 2.1.4: `~/.local/share/opencode/opencode.db` (SQLite); `session` rows
  carry `parent_id`, `agent`, `model`, `cost` and `tokens_*`; a worker is a child
  session.
- Pi 1.2.0: session jsonl, assistant `usage` with `input`, `output`, `cacheRead`,
  `cacheWrite`, `reasoning` and a host-computed `cost`.
- Copilot: no CLI installed on the probe machine; no usage source verified.

The question this record answers: how does a run learn, per worker and per phase,
what it spent, and what happens when it spends more than its budget?

## Decision Drivers

- The measure must exist before any token saving can be claimed
  ("savings require measurement", repository instructions).
- Worker-level attribution, because model routing calibration needs the cost and
  the verified outcome of each role on each tier.
- Standard library only, no network, no credentials, every host.
- A gap must stay visible: an unreadable source is not a zero.
- The run record owns run facts; ADR-0002 moves that owner to
  `deadly-brain:work-record` and routing to `model-routing`, so the ledger follows
  the run record and the prices follow the catalog.

## Decision

The run record gains a `usage` section filled by a protocol helper that reads the
active host's local logs. The helper normalizes every source to one row shape:
`host, model, session, worker, phase, input, cache_read, cache_write_5m,
cache_write_1h, output, reasoning, host_cost, source_key`, where `input` is uncached
input only. Rows are deduplicated by a per-host key (Claude Code `message.id` plus
`requestId`; Codex `response_id`; OpenCode message id; Pi message id).

Attribution: a delivery records the host's handle for its worker when dispatched
(Claude Code `toolUseId`, OpenCode child session id, Codex thread id); the helper
assigns that worker's rows to the delivery and to the delivery's phase. The
coordinator's own rows go to the phase whose recorded time window contains them.

Cost: each row is priced from the model catalog's `cost_usd_per_million`, labeled
with the catalog revision; a host-reported cost is kept beside the estimate and is
the figure shown when present. A model with neither is `unpriced`.

Harvest runs at every wave boundary and at every phase close, because hosts purge
transcripts. Hosts in scope: Claude Code, Codex, OpenCode and Pi. Copilot records
`unavailable` until a probe verifies a source.

Budget: `budget` accepts optional `max_usd` and `max_tokens`. At each wave boundary
the coordinator harvests and compares: from 75% it records a warning; at 100% it
does not start the next wave and asks the user, and work continues only after a
new grant of kind `spend` naming the new ceiling. Nothing interrupts a running
worker.

## Verified Interview Examples

- **EX-001** (nominal, Claude Code): Input: a run whose delivery `D1` was dispatched by Agent call `toolu_X`; `subagents/agent-a1.meta.json` has `toolUseId: toolu_X`; harvest at phase close -> Expected: `D1` carries the summed tokens of `agent-a1.jsonl` by bucket, its model and a USD estimate with the catalog revision; the coordinator's rows inside the phase window are summed under that phase.
- **EX-002** (boundary, duplicates): Input: two transcript lines with the same `message.id` and `requestId` (one per content block), harvested twice -> Expected: counted once; the second harvest produces a byte-identical `usage` section.
- **EX-003** (boundary, cached subset): Input: Codex `token_usage_record` with `input_tokens: 175458`, `cached_input_tokens: 23808` -> Expected: row `input: 151650`, `cache_read: 23808`.
- **EX-004** (rejection, no source): Input: a run on Copilot -> Expected: `usage.status: unavailable` with the reason; the budget check reports `unmeasured`, never 0 USD; the run's own completion rules are unchanged.
- **EX-005** (budget): Input: `budget.max_usd: 5.00`, harvest at a wave boundary shows 3.80 USD, then 5.10 USD at the next -> Expected: a warning recorded at 76%; at 102% the next wave does not start until a `spend` grant with a new ceiling is recorded.
- **EX-006** (unpriced): Input: a model absent from the catalog on a host that logs no cost -> Expected: `usd: null`, `priced: false`; the run total is marked `partial`.
- **EX-007** (purged source): Input: a worker transcript deleted by the host before harvest -> Expected: that delivery's usage is `missing` with the reason; rows harvested earlier remain.

## Rejected Alternatives

- **RA-001**: run totals only; rejected because they cannot say which role or tier spent the tokens, which is the data routing calibration needs.
- **RA-002**: a hard stop through per-host hooks; rejected for now because enforcement is not proved on all five hosts and the protocol does not claim token enforcement.
- **RA-003**: a separate cost plugin; rejected because it would be a second owner of run facts beside the run record.
- **RA-004**: storing usage in a vector memory through an npm CLI, as ruvnet/ruflo's cost tracker does; rejected because the toolchain is stdlib Python with no runtime service.
- **RA-005**: outcomes or usage reported by the model itself (ruflo's `hooks_model-outcome`); rejected because a model's account of its own success is not evidence. Outcomes come from deliveries and gates.
- **RA-006**: billing APIs or a host's `/cost` output; rejected because they need network and credentials and do not attribute to workers.
- **RA-007**: treating an unpriced model or an unreadable source as 0; rejected because it turns a gap into a false saving.

## Enforceable Invariants

- **INV-001**: the ledger reads only local host logs: no network, no credentials, no dependency outside the standard library; SQLite is opened read-only.
- **INV-002**: an unsupported, unreadable or purged source is recorded as `unavailable` or `missing` with its reason, never as zero tokens or zero cost.
- **INV-003**: harvest is idempotent: the same logs produce a byte-identical `usage` section, and each source row is counted once by its host key.
- **INV-004**: every host is normalized to the same row shape, with `input` meaning uncached input and cache reads and writes in their own buckets.
- **INV-005**: every USD figure names its price source and revision; host-reported cost is kept beside the estimate.
- **INV-006**: after a budget is reached no wave starts without a recorded `spend` grant.
- **INV-007**: usage is evidence, not authority: it never changes a delivery status, a gate or a completion decision.

## Consequences

- `contracts/work.toml` gains the `usage` loop section, the optional `budget.max_usd` and `budget.max_tokens`, a worker handle on deliveries and the grant kind `spend`.
- A new helper under `skills/project-protocol/scripts/` reads the four hosts; `run_state.py` validates the section.
- `project-lifecycle` waves gain the harvest and budget check at each boundary; finish reports totals per phase and per worker.
- The catalog's prices become load-bearing. They are marked indicative today, and on 2026-10-24 two sources disagreed for Claude Opus 5 and 5.5; the price source must be verified before this record is accepted.
- ADR-0002 moves this section with the run record to `deadly-brain:work-record`.
- The parked draft `docs/superpowers/specs/2026-10-24-derived-routing-signals-draft.md` gets its calibration data from this ledger joined to verified outcomes.
- Open before acceptance: Pi worker attribution through `pi-subagents`, how the coordinator learns its own host session id on each host, and a Copilot source.
- Implementation starts in a worktree once the concurrent uncommitted work in `run_state.py`, `work.toml` and `tier_router.py` is committed.

## Confirmation

- Fixture logs per host, trimmed from real samples, with one test per example EX-001 to EX-007.
- An idempotence test that harvests twice and compares bytes.
- A validation test that refuses a `usage` section with a zero in place of `unavailable`, and a wave start after budget without a `spend` grant.
- The existing compiler, registration and drift gates over all five hosts.

## Provenance

Ideas read in ruvnet/ruflo (MIT), `plugins/ruflo-cost-tracker/scripts/_ledger.mjs`
and `_pricebook.mjs`, on 2026-10-24: one normalized row shape across tools,
per-host double-counting rules and unpriced never shown as zero. No text or code is
copied.
