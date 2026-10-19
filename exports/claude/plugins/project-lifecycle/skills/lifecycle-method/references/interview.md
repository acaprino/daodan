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
before the first phase, and stop with that command when a required one is off.
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

## Grounding, before the first question

1. Load `codebase-map:map-method` and deepen the request's area as its
   `references/deepen.md` directs, then take the cards of the entities the
   request names and their one-hop neighbours from `edit-impact`, with their
   current source. A card is a lead; the source is the fact.
2. Load `project-knowledge:adr-method` and run `resolve` on the scope. The
   one to three active records it returns are the constraints the task
   inherits.
3. Read the base-commit instructions (`AGENTS.md`, `CLAUDE.md`, nested files)
   through `git show <base_sha>:<path>`.
4. Record the grounding in the run's `adr` section as `active` and in every
   later worker's brief.

## One question per turn

Ask one question at a time, anchored to a file and line, with the current
and the proposed behavior as concrete input and output from the code or its
tests. Prefer a question that closes a branch of the design. Offer the
recommended answer and what the alternatives cost. Ask through the host's
question tool; when the session has none, write every pending question to
the run's `questions` section, end the turn listing them, and resume on the
same run with the answers.

Stop asking when all of these are fixed:

- scope: paths, modules, domains, symbols, and what is out of scope;
- at least one nominal, one boundary and one rejection example, each as
  input and expected output;
- every alternative the user rejected, with the reason;
- the invariants the code and its tests must keep;
- whether an active record is respected or must be superseded, and by what;
- the authorization: edit, commit, both, or plan only.

Never infer a missing answer: a decision the user did not make stays open in
the record for the plan review to raise again.

## The record

Write the body from the helper's `template`, filling the examples (`EX-*`),
rejected alternatives (`RA-*`) and invariants (`INV-*`) from the answers.
Run `propose` with the title, a slug, the run identity, `base_sha`, the scope
lists and any `--supersedes`. Record the returned identity in the run's `adr`
section as `proposed`. The record stays `Proposed` until integration.

## Review of the record (stage A)

Run `senior-review:review-method` with shape `light`, kind `spec` and stage
`record` on the record: the premise auditor checks every claim it makes about
the code, and its missing boundary or rejection examples. A false claim or a
blocking finding reopens the interview on that point.

When the user asks another model to challenge the record, dispatch
`peer-review:packet-builder` and `peer-review:respondent` through
`peer-review:cross-model-peer-review`; standoffs return to the user. For a
second opinion, load the `moe:multi-model-deliberation` skill on the record.
Neither runs unasked.
