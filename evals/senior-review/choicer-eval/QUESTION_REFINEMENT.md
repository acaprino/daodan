# Improving Gutsy questions with real source examples

## Decision and scope

Question refinement remains worthwhile. The eleven historical cases should become
regression examples, not the only material used to optimize wording. The first
follow-up separates an input-packing change from a prompt change and retains both
positive and negative judgments. No routing specification or production component
is changed by this experiment.

## Two separate experiments

### Historical input ablation

C01 and C07 retain their original hunks, V2 question strings and handwritten V2
module context. The two arms use the same exact-letter activation policy:

- **Truncated:** the previous first-hunks, 350-characters-per-hunk representation.
- **Windowed:** all supplied hunk text, partitioned by file into windows containing
  at most 2,800 source characters. Larger functions can span windows; every byte
  of decoded source text is accounted for with hunk-relative character offsets.

Eight independent binary questions are asked per window; case selections are the
union. The generalist and historical TS/React filename rules are reported
separately. No automatic cleanup rule is introduced for mixed documentation/code
changes. More windows can increase both recall and excess activations, so neither
recall alone nor a file count settles the decision.

This tests full coverage of the supplied snippets, not full source understanding.
The original historical sampling used fix locations retrospectively. File-scoped
windows can lose cross-file contracts, and their union cannot recover an omitted
caller or interpret a relationship that no individual window establishes.

### Question comparison on additional source

The candidate uses direct questions about behavior and explicit non-triggers.
V2 and candidate receive identical complete source windows. Both use a `Z` reject
option. The candidate changes both question wording and the Yes/No option text;
the experiment measures this joint prompt treatment, not each word's causal effect.

All eight examples are extracted from Jupiter revision
`936ba644e2cee4680be1d2c29c7aadfbfb86e1bf`. They are actual source functions, not
newly reproduced bugs. Labels ask which perspective is applicable to the shown
code; a correct implementation can still warrant specialist review after a change.

| ID | Partition | Source scenario | Positive perspectives | Explicit negative controls |
| --- | --- | --- | --- | --- |
| E01 | Development | Account visibility filtering by scopes | Security, logic | Local sets do not imply persistence; no resource acquisition or UI |
| E02 | Development | Async cache get/set and TTL | Data integrity | No credentials, UI or acquired resources |
| E03 | Development | Publish/ACK correlation with bounded timeout retries | Temporal, distributed, logic | No storage or UI |
| E04 | Development | Datetime-to-Unix conversion | No required specialist label | A timestamp alone is not a scheduler, transport or resource lifecycle |
| E05 | Verification | Circuit-breaker admission and bounded probe-slot release | Temporal, logic, resource | No storage or UI |
| E06 | Verification | SHA-256-derived deterministic agent identifier | No required specialist label | Hashing alone does not imply authentication; no messaging is implemented here |
| E07 | Verification | Instrumented async lock and context-manager release | Resource | Local metrics do not imply database writes, messaging or UI |
| E08 | Verification | Masking sensitive values in log strings | Security | A connection string is not an acquired connection |

Expected labels and rationales live in `cases.json`, separate from model-facing
jobs. The requests carry opaque IDs, source paths/ranges/code and frozen questions.
Verification files differ from development files. The same coordinator selected
the snippets, authored judgments and designed prompts before viewing predictions;
this is not independently blinded labeling. All examples come from one project.
UI and cleanup positives, premise, startup, API contracts and additional specialist
roles remain outside the new-case coverage.

## Useful refinement directions

1. **Ask about review scope rather than asking the small model to prove a bug.**
   Security routing should recognize credential redaction even when it is correct.
   Cleanup's candidate still asks for visible evidence of obsolescence; this is a
   deliberately conservative hypothesis, not a complete applicability contract.
2. **Describe ownership and data flow, not isolated keywords.** A cache is a copy
   of authoritative state; not every dictionary is a cache. A string containing a
   database URL is not a live database connection. Explicit contrast examples test
   whether those distinctions improve selection.
3. **Preserve multiple lenses.** An ACK protocol may need both distributed and
   temporal review. Exclusive choice among those roles can suppress a necessary
   lens before it is scored.
4. **Keep abstention separate.** Missing top-k probabilities are unknown. Invalid
   output is failed coverage. `Z` is not `No`, and it never manufactures a citation.
5. **Keep source-grounding and question tests separate.** Authentic map cards need
   their source revision, symbol identity, edge provenance and freshness. The V2
   handwritten context cannot establish a map-integration result.

These eight formulations are an experimental adaptation of eight reviewer lenses,
not a lossless encoding of the full reviewer catalog. Workflow prerequisites and
role exclusions still belong to their canonical owners. No new production trigger
is approved by a successful local prediction.

## Evaluation and next iteration

Freeze the prompts, input rules, applicability judgments and partition before
inference. Score required-role recall, activation of explicitly negative roles,
abstention, model-versus-fixed selections, input coverage, calls, latency and memory.
Do not interpret every unlisted role as negative. Do not use a verification failure
to edit the prompt and then call that same set an unseen verification set.

After inspecting this run, move any verification example used for tuning into the
development pool. Acquire fresh source files or separate projects for the next
verification partition. Add independently adjudicated applicability labels and
actual downstream review outcomes before claiming routing quality. Bug recall,
role applicability, citation relevance and tier assignment are different targets.

Threshold fitting needs a labeled calibration split and option-normalized scores
with complete token identity. The present experiment deliberately uses exact `A`
activation; uncalibrated vocabulary probabilities remain diagnostic data only.
No fine-tuning, new model, model download or paid cloud baseline is part of this run.

## Runtime evidence and reproducibility

`gutsy_followup.py` uses the already available Windows CPU llama-server and Q4_K_M
model. It records model and binary hashes, exact requests/responses, prompt token
counts, server cache/timing fields and working-set samples for both owned processes.
The sampler terminates the server when their combined resident set reaches
1,000,000,000 bytes. This is a sampled watchdog, not an OS-enforced hard limit;
brief overshoot is possible. Host memory and OS caches are not included.

The first execution with the previous batch defaults exceeded that memory bound
before delivering a prediction. Batch 128 / microbatch 64 with additional RAM
prompt cache disabled also exceeded it after one delivered prediction. Those
attempts are retained in `runs/20261020-gutsy-followup/` and
`runs/20261020-gutsy-followup-bounded/`. Their failures must not be counted as model
negatives. Batch 32, microbatch 32 and one context checkpoint with a 4,096-token
context delivered 202 valid calls, then reached the bound (sampled peak 1,000,206,336
bytes) and is retained in `runs/20261020-gutsy-followup-smallbatch/`. Reducing the
allocated context to 1,536 tokens, above the largest measured prompt of 1,110 tokens,
completed all 496 calls in `runs/20261020-gutsy-followup-ctx1536/`. The answers and
exact probabilities of the 202 jobs shared by both executions are identical.

## Observed results (`runs/20261020-gutsy-followup-ctx1536/`)

All 496 planned calls returned a valid letter; there were no abstentions, invalid
outputs or truncations. `verify_gutsy_followup.py --complete` passed: frozen hashes,
61 source hunks against Git, prompts, generated token identities, score consistency
and memory. Sampled peak combined resident set: 977,641,472 bytes (server 924,270,592).
Wall time: 1,995 seconds, of which C07's 312 windowed calls took 1,387 seconds.

Historical input ablation, identical V2 questions and handwritten context:

| Case | Input | Calls | Expected found | Missing | Model selections without a label |
| --- | --- | --- | --- | --- | --- |
| C01 | Truncated | 8 | 0/2 | data-integrity, temporal | distributed, logic |
| C01 | Complete windows | 24 | 1/2 | data-integrity | distributed, logic |
| C07 | Truncated | 8 | 3/5 | cleanup, ui-race | none |
| C07 | Complete windows | 312 | 4/5 | cleanup | distributed, security |

Expected counts include the fixed `code-auditor` rule. On truncated input C07
recovered code, logic and temporal; complete windows added ui-race. On C07 the model
activated temporal in 39/39 windows, logic in 31/39 and ui-race in 24/39: a union
across many windows rewards permissive answers. Cleanup was never activated.

Question comparison on identical complete windows:

| Case | Split | V2 expected / negatives activated | Candidate expected / negatives activated |
| --- | --- | --- | --- |
| E01 account scope filter | Development | 0/2, 0/3 | 0/2, 0/3 |
| E02 cache get/set | Development | 0/1, 0/3 | 1/1, 0/3 |
| E03 ACK with retries | Development | 1/3, 0/2 | 2/3, 0/2 |
| E04 datetime conversion | Development | no positives, 0/6 | no positives, 0/6 |
| E05 circuit breaker | Verification | 3/3, 0/2 | 2/3, 0/2 |
| E06 deterministic ID | Verification | no positives, 0/6 | no positives, 0/6 |
| E07 instrumented lock | Verification | 0/1, 0/4 | 1/1, 0/4 |
| E08 log redaction | Verification | 1/1, 0/4 | 1/1, 0/4 |
| **Total** | | **5/11, 0/30** | **7/11, 0/30** |

Verification alone: V2 4/5, candidate 4/5. The candidate fixed the lock lens (E07)
and lost temporal on the circuit breaker (E05). Development alone: V2 1/6,
candidate 3/6. No explicitly negative perspective was activated by either variant.
V2 activated unlabeled roles on E02 (logic, temporal) and E07 (temporal); the
candidate activated none. Neither variant recognized the account visibility filter
(E01) as security or logic: raw P(A) stayed between 0.11 and 0.13 against P(B)
between 0.30 and 0.40. On these examples the candidate is more conservative, not
uniformly better. Eight snippets with single-author labels cannot separate wording
effects from chance; no question change is promoted from this run.

Raw probabilities are recorded for diagnosis only. Several V2 decisions are near
ties (for example E05 temporal 0.275 versus 0.269), so their selections are fragile.

## Prefix reuse

No call in the complete run reused the prompt prefix (`cache_n = 0` in all 496),
so every question re-encoded the whole window. A separate smoke test
(`runs/20261020-gutsy-slot-smoke/`) encoded the E07 state once, saved the slot with
`/slots/0?action=save` and restored it before each of E07's 16 questions. Every
request then reported `cache_n = 640`, evaluating only 83 to 98 suffix tokens.
Mean latency per question fell from 3.66 to 0.56 seconds on the same jobs.
15 of 16 letters matched the full-prompt run; Q0476 flipped from B to A on a near
tie (reference P(A) 0.209, P(B) 0.229). The largest probability difference was
0.029. Restored-state answers are close to, not identical with, full re-encoding,
and they need their own frozen comparison before replacing it. Peak memory was
982,310,912 bytes: the save path keeps the bound but leaves little margin. The
smoke test ran as an inline command; its arguments, records and memory peak are in
`smoke.json`. The 48 MB saved slot state was deleted after the test because it is
derived, binary and reproducible.

## Slot restore compared on every question (`runs/20261021-gutsy-followup-slot/`)

The runner now has a slot-restore mode. It replayed the exact 496 frozen prompts of
the full re-encoding run with an identical server profile plus the slot directory.
Each of the 53 states was encoded once from an empty slot and saved; the slot was
restored before every question. The adoption rule was frozen in `plan.json` before
inference. `verify_gutsy_followup.py --complete` passed, including prefix reuse on
all 496 calls (`cache_n` equal to the prefix tokens, `cache_n + prompt_n` equal to
the prompt tokens). The full comparison is in that run's `COMPARISON.md`.

| Measure | Full re-encoding | Slot restore |
| --- | --- | --- |
| Identical letters | reference | 495/496 |
| Wall time | 1,995 s | 580 s (3.44x faster) |
| Mean question call | 4.00 s | 0.67 s, plus 0.06 s restore |
| Prefix encodings | none | 53, 203 s in total |
| Sampled peak, server and runner | 977,641,472 bytes | 968,966,144 bytes |

- **Answers:** the only flip is Q0476 (E07, V2, logic), B to A, with reference P(A)
  0.209 against P(B) 0.229. It is the near tie seen in the smoke test. No A/B/Z
  probability is bit-identical: median absolute difference 0.0088, 95th percentile
  0.0273, maximum 0.0684 on a decision with a 0.477 margin. 29 reference answers
  fall inside the 0.05 near-tie margin; 28 of them kept their letter.
- **Scores:** the flip adds logic to E07's V2 selections, where logic is neither
  expected nor explicitly negative. Every recall and negative-activation total is
  unchanged; all other case selections are identical.
- **Speed:** 3.44x overall, not the earlier estimate of about 6x. Restoring is
  cheap, but each state's own encoding remains: 36% of slot-mode model time. The
  gain grows with questions per state: 5.7x on truncated C07 (8 questions per
  state), 2.4x on E05 (16 questions over a short state). The 16 smoke-test answers
  were reproduced exactly in a separate server process.

Verdict under the frozen rule: slot restore is adopted for later iterations, and
`prepare` now creates slot-restore runs by default (`--prefix-mode full` creates a
new reference). This run is the slot-mode baseline; earlier full re-encoding results
are not mixed with slot-mode results.

## Next iteration

1. Grow the real-source pool, prioritizing the measured gaps: account and ownership
   filtering (E01), cleanup and documentation drift, UI races, timing in breaker-like
   state machines (E05). Draw verification snippets from files and projects not
   used for development, and have their applicability judged by someone other than
   the prompt author. The source inventory, sampling target, label protocol and
   stage gates for this expansion are in [EXTERNAL_CORPUS.md](EXTERNAL_CORPUS.md).
2. Replace raw-letter union across many windows with an aggregation rule fitted on
   a labeled development split, so a lens that answers yes almost everywhere (C07
   temporal 39/39) is not automatically selected.
3. Only then revise the candidate wording, freeze it, and measure it on a new
   verification partition.

Prepare a new, nonexisting run directory and execute it from the repository root:

New runs use slot restore by default. Add `--prefix-mode full` to `prepare` to create
a full re-encoding reference.

```powershell
python -B evals/senior-review/choicer-eval/gutsy_followup.py prepare --out runs/<new-run-id>
python -B evals/senior-review/choicer-eval/gutsy_followup.py run --out runs/<new-run-id>
python -B evals/senior-review/choicer-eval/gutsy_followup.py report --out runs/<new-run-id>
python -B -m unittest discover -s evals/senior-review/choicer-eval -p test_gutsy_followup.py -v
```

A slot-restore run reuses the exact cases, jobs and prompts of a complete full
re-encoding run, then pairs every answer with it:

```powershell
python -B evals/senior-review/choicer-eval/gutsy_followup.py prepare-slot --out runs/<slot-run-id> --reference runs/<full-run-id>
python -B evals/senior-review/choicer-eval/verify_gutsy_followup.py --out runs/<slot-run-id>
python -B evals/senior-review/choicer-eval/gutsy_followup.py run --out runs/<slot-run-id>
python -B evals/senior-review/choicer-eval/verify_gutsy_followup.py --out runs/<slot-run-id> --complete
python -B evals/senior-review/choicer-eval/gutsy_followup.py compare --out runs/<slot-run-id> --reference runs/<full-run-id>
```

`prepare-slot` refuses an incomplete or changed reference and freezes the comparison
rule before inference. The runner checks every prompt's token prefix before the first
model call, encodes each state once from an empty slot, restores it before every
question and records the server's `cache_n` to prove the reuse. The saved state lives
under the ignored `.cache/gutsy/slots/` directory only while its run executes.

A run refuses changed frozen files and never retries a model request automatically.
It does not overwrite a prior execution. Creating a `STOP` file in its run directory
stops before the next request; an in-flight request can run until its HTTP timeout.
Termination and process reaping are owned by the runner. Failed runs remain failed,
with completed calls preserved separately.
