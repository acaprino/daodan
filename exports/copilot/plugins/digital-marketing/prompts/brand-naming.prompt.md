---
name: brand-naming
description: 'Runs the whole workflow from a brief, with optional language and TLD constraints. TRIGGER WHEN: the user asks for brand, startup, product, or company names. DO NOT TRIGGER WHEN: renaming source code identifiers (use clean-code), or picking SEO keywords (use /digital-marketing:seo-audit).'
argument-hint: '<brief description or industry> [--country <country>] [--languages <lang1,lang2>] [--tlds <.com,.app,.io>]'
---

> Arguments: `<brief description or industry> [--country <country>] [--languages <lang1,lang2>] [--tlds <.com,.app,.io>]`. Wherever `<arguments>` appears below, substitute the text the user typed after the prompt name.

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

<!-- Generated by the Daodan compiler for copilot. Edit the kernel, never this file. -->

# Brand Naming

## Invocation

Invoke the `brand-naming-method` skill and follow its full workflow.

## Arguments

- `<brief>`: Industry, target, values, and any constraints for the naming project
- `--country`: Reference country for the trademark check, graded first and weighted most; asked when neither the arguments nor the project name one
- `--languages`: Languages to check for cultural conflicts (default: en,it,es,fr,de,pt)
- `--tlds`: TLDs to check for domain availability (default: .com,.app,.io,.co)

## Examples

```
/digital-marketing:brand-naming Meal prep app for vegan athletes. Values: energy, nature, performance. Target: 20-35, international.
/digital-marketing:brand-naming SaaS project management tool for remote teams --languages en,es,pt
/digital-marketing:brand-naming Italian artisan coffee brand, premium positioning --tlds .com,.it,.coffee --country Italy
```

## What it does

1. Takes the brief from the arguments when they carry it, scans the current project only when the brief is thin or names the project, and asks for the reference country and any other field neither supplies
2. Generates 12-15 curated candidates across 4 Strategic Directions: Etymological Hijacking, Scientific Decontextualization, Metaphorical Shift, Phonetic Real-Word
3. Filters linguistically and culturally (pronunciation, negative meanings, phonosymbolism)
4. Checks domain registration once over the requested TLDs with the domain checker (RDAP, and a headless Patchright registrar page for TLDs with no RDAP), lists every dropped name with its reason, then checks social media handles
5. Analyzes market saturation: existing apps, websites, active businesses with same name (Google, Play Store, App Store, Crunchbase)
6. Pre-screens trademarks through a browser (the `playwright` plugin's MCP tools) in the national register of the reference country (UIBM for Italy), EUIPO TMview (falling back to EUIPO eSearch plus for EU trade marks when TMview refuses the browser), USPTO Trademark Search and the WIPO Global Brand Database, and grades the reference country, Europe and the world from class A (lowest risk) to D (highest); a register that did not answer makes its territory NS (not screened), never A
7. Scores the top 5 from 1 to 5 on weighted criteria (memorability, distinctiveness, market saturation, SEO, legal risk, etc.) and computes an overall score from 1.0 to 5.0, with the trademark score weighted to the reference country
8. Delivers the evaluation report from a fixed template: summary, scorecard of all 5 names, the top 3 with a description, a motivation for every score and a trademark class for each territory, the runners-up, the removed names, the checks still open and the evidence behind them
