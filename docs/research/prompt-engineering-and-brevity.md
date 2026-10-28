<a id="prompt-agent-design-research"></a>

# Designing reliable prompts and agents: evidence and architecture

[Used by Senior Review](../plugins/senior-review.md) · [Context-building research](context-building-research.md)

*Last substantive update: 2026-10-28. The operational recommendations below were
revised; no new literature search or behavioral experiment was performed.*

## Abstract

Building reliable agents, skills and prompts requires more than writing each
document clearly: it also requires organizing all the instructions a model
receives and retains throughout its work. We propose identifying obligations,
clarifying their priority and applicability, reducing unnecessary instruction
load, and making rules available before the actions they govern. Every
reorganization should preserve obligations, checks and prohibitions, verifying
both their presence and their effect in the new context. Structure, concision
and verbatim preservation are useful tools, not guarantees. Effectiveness should
be assessed through before-and-after comparisons and external checks on results,
including on the low-cost models intended for actual use. These are operational
recommendations to validate on the relevant models and tasks, not a promise of
universal reliability.

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

### 3. Operational application: making the principles executable

These five practices are operational recommendations, not universally validated
results. Structured templates, numbered procedures and MUST/MUST NOT lists can
improve clarity; their form alone does not establish compliance.

1. **Inventory before editing.** Register every obligation (directives, checks,
   exceptions, stop conditions) with stable ID, verbatim text, hash, source
   anchor, applicability and precedence. Audit coverage: preservation checks
   apply to the registered inventory, while undiscovered obligations remain a
   residual risk. Start as an index over existing sources; make it authoritative
   only after auditing coverage and checking the wording and activation of all
   required instructions in each applicable context.
2. **Account composition statically.** Build the declared load graph (skills,
   references, dispatched roles) without running workflows or agents. Account
   for the retained load per executor and phase, including repeated instructions
   and retained history; isolated agents have separate contexts. Static analysis
   covers declared loads, not necessarily dynamically retrieved content or tool
   output. Keep unresolved loads explicitly unknown, never zero. Constraint
   counts and rendered volume are diagnostics, not proof of compliance;
   splitting or merging rules must remain visible in the inventory comparison.
3. **Load lazily by applicability, not by convenience.** Defer a reference only
   if its obligations begin at that phase; otherwise extract the normative part
   into the earlier active set. Lazy loading is a semantic migration, not a
   plumbing change: it alters when rules become available.
4. **Preserve verbatim first.** One canonical owner per obligation, but as many
   deliveries as separate model contexts require. Identical wording does not
   guarantee identical behavior after changes to timing, priority or context.
   Review authoritative paraphrases separately, with old-to-new mappings and
   declared residual risk. Text checks and finite behavioral tests do not, by
   themselves, prove general semantic equivalence.
5. **Introduce checks incrementally and evaluate before and after.** Begin with
   reporting, then consider limits on load growth. A baseline describes the
   existing state; it does not establish an effective absolute threshold. Set
   limits against task outcomes and observed compliance, not counts alone.
   Use frozen old/new fixtures and external grading of results and tool traces,
   including on the intended low-cost models. Keep deterministic structural
   checks distinct from probabilistic behavioral evaluations. Results provide
   bounded regression evidence for the tested models and cases, not an
   equivalence proof or a guarantee for other models.

## Illustrative case and evidence limits

A preliminary inspection of one instruction marketplace reported a median role
of 42 lines and 3 rule markers. One illustrative eight-file composition was
estimated at about 5,300 tokens and 35 rule markers before project context.
These were exploratory counts: rule markers are lexical matches, not verified
independent constraints, and the token figure was an estimate rather than a
tokenizer measurement or an observation of the actual runtime context.

Internal model discussions critically reviewed these observations and the
proposed method; they did not independently validate the measurements or the
recommendations. This case motivates further evaluation, not a claim of
general effectiveness. The abstract and operational guidance do not depend on
these figures.

## Changelog

### 2026-10-28

Added a standalone operational abstract in English, separated the illustrative
case from the general guidance, and qualified the preservation and evaluation
claims. Existing literature references and findings remain unchanged.

- Superseded ~~fixed MUST/MUST NOT skeletons cannot contain procedures, output
  contracts and stop conditions~~: structured formats can help, but are not
  sufficient evidence of compliance.
- Superseded ~~"no rule lost" is provable only against a complete, human-audited
  register of obligations~~: preservation is auditable relative to the registered
  inventory, with residual risk from omissions and contextual changes.
- Superseded ~~mechanical equivalence proofs for paraphrase do not exist~~:
  text checks and finite behavioral tests alone do not prove general semantic
  equivalence.
- Superseded ~~absolute thresholds derive from rendered baselines, not from
  token conversion~~: baselines and volume measurements inform evaluation;
  effective limits require evidence from the relevant tasks and models.
