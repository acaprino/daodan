---
name: defect-taxonomy
description: >
  16 macro-categories and 140+ subcategories of source-code failure modes, with CWE and OWASP mappings, fix patterns, and review frameworks.
  TRIGGER WHEN: an audit needs structured defect classification, a detection strategy, or severity calibration; loaded by code-auditor, security-auditor, and ui-race-auditor.
---

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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
