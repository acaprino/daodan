---
name: defect-taxonomy
description: >
  16 macro-categories and 140+ subcategories of source-code failure modes, with CWE and OWASP mappings, fix patterns, and review frameworks.
  TRIGGER WHEN: an audit needs structured defect classification, a detection strategy, or severity calibration; loaded by code-auditor, security-auditor, and ui-race-auditor.
---

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

# Defect Taxonomy Knowledge Base

Unified classification of source code defects synthesizing MITRE CWE, OWASP Top 10, NASA Power of 10, IBM ODC, IEEE 1044, and Beizer's taxonomy into actionable detection references.

## Reference Files

Load relevant references based on the code domain under review. Do NOT load all files -- select only what applies.

### Taxonomy References (defect patterns)

| Reference | When to load |
|-----------|-------------|
| `references/concurrency-state.md` | Concurrent/parallel code, shared state, async patterns, closures, variable scoping |
| `references/logic-types.md` | Comparisons, boolean logic, type conversions, generics, serialization |
| `references/memory-resources.md` | Memory management (C/C++/Rust), resource lifecycle, error handling, performance bottlenecks |
| `references/security.md` | Security review -- injection, auth, crypto, secrets, CORS, SSRF, input validation |
| `references/distributed-integration.md` | Microservices, APIs, distributed state, message queues, service mesh, migrations |
| `references/data-design-ops.md` | Database/ORM, design patterns, build/deploy, testing, observability |
| `references/detection-matrix.md` | Cross-cutting: detection channels per category, language-weighted focus, ROI prioritization |

### Review Frameworks (analysis methodology)

| Reference | When to load |
|-----------|-------------|
| `references/review-frameworks.md` | Always load for code-auditor. Contains cognitive models, failure flow methodology, anti-pattern checklist, mental models, severity/scoring system |

## Language-Weighted Category Focus

- **C/C++**: concurrency-state.md + memory-resources.md (categories 1, 5)
- **JVM (Java/Kotlin/Scala)**: concurrency-state.md + logic-types.md + memory-resources.md (categories 2, 7, 8)
- **JavaScript/TypeScript**: concurrency-state.md + logic-types.md + security.md (categories 2, 4, 6)
- **Python**: logic-types.md + security.md + memory-resources.md (categories 4, 6, 7)
- **Go/Rust**: concurrency-state.md + memory-resources.md (categories 1, 5, 7)
- **Microservices (any)**: distributed-integration.md + data-design-ops.md (categories 8-12)

## Usage Instructions

1. Identify the language(s) and domain of the code under review
2. Load the review-frameworks.md reference (for code-auditor agent)
3. Load 1-3 taxonomy references matching the language/domain
4. Apply detection strategies from the loaded references during analysis
5. Map findings to CWE identifiers where applicable
6. Use the detection-matrix.md to prioritize detection approach
