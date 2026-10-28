---
description: 'Present the efficiency-versus-effectiveness frontier as labelled variants and let the user pick. TRIGGER WHEN: the user wants to review or optimize a prompt, system message, or agent instructions for clarity/tokens/reliability.'
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/`, `agents/` and `commands/`. The loader substitutes it in every body it registers; in any other file, resolve it once from where that file was loaded.

<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# prompt-optimize

<!-- Generated by the Daodan compiler for opencode. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **named-agent**, and declared
isolation **required**.

Dispatch one worker per entry in the plan below with the `subagent` tool. Name the role as the
agent, using the qualified identity in the bindings below, and give it a short `description` and the full
task as `prompt`. Each agent runs in a fresh child session, so isolation is native here.
For a local role the qualified form is `agent: "ai-tooling:<role>"`; external roles
use their owner's prefix from the bindings, never the coordinator's prefix.

Under `parallel-subagents`, dispatch every worker of one phase with `background: true`, then wait
for every completion notice before the phase closes; do not poll. Under `serial-isolated`, dispatch
them one at a time in the foreground.

Every role below is registered as an agent by this package. A `subagent` call that answers with an
unknown agent means the install is broken: stop and report it, never continue with a shorter
report.

Coordinator completion ownership: keep the method's owned run and delivery ledger,
including each expected worker, attempt, report path and required check evidence.
Validate report artifacts before recording delivered. An empty final message or
worker stop remains missing delivery: inspect or resume when permitted, otherwise
record failed with the uncovered scope. Follow the declared join and phase gates;
a recorded failure is accounted for, never converted into a successful delivery.
Continue authorized work and recovery until the requested result and its checks
exist or a concrete blocker is recorded. Preserve the exclusive final report owner
and the ledger schema; a tool exit or a promise cannot satisfy completion.

Harness obligations, none of them optional:

- Every dispatched worker runs in its own context and reads only coordinator-declared inputs.
  Independent reviewers never read peer results before their own delivery.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A worker reports delivered or failed in its final message; there is no shared task
  list, so the coordinator keeps that record itself.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `prompt-engineer`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `prompt-engineer` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:prompt-optimize-report`.

Role bindings:

- `prompt-engineer`: dispatch the installed `ai-tooling:prompt-engineer` agent by its qualified identity.

The phase graph and the record schemas are in `contracts/prompt-optimize.workflow.toml`.

## Method

# Prompt Optimization

## CRITICAL RULES

1. **Read the prompt first.** If `$ARGUMENTS` is a file path, read the file. If inline text, use it directly.
2. **Never modify the user's original prompt** until they approve a variant.
3. **Show the frontier.** Efficiency vs effectiveness is the user's call, not the optimizer's: present variants along that axis with honest cost labels, and let the user pick. `--optimize-for` is the shortcut for users who already know their pole.
4. **Name the model class.** `--model` accepts a vendor name or an open-weight model name; the analysis turns it into a class (frontier reasoning model, hybrid open reasoner, small open-weight instruct model, older non-reasoning model), and every recommendation is made for that class. What enforces an output shape, and whether a reasoning scaffold helps, differ by class more than by vendor.
5. **Never enter plan mode.** Execute immediately.

## Step 1: Analysis and variant frontier (single agent pass)

Spawn the `prompt-engineer` agent through the declared host harness, description "Analyze the prompt and generate the variant frontier", with the brief below as its prompt. One agent, one pass: it analyzes first, natively, and returns only the observable artifacts defined in Phase 2. No explicit reasoning scaffold is imposed on it, per its own anti-pattern rules for reasoning models.

```
You are evaluating and optimizing a prompt.

## Input
- Original Prompt: [Insert the prompt from $ARGUMENTS]
- Optimization Target: [--optimize-for flag value, or "frontier" when absent]
- Target Model: [--model flag value, default "claude"]

## Phase 1: Analysis (private)
Analyze the prompt thoroughly before writing any output. Extract its behavioral contract
first, then classify the archetype and score on a 1-5 scale only the rubric dimensions that
archetype wants, marking the rest N/A. Identify ambiguities, missing edge cases, structural
weaknesses, and injection vulnerabilities.
Do not include this working in the response: Phase 2 defines the only output you produce.

Model-class check: turn the target model into a class before anything else. Frontier
reasoning model (Claude 4.6 and later, GPT-5.x and GPT-6, Gemini 3, o-series, R1 class):
thinking is native and controlled by an effort setting. Hybrid open reasoner (Qwen3, Gemma 4,
DeepSeek V3.x, gpt-oss): thinking is switched by mode tokens. Small open-weight instruct model
(Gemma 3, Llama 3.x 8B, Phi-4-mini, Mistral Small and anything under roughly 30B served
through Ollama, llama.cpp, vLLM or similar): no native thinking control, weak format
compliance, and a serving stack that may offer constrained decoding. Older non-reasoning
model: the classic patterns apply. Read the model-fit rows of
`<plugin-root>/skills/prompt-engineering/SKILL.md` for the class before scoring model
fit, and `<plugin-root>/skills/prompt-engineering/references/model-guidance.md` when
the target is a named vendor model whose current guidance matters to the rewrite.

Usage-profile check: determine how the prompt is used (one-off, repeated system prompt,
agent loop) and whether prompt caching applies. Which tokens matter follows from this:
output tokens bill at full price and dominate latency; a cached prefix bills 0.1x on reads
(0.025x on Claude Fable 5.1 and Mythos 5.1), so shortening it saves a tenth of what it
appears to, and a cache-breaking edit re-bills it at the write multiplier (1.25x for the
5-minute TTL, 2x for the 1-hour TTL).

Reasoning-pattern check: for a frontier reasoning model, default to NO explicit scaffold:
direct instructions plus precise success criteria, with the effort setting as the lever;
consult the "Reasoning models change the defaults" section of
`<plugin-root>/skills/prompt-engineering/references/reasoning-patterns.md` before
adding any pattern, and never add worked reasoning traces as few-shot exemplars. For a
hybrid open reasoner or a small open reasoner, the same section says what the lever is
(mode tokens, depth self-selection, zero-shot first). Otherwise, decide whether the task
would benefit from a structured reasoning scaffold beyond plain instructions (CoT,
Step-Back, ReAct, Tree-of-Thought, Self-Consistency, Reflexion, Plan-and-Solve,
Least-to-Most, Self-Ask, Skeleton-of-Thought). If yes, read that reference, pick the pattern
that matches the task shape using the selection cheat sheet, and apply it in Phase 2.
For the efficiency variant, always consult that file's token-efficient patterns
(Chain of Draft, Concise CoT, token-budget prompting, Sketch-of-Thought) and its
"Cost-aware selection" section: the efficiency pole is built from those techniques,
not from bare word-deletion.
If the existing prompt already scores 4+ on every dimension, do not add a pattern just
for completeness: record the decision in the analysis instead.

Foundation check: apply the working baseline in the skill. Diagnose the intended result,
required task operations and interaction preferences separately; do not invent context or
requirements. For an incomplete brief, mixed inputs, example failures, source-grounded answers
or an iterative eval, consult
`<plugin-root>/skills/prompt-engineering/references/prompting-foundations.md`.
Numbered task operations are not a private reasoning scaffold. Examples address a concrete
task, format, tone or boundary defect after the model-class gate. Examples promoted from
development runs stay outside the held-out verification set. State the baseline, criteria and
paired comparison that would test the change; a proposed eval is not a measured gain.
Prefer the smallest justified change. Do not promote one unusual failure into a universal rule,
optimize against leaked examples or add mechanisms just to satisfy the checklist. If no material
defect or new requirement warrants a change, keep the original.

Output-shape check: if anything parses the output (JSON, a schema, an enum, a fixed
template), read `<plugin-root>/skills/prompt-engineering/references/structured-output.md`
and decide the enforcement rung for this model class: format instruction only,
instruction plus validate-and-repair, API structured outputs, or constrained decoding in
the serving stack. On a small open-weight model the instruction alone is never the
enforcement; say which rung the variant assumes and what it costs. Domain validation runs after
schema validation and the system fails closed on either, so the rung a variant names covers the
shape and not the correctness of what the shape holds: the variant says which obligations the
rung covers and which need a domain validator beside it. When the task needs
reasoning as well as a shape, order the prompt to reason first and format last, or split
it into two calls; never ask for reasoning inside the JSON. Where the target is a Claude
4.6 or later model, assistant prefill on the last turn is not available; on an open-weight
model served locally, prefilling the opening brace still is.

Task-family check: if the archetype is extraction or classification (NER, relations,
events, fields from documents, labels from a fixed set), read
`<plugin-root>/skills/prompt-engineering/references/extraction-prompting.md` and
apply the per-task shape it names; extraction is not a reasoning task, so a scaffold added
to it is a defect, and for a fixed schema at volume say plainly that a fine-tuned small
model is the ceiling the prompt cannot reach.

Judge and agent checks: if the archetype is judge / evaluator, read
`<plugin-root>/skills/prompt-engineering/references/judge-prompting.md` and build the
variants on its default shape (one criterion per judge, binary with evidence, a reference when
one exists, a checklist step for open-ended criteria, 0-5 where a scalar is needed); a judge
persona, a judge debate or a 1-10 scale in the original is a defect to report, not a style. If
the archetype is agentic / tool-use, or the text is a tool description, an instruction file, a
skill description or an orchestrator brief, read
`<plugin-root>/skills/prompt-engineering/references/agent-instructions.md` and apply
its anatomy: no few-shot demonstrations in a tool agent's system prompt by default, and long-job
persistence written as verified state rather than a reminder.

Constraint-count check: count the constraints the output must satisfy at once (format, length,
lexical, structural, content). Joint compliance saturates early on every class measured, so
escalate by count: zero to three constraints normal, four to five, add a verifier, and
above five simultaneously verifiable constraints propose a split into stages or a
verify-and-retry step as its own variant and say what it costs; the numbers are in the role's
over-constraining anti-pattern. The band decides only when the optimizer volunteers a split or
a verifier variant as its own option. It is not a reliability criterion and it does not answer
a caller's error budget: when the caller names a joint-success target, or when any counted
constraint is machine-checkable, decide on the four numbers of the output-shape eval
(schema validity, answer accuracy, executable accuracy, the wrong-but-valid rate) rather than
on the count. In a persistent agent rule file the guardrail rules are exempt: fifty guardrails
did not collapse a coding agent's task pass rate, and there the defect to hunt is a conflicting
or unverifiable rule. Output obligations the same file carries, a release-note or
commit-message format for example, count like any other simultaneous constraint.

Language check: the variants stay in the language the original is written in unless a
measurement on the target model and task says otherwise, in which case a translated variant may
enter the frontier, labelled, with the language change reported in the Behavioral changes
section and the measurement named. Absent that measurement, translating an Italian or other
non-English prompt to English is not an optimization, because the effect changes sign by task
and model; a language change the caller asks for is a behavioral change to report.

## Phase 2: Output
Based on your analysis, respond strictly in this format:

### Diagnostic Scorecard (original, predicted)
State the archetype and the model class in one line each, then one row per applicable
dimension. Include the conditional dimensions (output determinism, tool-use correctness,
trust boundaries, evalability, creative latitude) only when this archetype wants them, and
list the ones you marked N/A with a short reason underneath.

| Dimension | Score (1-5) | Key issue |
|-----------|:---:|-------|
| Intent alignment | X | ... |
| Instruction clarity | X | ... |
| Constraint correctness | X | ... |
| Model fit | X | ... |
| Context efficiency | X | ... |
| Robustness | X | ... |

### Variant Frontier
Produce 3 variants by default:
- **A. Max effectiveness**: prioritize quality, robustness, and output control; token cost is secondary.
- **B. Balanced**: resolve the analysis issues at neutral or lower token cost.
- **C. Max efficiency**: minimum tokens at estimated parity, built with a token-efficient
  technique where reasoning is involved.

Collapse to fewer variants only when they would genuinely converge (trivial or already
near-optimal prompts); say that you did and why. Each variant is a fully rewritten,
ready-to-use prompt in its own fenced block. Use XML tags if the target model is Claude
and the prompt mixes instructions, context, or examples; headings suffice for simple prompts.
When the output is parsed, every variant states the enforcement rung it assumes, and the
serving-stack setting or validator that rung needs sits next to the prompt, not inside it.

### Comparison
| Variant | Tokens (est.) | Delta vs original | Technique applied | Enforcement (if parsed) | Predicted effect (unmeasured) | What you give up |

Token estimates: characters/4 on the prompt text, labeled "est.". If a variant also
constrains reasoning or output length, state the expected output-token effect
separately: that is where most of the real savings live.

### Behavioral changes
For each variant, report what changed in behavior rather than in wording: constraints
strengthened or relaxed, behaviors removed or added, interface changes, tool-policy or
reasoning-strategy changes, output-enforcement changes, trust boundaries hardened or
weakened. Print only the lines that are true. If a variant changes nothing behavioral, say
so in one line. Lead with any relaxation or removal instead of burying it under the token
saving.

### Honesty note
Close with these caveats, adapted to the case:
- Label every quality claim predicted, measured, or verified. A score this pass assigned is
  predicted by definition, including the scorecard above.
- Predicted scores and parity are single-pass estimates by the same model that wrote
  the variants, not measurements; small formatting changes alone are known to swing
  task accuracy, so treat the deltas as hypotheses.
- To actually verify "fewer tokens, same results": run a paired eval (identical inputs
  per variant, pre-declared non-inferiority margin). The prompt-engineer prompt-evals
  guidance covers the method; promptfoo fits in CI.
- If the output is parsed, say that schema compliance on this model class is predicted
  until measured on a hundred real inputs, and name the parse-failure rate as the first
  number to collect, with the wrong-but-valid rate collected beside it: an obligation the
  schema cannot express is caught by a domain validator, not by the schema.
- If the prompt is a cached system prompt, repeat the cache-economics warning from
  the analysis.
- If the prompt is a judge, say that agreement with humans is predicted until Cohen's kappa
  is measured on the caller's own labels, one kappa per criterion.
```

## Step 2: The user picks the pole

After the agent returns, present its output and ask the user which variant to adopt with a user question: one option per variant, each label naming the pole and each description carrying the token estimate and the main trade-off; put your recommended variant first with "(Recommended)". Skip the question and deliver the matching pole directly when:

- `--optimize-for` was passed (clarity -> A, reliability -> A with constraints and examples emphasized, tokens -> C), or
- the user already stated their target in the request.

`--compare` forces the full frontier presentation even when a shortcut applies.

## Step 3: Deliver

Deliver the chosen variant ready to copy, with its token estimate, the enforcement rung and its setting when the output is parsed, and 1-2 test inputs the user can validate it with. Apply it to the source file only if the user asks; the original is never modified without approval.

## Quick Examples

- `/prompt-optimize "Summarize this document"`: full frontier, user picks the pole
- `/prompt-optimize prompts/system.md --optimize-for tokens`: straight to the efficiency pole
- `/prompt-optimize prompts/agent.md --model gpt --compare`: optimize for GPT, always show the full frontier
- `/prompt-optimize prompts/extract.md --model gemma-3-12b`: small open-weight target: the variants name their enforcement rung and the extraction shape they use
- `/prompt-optimize prompts/judge.md --model gpt`: judge archetype: the variants decompose the rubric, drop the persona, and name the agreement check
