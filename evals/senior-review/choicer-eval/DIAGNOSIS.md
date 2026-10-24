# Julia usage diagnosis

The original pilot rejects its tested input formulations. It does not establish that local reviewer routing is impossible. The follow-up confirms sensitivity to source presentation and option wording, while elementary code decisions remain unreliable in these controls.

## What was measured

All probes reused the same pinned Julia weights, CPU FP32 runtime and four threads. No new model download, environment or paid LLM call was needed. Original pilot requests, outputs and scores remain unchanged.

1. Reproduced the adapted pilot's irrelevant React activation on the Python cache hunk: P(true)=0.999919164. The diagnostic key `original_react` means that prior adapted criterion; it is not the original exact kernel criterion.
2. In a fixed two-option code-family choice, the numbered/path-annotated Python state is classified as React. The same code without those annotations is classified as Python database/cache code. Reversing the two option positions retains both decisions. This establishes a presentation effect on this example, not a universal benefit of removing line numbers or a separation of path effects from numbering effects.
3. Tested complementary criteria, explicit observable questions, literal Boolean options, raw code and manually authored natural-language summaries. Some corrections break positive controls. Complementary wording alone is not a demonstrated fix.
4. Compared `noul` and `choice` with identical question/description text and permuted description order in 48 low-level probes. Reversed `noul` rows are intentional position diagnostics with explicit semantic index tracking, not standard typed-API probabilities. No threshold was fitted.
5. Compared the optimized and original encoder forward paths on 8 identical probes: maximum absolute logit difference 0.0; all decisions equal True. This checks the exercised path, not every runtime configuration.

The official billing example also selects billing. Source audits found no false/true reversal, state loss, output-row mismatch, checkpoint mismatch, or truncation in the short failing example. Question IDs and role IDs are not model text: the generic reviewer question relies on the descriptions alone.

## Fresh source controls

An independent author supplied eight new snippets before inference: two React, two Python persistence/cache, two Python computations and two TypeScript computations. Gold stays outside model input. These are small development controls, not a representative test set or a validated reviewer-activation oracle.

| Input/question formulation | Family correct | React positive hits | React false positives | Persistence positive hits | Persistence false positives |
| --- | --- | --- | --- | --- | --- |
| Raw source, concrete questions | 5/8 | 0/2 | 0/6 | 0/2 | 0/6 |
| Automatic structural facts, same questions | 5/8 | 1/2 | 1/6 | 0/2 | 2/6 |
| Raw source, declarative Boolean instructions | 0/0 | 0/2 | 5/6 | 2/2 | 5/6 |

A 0/0 family entry means that formulation did not ask a family question. Boolean overall accuracy can hide an always-negative response, so the table shows positive detection and false positives explicitly. Declarative persistence detects both positives but falsely selects five of six negatives; its overall correctness is only 3/8. It is not a repair.

Structural facts are automatically extracted imports, called names, JSX elements and language. Python uses its standard AST; JavaScript/TypeScript uses a bounded diagnostic heuristic. The extractor receives no labels and emits no reviewer, bug or relevance assessment. These cards approximate an input boundary; they do not exercise the actual Codebase Map or prove that richer semantic cards would have the same outcome. Manually authored summaries in phase 1 are a separate representation experiment and do not establish free production preprocessing.

## Published Boolean sanity sample

On the first three published rows from each of three domains, Julia agrees with the provided Boolean gold on 13/15 questions. These nine rows are a small convenience sample, not a reproduction of the full published benchmark. Gold probabilities are dataset annotations and are never substituted for Julia outputs.

The exact state strings, questions, original rows, source URLs and pinned/current Parquet identities are retained in `official-controls.json`. The test-file hashes match the model card's pinned dataset revision despite a newer dataset HEAD.

## Decision

Keep the architecture question open. The pilot's broad negative result was insufficient to diagnose why routing failed. These probes establish that our representation matters and that importing dispatch descriptions as classification options is not a validated routing contract. They do not establish a working replacement by changing a flag or wording one question differently.

A further routing experiment should define self-contained, code-grounded predicates, bind them to actual map evidence, test both positive and negative controls, and evaluate on new cases before reusing the pilot as a reported accuracy set. Any semantic-card authoring, model adaptation or fallback cost belongs in the token accounting. Thresholds and criteria should be fixed before that evaluation. No production routing or reviewer definition was changed here.

## Reproduce and inspect

[Scored evidence](runs/20261020T-diagnostic/diagnosis-scores.json), [frozen diagnostic plan](runs/20261020T-diagnostic/plan.json), [fresh controls](runs/20261020T-diagnostic/fresh-controls.json), [published controls](runs/20261020T-diagnostic/official-controls.json).

Rebuild this report without inference:

```powershell
python -B evals/senior-review/choicer-eval/summarize_diagnosis.py
```

The inference entry points are `diagnose_julia.py`, `probe_julia_runtime.py` and `probe_julia_facts.py`; each separates preparation from execution and refuses to overwrite existing inference outputs. Their `run` actions require the already provisioned model environment.

Official references: [Julia model card](https://huggingface.co/SupersonicLabs/Julia-1), [typed-decisions dataset](https://huggingface.co/datasets/LocalLLaMA/typed-decisions).
