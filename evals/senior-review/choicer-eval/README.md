# Offline Choicer pilot

This development asset compares the section 3.6 `REVIEWER_CHOICER` prompt with
Julia-1 on the existing senior-review cases. It does not change any plugin,
installed routing, task cycle or marketplace dependency. The optional task-tier
experiment and secondary laya inference are not implemented.

The original evidence is in `runs/20261020T100258Z/`; the separately authorized
adapted experiment is in `runs/20261020T100258Z-adapted/`. `RESULTS.md` compares
both and links their detailed reports. Preparation and scoring never authorize
new downloads, environments or paid calls.

The [follow-up usage diagnosis](DIAGNOSIS.md) tests presentation, option wording,
runtime parity, fresh code controls and a small published Boolean sample.
Its evidence is under `runs/20261020T-diagnostic/`. These are adaptive development
probes, not a replacement accuracy benchmark. Regenerate that report with
`python -B evals/senior-review/choicer-eval/summarize_diagnosis.py`.

The [gutsy benchmark](GUTSY_RESULTS.md) separately evaluates
`kouhxp/gutsy` (`gutsy-0.8b-v04`, Q8_0 GGUF) on the same fresh controls,
team problems and transformed `C01..C11` inputs, through a custom PyTorch backend
(`probe_gutsy.py`, `run_gutsy_benchmark.py`) into
`runs/20261020T100258Z/gutsy-comparison.json`. It was separately authorized
(model download authorization) and changes no plugin or routing implementation.
Runtime parity, lossless input binding and production thresholds are not
established by that experiment. Read the corrected report before interpreting
its scores; the saved suite runner is not a certified offline-only replay tool.

The [CPU input/question follow-up](QUESTION_REFINEMENT.md) tests lossless file
windows on C01/C07 and one frozen prompt candidate on eight additional real-source
functions with development/verification partitions. It uses the existing Q4_K_M
llama-server installation without Python ML dependencies. See the Gutsy section in
[RESULTS.md](RESULTS.md) for corrections to the earlier V2 claims about automatic
map grounding, calibrated scores, citations and memory. The follow-up records exact
wire payloads and enforces a sampled memory stop; its execution record owns success.
Its slot-restore mode encodes each state once and restores the saved server slot
before every question; `compare` pairs each answer with a full re-encoding run of
the same frozen jobs under a rule fixed before inference.

The [all-reviewer follow-up](ALL_REVIEWERS_RESULTS.md) covers 22 registered review
lenses individually and in teams: 132 balanced applicability controls and 12
complete problems. It inventories all 44 registered roles and explains each
inclusion or exclusion. The document-structure editor is included explicitly as
an audit-capable hybrid. This evaluates selector routing, not execution of the
reviewer agents.

`all-reviewers/` holds authored fixtures, source hashes and independent reviews.
`runs/20261020T-all-reviewers/` preserves the frozen suite, requests, submitted
payloads and outputs. The new grounded criteria were checked before inference;
no thresholds or labels are tuned against predictions. Required and acceptable
optional team members are scored separately. Every team asks all 22 binary
questions; binary `choice` does not restrict a team to one reviewer.

Use ordinary Python for `all_reviewers_eval.py prepare` and `report`. The
`capacity` and `run` actions require the previously provisioned interpreter below
`.cache/uv/environments-v2/`; they load cached files offline and do not provision
another environment. `capacity` loads only the tokenizer. `run --resume` retains
existing outputs and runs missing requests only. Scoring is reproducible without
model inference:

```powershell
python -B evals/senior-review/choicer-eval/all_reviewers_eval.py report
```

## Start with ordinary Python

Run from the Daodan checkout. Python 3.11 or later is required. These commands
need only the standard library and do not create a uv environment:

```powershell
$evalScript = 'D:\Projects\daodan\evals\senior-review\choicer-eval\run_eval.py'
$evalRun = 'runs/20261020T100258Z'
python -B $evalScript extract-catalog --run-dir $evalRun
python -B $evalScript materialize-cases --run-dir $evalRun --jupiter-root 'D:\Projects\jupiter'
python -B $evalScript run --run-dir $evalRun --impl llm --variant noul --prepare-only
python -B $evalScript run --run-dir $evalRun --impl julia --variant noul --prepare-only
python -B $evalScript run --run-dir $evalRun --impl julia --variant choice --prepare-only
python -B $evalScript score --run-dir $evalRun
python -B $evalScript report --run-dir $evalRun
```

Use a new UTC timestamp directory for a new experiment. Source inputs and request
files are frozen: changed content cannot overwrite them. Scoring never calls a
model. The script confines every output path to this benchmark directory,
including symlink resolution. Source repositories are read with `git show` and
`git diff`; no checkout or scratch Git repository is created.

## Authorization gates

Before creating a uv environment or downloading weights, obtain explicit approval
for the paths and footprint. All caches and the isolated uv script environment
belong below `choicer-eval/.cache/`. The pinned upstream metadata reports:

| Item | Download bytes | Interpretation |
|---|---:|---|
| Julia FP32 weights | 577189056 | 550.45 MiB; downloaded and hash-verified in this authorized run |
| Julia tokenizer | 34363188 | Required in addition to weights |
| Complete Julia repository | 612712253 | Upper source-snapshot reference; not installed size |
| Torch Windows CPython 3.13 wheel | 124113865 | One direct dependency, compressed wheel |
| Transformers wheel | 10142091 | One direct dependency, compressed wheel |

Other dependencies, extraction and cache duplication add space. Complete download
and installed size are unknown until resolution and measurement. Small official
source/metadata reads under `runs/.../upstream/` are evidence, not provisioning.
The Python packages are declared only in the script's PEP 723 header.

Only after explicit environment and download approval:

```powershell
$evalRoot = 'D:\Projects\daodan\evals\senior-review\choicer-eval'
$env:UV_CACHE_DIR = "$evalRoot\.cache\uv"
$env:UV_PYTHON_INSTALL_DIR = "$evalRoot\.cache\python"
$env:TMP = "$evalRoot\.cache\tmp"
$env:TEMP = "$evalRoot\.cache\tmp"
New-Item -ItemType Directory -Force -Path $env:TMP | Out-Null
uv run --no-config --no-project --no-python-downloads --script "$evalRoot\run_eval.py" run --run-dir $evalRun --impl julia --variant noul --batch-size 1 --require-complete-catalog --allow-download
uv run --no-config --no-project --no-python-downloads --script "$evalRoot\run_eval.py" run --run-dir $evalRun --impl julia --variant choice --batch-size 1 --require-complete-catalog
```

The second command uses cached model files only. Both use CPU, FP32, four Torch
threads, strict encoding and the full decision head. Model/revision, weight hash,
runtime versions, actual thread count and load costs are recorded. Default cache
locations outside the benchmark are overridden before importing the runtime.
An ordinary Python invocation with an already provisioned runtime also works.
Do not run these commands simply to discover whether provisioning is necessary:
uv resolves the script dependencies before Python can evaluate its flags.

The original execution began with batch size 16 and resumed with batch size 1
after measured memory pressure. Use `--resume` only to continue a local run
with its existing hash-bound outputs; completed records are never overwritten.
Runtime segments and interruption evidence remain separate. This operational
change does not alter questions, thresholds, model precision or source hunks,
but it prevents treating all timings as one controlled configuration.
`--require-complete-catalog` checks every question before classification and
rejects the entire batch when any question cannot be encoded losslessly.
Historical partial classifications remain diagnostics; later atomic rejections
record `inference_performed=false`. Validation time is not inference speed.
Actual model submissions are preserved under `wire/`, separately from the
complete requested question set under `requests/`.
The 23 historical partial submissions predate wire capture. Their exact valid
question subsets are reconstructed under `execution/historical-model-inputs/`
with source hashes, encoding evidence and corroborating raw answer IDs; they
are explicitly labeled reconstructions rather than contemporaneous captures.

The optional `--impl laya` selector fails explicitly. Upstream's 324 MB refers
to an INT8 build output, not a verified complete download. No fallback or
unreviewed laya installation is performed.

## LLM baseline

Before paid inference, disclose the actual model, planned number of calls and
estimated input tokens and obtain approval. `plans/llm-noul.json` records that
estimate; `characters / 4` is only a planning heuristic. Provider usage is
recorded separately and remains unknown when not reported.

The baseline sends one full-review request per case. It fills only the declared
placeholders of the verbatim spec prompt and supplies the same hunk IDs, source,
symbol cards and parsed catalog as Julia. `noul` labels the multilabel experiment;
it does not imply that the unchanged LLM prompt emits probabilities.
One measured A baseline is compared with both Julia variants. `llm/choice` is
rejected because the required prompt selects all applicable reviewers and cannot
be made into a single-choice control without changing it.

There are two execution paths:

1. The active host can run each saved `requests/llm/noul/Cxx-batch.json` prompt
   in a fresh context without case files, evaluator labels or this chat history.
   Save the provider/host output in a capture file with the same name.
2. With an explicitly authorized OpenAI API model and an existing
   `OPENAI_API_KEY`, use `run --impl llm --variant noul --model MODEL
   --allow-paid-llm`. The script sends the exact prompt to the Responses API,
   records the wire request and raw response, and makes no automatic retries.
   A session model name is not assumed to be available through the API.

For host-native captures:

```json
{
  "request_sha256": "copy from the corresponding frozen request",
  "response": {"mode": "full", "selected": [], "recommend_full_review": false, "recommend_full_reason": null},
  "model": {"provider": "provider actually used", "requested": "requested model", "reported": null},
  "usage": null,
  "wall_seconds": null,
  "cpu_seconds": null,
  "phase": "unknown"
}
```

Use null for unavailable metadata. Preserve the full provider response alongside
the capture when available. Do not fill unknown timing, CPU or token usage with
estimates. Then import without a paid call:

```powershell
python -B $evalScript run --run-dir $evalRun --impl llm --variant noul --responses "$evalRoot\runs\20261020T100258Z\captures"
python -B $evalScript report --run-dir $evalRun
```

The importer checks the request digest, role IDs, valid tiers, concise reasons,
and exact hunk/file/line/snippet citations. A syntactically valid but unsupported
answer is saved as an error. A saved output is never silently replaced.

## Corpus and leakage boundary

`catalog.json` contains all 44 role frontmatters, raw descriptions, exact parsed
trigger spans, file hashes and plugin versions. Its reviewer subset consists of
the 18 lenses in `plugins/daodan/workflows/review-branch.toml`, excluding that
workflow's two codebase-map evidence producers. Writers, map producers and
protocol workers are retained in the inventory but are not reviewer candidates.

Three reviewer roles have no `DO NOT TRIGGER WHEN`: platform-reviewer,
distributed-flow-auditor and ui-race-auditor. Their parsed negative criterion is
null; the request records an empty string, never an invented opposite. Julia's
strict input contract rejects an empty rendered criterion. Those questions must
therefore be recorded as unsupported, and a partial hunk or case cannot count
as a complete comparison. This is an input-contract limitation discovered before
inference, not a measured classification failure.

Julia also limits each option to 48 tokenizer tokens and has a separate decision
head budget. `strict_encoding=True` and per-question `encoding_info` reject
truncation. Long exact triggers, the 18-option choice control or long source
hunks may be unsupported. Successful answers from supported questions are kept
for inspection, but no shorter trigger, windowing, inferred negative or smaller
catalog is substituted silently.

Hunk splitting is fixed before any inference:

- For five fix-history cases, use the old side of each `git diff -U3` block
  between the review and fix revisions, restricted to the case's declared
  paths. Retain context and removed lines only. The fixed code is never shown.
- For updater, use the new side of the explicitly allowed review-commit diff
  `936ba644~1..936ba644`, including that diff's docs, tests and configuration.
- Each synthetic source fence is one contiguous introduced block. The payment
  case's companion model has no supplied source; that context remains missing.
- Credential-refill has no diff. Read its two complete heartbeat and
  auto-registration modules at the stated revision. Split at complete Python
  declarations/class methods, attaching all intervening source to adjacent
  declarations. No methods are selected using the precision oracle.

Hunks are numbered H1..Hn independently within each case. C01..C11 are assigned
by sorted directory name. Original source coordinates, blobs, revisions, hashes,
scope choices and omissions are retained in scorer-side `dataset.json`. Every
historical hunk is checked against the reviewed blob. Retrospective localization
through a future fix is a sampling limitation, not prospective routing evidence.
No case supplies symbol cards; none are fabricated.

Only opaque case ID, hunk ID, source path, source line coordinates, source text
and any actually supplied symbol cards enter requests. Titles, expected roles,
ground-truth tables and scoring notes stay in evaluator files. Never give those
files or the evaluator session history to an LLM inference worker.

## Dimension mapping

| Expected dimension | Role |
|---|---|
| architecture | senior-review:code-auditor |
| data-integrity | senior-review:data-integrity-auditor |
| distributed-flow | senior-review:distributed-flow-auditor |
| documentation, hygiene | senior-review:cleanup-auditor |
| logic-integrity | senior-review:logic-integrity-auditor |
| premise | senior-review:premise-auditor |
| resource, resource-lifecycle | senior-review:resource-lifecycle-auditor |
| security | senior-review:security-auditor |
| temporal, temporal-resilience | senior-review:temporal-resilience-auditor |
| ui | senior-review:ui-race-auditor |

`dataset.json` records the method-table and role-body provenance for this mapping.
There are 10 labeled cases, one unlabeled precision case and no positive premise
label. Undefined premise recall cannot satisfy the complete critical-role gate.

## Metrics and threshold protocol

The noul threshold is fixed a priori at **0.5**, inclusive. A role activates if
any hunk crosses it. Case probability is the maximum hunk probability. The
threshold curve is descriptive and never selects a winning threshold.
Categorical choice uses one argmax per hunk, then unions the selected roles.

- Recall is the number of expected case-role pairs selected divided by expected
  pairs. Security, premise and data-integrity also have separate recall and
  false-negative counts.
- False activations are selections outside the case's expected set, reported
  per labeled case. These labels describe known defects, not every relevant
  review trigger, so the number is benchmark excess rather than proved wasted
  reviewer work.
- Reliability uses ten bins and one observation per labeled case-role pair.
  ECE weights each bin's absolute probability/frequency gap by observation
  count. Absent dimensions are proxy negatives. Unchanged LLM output contains
  no probabilities, so its ECE is unavailable. Categorical choice probabilities
  do not stand in for independent binary relevance probabilities.
- Agreement is exact set equality and Jaccard overlap on complete paired cases.
  Unlabeled credential-refill contributes here only.
- Latency is wall clock and process CPU for each attempted call, summed by
  case. The first inference in a fresh process is cold; subsequent calls are
  warm. Model load/provisioning is separate. OS disk caches are not flushed.
  No unmeasured cold or warm repetition is implied.
- Missing/failed/partial/duplicate records do not become negative predictions.
  Compare only paired complete cases and show coverage denominators.

Tokens saved by finer downstream routing and routing-error costs are unknown
without actual reviewer/retry outcomes. The pilot cannot prove a positive net
token balance or promotion. Its only prospective decision is whether evidence
supports opening Decision Log shadow observation.

## Evidence and verification

`prompts.json`, `catalog.json` and `dataset.json` freeze source evidence.
`requests/` contains every frozen requested input; `wire/` and the explicitly
labeled historical reconstructions record what was actually submitted.
`results/` contains every available raw
output and normalized decision, `scores.json` the reproducible metrics,
`metadata.json` identities/environment/gates, and `upstream/` bounded official
metadata plus a source-level API contract check. A contract check with mocked
logits is explicitly not a real inference result.

The executed A baseline consists of 11 isolated native Codex subagent tasks
with an accepted `gpt-6-luna`, low-effort override and no parent history. Each
task reads only its frozen request. `captures/Cxx-batch.json` preserves the exact
loader instruction, returned response and request digest. This transport adds
a file-loading instruction and the host's own system/tool context; it is not a
bare one-message API request. The host exposes neither provider-reported model
identity, token counts, API call counts, finish reasons nor inference timing.
Those values remain unknown. A returned final answer that a worker failed to
write was saved unchanged by the coordinator.

The frozen prompt asks for a base/candidate citation marker, but the supplied
hunk text omits that binding. Validation checks the hunk, path, line and quoted
text and records the unverified marker as a warning. Passing these limited
checks is not proof of full evidence-contract compliance. Invalid citations
and reasons exceeding the prompt's 15-word maximum remain failed outputs;
raw declared role sets are reported separately without repairing predictions
or counting them as validated baseline results.

Scoring rechecks each stored input digest against its run's dataset, catalog
and prompt before accepting a normalized record. Results from another catalog
cannot be imported merely because their reviewer IDs match.
`run_eval.py report` writes only that run's `RESULTS.md`; the combined report
has one writer, `summarize_runs.py`.

## Separate adapted experiment

The original strings and results stay frozen. After the user authorized
adaptation, an independent author with no case, label or prediction access
produced [adapted_reviewers.json](adapted_reviewers.json). All 18 roles remain,
including three explicitly authored missing negatives. Security, premise and
logic also receive documented policy changes from the frozen LLM prompt; this
is not equivalent compression. Compact `choice_description` strings are
separate from the binary criteria. The tokenizer-only checks and exact source
hashes are in [adapted_reviewers_audit.json](adapted_reviewers_audit.json).

The adapted run excludes a whole case when any original state already exceeds
8192 tokens. The tokenizer-only audit identifies C02 and C07, leaving nine
cases and 41 unchanged hunks. This rule was fixed before adapted inference and
does not depend on labels or predictions. It does not establish support for
large cases. All remaining questions still undergo strict lossless encoding.

```powershell
python -B evals/senior-review/choicer-eval/prepare_adapted.py `
  --source-run runs/20261020T100258Z `
  --run-dir runs/20261020T100258Z-adapted
```

Run Julia's `noul` and `choice` variants against that run directory using the
same authorized environment and cached model as above. Keep threshold 0.5;
do not copy original LLM outputs into the adapted run. There are no additional
paid baseline calls. Comparing adapted Julia with original A is explicitly an
exploratory comparison across different criteria, not an isolated model effect.
No kernel or installed reviewer description changes.

After all original and adapted attempts are recorded, regenerate the combined
report and its linked detailed reports without model calls:

```powershell
python -B evals/senior-review/choicer-eval/summarize_runs.py `
  --original runs/20261020T100258Z `
  --adapted runs/20261020T100258Z-adapted
```

Run the standard-library regressions without installing anything:

```powershell
python -B -m unittest discover -s evals/senior-review/choicer-eval -p 'test_*.py' -v
```
