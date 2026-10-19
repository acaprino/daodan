---
name: adr-method
description: >
  Create, resolve, validate and promote canonical architecture decision records in docs/adr/.
  TRIGGER WHEN: an interview settles a design, contract or domain decision; a task needs the decisions governing its scope; a merged change promotes a Proposed record.
  DO NOT TRIGGER WHEN: the change needs no decision beyond existing records, or the request is project documentation (use project-knowledge:project-knowledge).
---

> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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

# Architecture decision records

Load `project-protocol:project-protocol` for run ownership and authorization.
The helper is `python "<plugin-root>/skills/adr-method/scripts/adr_tool.py"`;
it writes records and the index atomically and refuses an inconsistent state
before the first write. The record format is `references/adr-template.md`.

## Load map

| Step | Read | Run |
|---|---|---|
| Any | this file | `validate --project ROOT` before relying on the directory |
| Before an interview | nothing more | `resolve --project ROOT --paths P... --modules M... --domains D... --symbols S...` |
| Writing a record | `references/adr-template.md` | `template`, then `propose` |
| After a verified merge | nothing more | `promote --adr ADR-NNNN --sha MERGED_SHA` |
| First use in a project | nothing more | `init-index --project ROOT` |

## Resolve: what governs this scope

Input: the paths, modules, domains and Codebase Map symbol identities the task
touches. Output: the `Accepted`, unsuperseded records that match, with the
reason for each match, most specific first. Load the one to three records that
matter into the interview or the worker brief; never the whole directory.
`Proposed` records are not returned: a decision not yet implemented binds only
the task that proposed it.

## Propose: the interview's output

Precondition: the interview fixed scope, at least one nominal, one boundary and
one rejection example, the alternatives it rejected and the invariants it
requires. Write the body from `template`, then run `propose` with title, slug,
the run or task identity, the current `HEAD`, the scope lists and any
`--supersedes`. The helper allocates the next identity, validates the sections
and refuses template placeholders. Outcome codes:

- `written`: the record exists as `Proposed` and the index lists it.
- `refused`: the helper named the missing section, item or scope; fix the body
  and run again. Do not hand-edit the index.

A record that supersedes another names it at proposal time, so reviewers can
compare the two while the task runs.

## Promote: at the merge, never before

Precondition: the candidate that implements the record is merged and the run's
required gates passed on that commit. `promote` sets `Accepted`,
`accepted_at_sha` and `last_verified_sha` to the merged commit, marks each
`supersedes` target `Superseded by` this record and rewrites the index, as one
transaction. A `Proposed` record that was abandoned stays `Proposed` with its
task identity; retire it by superseding it from a later record, never by
deletion.

## Instructions and documentation

Durable instructions (`AGENTS.md`, `CLAUDE.md`) carry the active records for a
domain inside the loop block that `project-knowledge:instructions-method`
maintains; the reasoning stays in the record. Guides cite a record by identity
and never restate its examples.
