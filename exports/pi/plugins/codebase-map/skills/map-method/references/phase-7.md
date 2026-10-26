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

Read `$RUN_DIR` reports 01 through 06 sequentially, retaining up to five
key-findings bullets each. Synthesize and link details; keep required sections
and evidence. Graph-assisted source mapping is static: metadata is neither deep
reading nor runtime evidence.

**Output file:** `$RUN_DIR/07-final-report.md`

```markdown
# Codebase Map Analysis Report

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
- Mode: classic
- Run: [run-id]
- Target: [path]
- Files in inventory: [count]: parsed source [N], configuration/documentation [N], presentation [N]; other extensions absent from all counts. Manifest `scope` excludes [N] dot directories ([names]) and [N] Git-ignored paths; ignore rules [applied | unavailable]
- Static graph mapping: [manifest binding, seeds/hops, AST coverage/gaps, truncation, parser fallback; phase-ledger links]
- Files read in depth: [count; actual files/ranges from phase ledgers]
- Exercised at runtime: none. This is static analysis; if the user supplied runtime evidence, cite it here instead
- Phases completed: [list]
- Date: [timestamp]
```

The three coverage lines are mandatory, including in the condensed lite report.

For requested or useful HTML, only the entry coordinator loads `references/human-view.md`.
Workers never load presentation instructions. The entry coordinator marks the run
complete only after native delivery and every requested view pass their gates.

## Team mode

### Team extensions

| Heading | File | Mode | Writer | After | Aggregation |
|---|---|---|---|---|---|
| Partial Completeness Warning | 07-final-report.md | consolidated | partition-synthesizer | first | Only for failed partitions; name them and the incomplete sections. |
| Partition Map | 07-final-report.md | consolidated | partition-synthesizer | Project at a Glance | Repeat the 01 Partition Map. |
| Cross-Partition Topology | 07-final-report.md | consolidated | partition-synthesizer | Project at a Glance | Repeat the 01 Dependency Graph. |
| Per-Partition Health Scorecard | 07-final-report.md | consolidated | partition-synthesizer | Design Insights | One row per partition: anti-pattern/red-flag C/H/M/L, doc gaps, debt and health. |

### Partition worker

The report is written by the synthesizer, not partition workers.

### Consolidation

| File | Common heading | Rule |
|---|---|---|
| 07-final-report.md | Executive Summary | Derive overall health from consolidated risk and documentation files. |
| 07-final-report.md | Project at a Glance | Aggregate semantics, or structure observations when semantics is absent. |
| 07-final-report.md | Architecture Overview | Synthesize 01 and 02. |
| 07-final-report.md | Technology Decisions | Aggregate partition technology choices. |
| 07-final-report.md | Critical Paths | Use Cross-Partition Flows when present; otherwise partition critical paths. |
| 07-final-report.md | Key Process Diagrams | Prioritize cross-partition end-to-end diagrams. |
| 07-final-report.md | Design Insights | Use Cross-Partition ADR when present. |
| 07-final-report.md | Risk Assessment | Keep the severity matrix and add a Cross-Partition Risk Attribution row. |
| 07-final-report.md | Documentation vs Reality | Aggregate mismatches. |
| 07-final-report.md | Top Priority Actions | Critical/high findings with cross-partition impact and citations. |
| 07-final-report.md | Quick Reference: Which File to Consult | Add the team-only cross-partition design-decisions row: 04 Cross-Partition ADR and 01; also 02 Cross-Partition Exports. Code review also checks 08. |
| 07-final-report.md | Analysis Metadata | Mode: team; partition count/list; preserve graph diagnostics; deduplicate phase-ledger reads without synthesis source reads. |
