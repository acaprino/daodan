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

# Verification panel and completeness critic

Consolidation unit of `senior-review:review-quality-gates`; account for every
selected reviewer first. Briefs: `references/panel-and-critic-prompts.md`.

Roster/run requirements set minimum panel/critic obligations. `--fast`/cost guard
reduce optional work only. `--no-context` changes inputs, never roster, blind
derivation, Lens 0 eligibility or actual provenance. Missing required evidence/delivery
leaves the run incomplete.

## Adversarial Verification Panel

For each selected deduplicated finding, dispatch isolated lenses through the
consuming workflow's host harness: Lens 0 uses declared
`senior-review:premise-auditor`; lenses 1-3 use declared
`project-protocol:isolated-worker`. Briefs carry owned scope, authorization, budget,
inputs and report path. Ledger delivered/failed outcomes. Lenses receive no peer
findings before independent delivery. Inherit session model; overrides require
explicit user request and supported host binding, never invented aliases.

### Lens gating and Lens 0 resolution

1. **Lens 0 runs first** (Premise Challenge, Mode 2): eligible provenance is
   `shared-context`, `mixed`, or missing after pipeline execution; also any
   universal/negative premise (`no`, `never`, `cannot`, `always`, `only`).
   - `REFUTED` (`PREMISE`) or (`SUPPORT` + `shared-context`): discard
     (`filtered: premise-refuted`); do not spawn lenses 1-2.
   - `REFUTED` (`SUPPORT` + `mixed`): strike shared support, restate from
     independent evidence, then lenses 1-2.
   - `UNCERTAIN`, errors or `REFUTED` without `file:line`: lenses 1-2,
     tagged `premise-contested`.
   - `HOLDS`: lenses 1-2 unchanged.
   - Record `premise_form: non-compliant` regardless of verdict.
   - **Absence claims too:** universal assurance over shared/multi-instance state
     receives Lens 0: verify instance/path scope and alternate paths.
     `REFUTED` becomes a contested coverage gap citing the counterexample, never
     an opposite defect without its own lenses 1-2.
2. **Lenses 1 (Reachability) and 2 (False-Positive Causes)** run independently:
   - >= 2 `REAL`: survives.
   - >= 2 `FALSE_POSITIVE`: discard, report filtered count.
   - Tie or < 2 valid verdicts: survives `contested` (fail-open).
3. **Lens 3 (Severity Calibration)**: gated, only after survival.
   Confirmed real: use its `severity_vote`; otherwise retain reviewer severity.

### Selection and Cost Guard

- **Normal:** every deduplicated finding with confidence >= 50%.
- **Cost guard:** > 25 survivors without `--rigorous`. Preserve required
  verification; optional selection retains Critical/High, Medium/Low at 50-75%
  confidence or conflicting severity. Label omitted optional findings
  `unverified (cost-guard)`; disclose narrowing. Count proxies token spend.
- **`--rigorous`:** all above the floor. **`--fast`:** optional panel/critic
  only; never waives required checks or Lens 0 eligibility.

## Completeness Critic

When required or included optionally in preparation, one isolated
`project-protocol:isolated-worker` runs after verification through the same host
binding. Prompt: `references/panel-and-critic-prompts.md`, Section 3.
Emit `## Coverage Gaps` for:
1. Warranted dimensions not run.
2. Unexamined scoped files; no citation alone does not prove omission.
3. Unverified interconnect assumptions.
4. Unexamined high-risk hot-spots (`05-risks.md`/Integration Hot-Spots); zero findings alone is not a gap.
5. Findings accepted on derived metrics alone or without user-visible consequences.

For high-risk uncovered scope, allow one targeted follow-up round with an
already-permitted reviewer; deduplicate and verify its findings. Cost guard/`--fast`
suppress optional follow-up only. Required coverage remains incomplete; an
unlisted role is a selection gap, never dispatch authorization.
