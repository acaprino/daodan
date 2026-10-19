---
name: review-consolidation
description: >
  Consolidate native review findings with evidence provenance, delivery accounting and adversarial verification. Load when consolidating code-review, team-review or pr-review results.
---

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

# Review consolidation

Input: variant, prepared brief/context/selection, native reviewer results, delivery
ledger. Output: the existing native review report
plus a project-result envelope. Keep canonical native reports; use the existing
review contracts to integrate their findings, without another finding schema.

Read `references/stack-findings.md` inside this skill before confidence filtering
or severity sorting. It defines how the specialist outputs enter the native review
contract while retaining original labels, source roles and evidence. Validate
required fields before treating a specialist delivery as complete.

Load the `senior-review:review-quality-gates` skill. Before consolidation account for every
selected reviewer, including stack specialists, failure, timeout or incomplete
delivery. Use one input finding set and delivery ledger for all dimensions;
preserve source role, native severity, premise and evidence provenance. Never merge
a failed worker into a successful result. A single final writer emits the report.

Load the `skill-catalog:skill-catalog` skill and run `validate-usage` against the
prepared `knowledge_selection` and all worker `knowledge_usage` records. Verify
every assigned scope/worker, the selection/body fingerprints and used references.
Failed, stale or missing selected knowledge is failed delivery coverage; any required
candidate gate stays unsatisfied. Keep unresolved inventory/classification/match
gaps in `knowledge_coverage` and the same report's coverage section. Loaded knowledge
does not prove that code paths ran, or establish a finding's premise. Preserve
knowledge provenance with each finding; generic knowledge patterns still need code
evidence and falsifiable premises. An independent derivation may use generic domain
knowledge, never shared project conclusions or peer findings.

Read `references/<variant>.md` inside this skill. Execute its consolidation, fresh
verification lenses, completeness check and report stages. For PR review, use the
same delivery/provenance/panel rules before producing the native PR description.
Two reviewers inheriting the same premise are an echo, not independent corroboration.
Deduplication preserves independent evidence and distinct failure modes.

Load the `project-protocol:project-protocol` skill to validate the snapshot and publish the
result envelope. A report can complete with explicitly degraded coverage; it cannot
claim a missing reviewer ran, or that static analysis exercised runtime behavior.

## Optional human view

The final writer saves the complete native Markdown report in the prepared owned
output root, using the caller's declared report path or the variant's filename.
Generate report content once. In the conversation link to native details with the
verdict, material findings and remaining gaps, except when a required approval or
the user's request needs the complete text. Workers deliver their native reports;
they do not produce separate UI or another final synthesis.

When the user requests HTML, or navigation and finding-table filters would
materially aid review, load the `report-rendering:report-renderer` skill and resolve its
helper through that skill. Use the saved native Markdown as `--input`, its
same-stem `.html` sibling as `--output`, `--profile review`, and the same prepared
owned output root as `--root`. The fixed renderer supplies controls, without new
analysis, finding content or a second finding schema. Keep the native report as
the authoritative `output_path`; account for the HTML only as a derived view.

Preserve all native sections and fields, source roles and severities, evidence,
confidence, premises and their provenance, verification results, filtered counts,
knowledge coverage, coverage gaps and degraded or unknown states. Link to native
worker and verification details instead of copying their full content into another
layout. Output economy never removes required evidence, independent premise
reconstruction, verification lenses or completion gates.

Verify the helper outcome before claiming delivery. Diagnose a rendering error
through the provider's recovery contract and preserve native Markdown. If the
view still fails, record the optional view failure explicitly and do not list it
as a successful output. An explicitly requested HTML deliverable remains open;
an unrequested optional view failure leaves the native review outcome intact.
