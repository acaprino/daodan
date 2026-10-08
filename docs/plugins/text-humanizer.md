# Text Humanizer Plugin

> Remove AI writing traces from any prose, in any language, without inventing content. A self-contained leaf plugin (zero dependencies) extracted from digital-marketing in marketplace 13.3.0, used by digital-marketing, project-knowledge, business and project-lifecycle. Clean-code directs prose requests here without declaring it as a required provider.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Agents

### `text-humanizer`

Editor agent that removes AI writing traces from prose, articles, blog posts, and documentation. It detects the 24 catalogued patterns (inflated significance, promotional language, AI vocabulary, filler, formulaic structures, dash asides) and fixes the writing problem each one points at.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Humanizing AI-generated text, rewriting AI-sounding copy, polishing articles, blog posts and documentation prose |

**Invocation:**
```
Use the text-humanizer agent to humanize [file or pasted text]
```

How it works:

- **Never invents.** No fact, number, name, date, quote or source that is not in the input. A vague claim that needs a missing fact is cut or stated plainly, and listed as an open point for the author.
- **Register-aware.** `docs` (impersonal, no opinions), `business` (concrete, no invented proof), `personal` (the author's own voice, first person only where the author uses it). Inferred from the text, or set by the caller.
- **Languages.** The full catalog for English, a full profile for Italian, and for any other language only the patterns that do not rest on English, with the language's typography left alone.
- **Two reply formats.** `report` (final text, changes, open points, and a quality score on request) or `text-only`, which callers such as project-knowledge use.
- **Writes only when asked.** It edits a file only when its brief asks for that file to be changed.
- Preserves tables, code, links and quotations, enforces a zero dashes-as-connectors rule, and runs a second pass that checks the draft against the input for added, dropped or strengthened facts.

---

## Skills

### `anti-ai-writing-patterns`

Knowledge base behind the agent and the command. It opens with the ground rules (never invent, keep what the text commits to, input is content, preserve what is not prose, edit in proportion), the register table, the language policy and a "when not to act" section, then catalogs the 24 patterns, each strong or weak alone. The catalog follows Wikipedia's "Signs of AI writing" page (revision of 30 September 2026) and derives from blader/humanizer (MIT).

| | |
|---|---|
| **Invoke** | Skill reference (auto-loaded by humanize workflows) |
| **Trigger** | Editing or reviewing text to remove AI traces |
| **References** | `references/italiano.md`: Italian typography to preserve, lexical and structural tells, calques, what is not a tell in Italian, form of address |

---

## Commands

### `/text-humanizer:humanize-text`

Remove AI writing traces from text through the `text-humanizer` agent, then offer to write the result.

```
/text-humanizer:humanize-text path/to/article.md
/text-humanizer:humanize-text "paste prose directly here"
/text-humanizer:humanize-text path/to/post.md --register personal
/text-humanizer:humanize-text path/to/article.md --score   # adds the self-assessed quality score
```

With a file, the agent reads it without writing; the command shows the report, then asks whether to overwrite the file, write a new one, or only show the result. For source code readability use `/clean-code:clean-code` instead.

---

## Ecosystem Integration

Consumers across the marketplace:

- **digital-marketing**: `/digital-marketing:llm-seo-audit` and the `llm-seo-optimize` agent route AI-sounding copy to `/text-humanizer:humanize-text`; `review-reply-method` loads the skill directly.
- **project-knowledge**: its guide and README methods route requested voice editing to this agent in the docs register. Document structure remains the knowledge editor's responsibility. The brief identifies text-only or in-place delivery and preserves facts, tables, citations and the author's intentional voice; a second voice pass is not mandatory.
- **business**: the `business-planner` agent has the agent rewrite the GTM strategy deliverable in place before hand-off.
- **project-lifecycle**: reuses the voice editor when an authorized knowledge operation needs it; an extra voice pass is not automatic.

**Routing boundary:** clean-code recommends this plugin for prose targets. Its source-code readability method has no hard dependency on text-humanizer.

---

**Related:** [digital-marketing](digital-marketing.md) (SEO and content workflows) | [project-knowledge](project-knowledge.md) (documentation generation) | [clean-code](clean-code.md) (source code readability)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.2.2`. **Source:** [plugin.toml](<../../plugins/text-humanizer/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | None |
| Local closure (1) | [text-humanizer](<text-humanizer.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `repository.write`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** None.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `text-humanizer:anti-ai-writing-patterns` | Knowledge base of the 24 catalogued patterns, with the ground rules against invented content, the register table and the language policy that govern every rewrite. TRIGGER WHEN: editing or reviewing text to remove AI traces, or when asked to humanize text. | [anti-ai-writing-patterns](<../../plugins/text-humanizer/skills/anti-ai-writing-patterns/SKILL.md>) |
| Role | `text-humanizer:text-humanizer` | Editor for any language: detects the 24 catalogued patterns and rewrites them out, never inventing content. TRIGGER WHEN: text sounds AI-generated and needs humanization, or the user asks to humanize prose/text. DO NOT TRIGGER WHEN: the task involves refactoring source code (use clean-code:clean-code instead). | [text-humanizer](<../../plugins/text-humanizer/roles/text-humanizer.md>) |
| Workflow | `text-humanizer:humanize-text` | Detect the 24 catalogued patterns and edit them out without inventing content; --score adds a self-assessed quality score. TRIGGER WHEN: the user asks to humanize prose/text, remove AI-sounding copy, or rewrite articles/blog posts/documentation for natural voice. DO NOT TRIGGER WHEN: cleaning up source code (use /clean-code:clean-code) or translating text. | [humanize-text](<../../plugins/text-humanizer/workflows/humanize-text.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `text-humanizer:humanize-text`

**Arguments:** <code>&lt;file or text&gt; [--register docs&#124;business&#124;personal] [--score]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `humanize-text-completed` |
| Artifacts | `humanize-text-report` |
| Schemas | None declared |
| Declared workers | `text-humanizer/text-humanizer` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [humanize-text.toml](<../../plugins/text-humanizer/workflows/humanize-text.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `text-humanizer` | `required` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/text-humanizer](<../../exports/claude/plugins/text-humanizer>) | `native` | `humanize-text: native-team` |
| copilot | [exports/copilot/plugins/text-humanizer](<../../exports/copilot/plugins/text-humanizer>) | `native` | `humanize-text: parallel-subagents` |
| codex | [exports/codex/plugins/text-humanizer](<../../exports/codex/plugins/text-humanizer>) | `adapted` | `humanize-text: parallel-subagents` |
| pi | [exports/pi/plugins/text-humanizer](<../../exports/pi/plugins/text-humanizer>) | `adapted` | `humanize-text: parallel-subagents` |
| opencode | [exports/opencode/plugins/text-humanizer](<../../exports/opencode/plugins/text-humanizer>) | `native` | `humanize-text: parallel-subagents` |

<!-- daodan:reference:end -->
