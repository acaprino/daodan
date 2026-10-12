---
description: 'Audit a codebase for structural entropy, or with --diff check whether a change introduces new entropy. Report-only; auto-launches /codebase-xray:analyze when .codebase-xray/ is missing. TRIGGER WHEN: the user asks to audit duplicated knowledge, competing sources of truth, redundant models, derivable state, or wrong abstractions.'
---

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

# audit

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **inline-prompt**, and declared
isolation **required**. Dispatch one worker per entry in the plan below with the `subagent`
tool supplied by the `pi-subagents` package, each in its own context. Role delivery here is
`inline-prompt`: paste that role's Markdown body into the dispatch prompt verbatim, because the
worker must receive the whole role rather than a summary of it.

Pi's core ships no subagent tool. If none is available in this session, the declared isolation
above decides what happens, and the two cases are not interchangeable:

- **`required`**: stop, and tell the user to run `pi install npm:pi-subagents`. Running the phases
  serially in this one context is the loss of isolation rather than a lesser form of it, so a
  report produced that way would claim a contract it did not meet.
- **`shared`**: run the phases in order in this context, and say in the report that no worker was
  isolated.

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
  Independent reviewers never read peer results before their own delivery.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A worker reports delivered or failed in its final message; there is no shared task
  list, so the coordinator keeps that record itself.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `abstraction-architect-agent`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `abstraction-architect-agent` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:audit-report`.

Role body bindings (load the complete body only for the selected worker):

- `abstraction-architect-agent`: read `skills/abstraction-architect-abstraction-architect-agent/SKILL.md` inside this package and pass its complete body verbatim.

The phase graph and record-schema references are in `contracts/audit.workflow.toml`.

## Method

# /abstraction-architect:audit

Audit a codebase for structural entropy: duplicated domain knowledge, competing sources of truth, redundant representations, duplicated or derivable state, missed unification, prior art that already exists, and abstractions that are fighting their callers. Report-only.

## Usage

```
/abstraction-architect:audit                                    # audit current directory
/abstraction-architect:audit src/services                       # audit a subpath
/abstraction-architect:audit --severity-floor high              # only high-severity findings
/abstraction-architect:audit --focus knowledge                  # D1-D4 only
/abstraction-architect:audit --focus D2                         # competing sources of truth only
/abstraction-architect:audit --diff                             # does my change add entropy?
/abstraction-architect:audit --diff origin/master               # same, against an explicit base ref
/abstraction-architect:audit --rebuild-index                    # ignore any existing concept index
```

## Arguments

- `[path]` (optional) — codebase root. Default: current working directory.
- `--diff [<base-ref>]` (optional) — run diff-anchored instead of a whole-codebase audit. Asks the same seven questions as "introduced or aggravated by this change". Base ref defaults to the merge base with the default branch, falling back to `HEAD` for uncommitted work.
- `--scope <subpath>` (optional) — limit findings to a subtree. The X-ray still runs on the full codebase.
- `--severity-floor low|medium|high` (optional) — default `medium`.
- `--focus all|knowledge|form|D1..D7` (optional) — default `all`. `knowledge` is D1 to D4, `form` is D5 to D7, or name a single dimension.
- `--no-index` (optional) — do not read or write `concept-index.json`. Use when auditing a directory that is not a git repository, or to measure what the audit finds without a seed.
- `--rebuild-index` (optional, global mode only) — ignore any existing index and census the codebase from scratch. Use after a large refactor or a history rewrite.

## What this command does

1. **Resolves the target path.** Defaults to the current working directory.

2. **Checks for `.codebase-xray/`.** Looks for `01-structure.md`, `02-interfaces.md`, `03-flows.md`, `04-semantics.md`. The optional `08-interconnect-map.md` enables the bounded-context check; without it, knowledge-track findings carry `Bounded-context exception: unverified`.

3. **Auto-launches X-ray if needed.** If `.codebase-xray/` is missing or incomplete, prints *"No X-ray output found at `.codebase-xray/`. Launching `/codebase-xray:analyze` first. This may take several minutes on a large codebase."* then invokes it without a confirmation prompt. Aborts with the log path if the X-ray fails.

   Under `--diff` this step is skipped. Diff mode consumes only `01-structure.md` and `02-interfaces.md`, uses whatever is on disk, and runs on the concept index plus host file-discovery binding and host content-search binding when nothing is.

4. **Resolves the concept index.** Unless `--no-index`, checks `<path>/.abstraction-architect/concept-index.json` and runs the freshness script. Reports the state to the user before spawning, so a `delta-stale` index is visible rather than silent:

   ```
   Concept index: delta-stale (baseline a13fe2, HEAD 92ac10, 4 concepts to revalidate)
   ```

   An absent or unusable index is not an error. The audit proceeds and declares the reduced coverage in its Gaps section.

5. **Resolves the diff (`--diff` only).** Runs `git diff --name-only <base-ref>...HEAD` plus `git diff --name-only` for uncommitted work, and passes the union as `changed_files`. Aborts with a clear message when the path is not a git repository.

6. **Spawns the `abstraction-architect-agent` agent** through its declared host harness, placing in the worker prompt `codebase_path`, `mode`, `xray_path`, `concept_index_path`, `changed_files` under `--diff`, and the parsed scope, severity-floor and focus flags.

7. **The agent writes the report** to `<path>/.abstraction-architect/findings.md`, or `findings-diff.md` under `--diff`. In global mode it also rewrites `concept-index.json`. **Diff mode never writes the index.**

8. **Prints to the user:** the report path, summary counts, the concept index state, and the top three findings as one-line previews.

The full report stays in the file so the user opens it deliberately.

## Output location

`<path>/.abstraction-architect/findings.md`, or `<path>/.abstraction-architect/findings-diff.md` under `--diff`.

The directory is created automatically if missing. Re-running the command overwrites the previous report.

## Prerequisites

- The `codebase-xray` plugin must be installed (a hard dependency declared in this plugin's `plugin.toml`). `--diff` degrades gracefully without X-ray output and reports the reduced confidence in its Gaps section.
- `--diff` requires the target path to be a git repository.
- For monorepos large enough to benefit from partitioned analysis, run `/codebase-xray:team-analyze` first to produce `08-interconnect-map.md`; the auditor will then include bounded-context fusion findings.

## Related commands

- `/codebase-xray:analyze` — produces the `.codebase-xray/` input this command consumes. Auto-launched by this command when missing.
- `/codebase-xray:team-analyze` — partitioned X-ray for monorepos; adds `08-interconnect-map.md` to the output.
- `/senior-review:code-review` and `/senior-review:team-review` — both run this agent in diff mode as their abstraction dimension, so a review already answers the "was this already available?" question for the changed code. Use `--diff` here when you want that check on its own, without the rest of the review.
- `/clean-code:clean-code` — style and readability cleanup. Different concern.

## Out of scope

This command does not produce a refactoring plan. The `suggested direction` field in each finding names the target layer or refactoring move in one sentence.
