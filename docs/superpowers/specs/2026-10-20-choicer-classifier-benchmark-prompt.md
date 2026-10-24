# Work prompt: benchmark a Jev-like classifier against the LLM `tier1` Choicer

Date: 20 October 2026. Companion to section 8 of
`docs/superpowers/specs/2026-10-19-graph-grounded-economy-routing-design.md`.
This file is the self-contained brief to hand to an agent session (any host)
that will build and run the benchmark. It grants no permission by itself: the
authorizations in "Gates" must be given in the session.

---

```text
# ROLE

You are working inside the Daodan repository (D:\Projects\daodan, branch master).
Your task is to build and run an OFFLINE benchmark that compares two implementations
of Daodan's routing Choicer on real inputs, and to report the results with evidence.
You do not modify the task cycle, the kernel prompts, or any file under plugins/
in this task. Everything you produce is a development asset under evals/.

Read first, in this order:
1. docs/superpowers/specs/2026-10-19-graph-grounded-economy-routing-design.md
   sections 3.6 (typed-decision Choicer contract and the three LLM prompts),
   7.5 (verified facts on EdgeJev and Julia-1, promotion criterion) and 8
   (the plan this task executes).
2. evals/senior-review/README.md, evals/senior-review/RESULTS.md and every
   evals/senior-review/cases/*/case.md (11 cases; the "Expected dimension"
   column is the ground truth for reviewer activation).
3. The reviewer role bodies: plugins/*/roles/*.md. Extract, for every role, the
   exact TRIGGER WHEN and DO NOT TRIGGER WHEN text from the frontmatter
   `description`. Do not hand-write or paraphrase them; parse them.
4. AGENTS.md sections "Working discipline", "Deliberately not vendored" and
   "Dependency policy". Nothing you install becomes a dependency of any plugin.

# WHAT IS BEING COMPARED

The Choicer contract (spec 3.6) is: (state, questions) -> probability per option.
Two implementations:

A. LLM tier1 (the implementation in force). Use the exact REVIEWER_CHOICER and
   TASK_TIER_CHOICER prompts from spec 3.6, verbatim, on the session's cheapest
   available model (the one `init` would register as tier1). Do not edit the
   prompts. Record the model identity actually used.

B. Jev-like local classifier (candidate). Primary: SupersonicLabs/Julia-1
   (Apache-2.0, mmBERT-small encoder + decision head, 8192-token context,
   choice/score/noul over 2-20 options, 550 MiB FP32, Python 3.11+, torch on
   CPU). Secondary, only if time allows: `laya` served by yzfly/edgejev
   (ONNX INT8, 324 MB). Treat every claim in their model cards as a claim,
   not as a result: you measure.

# SNODO 1 (REQUIRED): REVIEWER SELECTION, noul PER (reviewer, hunk)

Ground truth: for each of the 11 cases, the set of roles named in "Expected
dimension" (map dimension names to role IDs, e.g. data-integrity ->
senior-review:data-integrity-auditor, logic-integrity ->
senior-review:logic-integrity-auditor, distributed-flow ->
senior-review:distributed-flow-auditor, security ->
senior-review:security-auditor, premise -> senior-review:premise-auditor,
resource -> senior-review:resource-lifecycle-auditor, temporal ->
senior-review:temporal-resilience-auditor). Write the mapping table in the
results file so it can be checked.

Inputs per case:
- Materialize the buggy code of the case as the "diff under review" (the case
  file says how). Split it into hunks H1..Hn deterministically (one hunk per
  top-level function or per contiguous changed block; record the rule you use).
- state = the hunk text, plus any symbol card the case supplies. Do not add
  the case's own ground-truth table or scoring notes to the state. That is
  leakage and invalidates the run.
- questions = one `noul` per reviewer role in the catalog:
  instructions = "Does this hunk satisfy the reviewer's TRIGGER WHEN?";
  criteria.true = the role's TRIGGER WHEN text;
  criteria.false = the role's DO NOT TRIGGER WHEN text.
  All roles are asked, for every hunk. A role is "selected" for the case if
  any hunk gives P(true) >= threshold.
- Control variant: one `choice` over all ~20 roles per hunk (to measure the
  degradation the model card predicts on close labels).
- Implementation A gets the same hunks with the same enumerated IDs, through
  the verbatim REVIEWER_CHOICER prompt in mode "full", with the catalog
  rendered from the same parsed TRIGGER WHEN / DO NOT TRIGGER WHEN text.

Thresholds: fix the `noul` threshold on a held-out split BEFORE scoring the
rest (e.g. leave-one-case-out, or fix 0.5 a priori and report the full curve).
Never tune a threshold on the cases you then report.

Metrics, per implementation and per variant:
- recall on expected roles, overall and separately on the critical roles
  (security-auditor, premise-auditor, data-integrity-auditor);
- false activations per case (roles selected that are not expected): this is
  wasted tier2 reviewer spend;
- calibration: reliability table and ECE of P(true) against the ground truth;
- latency per case (wall clock, CPU, cold and warm) and, for A, input/output
  tokens as reported by the provider (or "unknown" if not reported);
- a per-case table: expected roles, A selected, B selected, agreement.

# SNODO 2 (OPTIONAL IN THIS TASK): TASK TIER, choice + score

There is no labeled ground truth yet. Do not invent one. If you do anything
here, limit it to: run TASK_TIER_CHOICER (A) and a Julia-1 `choice` over
{tier1, tier2, tier3} plus `score` over {low, medium, high} (B) on the
micro-tasks of the live probe report
docs/superpowers/reports/2026-10-19-closed-loop-probe-claude.md, and report
agreement between A and B only. Label it explicitly as agreement, not accuracy.

# DELIVERABLES

1. evals/senior-review/choicer-eval/run_eval.py
   - PEP 723 script header (`# /// script` with `dependencies = [...]`), run
     with `uv run --no-config --no-project --script`. Standard library only
     for everything except the model runtime it declares.
   - Subcommands: `extract-catalog` (parses plugins/*/roles/*.md into JSON),
     `materialize-cases`, `run --impl llm|julia|laya --variant noul|choice`,
     `score`, `report`.
   - Writes every model input and output to evals/senior-review/choicer-eval/
     runs/<timestamp>/ as JSON, so a reviewer can re-score without re-running.
   - Never writes outside evals/senior-review/choicer-eval/.
2. evals/senior-review/choicer-eval/README.md: how to run, what each metric
   means, the dimension-to-role mapping, the hunk-splitting rule, the
   threshold protocol.
3. evals/senior-review/choicer-eval/RESULTS.md: the comparison tables, the
   model identities (A: provider/model; B: HF repo, revision/commit, weight
   SHA-256, FP32 or INT8, runtime versions), hardware, dates, and a plain
   verdict against the promotion criterion in spec 7.5:
   net tokens saved per run = tier1 Choicer tokens avoided
   + tier2/tier3 tokens avoided by finer routing
   - cost of routing errors introduced;
   with the hard condition that false negatives on critical roles are not
   worse than implementation A. State clearly that 11 cases are a pilot and
   that the verdict decides only whether to open shadow mode on the Decision
   Log, not promotion.
4. A one-paragraph update proposal for spec section 7.5/8 (do not edit the
   spec; put the text in RESULTS.md under "Proposed spec update").

# GATES (STOP AND ASK BEFORE EACH)

- Before downloading any weights (Julia-1 ~550 MiB; laya ~324 MB) or creating
  a new uv environment: ask the user explicitly, naming sizes and paths. These
  are external downloads onto the user's machine.
- Before making any paid LLM call for implementation A: state the model, the
  number of calls (11 cases x variants) and an estimate of input tokens, then
  ask.
- If a model card claim turns out false (e.g. context limit, API shape),
  record it in RESULTS.md and continue; do not silently adapt the protocol.

# RULES

- No file under plugins/, adapters/, exports/, scripts/ or tests/ is touched.
- No dependency is added to any plugin.toml, pyproject or package manifest.
- Evidence over assertion: every number in RESULTS.md must be reproducible
  from files under runs/<timestamp>/.
- Keep leakage out: the model never sees "Expected dimension", "Ground truth",
  "Scoring notes" or the case title.
- Silent on routine, explicit on decisions: do not narrate tool calls. Report
  rulings (e.g. the hunk-splitting rule, the threshold protocol), anomalies and
  the final results.
- Record unknowns as unknown (token usage, finish reasons, CPU model if not
  readable). Do not estimate and present it as measured.

# EXIT

Return: paths of the three deliverables, the per-case agreement table, the
critical-role recall of A and B, the false-activation rate of A and B, the
verdict sentence, and the list of gates you hit and how they were resolved.
If a gate was not granted, stop there and report what was completed.
```
