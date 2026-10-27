---
name: adr-method
description: >
  Create, resolve, validate, approve, version and verify canonical architecture decision records in docs/adr/.
  TRIGGER WHEN: the user explicitly asks to record or write down an architecture or technical decision, an interview settles a design, contract or domain decision, a task needs the decisions governing its scope, the user approves, revises or abandons a record, or a reviewed change verifies records or lists their drift.
  DO NOT TRIGGER WHEN: the user only wants brainstorming or advice without recording a decision, the change needs no decision beyond existing records, or the request is project documentation (use project-knowledge:project-knowledge).
---

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
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

# Architecture decision records

Load the skill `work-controller:work-record` for run ownership and authorization.
The helper is `python "${CLAUDE_PLUGIN_ROOT}/skills/adr-method/scripts/adr_tool.py"`;
it writes records and the index atomically and refuses an inconsistent state
first.

## Load map

| Step | Run |
|---|---|
| Any | `validate --project ROOT` before relying on records |
| Before an interview | `resolve --project ROOT --paths P... --modules M... --domains D... --symbols S...` |
| Writing a record or a version | read `references/adr-template.md`; `template`, then `propose` |
| The user approved the text shown | `promote --adr ADR-NNNN --sha HEAD_SHA --expect-digest D` |
| Code reviewed as conforming | `verify --adr ADR-NNNN --sha SHA --expect-digest D` |
| Status, realignment | `validate --project ROOT --sha HEAD_SHA` |
| First use in a project | `init-index --project ROOT` |

## Resolve: what governs this scope

Input: the paths, modules, domains and Codebase Map symbols the task touches.
Output: the `Accepted` version of each matching decision, its `digest` and why
it matches, most specific first. Load the one to three that matter, never the
whole directory.

## Propose: the interview's output

Before choosing or revising alternatives, load `research:science-based-approach`
and compose its automatic checkpoint with the caller's run and grants. Cite
research identity, immutable revision and claim IDs with applicability and limits.
A changed source identifies decisions to review; it never rewrites or approves
an Accepted record. Reuse the same checkpoint when the interview already did it.

Once the interview fixed scope, nominal, boundary and rejection examples,
rejected alternatives and invariants, write the body and `propose` with
title, slug, run identity, `HEAD`, scope lists, any `--supersedes` (another
decision it replaces) and any `--depends-on` (`Accepted` decisions it builds
on). A refusal names what to fix; never hand-edit the index. To change an
`Accepted` decision, `propose --revise ADR-NNNN` writes its next version,
`Proposed` under the same number. `ADR-NNNN` cites the active version,
`ADR-NNNN vN` pins one.

Versions: at most one `Accepted` and one `Proposed` version per decision.

## Approve, retire, verify

`Accepted` means the user approved this exact text. Show the record with its `digest` (`validate --adr ADR-NNNN`) and ask. On
approval, `promote` sets `Accepted` and marks the previous version and each
`supersedes` target `Superseded`, as one transaction; record each
`dependents_to_review` as an open question (`ask`). Approval authorizes no
work; a merge never approves. Unapproved, a record stays `Proposed`;
abandoned, it gets `retire --adr ADR-NNNN --reason TEXT --expect-digest D`,
`Abandoned` for good. Never delete a record. A rewrite refuses, writing
nothing, on a digest other than `--expect-digest`: show the record again.

After a review confirms the code conforms, `verify` sets `last_verified_sha`;
approval never verifies. `validate --sha` lists as `drifted` each `Accepted`
record whose governed files changed since, `files: null` when never verified.

## Instructions and documentation

Durable instructions carry the active records for a domain inside the loop
block that `project-knowledge:instructions-method` maintains; guides cite a
record by identity and never restate its examples.
