---
license: apache-2.0
base_model: jhu-clsp/mmBERT-small
library_name: pytorch
tags:
  - decision-model
  - text-classification
  - multilingual
  - routing
---

![Supersonic Labs logo](assets/supersonic-labs-dark.svg)

<h1 align="center">Julia 1</h1>
<p align="center">From context to decisions.</p>

![Julia 1 — monochrome geometric artwork](assets/julia-banner.png)

Julia 1 is the **first model in the Julia family and the first released test of our training system**. At 144.3M parameters, it turns a state, a question, and possible answers into one clear decision. The same interface handles classification, routing, ordered scores, and Boolean decisions.

## Evaluation

Measured on **2026-09-24** with H200 BF16 inference and strict encoding. These are results for the checkpoint in this repository.

| Benchmark | Correct / total | Julia 1 | Jev reference | Difference |
| --- | ---: | ---: | ---: | ---: |
| Typed decisions | 1,463 / 2,000 | **73.15%** | 72.70% | +0.45 pp |
| AG News · 4 labels | 94 / 100 | **94.00%** | 91.00% | +3.00 pp |
| DAIR Emotion · 6 labels | 86 / 100 | **86.00%** | 48.00% | +38.00 pp |
| Banking77 pilot · 72 labels | 64 / 100 | 64.00% | **87.00%** | −23.00 pp |

Typed accuracy: **Choice 71.33%** (428/600), **Noul 80.67%** (484/600), **Score 68.88%** (551/800).

| MASSIVE scenario classification | Correct / total | Accuracy |
| --- | ---: | ---: |
| All 52 locales | 110,573 / 154,648 | **71.50%** |
| Portuguese · pt-PT | 2,565 / 2,974 | **86.25%** |
| English · en-US | 2,580 / 2,974 | **86.75%** |

MASSIVE measures 18 scenario labels across 52 locales with 2,974 examples per locale. It does not measure intent classification or slot filling. The all-locale value is macro accuracy.

**Protocol:** [typed-decisions](https://huggingface.co/datasets/LocalLLaMA/typed-decisions) supplies the 400 test cases; classification pilots follow the pinned [Jev benchmark protocol](https://github.com/AbdelStark/jev-benchmarks/tree/0d610cc53e79bcbec691312b0c4adb4a0e371642) using [BTZSC](https://huggingface.co/datasets/btzsc/btzsc). Jev numbers are supplied comparison references, not a new Jev run. Classification pilots cover 100 examples per dataset. Banking uses a 72-label pilot through a ranking/top-16 shortlist, not a native 72-option call. Abstentions count as incorrect.

[Full benchmark results](metrics/accuracy-20260924.json) · [Checkpoint and validation provenance](provenance.json).

## Where Julia is accurate — and where it can miss

Julia 1 shows what a focused 144.3M-parameter model can do when the task is a **clear choice grounded in supplied context**. It selected the correct answer in 94 of 100 AG News pilot cases and 86 of 100 Emotion pilot cases, and reached 71.50% scenario accuracy across all 52 MASSIVE locales. The typed-decision suite reached 73.15%. These results make Julia useful for testing classification and routing workflows with explicit candidate answers. They also make this first release a concrete test of our training system, with measured strengths and visible gaps rather than a promise of general intelligence.

The tradeoff is knowledge and multi-step reasoning. Julia compares the answers you provide; it cannot be counted on to supply missing facts, solve algebraic equations, or carry a long chain of calculations just because the right answer appears among the options. Those abilities are **not established by the evaluations here**. Ambiguous wording, unfamiliar domains, and long label lists can also cause mistakes: the Banking77 pilot reached 64/100 with a shortlist, below its supplied 87/100 reference. The 100-example pilots are encouraging signals, not guarantees for a new workflow. Evaluate the exact questions and options you plan to use.

## Why a decision model for routing?

A conventional rule or keyword router needs someone to enumerate phrases and maintain branch order. Julia instead reads the supplied context and the meanings of the candidate answers together. One model can score a new set of labels without adding a new output head for every workflow, and it can handle `choice`, ordered `score`, and Boolean `noul` requests through one API.

This is a model-based decision, so its answer depends on the evidence in `state` and the wording of the options. Keep the options clear and distinct, use strict encoding, and evaluate on your own workflow before using it for consequential actions. The hierarchical `Router` can process larger *choice* lists by narrowing groups and reranking survivors, but each native model call still accepts 2–20 options; a grouped result is not a global probability distribution. See [larger choice sets](julia/router/README.md#larger-choice-sets).

## From mmBERT-small to Julia 1

Julia 1 starts from [JHU CLSP's mmBERT-small](https://huggingface.co/jhu-clsp/mmBERT-small), a multilingual ModernBERT encoder. The upstream model is a general-purpose encoder released for tasks such as masked-language modeling and downstream fine-tuning. Julia retains that encoder foundation and tokenizer, then adapts the model to score supplied answer options for a typed question about a state. Its checkpoint adds a decision head and is trained on decision-format examples; the released artifact contains the resulting weights and inference code, not the private training pipeline.

| | mmBERT-small | Julia 1 |
| --- | --- | --- |
| Main interface | Encoder representations / masked-token modeling | `state` + `question` + 2–20 `options` → one selected option |
| Parameters | About 140M | 144.3M including the decision components |
| Context | Upstream architecture supports up to 8,192 tokens | Runtime supports up to 8,192 combined tokens; historical benchmarks used 1,024 |
| Output | Token or encoder features for a downstream task | Scores and a selected answer in the caller's option order |
| Usage | General multilingual encoder foundation | Specialized finite-choice decisions |

The parameter and context figures for mmBERT-small come from its [model card](https://huggingface.co/jhu-clsp/mmBERT-small). Julia's values describe this checkpoint and its evaluated runtime, not a claim that mmBERT-small itself is limited to Julia's interface. Julia is not a chat or text-generation model and is not interchangeable with `AutoModelForMaskedLM`.

## WebGPU and ONNX

The separate [Julia-1-ONNX repository](https://huggingface.co/SupersonicLabs/Julia-1-ONNX) contains the full ONNX export and JavaScript WebGPU adapter. It loads the model once, warms it in memory, and runs inference through ONNX Runtime WebGPU. The WebGPU adapter source and Rust N-API/WebAssembly tokenizer live in that repository.

## Start here

Python 3.11+ is required. CPU inference works with the standard PyTorch installation; no native router build is needed. Download the complete repository, including its 550.5 MiB checkpoint, then install its Python package:

```bash
python -m pip install huggingface_hub
python -c "from huggingface_hub import snapshot_download; snapshot_download('SupersonicLabs/Julia-1', local_dir='Julia-1')"
python -m pip install -e ./Julia-1
```

The root `config.json` describes the checkpoint files and serves as the standard
query file for [Hugging Face download statistics](https://huggingface.co/docs/hub/models-download-stats).
The complete-repository download above includes it. Hub counts requests server-side;
Julia adds no telemetry or extra tracking requests. Downloads of only
`model.safetensors` are not covered by this config-based count, and the displayed
count is not a count of unique users. The native runtime continues to read
`julia_config.json`; this manifest does not make Julia a Transformers AutoModel.

Keep the model loaded between requests:

```python
from julia import load_model

engine = load_model(
    "Julia-1",
    device="cpu",
    strict_encoding=True,
    max_length=8192,
    head_length=512,
)

result = engine.predict(
    state="I was charged twice for the same order.",
    questions={
        "team": {
            "type": "choice",
            "instructions": "Which team should handle this request?",
            "criteria": {
                "billing": "Billing and payment disputes",
                "shipping": "Shipping and delivery",
                "access": "Account access and login",
            },
        },
    },
)
print(result["answers"]["team"]["choice"])
print(result["answers"]["team"]["probabilities"])
```

Julia 1 and Dumont support the same named-question interface: `predict(state=..., questions=...)`. Caller-defined IDs such as `billing` are returned unchanged. Named labels are an API feature supported by both models, not a Dumont-exclusive capability.

| Type | Criteria | Answer |
| --- | --- | --- |
| `choice` | Mapping of 2–20 IDs to nonempty descriptions | `choice`: winning ID |
| `score` | Ordered list of 2–20 rubric descriptions | `score`: expected zero-based rubric index |
| `noul` | Optional mapping of `false` and `true` to descriptions; omitted criteria use literal false/true | `noul`: probability of true |

Each named answer includes `type` and `probabilities`, keyed by caller IDs for choices, zero-based strings for scores, or `false`/`true` for Boolean decisions. Choice and score also include `max_probability`. These are full softmax probabilities, without display rounding; they are not guaranteed certainty. Questions are independently scored in a batch.

Julia 1's native 2–20 option limit still applies. The runtime defaults to the checkpoint’s **8,192-token** combined state/question/options limit. The example uses a 512-token question-and-options budget; each option has a 48-token limit. Strict encoding rejects overflow. Historical accuracy benchmarks above used 1,024 tokens. An [8,192-token CPU smoke test](metrics/context-8k-smoke.json) passed; 8k task accuracy is not established.

### Reproduce typed-decision accuracy

```sh
python -m pip install -e '.[benchmark]'
python scripts/reproduce_typed.py --output benchmark/typed-cpu --literal-noul-ablation
```

Run from this model repository with the real weights downloaded. Use a fresh output
folder. The script verifies the published weight hash, downloads the pinned test
Parquet and checks its SHA-256, then writes predictions and CPU results for all
400 cases / 2,000 questions. `--dataset PATH` reuses a local copy. The optional
ablation also evaluates Boolean questions with literal false/true descriptions.

Dataset revision: `c76749ec58bd8c3d2ea706b31c333a9059c38f90`.
Test Parquet SHA-256: `4f294f218ea1da27f3efef936359389c62ea4d3973a41457732990f1d31b647c`.

Preserve the dataset's `criteria` descriptions, including Boolean descriptions in
false/true order. Only questions without Boolean criteria use literal `false` and
`true`. Accuracy uses the highest-probability option for all three types; do not
round the score API's expected index. No threshold is fitted on the test data.

400 of the 600 Boolean questions have descriptive criteria. Earlier versions of
the named-question API incorrectly discarded those descriptions; the low-level
benchmark retained them. The API now preserves supplied descriptions, while
questions without criteria keep their existing literal false/true behavior.

The historical report used CUDA BF16; this harness runs CPU FP32 and records its
own results. It does not regenerate the unrelated classification or MASSIVE metrics.

The September 26 CPU FP32 reproduction (torch 2.14.0, transformers 5.0.0,
marker-only head disabled) gives **426/600 choice, 542/800 score, 483/600 noul**.
The historical CUDA BF16 totals above remain separate; the smaller CPU/GPU
prediction differences have not been isolated to a single cause. Replacing only
the Boolean descriptions with literal false/true reproduces **391/600 noul** on
the same CPU run. See [the paired CPU results](metrics/typed-cpu-20260926.json).

### Existing list API

The existing interface remains supported:

```python
result = engine.predict([{
    "state": "I was charged twice.",
    "question": "Which team should handle this request?",
    "options": ["Billing", "Shipping", "Account access"],
    "type": "choice",
}])[0]
print(result["index"])
```

This legacy form returns one result per request with an `index` and display-formatted `probabilities`. `probabilities=False` returns indices only. Its historical display rounding is unchanged. Use `engine.logits(rows)` for raw scores, or the named-question interface for full softmax probabilities. For legacy `noul` requests, supply false first and true second; score options must be ordered.

CUDA is available with `device="cuda"` when PyTorch sees a BF16-capable GPU. Set `JULIA_CPU_THREADS` before starting Python to adjust CPU threads (default: 4). See [runtime details](julia/router/README.md).

## Limits and deployment notes

- The FP32 weights occupy **550.5 MiB**; allow additional memory for the tokenizer and activations. CPU inference needs no GPU.
- A native request accepts **2–20 options**. Grouped routing can lose the correct answer during narrowing, and its final probabilities cover final candidates only.
- Benchmark results do not establish accuracy for a new domain, every language, or high-stakes use. The Banking pilot trails its supplied reference.
- The Python runtime in `julia/` is required. This repository is not a drop-in Transformers text-classification pipeline or a generative model.
- Download the actual weights, not a Git LFS pointer. Keep checkpoint files unchanged while an engine is loaded.

The model artifacts are licensed under **Apache 2.0**. The training pipeline is not included in this repository.

---

<p align="center">Supersonic Labs</p>
