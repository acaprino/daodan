# Gutsy routing experiments: results and validity limits

Execution date recorded in the experiments: 2026-10-20.
Status after source review: **exploratory observations, not promotion evidence**.
This report corrects the earlier claims of exact-input parity, calibrated
production thresholds, runtime equivalence and a proven best operating point.
Historical result JSON files are preserved unchanged by this correction.

## Identity and what actually ran

V1 used `kouhxp/gutsy`, revision
`f9995fe26a337f1a4ea3f1a5ed38c9799e5a8f63`, Q8_0 GGUF,
811,843,008 bytes. The previously computed file SHA-256 is
`d71d7a3da4bb05fd7e26802c294fa08c937fb57c0d0fc75ea91ccc7231e708ee`.
It ran through the custom `probe_gutsy.py` PyTorch backend using
Qwen3NextForCausalLM, reconstructed tokenization, patched recurrent attention
and `decide_fast`. This is not the upstream llama.cpp runtime. The reported
cache self-check difference of 7.3e-08 checks internal cache consistency;
it does not establish model/tokenizer equivalence with upstream Gutsy.
The later batched path also needs independent parity verification.

V2 used Q4_K_M and native llama-server through `/completion`. Neither that
endpoint nor the custom V1 path establishes an end-to-end test of the official
`gutsy-inference` HTTP `/v1/systemone` service. Loading the library Engine in
V1 is a separate fact. Top-k completion probabilities, decoding a letter and
the typed-decision calibrated API are not interchangeable without proof.

Runtime observations included approximately 31-68 seconds per V1 team problem
and 40-90 seconds for several V1 case evaluations. These are custom-backend
timings, not official Gutsy performance. V2 summary values are mean query
latencies per case of roughly 1.5-3.8 seconds, not case totals or percentiles.
There is no verified sub-5-ms AST timing in the recorded comparison.
Local inference avoided hosted LLM calls for these routing requests, but still
tokenizes inputs and consumes CPU, memory and time. Net savings are unknown.

## Saved observations

Primary result: `runs/20261020T100258Z/gutsy-comparison.json`.
Input fixtures: `runs/20261020T-diagnostic/fresh-controls.json` and
`runs/20261020T-all-reviewers/suite.json`.

### Suite 1: eight small source controls

| Metric | V1 observation |
|---|---|
| Family classification | 8/8 |
| React positives / false positives | 2/2 and 0/6 |
| Persistence positives / false positives | 2/2 and 0/6 |

On the additional C01-H1 numbered source, family choice selected persistence
with probability 0.603620, while the binary persistence question returned
0.007788 and React 0.003484. Different question semantics matter; this is not
an unqualified successful persistence detection. One example cannot establish
absence of presentation sensitivity. Earlier Julia controls used different
question formulations, so juxtaposing their best/worst values is not an A/B.

The six model-router demo prompts produced choices but have no independently
validated cheapest-sufficient-model labels. Retract the earlier “6/6 correct”
claim; tier, effort and recovery accuracy were not established by those demos.

### Suite 2: twelve team problems, 22 lenses

| Threshold (descriptive curve) | Acceptable teams | Required found | Out of scope | Total selected |
|---|---|---|---|---|
| 0.45 | 2/12 | 33/39 | 16 | 53 |
| 0.50 | 2/12 | 31/39 | 12 | 45 |
| 0.55 | 2/12 | 26/39 | 7 | 35 |
| 0.60 | 1/12 | 20/39 | 4 | 25 |
| 0.65 | 1/12 | 17/39 | 2 | 20 |

At 0.50, T02 and T04 each miss two required roles; T05/T06/T07/T12 miss
one each. T08/T10 alone are acceptable. Some other teams find all mandatory
roles but add out-of-scope roles. Threshold 0.45 recovers two required
activations in aggregate, not most of the missing eight. This is not evidence
that a particular threshold is suitable for production.

### Suite 3: historical cases with transformed inputs

The runner `run_gutsy_benchmark.py` truncates each hunk using
`per_hunk_budget`, then truncates the combined state to 3800 characters.
It replaces missing negative criteria with “Not applicable to this hunk.”
Consequently the earlier “exact catalog, lossless encoding, 11/11” description
was incorrect: 11 executions completed on transformed inputs. The historical
LLM/Julia runs used other inputs and coverage. A shared scoring helper does
not make them directly comparable.

| Method | Expected-role recall | Critical hits/support | Excess per labeled case | Scored base |
|---|---|---|---|---|
| Historical validated LLM | 4/16 | 1/3 | 0.86 | 7 valid cases |
| Historical exact Julia | unavailable | unavailable | unavailable | 0 complete cases |
| Historical adapted Julia | 14/18 | 5/5 | 12.44 | 9 cases |
| Static signals | 9/23 | 1/5 | 1.5 | 10 labeled of 11 |
| AST domain router | 15/23 | 3/5 | 2.5 | 10 labeled of 11 |
| Static hybrid union | 16/23 | 3/5 | 3.8 | 10 labeled of 11 |
| V1 transformed input, 0.50 | 9/23 | 3/5 | 2.1 | 10 labeled of 11 |
| V1 transformed input, 0.40 | 13/23 | 3/5 | 3.5 | 10 labeled of 11 |
| AST union V1, 0.50 | 15/23 | 3/5 | 2.9 | 10 labeled of 11 |
| AST union V1, 0.40 | 16/23 | 3/5 | 3.4 | 10 labeled of 11 |

Sources: `RESULTS.md`, `static-router-comparison.json` and
`gutsy-comparison.json` under the historical run. The former 2.11 AST excess
value belongs to a different subset, not the 15/23 row. Excess activations
are selections absent from partial positive labels, not all proven false
positives. No premise-positive example exists in this C-case base; this does
not describe the separate all-reviewer suite. The LLM's four rejected outputs
comprise three citation failures and one reason-length violation. Its 184073
token figure is a characters/4 planning estimate, not observed provider usage.

## V2: hybrid system and unresolved provenance

`gutsy-v2-summary.json` reports 18/23 expected activations, 4/5 critical
(security 1/1, data-integrity 3/4), 2.4 excess per labeled case and 4.2 mean
selected. These arithmetic results do not establish causality or promotion.

Two scripts can overwrite that same output:
- `probe_gutsy_v2.py`: decoded A OR normalized yes probability >= 0.30 for
  critical lenses, 0.50 for other lenses;
- `run_gutsy_v2_eval.py`: decoded A OR, for critical lenses, raw p_A >= 0.15
  AND p_A > p_B.

The summary does not bind a frozen script digest, submitted payloads and
threshold profile to its results. Neither rule is the proposed 0.40 policy.
Do not retroactively assign a threshold based on the currently present script.

The latter runner uses manually authored `module_contexts` keyed by case ID,
eight targeted lens questions, code-auditor always on, and extension-based
React/TypeScript additions. It is not automated Codebase Map grounding or
full-catalog Gutsy-only selection. Input construction and label independence
need a separate audit before reporting generalization.

C08-C11 have empty citation mappings; other mappings are partial. The runner
may substitute the first hunk when citation selection rejects. Such a locator
does not prove semantic support and must not pass a citation-validation gate.
The model hash/runtime revision/calibration provenance also needs completion
in a **new** reproducible run, not invented metadata on the old summary.

## Reproduction boundaries

`show_gutsy_details.py` and `show_suite2.py` inspect saved results without
inference. The suite runner is not a certified replay harness: suite1 reruns
inference; suite2/3 skip saved IDs without complete input/runtime bindings.
Do not invoke it as an offline scorer or overwrite historical evidence.
Saved aggregates omit some raw payload/output detail; complete reproducibility
of inference is not established. The existing unit suite's green result does
not validate this custom backend or the missing bindings.

## Proposed spec update (corrected)

Keep Gutsy as an unpromoted experimental implementation of the typed-decision
contract. The previous recommendation of AST-primary plus a “validated 0.40”
Gutsy pass is withdrawn. The amended
`docs/superpowers/specs/2026-10-20-system1-work-graph-composition-design.md`
owns the proposed controller, rollout and per-decision evaluation requirements.

Before shadow/active adoption under the mother specification: use an official
runtime or demonstrate independent parity; freeze complete inputs, script and
model identities and thresholds; separate calibration from held-out scoring;
include critical positive and negative controls and a matched baseline;
measure downstream quality, recourse, CPU/latency and actual provider usage.
Do not extrapolate reviewer routing to archetype, tier/effort or retry decisions.
The deterministic graph controller can be tested independently with fixtures.
No production routing change or superiority claim follows from this pilot.
