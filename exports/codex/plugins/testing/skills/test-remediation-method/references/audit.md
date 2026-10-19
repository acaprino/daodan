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

## Step 3: Qualitative audit (agent)

Spawn this plugin's `test-suite-auditor` agent with: the target path, the Step 2 metrics, the scope, run permission (`--no-run` propagates), and an output path of `<output-root>/findings.md`. The agent covers the judgment dimensions (orphans, duplicates, contradictions, implementation-coupling, never-failing tests) and returns the findings report. It is report-only; nothing moves in this step.

## Step 4: Write TEST_AUDIT.md

Prepend a `## Audit <ISO date>` section to `<path>/TEST_AUDIT.md` (create the file when absent) in the format defined by `remediation-workflow.md` section 1: the metrics table with deltas against the previous audit section, then the findings summary by severity from Step 3, then the recommended remediation order.

Without `--fix`, print the report path, the metrics table, and the top findings.
For requested HTML or useful navigation/comparison, the coordinator reads
`references/human-view.md` in this skill and renders the completed native audit
before normal delivery and run closure. Do not proceed to quarantine.

## Step 5: Quarantine (only with `--fix`)

Use this method's accepted category inventory and the common project protocol: baseline, candidate gate, owned phase recovery and authorized commit. No external review fix loop is executed.

### 5a: Category acceptance gate

Build candidate batches only after the canonical cause classification below.
Removed source alone is not a confirmed orphan: follow renames/migrations and
verify the behavior was retired. Age of a skip and a red baseline are investigation
signals. Product defects and unknown causes stay active and block the affected
change; wrong oracles are repaired, environment failures route to environment/
configuration owners. Only confirmed ineligible/obsolete, unresolved environment
limitations or evidenced intermittent tests may be proposed for temporary
quarantine with remaining protection, owner, return condition and explicit acceptance.

Present the non-empty categories through the host question mechanism with multiple category choices (label: category and file count; description: sample paths). Only accepted categories proceed. This gate is never bypassed: `--yes` affects only the per-batch re-confirmation below.

### 5b: Baseline

Record the exact starting snapshot, native test results and meaningful behavior
protection. Under `--no-run`, historical metrics remain stale diagnostic evidence.
Mutation needs an executable local gate or a remote gate for this exact candidate
snapshot, with required command/configuration and job identity. A collect-only
check is structural evidence and cannot satisfy a behavior gate.

### 5c: Batch execution

Process accepted categories in fixed order, lowest ambiguity first: `orphan`, `skipped`, `failing`, `flaky`. Per batch, first capture `pre_phase_sha`, owned paths and required gate configuration:

1. Preview the exact file list and target paths (`tests/_quarantine/<original relative path>`). Confirm the batch unless `--yes`.
2. First batch only: add the runner's CI exclusion from this skill's `references/quarantine-layout.md` and create its native README ledger, preserving existing runner exclusions.
3. `git mv` each file to its mirrored quarantine path; append one ledger row per file (original path, date, category, cause, reason, evidence, owner, return condition, preserved protection and candidate gate identity).
4. Record the candidate snapshot and run its required checks. Preserve every approved behavior, distinct failure mode and bugfix regression. Neither pass counts nor line coverage establish equivalence; report unresolved or unexercised protection explicitly. Under `--no-run`, await authorized same-snapshot remote evidence instead of using collection or old CI as a pass.
5. Gate failed: use `project-protocol:project-protocol` recovery for the captured `pre_phase_sha` or exact owned pre-edit snapshot. Restore only owned changes and verified newly created artifacts; verify restoration and halt. No broad cleanup of the quarantine directory, and no deletion of artifacts created by another run.
6. Gate passed: commit the exact accepted batch only when authorized, with the candidate gate identity in its ledger.

### 5d: Refresh the audit

Refresh the current `## Audit <date>` section of `TEST_AUDIT.md` with the measured
post-quarantine numbers and remaining protection. Include the per-batch table,
suite status and Step 5e next steps in that native section. Finalize owned audit/ledger edits
before capturing their candidate snapshot and gating an authorized commit. If the
last batch is already committed, treat this refresh as a separate owned candidate
with the protocol's required gate, not an ungated trailing commit. Run-envelope
results can record gate outcomes without changing the gated source snapshot.

### 5e: Report

Per-batch table (category, files, commit sha, gate result), the new suite status, and next steps:

- Consolidation of each module (mode `consolidate`, through `/daodan:tidy-repo`) for the modules ranked worst by duplicate/implementation-coupling density in Step 3.
- The quarantine lifecycle reminder from the skill: entries are processed when their module is next touched; entries older than 3 months become investigation candidates. Retirement still requires accepted inventory and evidence of retired behavior or verified equivalent replacement beyond age.

For requested HTML or useful navigation/comparison, the coordinator reads
`references/human-view.md` in this skill after the refreshed native audit and
required gates are final, before run closure. Render no intermediate audit that
later quarantine batches or refreshes would invalidate.

## Output locations

- `<path>/TEST_AUDIT.md`: the native audit history (committed only when authorized).
- `<output-root>/findings.md`: the full auditor report backing the latest audit section.
- `tests/_quarantine/` plus its `README.md` ledger: only under `--fix`.
