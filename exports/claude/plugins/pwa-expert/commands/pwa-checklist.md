---
description: 'Walks the production deploy checklist, reporting pass, fail or N/A per category against the codebase and an optional URL. TRIGGER WHEN: checking PWA launch readiness, or walking a deterministic go/no-go list before deploying. DO NOT TRIGGER WHEN: an open-ended adversarial audit fits better (use /pwa-expert:pwa-audit).'
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

# pwa-checklist

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
- Dispatch only roles from this set, as the phase graph or loaded method requires: `pwa-architect`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `pwa-architect` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:pwa-checklist-report`.

Role bindings:

- `pwa-architect`: dispatch the installed `pwa-expert:pwa-architect` agent by its qualified identity.

The phase graph, the isolation and join policies and the record schemas are in
`contracts/pwa-checklist.workflow.toml`, which ships with this package.

## Method

# /pwa-expert:pwa-checklist

Walk the production deploy checklist from `references/production-checklist.md` interactively against the current project (or the provided URL).

Delegate to `pwa-architect`. The agent reads `production-checklist.md` upfront (this is one of the few cases where preloading a reference is correct, because the command IS the checklist), then walks every item.

## Modes

- If `$ARGUMENTS` is a URL: walk the checklist against the live deployment via the Playwright MCP tools of the `playwright` plugin where applicable, plus the codebase for items that can only be verified in source.
- If `$ARGUMENTS` is a path or omitted: walk against the codebase only.

## How the walk works

For every item in every category of `production-checklist.md`:

1. State the item verbatim.
2. Verify it. Use the active host repository-read, search, file-discovery and shell bindings, or registered Playwright MCP tools as appropriate.
3. Record the result as one of: **PASS**, **FAIL**, **N/A** (with a reason for N/A).

## Output format

Produce a markdown report:

```
# Production Checklist Report

**Target:** <path or URL>
**Date:** YYYY-MM-DD

## Summary

| Category | Pass | Fail | N/A | Score |
|---|---|---|---|---|
| Manifest | X | Y | Z | X / (X+Y) |
| iOS-specific | ... |
| Service Worker | ... |
| Security | ... |
| Performance | ... |
| Push | ... |
| Storage | ... |
| Testing | ... |
| Distribution | ... |
| Monitoring | ... |
| **Overall** | ... |

## Manifest

- [PASS] id is explicit (not implied from start_url). Found in `public/manifest.webmanifest:2`.
- [FAIL] Icons: 192 PNG purpose: "maskable" missing. Add via /pwa-expert:pwa-scaffold or by hand.
- ...

(... and so on for every category, every item)

## Recommended next actions

(Numbered list of the highest-impact fails, ordered by severity.)
```

## Difference from /pwa-expert:pwa-audit

- `pwa-audit` is open-ended and adversarial. It uses domain knowledge to find defects the checklist does not enumerate.
- `pwa-checklist` is deterministic. The output maps 1:1 to the source guide's deploy checklist sections. Two runs on the same target produce structurally identical reports.

Use `pwa-checklist` for release gates and CI integration. Use `pwa-audit` for design reviews and pre-launch deep-dives.

## CI integration

The deterministic, structured output makes this command suitable as a release gate:

1. Run `/pwa-expert:pwa-checklist <path-or-URL>` from a CI step that invokes Claude Code.
2. Parse the Summary table for the **Overall** row.
3. Fail the build if `Fail > 0` for any category that the team has flagged as blocking (typically Manifest, Service Worker, Security).
4. Treat `N/A` as informational, not failing.

## Category-to-reference map for FAIL remediation

When recording a FAIL, point the user at the matching reference so they can self-serve the fix:

| Checklist category | Reference file |
|---|---|
| Manifest, iOS-specific | `references/manifest.md` |
| Service Worker | `references/service-workers.md` |
| Security | `references/security.md` |
| Performance | `references/performance.md` |
| Push | `references/push-notifications.md` |
| Storage | `references/storage-persistence.md` |
| Testing | `references/frameworks-tooling.md` (debugging surface) |
| Distribution | `references/distribution.md` |
| Monitoring | `references/performance.md` (CrUX / RUM) and `references/push-notifications.md` (pushsubscriptionchange) |

## Output rules

- No emojis. Status indicators are text only: `[PASS]`, `[FAIL]`, `[N/A]`.
- Cite a file and line for every PASS / FAIL where possible (local mode) or a URL fragment / manifest field (live mode).
- Recommend the matching reference file from the knowledge base for every FAIL, so the user can self-serve the fix.
