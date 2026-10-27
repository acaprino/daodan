# Julia Boolean criteria ablation

User authorization: `ok fallo`, following the proposal to compare explicit Boolean criteria on fresh compaction cases. This is a bounded local CPU experiment. The cancelled Gutsy campaign and completed Julia pilot remain unchanged. No training, installation, cloud inference, production integration, commit or push.

## Question and design

Does adding descriptive `false`/`true` criteria improve Julia's compaction decisions on new synthetic scenarios? This experiment isolates that change. It does not also rewrite the question, optimize batches, change weights or tune thresholds.

Thirty-two new scenarios in eight families, four per family, with two English and two Italian states per family. Families: unique unrecoverable evidence, duplicates, superseded evidence, irrelevant output, recoverable immutable sources, nonrepeatable actions, useful negative evidence and quoted adversarial text. Cases are authored without inspecting Julia's previous response records. Related cases and translations are not independent real-world samples. No real messages or side effects are executed.

Each scenario uses one old candidate tool pair, six neutral messages to move it outside the pinned window, and optional pinned recent evidence. The actual pinned fast-jev dependency generates questions, prepares the state and reconstructs the compacted transcript. Both variants receive candidate output contents (the evidence-visible B representation from the previous pilot). Both receive the same context statement: minimize unnecessary retention while preserving the active task; rereading is available only when explicitly established by the history; dropping only a result retains its first 300 characters, while dropping the call removes the pair. Upstream's blanket claim that tools can always be rerun is inappropriate for these scenarios. These are adapter choices shared by both variants, not evidence about stock upstream accuracy.

- `literal`: original upstream questions, with no Boolean criteria (runtime uses literal false/true).
- `descriptive`: identical state and question text, with the following fixed descriptions.

Call criteria:

```json
{"false":"The record of this operation and its inputs is no longer needed to continue the active task correctly.","true":"The operation and its inputs must remain recorded to continue correctly, avoid repeating a side effect, or identify a necessary source."}
```

Result criteria:

```json
{"false":"The full output is unnecessary: useful facts survive in the retained prefix, are duplicated, superseded, irrelevant, or safely recoverable from an explicitly available source.","true":"The full output contains necessary facts absent from the retained prefix and other available evidence, and these facts cannot be safely and exactly recovered elsewhere."}
```

Criteria are English in both languages, as are the unchanged upstream instructions. This is not a full Italian-localization experiment. Only `criteria` differs between paired requests. Neither labels, rationale, family, criticality, required tokens nor case ID enters the model payload. State facts may legitimately explain availability, duplication or the next action. No answer-specific hints are added after results are observed.

All cases, inputs, question order, private labels, descriptions, source hashes and schedule are frozen before inference. Case order is deterministically shuffled with seed 20261027; which variant runs first alternates across scheduled cases. Both variants have exactly the same within-case question order. Clear encoding caches before each timed request, keeping resident model weights; timing includes tokenization and extra description tokens. No generation or cached-answer shortcut. Batch size one, four CPU threads, FP32, official Torch backend, optimized CPU head, strict encoding, maximum 1024 combined tokens and head budget 512. Overflow is coverage loss, never a false answer: if either variant fails strict encoding, exclude both requests from paired inference and quality comparisons and report the rejected pair. A disjoint warm-up has no oracle and is excluded from measured requests.

## Frozen scoring and interpretation

Primary outcome: accuracy of the `result_t1` decision at fixed probability threshold 0.5, against independently authored `result_required` labels. Report paired improvements/regressions, confusion counts, balanced accuracy, recall of required outputs and unnecessary retention of dispensable outputs. Call answers have no human oracle in this experiment; show their decisions but do not invent call accuracy. Factual preservation alone cannot establish an exact Boolean decision, because truncation or pinned duplicates can preserve facts independently.

Replay actual fast-jev reconstruction on every accepted response. Report loss of required tokens in raw compacted messages, critical losses, per-family and per-language results, actions, transcript invariants and byte savings. Fixed tokens are a synthetic factual-survival check, not downstream LLM task accuracy. For immutable recoverable cases, report raw losses separately from the deterministic verified-recovery outcome; do not credit recovery to Julia. No guardrail forces model answers in either arm. Never pool 64 requests as 64 independent scenarios. Families and language subsets are diagnostics, not significance claims or tuning sets. Do not fit a new threshold.

An improvement of at least 10 percentage points in result accuracy with no increase in critical factual losses is a promising follow-up signal only. Any critical raw factual loss prevents a claim of safe autonomous compaction. The operational targets remain combined sampled RSS <=1 GiB and warm whole-request latency <=1 second. Neither quality nor performance targets are completion gates for reporting a valid negative experiment. No automatic expansion, model adoption or rerun follows the outcome.

## Limits and completion

64 measured requests, 128 measured question evaluations, plus at most eight disjoint warm-up/parity evaluations. Max 600 seconds including model loading; max 45 seconds for one request; sampled combined RSS stop at 2 GiB. A parent watchdog polls every 100 ms. This is a sampled process guard, not an OS memory cap; shared pages can be counted twice. Stop records partial coverage explicitly, without silently retrying.

Completion requires: independent preflight review of exact cases/protocol/code; manifest/source/input/model validation; bounded execution with raw responses and resource ledger; deterministic scoring using pinned upstream code; independent replay of scoring and verification of report claims. Store operational evidence in `.daodan/runs/2026-10-27-julia-criteria-ablation/` and the human report in `docs/gutsay/`. Scope is limited to this experiment's new directory and new report.
