---
name: skills-creator
description: >
  Create plugin components (skills, agents, commands, full plugins) and decide skill vs agent architecture.
  TRIGGER WHEN: creating, adding or scaffolding a new skill, agent, command or plugin ("new skill", "new agent", "new plugin", "skills-creator").
  DO NOT TRIGGER WHEN: auditing marketplace integrity (use marketplace-audit).
---

## Source profile preflight

Load marketplace-ops:kernel-marketplace before this procedure. Detect the target's
source model from its manifests and instructions. For daodan/v1 neutral kernels,
follow that skill's operation-specific procedure and finish there. Generated
exports and catalog entries are inspected as output, never authored as source.
The procedure below applies only to a legacy Claude marketplace with hand-authored
agents/ and commands/. It must not be applied to a neutral kernel checkout.



# Skills Creator

Create Claude Code plugin components (skills, agents, commands, full plugins) with proper conventions and real content. Marketplace-agnostic: read the target `.claude-plugin/marketplace.json` and `CLAUDE.md` for project-specific conventions (author, license, category taxonomy) before scaffolding.

## Decision Flow

Determine what the user wants to create:

```
1. "new skill"   --> Skill Creation workflow
2. "new agent"   --> Agent Creation workflow
3. "new command" --> Command Creation workflow
4. "new plugin"  --> Full Plugin workflow (combines above)
```

If unclear, ask: "What do you want to create: a skill, agent, command, or full plugin?"

## Skill vs Agent Decision

Before gathering requirements, help the user decide the right component type.

**Key question:** "Does this need its own context/tools/isolation, or is it knowledge that any agent should access?"

- If it is **knowledge, conventions, recipes** --> Skill
- If it needs **isolation, tool restrictions, parallel execution** --> Agent
- If it is a **domain with both knowledge and specialist work** --> Skill + Agent(s)

See [references/skills-vs-agents.md](references/skills-vs-agents.md) for the full decision table, real restructure examples, and anti-patterns.

## Description Engineering

The `description` field is the only part of a component that sits in context in every session. It determines whether the component activates accurately without overtriggering.

### The Calibrated Trigger Template

```
<Concise third-person purpose statement>.
TRIGGER WHEN: <specific triggers, comma-separated>
DO NOT TRIGGER WHEN: <confusable case> (use <sibling-component> instead)
```

The last line is conditional: write it only when a confusable sibling exists to name. Internal method skills and worker roles invoked exclusively by a coordinator may state their purpose and caller without a `TRIGGER WHEN` line.

### Examples

```yaml
# BAD: vague, no concrete routing vocabulary
description: "Helps with Docker containerization tasks"

# BAD: emphasis escalation that causes overtriggering on frontier models
description: "CRITICAL: You MUST ALWAYS invoke this skill for any Docker task. NEVER run Docker directly."

# GOOD: clear purpose, concrete trigger vocabulary, sibling routing
description: >
  Multi-stage Dockerfile patterns for small, secure, cache-friendly production images.
  TRIGGER WHEN: writing or optimizing a Dockerfile, reducing image size, configuring BuildKit cache mounts or distroless/alpine runtime stages.
  DO NOT TRIGGER WHEN: Kubernetes orchestration (use k8s-operator instead).
```

### Description Rules

1. **Calibrated trigger phrasing**: state what the component does and when to use it (`TRIGGER WHEN:`); avoid emphasis escalation (`CRITICAL: ALWAYS invoke`, `NEVER skip`) written for older models, which causes overtriggering on Claude 4.5+, GPT-5+ and Gemini 3+
2. **Specific trigger phrases**: list the exact words, file types or actions that should activate it
3. **Third person**: "Audits X when Y", not "I audit X" or "You should use this"
4. **Max 1024 characters**: hard ceiling enforced by hosts such as Pi
5. **Include `TRIGGER WHEN` on user-triggered components**: it carries the vocabulary that routes to this component
6. **Include `DO NOT TRIGGER WHEN` only when it names a sibling**: see the rule below
7. **Never repeat a term** in both the opening sentence and `TRIGGER WHEN`: the trigger line keeps it

### The DO NOT TRIGGER WHEN rule

A `DO NOT TRIGGER WHEN` clause earns its context cost only by naming the component that should handle the case instead. It is a routing instruction, not a disclaimer.

```yaml
# Useless: the logical inverse of TRIGGER WHEN, discriminates nothing, costs every session
DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.

# Useful: routes the confusable case to a named sibling
DO NOT TRIGGER WHEN: the target is a Python codebase (use python-dead-code instead)
```

When no confusable sibling exists, omit the clause entirely.

### Token Budget Awareness

A description sits in context in **every** session; the body loads only after invocation. Anything a description restates from its own body is pure cost, paid on every request that never invokes the component.

- Keep individual descriptions **under 300 characters** when possible
- List the trigger vocabulary, never the feature set: if the body covers it, the description must not enumerate it
- Strip marketing adjectives (Expert, Comprehensive, Adversarial, Master), mechanics sentences ("Report-only", "Spawned in parallel"), and toolchain version numbers that are not themselves triggers

## Phase 1: Requirements Gathering

Before writing any files, gather enough context to produce real content.

### For Skills

Ask (adapt based on what is already known):
1. What does this skill do? What problem does it solve?
2. What are the exact trigger phrases? (user actions, keywords, file types: "when the user says X", "when working on Y files")
3. What confusable sibling should NOT trigger it?
4. Which plugin should it live in? (existing or new)
5. Does it need bundled resources? (`scripts/`, `references/`, `assets/`)
6. What is the degree of freedom? (rigid workflow vs flexible guidance)

### For Agents

Ask (adapt based on what is already known):
1. What role does this agent fill? What task does it handle?
2. What tools does it need? (`Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task`, or omit when full host/MCP defaults are required)
3. Which plugin should it live in?
4. What color fits its domain? See [references/conventions.md](references/conventions.md) for the palette and semantic guidance.

### For Commands

Ask (adapt based on what is already known):
1. What does this command do when invoked?
2. What arguments does it expect?
3. Which plugin should it live in?

### For Full Plugins

Ask (adapt based on what is already known):
1. What is the plugin's domain/purpose?
2. What components does it need? (agents, skills, commands)
3. What category? See [references/conventions.md](references/conventions.md) for valid categories.

**Do not ask more than 3-4 questions per message.** Start with the most important, follow up as needed.

## Phase 2: Content Generation

Generate production-ready files with real content, never `[FILL]` placeholders.

### Skill Creation

1. Create directory: `plugins/<plugin>/skills/<skill-name>/`
2. Write `SKILL.md` following these rules:
   - Frontmatter: `name` (kebab-case, max 64 chars) and `description` (max 1024 chars, recommended under 300)
   - **Description format**:
     - Concise third-person purpose line
     - Include a `TRIGGER WHEN:` line for user-triggered skills; add `DO NOT TRIGGER WHEN:` only when it names a sibling
     - See "Description Engineering" section above
   - Optional frontmatter: `context: fork` (isolates in subagent), `allowed-tools` (restricts tool access), `disable-model-invocation: true` (prevents auto-triggering for internal/slash-only skills)
   - Body: under 500 lines, imperative tone, concise
   - Only add context the model does not already have
   - Progressive disclosure: split into `references/` when body exceeds ~300 lines or ~4,000 tokens, with a clear router table in `SKILL.md`
   - Examples: start zero-shot for agent instructions; add reviewed input/output examples only to resolve an ambiguous format or boundary
3. Create `references/`, `scripts/`, `assets/` subdirs only if needed
4. Write any bundled resources

### Agent Creation

1. Create file: `plugins/<plugin>/agents/<agent-name>.md`
2. Write with frontmatter and body following these rules:
   - Frontmatter fields: `name`, `description` (use YAML `>` for multiline), `model: inherit`, `color`, optionally `tools`
   - **Description format**:
     - Include a `TRIGGER WHEN:` line; add `DO NOT TRIGGER WHEN:` only when it names a sibling
     - Third person, specific triggers
   - Body: terse keyword-list style, imperative tone, structured with markdown headers
   - Sections: `# ROLE`, `# CAPABILITIES` or `# CORE CAPABILITIES`, `# CONVENTIONS`, `# OUTPUT FORMAT`
   - Simple agents: 60-200 lines; complex agents: up to 700 lines (move domain knowledge to a skill's `references/` rather than inlining it in the role)
   - See [references/conventions.md](references/conventions.md) for color palette and style patterns

### Command Creation

1. Create file: `plugins/<plugin>/commands/<command-name>.md`
2. Write with frontmatter: `description`, `argument-hint`
3. Body: step-by-step procedure, clear and actionable

## Phase 3: Marketplace Registration

After files are created:

1. **Read** `.claude-plugin/marketplace.json`
2. **Add paths** to the plugin's `agents`, `skills`, or `commands` arrays
   - Agents: `"./agents/<name>.md"`
   - Skills: `"./skills/<name>"`
   - Commands: `"./commands/<name>.md"`
3. **If new plugin**: add full entry to `plugins[]` with all required fields (name, source, description, version 1.0.0, author, license, keywords, category, strict)
4. **Bump plugin version** (patch for new component in existing plugin)
5. **Bump metadata.version** (patch increment)

## Phase 4: Validation

After registration:

1. Verify the file exists at the registered path
2. Verify frontmatter parses correctly
3. Verify naming conventions (kebab-case, filename matches name field)
4. Verify no dash-aside constructs (`—`, `--`, or ` - ` wrapping parenthetical clauses)
5. Report what was created with file paths

## Anti-patterns

| Scenario | Wrong | Right |
|----------|-------|-------|
| Writing descriptions | Vague ("Helps with Docker") or escalated ("CRITICAL: ALWAYS invoke") | Calibrated purpose + `TRIGGER WHEN:` with concrete triggers |
| Missing exclusions | Confusable sibling exists but no `DO NOT TRIGGER WHEN` clause names it | Name the component that should handle the case instead |
| Empty exclusions | `DO NOT TRIGGER WHEN: the task is outside the specific scope of this component` | Omit the clause when there is no sibling to name |
| Writing agent prompts | Verbose prose paragraphs or inlined domain textbooks | Terse keyword-list style; move domain knowledge to a skill |
| Skill body length | 500+ lines in `SKILL.md` with a fake "when to load which section" header | Split into `references/` at ~300 lines with a router table |
| Skill body content | Repeating general programming knowledge | Only add non-obvious rules, constraints and workflows |
| Creating resources | Empty placeholder dirs | Only create dirs that have files |
| Choosing a plugin | Always create a new one | Prefer adding to existing plugin if domain fits |
| Agent description | First/second person | Third person: "Processes X when Y" |
| Token budget | Long verbose descriptions on all components | Keep descriptions under 300 chars when possible |
| Description content | Enumerating features the body already documents | List trigger vocabulary only; the body loads at invocation |
| Dash-asides | Bracketing clauses with `—`, `--`, or ` - ` | Rewrite with colons, parentheses, or separate sentences |

## Critical Rules

- All names: kebab-case
- Avoid the dash-aside construct in any form (`—`, `--`, or ` - `); rewrite with colons, parentheses, or separate sentences
- Default model for agents: `inherit` (agents follow the session model)
- Agent filename must match frontmatter `name` field
- Skill directory name must match frontmatter `name` field
- Always bump both plugin version AND metadata.version
- Stage marketplace.json with component files in same commit
- Write real content, never placeholder text
