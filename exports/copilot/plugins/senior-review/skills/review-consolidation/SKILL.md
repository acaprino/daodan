---
name: review-consolidation
description: >
  Consolidate native review findings with evidence provenance, delivery accounting and adversarial verification. Load when consolidating code-review, team-review or pr-review results.
---

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

# Review consolidation

Input: variant, prepared context/selection, native results and delivery ledger.
Output: native report and project-result envelope through existing review contracts,
without another finding schema.

Read `references/stack-findings.md` before confidence filtering or severity sorting.
Retain native labels, roles and evidence; validate required delivery fields.

Load `senior-review:review-quality-gates`. Account for every expected job and
member/scope obligation against candidate/body-bound deliveries before filtering.
Validate `member_results`, including failures, timeouts and incomplete coverage.
Share canonical finding IDs without duplicating findings; preserve source role,
native severity, premise and evidence provenance in one ledger. Failed or missing
required coverage prevents completion; never merge failure into success.
A single final writer emits the report.

Account separately for blind derivation, critic and eligible verification lenses
under work-controller; discovery cannot satisfy a check through its job ID, file
or context. Historical records retain their original contract.

Load `skill-catalog:skill-catalog`; run `validate-usage` against prepared
`knowledge_selection` and worker `knowledge_usage`. Verify assigned scope/worker,
selection/body fingerprints and used references. Failed/stale/missing selected
knowledge fails delivery coverage and leaves required candidate gates unsatisfied.
Preserve inventory/classification/match gaps in `knowledge_coverage` and report
coverage. Knowledge neither proves execution nor establishes a finding's premise.
Generic patterns require source evidence and falsifiable premises. Independent
derivation may use domain knowledge, never shared project conclusions or peer findings.

Read `references/<variant>.md`; execute consolidation, fresh lenses, completeness
and reporting. PR description follows the same delivery/provenance/panel gates.
Shared premises are echoes, not independent corroboration. Deduplication preserves
independent evidence and distinct failure modes.

Load `work-controller:work-record` to validate the snapshot and publish the
envelope. Explicitly degraded coverage cannot claim missing reviewers ran or
static analysis exercised runtime; mandatory missing coverage keeps completion open.

## Optional human view

The final writer saves complete native Markdown once in the owned output root,
using the caller's path or variant filename. Link native details with verdict,
material findings and gaps; include full text when requested or needed for approval.
Workers deliver native reports, never separate UI or another final synthesis.

For requested HTML or useful navigation/filters,
load the `report-rendering:report-renderer` skill and resolve its helper there.
Use saved Markdown as `--input`, its same-stem `.html` sibling as `--output`,
`--profile review` and the prepared owned root as `--root`. The fixed renderer
adds controls, never analysis, findings or a schema. Native `output_path` remains
authoritative; account for HTML as a derived view.

Preserve native sections/fields, roles/severities, evidence/confidence, premises/
provenance, verification, filtered counts, knowledge/coverage gaps and degraded or
unknown states. Link worker and verification details instead of copying them.
Economy never removes required evidence, independent premise reconstruction,
lenses or gates.

Verify rendering before delivery. Diagnose failure through provider recovery and
preserve Markdown. Persistent optional failure is explicitly reported and never
listed as successful. Requested HTML remains an open deliverable; unrequested
optional view failure leaves the native outcome intact.
