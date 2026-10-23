<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# Phases 2 and 3: interview and decision record

## Grounding before questions

1. Load `codebase-map:map-method`; deepen the requested area using
   `references/deepen.md`. Read the named entities' cards, their one-hop
   neighbours from `edit-impact`, and current source. Cards are leads; source
   establishes facts.
2. Load `project-knowledge:adr-method`; `resolve` the scope. Inherit the
   returned one to three active records as constraints.
3. Read base-commit instructions (`AGENTS.md`, `CLAUDE.md`, nested files)
   through `git show <base_sha>:<path>`.
4. Record grounding as `active` in the run's `adr` section and every later
   worker brief.

Before fixing scope, trace affected flows in source beyond immediate map
neighbours: callers, tests, fixtures, configuration and exports that must change
together. These are required scope, not extra features. For bugs, locate the
shared cause before choosing a repair site. Necessary paths outside approved
scope return to planning before edits there.

## One question per turn

Ask one question at a time. Anchor it to a file and line, showing current and proposed behavior
through concrete inputs and outputs from code or tests. Prefer questions that
close design branches. Recommend an answer and explain alternatives' costs.
Use the host's question tool; without one, record every pending question in the
run's `questions` section, end the turn listing them, and resume that run with
answers.

Stop when these are fixed:

- scope: paths, modules, domains, symbols and exclusions;
- at least one nominal, one boundary and one rejection example, each with
  input and expected output;
- every alternative the user rejected, with its reason;
- code and test invariants;
- active records respected or superseded, and their replacements;
- authorization: edit, commit, both or plan only.

Never infer missing answers: undecided questions stay open in the record for
plan review to raise again.

## The record

Fill the helper's `template` with answered examples (`EX-*`), rejected
alternatives (`RA-*`) and invariants (`INV-*`). Run `propose` with title, slug,
run identity, `base_sha`, scope lists and any `--supersedes`. Save the returned
identity as `proposed` in the run's `adr` section. Keep the record `Proposed`
until integration.

## Record review (stage A)

Run `senior-review:review-method` on the record: shape `light`, kind `spec`, stage `record`.
The premise auditor checks every code claim and missing boundary or rejection
examples. False claims or blocking findings reopen that interview point.

Only on request, challenge the record through `peer-review:cross-model-peer-review`,
dispatching `peer-review:packet-builder` and `peer-review:respondent`; return
standoffs to the user. For a requested second opinion, load
`moe:multi-model-deliberation` on the record.
