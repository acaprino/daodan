---
adr_id: ADR-0003
title: "Measure each run's tokens and cost from local host logs"
status: Proposed
scope:
  paths:
    - plugins/work-controller/contracts/work.toml
    - plugins/work-controller/skills/work-record/scripts/**
    - plugins/project-lifecycle/skills/lifecycle-method/references/waves.md
    - plugins/project-lifecycle/skills/lifecycle-method/references/finish.md
  modules:
    - work-controller
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
`budget` (`plugins/work-controller/contracts/work.toml:4`, enforced at
`skills/work-record/scripts/run_state.py:1109`) whose only known content is
`{"max_workers": N}`. Deliveries carry a status and an `output`
(`contracts/work.toml:27-33`) and no usage. The protocol says the helper does not
enforce worker token limits (`skills/work-record/SKILL.md:186`). The router
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
  `cacheWrite`, `reasoning` and a host-computed `cost`, 0 for a gateway model with
  51531 tokens in the sample.
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
  `work-controller:work-record` and routing to `model-routing`, so the ledger follows
  the run record and the prices follow the catalog.

## Decision

The run record gains a `usage` section filled by a protocol helper that reads the
active host's local logs. The helper normalizes every source to one row shape:
`host, model, session, worker, phase, input, cache_read, cache_write_5m,
cache_write_1h, output, reasoning, host_cost, source_key`, where `input` is uncached
input only. Rows are deduplicated by a per-host key (Claude Code `message.id` plus
`requestId`; Codex `response_id`; OpenCode message id; Pi message id).

The helper has one reader per host, because runtime code ships under a skill and
`adapters/` act only at compile time. The compiled host binding passes the host to
the helper, which never guesses it from the logs it finds. Each reader maps its
host's cache semantics to the row. Claude Code, OpenCode and Pi log input without
cache (verified on local samples: OpenCode and Pi totals equal input plus output
plus cache). Codex logs `cached_input_tokens` inside `input_tokens`, so uncached
input is the difference. Only Claude Code splits cache writes into 5 minutes and
1 hour; the other readers put every write in `cache_write_5m`. Reasoning is
counted once: Claude Code `thinking_tokens` and Codex `reasoning_output_tokens` sit
inside output (verified: Codex input plus output equals its total), so a reader
splits them out and a separate `reasoning` price applies to them alone.

Attribution: a delivery records the host's handle for its worker when dispatched
(Claude Code `toolUseId`, OpenCode child session id, Codex thread id); the helper
assigns that worker's rows to the delivery and to the delivery's phase. The
coordinator's own rows go to the phase whose recorded time window contains them.

Cost: Daodan computes every figure itself, as a comparison measure at list price
and not a bill: its purpose is to compare runs, roles and tiers on cost
efficiency. One rule serves every model family, and no family gets a
hand-written price table. A row is priced at the endpoint that served it (the
provider the log names, such as Pi's `tri-llm-gateway` or OpenCode's `providerID`),
because prices belong to endpoints: the catalog's Sonnet 5.5 cache read is 0.20 USD
on its selected `opencode` endpoint and 0.10 on Anthropic's. The prices live
beside the catalog in `references/model-prices.json`, generated by
`build_model_prices.py` with every price dimension models.dev publishes (input,
output, cache_read, cache_write, context-size `tiers`, `reasoning`, audio) for the
creator's endpoint, the catalog's selected endpoint and the common resellers, and
every name a model is sold under at each (a `-free` spelling costs 0 beside the
paid one). The catalog itself stays lean: its builder dropped full endpoint prices
at about 1.9 MB because routing reads none of them. An endpoint models.dev does not
list, such as a private gateway, is priced from the harness's own provider config
(Pi's `models.json`, an OpenCode config) when one is passed, otherwise at the
creator's endpoint and marked approximate. The row's prompt size, input plus cache,
selects the tier. What models.dev does not publish lives in
`references/price-rules.json`, each rule with its official source, date and quote.
Every figure names the price and rule revisions. The catalog's `cache_write` is the 5-minute rate.
A 1-hour write on an Anthropic model is priced at twice the input rate, the
multiplier the official pricing page publishes for every Claude model; providers
that log one write bucket use `cache_write`. A host-reported cost is
stored only as a comparison field. A model absent from the catalog is `unpriced`,
whatever the host reported.

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
- **EX-006** (unpriced): Input: a Pi row for `tritech-auto` through `tri-llm-gateway`, 51531 tokens, host `cost.total: 0`, model absent from the catalog -> Expected: `usd: null`, `priced: false`, `host_cost: 0` kept as a comparison field; the run total is marked `partial`.
- **EX-007** (purged source): Input: a worker transcript deleted by the host before harvest -> Expected: that delivery's usage is `missing` with the reason; rows harvested earlier remain.
- **EX-008** (1-hour cache write): Input: a Claude Code row on `claude-opus-5-5` with `ephemeral_1h_input_tokens: 488681` and catalog input 4 -> Expected: that bucket priced at 8 USD per million, 3.91 USD; the measured session of 2026-10-24 (89 responses) is priced at 10.12 USD, the figure the official rates give.
- **EX-009** (context tier): Input: a row on Anthropic's `claude-haiku-5-5` with a 150000-token prompt -> Expected: priced at the tier above 100000 tokens that the endpoint publishes (input 0.50, output 2.50), not at the base rate.

## Rejected Alternatives

- **RA-001**: run totals only; rejected because they cannot say which role or tier spent the tokens, which is the data routing calibration needs.
- **RA-002**: a hard stop through per-host hooks; rejected for now because enforcement is not proved on all five hosts and the protocol does not claim token enforcement.
- **RA-003**: a separate cost plugin; rejected because it would be a second owner of run facts beside the run record.
- **RA-004**: storing usage in a vector memory through an npm CLI, as ruvnet/ruflo's cost tracker does; rejected because the toolchain is stdlib Python with no runtime service.
- **RA-005**: outcomes or usage reported by the model itself (ruflo's `hooks_model-outcome`); rejected because a model's account of its own success is not evidence. Outcomes come from deliveries and gates.
- **RA-006**: billing APIs or a host's `/cost` output; rejected because they need network and credentials and do not attribute to workers.
- **RA-007**: treating an unpriced model or an unreadable source as 0; rejected because it turns a gap into a false saving.
- **RA-008**: ignoring cache tokens; rejected because cache reads and writes were 82% of the cost of the measured session of 2026-10-24 at official rates (1.81 USD counted against 10.12), and a run that reuses its cache well would look almost free.
- **RA-009**: pricing every cache write at the catalog's single `cache_write` rate; rejected because it priced the measured session at 8.65 USD against 10.12 (15% low), while the exact 1-hour rate needs no catalog field.
- **RA-010**: reporting the host's cost; rejected because a gateway logged 0 USD for 51531 tokens, so a host figure is not evidence of a price.
- **RA-011**: a hand-maintained price list per model family, like ruflo's `data/prices.json` (20 rows); rejected because it covered three families and already carried a wrong rate (Sonnet 5.5 cache read 0.2 against the official 0.10).

## Enforceable Invariants

- **INV-001**: the ledger reads only local host logs: no network, no credentials, no dependency outside the standard library; SQLite is opened read-only.
- **INV-002**: an unsupported, unreadable or purged source is recorded as `unavailable` or `missing` with its reason, never as zero tokens or zero cost.
- **INV-003**: harvest is idempotent: the same logs produce a byte-identical `usage` section, and each source row is counted once by its host key.
- **INV-004**: every host is normalized to the same row shape, with `input` meaning uncached input and cache reads and writes in their own buckets.
- **INV-005**: every USD figure is computed from the catalog and names its revision; a host-reported cost is a comparison field and never the reported figure.
- **INV-006**: after a budget is reached no wave starts without a recorded `spend` grant.
- **INV-007**: usage is evidence, not authority: it never changes a delivery status, a gate or a completion decision.
- **INV-008**: no model family has a hand-written price; every rate comes from the catalog's endpoint data or from a provider rule that names its official source and date.

## Consequences

- `contracts/work.toml` gains the `usage` loop section, the optional `budget.max_usd` and `budget.max_tokens`, a worker handle on deliveries and the grant kind `spend`.
- A new helper under `skills/work-record/scripts/` reads the four hosts; `run_state.py` validates the section.
- `project-lifecycle` waves gain the harvest and budget check at each boundary; finish reports totals per phase and per worker.
- The catalog's prices become load-bearing. They are marked indicative today. Checked on 2026-10-24 against the official Claude pricing page: the catalog matches it for Fable 5.1, Opus 5.5, Opus 5 and Haiku 5.5, and its `cache_write` is the 5-minute rate; for Sonnet 5.5 it lists cache read at 0.2, the price of its selected `opencode` endpoint, where the page and models.dev's Anthropic endpoint say 0.10. Pi's own cost for one Opus 5.5 response (0.5006312 USD) reproduces exactly at the official rates with its single write bucket priced at the 1-hour rate.
- ADR-0002 moves this section with the run record to `work-controller:work-record`.
- The parked draft `docs/superpowers/specs/2026-10-24-derived-routing-signals-draft.md` gets its calibration data from this ledger joined to verified outcomes.
- Open before acceptance: Pi worker attribution through `pi-subagents`, how the coordinator learns its own host session id on each host, and a Copilot source.
- Pricing ships as `scripts/usage_pricing.py` (one reader per host, the pricer, a `summary` and a `rows` command), `scripts/build_model_prices.py`, `scripts/price_crosscheck.py` and `references/price-rules.json`, refreshed with the catalog through `references/model-catalog-refresh.md`; they move with the catalog to `model-routing` after ADR-0002. Measured on the local logs of 2026-10-24: every priced OpenCode group reproduces the host's logged cost exactly, and every Pi group does where the harness prices did not change since.
- Provider rules: Anthropic verified on 2026-10-24 (1-hour write twice input, `inference_geo: us` 1.1 times); OpenAI, xAI, Moonshot, DeepSeek, Google, Alibaba, Zhipu, Mistral, MiniMax and Xiaomi still to verify on their official pricing pages.
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
