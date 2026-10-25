---
description: 'Audit pages for generative search / answer engine citation readiness (AI Overviews, Perplexity, ChatGPT/Claude Search, Bing Copilot). TRIGGER WHEN: auditing AI search visibility, AI-bot crawler allowlists, E-E-A-T, llms.txt, JSON-LD citation schemas, passage extractability or prompt-injection hardening. DO NOT TRIGGER WHEN: traditional SERP ranking SEO (use /digital-marketing:seo-audit) or copy tone/voice (use content-marketer).'
argument-hint: '<url or local path> [--focus <comma-separated: crawlers,eeat,schema,passages,injection | all>] [--strict-mode]'
---

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

# LLM SEO / Answer Engine Optimization Audit

Invokes the `llm-seo-optimize` agent to audit a site for answer-engine discoverability and citation-worthiness. Different from `/digital-marketing:seo-audit` (traditional SERP ranking): this optimizes for getting **quoted inside an LLM-generated answer**.

## CRITICAL RULES

1. **Delegate to the `llm-seo-optimize` agent**. This command is a thin wrapper -- the agent owns the full 6-phase audit.
2. **Verify live, not just code**. For a live URL, use the Playwright MCP tools (the `playwright` plugin, a declared dependency) to confirm crawler access (`robots.txt` live fetch), JSON-LD presence, and rendered passage extractability.
3. **Write output to `.aeo-audit/` for persistence** so re-runs can diff against the baseline.
4. **Never fabricate crawler policies**. If `robots.txt` cannot be fetched, state the gap explicitly.
5. **Complementary to `/digital-marketing:seo-audit`, not a replacement**. Traditional SEO and AEO require different optimizations: flag the overlap, not duplication.

## Procedure

### 1. Parse arguments

- `<url or local path>`: required target -- live URL or path to static site / built HTML output
- `--focus`: restrict the audit to a subset of dimensions. Values are comma-combinable (`--focus schema,eeat`). Default: `all`, which runs every phase
  - `crawlers` -- the AI-bot robots.txt allowlist check
  - `eeat` -- E-E-A-T signal audit (authorship, citations, dates)
  - `schema` -- JSON-LD / Schema.org structured data, plus citation readiness
  - `passages` -- passage-level extractability (direct-answer paragraphs, tables, bullet lists)
  - `injection` -- prompt-injection hardening (hidden text, invisible CSS, comment payloads)
- `--strict-mode`: report-level severity escalation. Every Warning is raised to Critical and the report opens with an explicit `VERDICT: PASS` / `VERDICT: FAIL` line, FAIL when any Critical remains

### 2. Spawn the agent

Invoke `digital-marketing:llm-seo-optimize` with the target, focus, and strict-mode flag. The agent loads its own knowledge base and runs the 6-phase protocol.

### 3. Report

Agent writes `.aeo-audit/REPORT.md` with:

```
# AEO Audit -- <site/page> -- <date>

## Summary
- Pages audited: N
- Blocked from: <list of engines with robots.txt denies>
- E-E-A-T score: X/5
- Extractability score: X/5
- JSON-LD coverage: P%

## Critical findings
- [CRITICAL] <page:line / selector> <issue>

## Per-page findings
...

## Cross-cutting recommendations
...

## Tracking setup
- Analytics filters for AI-referral hostnames: chatgpt.com (legacy chat.openai.com), perplexity.ai, claude.ai, copilot.microsoft.com, gemini.google.com
- Weekly brand-mention query set for citation-share tracking
```

## Typical flow

```
# Full audit against a live URL
/digital-marketing:llm-seo-audit https://example.com

# Focus on Schema + E-E-A-T only
/digital-marketing:llm-seo-audit https://example.com --focus schema,eeat

# Static site audit
/digital-marketing:llm-seo-audit ./dist/

# Strict grading: warnings become critical, report opens with PASS/FAIL
/digital-marketing:llm-seo-audit https://example.com --strict-mode
```

## Complementary commands

Run alongside traditional SEO tooling for a complete picture:

| Command | Purpose | Overlap with AEO |
|---------|---------|------------------|
| `/digital-marketing:seo-audit` | Technical SEO (Core Web Vitals, meta tags, sitemap, redirects, SERP ranking) | Low: traditional ranking signals |
| `/digital-marketing:content-strategy` | Conversion / CTA / tone / funnel audit | Medium: answer-worthiness often correlates with clarity |
| `/digital-marketing:ga4-audit` | GA4 + GTM + Consent Mode v2 verification | Measurement only: AEO needs AI-referrer tracking set up in GA4 |
| **`/digital-marketing:llm-seo-audit`** | **AEO / answer-engine optimization** | -- |

## Synergies

- Deep knowledge base -> `digital-marketing:llm-seo-optimize` agent (the actual worker)
- Structured data validation alongside broader checks -> `/digital-marketing:seo-audit`
- Measurement setup -> `digital-marketing:ga4-implementation-expert` agent (AI-referrer tracking)
- Humanizing AI-sounding copy to raise E-E-A-T -> `/text-humanizer:humanize-text`
- Playwright-based live verification -> the `playwright` plugin (Microsoft's Playwright MCP server)
