# Evaluating prompt/context compression without effectiveness regression

## Which regression metrics matter: instruction following, precision/recall, false positives/negatives, coverage, evidence fidelity, calibration, multi-turn/long-context and independent verification?

### Takeaway

No single average score can show that compression is safe for a multi-specialist code-review pipeline. The primary outcome should be independently confirmed defect recall, guarded by false-positive, instruction, evidence and critical-stratum gates, with separate measurements before and after independent verification.

### Cited Findings

- **Verifiable instructions need deterministic, granular checks.** IFEval uses programs to check compliance and reports four accuracies: prompt-level strict, instruction-level strict, prompt-level loose and instruction-level loose. Its 541 prompts cover 25 verifiable instruction types. The paper also acknowledges that strict string checks can create false negatives, while loose response transformations can create false positives. [Instruction-Following Evaluation for Large Language Models (Zhou et al., 2023)](https://arxiv.org/abs/2311.07911). **Evidence type:** original benchmark paper with released code and prompts. **Limitation:** it measures generic, automatically verifiable instructions, not whether a code review found the right defect; loose accuracy is not an error-free oracle.
- **Evidence quality is distinct from answer fluency and correctness.** ALCE evaluates fluency, correctness and citation quality separately for end-to-end systems that retrieve evidence and generate cited answers. [Enabling Large Language Models to Generate Text with Citations (Gao et al., 2023)](https://aclanthology.org/2023.emnlp-main.398/). **Evidence type:** peer-reviewed original benchmark paper, EMNLP 2023. **Limitation:** ALCE addresses information-seeking answers and retrieval corpora, not code semantics, file/line references or test-backed review claims. Its citation metrics require adaptation rather than direct reuse.
- **Long context requires several task types and lengths, not one retrieval probe.** LongBench contains 21 datasets across six categories in English and Chinese, including code completion, multi-document QA and summarization. [LongBench: A Bilingual, Multitask Benchmark for Long Context Understanding (Bai et al., 2024)](https://aclanthology.org/2024.acl-long.172/). **Evidence type:** peer-reviewed original benchmark paper, ACL 2024. **Limitation:** public generic tasks do not establish effectiveness on a private review pipeline. RULER instead supplies configurable synthetic lengths and complexity across 13 tasks, including retrieval, multi-hop tracing and aggregation; nearly perfect needle retrieval did not imply stable performance as length increased. [RULER: What's the Real Context Size of Your Long-Context Language Models? (Hsieh et al., 2024)](https://arxiv.org/abs/2404.06654). **Evidence type:** original synthetic benchmark paper, COLM 2024. **Limitation:** synthetic retrieval and aggregation are diagnostic probes, not substitutes for held-out real code reviews.
- **Multi-turn evaluation and evaluator bias must be addressed together.** MT-Bench is explicitly multi-turn; the associated methodology paper identifies position, verbosity and self-enhancement biases and limited reasoning in LLM judges. It reports over 80% agreement between strong LLM judges and human preferences in its setting. [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685). **Evidence type:** original evaluation-methodology and benchmark paper, NeurIPS 2023 Datasets and Benchmarks. **Limitation:** preference agreement on general chat is not proof of correctness on code-review claims, and the identified biases remain relevant even with high agreement.
- **Calibration and realistic software evaluation are separate dimensions.** Confidence calibration means probability estimates representative of the true correctness likelihood. [On Calibration of Modern Neural Networks (Guo et al., 2017)](https://proceedings.mlr.press/v70/guo17a.html). **Evidence type:** peer-reviewed original empirical and methodology paper, ICML 2017. **Limitation:** its experiments concern classification, not generative code review or self-reported LLM confidence. SWE-bench supplies 2,294 real GitHub issues and corresponding pull requests from 12 Python repositories, requiring coordinated repository changes and long-context reasoning. [SWE-bench: Can Language Models Resolve Real-World GitHub Issues? (Jimenez et al., 2024)](https://arxiv.org/abs/2310.06770). **Evidence type:** original real-world software-engineering benchmark, ICLR 2024. **Limitation:** issue resolution is not defect detection during review, and its presence in public repositories also makes it unsuitable as an uncontaminated final test by default.

### Inferences

**The following metric plan is synthesis and recommendation, not a published standard.** Use the public benchmarks as diagnostics, but make frozen, real review tasks the deployment decision.

| Dimension | Operational metric for this A/B evaluation | Why it must remain separate |
|---|---|---|
| Instruction following | Strict prompt-level success (all required constraints satisfied), strict instruction-level accuracy, JSON/schema parse rate, required-section rate and forbidden-content violations. Keep loose matching only as a diagnostic. | A review can remain fluent and find real defects while dropping severity labels, evidence fields, requested lenses or output contracts that downstream consumers require. |
| Defect detection | Deduplicate findings within a run, then match them to independently adjudicated gold defects. `TP` is a gold defect matched at least once; `FN` is a gold defect missed; `FP` is an emitted finding not confirmed as valid. Report precision `TP/(TP+FP)`, recall `TP/(TP+FN)`, unsupported findings per task and per KLOC, plus macro-by-task and micro totals. | Recall alone rewards noisy reviewers; precision alone rewards terse reviewers. Per-task macro results prevent large patches from dominating, while micro results expose total defect burden. |
| Coverage | Report recall by specialist, defect class, severity, language, changed-file count and context-length stratum. Separately record required-lens execution rate and the proportion of applicable source files actually inspected through declared tool evidence. | Averages can hide the loss of one specialist or an entire defect class. Tool activity is process coverage, not proof of semantic coverage, so neither measure replaces the other. |
| Evidence fidelity | For every finding, verify that paths, symbols and line ranges exist and that the cited code, log or test supports the claim. Report supported-finding precision, fabricated-reference count and claim-level support. On the compressed artifact itself, measure retention of independently annotated oracle-critical evidence spans and contradictions introduced by compression. | A correct final verdict can occur for the wrong reason. Intermediate evidence retention localizes information loss that final task scores can miss by luck. |
| Calibration | If the pipeline emits probabilities, report Brier score, reliability curves and ECE with fixed bins chosen before testing. If confidence controls abstention or routing, also report risk-coverage curves and selective risk at the production coverage point. | Better average accuracy can coexist with dangerous overconfidence. Calibration becomes a release gate when confidence changes downstream behavior; otherwise it is secondary. |
| Multi-turn and long context | Score every turn, not only the last answer: instruction retention, earlier-defect carry-over, contradiction/staleness rate and follow-up correction success. Cross context-length bins with early/middle/late placement of critical evidence and with single-turn versus multi-turn tasks. | Compression can preserve the current diff while losing earlier constraints or evidence. Nominal context-window size does not demonstrate effective use of that context. |
| Independent verification | Measure raw reviewer precision/recall, verifier confirmation yield, false rejection of true findings, post-verification precision/recall and defects rescued only by verification. Give the verifier the original repository and candidate under a fixed budget, not merely the compressed summary. | A stronger verifier can conceal reviewer degradation or shift cost into extra verification. Pre/post measurements reveal that shift; original-source verification reduces shared-omission risk. |

### Gaps

- The cited public benchmarks do not provide a validated, universal code-review compression score or acceptance threshold.
- Real repositories rarely have complete defect ground truth. Known fixed defects, seeded defects and blindly adjudicated pooled findings measure different subsets and should be reported separately.
- Self-reported LLM confidence is not automatically a calibrated probability. It requires empirical validation on the same task distribution and elicitation method.

## How should baseline and compressed variants be compared: same model/candidate, held-out cases, repeated runs, variance, non-inferiority margins, and adjudication blind to variant?

### Takeaway

Use a paired, frozen A/B protocol in which the candidate patch and production configuration are identical and only the context-compression policy differs. Pre-register held-out tasks, repetitions, primary outcomes and margins; analyze paired task differences with uncertainty and keep adjudicators blind until scores are frozen.

### Cited Findings

- **The statistical test must match the task, experimental setup and measure.** Dror et al. present a protocol for selecting significance tests and document ignored or misused significance testing in NLP papers. [The Hitchhiker’s Guide to Testing Statistical Significance in Natural Language Processing (Dror et al., 2018)](https://aclanthology.org/P18-1128/). **Evidence type:** peer-reviewed opinion/theoretical methodology paper with an ACL/TACL survey, ACL 2018. **Limitation:** it does not supply a ready-made non-inferiority margin or a universal bootstrap procedure for stochastic multi-agent pipelines.
- **Non-inferiority requires a chosen margin and an explicit hypothesis, not failure to detect a difference.** FDA guidance describes when non-inferiority studies yield interpretable results, how to choose the margin and how to test the hypothesis. [Non-Inferiority Clinical Trials (U.S. FDA, 2016)](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/non-inferiority-clinical-trials). **Evidence type:** official final regulatory guidance, November 2016. **Limitation:** it concerns drug and biologic effectiveness, not software or LLMs. Its use here is analogical support for pre-specified margins and hypotheses, not for any numerical threshold proposed below.
- **Variant-visible adjudication can introduce measurement bias.** The LLM-judge methodology documents position, verbosity and self-enhancement biases and proposes mitigations. [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685). **Evidence type:** original evaluation-methodology paper with human-preference comparisons, NeurIPS 2023. **Limitation:** the paper does not establish that blinding alone makes an LLM judge a valid code-review oracle.

### Inferences

**The following experiment and numerical gates are synthesis and illustrative recommendations, not published facts or validated defaults.** Margins must be justified from business risk, baseline performance and pilot variance before the final test. A result whose confidence interval crosses a margin is inconclusive, not a pass.

1. **Freeze the protocol and isolate the final test.** Create development, validation/pilot and final-test partitions at repository level, with a time split where feasible. Tune compression only on development; estimate variance and finalize margins on validation; run the final test once. A practical planning target is 300 final held-out tasks with five paired repetitions per arm, but this is not a claim of adequate power. Increase `N` until a validation-only power analysis gives at least 90% power for the primary recall margin at one-sided alpha 0.05. If budget cannot support the required `N`, declare the affected gate underpowered.
2. **Pair everything except compression.** Use the same frozen reviewer model ID, candidate patch/repository SHA, specialist roster, tools, decoding settings, output caps, retry policy, time budget and seed schedule. The baseline receives production-full context; the variant receives the compressor's output. Any compressor model/call is part of the variant and is logged. “Same candidate” means the same patch under review, not reuse of the baseline's generated review. Execute five paired repetitions with randomized arm order and balanced infrastructure. Measure cold-cache and production-like warm-cache scenarios separately.
3. **Blind and independent adjudication.** Remove arm identifiers, token usage and costs from outputs; randomize left/right order. Pool unique findings from both arms plus independently known defects, then have two adjudicators with original-source access assess them independently, with a pre-defined tie-break process. Use deterministic parsers/tests where applicable. LLMs may assist, but final disputed labels require source-backed human adjudication; swap output order for LLM-assisted judgments. Freeze labels and scores before unblinding.
4. **Analyze paired tasks, not thousands of pseudo-independent findings.** Average each task's metric over its five runs, then compute paired task deltas and a two-sided 95% bootstrap CI by resampling tasks. Alternatively use a hierarchical bootstrap that resamples tasks first and runs within task second. Report between-task and within-task/run variance, all exclusions and all failed runs. For a higher-is-better metric with `Δ = compressed − baseline`, non-inferiority requires `CI_lower(Δ) > −δ`; for lower-is-better harm, require `CI_upper(Δ) < δ`. Do not interpret `p > 0.05` as equivalence.
5. **Require quality non-inferiority and end-to-end efficiency superiority.** The primary quality endpoint is final independently confirmed defect recall. Raw recall, false positives, instructions, evidence and critical strata remain gates so that verification cannot conceal degradation. Cost is evaluated only after all quality gates pass. Publish overall and pre-declared stratum results, including inconclusive intervals, rather than selecting a favorable aggregate.

**Illustrative acceptance protocol to finalize before unblinding:**

| Gate | Example measurable acceptance criterion |
|---|---|
| Primary final recall | Overall `CI_lower(Δrecall) > −2 percentage points`. No newly missed independently confirmed critical gold defect in any final-test run; still report the upper confidence bound because zero observed misses does not prove zero risk. |
| Raw detection and noise | Raw pre-verification recall `CI_lower(Δ) > −3 points`; final precision `CI_lower(Δ) > −2 points`; unsupported findings/task `CI_upper(Δ) < +0.10`. All use the same verification budget in both arms. |
| Instructions and evidence | Strict prompt-level instruction accuracy `CI_lower(Δ) > −1 point`; supported-evidence rate `CI_lower(Δ) > −1 point`; zero accepted fabricated file/line references. |
| Coverage and robustness | No required specialist lens is skipped. In every adequately powered critical specialist/severity/length/turn stratum, recall `CI_lower(Δ) > −5 points`; multi-turn task success `CI_lower(Δ) > −3 points`. Underpowered strata remain unvalidated. |
| Calibration and verification | When confidence drives routing/abstention, Brier-score increase `CI_upper(Δ) < 0.01` and selective risk at fixed coverage `CI_upper(Δ) < +2 points`. Verifier false rejection of true findings `CI_upper(Δ) < +1 point`. |
| Efficiency and completion | Mean production cost per attempted task is at least 15% lower, with the paired 95% CI for relative savings entirely above 10%; completion-rate `CI_lower(Δ) > −1 point`; p95 end-to-end latency increases no more than 10%. Report median and p95 cost/latency even when the gate uses mean cost. |

### Gaps

- No cited source establishes that 300 tasks, five runs or the example margins are sufficient for this pipeline. They are planning values only; pilot discordance and desired margins determine the real sample size.
- Same seeds reduce avoidable variation only when the provider supports them; they do not guarantee bitwise reproducibility or eliminate service-side nondeterminism.
- A fixed model ID and frozen candidate remove important confounders but cannot remove changing provider infrastructure, rate limits or shared-cache conditions. These need run metadata and sensitivity reporting.

## Why are word counts not token costs? How should input/output/cache-read/cache-write tokens, latency, retries and verification lenses be measured end-to-end?

### Takeaway

Words are not billing units, and visible prompt/output text is not the full API workload. Compute realized cost from per-call provider usage and a dated price snapshot across compression, every specialist, retries and verification, while reporting cache state and end-to-end latency explicitly.

### Cited Findings

- **Token counts differ from word counts and from visible text length.** OpenAI states that a token can be a character, part of a word, a whole word or punctuation; spaces matter; tokenization varies by model, encoding and language. It also states that reasoning tokens can be invisible yet billed as output, and that message structure, tools, schemas, images and files can affect complete input counts. [Understanding and counting tokens (OpenAI, living documentation, no fixed publication year; accessed 2026-10-26)](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them). **Evidence type:** official provider usage/tokenization documentation. **Limitation:** its rough English heuristics and field names are provider/model-specific and are not valid billing formulas for every vendor.
- **OpenAI cache categories require subtraction and component-level pricing.** The current prompt-caching guide says to track `response.usage`, cached reads and cache writes by lifetime. In its Responses API example, ordinary input equals `input_tokens − cached_tokens − cache_write_tokens`; TTL-specific write components sum to `cache_write_tokens`, so the aggregate must not be charged again. Cache reuse depends on the rendered prefix and relevant settings, not simply repeated words. [Prompt caching (OpenAI, living documentation, no fixed publication year; accessed 2026-10-26)](https://platform.openai.com/docs/guides/prompt-caching). **Evidence type:** official provider caching, usage-field and pricing documentation. **Limitation:** exact fields, TTLs, rates and cache behavior vary by endpoint/model and can change; the example must not be generalized blindly.
- **Anthropic uses a different usage decomposition and distinguishes estimates from billed usage.** Its caching guide defines `cache_creation_input_tokens`, `cache_read_input_tokens` and uncached `input_tokens`, with total processed input equal to their sum. It documents different cache-write/read price categories and TTLs. [Prompt caching (Anthropic, living documentation, no fixed publication year; accessed 2026-10-26)](https://platform.claude.com/docs/en/build-with-claude/prompt-caching). Its token-counting guide says pre-request counts can differ slightly from actual message creation and that tokenizer changes can change counts for identical text. [Token counting (Anthropic, living documentation, no fixed publication year; accessed 2026-10-26)](https://platform.claude.com/docs/en/build-with-claude/token-counting). **Evidence type:** official provider API and pricing documentation. **Limitation:** these semantics are Anthropic-specific; Bedrock or other hosted integrations can differ, and current prices must be captured at run time rather than copied from these notes.

### Inferences

**The following accounting design is synthesis and recommendation, not a provider-published evaluation standard.**

**Why words do not measure cost:** identical words can tokenize differently across models; code adds punctuation, whitespace and identifiers; invisible reasoning can be billed output; tools and schemas add input; cached reads and writes have different rates; compression adds its own calls; retries multiply work; and the variant can change output length. Word count may remain a descriptive size statistic, but it is not a cost endpoint.

**Log once per call and aggregate once per run:**

| Record | Required fields |
|---|---|
| Run identity | `run_id`, held-out `task_id`, arm, repetition, seed, candidate/repository SHA, model/provider IDs, prompt/compressor version, tool versions, cache scenario and price-snapshot timestamp. |
| Call accounting | `call_id`, stage (`compress`, named specialist, aggregator, verifier, retry), attempt number, provider request ID, start/end, time to first token, status/error and raw `usage` payload. |
| Token categories | Ordinary uncached input `U`, cached reads `R`, cache writes `W_ttl` separated by TTL, output `O` including provider-billed reasoning, plus actual billable tool/other charges. Preserve raw fields so provider-specific reconciliation is auditable. |
| Operational totals | API calls, retries, timeout/failure count, compression non-API compute cost, test/verification compute cost, queue/backoff time and wall-clock from task intake to final verified report. Parallel-call latencies must not be summed and labeled wall-clock. |
| Evaluation-only work | External adjudicator tokens/cost and human review time in a separate research ledger. Do not silently add experiment-only judging to production cost, and do not omit production verification merely because it is called “evaluation.” |

For each run, using per-token prices from the dated model/provider/region price snapshot:

```text
C_run = sum over calls [
          U * p_uncached_input
        + R * p_cache_read
        + sum over TTLs (W_ttl * p_cache_write_ttl)
        + O * p_output
        + actual other billable charges
      ]
      + non-API compression cost
      + non-API verification/test cost
```

Apply the provider's inclusion rules before using this formula. For the cited OpenAI Responses example, `U = input_tokens − cached_tokens − cache_write_tokens`; charge TTL write components once, not their aggregate again. For the cited Anthropic Messages usage, ordinary input is already separate and total processed input is `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`. Reconcile computed totals against provider usage/cost exports where available; flag missing usage from failed calls rather than inventing it.

Measure and report all of the following:

1. **Whole-pipeline cost:** compression calls, all specialists, aggregation, retries, production verification lenses and failed/abandoned attempts. Report cost per attempted task, per successfully completed task and, secondarily, per independently confirmed true finding.
2. **Cache realism:** separate cold-start and steady-state warm-cache experiments. Prevent cross-arm cache sharing, record actual hits/misses and TTL writes, and never assume a matching textual prefix produced a billed cache hit.
3. **Latency:** p50/p95 wall-clock, time to first token where relevant, API/service time, compression time, verifier time, queueing and retry backoff. Keep human adjudication latency out of production latency and report it separately.
4. **Reliability-adjusted efficiency:** completion rate, retry amplification (`actual calls / planned calls`), timeout rate and cost of unsuccessful runs. A cheaper average successful call is not cheaper end-to-end if it causes more retries or incomplete reviews.
5. **Reproducible prices:** preserve currency, unit, provider, model, region, pricing modifiers and retrieval timestamp. Recompute historical comparisons when prices change; do not rewrite the original realized-cost ledger.

### Gaps

- Provider documentation does not establish one cross-vendor usage schema. Other APIs and hosted integrations need their own field mapping and double-counting checks.
- Response usage may not determine the final invoice for every error, tool or background operation. Actual billing exports are needed for reconciliation; unknown failed-call charges should be disclosed.
- No fixed token-per-word conversion or current price is safe to embed in a durable protocol. Both must be measured for the selected model and run date.

## Which experiment designs are vulnerable to leakage, oracle contamination or cherry-picking?

### Takeaway

The most dangerous designs let the final test influence the compressor, give gold information to a production component, or select favorable runs/metrics after seeing results. Public benchmark scores and LLM-judge agreement cannot compensate for a leaky or selectively reported held-out test.

### Cited Findings

- **Benchmark exposure can inflate measured performance.** Sainz et al. define levels of contamination, identify training on the test split followed by evaluation on that split as the worst case, and state that contamination overestimates performance relative to non-contaminated counterparts. [NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark (Sainz et al., 2023)](https://aclanthology.org/2023.findings-emnlp.722/). **Evidence type:** peer-reviewed position paper, Findings of EMNLP 2023. **Limitation:** it argues for measurement and community action but does not prove that any particular private split is uncontaminated or supply a complete detector.
- **Automatic oracles can themselves be wrong.** IFEval's strict checks can misclassify acceptable formatting, while its loose transformations can introduce false positives; its prompts were generated, rephrased and manually edited. [Instruction-Following Evaluation for Large Language Models (Zhou et al., 2023)](https://arxiv.org/abs/2311.07911). **Evidence type:** original benchmark paper with explicit metric limitations. **Limitation:** deterministic checking is valuable only for constraints whose verifier has itself been tested; it does not validate semantic review correctness.
- **Shared or variant-visible judges are vulnerable to bias.** Position, verbosity and self-enhancement biases are documented in the LLM-judge methodology. [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685). **Evidence type:** original evaluation-methodology paper. **Limitation:** its mitigations do not guarantee valid labels for code, especially when the judge shares the compressor's missing context or model family.
- **Public and synthetic diagnostics are easy to overfit if reused as the final test.** LongBench is a public multi-task benchmark, while RULER deliberately provides configurable synthetic task generation. [LongBench: A Bilingual, Multitask Benchmark for Long Context Understanding (Bai et al., 2024)](https://aclanthology.org/2024.acl-long.172/); [RULER: What's the Real Context Size of Your Long-Context Language Models? (Hsieh et al., 2024)](https://arxiv.org/abs/2404.06654). **Evidence type:** original benchmark papers. **Limitation:** neither was designed to serve as an untouched deployment oracle after iterative compressor tuning.

### Inferences

**The following threat model and controls are synthesis and recommendation, not published facts.**

| Vulnerable design | How it distorts the A/B result | Required control |
|---|---|---|
| **Leakage through tuning, retrieval or state:** final tasks, near-duplicate patches or their reviews appear in compressor training, few-shot examples, prompt search, retrieval indexes, caches or earlier conversation state. | The variant has indirectly seen the test or its answer, so measured generalization is optimistic. | Split by repository and time; record provenance and near-duplicate exclusions; freeze retrieval indexes; prohibit final-test use in every tuning artifact; isolate memory/cache namespaces and clear conversational state between tasks. Private model pretraining exposure cannot be ruled out, so disclose it. |
| **Oracle contamination:** gold defect descriptions, expected findings, fix patches, hidden-test names or adjudication comments enter the compressor, reviewer or production verifier. | The system is evaluated on information unavailable in production, and the compressor can preferentially retain the answer. | Give production components only production-available inputs. Keep gold and adjudication in a separate enclave. Independent verifiers may use original source and tests but not the gold finding list; external adjudicators can use gold only under the frozen labeling protocol. |
| **Baseline-only or shared gold:** ground truth is built from baseline findings, or the same compressed context/model generates and judges the answer. | Compressed-only true findings become false positives; shared omissions become invisible; agreement is mistaken for correctness. | Build a blind pooled union of findings from both arms plus independent known defects; adjudicate unique issues against original evidence; use deterministic tests/static checks where applicable and independent humans for disputes. Report unresolved and inter-adjudicator disagreement. |
| **Cherry-picking and pseudoreplication:** select the best of repeated runs, discard timeouts, tune margins/strata after inspection, repeatedly peek at the final test, or treat findings/runs as independent tasks. | Variance is understated and the reported arm looks better than the pre-specified procedure. | Pre-register seeds, repetitions, exclusions, primary endpoint, margins and analysis; include failed runs in completion and cost outcomes; retain every run in an immutable ledger; resample at task level; label additional analyses exploratory and correct or disclose multiplicity. |
| **Biased efficiency and adjudication presentation:** only the compressed arm gets a warm cache, compression/retry/verifier calls are omitted, or judges can infer arm from order, verbosity and formatting. | Token savings and quality preferences reflect experimental artifacts rather than the intervention. | Balance execution order/infrastructure, run separate cold/warm scenarios, count all production calls, normalize output presentation where possible, randomize and swap judge order, and conceal cost/token metadata until labels are frozen. |

Use IFEval/RULER-style probes as secondary diagnostics with fresh configurations, not as the sole final oracle. The deployment claim should rest on real, frozen, held-out candidate patches and end-to-end pipeline behavior.

### Gaps

- With undisclosed proprietary-model training data, contamination cannot be proved absent. New private tasks, repository/time isolation and provenance checks reduce risk but do not eliminate it.
- Tests and static analyzers are incomplete oracles for design, maintainability and some security findings. Human source-backed adjudication remains necessary, with its own subjectivity and disagreement reported.
- Blinding reduces variant recognition but does not guarantee it: writing style or formatting can reveal the arm. A post-hoc judge guessing check can measure apparent leakage, but it is not proof of perfect blinding.
