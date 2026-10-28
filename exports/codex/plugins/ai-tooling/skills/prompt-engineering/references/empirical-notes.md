<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Empirical Measurements Behind the Role Digest

On-demand reference for `ai-tooling:prompt-engineer` and `ai-tooling:prompt-engineering`. Contains the detailed benchmark breakdowns, sample sizes, and per-model curves summarized in the role's design and anti-pattern rules. Every figure is **measured** on the named model and benchmark and **predicted** on any other target until evaluated.

## 1. Persona and Ideation Effects

- **Persona vs accuracy (arXiv 2605.29420 v1, older non-reasoning class):** On GPT-4o-mini over 1,140 open-ended questions, a generic expert role left accuracy unchanged (4.054 vs 4.052 on a 5-point scale), raised expertise depth by +0.185, and lowered clarity by -0.180. A role steers depth and style, not accuracy.
- **Heterogeneous personas for ideation (arXiv 2602.20408 v1):** Across independent samples on GPT-4o, heterogeneous ordinary personas raised unique idea combinations from 39.15 to 56.97 (vs 50.40 for a single expert persona). Within a single persona session, the exploration rate declines over successive ideas; rotate perspectives between batches.

## 2. Few-Shot Calibration, Delimiters, and Exemplar Retrieval

- **Reasoning traces in exemplars (arXiv 2509.23196):** Few-shot CoT often underperforms direct answering on RL-trained reasoners, and adding more worked traces degrades further; distilling traces into explicit instruction insights recovered +14.0% on AIME'25 for GPT-4.1.
- **Delimiter sensitivity (arXiv 2510.05152):** Changing the delimiter between few-shot examples alone moved MMLU accuracy by up to 23 points and reordered model rankings across Llama, Qwen, and Gemma at every scale. Pin the delimiter explicitly and keep it constant.
- **Shot-count non-monotonicity (arXiv 2607.22969 v1, AG News, n=200):** Llama-3.1-8B went from 0.525 macro-F1 zero-shot to 0.866 at 2 shots and back to 0.553 at 8 shots; Llama-4-Scout was best zero-shot (0.877) and lost 0.18 at 1 shot; GPT-4o-mini's gain up to 8 shots was not statistically significant. Sweep 0, 1, 2, and 8 shots rather than picking a fixed count.
- **Similarity-based retrieval (arXiv 2506.05614):** Across 10 software-engineering tasks, nearest-neighbour exemplar retrieval gave the most consistent gains (code translation CodeBLEU 30.19 -> 42.08, assert generation BLEU 25.24 -> 65.44). Random exemplars do not reproduce this gain.

## 3. Prompt Syntax and Rule Ordering

- **Format sensitivity (arXiv 2608.21074 v1; arXiv 2508.11383):** On GPT-4o HumanEval (8,200 runs), JSON scored 0.901 vs 0.886 plain, Markdown 0.890, YAML 0.873, and an LLM-rewritten "optimized" prompt 0.748. Across 52 Natural Instructions tasks, semantically equivalent format changes moved Llama-3.1-8B by a 0.161 accuracy spread and Qwen2.5-7B by 0.190 (vs 0.032 on GPT-4.1).
- **Rule order and priority encoding (arXiv 2608.12426; ManyIH-Bench, arXiv 2604.09443):** Over 1 to 12 non-conflicting constraints, rule order had near-zero effect on compliance (mean absolute Spearman correlation ~0.03). However, relabelling priority tiers from ordinal to numeric moved GPT-5.4 by 8.4 points and Opus 4.6 by 8.0 points.

## 4. Compositional Constraint Saturation

- **Multiplicative decay (arXiv 2608.12426 v1, 36 constraint types, 369,753 checks):** The smallest constraint count at which all-constraints joint success fell below 50% (compositional half-life) was:
  - 7 for GPT-5.5
  - 6 for Claude 4.7 Opus
  - 4 for Gemini 3.1 Pro
  - 3 for Claude 4.6 Opus, GPT-5.4 Pro, and DeepSeek-V4-Pro
  - 2 for GPT-5.2 (12 of 15 tested models crossed 50% by 3 constraints)
  At 8 constraints, per-constraint accuracy remained ~40.7% while all-8 joint success fell to 5.7% (each added constraint multiplied survival by ~0.922 on the fitted mean curve; structural constraints decayed ~2x faster than lexical ones).
- **Earlier generation comparison (arXiv 2509.21051, EMNLP 2025):** Gemini-1.5-Pro followed a characters-per-line rule 99% alone and 20% when composed with five others; Claude 3.5 dropped from 97% to 2%.
- **Working synthesis:** Zero to three constraints: normal; four to five, add a verifier; above five simultaneously verifiable constraints: split into stages or verify and retry, unless a target-model eval shows otherwise. Shape compliance (JSON validity) and domain correctness (e.g. totals matching line items, no omitted eligible records) are distinct predicates requiring separate validation rungs.

## 5. Context Rot, RAG Abstention, and Injection Defenses

- **Claude API context primitives:** Tool-result clearing (`clear_tool_uses_20250919`, default 100K input tokens, lossless for re-fetchable content, invalidates cached prefix), server-side compaction (`compact_20260112`, default 150K, min 50K, lossy), and client-side memory (`memory_20250818`). In the Anthropic cookbook, a research agent's 335,279-token peak dropped to ~173K with clearing or ~169K with compaction.
- **Abstention under conflicting/misleading context (Zhang & Wu, CMC 89(1), 2026-08; arXiv 2608.22228):** Assess-first prompting raised abstention under conflicting evidence from 0% to 47.9% on GPT-5.5 and from 5.2% to 55.2% on Gemini 2.5, but only from 7.2% to 11.2% on Claude Sonnet 4.6 (which notices the conflict and answers anyway; over-answering remained >65% in the worst condition, 90.5% on Claude). On small models, an abstention instruction still answered 41.6% of misleading-context questions, 63% copying the planted wrong entity.
- **Prompt injection mitigations (arXiv 2606.18530; arXiv 2505.18333; arXiv 2606.07808):** Paraphrasing cut camouflaged attack success by 55-84%; spotlighting halved it on Claude Haiku while having no effect on Llama-3.1-8B; adaptive attacks defeat static defenses and instruction hierarchy degrades in long contexts. Enforce architectural boundaries (untrusted tool output as data, isolated context for fetched content, least privilege, human confirmation before external sinks).

## 6. Language and Modality Ordering

- **Prompt language (arXiv 2607.14816 v1):** On GPT-4o-mini code generation, Python pass rate was 23.35% in English vs 23.91% in Italian, Java 32.78% vs 33.39%, and ClassEval 37 vs 33. Do not translate non-English prompts to English as a default optimization without a target-model measurement.
- **Modality ordering (Wardle & Susnjak, BDCC 9(6):149, 2025-06):** On GPT-4o, chemistry scored 0.32 text-first vs 0.72 interleaved, while economics reversed to 0.73 text-first vs 0.48 interleaved. Order modalities by reasoning dependency and label ordering claims as predicted on newer vision models.
