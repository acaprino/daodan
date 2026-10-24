# Slot restore versus full re-encoding

Reference: `runs/20261020-gutsy-followup-ctx1536` (full re-encoding). Candidate: `runs/20261021-gutsy-followup-slot` (slot restore).

**Verdict: adopt slot restore as the prefix mechanism for later iterations.** The rule was frozen in `plan.json` before inference.

## Checks

| Check | Result |
| --- | --- |
| All planned calls valid in both runs | pass |
| Identical frozen prompts | pass |
| Same model, binary and server profile except the slot directory | pass |
| Prefix reuse verified on every call | pass |
| Every letter flip is a near tie (reference margin below 0.05) | pass |
| Memory bound respected | pass |

## Answers

- Identical letters: 495/496 (99.8%).
- Identical A/B/Z probabilities: 0/496 (0.0%).
- Largest absolute probability difference: 0.0684; median 0.0088; 95th percentile 0.0273.
- Reference answers inside the near-tie margin: 29 of 496.
- Questions with a probability outside the returned top 100: 0.

| Question | Case | Input | Questions | Window | Role | Full | Slot | Reference P(A), P(B) | Reference margin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q0476 | E07 | windowed | v2 | W001 | logic-integrity-auditor | B | A | 0.209, 0.229 | 0.019 |

## Case-level selections

| Case | Input | Questions | Added | Removed | Expected found (full, slot) | Negatives activated (full, slot) |
| --- | --- | --- | --- | --- | --- | --- |
| E07 | windowed | v2 | logic-integrity-auditor | none | 0/1, 0/1 | 0/4, 0/4 |

| Rows | Expected found, full | Expected found, slot | Negatives activated, full | Negatives activated, slot |
| --- | --- | --- | --- | --- |
| C01, truncated, v2 | 0/2 | 0/2 | 0/0 | 0/0 |
| C01, windowed, v2 | 1/2 | 1/2 | 0/0 | 0/0 |
| C07, truncated, v2 | 3/5 | 3/5 | 0/0 | 0/0 |
| C07, windowed, v2 | 4/5 | 4/5 | 0/0 | 0/0 |
| development, windowed, candidate | 3/6 | 3/6 | 0/14 | 0/14 |
| development, windowed, v2 | 1/6 | 1/6 | 0/14 | 0/14 |
| verification, windowed, candidate | 4/5 | 4/5 | 0/16 | 0/16 |
| verification, windowed, v2 | 4/5 | 4/5 | 0/16 | 0/16 |

## Runtime

| Measure | Full re-encoding | Slot restore |
| --- | --- | --- |
| Wall time, seconds | 1994.7 | 580.0 |
| Model time, seconds | 1982.8 | 567.6 |
| Mean question call, seconds | 4.00 | 0.67 |
| Prefix encodings | none | 53, 202.9 s |
| Slot saves and restores, seconds | none | 31.1 |

Speedup: 3.44x wall time, 3.49x model time.

| Case and input | Full, seconds | Slot, seconds | Speedup |
| --- | --- | --- | --- |
| C01 truncated | 50.8 | 10.3 | 4.92x |
| C01 windowed | 102.9 | 28.1 | 3.66x |
| C07 truncated | 57.1 | 10.0 | 5.69x |
| C07 windowed | 1387.1 | 385.9 | 3.59x |
| E01 windowed | 52.2 | 15.3 | 3.42x |
| E02 windowed | 33.5 | 13.3 | 2.52x |
| E03 windowed | 90.4 | 32.4 | 2.79x |
| E04 windowed | 35.9 | 14.5 | 2.47x |
| E05 windowed | 40.3 | 16.9 | 2.39x |
| E06 windowed | 39.3 | 13.0 | 3.03x |
| E07 windowed | 58.6 | 15.3 | 3.83x |
| E08 windowed | 34.7 | 12.5 | 2.78x |

## Memory

| Measure | Full re-encoding | Slot restore |
| --- | --- | --- |
| Sampled peak, server and runner, bytes | 977641472 | 968966144 |
| Server lifetime peak working set, bytes | 924270592 | 926564352 |

Cross-process repeatability: 16 of 16 slot answers from the earlier smoke test were reproduced exactly (letter and exact largest probability difference against the same reference).

## Boundaries

- Full re-encoding is the frozen reference, not ground truth. Both paths process the same tokens; slot restore encodes the state prefix as its own prompt, so prompt batches end at different positions and floating-point results differ slightly. A decision whose two options are nearly tied can flip under either path.
- If slot restore is adopted, results are compared only within one prefix mode. This run is the slot-mode baseline for the same 496 questions.
- The near-tie margin was fixed from the 16-question smoke test, whose questions are part of this comparison.
- One machine, binary, model, thread count and server profile. Raw probabilities are uncalibrated.
