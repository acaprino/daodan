# Choicer offline pilot results

**Verdict: this pilot does not justify opening Decision Log shadow mode or promoting Julia as a replacement.** The exact catalog is incompatible with Julia's lossless input contract. Adaptation is a separate exploratory experiment, and critical-role coverage remains incomplete.

This verdict applies to the evaluated input formulations. It does not establish that local reviewer routing is infeasible. The [follow-up usage diagnosis](DIAGNOSIS.md) finds a measured source-presentation effect and tests alternative questions, runtime parity and fresh controls.

See the [all-reviewer selection follow-up](ALL_REVIEWERS_RESULTS.md) for the expanded 22-role applicability experiment.

Execution date: 2026-10-20. All changes are development assets under this benchmark directory.

[Original detailed results](runs/20261020T100258Z/RESULTS.md) and [adapted detailed results](runs/20261020T100258Z-adapted/RESULTS.md) contain the reliability tables, individual-role diagnostics, per-case wall/CPU timings, runtime identities and anomalies. The full threshold curves are in the [original scoring JSON](runs/20261020T100258Z/scores.json) and [adapted scoring JSON](runs/20261020T100258Z-adapted/scores.json). [Comparison data](runs/20261020T100258Z/adapted-comparison.json) is derived offline.

## Results and coverage

A uses the frozen full-mode prompt with the original catalog. Its passing responses satisfy limited citation checks; base/candidate identity was omitted from the supplied hunks and remains unverified. B and C use the exact catalog; B is binary noul at 0.5, C is one categorical choice per hunk.

Adapted B/C use all 18 reviewer IDs with independently authored compact criteria. Three missing negatives and security/premise/logic policy changes are explicit. The author read no cases, labels or predictions. Whole cases C02 and C07 were excluded using pre-inference context-size evidence, leaving 9 cases and 41 unchanged hunks. There is no adapted LLM baseline.

| Implementation | Complete cases | Labeled scored | Expected-role recall | Critical recall | Excess / labeled case | Descriptive ECE |
| --- | --- | --- | --- | --- | --- | --- |
| A: original LLM, limited checks | 7/11 | 7 | 4/16 (25.0%) | 1/3 (33.3%) | 0.857 | unknown |
| B: exact Julia noul | 0/11 | 0 | 0/0 (unknown) | 0/0 (unknown) | unknown | unknown |
| C: exact Julia choice | 0/11 | 0 | 0/0 (unknown) | 0/0 (unknown) | unknown | unknown |
| Adapted Julia noul | 9/9 | 9 | 14/18 (77.8%) | 5/5 (100.0%) | 12.444 | 0.689 |
| Adapted Julia choice | 9/9 | 9 | 0/18 (0.0%) | 0/5 (0.0%) | 1.556 | unknown |

Adapted binary routing selects 14.0 of 18 reviewers per case on average. Its measured critical recall therefore comes with broad selection; this pilot does not demonstrate economical routing. The categorical control misses every expected activation on the adapted subset.

The rows have different coverage and must not be read as a controlled accuracy ranking. Expected dimensions are partial positive labels: excess selections are a benchmark proxy, not proof of wasted reviewer work. Missing predictions never become negatives.

## Critical roles

| Role | A hits / support | Exact B hits / support | Adapted B hits / support |
| --- | --- | --- | --- |
| security | 0/1 (0.0%) | 0/0 (unknown) | 1/1 (100.0%) |
| premise | 0/0 (unknown) | 0/0 (unknown) | 0/0 (unknown) |
| data-integrity | 1/2 (50.0%) | 0/0 (unknown) | 4/4 (100.0%) |

| Exact B diagnostic only | Accepted encodings | Conditional hits / support | Conditional recall |
| --- | --- | --- | --- |
| security | 125 | 0/0 | unknown |
| premise | 0 | 0/0 | unknown |
| data-integrity | 125 | 1/1 | 100.0% |

The conditional table evaluates one representable role at a time across all hunks of its supporting cases. It does not establish a valid full-catalog routing decision.

There are no premise-positive cases. Its recall is undefined, so this pilot cannot establish the full critical-role non-inferiority condition even if other measured roles pass.

## Per-case selections and agreement

A/B is the required exact-catalog comparison. The separate A/adapted column is exploratory and combines changes to the model and reviewer criteria. Each agreement cell gives exact equality and Jaccard overlap.

| Case | Expected | A | Exact B | Adapted B | Adapted choice | A/B agreement | A/adapted reference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | data-integrity, temporal | distributed-flow, logic-integrity, premise | unavailable | platform, React-performance, workspace, api-contract, chicken-egg-detector, cleanup, code, data-integrity, distributed-flow, logic-integrity, premise, resource, security, temporal, ui-race, test-suite, type-safety | platform, cleanup | unavailable | False; 0.176 |
| C02 | unlabeled | unavailable | unavailable | excluded by context rule | excluded by context rule | unavailable | unavailable |
| C03 | data-integrity | unavailable | unavailable | platform, React-performance, api-contract, chicken-egg-detector, cleanup, code, data-integrity, distributed-flow, premise, security, temporal, ui-race, test-suite | platform, cleanup | unavailable | unavailable |
| C04 | logic-integrity, temporal | premise | unavailable | platform, React-performance, workspace, api-contract, chicken-egg-detector, cleanup, code, data-integrity, distributed-flow, logic-integrity, premise, resource, security, temporal, ui-race, test-suite | platform, cleanup | unavailable | False; 0.062 |
| C05 | logic-integrity, security | none | unavailable | platform, React-performance, workspace, api-contract, chicken-egg-detector, cleanup, code, data-integrity, distributed-flow, premise, resource, security, temporal, ui-race, test-suite | platform, cleanup | unavailable | False; 0.000 |
| C06 | temporal, ui-race | none | unavailable | platform, React-performance, workspace, api-contract, chicken-egg-detector, cleanup, code, data-integrity, distributed-flow, logic-integrity, premise, resource, security, temporal, ui-race, test-suite | platform, cleanup | unavailable | False; 0.000 |
| C07 | cleanup, code, logic-integrity, temporal, ui-race | unavailable | unavailable | excluded by context rule | excluded by context rule | unavailable | unavailable |
| C08 | data-integrity | unavailable | unavailable | platform, React-performance, api-contract, chicken-egg-detector, cleanup, code, data-integrity, distributed-flow, premise, temporal, ui-race, test-suite | cleanup | unavailable | unavailable |
| C09 | code, resource, temporal | resource, temporal | unavailable | platform, React-performance, workspace, api-contract, chicken-egg-detector, cleanup, code, data-integrity, distributed-flow, premise, security, temporal, ui-race, test-suite | platform | unavailable | False; 0.067 |
| C10 | data-integrity, distributed-flow, logic-integrity | data-integrity, premise, security | unavailable | platform, React-performance, workspace, api-contract, chicken-egg-detector, code, data-integrity, distributed-flow, premise, temporal, ui-race, test-suite, type-safety | cleanup | unavailable | False; 0.143 |
| C11 | code, temporal | temporal | unavailable | platform, React-performance, api-contract, cleanup, code, data-integrity, premise, ui-race, test-suite, type-safety | cleanup | unavailable | False; 0.000 |

Cross-catalog reference: 7 paired cases, exact agreement 0.0%, mean Jaccard 0.064. This is not evidence of an isolated classifier effect.

| Exploratory common-case reference | Labeled cases | Expected-role recall | Critical recall | Excess / case |
| --- | --- | --- | --- | --- |
| Original A on common cases | 7 | 4/16 (25.0%) | 1/3 (33.3%) | 0.857 |
| Adapted B on common cases | 7 | 12/16 (75.0%) | 3/3 (100.0%) | 12.714 |

## Output validity and exact-input failures

Four native A outputs fail the limited checks: C02/C03/C07 cite an incorrect hunk or snippet; C08 contains a 16-word reason against the prompt's 15-word limit. Their raw declarations are retained in a separate diagnostic, never used in primary recall, agreement or the verdict. The marker omission affects all A outputs regardless of whether their other checks pass.

Unvalidated declaration diagnostic only: 11 readable role sets, 7/23 expected activations, critical recall 40.0%, and 1.400 excess selections per labeled case. These numbers show the effect of validation attrition; they are not a replacement baseline.

The exact binary catalog has three missing negatives and additional criteria beyond Julia's 48-token option limit. Only nine of 18 reviewer pairs fit losslessly; the critical premise criterion does not. The exact choice control also fails its input contract. Successful partial answers remain visible in the detailed report. Four original source states already exceed 8192 tokens; no truncation was applied.

After establishing that universal catalog failure, execution switched to atomic full-catalog validation: every remaining question is checked, but any rejected question prevents classification of that incomplete batch. Historical partial inference is retained as such. Validation-only attempts are not classifier predictions or measurements of classifier inference speed.

## Execution and reproducibility

A: OpenAI through native Codex tasks, requested and accepted model override `gpt-6-luna`, low effort, 11 isolated case tasks and no reruns. Provider-reported model identity, API-call count, usage and inference timing are unknown. Exact loader prompts and returned responses are saved. The transport includes the loader and host system/tool context; cheapest-model pricing was not independently verified.

B: `SupersonicLabs/Julia-1`, revision `a85b127321d580d65176c89ced8273f305745d85`, CPU FP32, weight SHA-256 `df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72`. The recorded environment uses torch 2.14.0, transformers 5.0.0, safetensors 0.8.0 and numpy 2.5.4. Hardware: Intel Core Ultra 7 155H, 22 logical processors, 33,775,378,432 bytes physical RAM; four inference threads, no GPU.

The original local run began with batch size 16 (nine representable questions per hunk) and was resumed with batch size 1 after an observed memory peak of 19,316,727,808 bytes resident and 26,873,974,784 bytes private allocation. Saved outputs are retained unchanged; interrupted attempts and runtime segments are recorded under `execution/`. These timings describe the executed workload, not a controlled model-speed comparison. Cold means first inference in a process; OS caches were not flushed. Load and interrupted work are separate from completed-call totals.

All model inputs and outputs are JSON. Scores are bound to the exact input, catalog and prompt hashes. Frozen prompts match the current spec bodies despite concurrent edits elsewhere in that document. All 129 original hunks were independently rematerialized from their recorded source revisions or inline case sources. Historical fix localization is retrospective sampling, and no symbol cards were supplied.

Rebuild both detailed reports and this summary without inference:

```powershell
python -B evals/senior-review/choicer-eval/summarize_runs.py `
  --original runs/20261020T100258Z `
  --adapted runs/20261020T100258Z-adapted
```

## Dimension mapping and display names

| Expected dimension | Exact role ID | Display name |
| --- | --- | --- |
| architecture | senior-review:code-auditor | code |
| data-integrity | senior-review:data-integrity-auditor | data-integrity |
| distributed-flow | senior-review:distributed-flow-auditor | distributed-flow |
| documentation | senior-review:cleanup-auditor | cleanup |
| hygiene | senior-review:cleanup-auditor | cleanup |
| logic-integrity | senior-review:logic-integrity-auditor | logic-integrity |
| premise | senior-review:premise-auditor | premise |
| resource | senior-review:resource-lifecycle-auditor | resource |
| resource-lifecycle | senior-review:resource-lifecycle-auditor | resource |
| security | senior-review:security-auditor | security |
| temporal | senior-review:temporal-resilience-auditor | temporal |
| temporal-resilience | senior-review:temporal-resilience-auditor | temporal |
| ui | senior-review:ui-race-auditor | ui-race |

Other selected roles retain their registered names with the `-auditor` suffix omitted in compact tables; all exact IDs appear in the detailed JSON and reports.

## Gates and token economics

The user explicitly authorized the benchmark-local uv environment, approximately 584 MiB of Julia snapshot files plus runtime dependencies, and 11 native gpt-6-luna case tasks after disclosure of the 184,073-token planning estimate (characters/4, not measured usage). Reviewer adaptation was separately authorized. No additional paid adapted baseline, secondary laya run or optional task-tier run was performed. No plugin dependency or kernel file was changed.

Net tokens saved per run = tier1 Choicer tokens avoided + downstream reviewer tokens avoided - routing-error costs. **Unknown**: provider usage, actual downstream spend and the cost of missed reviews were not measured. Local inference itself does not establish a positive token balance.

## Proposed spec update

Treat Julia-1 as an unpromoted experimental adapter. The 11-case pilot found that exact reviewer metadata cannot be encoded losslessly, while a separately authored nine-case adaptation changes the routing contract and lacks a matched LLM baseline. Before opening Decision Log shadow mode, define canonical typed criteria, repair the evidence-side binding, specify handling for oversized hunks, and rerun with an independent premise-positive set and provider-level telemetry. Keep the fixed threshold and full provenance; require critical-role false negatives no worse than the matched baseline and measured positive net token savings before considering promotion.

---

## Gutsy local decision model evaluation (`kouhxp/gutsy` on CPU)

The saved V1 and V2 outputs are exploratory observations. The earlier wording of
this section overstated their provenance, calibration, citation quality and runtime
verification. The corrections below supersede those claims without altering the
historical JSON results.

| Historical run | Expected-role recall | Security + data recall | Excess / labeled case | Mean reviewers / case |
| --- | --- | --- | --- | --- |
| [V1](runs/20261020T100258Z/gutsy-eval-summary.json) | 13/23 (56.5%) | 3/5 (60.0%) | 1.50 | 2.8 |
| [V2](runs/20261020T100258Z/gutsy-v2-summary.json) | 18/23 (78.3%) | 4/5 (80.0%) | 2.40 | 4.2 |

Both scored ten labeled cases; C02 is unlabeled. V2 recovered the expected roles
on C04 and C05 but missed both expected roles on C01, temporal on C06, and cleanup
and UI on C07. The four tier examples returned their expected choices. Four
hand-authored tasks do not validate tier assignment on real execution outcomes.
Security support is one case. Premise support is zero and that lens was not queried.

### Corrections established by inspecting the runners

- **Context provenance:** V2's `module_contexts` dictionary is handwritten. It
  does not load `01-structure.md`, `04-semantics.md`, symbol cards or one-hop edges.
  Its author had access to case ground truth. Label contamination cannot be ruled
  out merely because expected role IDs were absent from the transmitted state.
  V1 also explicitly transmitted `source_case` titles, violating the blind-input rule.
- **Coverage:** `build_hunks_repr` clips each hunk to 350 characters, restores
  original order after picking first-per-file entries, then stops near 2,800
  characters. It does not ensure every touched file is represented. Truncation is
  an observed input defect; it is not proven to explain every missed activation.
- **Probabilities:** V2 normalizes token strings with `strip().upper()` and assigns
  them into a dictionary, allowing distinct token IDs to overwrite each other.
  Missing top-k entries become zero. Its raw-vocabulary heuristic is neither the
  proposed 0.30 threshold nor fitted task calibration. A claimed 35x security
  margin was not established by the saved summary.
- **Citations:** only the first eight original hunks are candidates, even when
  their bodies were not transmitted. Rejection falls back to the first hunk;
  single-hunk cases and fixed rules have no such citation query. Mapping a letter
  to an existing line does not establish semantic relevance. The earlier claim
  of valid citations for every activated specialist is withdrawn.
- **Runtime:** `-np 1` and `cache_prompt: true` request caching, not prove reuse.
  V2's saved averages range roughly 1.5 to 3.8 seconds per query, not per complete
  case. The prior ~650 MB figure was not accompanied by a V2 peak-memory trace.
  HTTP 503 was observed during startup; cache compaction was not established as
  its cause. Retry sleeps in the runner are constant/linear, not exponential.
- **Comparisons:** cloud, Julia and Gutsy rows use different inputs, catalogs,
  validation and case coverage. They do not prove a controlled model ranking or
  that a promotion gate has passed. Excess against partial labels is not precision.

### Frozen input and question follow-up

[`gutsy_followup.py`](gutsy_followup.py) separates two experiments:

1. C01/C07: the same V2 questions and handwritten context, with truncated input
   versus complete file-scoped windows. Selection is exact generated `A` in both
   arms; the broken probability heuristic is not reused. This comparison isolates
   packing under a common decoding policy, not the entire historical V2 result.
2. Eight additional functions from pinned Jupiter source: a frozen V2 prompt
   versus one candidate phrasing with positive and negative boundaries. Four
   files are development examples and four different files are verification
   examples. They are real code with coordinator-authored applicability judgments,
   not eight newly verified bugs or an independently blinded test set.

The [completed run](runs/20261020-gutsy-followup-ctx1536/) delivered all 496 planned
calls with no invalid output, and its independent verification passed. Three earlier
attempts with larger batch or context settings were stopped by the memory watchdog;
they are retained and never scored as model answers. Sampled peak combined memory of
the completed run was 977,641,472 bytes.

- **Input packing:** complete windows recovered temporal on C01 (0/2 to 1/2) and
  ui-race on C07 (3/5 to 4/5). Data-integrity on C01 and cleanup on C07 were still
  missed. C07 needed 312 calls and 23 minutes, with temporal activated in every
  window, so a plain union across windows is not a usable aggregation rule.
- **Questions:** on eight real-source functions, V2 found 5/11 expected perspectives
  and the candidate 7/11; neither activated any of 30 explicitly negative ones.
  Verification alone was a tie at 4/5. Both missed security and logic on the
  account visibility filter. The sample is too small to promote either wording.
- **Runtime:** no request reused the prompt prefix in that run. A slot-restore
  replay of all 496 prompts ([comparison](runs/20261021-gutsy-followup-slot/COMPARISON.md))
  reused the prefix on every call and ran 3.44x faster (580 s against 1,995 s).
  495/496 letters matched; the flip was a near tie and left every recall and
  negative-activation total unchanged. Slot restore is adopted for later runs.

Full tables, probabilities and the next iteration are in
[QUESTION_REFINEMENT.md](QUESTION_REFINEMENT.md). No production or specification
change is implied.
