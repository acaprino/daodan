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
selected reviewer first. Prompts: `references/panel-and-critic-prompts.md`.

## Adversarial Verification Panel

For each selected deduplicated finding, dispatch one isolated worker per lens
through the consuming workflow's host harness. Lens 0 uses declared
`senior-review:premise-auditor`; lenses 1-3 use only declared
`project-protocol:isolated-worker`, with Section 2's lens-specific briefs.
Include owned scope, authorization, budget, declared inputs and expected report
path. Ledger every delivered/failed outcome; no peer findings before independent
delivery. Inherit the session model; overrides require explicit user request and
supported host binding, never invented host-specific aliases.

### Lens gating and Lens 0 resolution

1. **Lens 0 (Premise Challenge, Mode 2 of `senior-review:premise-auditor`) runs first**, gated on `premise_provenance` (`shared-context` or `mixed`, or missing when pipeline ran) **or** any declared premise containing a universal/negative quantifier (`no`, `never`, `cannot`, `always`, `only`).
   - `REFUTED` (`PREMISE`), or `REFUTED` (`SUPPORT` + `shared-context`): finding discarded (`filtered: premise-refuted`), lenses 1-2 not spawned.
   - `REFUTED` (`SUPPORT` + `mixed`): strike the shared leg, restate from independent evidence, run lenses 1-2.
   - `UNCERTAIN` (including Lens 0 errors or `REFUTED` without `file:line`): proceeds to lenses 1-2 tagged `premise-contested`.
   - `HOLDS`: proceeds to lenses 1-2 unchanged.
   - `premise_form: non-compliant` is recorded in the verification file regardless of verdict.
   - **Absence claims too:** universal assurance over shared/multi-instance state
     receives Lens 0. Its premise is instance/path scope: verify multiplicity and
     alternate paths. `REFUTED` becomes a contested coverage gap naming the
     counterexample path, never an opposite defect without its own lenses 1-2.
2. **Lenses 1 (Reachability) and 2 (False-Positive Causes)** run independently on findings surviving Lens 0:
   - **>= 2 REAL**: finding survives.
   - **>= 2 FALSE_POSITIVE**: finding discarded (`filtered`, count reported).
   - **Tie (1 REAL / 1 FALSE_POSITIVE) or < 2 valid verdicts**: finding survives marked `contested` (fail-open).
3. **Lens 3 (Severity Calibration)** is gated and runs only on findings that survive Lenses 1-2. Final severity is Lens 3's `severity_vote` when confirmed real, else the original reviewer severity.

### Selection and Cost Guard

- **Normal (default-on):** every deduplicated finding with confidence `>= 50%`.
- **Cost guard (> 25 survivors without `--rigorous`):** verify Critical/High plus
  Medium/Low at 50-75% confidence or conflicting reviewer severities. Pass others
  through as `unverified (cost-guard)`; disclose narrowing. Finding count proxies
  token spend.
- **`--rigorous`:** verify all findings above the floor. **`--fast`:** skip panel and critic.

## Completeness Critic

After verification, one isolated `project-protocol:isolated-worker` critic uses the consuming workflow's host binding and the prompt in `references/panel-and-critic-prompts.md` (Section 3) to emit `## Coverage Gaps` across five categories:
1. **Dimensions not run** warranted by scope
2. **Files in scope cited by no reviewer**
3. **Unverified assumptions** in the interconnect map unaddressed by findings
4. **High-risk hot-spots** (`05-risks.md` or Integration Hot-Spots) with zero findings
5. **Findings closed on metrics alone** without stating user-visible consequences or with `derived`-only numbers

If the critic identifies a high-risk uncovered area (and cost guard / `--fast` is not active), spawn **one** targeted reviewer for a **single** follow-up round; its findings pass through deduplication and the verification panel.
