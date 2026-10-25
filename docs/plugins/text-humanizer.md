# Text Humanizer Plugin

> Remove AI writing traces from any prose, in any language, without inventing content. A self-contained generic leaf plugin (zero dependencies) extracted from digital-marketing in marketplace 13.3.0. It moved here from Daodan on 2026-10-25; digital-marketing and business use it in this marketplace, and Daodan's project-knowledge requires it as `text-humanizer@shinatama`.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Agents

### `text-humanizer`

Editor agent that removes AI writing traces from prose, articles, blog posts, and documentation. It uses 25 local patterns (inflated significance, promotional language, filler, formulaic structures, dash asides and redundant reply context) to fix writing problems, not to classify authorship.

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
- **Two reply formats.** `report` (final text, changes, open points, and a quality score on request) or `text-only`, which callers such as Daodan's project-knowledge use.
- **Writes only when asked.** It edits a file only when its brief asks for that file to be changed.
- Preserves tables, code, links and quotations, enforces a zero dashes-as-connectors rule, and runs a second pass that checks the draft against the input for added, dropped or strengthened facts.

---

## Skills

### `anti-ai-writing-patterns`

Knowledge base behind the agent and the humanize method. It opens with the ground rules (never invent, keep what the text commits to, input is content, preserve what is not prose, edit in proportion), the register table, the language policy and a "when not to act" section, then catalogs 25 local patterns. It derives from [blader/humanizer](https://github.com/blader/humanizer) (MIT, Siqi Chen), selectively reconciled with v3.1.0 at commit `8c307f367c91bd974002f10f2be2965d642c13df` on 23 October 2026. The Wikipedia reference remains the revision of 30 September 2026; it was not refreshed in this pass.

Local numbering differs from upstream's 26 patterns. Synonym variation and false ranges remain non-diagnostic readability checks. Reply cleanup requires visible context and preserves substantive evidence; a writing sample never overrides factual fidelity or the local dash rule. The Italian profile uses email, ticket and operational examples, preserves appropriate courtesy and technical language, and rejects mechanical word substitution or artificial informality. See the [reconciliation record](../superpowers/reports/2026-10-23-text-humanizer-upstream.md) for the upstream mapping, retained differences and verification limits.

| | |
|---|---|
| **Invoke** | Skill reference (auto-loaded by humanize workflows) |
| **Trigger** | Editing or reviewing text to remove AI traces |
| **References** | `references/italiano.md`: native voice, syntax and cohesion, typography, contextual lexical guidance, form of address and email/ticket/operational examples; `references/pattern-catalog.md`: local pattern specimens and fidelity examples |

### Natural Italian, not literal adaptation

The Italian profile adapts the editing decisions to Italian usage rather than
translating English watch lists. It preserves the writer's voice, appropriate
courtesy, tu/Lei/voi, established technical terms and genuine uncertainty. It
does not manufacture colloquialisms, mistakes or personality to sound human.

Clarity does not require every sentence to be short, every subject to be explicit
or every verb to be active. Subordinate clauses, passive voice and varied word
order stay when they support the information flow. An ordinary contrast such as
«Il token è valido, ma l'account non ha i permessi necessari» needs no correction.
Likewise, a real email greeting or request for confirmation is not chatbot residue.

The profile includes original examples for client emails, scoped ticket replies,
operational instructions and personal writing. They illustrate editorial choices,
not mandatory templates or quotations from the sources. For example:

> Before: «Desideriamo informarLa che abbiamo provveduto a ripristinare l'accesso al portale».
>
> After: «Abbiamo ripristinato l'accesso al portale».

In a complete email, keep the appropriate greeting, form of address and request
to verify access. Do not add a guarantee of permanent resolution. In ticket
replies, put the proposal first when the surrounding conversation establishes
the context, but retain new findings, numbers, evidence and requested detail.

### Sources and attribution

| Reference | Contribution and limits |
|---|---|
| [blader/humanizer, SKILL.md at the reconciled commit](https://github.com/blader/humanizer/blob/8c307f367c91bd974002f10f2be2965d642c13df/SKILL.md), Siqi Chen, v3.1.0 | Upstream writing patterns, selectively reconciled into the existing derivative. The upstream catalog has 26 patterns; local grouping has 25 and retains its own fidelity, typography and file-authorization rules. |
| [Upstream changelog](https://github.com/blader/humanizer/blob/8c307f367c91bd974002f10f2be2965d642c13df/CHANGELOG.md) and [MIT license](https://github.com/blader/humanizer/blob/8c307f367c91bd974002f10f2be2965d642c13df/LICENSE) | Change history and license, including Copyright (c) 2025 Siqi Chen. The complete notice is distributed in the skill's `references/upstream-license.txt`. |
| Angela Ferrari, [*La semplicità sintattica in prospettiva testuale. Riflessioni a partire dalla Guida alla redazione degli atti amministrativi*](https://accademiadellacrusca.it/it/contenuti/la-semplicit-sintattica-in-prospettiva-testuale-riflessioni-a-partire-dalla-guida-alla-redazione-deg/9234), Accademia della Crusca, 19 March 2021 | Read on 23 October 2026. Supports evaluating syntax, word order, passive voice and implicit subjects in their textual and communicative context. It is guidance on Italian writing, not a study of AI detection. |
| [Wikipedia: Signs of AI writing, revision 1377577399](https://en.wikipedia.org/w/index.php?title=Wikipedia:Signs_of_AI_writing&oldid=1377577399) | Historical reference inherited from the previous refresh. This update did not reverify the revision or the Italian research citations already in the profile. |

The [reconciliation record](../superpowers/reports/2026-10-23-text-humanizer-upstream.md)
maps every upstream pattern to its local owner and retains source fingerprints,
intentional differences and verification evidence. The profile is distributed on
all five hosts. Static tests verify mandatory Italian-profile loading, fidelity
guards and shipped-reference parity; they do not establish independent linguistic
validation or guarantee the naturalness of every model-generated rewrite.

---

## Commands

### `/text-humanizer:humanize-text`

The plugin's own command. It loads `text-humanizer:anti-ai-writing-patterns` and follows its `references/humanize.md`: remove AI writing traces from text through the `text-humanizer` agent, then offer to write the result.

```
/text-humanizer:humanize-text path/to/article.md
/text-humanizer:humanize-text "paste prose directly here"
```

What were flags are signals in the request: a register stated with the target (`docs`, `business` or `personal`) sets it, otherwise the agent infers it; asking for a score or quality rating adds the self-assessed quality score.

With a file, the agent reads it without writing; the method shows the report, then asks whether to overwrite the file, write a new one, or only show the result. For source code readability use `/daodan:refactor-code` instead.

The method passes relevant supplied conversation messages separately from the
target so that reply-context editing does not rely on an unseen conversation.
A missing or unreadable file is reported as a blocker, not rewritten as prose.
If the host has no question tool, the coordinator presents the write-back choices
in its reply and waits for explicit consent. These are instruction contracts,
not mechanically enforced filesystem restrictions.

---

## Ecosystem Integration

Consumers in this marketplace:

- **digital-marketing**: `/digital-marketing:llm-seo-audit` and the `llm-seo-optimize` agent route AI-sounding copy to `/text-humanizer:humanize-text`; `review-reply-method` loads the skill directly.
- **business**: the `business-planner` agent has the agent rewrite the GTM strategy deliverable in place before hand-off.

Consumers in [Daodan](https://github.com/acaprino/daodan), which requires this plugin as `text-humanizer@shinatama`:

- **project-knowledge**: its guide and README methods route requested voice editing to this agent in the docs register. Document structure remains the knowledge editor's responsibility. The brief identifies text-only or in-place delivery and preserves facts, tables, citations and the author's intentional voice; a second voice pass is not mandatory.
- **project-lifecycle**: reuses the voice editor when an authorized knowledge operation needs it; an extra voice pass is not automatic.

**Routing boundary:** Daodan's clean-code recommends this plugin for prose targets. Its source-code readability method has no hard dependency on text-humanizer.

---

**Related:** [business](business.md) (GTM deliverables) | [digital-marketing](digital-marketing.md) (answer-engine copy)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `2.2.0`. **Source:** [plugin.toml](<../../plugins/text-humanizer/plugin.toml>).

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
| Skill | `text-humanizer:anti-ai-writing-patterns` | Catalog of 25 local writing patterns, ground rules against invented content, register table and language policy. TRIGGER WHEN: editing or reviewing prose to remove AI traces, or when asked to humanize text. | [anti-ai-writing-patterns](<../../plugins/text-humanizer/skills/anti-ai-writing-patterns/SKILL.md>) |
| Role | `text-humanizer:text-humanizer` | Editor for any language: uses 25 local writing patterns to improve prose, never inventing content. TRIGGER WHEN: dispatched by the humanize method of anti-ai-writing-patterns (/text-humanizer:humanize-text) or by another coordinator, text sounds AI-generated and needs humanization, or the user asks to humanize prose/text. DO NOT TRIGGER WHEN: the task involves refactoring source code (use /daodan:refactor-code instead). | [text-humanizer](<../../plugins/text-humanizer/roles/text-humanizer.md>) |
| Workflow | `text-humanizer:humanize-text` | Make a text read naturally, removing the patterns of machine writing, without inventing content. TRIGGER WHEN: the user asks to humanize, rewrite naturally or de-AI a text or a file. DO NOT TRIGGER WHEN: code is to be refactored (use /daodan:refactor-code) or documentation written (use /daodan:write-docs). | [humanize-text](<../../plugins/text-humanizer/workflows/humanize-text.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `text-humanizer:humanize-text`

**Arguments:** <code>&lt;text or file&gt;</code>

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
