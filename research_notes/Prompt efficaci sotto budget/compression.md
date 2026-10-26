# Prompt and Context Compression Under a Token Budget

## What does each technique do, and what evidence shows preserved or degraded accuracy?

### Takeaway
The methods divide into hard prompts (shortened text) and soft prompts (learned activations or model parameters). Every family has operating points where accuracy is preserved or improves and others where it degrades materially; a headline compression ratio is not evidence of general, lossless behavior.

### Cited Findings

#### Hard prompt compression

- **“LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models” (2023)** uses a small LM to rank content by perplexity, allocates different budgets to instructions, demonstrations, and questions, then applies iterative token-level pruning and optional distribution alignment. In the authors' GPT-3.5 evaluation, GSM8K EM was 79.08 at 5x versus 78.85 full-shot and 77.33 at 20x; BBH was 70.11 at 3x versus 70.07 full-shot but fell to 56.85 at 7x. Thus “up to 20x with little performance loss” describes the GSM8K operating point, not BBH or a universal guarantee. Evidence: original authors' benchmark tables and ablations, EMNLP 2023. [Primary paper](https://arxiv.org/html/2310.05736); [publication record](https://aclanthology.org/2023.emnlp-main.825/).

- **“LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression” (2024)** adds question-aware document ranking and contrastive perplexity, document reordering, adaptive budgets, and subsequence recovery to LLMLingua. On NaturalQuestions with the gold document in position 10, the 3.9x compressed prompt scored 71.2 versus 54.1 for the original; with the gold document first, it scored 75.0 versus 75.7 original. On LongBench, average scores were 48.8 at 3x and 48.3 at 6x versus 44.0 original. Improvements are therefore position- and setup-dependent and come from the full pipeline, not token pruning alone. Evidence: original authors' multi-benchmark evaluation, ACL 2024. [Primary paper and tables](https://arxiv.org/html/2310.06839); [publication record](https://aclanthology.org/2024.acl-long.91/).

- **“LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression” (2024)** distills GPT-4 word-deletion decisions from MeetingBank into an XLM-RoBERTa-large or mBERT token classifier, using bidirectional context to retain an ordered subsequence of the source. At roughly 3.1x on MeetingBank, QA EM was 86.92 versus 87.75 original and summary ROUGE-L was 34.24 versus 35.15. At 5x on LongBench, its average was 39.1 versus 44.0 original and 48.0 for question-aware LongLLMLingua; on GSM8K it retained 79.08 at 5x and 77.79 at 14x versus 78.85 full-shot. “Faithful” means extractive fidelity to source words, not preservation of all information. Evidence: original authors' in-domain and out-of-domain tables, Findings of ACL 2024. [Primary paper](https://arxiv.org/html/2403.12968v2); [publication record](https://aclanthology.org/2024.findings-acl.57/).

- **“Compressing Context to Enhance Inference Efficiency of Large Language Models” (Selective Context, 2023)** computes token self-information with a small causal LM, sums it over tokens, noun phrases, or sentences, and deletes low-information units by percentile. At 50% phrase-level reduction, averaged BERTScore F1 fell from .909 to .887 and ROUGE-1 from .571 to .449 relative to full-context-generated references; manual QA analysis reported .038 unfaithfulness. One Vicuna-13B example showed 36% lower inference memory and 32% lower time. The evaluation mainly measures similarity to outputs from the full context, not correctness against independent gold answers. Evidence: original authors' automatic, manual, and case-study evaluation, EMNLP 2023. [Primary paper](https://arxiv.org/html/2310.06201); [publication record](https://aclanthology.org/2023.emnlp-main.391/).

- **“RECOMP: Improving Retrieval-Augmented LMs with Compression and Selective Augmentation” (2023 preprint; 2024 publication title uses “Context Compression”)** trains a Contriever-based sentence selector or a T5-large query-focused abstractive summarizer. The abstractive compressor can return an empty summary for selective augmentation; the extractive experiments used a fixed number of selected sentences. With Flan-UL2, full five-document NQ context used 660 tokens and scored 39.39 EM; the abstractive compressor used 36 tokens and scored 37.04. TriviaQA went from 677 tokens/62.37 EM to 32/58.68, while HotpotQA went from 684/32.80 to 64/28.20. Extractive compression was better on multi-hop HotpotQA. Evidence: original authors' QA and language-modeling tables plus small manual faithfulness study, ICLR 2024. [Primary paper](https://arxiv.org/html/2310.04408); [publication record](https://openreview.net/forum?id=mlJLVigNHp).

#### Learned soft prompts and compressed tokens

- **“Adapting Language Models to Compress Contexts” (AutoCompressors, 2023)** fine-tunes OPT or Llama-2 to emit summary vectors, processes long documents in segments, and accumulates those vectors as soft prompts; 2,048 text tokens can become 50 summary vectors. Summary vectors improved perplexity relative to no long context and beat 150-token plain demonstrations on 8 of 11 ICL tasks, but extended full attention outperformed them with longer contexts. The authors also report worse zero-shot accuracy on some tasks after Llama-2 adaptation, which they attribute to fine-tuning-domain mismatch. Evidence: original authors' language-modeling, ICL, retrieval, and ablation results, EMNLP 2023; this is model adaptation, not black-box prompt shortening. [Primary paper](https://arxiv.org/html/2305.14788); [publication record](https://aclanthology.org/2023.emnlp-main.232/).

- **“In-context Autoencoder for Context Compression in a Large Language Model” (ICAE, 2024)** uses a LoRA-adapted LLM encoder and the fixed target LLM as decoder, pretraining 128 memory slots with autoencoding and text continuation before instruction tuning. At 512-to-128-token compression, normal-text BLEU was 99.3 but completely random text scored 0.2; continuation perplexity worsened from 9.01 with source context to 9.50 with memory slots. On the authors' PwC test, Llama-2-7B-chat with 128 slots won 19.6%, lost 45.4%, and tied 35.0% against the same model with original context under GPT-4 judging. Near-perfect BLEU therefore coexists with clear task and reconstruction loss. Evidence: original authors' reconstruction, continuation, GPT-4-judged, and latency evaluations, ICLR 2024. [Primary paper](https://arxiv.org/html/2307.06945); [publication record](https://openreview.net/forum?id=uREj4ZuGJE).

- **“Learning to Compress Prompts with Gist Tokens” (2023)** instruction-tunes a model with gist tokens and attention masks that prevent the input and output from attending to the original instruction; cached gist activations replace that instruction at compression rates up to 26x. One-token LLaMA-7B gisting reached a 49.7% ChatGPT win rate against the uncompressed control on unseen Alpaca+ prompts and 45.8% on the human OOD split; exact output matches fell from nearly 50% on seen tasks to about 20–25% unseen and 10% OOD. Against full instruction caching, the LLaMA benefit was only 0.11% fewer FLOPs and 1% lower wall time, although storage falls sharply. Documented failures include losing verbatim label constraints and runaway generations. Evidence: original authors' automatic, ChatGPT, human, exact-match, and profiling results, NeurIPS 2023. [Primary paper](https://arxiv.org/html/2304.08467); [publication record](https://openreview.net/forum?id=2DtxPCL3T5).

- **“Prompt Compression and Contrastive Conditioning for Controllability and Toxicity Reduction in Language Models” (2022)** optimizes a soft prompt for each hard prompt by minimizing KL divergence between their continuation distributions. Reading-comprehension experiments show that general questions degrade less than questions about specific details as compression increases; reconstruction likewise loses fine-grained content. A roughly 900-token toxicity context could sometimes collapse to one soft token while retaining steering utility, but this is evidence about abstract attributes, not preservation of arbitrary facts. Each prompt required about 1–4 GPU-hours of optimization, and experiments used GPT-2 models up to 1.5B. Evidence: original authors' GPT-2 distribution, reading, reconstruction, and RealToxicityPrompts experiments, Findings of EMNLP 2022. [Primary paper](https://arxiv.org/html/2210.03162); [publication record](https://aclanthology.org/2022.findings-emnlp.412/).

#### Summary and context distillation

- **“Learning by Distilling Context” (2022)** fine-tunes the student to produce the teacher's final answer without the teacher's detailed instructions, examples, or scratchpad; it internalizes context in model weights rather than creating a reusable compressed prompt. On Natural-Instructions-V2, student ROUGE-L rose from 9.0 to 34.7 versus 43.4 for the teacher while using 11.1x fewer inference tokens. On SPIDER, distilled students scored 22.1 and 27.9 exact-set match with four and eight examples versus 13.4 and 18.9 for direct gradient descent; the teachers scored 27.7 and 28.2. Evidence: original authors' task-specific training experiments, arXiv preprint; remaining gaps from the teacher and the need to modify the model limit its use as a drop-in compression mechanism. [Primary paper](https://arxiv.org/html/2209.15189).

### Inferences
- For black-box APIs and inspectable text, hard extraction or summarization is the applicable family. Soft prompts require model-specific representations or retraining and should be evaluated as a model/architecture change, not as a portable prompt edit.
- Query-aware compression spends compute per query but can retain task-critical evidence. Query-agnostic compression is cacheable across queries but must preserve enough information for unknown future uses.
- “Faithful,” “semantic,” and “near-lossless” are not synonyms for lossless. Extractive methods avoid introducing new words; they still discard source information.
- Token savings alone overstate system savings. Compressor inference, repeated per-query work, training, cached-vector storage, source storage, and optimized serving can dominate the result.
- Cross-paper compression ratios are not directly comparable when original prompt length, target model, task, metric, and allowed distortion differ.

### Gaps
- The original papers do not share one definition of preserved accuracy: some use gold-task metrics, some similarity to full-context outputs, some LLM preferences, and some reconstruction scores.
- The soft-prompt results do not establish compatibility with an untouched arbitrary LLM or with current production models.
- No cited original study demonstrates that a finite set of benchmark wins implies preservation on rare, safety-critical, or unseen queries.

## Which tasks and datasets were used, and what limits or generalization concerns apply?

### Takeaway
Evaluation regimes are highly heterogeneous, so they cannot support a simple global ranking. Long noisy contexts, multi-hop reasoning, exact structure, and detail-heavy tasks are recurrent failure points; summarization is often more tolerant because its target already discards detail.

### Cited Findings

#### Original evaluation map

| Method | Tasks, datasets, and target models | Generalization limits stated or visible in the design |
|---|---|---|
| LLMLingua (2023) | GSM8K and BBH for reasoning/ICL; ShareGPT conversation; Arxiv-March23 summarization; GPT-3.5-Turbo-0301 and Claude-v1.3. [Source](https://arxiv.org/html/2310.05736) | Claude was tested only under two GSM8K budget constraints. BBH degraded much more than GSM8K at high ratios, and compressed text can be disfluent. [Source](https://arxiv.org/html/2310.05736) |
| LongLLMLingua (2024) | NaturalQuestions 20-document QA, LongBench, ZeroSCROLLS, MuSiQue, and LooGLE; GPT-3.5-Turbo and LongChat-13B-16k. [Source](https://arxiv.org/html/2310.06839) | Results combine retrieval, reordering, dynamic budgets, pruning, and recovery. Ablations show that removing question awareness sharply reduces NQ performance, so gains should not be assigned to generic token entropy alone. [Source](https://arxiv.org/html/2310.06839) |
| LLMLingua-2 (2024) | MeetingBank in-domain QA/summarization; LongBench, ZeroSCROLLS, GSM8K, and BBH out-of-domain; GPT-3.5-Turbo and Mistral-7B. [Source](https://arxiv.org/html/2403.12968v2) | The compressor was trained only on MeetingBank meeting transcripts; its QA benchmark questions were GPT-4-generated. The authors explicitly acknowledge domain-generalization concerns despite positive transfer results. [Source](https://arxiv.org/html/2403.12968v2) |
| Selective Context (2023) | Custom BBC News, arXiv, and ShareGPT sets; summarization, QA, reconstruction, and conversation; GPT-3.5, GPT-4, LLaMA, and Vicuna. [Source](https://arxiv.org/html/2310.06201) | Documents were capped at 2,048 tokens, and full-context outputs were the references. The authors note sensitivity to phrase boundaries and task/context-dependent optimal thresholds. [Source](https://arxiv.org/html/2310.06201) |
| RECOMP (2023/2024) | WikiText-103 language modeling; NQ, TriviaQA, and HotpotQA; GPT-2/GPT-2-XL/GPT-J and Flan-UL2, with transfer tests to LLaMA-13B. [Source](https://arxiv.org/html/2310.04408) | Separate compressors were trained per QA dataset. HotpotQA used 500 development examples and abstractive training only for the 56% of training cases where gold appeared in retrieved documents; cross-LM QA transfer was weaker. [Source](https://arxiv.org/html/2310.04408) |
| AutoCompressors (2023) | Pile/Books3/Gutenberg and RedPajama language modeling; 11 classification/multiple-choice ICL datasets; retrieval-augmented LM and passage reranking; OPT and Llama-2. [Source](https://arxiv.org/html/2305.14788) | Requires substantial fine-tuning and summary-vector caching. Full attention was stronger with longer plain-text context, and fine-tuning hurt some zero-shot tasks; cached half-precision summaries for each 10B-token retrieval domain required about 5 TB. [Source](https://arxiv.org/html/2305.14788) |
| ICAE (2024) | Pile pretraining; GPT-4-assisted PwC instruction data with 240k training and 18k test samples; Llama-1/2 models from 7B to 13B. [Source](https://arxiv.org/html/2307.06945) | PwC is authors-constructed, response quality was GPT-4-judged, and experiments stopped at 13B. Random text and smaller memory budgets exposed sharp reconstruction loss. [Source](https://arxiv.org/html/2307.06945) |
| Gist tokens (2023) | Alpaca+ (130,321 examples) with Seen, Unseen, and 252 Human prompts; LLaMA-7B and FLAN-T5-XXL. [Source](https://arxiv.org/html/2304.08467) | Human evaluation covered 100 examples with three annotators. OOD quality and exact-match rates fell, FLAN-T5 was weaker OOD, and each architecture needs gist-specific tuning and masks. [Source](https://arxiv.org/html/2304.08467) |
| Wingate et al. (2022) | Pile-sampled prompts, a constructed reading/reconstruction task, and 2,000 RealToxicityPrompts; GPT-2 family up to 1.5B. [Source](https://arxiv.org/html/2210.03162) | Per-prompt optimization is expensive, and the main application is abstract steering/toxicity rather than general factual QA. [Source](https://arxiv.org/html/2210.03162) |
| Context distillation (2022) | Natural-Instructions-V2, SPIDER text-to-SQL, and synthetic 1-to-8-digit addition; T5/TK-Instruct and Incoder. [Source](https://arxiv.org/html/2209.15189) | Training is task- and template-specific and modifies model weights. Experiments show successful internalization, not a task-agnostic compressor or guaranteed retention of source evidence. [Source](https://arxiv.org/html/2209.15189) |

#### Independent generalization evidence

- **“Characterizing Prompt Compression Methods for Long Context Inference” (2024)** evaluates nine LongBench datasets across single-document QA, multi-document QA, and summarization using GPT-3.5-Turbo, Mixtral-8x7B, and DBRX. A chunk reranker often outperformed LongLLMLingua and abstractive summarization; examples included 7.75x compression with a 7.89-point F1 gain on 2WikiMultihopQA. LongLLMLingua variants were typically weakest in this setup, while query-aware summaries beat query-agnostic ones by 3–6 points on several QA datasets. Evidence: independent UC Berkeley ICML 2024 workshop comparison; it tests 128-token chunking and does not evaluate the original trained RECOMP, LLMLingua-2, gist, AutoCompressor, or ICAE systems. [Primary paper](https://arxiv.org/html/2407.08892v1).

- **“Understanding and Improving Information Preservation in Prompt Compression for LLMs” (2025)** tests LLMLingua and xRAG with the same Mistral-7B target on HotpotQA, QuAC, TriviaQA, arXiv summarization, and GSM8K, with contexts from about 850 to 6.5K tokens. LLMLingua dropped from .664 to .306 EM on HotpotQA and from .477 to .305 on GSM8K; both were only about 4% below baseline in relative BERTScore on arXiv summarization. On GSM8K, compressed demonstrations were worse than no demonstrations (.440). Evidence: independent downstream, FABLES grounding, reconstruction, and entity-preservation evaluation, Findings of EMNLP 2025. [Primary paper](https://arxiv.org/html/2503.19114v1); [publication record](https://aclanthology.org/2025.findings-emnlp.949/).

- **“Prompt Compression in the Wild: Measuring Latency, Rate Adherence, and Quality for Faster LLM Inference” (2026)** reports over 30,000 end-to-end experiments with LLMLingua variants, prompt lengths from 100 to 50,000 tokens, ratios from 1.5x to 5x, open models from 7B to 70B, proprietary APIs, and three hardware classes. Summarization stayed robust up to 5.7x in its setup, but Passage Counting fell from below 20% to below 4.5%, passage retrieval lost paragraph-number structure, and TREC/LSHT-ZH few-shot classification dropped by up to 52%. Compression sometimes helped Mistral by avoiding truncation, while longer-window models lost accuracy. Evidence: large independent arXiv preprint, not yet peer-reviewed; the authors also find little or no net speedup in several optimized-serving and API configurations. [Primary paper](https://arxiv.org/html/2604.02985v1).

### Inferences
- Accuracy gains after compression can come from denoising, better document order, or avoiding context-window truncation. They do not demonstrate that the discarded information was preserved.
- Multi-hop QA, structured synthetic tasks, exact class labels, code, and demonstrations need targeted tests; success on summarization or single-document QA is insufficient evidence for them.
- A fair local evaluation should vary ratio and prompt length, include the actual target model and serving stack, and compare against zero-shot, retrieval/reranking, full-context, and no-compression controls.
- Task-agnostic compression is attractive for offline reuse, while query-aware compression may need to be recomputed and cannot be treated as one canonical compressed document for all future questions.
- A later target-model or tokenizer change can invalidate previously measured soft-prompt compatibility and hard-prompt token budgets.

### Gaps
- No cited benchmark evaluates all requested methods under one target model, training budget, source set, ratio sweep, and metric suite.
- Coverage of non-English language, code structure, adversarial inputs, rare entities, and current frontier models remains thin and inconsistent.
- Several original studies provide limited confidence intervals or rely on LLM judges and small human samples, making small “preserved accuracy” differences uncertain.

## When is compression lossless versus lossy, and when should source evidence remain available on demand?

### Takeaway
None of the surveyed methods establishes general lossless compression of arbitrary prompts or model behavior. “Lossless” is defensible only for an explicitly bounded operational criterion and tested operating point; source evidence should remain retrievable whenever exact details, provenance, auditability, or unanswered future queries matter.

### Cited Findings

#### Evidence about distortion and information loss

- **“Fundamental Limits of Prompt Compression: A Rate-Distortion Framework for Black-Box Language Models” (2024)** formalizes rate as compressed/original length and distortion as task-output error under log, 0/1, or semantic losses. It derives optimal query-aware and query-agnostic distortion-rate curves and finds existing methods far from the theoretical limit on synthetic and small natural-language data; query awareness materially improves the trade-off. Evidence: NeurIPS 2024 theory plus controlled experiments, not a proof of a universal numeric limit for arbitrary natural-language deployments. [Primary paper](https://arxiv.org/html/2407.15504); [publication record](https://openreview.net/forum?id=ecmrk5PEjy).

- Wingate et al. directly show that soft compression preferentially retains general themes while specific-question accuracy and reconstruction degrade. ICAE similarly reaches 99.3 BLEU on normal text but 3.5 on patterned random text and 0.2 on completely random text at 4x, demonstrating that redundancy and predictability determine what can be preserved. Evidence: original controlled reading/reconstruction and content-type experiments. [Wingate et al., 2022](https://arxiv.org/html/2210.03162); [ICAE, 2024](https://arxiv.org/html/2307.06945).

- Gist models' exact outputs matched the uncompressed control nearly 50% of the time for seen tasks but only about 20–25% for unseen tasks and 10% for OOD human tasks. Even when preference scores look comparable, behavioral equivalence is not exact. [Mu et al., 2023](https://arxiv.org/html/2304.08467).

- In the 2025 information-preservation study, xRAG reconstruction averaged 0.66 BERTScore and retained only 28% of entities on unseen one-token-per-sample inputs. LLMLingua answers were more grounded than xRAG in several settings but still lost task accuracy, showing the difference between verbatim retention of selected spans and preservation of the whole evidence set. [Łajewska et al., 2025](https://arxiv.org/html/2503.19114v1).

- LongLLMLingua's subsequence recovery explicitly consults the original prompt to replace compressed entity fragments in generated responses. This is a direct implementation example where retaining source text is part of restoring exact surface information rather than treating compressed text as the sole record. [Jiang et al., 2024](https://arxiv.org/html/2310.06839).

#### Evidence relevant to source-on-demand designs

- RECOMP's manual analysis of 30 non-empty summaries per dataset found its abstractive compressor's “useful” rate (faithful and comprehensive) was 80% on NQ, 77% on TriviaQA, and 40% on HotpotQA; 33% of HotpotQA summaries were rated unfaithful. Abstractive compression therefore needs source fallback for verification, especially for multi-hop evidence. The sample is small and author-annotated. [Xu et al., 2023/2024](https://arxiv.org/html/2310.04408).

- The 2025 study argues that downstream performance alone is insufficient and separately measures response grounding and source reconstruction/entity retention. This supplies primary evidence for evaluating compressed prompts as evidence containers, not merely as accuracy optimizers. [Łajewska et al., 2025](https://arxiv.org/html/2503.19114v1).

- The 2026 deployment study found that LLMLingua-2 can remove paragraph numbering and class-indicative patterns even when summarization remains stable. A task that requires exact structure therefore cannot infer safety from aggregate QA or summarization results. [Kummer et al., 2026](https://arxiv.org/html/2604.02985v1).

### Inferences
- Use three distinct meanings of “lossless”: **reversible** means exact source recovery; **behavior-equivalent** means the target model's output distribution is unchanged under a stated distortion; **task-equivalent** means a specified gold metric is statistically unchanged on a stated distribution. Extractive compression can additionally be **span-faithful** for retained words while remaining lossy about omitted evidence.
- Compression may be task-equivalent at one ratio, model, query set, and tolerance when it removes only irrelevant redundancy. It can even improve a score through denoising or truncation avoidance without being reversible or behavior-equivalent.
- Keep an immutable original plus document IDs, offsets, and compressed-span mappings when handling citations, legal/compliance evidence, exact names/numbers/code, structured records, multi-hop facts, conflicting sources, or high-impact decisions. Retrieve the original on demand rather than asking the compressed representation to regenerate it.
- Source fallback is especially important for abstractive summaries, soft vectors, and weight-level distillation because users cannot directly inspect all retained content. Reconstruction from the compressed form is not a substitute for the original, since plausible hallucinations can score well on semantic similarity.
- A practical gate should test gold-task quality, grounding, exact/entity preservation, and total latency. Low grounding, failed structural checks, novel queries, or disagreement among compressed sources should trigger original-context retrieval.

### Gaps
- The rate-distortion work does not supply a general natural-language certificate that a chosen deployed compressor is lossless at a particular ratio.
- There is no accepted metric that proves semantic equivalence for every downstream task; BLEU, ROUGE, BERTScore, preference judging, and task EM measure different distortions.
- The scoped primary sources do not directly compare source-on-demand fallback architectures or quantify their extra latency against always-compressed operation.

## Which findings are replicated versus single studies or vendor claims?

### Takeaway
Independent work converges on qualitative conclusions: detail loss is real, task/query awareness helps, and robustness varies sharply by task and deployment. Exact headline ratios, speedups, and several soft-prompt quality claims remain primarily original-team results, with only partial or setting-specific independent comparisons.

### Cited Findings

#### Independent and convergent evidence

- The 2024 UC Berkeley comparison independently challenges LongLLMLingua's original ranking by finding reranker-based extraction generally stronger and LongLLMLingua variants generally weaker across its nine LongBench datasets. This is one independent workshop study with a different compressor and chunking setup, not a direct refutation of every original data point. [Jha et al., 2024](https://arxiv.org/html/2407.08892v1); [original LongLLMLingua study](https://aclanthology.org/2024.acl-long.91/).

- The 2025 Findings of EMNLP study includes a baseline reproducibility check and then evaluates LLMLingua on new task/model combinations. It independently reproduces the broad possibility of compression but finds 3–55% relative downstream losses, severe HotpotQA degradation, worse-than-no-demo GSM8K behavior, and reduced grounding. This is stronger evidence than a vendor page, but it covers LLMLingua and xRAG rather than every requested method. [Łajewska et al., 2025](https://arxiv.org/html/2503.19114v1).

- The 2024 rate-distortion paper independently gives theoretical and empirical support for query-aware compression and shows a substantial gap between existing hard-prompt methods and the computed optimum. It converges with LongLLMLingua, RECOMP, and the 2024 comparison's query-aware summarization results, but uses different tasks and does not replicate their exact numbers. [Nagle et al., 2024](https://arxiv.org/html/2407.15504).

- The 2026 “Prompt Compression in the Wild” preprint independently supports robust summarization and variable QA outcomes while finding severe structured/few-shot failures and hardware-dependent speedups. Its detailed conclusion reports no substantial non-batched end-to-end gain in several optimized settings, in contrast to large speedups reported on the original V100 setups. Treat it as broad but not yet peer-reviewed evidence. [Kummer et al., 2026](https://arxiv.org/html/2604.02985v1); [original LLMLingua latency setup](https://arxiv.org/html/2310.05736); [original LLMLingua-2 latency setup](https://arxiv.org/html/2403.12968v2).

- **“Large Language Model as Token Compressor and Decompressor” (2026)** evaluates AutoCompressor, Gist Token, and ICAE baselines on Qwen models under its unified setup. At 4x reconstruction, their BLEU scores were 96.44, 96.29, and 98.45 respectively; at 8x they were 92.67, 94.63, and 93.44. On CNN/DailyMail, all three scored below the uncompressed Qwen3-0.6B baseline in ROUGE-1/2/L. This is useful independent comparison evidence but a single preprint promoting a new method, not a replication of the original models or datasets. Its speedup statements also vary across sections, so those claims should not be reused without checking the tables. [Li et al., 2026](https://arxiv.org/html/2603.25340v1).

#### Original-team results, reused numbers, and convergent patterns

- LLMLingua, LongLLMLingua, and LLMLingua-2 are closely related Microsoft research efforts. LLMLingua-2 marks several LongLLMLingua, LLMLingua, and Selective Context table entries with a dagger and states that those numbers were reported by the earlier papers; these are reused baselines, not new independent replications. [LLMLingua-2 tables and notes](https://arxiv.org/html/2403.12968v2); [LLMLingua](https://aclanthology.org/2023.emnlp-main.825/); [LongLLMLingua](https://aclanthology.org/2024.acl-long.91/).

- **Detail loss is independently convergent.** Wingate reports loss of fine-grained information, gist documents lost constraints and falling exact matches, RECOMP finds worse multi-hop summarization/faithfulness, and the 2025 and 2026 independent studies find entity, structure, and grounding losses. This is a robust qualitative finding across different methods, not evidence of one shared degradation rate. [Wingate et al., 2022](https://arxiv.org/html/2210.03162); [Mu et al., 2023](https://arxiv.org/html/2304.08467); [Xu et al., 2023/2024](https://arxiv.org/html/2310.04408); [Łajewska et al., 2025](https://arxiv.org/html/2503.19114v1); [Kummer et al., 2026](https://arxiv.org/html/2604.02985v1).

- **Query/task awareness is independently convergent.** LongLLMLingua's ablations, RECOMP's query-focused training, the 2024 comparison's query-aware summaries, and Adaptive QuerySelect all support using downstream query information when per-query cost is acceptable. They do not prove that query-aware compression is preferable when one compressed artifact must serve many unknown queries. [LongLLMLingua](https://arxiv.org/html/2310.06839); [RECOMP](https://arxiv.org/html/2310.04408); [Jha et al., 2024](https://arxiv.org/html/2407.08892v1); [Nagle et al., 2024](https://arxiv.org/html/2407.15504).

- **Summarization robustness is repeated but conditional.** Selective Context reports tolerable degradation at modest pruning, the 2025 study finds only about 4% relative arXiv-summary loss for LLMLingua/xRAG, and the 2026 preprint finds stable summarization at some high ratios. These results use different metrics and do not protect fact-dense summaries, citation completeness, or structured QA. [Selective Context](https://arxiv.org/html/2310.06201); [Łajewska et al., 2025](https://arxiv.org/html/2503.19114v1); [Kummer et al., 2026](https://arxiv.org/html/2604.02985v1).

- Microsoft Research and project repositories are useful for code and configuration, but their performance statements are author/project claims or restatements of the associated papers, not independent replication. For example, the LongLLMLingua project page repeats the NaturalQuestions and latency claims from the ACL paper. [Microsoft project page](https://www.microsoft.com/en-us/research/project/llmlingua/longllmlingua); [ACL paper](https://aclanthology.org/2024.acl-long.91/); [Selective Context repository](https://github.com/liyucheng09/Selective_Context).

### Inferences
- **Stronger evidence:** compression is lossy in task-relevant ways; fine detail and structure are vulnerable; query awareness often improves rate/distortion; local task and model choice change the outcome.
- **Moderate evidence:** coarse extraction/reranking is a strong RAG baseline, and summarization often tolerates more compression than detail-heavy QA. Generality remains bounded by the small number of independent task suites.
- **Weaker or unsettled evidence:** universal 10x/20x “no-loss” claims, exact latency multipliers, broad cross-model soft-token compatibility, and any single method's superiority across domains.
- Peer review establishes a publication review process, not independent replication. Conversely, an independent preprint can provide useful contradiction or confirmation but should be labeled by that maturity level.
- Report original and independent results side by side when they conflict, including compressor model, chunking, target model, ratio, metric, and whether numbers were reused.

### Gaps
- In the scoped search, I found no independent exact replication of Gist's original human evaluation, ICAE's PwC evaluation, AutoCompressors' 11-task ICL study, or RECOMP's trained-compressor results on the same models and datasets. This is a search result, not proof that no such work exists.
- No independent study covers all soft and hard methods with identical source data and controls; the 2025 soft/hard comparison uses xRAG and LLMLingua, not ICAE, AutoCompressors, or Gist.
- The 2026 papers are preprints, and the Z-token paper's baseline implementation and internal reporting need further scrutiny before treating its numbers as settled replication evidence.
- Current-model, multilingual, adversarial, code/structure-sensitive, and high-stakes evidence remains insufficient for broad production guarantees.
- This was a targeted primary-source review through 26 October 2026, not an exhaustive systematic-review protocol with citation-graph snowballing and formal risk-of-bias scoring.
