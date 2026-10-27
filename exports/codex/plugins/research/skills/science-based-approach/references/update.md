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

# Refresh and supersession

Read `runtime.md` for selectors, revision checks and receipts. Explicit
update-research works even when Science Mode is OFF or its config is malformed;
it does not repair/change mode. Reuse caller scope and grants.

Resolve an exact ID or topic; disambiguate multiple matches before mutation.
With no selector, use research explicitly linked to the current task only when
exactly one identity is linked; otherwise ask for the scope before any mutation.
An empty inventory, including an empty all/tutte batch, returns `nessuna ricerca
da aggiornare` without network work or archive writes. A nonexistent selector
never implicitly creates research.
Apply `reuse.md` first, including existing unindexed Markdown. Keep the same
current file and identity: new evidence updates it, visibly strikes through
superseded claims, refreshes research timestamps and appends a descriptive
changelog. Historical snapshots are separate from that single current page.
For all/tutte, snapshot the list once, visit each canonical identity once and
report successes, unchanged, partial and failed records separately. A failed
record does not imply success for the batch or prevent independent updates.

For each record read its pinned revision and question, compare relevant
technology versions, search new findings/replications and check source versions
and editorial notices through primary publishers and available metadata services.
Record actual queries, access times, coverage and limits.

Keep these separate: source publication/editorial status; support for each claim;
local applicability; research supersession; experiment execution/result. Age alone
never makes a paper obsolete. A retraction triggers review of dependent claims,
not proof of their opposite. Suspend the retracted source as reliable positive
support until clarified; identify dependent claims and publish their changed
status and notice while preserving the historical revision. A newer technology may change applicability without
refuting the original result.

Use an immutable check receipt for every attempt. A completed no-change check
leaves the scientific revision unchanged; failed/partial/cancelled checks never
claim full freshness. Distinguish last_checked_at, latest complete check and
last_updated_at. Material changes publish a new immutable revision with expected
revision, cumulative changelog, reasons, replacement evidence, changed claim IDs
and residual uncertainty. Never erase old sources or revisions.

List known consuming specifications, ADR/FRD and tests, the pinned claims they
use and why they need review. State coverage of that consumer list. The owner
decides subsequent edits; accepted records are never silently rewritten.
