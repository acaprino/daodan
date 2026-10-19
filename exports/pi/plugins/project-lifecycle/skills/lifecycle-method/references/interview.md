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

# Phases 2 and 3: interview and decision record

## Grounding, before the first question

1. Load `codebase-map:map-method`. From the bound run, take the symbol cards of
   the entities the request names and their one-hop callers and callees; read
   the current source of each through the map's source reader. A card is a
   lead; the source is the fact.
2. Load `project-knowledge:adr-method` and run `resolve` with the scope's
   paths, modules, domains and symbols. The one to three active records it
   returns are the constraints the task inherits.
3. Read the base-commit instructions (`AGENTS.md`, `CLAUDE.md`, nested files)
   through `git show <base_sha>:<path>`.
4. Record the grounding (run, cards, records, instructions) in the run's `adr`
   section as `active` and in the brief that every later worker receives.

## One question per turn

Ask one question at a time, anchored to a file and line, with the current
behavior and the proposed behavior written as concrete input and output
taken from the code or its tests. Prefer a question that closes a branch of
the design over one that gathers color. Offer the recommended answer and what
the alternatives cost.

Stop asking when all of these are fixed:

- scope: paths, modules, domains, symbols, and what is out of scope;
- at least one nominal, one boundary and one rejection example, each as
  input and expected output;
- every alternative the user rejected, with the reason;
- the invariants the code and its tests must keep;
- whether an active record is respected or must be superseded, and by what;
- the authorization: edit, commit, both, or plan only.

Do not infer a missing answer. A decision the user did not make stays open in
the record as a question for the plan review to raise again.

## The record

Write the body from the helper's `template`, filling the examples (`EX-*`),
rejected alternatives (`RA-*`) and invariants (`INV-*`) from the answers.
Run `propose` with the title, a slug, the run identity, `base_sha`, the scope
lists and any `--supersedes`. Record the returned identity in the run's `adr`
section as `proposed`. The record stays `Proposed` until integration.

## Review of the record (stage A)

Run `senior-review:review-method` through `senior-review:review-preparation`
with `target-kind=spec` on the record and shape `light`. The preparation
selects the premise lens against the current source, the logic lens for
invariants and missing examples, the abstraction lens against the concept
index, and the stack lenses the scope activates. A `disputed` premise or a
blocking finding reopens the interview on that point; nothing proceeds to the
plan with a refuted premise.

On `--peer-review`, dispatch `peer-review:packet-builder` and
`peer-review:respondent` through `peer-review:cross-model-peer-review` on the
record; standoffs return to the user as decisions. On `--second-opinion`,
load the `moe:multi-model-deliberation` skill with the record as the brief.
Both are opt-in.
