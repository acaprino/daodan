---
description: 'Audit whether answer engines (AI Overviews, AI Mode, ChatGPT Search, Perplexity, Copilot, Claude) can reach, select and correctly cite a site. TRIGGER WHEN: auditing AI search visibility, AI-bot crawler or CDN access, Search Console generative AI settings, E-E-A-T, answerability of customer questions, JSON-LD accuracy, llms.txt questions or prompt-injection hardening. DO NOT TRIGGER WHEN: traditional SERP ranking SEO (use /digital-marketing:seo-audit) or copy tone/voice (use content-marketer).'
argument-hint: '<url or local path> [--focus <comma-separated: crawlers,eeat,schema,passages,injection | all>] [--strict-mode]'
---

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

<!-- Generated by the Daodan compiler for opencode. Edit the kernel, never this file. -->

# LLM SEO / Answer Engine Optimization Audit

Invokes the `llm-seo-optimize` agent to audit whether answer engines can reach a site, select its pages and cite them correctly. Different from `/digital-marketing:seo-audit` (traditional SERP ranking), although most of the groundwork is shared: answer engines retrieve from search indexes first.

## CRITICAL RULES

1. **Delegate to the `llm-seo-optimize` agent**. This command is a thin wrapper: the agent owns the full 6-phase audit, the report format and the measurement plan.
2. **Verify live, not just code**. For a live URL, use the Playwright MCP tools (the `playwright` plugin, a declared dependency) to fetch `robots.txt`, read response headers, check JSON-LD and render the pages.
3. **Write output to `.aeo-audit/` for persistence** so re-runs can diff against the baseline.
4. **Never fabricate crawler policies or settings**. If `robots.txt`, the CDN bot policy or the Search Console setting cannot be read, report it as `not confirmed`.
5. **Probe a WAF only with authorization**. Requests with a bot's user agent run only when the user owns the site or confirms authorization, and their result describes unverified traffic, not the real bot.

## Procedure

### 1. Parse arguments

- `<url or local path>`: required target, a live URL or a path to a static site / built HTML output
- `--focus`: restrict the audit to a subset of dimensions. Values are comma-combinable (`--focus schema,eeat`). Default: `all`, which runs every phase
  - `crawlers`: eligibility and access (indexing, snippet controls, Search Console control, robots.txt per user agent, CDN/WAF, discovery)
  - `eeat`: E-E-A-T signals (authorship, dates, citations, evidence)
  - `schema`: JSON-LD accuracy and citation readiness
  - `passages`: answerability of the customers' real questions
  - `injection`: prompt-injection hardening (non-rendered HTML, hidden text, persuasion aimed at engines)
- `--strict-mode`: report-level severity escalation. Every Warning is raised to Critical and the report opens with an explicit `VERDICT: PASS` / `VERDICT: FAIL` line, FAIL when any Critical remains

### 2. Spawn the agent

Invoke `digital-marketing:llm-seo-optimize` with the target, focus, and strict-mode flag. The agent runs its 6-phase protocol.

### 3. Report

The agent writes `.aeo-audit/REPORT.md` in its OUTPUT FORMAT, closing with the measurement setup: the Search Console Generative AI performance report, Bing Webmaster Tools AI Performance, GA4's AI Assistant channel and the repeated sampling of the customer question set.

## Typical flow

```
# Full audit against a live URL
/digital-marketing:llm-seo-audit https://example.com

# Access only: indexing, robots.txt, CDN, Search Console control
/digital-marketing:llm-seo-audit https://example.com --focus crawlers

# Static site audit
/digital-marketing:llm-seo-audit ./dist/

# Strict grading: warnings become critical, report opens with PASS/FAIL
/digital-marketing:llm-seo-audit https://example.com --strict-mode
```

## Complementary commands

Run alongside traditional SEO tooling for a complete picture:

| Command | Purpose | Overlap with AEO |
|---------|---------|------------------|
| `/digital-marketing:seo-audit` | Technical SEO (Core Web Vitals, meta tags, sitemap, redirects, SERP ranking) | High: indexing and crawlability are prerequisites for every Google AI feature |
| `/digital-marketing:content-strategy` | Conversion / CTA / tone / funnel audit | Medium: answering customer decisions serves both |
| `/digital-marketing:ga4-audit` | GA4 + GTM + Consent Mode v2 verification | Measurement only: AI traffic arrives through GA4's AI Assistant channel |
| **`/digital-marketing:llm-seo-audit`** | **AEO / answer-engine optimization** | |

## Synergies

- Deep knowledge base: `digital-marketing:llm-seo-optimize` agent (the actual worker)
- Structured data validation alongside broader checks: `/digital-marketing:seo-audit`
- Measurement setup: `digital-marketing:ga4-implementation-expert` agent (AI traffic channels)
- Humanizing AI-sounding copy: `/daodan:humanize-text`
- Playwright-based live verification: the `playwright` plugin (Microsoft's Playwright MCP server)
