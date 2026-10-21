---
name: multi-model-deliberation
description: >
  Coordinates bounded independent proposals and reciprocal critique.
  TRIGGER WHEN: /daodan:get-second-opinion receives a question rather than a file, or explicitly requesting Ultra Nerd, moe, or a multi-model expert debate for a difficult problem.
  DO NOT TRIGGER WHEN: challenging an existing plan only (use peer-review:cross-model-peer-review).
---

# Multi-model deliberation

Execute a deliberation with `references/deliberation.md`. This skill supplies the method;
the `moe` MCP server owns run-directory creation (`.moe/<run-id>/`), payload composition,
identity pinning and `exchange.json` state, while the active harness owns transport
admission, accounting and cancellation.

Load the `peer-review:cross-model-peer-review` skill for its independence and safety
doctrines. Use the `moe` MCP server (`moe_models`, `moe_ask`); do not call `peer_ask`
and do not claim peer-review certification.

## How it works

1. **Freeze the brief (≤ 6000 UTF-8 bytes):** state the problem, constraints, evidence
   locators and success criteria. Discover two distinct models via `moe_models` and
   obtain or confirm user consent for the higher token/latency cost.
2. **Round 1 — Independent proposals:**
   - Call `moe_ask(model=model_a, phase="proposal", brief=brief_text)`. The MCP server
     automatically creates `<run_root>/<run_id>/`, writes `brief.md` and `exchange.json`,
     and returns `run_id` alongside the first proposal.
   - Call `moe_ask(model=model_b, phase="proposal", run_id=run_id)`. The MCP server
     reuses `brief.md`, pins `peer_model` to the first returned identity, rejects
     model collisions, and records the second proposal.
3. **Round 2 — Reciprocal critiques (and optional Round 3):**
   - Call `moe_ask(model=model_a, phase="critique", run_id=run_id)` and
     `moe_ask(model=model_b, phase="critique", run_id=run_id)`. The MCP server
     automatically composes each reciprocal payload from `brief.md` and both previous
     replies, pins `expected_model` and `peer_model`, and updates `exchange.json`.
4. **Verify and synthesize:** check decisive claims against the actual repository or
   available evidence, write `<run_root>/<run_id>/answer.md`, and deliver the synthesized
   recommendation with model identities, completed rounds and observed usage.

## Load map

| Need | Reference |
|---|---|
| Running a deliberation on a question (`/daodan:get-second-opinion`, or an explicit Ultra Nerd or moe request): preparation, managed `moe_ask` calls, failure codes and synthesis | `references/deliberation.md` |
