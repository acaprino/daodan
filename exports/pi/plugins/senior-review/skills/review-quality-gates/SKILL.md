---
name: review-quality-gates
description: >
  Verification panel, completeness critic, pipeline conventions and shared-context provenance rules for multi-reviewer consolidation.
  TRIGGER WHEN: running /senior-review:team-review or /senior-review:code-review quality gates, or consolidating findings from parallel reviewers.
---

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

## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

# Review Quality Gates

Gates and consolidation rules shared by `/senior-review:team-review` and `/senior-review:code-review`.

## Reference router

| Need | Reference |
|---|---|
| Verbatim prompts for context-aware reviewers, Verification Panel Lenses 0-3, and the Completeness Critic | `references/panel-and-critic-prompts.md` |
| `/code-review` agent dispatch templates and Codebase Map context injection | `references/code-review-agents.md` |
| `/code-review` native output and optional HTML view rendering | `references/code-review-output.md` |
| `/code-review --fix` and `--commit` remediation loop | `references/code-review-fix-loop.md` |

## Shared-Context Provenance Rule

> **Evidence derived from a shared artifact cannot independently corroborate the claims contained in that same artifact. N reviewers agreeing on a premise they were all given is one observation, not N.**

Three consequences bind every gate below:
1. A reviewer that consumed a claim from the Codebase Map output or the interconnect map has not verified that claim. It must re-derive the claim independently before standing a finding on it.
2. Concordance between reviewers who share a premise is an **echo**. It raises no confidence and no severity. Consolidation reports it as such.
3. No metric may reward agreement with a shared artifact. Utilization of the map is an operational number, never a quality signal.

## Context Sharing Pattern

When `/team-review` runs in pipeline mode (no `--no-context`), reviewers receive three context artifacts produced in Phase 1:

1. **Codebase Map output** (from `codebase-map`) at `$XRAY_RUN_DIR` when the command started the run itself (`/team-review` Phase 1a), or the `.codebase-map/` mirror when consuming an existing analysis (`/code-review` Step 2). A command that started a run never reads the mirror. Files: `01-structure.md`, `02-interfaces.md`, `05-risks.md`, and optionally `03-flows.md`, `04-semantics.md`, `06-documentation.md`, `07-final-report.md`.
2. **Interconnect map** at `.team-review/02-interconnect.md` (from `codebase-map:semantic-interconnect-mapper`): contracts (formal / structural / implicit), invariants, domain rules, assumptions (verified / documented / unverified), integration hot-spots, change impact radius.
3. **Knowledge provenance** at `.team-review/01-knowledge-provenance.md` (from `/team-review` Phase 1d): which concepts each discovery branch found, which neither found, and which they disagree about.

A fourth artifact, `.team-review/01b-independent-claims.md`, is derived in Phase 1c by `senior-review:premise-auditor` while blind to both of the above, and joined into `01-knowledge-provenance.md` in Phase 1d (contradictions become `disputed` rows).

### Default anchor routing

Reviewers Grep or read only the anchors relevant to their dimension from `.team-review/02-interconnect.md` (see `references/panel-and-critic-prompts.md` for the context-aware spawn template):

| Reviewer dimension | Primary anchors in interconnect map |
|---|---|
| security | `## Integration Hot-Spots` (inbound), `## Assumptions` (unverified), `## Contracts` (implicit, input validation) |
| architecture (code-auditor) | `## Invariants`, `## Contracts` (structural + implicit), `## Call Graph` |
| logic-integrity | `## Contracts` (implicit, unverified), `## Invariants`, `## Assumptions` (unverified), `## Domain Rules` |
| distributed-flows | `## Integration Hot-Spots` (HTTP / queue / IPC), `## Call Graph` (cross-service) |
| chicken-egg | `## Assumptions` (initialization order), `## Integration Hot-Spots` (Env / config), `## Invariants` (cross-component) |
| ui-races | `## Invariants` (temporal), `## Integration Hot-Spots` (UI state) |
| temporal-resilience | `## Invariants` (temporal, liveness), `## Assumptions` (unverified, timing/retry), `## Integration Hot-Spots` (queues, timers, network loops) |
| data-integrity | `## Invariants` (uniqueness, state exclusivity, balances), `## Contracts` (structural, persistence shapes), `## Assumptions` (unverified, isolation/consistency) |
| resource-lifecycle | `## Assumptions` (pool bounds, connection reuse), `## Integration Hot-Spots` (connections, subprocesses, long-lived handles) |
| api-contracts | `## Contracts` (formal) -> `senior-review:api-contract-auditor` |
| structural entropy (diff mode) | none (reads `$XRAY_RUN_DIR/01-structure.md` + `02-interfaces.md` + concept index) |

### Metrics

**Map utilization rate** (operational, not a quality signal): fraction of findings citing an interconnect anchor. Do not set a target for it.

Quality signals:
- **Independent premise reconstruction rate**: fraction of findings whose load-bearing premise was obtained without exposure to that premise (Phase 1c Premise Auditor or independent reviewer re-derivation; **Lens 0 does not count** because Mode 2 is primed).
- **Premise challenge rate**: fraction of eligible premises (`shared-context`, `mixed`, or universal/negative quantifier) attacked by Lens 0.
- **Map challenge rate**: fraction of consumed map rows explicitly tested rather than assumed.
- **Map gap rate**: `[MAP-GAP]` findings over total findings.
- **Cross-source corroboration rate**: diagnostic over findings corroborated across code, tests, and docs.

### Fallback: raw mode (`--no-context`)

When `--no-context` is set, reviewers receive only target + diff: `logic-integrity-auditor`, `premise-auditor`, Phase 0c, and Lens 0 do not run; all findings are `independent` by construction; no `.codebase-map/`, `$XRAY_RUN_DIR`, or `.team-review/02-interconnect.md` references appear in reviewer prompts.

## Reviewer Pipeline Conventions

Every Phase 2 reviewer carries four rules in its system prompt:
- **Scope budget**: stop after ~15 file reads without a finding and return a "scope-off-topic" report.
- **No-findings protocol**: "examined X, Y, Z: no issues" is a valid Phase 3 input, not a failure.
- **Cross-Reviewer Notes**: observations belonging to other dimensions go in `## Cross-Reviewer Notes` for Phase 3 routing.
- **Interconnect anchor citation**: reviewers cite map anchors when applicable. Findings that cite map anchors feed the map utilization rate, an operational measure of map consumption, not a quality signal. See `### Metrics` for the quality signals that actually matter.

## Evidence Classes for Quantitative Claims

Any finding quantifying damage (N times/day, GB transferred, $/month, req/s) must label the number:
- **`measured`**: obtained from a harness, simulation, reproduction, or real logs/metrics (state method in one line; build any harness outside the work tree and delete afterwards).
- **`derived`**: computed by reading code (a hypothesis, not a fact; unlabeled quantitative claims default to `derived`).

Consequences:
1. A `derived` number alone cannot justify **Critical** severity (measure it or cap at High).
2. A finding cannot be closed as acceptable ("bounded", "low traffic") on a `derived` number alone, nor without answering **what the user or operator sees, and when** ("None (silent)" is a severity escalator, never a mitigation).
3. Lens 2 actively checks whether claimed rates/costs survive actual control flow (deduplication, caps, phase transitions).

## Adversarial Verification Panel

Each deduplicated finding selected for verification is judged by up to 4 verifiers (`references/panel-and-critic-prompts.md` Section 2). Dispatch one isolated worker per lens per finding through the consuming workflow's host harness. Lens 0 uses the declared `senior-review:premise-auditor` binding; lenses 1-3 use only the declared `project-protocol:isolated-worker` binding with the lens-specific briefs in `references/panel-and-critic-prompts.md`. Every brief carries the owned scope, authorization, budget, declared inputs and expected report path. Record each delivered or failed outcome in the same delivery ledger. Independent lenses receive no peer findings before their delivery. All lenses inherit the session model by default; apply a supported model override only when explicitly requested by the user and bound by the host harness, never by choosing a host-specific alias here.

### Lens gating and Lens 0 resolution

1. **Lens 0 (Premise Challenge, Mode 2 of `senior-review:premise-auditor`) runs first**, gated on `premise_provenance` (`shared-context` or `mixed`, or missing when pipeline ran) **or** any declared premise containing a universal/negative quantifier (`no`, `never`, `cannot`, `always`, `only`).
   - `REFUTED` (`PREMISE`), or `REFUTED` (`SUPPORT` + `shared-context`): finding discarded (`filtered: premise-refuted`), lenses 1-2 not spawned.
   - `REFUTED` (`SUPPORT` + `mixed`): strike the shared leg, restate from independent evidence, run lenses 1-2.
   - `UNCERTAIN` (including Lens 0 errors or `REFUTED` without `file:line`): proceeds to lenses 1-2 tagged `premise-contested`.
   - `HOLDS`: proceeds to lenses 1-2 unchanged.
   - `premise_form: non-compliant` is recorded in the verification file regardless of verdict.
2. **Lenses 1 (Reachability) and 2 (False-Positive Causes)** run independently on findings surviving Lens 0:
   - **>= 2 REAL**: finding survives.
   - **>= 2 FALSE_POSITIVE**: finding discarded (`filtered`, count reported).
   - **Tie (1 REAL / 1 FALSE_POSITIVE) or < 2 valid verdicts**: finding survives marked `contested` (fail-open).
3. **Lens 3 (Severity Calibration)** is gated and runs only on findings that survive Lenses 1-2. Final severity is Lens 3's `severity_vote` when confirmed real, else the original reviewer severity.

### Selection and Cost Guard

- **Normal (default-on):** every deduplicated finding with confidence `>= 50%`.
- **Under cost guard (> 25 surviving findings and `--rigorous` not set):** verify all Critical/High findings plus Medium/Low in the 50-75% confidence band or with conflicting reviewer severities; pass the rest through tagged `unverified (cost-guard)` and declare the narrowing (the threshold of 25 surviving findings is a finding-count proxy for token spend).
- **`--rigorous`:** verify all findings above the floor. **`--fast`:** skip panel and critic.

## Completeness Critic

After verification, one isolated `project-protocol:isolated-worker` critic uses the consuming workflow's host binding and the prompt in `references/panel-and-critic-prompts.md` (Section 3) to emit `## Coverage Gaps` across five categories:
1. **Dimensions not run** warranted by scope
2. **Files in scope cited by no reviewer**
3. **Unverified assumptions** in the interconnect map unaddressed by findings
4. **High-risk hot-spots** (`05-risks.md` or Integration Hot-Spots) with zero findings
5. **Findings closed on metrics alone** without stating user-visible consequences or with `derived`-only numbers

If the critic identifies a high-risk uncovered area (and cost guard / `--fast` is not active), spawn **one** targeted reviewer for a **single** follow-up round; its findings pass through deduplication and the verification panel.

## Delivery Gate

1. **Every reviewer delivers or declares:** Consolidation does not start until every spawned reviewer has produced either its findings file or an explicit no-findings report. An idle reviewer receives one nudge; if still silent, salvage partial output as `[undelivered -- collected by orchestrator]` and mark the dimension **degraded** (or **not delivered** if empty), never clean.
2. **The work tree is left as found:** Compare the complete pre-review workspace snapshot with the final state. A new file in status is not proof the review owns it. Workers keep an explicit manifest of files they created, with original absence and final hashes; foreign or changed files are preserved and reported. Keep probes inside the owned run root. Before removing an unchanged owned temporary artifact, preserve its conditions, commands, outcomes, errors and limitations in the native report and verify every remaining evidence reference still resolves. Preserve unresolved evidence and resume data. Broad cleanup or Git clean is forbidden. Persistent run retention belongs to the caller's consolidate path; the review returns the owned manifest and report, rather than deleting arbitrary repository residue on status alone.
