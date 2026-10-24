# Derived routing signals (temporary draft)

Status: temporary draft, parked on 2026-10-24. Nothing here is decided. A Proposed
record under `docs/adr/` replaces this file when the work resumes; delete this file
then.

## Problem

`task_router.py` already selects the model deterministically: weights, thresholds,
floors and the selection rule are code. Only the ten signals of `SIGNALS`
(`task_router.py:107`) come from a model call. For every LLM node the coordinator
runs five steps from `references/task-routing.md`: write `REQUEST.txt`, run `plan`,
call the cheapest classifier, save `REPLY.txt`, run `assign`. The cost is one model
call per node plus a procedure that an economical coordinator must follow exactly
(enum rules, no repair, fallback on failure). The accuracy of that classifier has not
been measured.

For a wave task or a review job, most signals are already facts in the run: the
`write_set` (at most 4 files, `contracts/work.toml` `[loop.waves]`), the role, the
phase, the grants, the Codebase Map and the knowledge selected by skill-catalog.
Asking a model to restate them spends tokens and adds a point of failure.

## Proposal

A `derive` subcommand of `task_router.py` computes the signals from structured
inputs, with no model and no network, and feeds them to the existing weighting and
selection unchanged. The model classifier remains only for the free-text request that
opens a run, before a plan exists: one call per run instead of one per node.

| Signal | Deterministic rule | Source | Strength |
|---|---|---|---|
| `work_type` | declared by the role (test-writer: coding, reviewer: analysis, doc writers: writing); image inputs: vision | role declaration | exact |
| `scope` | 1 file: single_file; 2 to 4: few_files; one map module: module; several: cross_module; glob or repository: repo_wide | `write_set`, map modules | exact |
| `ambiguity` | before the interview: needs_interview; record and oracle present: fully_specified; oracle missing: minor_gaps | run phase, `adr`, task `oracle` | exact |
| `risk` | path rules (migrations, CI workflows, infrastructure, deletions in the `write_set`); push, publish or purge grant: irreversible; cross-module: reversible_broad | `write_set`, `grants` | exact on paths |
| `tool_use_required` | the role's tools include edit or shell | role declaration | exact |
| `evidence_required` | review, audit or verification phase | phase | exact |
| `long_context` | input bytes / 4 against `TIER_MIN_CONTEXT` (8k, 32k, 128k) | input digests | exact (token estimate) |
| `reasoning_depth` | floor from the role (adversarial reviewer: adversarial_review; record author: architectural); otherwise fan-in and blast radius of the touched files | role, map `compute_fan_in` (`codebase-map/.../classifier.py:255`), `blast_radius` (`snapshot.py`) | heuristic |
| `domain_knowledge` | none selected: none; stack skill: common; vertical skill: specialized | skill-catalog selection | heuristic; the catalog has no level field today |
| `output_volume` | line count of the `write_set` files plus output kind (documentation: long) | `write_set`, role | heuristic |

### Keywords escalate only

A keyword in the request may raise a signal, never lower it: "migrate", "drop",
"prod", "force" and similar raise `risk`. A false alarm costs tokens; a false
reassurance costs a wrong task. This is the same asymmetry as `FALLBACK_TIER = tier3`.
Keywords never classify on their own: ruflo's keyword agent router scores 0.257
accuracy on its own 197-prompt corpus (`router-bench-2026-09-23.json`, candidate A).

### Missing facts escalate

A signal whose source is absent (no map, undeclared role, unreadable input) resolves
to its most demanding value, recorded with the reason. `derive` never guesses
downward, matching the existing `--no-reply` path.

## Calibration (deferred)

The three heuristic signals use guessed thresholds (for example a fan-in above N
means multi_step). They become measured only with verified outcomes per node: oracle
green on first attempt, review findings, retries, tokens and cost. That needs the
per-run cost and outcome ledger discussed on 2026-10-24, which does not exist yet.
Outcomes must come from tests and cycle gates, never from the model's own report.
A learning router fed by self-reported outcomes is the defect seen in ruflo's
`hooks_model-outcome` bandit.

## Work outline

1. Role declarations: `work_type`, tools, evidence and depth floor in role metadata,
   validated by the compiler against the `SIGNALS` enums.
2. Catalog field: a knowledge level per skill, read by skill-catalog.
3. `task_router.py derive --task TASK.json --run RUN.json --map MAP --out SIGNALS.json`,
   output identical in shape to a parsed classifier reply, plus a `derived_from`
   entry per signal.
4. `references/task-routing.md`: structured nodes use `derive` then `assign`;
   the model classifier stays for the opening free-text request.
5. Tests: one case per rule, the escalation cases, byte-identical output across runs.

Estimate: 1 to 2 days for steps 1 to 5. Calibration follows the ledger.

## Open questions

- Which roles lack a natural `work_type` and need an explicit choice.
- Whether `reasoning_depth` should use fan-in of touched symbols or of touched files.
- Whether the opening request needs routing at all or runs on the session model.

## Provenance

Prompted by a reading of [ruvnet/ruflo](https://github.com/ruvnet/ruflo) (MIT) on
2026-10-24: its model router (`v3/@claude-flow/cli/src/ruvector/model-router.ts`)
scores complexity lexically and learns tier choice with a Thompson bandit. This draft
adopts only the idea of offline signal computation and learning from outcomes, with
original content. If the work is accepted, the intake method's watch row and README
paragraph apply.
