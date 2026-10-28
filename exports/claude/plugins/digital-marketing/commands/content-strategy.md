---
description: 'Reviews whether the material actually persuades a visitor, not whether it is well built. TRIGGER WHEN: the user asks for a content, marketing, conversion, or CRO audit of a website, landing page, or funnel. DO NOT TRIGGER WHEN: the audit is technical SEO only (use /digital-marketing:seo-audit).'
---

<daodan_host_binding host="claude">
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

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# content-strategy

<!-- Generated by the Daodan compiler for claude. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **native-team**. Use native Agent Teams when they are enabled in this session;
otherwise dispatch the same roles as isolated subagents. Both paths satisfy the same contract, and
which one answered changes nothing a reader of the report can observe.
Declared worker isolation: **required**.

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
  Independent reviewers never read peer results before their own delivery; no worker runs in the coordinator's context.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A missing result is a recorded failure, never a silently shorter report.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `content-marketer`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:content-strategy-context`, `selection:audits`.
2. `audit`: one `content-marketer` per item of `selection:audits`, each in its own isolated context, in parallel where the host allows; barrier `all-delivered`; needs `scope`; consumes `artifact:content-strategy-context`; produces `artifact:content-strategy-findings`.
3. `synthesis`: runs in the orchestrating context; needs `audit`; consumes `artifact:content-strategy-findings`; produces `artifact:content-strategy-plan`.
4. `approval`: runs in the orchestrating context; needs `synthesis`; consumes `artifact:content-strategy-plan`; produces `artifact:content-strategy-approval`.
5. `apply`: runs in the orchestrating context; needs `approval`; consumes `artifact:content-strategy-approval`; produces `artifact:content-strategy-changes`.
6. `report`: runs in the orchestrating context; needs `apply`; consumes `artifact:content-strategy-context`, `artifact:content-strategy-findings`, `artifact:content-strategy-plan`, `artifact:content-strategy-changes`; produces `artifact:content-strategy-report`.

Role bindings:

- `content-marketer`: dispatch the installed `digital-marketing:content-marketer` agent by its qualified identity.
- `content-marketer`: dispatch the installed `digital-marketing:content-marketer` agent by its qualified identity.

The phase graph, the isolation and join policies and the record schemas are in
`contracts/content-strategy.workflow.toml`, which ships with this package.

## Method

# Content Strategy Audit

## CRITICAL RULES

1. **Execute phases in order.** Scope → Parallel Audit → Synthesis → Approval → Apply → Report.
2. **Write output files.** Each phase writes to `.content-strategy/` for persistence.
3. **Isolate every selected audit.** Phase 2 prefers parallel delivery through the host harness; a serial isolated topology preserves the same area selection and delivery barrier.
4. **Stop at checkpoint.** Get user approval before applying any changes.
5. **Use Playwright for live sites.** Browser tools for DOM, screenshots, responsive testing.
6. **Never enter plan mode.** Execute immediately.

## Pre-flight

### Dependency check (live sites only)

For live URL targets, this command uses the Playwright MCP tools (`browser_navigate`, `browser_snapshot`, `browser_take_screenshot`, `browser_resize`). If they are not available, print this and stop:

```
Missing required dependency: Playwright MCP (Microsoft, @playwright/mcp)

Live site analysis needs the Playwright MCP tools for DOM inspection,
screenshots, and responsive testing.

Install Microsoft's Playwright MCP server for the host you run in, then
run this again:
  Claude Code  claude plugin install playwright@claude-plugins-official
  Codex        codex mcp add playwright npx "@playwright/mcp@latest"
  VS Code      code --add-mcp '{"name":"playwright","command":"npx","args":["@playwright/mcp@latest"]}'
  Copilot CLI  /mcp add  (name playwright, command npx @playwright/mcp@latest)
  Pi           pi install npm:pi-mcp-adapter, then add the same server under
               "playwright" in mcpServers of ~/.config/mcp/mcp.json
  OpenCode     opencode mcp add playwright --global -- npx @playwright/mcp@latest
```

Do not fall back to a fetch-only analysis. Local files need no browser.

### Initialize

Create `.content-strategy/` directory. If it already exists, automatically rename the old one to `.content-strategy-archive-[timestamp]/` to prevent data loss, then create a fresh one. Do NOT ask for permission for this step.

Use the `content-marketer` agent for analysis.

## Phase 1: Audit Scope

### Parse flags

- `--focus <areas>`: comma-separated area names, resolved against the Phase 2 ownership map. Only the agents owning a requested area run; every area not requested is marked `not audited` in the Phase 3 table. Default: all areas
- `--social`: shorthand for `--focus social,images,video`, which runs Agent C alone
- `--strict-mode`: in Phase 3, promote every Important finding to Critical and open the plan with an explicit `VERDICT: PASS` / `VERDICT: FAIL` line. FAIL when any Critical remains

### Gather scope

1. **Read target** -- navigate to URL (Playwright) or read local files
2. **Identify page types** -- landing, product, blog, about, pricing, checkout, FAQ
3. **Understand the business** -- extract value proposition, target audience, offering
4. **Baseline metrics** -- page count, CTA count, form count, social links

**Output file:** `.content-strategy/01-scope.md`

### Shared context block

Assemble this once at the end of Phase 1. Every Phase 2 subagent prompt includes it verbatim, so it is written here and nowhere else:

```
## Scope
[Contents of .content-strategy/01-scope.md]

## Target
[URL or local path, plus the resolved focus areas]

## Page Contents
[Key page content: Playwright snapshot or file text, including OG and meta tag data]
```

Present scope summary and confirm focus areas.

---

## Phase 2: Parallel Audit (3 agents)

Build `selection:audits` from the requested areas: one item for each nonempty A, B or C ownership group below, each bound to `digital-marketing:content-marketer`. Use the host harness to dispatch one isolated reviewer per selected item with the shared context, only its owned areas, authorization and an intermediate report path `.content-strategy/audits/<A|B|C>.md`. Prefer parallel delivery when supported. Record every selected reviewer as delivered or failed before synthesis; missing output is a failed delivery, never a clean area. Workers cannot read peer findings or write the final report.

Area ownership, used to resolve `--focus`: Agent A owns `ux`, `cta`, `social-proof`, `pricing`, `forms`, `navigation`. Agent B owns `copy`, `seo-copy`, `microcopy`, `product-descriptions`. Agent C owns `social`, `images`, `video`. Skip any agent whose areas were all excluded, and tell the agents that do run to report only on the requested areas.

### Agent A: UX & Conversion Analysis

```text
Audit the UX patterns and conversion elements of this website/page.

[Shared context block from Phase 1, verbatim]

## Instructions
Evaluate:
1. **Page Layout**: Visual hierarchy, above-the-fold content, whitespace, content flow
2. **CTAs**: Presence, clarity, contrast, placement, urgency, primary/secondary hierarchy
3. **Social Proof**: Testimonials, reviews, trust badges, client logos, case studies, numbers
4. **Pricing**: Clarity, comparison table, anchoring, free trial CTA, FAQ, guarantee
5. **Forms**: Field count, labels, error handling, progress indicators, mobile-friendly
6. **Navigation**: Hierarchy, breadcrumbs, search, mobile menu, sticky header, footer

For each finding: severity (Critical/Important/Nice-to-have), element, issue, specific fix.
Note what's working well.

Return structured findings.
```

### Agent B: Content & Copy Analysis

```text
Audit the written content and copy of this website/page.

[Shared context block from Phase 1, verbatim]

## Instructions
Evaluate:
1. **Headlines**: Clarity (5-second test), benefit-driven, keyword presence, emotional triggers
2. **Body Copy**: Scannable, benefit-focused, objection handling, specificity, reading level
3. **Tone & Voice**: Consistency, audience-appropriate, brand alignment, authenticity
4. **SEO Copy**: Keyword density, internal links, meta descriptions, featured snippet targeting
5. **Microcopy**: Button labels, form hints, error messages, empty states, confirmations
6. **Product Descriptions**: Feature→benefit framing, specifications, comparisons, use cases

For each finding: severity, location, issue, specific rewrite suggestion.
Note what's working well.

Return structured findings.
```

### Agent C: Social Media & Visual Audit

```text
Audit the social media presence and visual assets of this website/page.

[Shared context block from Phase 1, verbatim]

## Instructions
Evaluate:
1. **OG/Twitter Tags**: Presence, quality, share preview appearance
2. **Social Profiles**: Linked from site, consistent branding, active presence
3. **Share Buttons**: Placement, platform selection, mobile-friendly
4. **Images**: Quality, relevance, consistency, alt text, performance
5. **Product Gallery**: Count, angles, zoom, lifestyle shots, consistency
6. **Video**: Hero video, demos, testimonials, thumbnails, loading behavior
7. **Icons & Illustrations**: Consistent style, meaningful, accessible

For each finding: severity, element, issue, specific fix.
Note what's working well.

Return structured findings.
```

The coordinator alone consolidates all delivered audit findings into **`.content-strategy/02-audit.md`**. Preserve failed delivery records and mark excluded areas `not audited`; do not declare the audit complete when a selected reviewer has not delivered. Synthesis owns this intermediate artifact, while the report phase alone owns `05-report.md`:

```markdown
# Phase 2: Content Strategy Audit

## UX & Conversion Findings
[From Agent A, organized by severity]

## Content & Copy Findings
[From Agent B, organized by severity]

## Social & Visual Findings
[From Agent C, organized by severity]

## What's Working Well
[Positives from all agents]
```

---

## Phase 3: Synthesize & Prioritize

Read `.content-strategy/02-audit.md` and create actionable plan. If `--strict-mode` was passed, promote every Important finding to Critical before building the table, and open the plan with the `VERDICT:` line.

**Output file:** `.content-strategy/03-plan.md`

```markdown
# Content Strategy Plan

## Findings Summary
| Category | Critical | Important | Nice-to-have |
|----------|----------|-----------|--------------|
| UX & Conversion | X | X | X |
| Content & Copy | X | X | X |
| Social & Visual | X | X | X |
| **Total** | **X** | **X** | **X** |

## Quick Wins (high impact, low effort)
[Numbered list with specific before/after examples]

## Medium Effort
[Changes requiring moderate work]

## Major Recommendations
[Bigger changes requiring design/content decisions]

## Estimated Conversion Impact
[Which changes are most likely to improve conversion, ordered by expected impact]
```

---

## PHASE CHECKPOINT -- User Approval Required

```
Content strategy audit complete.

Findings: [X critical, Y important, Z nice-to-have]
Quick wins available: [count]

Please review:
- .content-strategy/02-audit.md
- .content-strategy/03-plan.md

1. Apply quick wins -- implement high-impact, low-effort changes
2. Apply all fixable items -- implement everything that doesn't need design decisions
3. Choose specific improvements -- I'll tell you which ones
4. Report only -- skip implementation, generate final report
```

Record `artifact:content-strategy-approval` with the user's actual choice and authorized scope. Do not simulate the answer or begin unapproved changes. Use the host's question mechanism and wait for explicit user input. If the user chooses report only, Phase 4 records that choice and zero applied changes in `04-changes.md`, then proceeds to the final report without mutation.

---

## Phase 4: Apply Changes

**Target type determines behavior:**
- **If local target** (e.g., `src/pages/landing.html`): use Edit tools to implement changes directly in the source code
- **If remote URL** (e.g., `https://example.com`): do NOT attempt to edit local files. Generate improved code/copy as standalone files inside `.content-strategy/improvements/` (e.g., `optimized-hero-copy.md`, `rebuilt-pricing-table.html`)

Implement approved changes in logical order:
1. Copy improvements first (headlines, CTAs, microcopy)
2. Structure changes (layout, navigation, form optimization)
3. Media optimization (images, OG tags, social)

Log changes to **`.content-strategy/04-changes.md`**:

```markdown
# Changes Applied

## Change 1: [description]
- Category: [UX/Content/Social]
- Before: [state]
- After: [state]
- Expected impact: [description]
```

---

## Phase 5: Final Report

Read all `.content-strategy/*.md` files and generate consolidated report.

**Output file:** `.content-strategy/05-report.md`

```markdown
# Content Strategy Audit Report

## Target: [URL or path]
## Date: [timestamp]

## Executive Summary
[2-3 sentences on marketing effectiveness]

## Findings by Category
| Category | Critical | Important | Nice-to-have | Fixed |
|----------|----------|-----------|--------------|-------|
| UX & Conversion | X | X | X | X |
| Content & Copy | X | X | X | X |
| Social & Visual | X | X | X | X |

## Changes Applied
[Summary with before/after highlights]

## Remaining Recommendations
[Items requiring manual intervention: photography, video, design work, A/B testing]

## Ongoing Strategy
- Content calendar suggestions
- A/B testing opportunities
- Metrics to track
- Review frequency

## Audit Metadata
- Audits selected: [actual A/B/C groups and their owned areas]
- Deliveries: [delivered/failed per selected audit; excluded areas are not audited]
- Total findings: [count]
- Fixes applied: [count]
```

---

## Completion

```
Content strategy audit complete for: $ARGUMENTS

Output Files:
- Scope: .content-strategy/01-scope.md
- Audit: .content-strategy/02-audit.md
- Plan: .content-strategy/03-plan.md
- Changes: .content-strategy/04-changes.md
- Report: .content-strategy/05-report.md

Findings: [X critical, Y important, Z nice-to-have]
Changes applied: [count]
```

## Quick Examples

- `/digital-marketing:content-strategy https://example.com`: Full marketing audit
- `/digital-marketing:content-strategy https://example.com/pricing`: Pricing page conversion optimization
- `/digital-marketing:content-strategy src/pages/landing.html`: Audit local landing page
- `/digital-marketing:content-strategy https://example.com --focus cta,social-proof`: Focused audit
- `/digital-marketing:content-strategy https://example.com --social`: Social media presence focus
