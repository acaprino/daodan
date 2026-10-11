---
name: web-search-techniques
description: >
  Knowledge base for web research: query formulation, source authority ranking, the two search backends (native WebSearch, optional serper.dev through websearch.py), reading pages with WebFetch and the webfetch.py bot-block fallback, and the anti-loop rules. Used by quick-searcher, deep-researcher and /research:team-research.
  TRIGGER WHEN: performing web research with WebSearch, WebFetch, or the research plugin's scripts.
  DO NOT TRIGGER WHEN: searching a local codebase (use Grep or Glob directly).
---

> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# Web Search Techniques

Shared knowledge base for `research:quick-searcher`, `research:deep-researcher` and the `/research:team-research` lead. Scope: web-only. Covers query formulation, source authority, tool usage, bot-block fallback, and anti-loop rules.

## Query Formulation

Extract core concepts from the question before querying:
- Identify synonyms and domain terminology (e.g. "authentication": auth, login, signin, session, token, jwt, oauth, credentials)
- Account for abbreviations and full forms
- Add the year ("2026") when the query has temporal dependency
- Add "official" or "documentation" to push toward authoritative sources
- Quote exact phrases for precise matches
- Use `site:` to restrict to known-good domains (e.g. `site:developer.mozilla.org`)

Start broad, narrow progressively. Overly specific first queries miss adjacent information. Each refinement round incorporates terms surfaced in prior results.

## Source Authority Ranking

Rank every source before citing:

1. **Official documentation sites and API references**: highest authority
2. **RFC and specification documents**: canonical for standards
3. **GitHub issues, discussions, and source code**: authoritative for specific libraries
4. **Peer-reviewed or community-validated content**: Stack Overflow with high votes, maintainers' blogs
5. **General blog posts and tutorials**: use only when nothing better exists
6. **Deprioritize**: SEO content farms, AI-generated summaries, scraped aggregators

Currency checks:
- Last modified date on the page
- Version numbers cited vs latest release
- Deprecation warnings

## Search Backends

Two backends produce candidate pages. Neither produces claims: only a page that was read does.

| Backend | When | How |
|---|---|---|
| Native host network search | Default. Always available when the tool is in the toolset | The tool call, with the operators below |
| serper.dev (Google) | A key is available, or `--backend serper` | `python "${PLUGIN_ROOT}/skills/web-search-techniques/scripts/websearch.py" "<query>" [--vertical search|news|scholar] [--num N] [--since h|d|w|m|y] [--gl CC] [--hl LANG] [--page P] [--json]` through the host shell binding |

Selection rule (the lead decides once per run and writes it into every spawn prompt): `auto` means serper when a key is available, else native. The chosen backend is stated in the plan, in each researcher report and in the final report header.

Where the key comes from, in order: `SERPER_API_KEY` in the environment, then `~/.serper_key`. Ask the script rather than looking yourself: `python "${PLUGIN_ROOT}/skills/web-search-techniques/scripts/websearch.py" --check-key` exits 0 when a key is available and 2 when none is, makes no network call, and costs no credit. A key the user pastes in chat is saved by piping it to `--set-key`, which is the lead's job at pre-flight and nobody else's: researchers never see a key, they call the script and the script reads it. Never echo a key, never write one into a prompt, a report or any other file, and never read the key file yourself.

A run never silently upgrades or degrades: with `auto` and no key the backend is native search and the plan says so, and a forced `--backend serper` with no key either collects one in chat or stops with the setup line, never quietly searches elsewhere.

What serper earns its call for:
- `--vertical scholar` for academic threads, `--vertical news --since w|m` for recency threads
- `--num 30` to `50` on the orient round, to map a topic's vocabulary in one call (above 10 results costs 2 credits; the script says so on stderr)
- `--since` for "what changed lately" questions; `before:YYYY-MM-DD` / `after:YYYY-MM-DD` inside the query for exact windows
- Cross-index corroboration: a claim whose sources surface on both indexes ranks above one found on one index only

Operators both backends honour: `site:` (restrict to a domain), `"exact phrase"`, `-term` (exclude), `filetype:pdf`, a year token (`2026`) for temporal queries, `official` or `documentation` to bias toward primary sources, version numbers when relevant (`react 19`).

Cost note (checked 2026-08-23): serper.dev gives 2,500 free queries, then $1.00 per 1,000 on the entry plan, down to $0.30 per 1,000 at volume; credits are deducted only on successful responses. A `standard` run makes on the order of 45-75 calls, a `deep` run 150-300. Tavily and Exa are LLM-oriented alternatives (LLM-ready snippets, neural search) that would slot behind the same script interface; not built.

## Reading, Not Skimming

A search result is a candidate. A claim enters a researcher's ledger only from a page that was read:
1. Fetch the page through the active host network-fetch binding (prefer docs and primary sources; target anchors on long pages)
2. On a bot-block (403, 429, challenge page) or thin content (under ~200 useful characters), `python3 "${PLUGIN_ROOT}/skills/web-search-techniques/scripts/webfetch.py" <url>`
3. If the Playwright MCP tools of the `playwright` plugin are available and the page is a primary source the answer depends on, drive a real browser with them as the last resort (`browser_navigate`, then `browser_snapshot`); if they are not, record the URL under limitations and move on. This is a pointer, not a dependency.
4. Record: URL, title, the date the page carries, authority rank (below), and the claims taken from it

## host page-fetch binding Guidance

- Prefer documentation pages and API references over blog posts
- Evaluate fetched content: low-authority source means discard and re-search
- Large pages may be truncated: target specific sections (anchor URLs) when possible
- Track the accessed URL with date for citation

## webfetch.py Fallback

When the host network-fetch tool returns a bot-block (403, 429, Cloudflare challenge) or thin content (under ~200 chars of useful text), fall back to the plugin's stealth fetcher:

```bash
python3 "${PLUGIN_ROOT}/skills/web-search-techniques/scripts/webfetch.py" <url>
```

Behavior:
- Impersonates Chrome TLS fingerprint via curl_cffi
- Returns clean extracted text on stdout
- Exits 0 on success, 1 on timeout or error
- On failure, proceed without the result (do not retry in a loop)

Invocation options:
- `--timeout SECONDS` (default: 30)
- `--max-chars CHARS` (truncate output)
- `--raw` (return raw HTML instead of extracted text)

Requires the active host shell capability and a worker permission that allows executing this helper. Do not copy a foreign tool name into frontmatter.

## Anti-Loop Rules

- Never repeat the exact same query or search parameters
- If a search returns nothing, change terminology, broaden the regex, or switch tool/target
- Maximum 2 failed attempts per sub-topic before pivoting or escalating
- After 2 failed attempts on the same angle, document the gap and proceed with what you have
