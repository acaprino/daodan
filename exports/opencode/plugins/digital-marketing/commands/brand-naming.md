---
description: 'Runs the whole workflow from a brief, with optional language and TLD constraints. TRIGGER WHEN: the user asks for brand, startup, product, or company names. DO NOT TRIGGER WHEN: renaming source code identifiers (use clean-code), or picking SEO keywords (use /digital-marketing:seo-audit).'
argument-hint: '<brief description or industry> [--languages <lang1,lang2>] [--tlds <.com,.app,.io>]'
---

<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
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

<!-- Generated by the Daodan compiler for opencode. Edit the kernel, never this file. -->

# Brand Naming

## Invocation

Invoke the `brand-naming-method` skill and follow its full workflow.

## Arguments

- `<brief>`: Industry, target, values, and any constraints for the naming project
- `--languages`: Languages to check for cultural conflicts (default: en,it,es,fr,de,pt)
- `--tlds`: TLDs to check for domain availability (default: .com,.app,.io,.co)

## Examples

```
/digital-marketing:brand-naming Meal prep app for vegan athletes. Values: energy, nature, performance. Target: 20-35, international.
/digital-marketing:brand-naming SaaS project management tool for remote teams --languages en,es,pt
/digital-marketing:brand-naming Italian artisan coffee brand, premium positioning --tlds .com,.it,.coffee
```

## What it does

1. Takes the brief from the arguments when they carry it, scans the current project only when the brief is thin or names the project, and asks clarifying questions for what neither supplies
2. Generates 12-15 curated candidates across 4 Strategic Directions: Etymological Hijacking, Scientific Decontextualization, Metaphorical Shift, Phonetic Real-Word
3. Filters linguistically and culturally (pronunciation, negative meanings, phonosymbolism)
4. Checks domain registration once over the requested TLDs with the domain checker (RDAP, and a headless Patchright registrar page for TLDs with no RDAP), lists every dropped name with its reason, then checks social media handles
5. Analyzes market saturation: existing apps, websites, active businesses with same name (Google, Play Store, App Store, Crunchbase)
6. Pre-screens trademarks in EUIPO TMview (falling back to EUIPO eSearch plus for EU trade marks when TMview refuses the browser), USPTO Trademark Search and the WIPO Global Brand Database through a browser (the `playwright` plugin's MCP tools), and reports any register that did not answer as not screened instead of rating the name LOW
7. Scores the top 5 from 1 to 5 on weighted criteria (memorability, distinctiveness, market saturation, SEO, legal risk, etc.) and computes an overall score from 1.0 to 5.0
8. Delivers the evaluation report from a fixed template: summary, scorecard of all 5 names, the top 3 with a description and a motivation for every score, the runners-up, the removed names, the checks still open and the evidence behind them
