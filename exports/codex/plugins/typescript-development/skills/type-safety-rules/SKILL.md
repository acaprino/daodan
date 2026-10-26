---
name: type-safety-rules
description: >
  20 rules across 7 categories, each with detection and fix guidance.
  TRIGGER WHEN: reviewing or hardening TypeScript against type-system erosion: `any` leakage, unsound casts, missing boundary validation, assertion abuse, tsconfig strictness, exhaustiveness and generics soundness.
  DO NOT TRIGGER WHEN: style and naming review (use typescript-write), or dead-code detection (use knip).
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

# TypeScript Type-Safety Rules

Review-oriented rule set for hunting type-system erosion in TypeScript codebases. 20 rules across 7 categories, prioritized by blast radius. Used as the audit checklist by the `type-safety-auditor` agent and usable standalone while writing or hardening TypeScript.

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Any Erosion | CRITICAL | `any-` |
| 2 | Unsound Casts | CRITICAL | `cast-` |
| 3 | Boundary Validation | CRITICAL | `boundary-` |
| 4 | Assertion Abuse | HIGH | `assert-` |
| 5 | Compiler Configuration | HIGH | `config-` |
| 6 | Exhaustiveness | MEDIUM-HIGH | `exhaust-` |
| 7 | Generics Soundness | MEDIUM | `generics-` |

## Quick Reference

### 1. Any Erosion (CRITICAL)

- `any-explicit` - Replace explicit `any` with `unknown` plus narrowing
- `any-implicit-boundary` - Type the results of `JSON.parse`, `response.json()`, and `catch` immediately
- `any-generic-default` - Never default a type parameter to `any`

### 2. Unsound Casts (CRITICAL)

- `cast-as-unsound` - An `as` cast that changes the shape needs a runtime check instead
- `cast-double` - `as unknown as X` is a type-system bypass; write a guard or converter
- `cast-const-assertion` - Use `as const` for literal narrowing instead of widening annotations

### 3. Boundary Validation (CRITICAL)

- `boundary-http` - Parse HTTP payloads with a schema at the edge
- `boundary-queue` - Validate queue and event messages before processing
- `boundary-storage` - Validate and version storage reads (localStorage, files, DB JSON)
- `boundary-env` - Access environment variables through one validated config module

### 4. Assertion Abuse (HIGH)

- `assert-non-null` - `!` needs an adjacent invariant justification or a fail-fast check
- `assert-ts-expect-error` - Use `@ts-expect-error` with a reason, never `@ts-ignore`

### 5. Compiler Configuration (HIGH)

- `config-strict` - `"strict": true` is the baseline
- `config-unchecked-index` - Enable `noUncheckedIndexedAccess`
- `config-exact-optional` - Enable `exactOptionalPropertyTypes`
- `config-skiplibcheck` - `skipLibCheck` may speed up third-party types, never hide first-party errors

### 6. Exhaustiveness (MEDIUM-HIGH)

- `exhaust-switch-never` - Discriminated unions get a `never` assertion in the default branch
- `exhaust-satisfies-record` - Use `satisfies Record<K, V>` for complete lookup tables

### 7. Generics Soundness (MEDIUM)

- `generics-constraint` - Constrain type parameters on public APIs
- `generics-type-guards` - A type predicate must verify the whole shape it claims

## How to Use

Read individual rule files in the `rules/` directory for detailed explanations and code examples. Each rule file contains a brief explanation, an incorrect example, a correct example, and a detection hint for reviewers.
