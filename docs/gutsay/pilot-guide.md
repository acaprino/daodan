# Gutsy Q4 decision pilot

Evaluation-only implementation of the [frozen preliminary protocol](gutsy-preliminary-tests-2026-10-26.md). The user's request of 26 October 2026 authorizes this bounded Modal CPU execution. No training, production integration, commits or real external actions are part of the pilot.

The three fixture modules keep oracle data separate from model inputs. `pilot.py` prepares an immutable bundle and scores downloaded responses. `modal_pilot.py` runs the official Gutsy service in an ephemeral CPU-only Modal Function. `compaction_bridge.mjs` uses the actual upstream fast-jev library for preparation, reconstruction and mechanical contracts.

## Runtime and provenance

- Gutsy source: `kouhxp/gutsy`, commit `db5c2ec62fc81703938adbd714915b53a9fb0de1`, Apache-2.0.
- Weights: `kouhxp/gutsy`, HF revision `f9995fe26a337f1a4ea3f1a5ed38c9799e5a8f63`, Q4_K_M SHA256 `ddf9c23b8a07c008172f1731f4dd93c464b651b9a70409f0feaf8c2d4e089152`, 529,296,832 bytes. Weights are downloaded only inside the remote container.
- Fast-jev: `tamaratran/fast-jev-compaction`, commit `e3f262a7f4d42bd8dd32ced30d26176f7cb545b0`, MIT. Source and build dependencies are transient evaluation dependencies under the owned run's `deps/`, not a new vendored kernel.
- Remote inference: Python 3.12, llama-cpp-python 0.3.36, NumPy 2.3.4; record actual versions and native-library hashes in the returned evidence.
- Synthetic tools and operations are never executed. The pilot invokes only model inference and deterministic local scoring.

## Local checks and preparation

Provide the pinned upstream package built with its lockfile (`npm ci --ignore-scripts`, `npm run build`). Set `FAST_JEV_MODULE` to that package's absolute `dist/index.js`, then run from the repository root:

```text
python -B -m unittest discover -s evals/gutsy-decision-pilot -p test_*.py -v
python -B evals/gutsy-decision-pilot/pilot.py prepare
```

By default, `pilot.py` resolves the existing dependency at `.daodan/runs/2026-10-26-gutsy-modal-pilot/deps/fast-jev/dist/index.js`. Preparation writes separate `cases.json`, `input.json`, `manifest.json` and `deterministic-checks.json` under that run's `artifacts/`. Changed frozen artifacts are refused rather than overwritten. A new experiment needs a new named artifact directory.

The effective first corpus is 47 requests and 314 model questions: 15 routing requests/150 questions, 16 tool requests/132 questions after eligibility filtering, and 16 compaction requests/32 questions. Additional mechanical contracts call no model. Discovery cases T15/T16 are not independent semantic successes.

## Modal execution

This command starts paid remote CPU work; use the authorization and budgets for the intended run. On Windows, enable UTF-8 for the Modal client before launching it.

```text
modal run evals/gutsy-decision-pilot/modal_pilot.py --input-path .daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts/input.json --output-path .daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts/modal-results.json
python -B evals/gutsy-decision-pilot/pilot.py score --result .daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts/modal-results.json
```

The Function has four requested/maximum CPU cores, four inference threads, a 2 GiB hard memory limit, no GPU, one container and no automatic retries. The model uses n_ctx=4096, one prefix cache entry and a 128 MiB cache budget. It invokes R01, C01-A and T01 first. The duration cap is conservative: download, startup and inference together share at most 1,800 seconds inside the Function; image build time is separate. The Function timeout is 2,400 seconds. HTTP errors stop the corpus to avoid enqueueing behind a potentially still-running request.

Returned evidence includes raw responses, per-request time, cache diagnostics, weights/calibration hashes, environment and sampled combined RSS. Summing process RSS can count shared pages more than once and is not whole-machine memory. Memory, task success and latency targets are separate facts. Cold start, download, server startup and full multi-question decision times must not be presented as single-question inference time.

## Scoring boundaries

Routing uses partial signal labels and the canonical router; a diagnostic argmax can match an oracle while reject still forces a conservative result. A label may be an acceptable set, mildest value first, and `tier_changed_by_labeled_errors` says whether correcting the labeled misses would move the tier at all. Tool sufficiency accepts OR alternatives and separates raw selection, mandatory discovery and broad fallback; `superfluous_canonical`, `exact_sufficient` and `schema_bytes_minimal` keep over-selection visible, since sufficiency alone is satisfied by selecting everything. Compaction reconstructs the actual transcript before checking facts, recovery and pairing; `evidence_decision_bearing` marks the cases whose required fact lives only in the candidate result, and only those count as evidence about the classifier. C08 protection is scored separately.

The scorers were revised after the first run (see the results document). The frozen run keeps its original `cases.json` digest; `prepare` refuses to overwrite it, so a rerun needs a new named artifact directory.

The upstream compaction question presumes a tool can always be run again. C01/C05/C08 explicitly contradict that premise with irreproducible evidence. Both A/B retain the same upstream question so the experiment isolates result visibility; the conflict is a limitation to report, not evidence that a new question policy was tested.

`REPORT.md` and `scores.json` inside the run artifacts are generated from saved evidence. Token savings for an unspecified downstream tokenizer are unavailable; byte reductions are measured. These small synthetic cases do not establish production reliability or success of downstream LLM work.
