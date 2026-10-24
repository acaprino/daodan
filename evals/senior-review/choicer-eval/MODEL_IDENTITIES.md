# Model and project identity clarification

Checked against primary project pages on 2026-10-20 after a supplied research
note used different projects from those named in the benchmark prompt.

| Name | Identity | Relation to this benchmark |
| --- | --- | --- |
| [SupersonicLabs/Julia-1](https://huggingface.co/SupersonicLabs/Julia-1) | A learned typed-decision model with a Python runtime; accepts state, question and candidate answers. | The pinned local model actually exercised here. |
| [kouhxp/gutsy](https://huggingface.co/kouhxp/gutsy) | `gutsy-0.8b-v04`, a Qwen3.5-0.8B fine-tune distributed as GGUF with the `gutsy-inference` Jev-style runtime. Served here through a pure PyTorch `Qwen3NextForCausalLM` backend (`probe_gutsy.py`), revision `f9995fe26a337f1a4ea3f1a5ed38c9799e5a8f63`, Q8_0 811,843,008 bytes. | The local model exercised in the [gutsy benchmark](GUTSY_RESULTS.md); not part of the original Julia-1 pilot. |
| Julia programming language | The programming language used in the supplied note's `using HTTP`, `Threads.@spawn` and Dagger examples. | Those orchestration examples do not describe the Julia-1 model being evaluated. |
| [yzfly/edgejev](https://github.com/yzfly/edgejev) | A local inference project with ONNX/INT8 backends such as Laya. | The original prompt's optional secondary candidate. It has not been provisioned or benchmarked here. |
| [kiwi0719/jev-edge](https://github.com/kiwi0719/jev-edge) | An independent gateway admission-control project for prompt injection and abuse, using TypeSafe Jev or other judges. | A different repository from edgejev. Its gateway benchmarks do not measure Daodan reviewer selection. |

The custom Gutsy PyTorch backend is an experimental reimplementation, not a
verified equivalent of the official Qwen3.5/llama.cpp runtime. Its internal
cache self-check does not establish tokenizer, model or batched-path parity.
The separate Q4_K_M v2 summaries also lack complete frozen execution provenance;
see [the corrected results](GUTSY_RESULTS.md) before comparing scores.

The supplied note's recommendation to include relevant context is compatible
with this experiment: the fresh controls provide task scope and concrete source
or document artifacts. This does not transfer another model's accuracy,
latency, calibration or commercial terms to Julia-1.

The sources above establish identities and documented interfaces only. The
benchmark's pinned revision, runtime and actual outputs remain its execution
evidence. The supplied note's remaining version, pricing, framework and
production recommendations were not audited as part of this offline selection
task. No gateway, Julia-language service or hosted Jev client was installed.
