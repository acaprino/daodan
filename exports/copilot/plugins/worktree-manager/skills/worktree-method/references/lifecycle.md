<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

# Lifecycle handoff

The caller owns its task cycle and loads this reference through worktree-method.
Return evidence to that caller; never fabricate a completed review or waive its
required gates. Direct inventory and annotations require no merge workflow.

## Prepare and integrate

The integration choice offers Squash first and preselected, then full history
(and rebase only where supported). Record the user's actual answer through the
existing question mechanism. Preselection is not consent. Reuse a scoped grant
already given for the exact candidate; changed candidate, target or method
requires revalidation. Apply repository merge rules and remote protections.

Preserve the source branch and original commits. Prepare the selected result in
an integration candidate with explicit source and target SHAs. Stage only owned,
authorized paths. Squash, rebase, conflict resolution and content-changing hooks
precede final tests and review. Full history must not acquire an implicit rebase.
The caller reviews the resulting candidate and records its identity, including
the target on which it was prepared. If either side moves, stop and refresh the
affected preparation and evidence.

Worktrunk's default merge can stage all local files, squash, rebase and remove
the source checkout. Do not use that default as a final integration operation.
The supported CLI documents `merge --no-commit --no-rebase --no-remove --no-hooks`
for integrating an already prepared, clean candidate without those transforms.
Use `--no-ff` only if a merge commit was chosen and the caller's review contract
covers that integration. Invoke the verified executable with explicit cwd and
controlled configuration; do not reuse a shell alias or append arbitrary user
flags. A local merge never fetches or publishes to GitHub. Remote PR integration
continues through the caller's GitHub method and branch-protection checks.

Work Controller requires current HEAD in the run-bound checkout to equal the
recorded merged SHA. Ordinarily it must descend from the reviewed candidate.
For a server-side squash, record `integration.strategy: squash` and the full
pre-merge `integration.target_sha`. The helper verifies actual Git objects: the
reviewed candidate includes that target, the merged commit has exactly that
target as its sole parent, and both candidate and result have the same tree.
It also requires the review snapshot to match the clean integrated checkout.
Fetch the result before checking it; a moved target or different tree requires
fresh preparation and review. There is no equivalent exception for an arbitrary
rebase. Retain the reviewed commit locally until verification and archival finish.
Do not rewrite sealed wave receipts to make a later squash appear reviewed.
Do not complete from another checkout merely because its files look identical.
The delivery owner must establish the original binding at the integrated result
and verify current state before closure, or leave the task open with the actual
integration recorded. Preserve the original branch when moving a clean checkout
to the integrated commit; never force-reset local work. Use a clean detached
checkout at that SHA in the original run-bound path, keeping the source branch
intact. Before detaching, persist the integration result, pinned target and
delivered branch candidate review while the recorded candidate still names the
reviewed source commit and raw snapshot. After detaching, call `resume` with the
same authorizations. It revalidates that recorded proof and original identity,
preserves the source branch and sealed receipts, and refreshes the candidate.
An interruption at this handoff uses the same resume route; discover a detached
task by the original checkout path and exact run ID, not branch `HEAD`.
Changed work blocks that transition. Realignment that changes tracked
content needs a new reviewed, authorized integration and fresh final gates.

The proof retains the raw reviewed snapshot and compares scoped content with
actual committed blobs. It recognizes Git's built-in text line-ending conversion
when committed and live attributes/configuration prove that conversion,
including Windows CRLF checkouts. Each matching raw blob is accepted first;
Git's own text statistics distinguish forced text from automatic binary detection
and preserve legacy CRLF index blobs. Arbitrary filters, encoding transforms and identity substitutions are
not accepted as equivalence evidence. Preserve an unsupported proof failure;
never change repository conversion settings automatically or relabel the review.

## Remove only owned, concluded workspaces

Record integration first. Close the run under its original binding before
removing that checkout. Worktree removal and branch disposition are separate:
a successful merge with failed cleanup is not another merge to repeat.

Before removal, re-resolve Git inventory, canonical path, branch/head, task and
holder. Confirm no active session, lock, nested worktree, changed fingerprint,
tracked changes, untracked files or ignored local data needing preservation.
Inspect ignored data explicitly: upstream removal can delete it. Only scoped
existing authorization permits removal; otherwise present the concrete path and
data disposition once. A catalog annotation alone proves no deletion authority.

Use foreground cleanup of the verified owned path and preserve the branch when
original history or evidence requires it. Inspect the actual Git inventory and
filesystem after return; do not interpret background launch as deletion success.
Keep task records and catalog history in the main home. Conflicts, interruptions
and partial cleanup retain their recovery information. No force removal, branch
force deletion or automatic trash purge belongs in this method.

Analysis-only tasks retain their report and close without invented commits or
merges. Their workspace still needs the same scoped removal checks.
