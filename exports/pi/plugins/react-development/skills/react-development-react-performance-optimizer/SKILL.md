---
name: react-development-react-performance-optimizer
description: 'Measure first, then cut wasted React 19 component work, store re-renders and bundle bloat. TRIGGER WHEN: dispatched by the React performance audit of react-best-practices (run by `/daodan:check-health`) or by senior-review in `/daodan:review-changes` and `/daodan:review-branch`; reviewing or optimizing React 19 performance: re-renders, React Compiler, Server Components, bundle analysis, state management (Zustand/Redux/Jotai/TanStack), or profiling. DO NOT TRIGGER WHEN: CSS/design polish, native desktop backend work (Rust, IPC), or general Next.js setup (use react-best-practices).'
disable-model-invocation: true
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.

# React Performance Optimizer

Apply the common review conventions and working discipline supplied in the assignment once. Missing required brief inputs fail the assignment.

## Mandate and input

Find React-caused work, staleness or leaks whose consequence violates a stated requirement, a supplied budget or observable behavior. One assignment covers four mechanisms: effect synchronization, request and server/client dataflow, render and subscription cost, module and resource delivery.

Require the installed React, compiler, store, framework and bundler versions, the component and store topology, rendered data cardinality, interaction or loading requirements, and any profile, chunk report or budget bound to this candidate. Unknown versions, cardinality or budgets stay explicit gaps; never substitute a universal target.

Read only the applicable rules under `<plugin-root>/skills/react-best-practices/rules/` (`advanced-*`, `async-*`, `bundle-*`, `client-*`, `js-*`, `rendering-*`, `rerender-*`, `server-*`) and the matching section of `<plugin-root>/skills/react-best-practices/references/react19-stores-and-effects.md`. Rules and templates are leads and fix shapes; the common evidence rules decide applicability and severity.

## Causal checks

- **Effects.** Trace effect and callback dependencies and the state they write to prove self-sustaining re-entry, or a stale closure that changes behavior. Follow timers, listeners, sockets, channels, fetch/IPC completion and manual store subscriptions through dependency replacement and unmount; verify that the cleanup or stale-result suppression prevents the consequence (not every API accepts an AbortController). Effect Events read the latest committed values in supported versions; they are not a way to hide dependencies.
- **Dataflow.** Build the real dependency graph of route, component and nested fetches; separate required sequencing from independent awaits. Check per-request deduplication, cross-request caches, keys and invalidation; request state must not leak through module globals. Freshness comes from the contract: `staleTime` and refocus have no universally correct value, and `gcTime` governs inactive retention, not freshness. Check server/client serialization and redundant payloads against what the framework transfers.
- **Render and subscriptions.** Follow whole-store versus leaf subscriptions, fresh selector results and equality checks to the notifications and renders they cause. The compiler memoizes component work; it does not stabilize an external store snapshot, so a selector returning a new object on each read still notifies. Check component and key identity, list virtualization with stable item IDs, hydration differences and repeated computation derived from call frequency and input size.
- **Delivery.** Trace initial versus conditional imports, barrel and namespace reexports, package `exports`/`sideEffects` and dynamic chunks to what the effective build ships or loads. A lazy boundary still needs loading and error behavior.
- For every candidate, state the triggering frequency or cardinality and the affected interaction, state or payload. Keep a derivation from source distinct from a supplied measurement.

## Counterevidence

Stable selectors or equality functions, effective teardown, intentional fresh queries, tree shaking and externalization, bounded cheap work, legitimate remount initialization and required first-render work can refute a candidate. A missing memo, virtualizer, compiler flag, library or React 19 API is not a defect by itself. Record the verified protections that refuted candidates; the coordinator reports them.

## Boundaries and output

General query and algorithm cost belong to the general performance reviewer; timing races between async data, render and focus to the UI race reviewer; static CSS and layout to accessibility; native desktop backends to platform. Authorization inside server actions is a lead for the authorization owner; the React cause stays here. Write only the assigned report. Run builds, bundle analyzers or profilers only with the caller's authorization; a supplied report proves only its own candidate.

Native severity: `CRITICAL` when the evidenced consequence breaks a required interaction, loops without bound or leaks on every mount; `IMPORTANT` when it exceeds a stated budget or requirement; `IMPROVEMENT` when the benefit is evidenced but nothing required is violated.

Each finding adds its mechanism, trigger and frequency, affected state or interaction, counterevidence checked, a fix direction from the reference and how to verify it (Profiler trace, test, emitted chunk). Report coverage per mechanism, rejected candidates and unexamined scope.
