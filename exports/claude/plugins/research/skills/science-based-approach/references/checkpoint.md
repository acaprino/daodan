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

# Automatic scientific checkpoint

Receive project, caller task ID, phase, semantic context (question, constraints,
candidate/document and relevant technology versions), budget and grants. Apply
during brainstorming, substantive problem/algorithm work, specification drafting
and ADR/FRD proposal or revision. An editorial-only change can be not-applicable.

1. Read mode using the helper in `runtime.md` before reading the archive.
   OFF returns disabled with no scientific reads, search or writes.
   Malformed configuration returns configuration-error; do not repair silently.
2. Evaluate whether empirical/theoretical evidence could affect this decision.
   If not, record not-applicable in the caller's run with the reason.
   No keyword match alone triggers research. Ignore callbacks caused solely by
   writing research, templates, receipts, indexes or mode configuration.
3. Inspect the checkpoint key using caller task, phase, semantic context and
   current mode revision. A workflow and a native event use the same key.
   Claim it with the helper only where the caller grants state writes. Do not
   launch another coordinator or repeat an in-progress/completed key. On resume,
   inspect the existing owner/result; an interrupted claim is not success.
4. Apply `reuse.md` to indexed and unindexed related Markdown before any new
   document. Consult pertinent current research. Choose reuse, refresh or new research
   from actual question/version/source fit. A reuse cites the exact revision
   and claims, and does not claim a new online check. Changed constraints form
   a new context; a simple save does not. Compose this skill in the caller.
5. Record the outcome and reason: disabled, not-applicable, reused, updated,
   created, partial, unavailable or configuration-error, with revision/claim
   references. Re-read mode before new automatic work; retain labelled partial
   output on cancellation and stop at the next safe point.

ON grants no additional write permission. Brainstorming may publish research only
when its caller already authorizes documented research; otherwise use chat or the
owned run. Specifications and decisions pin research revision and claim IDs.
Evidence never approves a requirement or rewrites an accepted ADR/FRD.

Native session/prompt hooks only supply routing context; they perform no research,
network access, mode mutation or archive publication. Claude/Codex packages
register supported events, subject to the host's trust settings. OpenCode's
loader registers prompt and primary-context callbacks, with a first-prompt
session-start fallback when creation was not observed. Copilot and Pi retain
these method checkpoints without promising interception outside Daodan.

## Resume and explicit retry

A running checkpoint is unfinished work. Inspect its task_id and the original
Work Controller run; resume that same authorized work without claiming a new
checkpoint, then finish the existing key with outcome/reason/references. Never
mark it successful because the previous worker stopped. If its holder is still
active, use the caller's normal coordination and do not duplicate execution.

A terminal partial/unavailable result remains historical. Retry only when the
user requests it or relevant context changes. Include that request's stable
identity in the semantic context, preserving the previous result; this forms a
new deduplication key. An explicit research command can also perform the requested
retry without toggling mode. There is no automatic retry scheduler.
