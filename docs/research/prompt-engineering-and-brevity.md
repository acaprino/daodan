<a id="prompt-agent-design-research"></a>

# Designing reliable prompts and agents: evidence and architecture

[Used by Senior Review](../plugins/senior-review.md) · [Context-building research](context-building-research.md)

## TL;DR

- **Core principle:** Design instructions and agents around observable evidence, authority boundaries, and independent verification, rather than imaginary personas or sprawling prose.
- **Length and complexity:** Adding constraints and instructions does not scale compliance linearly. As rules accumulate, joint compliance degrades (*ManyIFEval*, *FollowBench*).
- **Internal self-correction:** An LLM cannot self-correct complex reasoning without an oracle or external executable feedback (*Large Language Models Cannot Self-Correct Reasoning Yet*). Unanchored self-approval is a fallacy.
- **Chain of Thought (CoT):** The benefits of CoT concentrate on mathematics, logic, and symbolic manipulation; for code review and routine textual tasks, concise and structured responses achieve equivalent performance at substantially lower latency and cost (*To CoT or not to CoT?*).
- **Citation verification:** Claim correctness must bind to exact textual spans and verified sources (*ALCE*).

## Why we conducted the research

1. **Excessive verbosity and compliance degradation:** In multi-agent systems, instructions tend to accumulate redundant rules ("be accurate", "double-check", lengthy persona descriptions). Literature shows that every added constraint lowers accuracy across all other constraints. A strict discipline of conciseness and context economy was required.
2. **False positives in self-evaluation:** Many agent and review pipelines implemented "reflection" or "agent debate" loops hoping models would autonomously detect errors. It was necessary to empirically verify when self-feedback works (only with tests, compilers, or external verifiers) and when it merely produces overconfidence and billing overhead.
3. **Cost management and token economy:** Every token added to system instructions or conversational history is billed across every turn and tool invocation. Determining whether modular decomposition and concise completions preserve efficacy while slashing token usage by 30–50% was essential.

## Links to cited papers

### 1. Instructions, constraints, and context attention

| # | Paper | Link | Primary topic |
|---|---|---|---|
| 1 | Schulhoff et al. *The Prompt Report: A Systematic Survey of Prompt Engineering Techniques*. 2024. | [arXiv:2406.06608](https://arxiv.org/abs/2406.06608) | Systematic survey of prompt engineering techniques and their obsolescence boundaries. |
| 2 | Zhou et al. *Instruction-Following Evaluation for Large Language Models* (IFEval). 2023. | [arXiv:2311.07911](https://arxiv.org/abs/2311.07911) | Rigorous evaluation of verifiable constraints (strict/loose) without subjective grading. |
| 3 | Wang et al. *FollowBench: A Multi-level Fine-grained Constraints Following Benchmark*. ACL 2024. | [arXiv:2310.20410](https://arxiv.org/abs/2310.20410) | Demonstrates compliance degradation as concurrent constraints multiply. |
| 4 | Yin et al. *When Instructions Multiply: Measuring LLM Capabilities of Multiple Instructions Following*. 2025. | [arXiv:2509.21051](https://arxiv.org/abs/2509.21051) | ManyIFEval: sharp degradation of joint compliance with up to 10 instructions. |
| 5 | Wallace et al. *The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions*. 2024. | [arXiv:2404.13208](https://arxiv.org/abs/2404.13208) | Security separation and privilege hierarchy between system, user, and third-party data instructions. |
| 6 | Hsieh et al. *RULER: What’s the Real Context Size of Your Long-Context Language Models?*. 2024. | [arXiv:2404.06654](https://arxiv.org/abs/2404.06654) | Needle-in-a-haystack does not guarantee aggregation or multi-hop reasoning across long contexts. |
| 7 | Liu et al. *Lost in the Middle: How Language Models Use Long Contexts*. TACL 2024. | [arXiv:2307.03172](https://arxiv.org/abs/2307.03172) | Evidence of the U-shaped attention curve: attention drops on documents placed in the middle of context. |
| 8 | Bai et al. *LongBench: A Bilingual, Multitask Benchmark for Long Context Understanding*. ACL 2024. | [arXiv:2308.14508](https://arxiv.org/abs/2308.14508) | Bilingual benchmark demonstrating trade-offs between dense retrieval and long-context comprehension. |

### 2. Agents, reasoning, reflection, and verification

| # | Paper | Link | Primary topic |
|---|---|---|---|
| 9 | Yao et al. *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR 2023. | [arXiv:2210.03629](https://arxiv.org/abs/2210.03629) | Interactive action-observation loops grounding reasoning in environment feedback. |
| 10 | Shinn et al. *Reflexion: Language Agents with Verbal Reinforcement Learning*. NeurIPS 2023. | [arXiv:2303.11366](https://arxiv.org/abs/2303.11366) | Verbal memory and heuristics; effective only when environment feedback provides ground truth. |
| 11 | Madaan et al. *Self-Refine: Iterative Refinement with Self-Feedback*. NeurIPS 2023. | [arXiv:2303.17651](https://arxiv.org/abs/2303.17651) | Iterative refinement; beneficial for style and formatting, not for validating logical correctness. |
| 12 | Huang et al. *Large Language Models Cannot Self-Correct Reasoning Yet*. ICLR 2024. | [arXiv:2310.01798](https://arxiv.org/abs/2310.01798) | Proves self-correction without an external oracle is an illusion that frequently degrades output. |
| 13 | Dhuliawala et al. *Chain-of-Verification Reduces Hallucination in Large Language Models*. 2023. | [arXiv:2309.11495](https://arxiv.org/abs/2309.11495) | Hallucination reduction via factored verification questions. |
| 14 | Hong et al. *MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework*. ICLR 2024. | [arXiv:2308.00352](https://arxiv.org/abs/2308.00352) | SOP proceduralization and typed artifacts to prevent multi-agent communication overhead. |
| 15 | Liu et al. *AgentBench: Evaluating LLMs as Agents*. ICLR 2024. | [arXiv:2308.03688](https://arxiv.org/abs/2308.03688) | Multi-environment benchmark for agents; categorizing operational loop failures. |
| 16 | Spreafico et al. *To CoT or not to CoT? Chain-of-thought helps mainly on math and symbolic reasoning*. ICLR 2025. | [arXiv:2409.12183](https://arxiv.org/abs/2409.12183) | Meta-analysis across 110 papers: CoT is critical for math/symbols, largely negligible elsewhere. |
| 17 | Chen et al. *Chain of Draft: Thinking Faster by Writing Less*. 2025. | [arXiv:2502.18600](https://arxiv.org/abs/2502.18600) | Drastic reduction of reasoning tokens while preserving accuracy via concise draft reasoning. |
| 18 | Gao et al. *Enabling Large Language Models to Generate Text with Citations* (ALCE). EMNLP 2023. | [arXiv:2305.14627](https://arxiv.org/abs/2305.14627) | Decoupling response correctness from verifiable citation support. |

## Content summary and findings

### 1. Empirical rules for prompt design

1. **Verifiability over adjectives:** Constraints must be verifiable by mechanical tests or observable boolean conditions (e.g., "produce valid JSON with keys X and Y", rather than "be thorough and detailed").
2. **Instruction budgeting:** Every additional instruction incurs a penalty in joint compliance. Policy rules must remain minimal, concise, and non-contradictory.
3. **Strict separation between instructions and data:** External data (read files, tool outputs, user inputs) must be confined within delimited blocks and must never inject operational directives into the agent (*Instruction Hierarchy*).

### 2. Agent architecture and review loops

1. **Rejection of unanchored self-verification:** Never instruct an agent to "review its own response" without supplying fresh evidence (linter output, test outcome, search result). Without external grounding, models confirm their own hallucinations (*Huang et al.*).
2. **Closed loops on real tools (ReAct):** Agents must operate through dedicated tools with bounded, deterministic outputs, observe outcomes, and advance based on demonstrated evidence.
3. **Avoid verbose CoT when unnecessary:** For extraction, formatting, or translation tasks, demanding intermediate reasoning chains multiplies costs without improving semantic accuracy (*To CoT or not to CoT?*).
4. **Mandatory verifiable citations:** Any finding or verdict emitted during audit or review phases must cite the exact file and line number; lack of citation invalidates the finding (*ALCE*).
