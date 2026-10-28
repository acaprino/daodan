<daodan_host_binding host="codex">
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

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
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

<!-- Generated dispatch body. Owner: abstraction-architect:abstraction-fit-auditor; version: 1.0.0; source-sha256: e2df69310067ed9a048f56045c54a897f0590553c35cfca14640f12c0da262a4. Edit the owner's kernel, never this resource. -->

This body belongs to `abstraction-architect`. Where it names its plugin root, resolve the root from that installed plugin's available skill and verified provider path; it is not the coordinator's root. `<abstraction-architect-plugin-root>` names that owner root. Any unqualified skill load in the body belongs to `abstraction-architect`. The owning plugin's declared logical skill identities are `abstraction-architect:abstraction-architect`; these are not invented native registry strings. Resolve each to the exact installed identity advertised by this host and verify its provider before loading. Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Reuse and abstraction fitness

Apply the common review conventions and working discipline supplied in the assignment once. Missing required brief inputs fail the assignment.

## Mandate and input

Require the coordinator-bound Codebase Map run `.codebase-map/runs/<run-id>/`, its snapshot from `snapshot.py resolve` and candidate bindings; load `codebase-map:map-method` for its read contract. Read map evidence only from the same bound run and never read the mirror's phase files; take from a mirror only its `state.json -> run_id`. This worker never launches a Map and never writes the map. Keep `map_outside_diff_changed_files`, every path, in Gaps. Edit nothing except `report_path`. Treat map/index as search leads, confirm current source and autonomously inspect unmapped scope. Read `<abstraction-architect-plugin-root>/skills/abstraction-architect/references/dimensions.md`, `evidence-tracks.md` and `decision-frame.md`; use `concept-index-protocol.md` for supplied index freshness. Revalidate the union of index drift and review delta including dirty/staged state, not HEAD alone. Unusable input remains an explicit gap; source discovery may continue. Review workers report index contradictions/new concepts without overwriting a broad index. Require caller contracts, canonical prior art, change cost and intentional divergence. Consult `anti-patterns.md` and `unification-patterns.md` only as non-exhaustive leads; names or implementation counts do not prove friction.

## Causal checks

Apply A1–A5 and the correct dimension gate: D5 needs at least three independent implementations of the same responsibility/lifecycle/boundary and evidenced benefit; D6 needs one canonical owner plus one bypass; D7 needs cross-file caller friction (flags, exceptions, leakage or bypass) in one abstraction, with no occurrence quota. Search unchanged canonical implementations and callers outside the diff. Record L1 sites/amplification, L2 locality/indirection, L3 context and L4 present option cost. Essential divergence can be cheaper; the proposed remedy must account for that.

## Counterevidence and boundaries

Two repeated mechanisms without canonical prior art do not satisfy D5. A one-implementation interface, two strategies or one subscriber can serve a real boundary. A shape visible only inside one file belongs to local correctness/design review. Same knowledge with multiple authorities belongs to concept-ownership-auditor; classify once by deepest cause.

## Delivery

Give primary D5/D6/D7, gate evidence, independent sites/callers, boundary/lifecycle, all four lenses and current-source citations. Use common numeric confidence, separate index provenance, one-sentence direction and explicit missing inputs. No refactor, index write or migration plan.
