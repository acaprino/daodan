# AI Tooling Plugin

> Prompt engineering knowledge base and optimization, and Agent SDK guidance.

**Note:** the `acp-loader` skill was removed in ai-tooling 4.0.0, together with the `acp-hooks` plugin that injected it at session start. Its generic behavior (check for a relevant skill before acting) is covered by the superpowers `using-superpowers` skill, which loads itself through its own SessionStart hook.

**Note:** the `brainstorming`, `writing-plans`, and `executing-plans` skills used to live here as ports of [obra/superpowers](https://github.com/obra/superpowers). They were removed in ai-tooling 3.0.0: superpowers maintains them upstream and ships the full methodology around them. Since ai-tooling 3.1.0, superpowers is a declared hard dependency of this plugin, not an optional companion. See the [README](../../README.md#brainstorming-planning-and-execution) for install instructions.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Agents

### `prompt-engineer`

Authors, restructures and evaluates the text that steers a model. It carries the method: it extracts a prompt's behavioral contract before touching it, classifies the archetype and scores only the rubric dimensions that archetype wants, rewrites, reports a semantic diff of what changed in behavior rather than in wording, and labels every quality claim predicted, measured or verified.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | System prompts, agent instructions and tool descriptions, judge prompts, few-shot design, token optimization, output-shape enforcement, extraction prompts, prompt evals |

**Invocation:**
```
Use the prompt-engineer agent to optimize [prompt/system]
```

**Audit depth:** a quick pass for throwaway prompts (contract, defects, rewrite), a deep pass for anything that is a system prompt, drives a tool loop, ships to production, is parsed downstream or handles untrusted input. The deep pass loads only the references the task needs from the `prompt-engineering` skill.

---

## Skills

### `prompt-engineering`

The knowledge base behind the agent and the command, loadable on its own. Its `SKILL.md` carries the source-of-truth order for model facts (the vendor's current page, then a measurement, then the bundled references), the model-class gate every recommendation is made against (frontier reasoning model, hybrid open reasoner, small open-weight instruct model, older non-reasoning model), and a router to six on-demand references:

| Reference | Covers |
|---|---|
| `reasoning-patterns.md` | Chain-of-Thought, Step-Back, Self-Consistency, Tree-of-Thought, ReAct, Reflexion, Plan-and-Solve, Least-to-Most, Self-Ask, Skeleton-of-Thought; the token-efficient patterns (Chain of Draft, Concise CoT, token-budget prompting, Sketch-of-Thought); how reasoning models, hybrid open reasoners and small open models change the defaults; cost-aware selection |
| `structured-output.md` | Forcing JSON, a schema, an enum or a template: the enforcement ladder from format instruction to validate-and-repair to API structured outputs to constrained decoding, what each rung costs, and what holds on small open-weight models such as Gemma |
| `extraction-prompting.md` | Per-task prompt shapes for NER, relation and event extraction, schema-guided document and table extraction, with measured gains, failure modes and the small-model order of operations |
| `judge-prompting.md` | The judge prompt shape that measured the highest human agreement per model class (one criterion per judge, binary with evidence, reference-guided, checklist step, 0-5 where scalar) and the additions that measured as harmful (personas, debate, strictness on strong judges) |
| `agent-instructions.md` | What has a measured effect in an agent's instruction surface: tool-description anatomy, guardrails over guidance in rule files, history scope per model, verified state for long jobs, test generation in a fresh context, and what is still unmeasured |
| `model-guidance.md` | What Anthropic, OpenAI and Google currently say about their models, quoted and dated: thinking modes, effort, prefill, caching, structured outputs, Gemma templates |

| | |
|---|---|
| **Invoke** | Skill reference |
| **Trigger** | designing, reviewing or optimizing a prompt; forcing JSON or a schema from a model; prompting for extraction; deciding on a reasoning scaffold, examples or a thinking budget; writing a judge prompt, a tool description, an instruction file or a skill description |

### `agent-sdk-builder`

Build apps with the Claude Agent SDK (formerly Claude Code SDK). Covers programmatic agent orchestration, subagent management, custom tools, and deployment workflows.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Trigger** | `claude-agent-sdk`, `@anthropic-ai/claude-agent-sdk`, "agent sdk", "build an agent", "programmatic claude", "sidecar" |

References, loaded on demand:

| Reference | Covers |
|---|---|
| `sdk-api.md` | Install, `query()`, full options table, built-in tools, streaming, structured output, cost tracking, migration from `claude-code-sdk` |
| `sessions-subagents.md` | Sessions, resume, fork, session metadata, introspection, subagent definitions, Python client methods |
| `permissions-hooks-security.md` | Permission modes and evaluation order, `canUseTool`, hook events and matchers, security practices |
| `mcp-plugins-skills.md` | Custom tools as in-process MCP servers, external MCP servers, loading plugins and settings |
| `deployment.md` | Hosting shapes, sandbox isolation, CI/CD review agent, research pipeline, chat loop |

**Key distinction:** The Agent SDK (`claude-agent-sdk`) runs the full Claude Code agent loop with built-in tools. The Anthropic Client SDK (`anthropic`) is for raw API calls.

**Packages:**
| | TypeScript | Python |
|---|---|---|
| Install | `npm install @anthropic-ai/claude-agent-sdk` | `pip install claude-agent-sdk` |

---

## Commands

### `/ai-tooling:prompt-optimize`

Analyzes a prompt in one `prompt-engineer` pass and presents the efficiency-versus-effectiveness frontier as labelled variants (max effectiveness, balanced, max efficiency), each with a token estimate, the technique applied, the enforcement rung it assumes when the output is parsed, what it gives up, and the behavioral changes it makes. The user picks the pole; `--optimize-for` skips the question for a user who already knows it, and `--compare` forces the full frontier.

```
/ai-tooling:prompt-optimize "You are a helpful assistant that..." --optimize-for tokens
/ai-tooling:prompt-optimize prompts/extract.md --model gemma-3-12b
```

**Flags:** `--model claude|gpt|gemini|<open-weight model name>` (the analysis turns it into a model class), `--optimize-for clarity|tokens|reliability`, `--compare`.

**Phases:** Analyze (contract, archetype, model class, usage profile, reasoning-pattern, output-shape, task-family, judge and agent, constraint-count and language checks) -> Variant frontier -> The user picks -> Deliver with test inputs.

---

**Related:** upstream wshobson/agents agent-teams (generic team orchestration); local team pipelines live in senior-review, codebase-xray, project-knowledge, research

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `5.4.3`. **Source:** [plugin.toml](<../../plugins/ai-tooling/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | `superpowers@claude-plugins-official` |
| Local closure (1) | [ai-tooling](<ai-tooling.md>) |
| External closure (1) | `superpowers@claude-plugins-official` |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `network.fetch`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** None.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `ai-tooling:agent-sdk-builder` | Run the Claude Agent SDK (formerly Claude Code SDK) loop inside your own program, not the `anthropic` client SDK for chat completions. TRIGGER WHEN: code references claude-agent-sdk, user says "agent sdk", "build an agent", "programmatic claude", "claude code sdk", "sidecar", "run claude programmatically"; or asks about tool integration, subagent orchestration, prompt caching or model migration inside that loop. | [agent-sdk-builder](<../../plugins/ai-tooling/skills/agent-sdk-builder/SKILL.md>) |
| Skill | `ai-tooling:prompt-engineering` | Knowledge base behind the prompt-engineer agent and /prompt-optimize: the source-of-truth order for model facts, the model-class gate, and six on-demand references covering reasoning patterns, output-shape enforcement, extraction prompting, judge prompts, agent and tool instructions, and dated vendor guidance. TRIGGER WHEN: designing, reviewing or optimizing a prompt, system message or agent instructions; forcing JSON or a schema out of a model, especially a small one such as Gemma; prompting for extraction (NER, relations, events, fields from documents); deciding whether a reasoning scaffold, few-shot examples or a thinking budget belongs in a prompt; writing an LLM-as-judge prompt; writing a tool description, an instruction file, a skill description or an orchestrator brief. DO NOT TRIGGER WHEN: building an agent on the Claude Agent SDK (use agent-sdk-builder), or the question is about a model's pricing or API surface with no prompt involved. | [prompt-engineering](<../../plugins/ai-tooling/skills/prompt-engineering/SKILL.md>) |
| Role | `ai-tooling:prompt-engineer` | Author, restructure, and evaluate the text that steers a model. TRIGGER WHEN: writing system prompts, designing agent instructions, or optimizing prompt performance for reliability and token efficiency. | [prompt-engineer](<../../plugins/ai-tooling/roles/prompt-engineer.md>) |
| Workflow | `ai-tooling:prompt-optimize` | Present the efficiency-versus-effectiveness frontier as labelled variants and let the user pick. TRIGGER WHEN: the user wants to review or optimize a prompt, system message, or agent instructions for clarity/tokens/reliability. | [prompt-optimize](<../../plugins/ai-tooling/workflows/prompt-optimize.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `ai-tooling:prompt-optimize`

**Arguments:** <code>&lt;prompt text or file path&gt; [--model claude&#124;gpt&#124;gemini&#124;&lt;open-weight model, e.g. gemma-3-12b&gt;] [--optimize-for clarity&#124;tokens&#124;reliability] [--compare]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `prompt-optimize-completed` |
| Artifacts | `prompt-optimize-report` |
| Schemas | None declared |
| Declared workers | `ai-tooling/prompt-engineer` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [prompt-optimize.toml](<../../plugins/ai-tooling/workflows/prompt-optimize.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `prompt-engineer` | `required` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/ai-tooling](<../../exports/claude/plugins/ai-tooling>) | `native` | `prompt-optimize: native-team` |
| copilot | [exports/copilot/plugins/ai-tooling](<../../exports/copilot/plugins/ai-tooling>) | `native` | `prompt-optimize: parallel-subagents` |
| codex | [exports/codex/plugins/ai-tooling](<../../exports/codex/plugins/ai-tooling>) | `adapted` | `prompt-optimize: parallel-subagents` |
| pi | [exports/pi/plugins/ai-tooling](<../../exports/pi/plugins/ai-tooling>) | `adapted` | `prompt-optimize: parallel-subagents` |
| opencode | [exports/opencode/plugins/ai-tooling](<../../exports/opencode/plugins/ai-tooling>) | `native` | `prompt-optimize: parallel-subagents` |

<!-- daodan:reference:end -->
