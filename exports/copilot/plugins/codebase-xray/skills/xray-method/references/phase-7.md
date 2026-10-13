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

# Phase 7

## Phase 7: Final Report

Synthesize all `$RUN_DIR/*.md` files (01 through 06) into a consolidated report.

**Context management strategy** (to avoid "lost in the middle" on large codebases):
1. Read each phase file one at a time
2. After reading each file, extract the key findings into a running summary (max 5 bullet points per phase)
3. After processing all 6 files, write the final report from the extracted summaries
4. For detailed sections, cross-reference the original phase files rather than duplicating content

**Output file:** `$RUN_DIR/07-final-report.md`

```markdown
# Codebase X-Ray Analysis Report

## Target
[From scope]

## Executive Summary
[2-3 sentences on overall codebase health]

## Project at a Glance
[2-3 paragraph narrative explaining what this project does, who it's for, and how it works - written for someone who has never seen the codebase]

## Architecture Overview
[Mermaid diagram + narrative from Phases 1-2]

## Technology Decisions
[Key tech choices and why they were made - useful for presentations and onboarding]

## Critical Paths
[Key findings from Phase 3]

## Key Process Diagrams
[Include the most important Mermaid flowcharts from 03-flows.md - select 3-5 diagrams that best represent the system's core processes. Prioritize E2E and Functional diagrams over Technical ones. Reference 03-flows.md for the complete set.]

## Design Insights
[Key findings from Phase 4]

## Risk Assessment
| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Anti-patterns | X | X | X | X |
| Security risks | X | X | X | X |
| Usability-blocking | X | X | X | X |
| Technical debt | X | X | X | X |
| Doc gaps | X | X | X | X |

## Documentation vs Reality
[Discrepancies found between existing docs and actual code behavior - useful for doc maintenance]

## Top Priority Actions
1. [Most important fix/improvement]
2. [Second priority]
3. [Third priority]

## Detailed Findings
[Cross-references to phase files for full details]

## Quick Reference: Which File to Consult

| Your Task | Start With | Also Check |
|-----------|-----------|------------|
| Onboarding / understanding the project | 07-final-report, 01-structure | 04-semantics |
| Writing new feature | 01-structure (Where to Add), 02-interfaces | 04-semantics |
| Fixing a bug | 03-flows, 05-risks | 01-structure |
| Refactoring | 01-structure, 04-semantics, 05-risks | 03-flows |
| Code review | 02-interfaces, 05-risks | 06-documentation |
| Updating documentation | 06-documentation, 04-semantics | 02-interfaces |
| Creating report/presentation | 07-final-report, 01-structure | 04-semantics |
| Finding doc vs code discrepancies | 06-documentation | 03-flows, 05-risks |

## Analysis Metadata
- Run: [run-id]
- Target: [path]
- Files in inventory: [count] (parsed source: [N], configuration and documentation: [N], presentation: [N]; extensions outside those three sets are absent from every count). Outside the perimeter by rule: [N] dot directories ([names]) and [N] paths Git ignores, ignore rules [applied | unavailable], from the manifest's `scope` block
- Files read in depth: [count, and the list or the directories]
- Exercised at runtime: none. This is static analysis; if the user supplied runtime evidence, cite it here instead
- Phases completed: [list]
- Date: [timestamp]
```

The three coverage lines are mandatory, in the condensed lite report as well. A single file count read as coverage is how a blocking defect in an inventoried component once went unreported: the component was in the inventory, the stylesheet that broke it was not, and nothing had exercised the path. The inventory line names what the perimeter left out for the same reason: `.github/` or a generated client is exactly what a reader assumes was read.

Update `$RUN_DIR/state.json`: set `status` to `"complete"`.
