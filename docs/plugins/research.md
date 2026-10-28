# Research Plugin

> Scientific project research with papers, revision history and Science Mode, plus deep web research and quick lookups. The existing web research pipeline keeps its web-only scope.

Start with the [research dossier](research/README.md) for scientific commands,
ON/OFF, refresh history, hook coverage, dependencies and validation. The guide
below retains the existing team-research workflow.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Command

### `/research:team-research`

| | |
|---|---|
| **Invoke** | `/research:team-research "<question>" [--depth auto\|quick\|standard\|deep] [--no-clarify] [--auto] [--out <file-or-dir>] [--backend auto\|websearch\|serper] [--domain <hint>]` |
| **Writes** | `research/<YYYY-MM-DD>-<slug>.md` (or `--out`) and `<stem>.researchers.md` beside it |

Phases: pre-flight (backend detection), clarify (2-4 questions in one call, only when the question is ambiguous; `--no-clarify` skips), plan (sub-questions with source families and boundaries, shown for approval; `--auto` skips both gates), wave 1 (one `deep-researcher` per sub-question, parallel), gap analysis (verifiers on contradictions; at `deep` a targeted wave 2), synthesis (long-form report in prose), citation check (every claim resolves to a source a researcher read), deliver (file + companion + chat summary).

| Tier | Researchers | Pages read | Waves | Per-researcher budget |
|---|---|---|---|---|
| `quick` | 1-2 | ~10 | 1 | 8 searches / 6 pages / 2 rounds |
| `standard` | 3-5 | 30-60 | 1 + verifiers | 15 / 12 / 4 |
| `deep` | 6-12 | 100+ | 2 + verifiers | 25 / 20 / 6 |

`auto` picks the tier from the question; a one-fact question is answered by `quick-searcher` directly with no run. Report sections: run header, executive summary, key findings, one section per sub-question, contradictions and resolutions, confidence and limitations, sources (only pages actually read), methodology (the approved plan verbatim, per-researcher budgets and exit reasons).

```
/research:team-research "Best practices for WebSocket reconnection in 2026"
/research:team-research "GDPR retention rules for transaction logs" --domain law --depth deep
/research:team-research "Should we migrate from REST to gRPC?" --auto --out docs/research/
```

## Using it

### A first run

```
/research:team-research "How do Rust, Go and Zig handle error propagation, and what do practitioners complain about in each?"
```

What you will see, in order:

1. **A clarification prompt, only if the question is ambiguous.** Up to four multiple-choice questions in one dialog (scope, audience, time window, jurisdiction, what a good answer looks like). A clear question skips this step and the lead says so in one line. Answer with the `Other` field when none of the choices fit.
2. **The research plan**, as a dialog with three options: `Approve` runs it; `Change depth` re-plans at another tier; `Edit the plan` takes free text (drop a sub-question, add one, narrow the time window), merges it, and shows the plan once more. The plan lists the restated question, the tier and why, the backend, the sub-questions with their source families and boundaries, the researcher count, estimated pages read and time, and the output path.
3. **The run.** Researchers spawn in one batch; at `deep` a second batch follows the gap analysis. Nothing is printed between the plan and the delivery beyond the spawn activity the session already shows. The plan's estimated time is the figure to go by.
4. **The delivery**: run header, executive summary, the two file paths and the run metadata (tier, researchers per wave, pages read, backend, wall time, failures and re-spawns). The full report is in the file.

### Choosing the depth

`--depth auto` (the default) reads the question: one well-defined question with a few authoritative answers gets `quick`, a comparison or a "how do people do X" gets `standard`, an open-ended or decision-grade question gets `deep`. Force a tier when you know better: `--depth quick` for a cheap first pass you may deepen later, `--depth deep` when the report is going to drive a decision and you want the second wave and 100+ pages read. A single-fact question ("what is the default port of PostgreSQL") is not a research run at all: the lead answers it through `quick-searcher` with one source and writes no file.

### Reading the output

- `research/<date>-<slug>.md` is the report. Start from the executive summary and key findings; every `[n]` resolves to the Sources section, which lists only pages a researcher actually read, each with the date the page carries and an authority rank from 1 (official documentation) to 5 (general blog). The confidence and limitations section says what rests on one source, what could not be verified, and which primary sources were paywalled or bot-blocked, by URL, so you can open them yourself.
- `research/<date>-<slug>.researchers.md` is the companion: every researcher and verifier report verbatim, in spawn order. Use it to audit a claim back to the researcher that found it, or to see what was searched and not found.
- The methodology appendix holds the approved plan verbatim and, per researcher, the exit reason (`saturated`, `budget-exhausted`, `target-not-found`, `error`) and the budget used. A report whose researchers mostly exited `budget-exhausted` is one worth re-running at the next tier.

### Unattended runs

`--auto` skips both gates: the plan is printed and the run starts. Combine it with `--out` to land the report where you want it:

```
/research:team-research "State of WebGPU support across browsers" --auto --depth standard --out docs/research/
```

`--out` takes a file path or a directory; a directory gets the default filename inside it. `--no-clarify` is the half-way option: no clarification questions, but the plan still waits for approval.

### Enabling the serper.dev backend (optional)

By default the plugin searches with the session's native `WebSearch`. Adding a serper.dev key switches discovery to Google's index and adds the `news` and `scholar` verticals, date filters and up to 100 results per call; the report header then says `Backend: serper`.

The short way: get a key at https://serper.dev (2,500 free queries, no card), then run

```
/research:team-research "<your question>" --backend serper
```

With no key set, that asks for one in chat: paste it into the free-text field and the run continues on serper. The key is saved to `~/.serper_key`, so every later run finds it and the question is asked once, not every time. The other two options in that dialog are to continue on native search for this run, or to cancel.

Two things worth knowing before you paste: a key typed in chat is in the session transcript, and the file is written readable only by your user (a real permission on POSIX; on Windows it inherits your profile's ACL). If you would rather the key never appear in a transcript, set it in the environment instead, which takes precedence over the file:

```
export SERPER_API_KEY=...          # bash, zsh; put it in your profile to persist
$env:SERPER_API_KEY = "..."        # PowerShell
```

Either way `--backend auto` (the default) uses serper whenever a key is available, `--backend websearch` forces the native tool even when one is, and `--backend serper` forces serper. To check what the plugin can see, or to save a key by hand:

```
python plugins/research/skills/web-search-techniques/scripts/websearch.py --check-key
printf '%s' YOUR_KEY | python plugins/research/skills/web-search-techniques/scripts/websearch.py --set-key
```

`--check-key` makes no network call and costs no credit. To revoke, delete `~/.serper_key` (and unset the environment variable). Unattended runs never ask: `--backend serper --auto` with no key stops with the setup line rather than waiting on a question nobody is there to answer.

Cost per run, order of magnitude: `standard` makes 45-75 serper calls, `deep` 150-300; a call returning more than 10 results costs two credits. The plan states the approximate count before you approve it. Serper never replaces reading: snippets qualify a page for fetching, and only pages actually read are cited.

### When it stops instead of running

| Message | Cause | What to do |
|---|---|---|
| "No search backend available" | `WebSearch` is not in the session's toolset and no serper key is set | Enable web search for the session, or set `SERPER_API_KEY` |
| The `websearch.py` setup line | `--backend serper --auto` with no key, or the service failed | Paste a key when asked (an attended run offers this), set one as above, or drop the flag to use native search |
| The lead says the question is about local code and stops | The question is about local code; the command researches the web only | Use Grep, Glob, or a codebase-oriented plugin |
| The lead lists which researchers failed and why, and stops | More than half the researchers of a wave failed (offline, blocked, quota) | Fix the connectivity and re-run; nothing is synthesized from a failed wave |

### Using the agents directly

`deep-researcher` can be invoked on its own for one focused investigation ("investigate X in depth across several sources, with citations"): it runs at the `standard` per-researcher budget and returns the same compressed report it would return to the lead. `quick-searcher` answers single facts with one source, and flags when a question actually needs a full run.

## Agents

### `deep-researcher`

Iterative investigator for one sub-question: orient with broad queries, read the pages that matter, keep a ledger (claims, sources with dates and authority rank, contradictions, open threads), narrow round by round, stop at saturation or budget, return a compressed cited report. Spawned by the command; directly invokable for one focused investigation.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, WebSearch, WebFetch, Bash |

### `quick-searcher`

Single-fact lookups (1-3 searches, lead with the answer) and the verifier the command spawns to settle one contested claim with a third independent source.

| | |
|---|---|
| **Model** | `sonnet` |
| **Tools** | Read, WebFetch, WebSearch, Bash |

## Skill

### `web-search-techniques`

Query formulation, source authority ranking, the two search backends, reading rules (WebFetch, then `webfetch.py` on a bot-block, browser only if the `playwright` plugin's MCP tools happen to be available), anti-loop rules. Loaded by both agents and the command.

## Scripts

| Script | Purpose |
|---|---|
| `skills/web-search-techniques/scripts/websearch.py` | Optional serper.dev backend. Used when a key is available or `--backend serper`; `--vertical search\|news\|scholar`, `--num`, `--since h\|d\|w\|m\|y`, `--gl`, `--hl`, `--page`, `--timeout`, `--json`. `--check-key` reports availability without a network call; `--set-key` saves a key from stdin to `~/.serper_key`. Reads `SERPER_API_KEY` first, then that file. Exit 2 when no key is available, 1 on HTTP errors. Stdlib only |
| `skills/web-search-techniques/scripts/webfetch.py` | Bot-block fallback fetcher (Chrome TLS impersonation via curl_cffi, httpx fallback) |

Backend rule: `auto` uses serper when a key is available, native `WebSearch` otherwise; the choice is stated in the plan, in each researcher report and in the report header. Serper never replaces reading: snippets qualify a page for fetching, only read pages are cited.

---

**Related:** [digital-marketing](digital-marketing.md) (SEO research and content strategy) | [learning](learning.md) (turn findings into a mind map)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.0.1`. **Source:** [plugin.toml](<../../plugins/research/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [work-controller](<work-controller.md>) |
| Direct external | None |
| Local closure (2) | [research](<research.md>), [work-controller](<work-controller.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `network.fetch`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`, `hooks.lifecycle`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `research:web-search-techniques` | Web research methodology: query formulation, source authority ranking, WebSearch/serper.dev backends, bot-block fallbacks and anti-loop rules. TRIGGER WHEN: performing web research in quick-searcher, deep-researcher or /research:team-research. DO NOT TRIGGER WHEN: searching a local codebase (use Grep or Glob directly). | [web-search-techniques](<../../plugins/research/skills/web-search-techniques/SKILL.md>) |
| Skill | `research:science-based-approach` | Build and refresh a project's scientific evidence base from papers actually read, with traceable claims, local test protocols and immutable research history. Use for explicit scientific research or substantive brainstorming, specifications, ADR/FRD and problem solving when evidence can change the decision. | [science-based-approach](<../../plugins/research/skills/science-based-approach/SKILL.md>) |
| Role | `research:deep-researcher` | Iterative web investigator for one research sub-question: searches, reads primary sources, maintains a dated claim ledger and returns a cited report. TRIGGER WHEN: spawned by /research:team-research with a spawn block, or asked to investigate a question in depth across multiple web sources with citations. DO NOT TRIGGER WHEN: single-fact lookup (use quick-searcher), multi-question research run (use /research:team-research), or local codebase work. | [deep-researcher](<../../plugins/research/roles/deep-researcher.md>) |
| Role | `research:quick-searcher` | Fast web search agent for single-fact lookups and the verifier spawned by /research:team-research to settle contested claims. TRIGGER WHEN: asking for a single fact, definition, stat, URL or confirmation answerable in 1-3 web searches, or spawned with a verifier block. DO NOT TRIGGER WHEN: multi-source synthesis (use deep-researcher or /research:team-research) or local codebase work. | [quick-searcher](<../../plugins/research/roles/quick-searcher.md>) |
| Workflow | `research:team-research` | Deep web research run: plan sub-questions, spawn parallel iterative researchers, verify contradictions and write a cited report to disk. TRIGGER WHEN: the user asks for a deep multi-source web research report on a topic. DO NOT TRIGGER WHEN: single-fact lookup (use research:quick-searcher) or local codebase analysis (use codebase-map). | [team-research](<../../plugins/research/workflows/team-research.md>) |
| Workflow | `research:science-research` | Research a concrete problem through academic sources and publish a traceable scientific record. | [science-research](<../../plugins/research/workflows/science-research.md>) |
| Workflow | `research:update-research` | Recheck scientific research, preserve revision history and identify superseded evidence and affected decisions. | [update-research](<../../plugins/research/workflows/update-research.md>) |
| Workflow | `research:science-mode` | Read or change the project's Science Mode; default ON, explicit on/off, empty input reports status. | [science-mode](<../../plugins/research/workflows/science-mode.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `research:team-research`

**Arguments:** <code>\"&lt;question&gt;\" [--depth auto&#124;quick&#124;standard&#124;deep] [--no-clarify] [--auto] [--out &lt;file-or-dir&gt;] [--backend auto&#124;websearch&#124;serper] [--domain &lt;hint&gt;]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `team-research-completed` |
| Artifacts | `team-research-report` |
| Schemas | None declared |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [team-research.toml](<../../plugins/research/workflows/team-research.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

#### `research:science-research`

**Arguments:** <code>&lt;problem&gt;</code>

| Contract | Value |
|---|---|
| Inputs | `repository`, `user-request` |
| Outcomes | `science-research-completed` |
| Artifacts | `science-research-result` |
| Schemas | [work-controller/contracts/work.toml](<../../plugins/work-controller/contracts/work.toml>) |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [science-research.toml](<../../plugins/research/workflows/science-research.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

#### `research:update-research`

**Arguments:** <code>&lt;topic, identity or tutte&gt;</code>

| Contract | Value |
|---|---|
| Inputs | `repository`, `user-request` |
| Outcomes | `update-research-completed` |
| Artifacts | `science-update-result` |
| Schemas | [work-controller/contracts/work.toml](<../../plugins/work-controller/contracts/work.toml>) |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [update-research.toml](<../../plugins/research/workflows/update-research.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

#### `research:science-mode`

**Arguments:** <code>[on&#124;off]</code>

| Contract | Value |
|---|---|
| Inputs | `repository`, `user-request` |
| Outcomes | `science-mode-completed` |
| Artifacts | `science-mode-result` |
| Schemas | [work-controller/contracts/work.toml](<../../plugins/work-controller/contracts/work.toml>) |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [science-mode.toml](<../../plugins/research/workflows/science-mode.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/research](<../../exports/claude/plugins/research>) | `native` | `team-research: native-team`, `science-research: native-team`, `update-research: native-team`, `science-mode: native-team` |
| copilot | [exports/copilot/plugins/research](<../../exports/copilot/plugins/research>) | `native` | `team-research: parallel-subagents`, `science-research: parallel-subagents`, `update-research: parallel-subagents`, `science-mode: parallel-subagents` |
| codex | [exports/codex/plugins/research](<../../exports/codex/plugins/research>) | `adapted` | `team-research: parallel-subagents`, `science-research: parallel-subagents`, `update-research: parallel-subagents`, `science-mode: parallel-subagents` |
| pi | [exports/pi/plugins/research](<../../exports/pi/plugins/research>) | `adapted` | `team-research: parallel-subagents`, `science-research: parallel-subagents`, `update-research: parallel-subagents`, `science-mode: parallel-subagents` |
| opencode | [exports/opencode/plugins/research](<../../exports/opencode/plugins/research>) | `native` | `team-research: parallel-subagents`, `science-research: parallel-subagents`, `update-research: parallel-subagents`, `science-mode: parallel-subagents` |

<!-- daodan:reference:end -->
