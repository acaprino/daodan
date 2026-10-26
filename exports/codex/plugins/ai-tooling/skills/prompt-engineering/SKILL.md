---
name: prompt-engineering
description: >
  Design and improve model instructions using practical prompting foundations and model-aware guidance.
  TRIGGER WHEN: writing or reviewing prompts, system messages, examples, extraction or judge prompts, tool descriptions, skills or orchestrator briefs.
  DO NOT TRIGGER WHEN: implementing a Claude Agent SDK app (use agent-sdk-builder).
---

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
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

# Prompt engineering knowledge base

The `prompt-engineer` agent and the `/prompt-optimize` command carry the method: extract the
behavioral contract, classify the archetype, diagnose, rewrite, report the semantic diff, label
every claim predicted, measured or verified. This skill carries the knowledge the method draws
on, split into references that are read only when a task needs them. Read this file first; it
tells you which reference to open and what every reference assumes you already decided.

## Working baseline

Use these checks when the skill is invoked directly as well as through the role. They are
diagnostic questions, not sections every prompt must contain:

1. **Result:** name the task and the output the caller needs. Include audience, purpose and
   relevant background when they change the answer. Use supplied facts; do not invent a business
   policy, recipient or requirement to make a vague brief look complete.
2. **Procedure and collaboration:** distinguish output requirements from necessary task steps
   and interaction preferences. Ordered operations can be useful without requesting private
   reasoning. Keep intentional creative freedom and the original language.
3. **Contract:** preserve hard constraints, placeholders, interfaces and trust boundaries before
   optimizing wording. State a material assumption or ask for missing information when it would
   change the result. Report added requirements as behavioral changes.
4. **Inputs:** distinguish instructions, source material and examples. Use meaningful delimiters
   for mixed content; delimiters organize text but do not enforce trust or response validity.
5. **Demonstrations:** add reviewed input/output examples to address an identified failure or a
   genuinely ambiguous requirement. Choose the count after the model-class gate; examples are
   neither mandatory decoration nor a substitute for evidence.
6. **Evidence:** for source-bound tasks, specify usable sources and what to do when evidence is
   missing or conflicting. Never invent supporting quotes. A short evidence excerpt is an
   observable artifact, not a request for hidden reasoning.
7. **Feedback:** identify the actual discrepancy, choose a change that addresses it, and compare
   against the original on the same inputs. A rewrite without an eval is a prediction.

For a simple one-off, apply only the relevant checks and deliver the prompt. For a missing brief,
mixed inputs, source-grounded answers or an iterative evaluation, read
`references/prompting-foundations.md`. It adapts Claude Academy's Description framework and
prompting lessons, with original examples and explicit compatibility limits.

## Minimum intervention and generalization

Choose the smallest change that fixes an evidenced defect or a requirement the caller stated.
If neither exists, leave the prompt alone. The working baseline is not a mandate to add roles,
tags, examples, constraints, validators or extra calls. Each addition must earn its cost.

Do not turn one unusual failure into a universal rule. Keep a narrow fix provisional until it
holds on different, representative inputs without breaking ordinary cases. Separate examples
used for tuning from verification data, and inspect whether a grader rewards verbosity or a
format shortcut instead of the intended result. Never claim general reliability from a
handpicked demonstration, a self-assigned score or a case already shown in the prompt.

## Source of truth

Model facts move faster than any bundled document. Three tiers, stop at the first that answers:

1. **The target model's current official page.** Anthropic: "Prompting best practices" at
   platform.claude.com plus the per-model page. OpenAI: the Model guidance hub and the
   reasoning best-practices page at developers.openai.com. Google: the Gemini 3 developer
   guide and the Gemma prompt-formatting page at ai.google.dev. When a prompt ships to
   production, fetch the page and confirm any vendor fact the rewrite restates.
2. **A measurement on that model**, yours or a published one on the same model and task.
3. **These references.** Orientation, dated, quoted; never the authority over tier 1.

A fact you could not confirm is unconfirmed, not confirmed absent: tag it *(verify)* in the
rewrite rather than deleting it or letting it read as checked.

## What decays and what does not

| Shelf life | Content | Lives in |
|---|---|---|
| **Stable** | The method: behavioral contract, archetype-aware rubric, semantic diff, epistemic labels, audit depth | the `prompt-engineer` role |
| **Slow** | The prompting foundations, pattern catalog, extraction shapes, enforcement ladder, judge shape and agent-instruction anatomy | `prompting-foundations.md`, `reasoning-patterns.md`, `extraction-prompting.md`, `structured-output.md`, `judge-prompting.md`, `agent-instructions.md` |
| **Model-sensitive** | Thinking modes, effort names, prefill, cache multipliers, structured-output support, Gemma templates, the model-fit rows below | `model-guidance.md`; refresh every three months, like the `agent-sdk-builder` skill |
| **Measured and dated** | Every number with an arXiv ID or a vendor benchmark | the reference that cites it; each carries its check date |

## The model-class gate

Every reference assumes this decision was made first. Turn the target model into a class, then
read the row; the vendor matters less than the class.

| Class | Examples | Thinking control | Reasoning scaffold | Examples | Output shape | Measure first |
|---|---|---|---|---|---|---|
| **Frontier reasoning model** | Claude 4.6 and later, the Claude 5 family, GPT-5.x and GPT-6, Gemini 3, o-series, DeepSeek R1 by API | The native setting: `effort` on Claude (`budget_tokens` returns 400 from 4.7 on), `reasoning_effort` on OpenAI, `thinking_level` on Gemini 3 | None by default; a brief explicit plan only at the lowest effort setting | Zero-shot first; add input/output examples for demonstrated task, format, tone or boundary failures; never worked reasoning traces | Ask first, retries second, API structured outputs or an enum tool third; last-turn prefill is gone on Claude 4.6 and later | Overthinking cost on easy inputs; parse-failure rate and the wrong-but-valid rate if parsed |
| **Hybrid open reasoner** | Qwen3, Gemma 4, DeepSeek V3.x, gpt-oss | Mode tokens or a thinking prefill, not prose; depth self-selection at 9B and below, draft-agreement routing from 8B to 32B | None by default; the reasoning-patterns reference names the training-free options | Zero-shot first; input and output only | Constrained decoding in the serving stack; the schema in the prompt is a courtesy, not the enforcement | Think versus no-think per task; output validity |
| **Small open-weight instruct model** | Gemma 3, Llama 3.x 8B, Phi-4-mini, Mistral Small, anything under roughly 30B on Ollama, llama.cpp, vLLM or Transformers | None | A per-model choice: CoT measured anywhere from a gain to a 56-point loss on this class, so test zero-shot first | Input and output only, delimiter pinned, retrieved rather than random for extraction, kept short; shot count swept, since one example repaired Llama-3.1-8B on AG News (0.53 to 0.87 macro-F1) and eight undid it (0.55) | Validate-and-repair at minimum, constrained decoding when the stack offers it; the format instruction alone is never the enforcement (prompt-only validity measured 61% to 92% below 8B); prefilling the opening brace is still available when thinking is off | Output validity before anything else; then answer accuracy and the wrong-but-valid rate as separate numbers |
| **Older non-reasoning model** | GPT-4 class, Claude 3.x, Gemini 2.x without thinking | Not applicable | The classic catalog applies; CoT pays on math, logic and symbolic tasks and adds variance elsewhere | 3-5 diverse examples in delimited blocks on Claude (vendor); elsewhere swept, since Llama-4-Scout was best zero-shot on the task where an 8B needed two shots | JSON mode where the API has it; prefill on Claude 4.5 and earlier; validate-and-repair | Format drift across runs |

A model that fits two rows (a Gemma 4 served through Ollama with thinking off) takes the more
conservative row for output shape and the more specific row for thinking control.

## Reference router

| You need to decide | Read | It settles |
|---|---|---|
| How to turn a brief into a useful prompt, repair missing context, select examples, ground an answer or iterate from observed failures | `references/prompting-foundations.md` | Product, Process and Performance; defect-driven use of the six Academy techniques; original prompt examples; feedback and eval separation |
| Whether any reasoning scaffold belongs in the prompt, which one, and what it costs in tokens; how to build the efficiency pole of a variant frontier | `references/reasoning-patterns.md` | The selection cheat sheet, the reasoning-model defaults per class, the token-efficient patterns, cost-aware selection |
| How to make the model return JSON, a schema, an enum or a fixed template, and what holds on a small model | `references/structured-output.md` | The enforcement ladder, per-rung costs, reason-then-format ordering, the measured compliance of prompt-only techniques, serving-stack options |
| How to prompt for NER, relation or event extraction, document fields, tables, classification | `references/extraction-prompting.md` | The per-task shapes, what fails, the error taxonomy to diagnose against, the small-model order of operations |
| How to write the prompt of an LLM-as-judge, a rubric verifier or a grader, and which additions measured as harmful | `references/judge-prompting.md` | The default judge shape, the per-class table, the lever table (reference, checklist, scale, permutation, strictness, persona, debate), the agreement check |
| What has a measured effect in an agent's instruction surface: tool descriptions, rule and instruction files, skill descriptions, history scope, long-job persistence, coding-agent workflows | `references/agent-instructions.md` | Description anatomy, guardrails over guidance, per-model history scope, verified state, fresh-context test generation, and what is still unmeasured |
| What a vendor currently says about a named model before restating it | `references/model-guidance.md` | Quoted, dated vendor statements and their consequence for a prompt |
| Detailed benchmark numbers, sample sizes and per-model curves behind the role's digest rules | `references/empirical-notes.md` | Persona ratings, shot-count curves, delimiter spreads, compositional constraint half-lives, RAG abstention rates and language/modality measurements |

Skip reference reads for a simple persona or single-turn free-text prompt when the working
baseline suffices, with no reasoning component, parsed output or cost constraint. That is the
quick pass in the role's audit-depth rule, and it stays cheap on purpose.

## Two rules every reference shares

- **A number in these files is measured on the model it names and predicted on yours.** Apply
  it as a hypothesis, then run the eval the reference ends with. The epistemic labels in the
  `prompt-engineer` role are not optional vocabulary. The measured case: across model
  generations the few-shot effect reversed on average from Qwen2 to Qwen2.5 and shrank from
  GPT-3.5 to GPT-4o (arXiv 2608.24641, ICSME 2026).
- **The efficiency pole is the caller's to pick, never the optimizer's.** Where a technique
  trades accuracy for tokens, present both ends with costs and let the caller choose.
