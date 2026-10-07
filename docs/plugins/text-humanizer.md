# Text Humanizer Plugin

> Remove AI writing traces from any prose, in any language, without inventing content. A self-contained leaf plugin (zero dependencies) extracted from digital-marketing in marketplace 13.3.0, consumed by digital-marketing, project-knowledge, business, and clean-code.

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

### `/humanize-text`

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

- **digital-marketing**: `/llm-seo-audit` and the `llm-seo-optimize` agent route AI-sounding copy to `/text-humanizer:humanize-text` to raise E-E-A-T credibility; `review-reply-method` loads the skill directly.
- **project-knowledge**: its guide and README methods route requested voice editing to this agent in the docs register. Document structure remains the knowledge editor's responsibility. The brief identifies text-only or in-place delivery and preserves facts, tables, citations and the author's intentional voice; a second voice pass is not mandatory.
- **business**: the `business-planner` agent has the agent rewrite the GTM strategy deliverable in place before hand-off.
- **clean-code**: routes prose targets here (`/clean-code:clean-code` handles source code, `/text-humanizer:humanize-text` handles text).

---

**Related:** [digital-marketing](digital-marketing.md) (SEO and content workflows) | [project-knowledge](project-knowledge.md) (documentation generation) | [clean-code](clean-code.md) (source code readability)
