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

# Decision Frame

What happens **after** a candidate has passed its dimension's gate: whether it is promoted, at what severity, and how the remediation is framed.

This file does not restate the gates. Track A gates `A1` to `A5` and track B gates `K1` to `K6` live in `references/evidence-tracks.md`, and duplicating them here would create two authorities over one rule, which is the D2 defect this plugin exists to find.

## Promotion

A candidate becomes a finding when all three hold:

1. **Its dimension's gate passed**, per `references/evidence-tracks.md`.
2. **Every cited representation has been read against current source.** A finding whose prior art you have not opened and compared is not reportable. Near-identical names routinely hide different behaviour, and an index entry is a search target rather than a proof.
3. **The lenses have been applied and recorded**, per `references/dimensions.md`. A lens does not veto, with one exception: an L2 verdict of "consolidating adds a hop and saves nothing" changes the suggested direction rather than the finding.

A candidate that fails any of the three is dropped. Silence is the correct output when the proof is not there.

## Severity calibration

Default to **Medium**. Escalate or de-escalate only when the evidence supports it. Reserve High for findings you can argue for in one paragraph. Reserve Low for smells with no concrete pressure.

**Severity follows consequence, never occurrence count.** There is no mapping of the form two equals Low, three equals Medium. Two independent authoritative permission policies can be High on two occurrences; four duplicated formatting constants can be Low on four.

- **High** when the finding creates:
  - **Security risk**: duplicated authorization rules, scattered token handling, an eligibility predicate that guards access and disagrees with itself, competing authorities over a permission fact.
  - **Data-correctness risk**: money arithmetic, rounding or pricing sequence, date and timezone handling, derivable state with repair code, two authorities over a value that reconciliation depends on.
  - **Operational risk**: incompatible retry or timeout policies on the same dependency, a status vocabulary that drifts between a producer and a consumer, a transition rule enforced in one path and not another.
- **Medium**, the default, when the finding creates maintenance drag: a mechanism repeated three times, a layer that is accumulating flags, a redundant representation with a real but bounded mapping cost. The cost is paid in change velocity, not in incidents.
- **Low** when the pattern is a smell with no concrete pressure. A stable strategy-for-two on a cold path. A second occurrence noted so the third is recognisable.

## Confidence

Severity says how much it matters. Confidence says how sure you are, and they are reported separately.

- **High confidence**: every cited representation was read on current source, and the dimension gate passed on evidence from more than one signal.
- **Medium confidence**: the gate passed but one input was unavailable, for example a missing Codebase Map file or an `unusable` concept index.
- **Low confidence**: a single signal, worth manual verification. Say what would raise it.

Two flags are mandatory when they apply, because they mark the failure modes that cost the most:

- **`Bounded-context exception: unverified`** when context membership could not be determined. On track B this remains an unresolved candidate in Gaps, not a finding at lower confidence or severity; K6 is a hard gate.
- **`Index-seeded: yes`** when a concept index entry pointed at the evidence. This is provenance, not a quality signal, and nothing in the report or in any consuming pipeline may reward it.

## Remediation framing

`Suggested direction` names the target layer or the move in one sentence. It is not a refactoring plan, a file list or a migration sequence.

Frame it with L4, the option price, when the recommendation is contested:

> The upfront cost of unifying these three sites is one module plus indirection at each call site. The future value is that a threshold change becomes one edit rather than three, and finance has changed it twice this year. Recommendation: unify.

Frame the reverse the same way. An abstraction whose expected value no longer covers its cost gets an inline recommendation, and the intermediate state is supposed to look worse than both endpoints.

Match the remediation to the dimension. This is the difference between an actionable finding and a shallow one:

| Dimension | The move |
|---|---|
| D1 | Give the knowledge one authoritative statement, then have the others call it |
| D2 | Name the canonical owner first. Extracting a helper before ownership is settled adds an authority |
| D3 | Collapse the representations, or document the boundary that justifies keeping them |
| D4 | Derive instead of storing, or make one copy authoritative and the other a cache with a stated invalidation rule |
| D5 | Design the shared mechanism |
| D6 | Migrate to the canonical implementation and delete the reimplementation |
| D7 | Inline the abstraction back to its call sites, then redesign from what they reveal |
