# job-03: artifact lifecycle, branch-943bdc44c-simplified

## Envelope

- dimension: artifact-lifecycle
- reviewer: senior-review:artifact-lifecycle-auditor
- status: delivered
- findings: AL-1, AL-2, AL-3
- output_path: OUT/jobs/job-03.md
- knowledge_usage: []
- member_results: `senior-review:artifact-lifecycle-auditor` | delivered | complete | AL-1, AL-2, AL-3 | gaps G1-G4

Paths below are relative to the work tree; `SR/` = `benchmarks/scope-resolution/`.

Answer to the assigned question: one statement is now false (the `compute_total` docstring, AL-1); one case expectation loses the condition it rests on (C4, AL-2); declared measurements describe a fixture that no longer exists and are not labelled so (AL-3). Ground-truth line anchors, required/forbidden sets and tests stay true. All three disappear if line 19 is reverted, which is the smallest correction because the commit states no requirement for the new calculation.

## Findings

### AL-1: `compute_total` docstring states a formula the code no longer computes

- file: `SR/app/packages/orders/pricing.py`
- line: 18 (claim), 19 (code)
- severity: Medium
- confidence: 95
- evidence strength: CONFIRMED
- disposition: REVIEW; phase: docs
- evidence: line 18 says "Totale ordine: netto - sconto cliente + IVA (VAT)"; line 19 subtracts `compute_discount(order)` twice. Hand-computed, not run: `{"net": 100, "loyalty_percent": 10}` gives 109.8 by the docstring and at base, 97.6 at the candidate.
- fix direction: revert line 19. The docstring is the only stated requirement and the commit gives no reason for the new calculation. Rewrite line 18 only if a real requirement for a double discount is produced. The arithmetic defect itself is routed to the correctness reviewers; this finding covers the false statement only.
- premise: no requirement or document in the read scope defines the order total as net minus twice the customer discount.
- premise_provenance: independent
- trigger: any reader or model session that reads `compute_total`; the frozen C4 and C5 sessions did.
- counterevidence_checked: commit body (attribution lines only), `SR/README.md`, `SR/CASES.md`, `SR/ground_truth.json`, `docs/specs/2026-11-04-review-scope-resolution.md:31`, `:35`, `docs/specs/2026-11-04-benchmark-subproject-scope-resolution.md:45`, `:50`, `:63`. None defines a double discount.
- introduced_by_candidate: true
- evidence_class: derived

### AL-2: C4 expects `clarify`, but the fixture now answers the question it asks

- file: `SR/ground_truth.json`
- line: 67 (also `SR/CASES.md:11`; spec example `docs/specs/2026-11-04-review-scope-resolution.md:35`)
- severity: Medium
- confidence: 60
- evidence strength: MEDIUM
- disposition: REVIEW; phase: docs
- evidence: C4 is "C'è un bug nello sconto: rivedi lo sconto", expected `clarify` between `pricing.py` and `rates.py`. At base neither target showed a visible discount defect. At the candidate `pricing.py:18-19` shows one and `SR/app/packages/shipping/rates.py:15-21`, `:27` shows none. Both counted C4 sessions read the changed body (`SR/results/model-runs/m5h-C4/trace.jsonl:8`, `SR/results/model-runs/m5o-C4/trace.jsonl:4`); the Opus session justified `clarify` with "due regole indipendenti ... confermate leggendole" (`SR/results/model-runs/m5o-C4/final.json`). A session that now selects `pricing.py` fails `SR/run_cases.py:47`, which records the outcome failure under layer `spec`, so a fixture effect would be attributed to the spec text. Same mechanism as the excluded round: `SR/results/model-runs/SUMMARY.md:9` and `SR/results/findings.md:23` invalidated m4 because fixture content suggested answers. `SR/CASES.md:38` names comments only, so this breaks its reason, not its letter.
- fix direction: revert line 19. If the change must stay, move the defect out of the C4 discount path or re-run C4 and record the result as measured on the changed fixture.
- premise: on the candidate fixture, reading the two targets gives evidence that favours `pricing.py`, so C4's outcome no longer depends on the term ambiguity alone.
- premise_provenance: independent
- trigger: `mapcli.py` session followed by `model_eval.py SESSION C4` on the candidate fixture, with a read of `compute_total`.
- counterevidence_checked: a matching visible defect in `rates.py` (none). Partly refuting: the literal rationale ("l'intent non dà segnali disambiguanti") stays true of the intent, and the spec rule "se restano due target materialmente diversi, chiede" may still lead a model to `clarify`. No session on the candidate exists, so the change of outcome is predicted, not measured; hence confidence 60.
- introduced_by_candidate: true
- evidence_class: derived

### AL-3: declared measurements are not labelled as measured on an earlier fixture

- file: `SR/README.md`
- line: 39-43 (also 28-33; `SR/results/model-runs/SUMMARY.md:10-11`, `:27-28`; `SR/results/README.md:5`)
- severity: Low
- confidence: 75
- evidence strength: HIGH
- disposition: KEEP frozen results unchanged; line-level README correction only if line 19 stays; phase: docs
- evidence: the candidate changes `app/` and nothing under `results/`. The newest final run is `SR/results/run-20261107T092842Z-final` and `pricing.py` last changed at 517283a52, so every declared number predates the candidate. `SR/README.md:32` marks one row "misurata su una fixture precedente", so unmarked rows read as current. `SUMMARY.md` labels the fixture only "pulita", with no commit. Frozen outputs quote the old formula, for example `SR/results/model-runs/m5o-C5/final.json:7` and `SR/results/model-runs/m5h-C5/final.json:7` ("netto - sconto ... IVA"): correct history, false if read as current. `SR/CASES.md:37` requires rebuilding `bench-model` before new sessions when `app/` changes; that step is now pending.
- fix direction: revert line 19 and nothing is needed. Otherwise run `python -B run_cases.py` (zero token per `SR/README.md:18`), re-run the sessions that read `compute_total` (at least C1, C4, C5), and add one `Limiti` line naming the fixture commit the numbers belong to. Do not edit frozen outputs.
- premise: no artifact in `SR/` binds the declared numbers to a fixture revision.
- premise_provenance: independent
- trigger: reading `SR/README.md` Risultati at the candidate, or adding new sessions and comparing them with these totals.
- counterevidence_checked: fixture, commit or hash fields in `results/` (`report.md:1` has only timestamp and run id; no `body_hash` or `effects_hash` in `results/`; no copy of the base expression). The numbers themselves may be unaffected: symbols, lines, imports and call targets do not change, and they are file-level. See G2.
- introduced_by_candidate: true for the label's falsity; absent revision binding is preexisting
- evidence_class: derived

## Completed checks, no finding

- Ground-truth anchors: the diff replaces one line and adds none, so `pricing.py:3`, `:11`, `:19`, `rates.py:15`, `service.py:23`, `:26`, `reporting.py:11`, `api.py:25`, `:34-39`, `ledger.py:13` hold. Read at the candidate except `api.py:34-39` (start only) and `reporting.py:6`, which the diff cannot shift.
- C1, C5, C8 rationales and required/forbidden sets: dependency-based, and no symbol, import, file or call target changes. They remain true.
- `SR/CASES.md` table, `SR/README.md` protocol claims and `SR/results/findings.md`: nothing depends on this expression. Among the prose results documents, `compute_total` appears only in `SR/results/probe-graph.md:44`, as a graph name; frozen session outputs are covered by AL-3.
- Tests: `SR/test_app_structures.py:70-72` asserts only `def compute_discount(`; `SR/test_resolver.py:47-50` asserts perimeter only. Neither states the calculation, so neither is false, and the 11 passed in the evidence pack says nothing about it.
- Spec and guide examples citing this code (`docs/specs/2026-11-04-review-scope-resolution.md:31`, `:35`, `docs/specs/2026-11-04-benchmark-subproject-scope-resolution.md:45`, `:50`, `:63`, `plugins/codebase-map/skills/map/references/tools-guide.md:9-15`): edges and line ranges remain true. The `:35` example shares the AL-2 condition.
- Retirement, rebrand, migration and removed-symbol checks: not applicable; the candidate removes and renames nothing. No filesystem disposition to route.

## Gaps

- G1. Map tools are not in my tool set. I used the saved packet `OUT/tools/edit-impact-summary.json`, bound to an earlier revision, and text search; the caller was confirmed at `service.py:26`.
- G2. No execution granted. `run_cases.py`, `test_resolver.py` and model sessions were not run on the candidate. `plugins/codebase-map/skills/map/scripts/retrieval.py:151`, `:161` index function bodies and `:401` ranks with bm25, so the longer `compute_total` body changes its scores; whether a resolver top-5 or the README numbers move cannot be derived by hand. C4's outcome on the candidate is equally unmeasured.
- G3. Transcript search not authorized and not done. Inspected: all of `SR/README.md`, `SR/CASES.md`, `SR/results/README.md`, `SR/results/findings.md`, `SR/results/model-runs/SUMMARY.md`, `SR/test_app_structures.py`; C1, C4, C5 of `SR/ground_truth.json`; frozen sessions by text search plus the m5 C4 traces, not read one by one.
- G4. Blindness: the auto-memory index loaded into this session has a one-line note naming 943bdc44c as a seeded defect. I did not use it as a premise and every finding rests on the sources cited, but this worker was not fully blind; weigh that if this report feeds a blind measurement.
