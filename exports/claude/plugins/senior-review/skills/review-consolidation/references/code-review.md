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



## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

## Step 4: Consolidate Findings & Extract Score

After all agents complete, run the merge pipeline:

### 4a. Confidence Gating

Apply a three-tier confidence filter to all findings:

| Confidence | Action |
|------------|--------|
| **< 0.50 (< 50%)** | **Suppress** -- finding is speculative, discard it. Record suppressed count. |
| **0.50 - 0.69** | **Flag** -- include in report but mark as low-confidence |
| **>= 0.70** | **Report** -- full confidence, include normally |

### 4b. Deduplication

When multiple agents flag the same issue, merge them:

1. Compute fingerprint: `normalize(file) + line_bucket(line, +-3) + normalize(title)`
2. When fingerprints match:
   - Keep the **highest severity**
   - Keep the **highest confidence** with strongest evidence
   - **Union** the evidence from all agents
   - Weigh the agreement by provenance, per `## Shared-Context Provenance Rule` in the `senior-review:review-quality-gates` skill, instead of just noting which agents flagged it:
     - All agreeing agents report `independent` `premise_provenance`, or their load-bearing premises are disjoint: **corroborated**. Note the agreeing agents; the merge is a likely-real root cause.
     - All agreeing agents share the same `shared-context` premise: **echo**. Note it as `Echo: N agents agreed from the shared premise "[premise text]"`. This raises no confidence and no severity, and it is not evidence the finding is real.
     - Mixed: count only the independent agents toward corroboration.
3. Record the dedup count, split into corroborated merges and echo merges

### 4c. Separate Pre-existing

Pull out findings with `[PRE-EXISTING]` prefix into a separate list. These are reported in their own section and do NOT count toward the verdict.

### 4d. Sort & Score

- Sort by severity (Critical first) -> confidence (descending) -> file path -> line number
- Extract the Code Quality Score from code-auditor (Agent A) directly

## Step 4b: Adversarial Verification Panel

Skip this step if `--fast` was passed. Otherwise verify findings with the 4-lens panel defined in the `senior-review:review-quality-gates` skill, file `references/verification-panel.md` (resolve it inside that skill's installed directory), section `## Adversarial Verification Panel`. This replaces the former single-validator step: four independent lenses (premise veto, reachability/correctness, false-positive causes, severity) catch more failure modes than one judge, and the scope widens from Critical/High only to every finding above the confidence floor.

### Selection

- **Default:** every finding with confidence `>= 50%` that survived Step 4b deduplication, regardless of severity.
- **Cost guard** (more than 25 surviving findings AND `--rigorous` not set): narrow to all Critical/High plus any Medium/Low in the 50-75% confidence band or with conflicting reviewer severity. The rest pass through tagged `unverified (cost-guard)`. Note the narrowing in the report.
- **`--rigorous`:** verify everything above the floor, ignoring the cap.

The cost-guard threshold is a finding-count proxy (no token budget exists in this substrate).

### Panel

**Lens 0 first.** For each selected finding whose `premise_provenance` is `shared-context` or `mixed`, **or whose declared premise carries a universal or negative quantifier (`no`, `never`, `cannot`, `always`, `only`) at any provenance**, dispatch lens 0 through the declared `senior-review:premise-auditor` binding (mode 2, inheriting the session model) using the Lens 0 prompt from the skill, with the Codebase Map line resolved to the `.codebase-map/` mirror and the interconnect-map and knowledge-provenance lines omitted, since this command builds neither. A finding declaring no provenance is `shared-context` whenever `.codebase-map/` context was injected into the agent prompts, and the report records the agent as format-non-compliant; it is `independent` only when no such context was supplied at all. Defaulting the other way would send exactly the non-compliant findings Lens 0 exists to catch straight past the veto. Apply the skill's Lens 0 resolution table: a `REFUTED` verdict targeting `PREMISE` discards the finding (`filtered: premise-refuted`) without spawning lenses 1-2; targeting `SUPPORT` on `mixed` provenance strikes the shared leg and restates the finding from the surviving independent evidence before it proceeds; targeting `SUPPORT` on `shared-context` provenance discards it the same way. `UNCERTAIN` and `HOLDS` proceed to lenses 1-2, `UNCERTAIN` tagged `premise-contested`. Findings declared `independent` whose premise carries no such quantifier skip lens 0 entirely and proceed directly to lenses 1-2.

For each finding that reaches this step, dispatch lenses 1 and 2 independently through the declared `project-protocol:isolated-worker` binding using the skill's full lens briefs, owned scope, authorization, budget and expected report paths. Use the host harness's supported topology, inherit the session model and substitute the finding, diff and full file content. Dispatch lens 3 through that same binding only for findings that survive lenses 1-2, per the skill's gated-lens rule: calibrating a finding about to be discarded is spend for nothing.

### Survival rule

A finding discarded by Lens 0 never reaches this rule. Otherwise apply the skill's rule: survive on `>= 2` of lenses 1-2 voting REAL; discard (`filtered`, counted) on `>= 2` FALSE_POSITIVE; tie or fewer-than-2-verdicts means survive and mark `contested`. Final severity is the lens-3 vote when confirmed real, else the original.

**After the panel completes:**
- Drop `filtered` findings; apply recalibrated severities; tag `contested`, `premise-contested`, and `unverified (cost-guard)` findings.
- Add to the report: `Verification: X of Y (4-lens panel), Z false positives, W contested, V premise-refuted, U premise-contested`.

Medium and Low findings are no longer skipped by default: they enter the panel like any other finding above the floor (subject to the cost guard).

## Step 4c: Completeness Critic

Skip this step if `--fast` was passed. Otherwise run the critic defined in the `senior-review:review-quality-gates` skill, file `references/verification-panel.md`, section `## Completeness Critic`.

1. Dispatch one `project-protocol:isolated-worker` critic through the host harness with the skill's critic prompt, owned scope, authorization, budget and expected report path. Record its delivered or failed outcome before closing the critic phase. Pass the verified findings, the changed-file scope, the agents that ran, and the Codebase Map context paths if `.codebase-map/` exists (else "none").
2. If the critic names a single high-risk uncovered area under `## Recommended follow-up` AND the cost guard did not fire: spawn ONE targeted reviewer (the most specialized agent for that area) scoped to the files named, then route its findings back through Step 4 (dedup) and Step 4b (panel). At most one round.
3. Otherwise degrade to report-only.
4. Carry the critic's `## Coverage Gaps` list into the Step 5 report.
