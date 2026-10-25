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

# Phases 2 and 3: interview and decision record

## Grounding before questions

1. Load `codebase-map:map-method`; deepen the requested area using
   `references/deepen.md`. Read entity cards, `edit-impact` one-hop neighbours and current source;
   cards are leads, source establishes facts.
2. Load `project-knowledge:adr-method`; `resolve` the scope. Inherit the
   returned one to three active records as constraints.
3. Read base-commit instructions (`AGENTS.md`, `CLAUDE.md`, nested files)
   through `git show <base_sha>:<path>`.
4. Record grounding as `active` in the run's `adr` section and every later
   worker brief.

Before fixing scope, trace affected callers, tests, fixtures, configuration and
exports beyond map neighbours. Include paths that must change together; locate
bugs’ shared cause before choosing repairs. Replan before editing unapproved paths.
Before splitting producer/consumer work, agree the authoritative contract and
wire/error/version compatibility. Derive types/mocks; check actual serialization.
A shared type suffices within an atomic boundary; schema validity proves no domain rule.

## One question per turn

Ask as the work record's question rule says, anchored to a file/line and
concrete current/proposed inputs and outputs. Close design branches.

Stop when these are fixed:

- scope: paths, modules, domains, symbols and exclusions;
- at least one nominal, one boundary and one rejection example, each with
  input and expected output;
- every alternative the user rejected, with its reason;
- code and test invariants;
- active records respected, revised or superseded;
- authorization: edit, commit, both or plan only.

Undecided questions stay open in the record for plan review.

## The record

Fill the helper's `template` with answered examples (`EX-*`), rejected
alternatives (`RA-*`) and invariants (`INV-*`). Run `propose` at `base_sha`,
`--revise` to change an active decision; its id is `adr.proposed`. Without
records, it is the run's `intent.md`.

## Review (stage A) and approval

Run `senior-review:review-method` on the record: shape `light`, kind `spec`, stage `record`.
False claims or blocking findings reopen that interview point.

On request only, challenge the record through `peer-review:cross-model-peer-review`,
dispatching `peer-review:packet-builder` and `peer-review:respondent`, standoffs
to the user, or load `moe:multi-model-deliberation` for a second opinion.

With records, show the record and its `digest` and ask the user to approve it;
on approval, `promote` it at `HEAD`, recording each `dependents_to_review` with
`ask`. Unapproved, it stays `Proposed`.
