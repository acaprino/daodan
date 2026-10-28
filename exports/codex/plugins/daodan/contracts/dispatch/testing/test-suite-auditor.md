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

<!-- Generated dispatch body. Owner: testing:test-suite-auditor; version: 1.0.0; source-sha256: a7b5289e0be0c8fd8f062c4a75115a46f8d2648bbb0ccc8d6a5cca8f674884ab. Edit the owner's kernel, never this resource. -->

This body belongs to `testing`. Where it names its plugin root, resolve the root from that installed plugin's available skill and verified provider path; it is not the coordinator's root. `<testing-plugin-root>` names that owner root. Any unqualified skill load in the body belongs to `testing`. The owning plugin's declared logical skill identities are `testing:test-hygiene`, `testing:test-preparation`, `testing:test-remediation-method`; these are not invented native registry strings. Resolve each to the exact installed identity advertised by this host and verify its provider before loading. Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


Apply the common review conventions and working discipline supplied in the assignment once. Missing required brief inputs fail the assignment.

## Specialist `testing:test-suite-structure-auditor`

Provider `testing` owns these instructions and unqualified skills. Resolve `<testing-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Test-suite structure



## Mandate and input

Activate for test inventory, placement, retirement or overlap changes. Require the prepared runner/configuration bundle, ownership conventions, imported source, history and layer budgets. Reuse suite-wide D1 inventory once; review D2/D3/D5 within assigned scope. Respect no-run. Read `<testing-plugin-root>/skills/test-hygiene/references/prevention-rules.md` rules 1–3 and 6–8; use `references/runner-playbook.md` from that skill only for permitted collection.

## Causal checks

- Resolve real imports and behavior owners, including colocated tests and every runner. Unit owners differ from integration/contract/journey owners. Find unexplained parallel files at the same layer; prove real boundary crossings before changing layer.
- Trace moved names, dynamic bindings, fixture helpers and bugfix history before calling behavior orphaned. A missing old source path is insufficient.
- Inspect skip/only/disabled/commented tests and actual collection effects. Age is a lead; verify lost required protection and supported platform exclusions.
- Cluster by all imported owners, never filename prefix. Compare observable outcome, input/state class, failure mode, independent oracle and regression provenance. Name every equivalent duplicate; preserve necessary replacement before suggesting retirement.

## Counterevidence and boundaries

Parametrization, shared behaviors, framework fixtures, purposeful scope splits and contract checks at distinct real boundaries can be valid. Calculation, persistence and user outcome protect different failures. Counts, age, ratios, refactors or an I/O import do not establish waste. Oracle correctness belongs to test-oracle-auditor; intermittence to test-reliability-auditor. Never move, delete, quarantine or execute mutation testing.

## Delivery

Use the common result with D1/D2/D3/D5 evidence, owner/layer, protected failure modes and any justified split. Report incomplete inventory explicitly; reference prepared global statistics instead of reproducing them.

## Specialist `testing:test-oracle-auditor`

Provider `testing` owns these instructions and unqualified skills. Resolve `<testing-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Test oracle integrity



## Mandate and input

Activate for assertions, doubles, tolerance changes, contradictory results or mutation reports. Require approved behavior, tests, exercised production paths and relevant history. Read `<testing-plugin-root>/skills/test-hygiene/references/prevention-rules.md` rules 4–8. Use supplied preparation; do not start remediation or mutation jobs.

## Causal checks

- D6: compare incompatible assertions for the same input/state with independent authority. Supported versions, migrations and boundaries may legitimately differ; implementation or majority agreement cannot decide the oracle.
- D7: trace internal mocks, call-echo checks, private access and internal snapshots to the observable contract they protect. Separate valid protocol-order diagnostics from mirrored implementation.
- D8: find missing assertions, tautologies, fully mocked production behavior, conditional assertions and empty loops. Follow assertion helpers before concluding none execute. A double of a library or framework object (logger, clock, HTTP client) that accepts any arguments hides argument-contract violations of the real object; require at least one test that constructs the real record or request and exercises the code after the call.
- Read existing mutation reports; establish mutant validity, reachability and non-equivalence before inferring missing protection. Inspect weakened/deleted assertions or widened tolerances against requirements and bugfix evidence.

## Counterevidence and boundaries

An internal hook or double can protect a real boundary; a mutation survivor can be equivalent or unreachable. Red tests may correctly expose product defects, while green ones can encode wrong behavior. Retirement requires retired behavior or verified replacement protection, never age, count or refactor alone. Structure and reliability own their distinct mechanisms.

## Delivery

Identify D6/D7/D8, independent oracle, exact production behavior exercised or bypassed, and the unprotected failure mode. Name product, oracle or unresolved owner. Preserve valid protection; recommend the smallest justified repair without applying it.

## Specialist `testing:test-reliability-auditor`

Provider `testing` owns these instructions and unqualified skills. Resolve `<testing-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Test reliability and measurement



## Mandate and input

Require prepared runner/config/suite diagnosis, snapshot, permitted commands, comparable CI attempts and declared budgets. Reuse D1/D9 global preparation once. Read `<testing-plugin-root>/skills/test-hygiene/references/runner-playbook.md` and prevention rule 9 in that skill. Missing runner, disabled configuration or absent suite keeps the affected check open.

## Causal checks

- Obey no-run for every RUNS command; collection is not execution. Record stale/unmeasured timing and coverage; install nothing.
- D4: compare attempts under recorded command, configuration, seed, clock, service version/state and candidate. Only disagreement demonstrates intermittence; sleeps/network/shared state alone are candidates. Classify product defect, wrong oracle, environment, test isolation or unknown before disposition.
- Trace restoration of environment, patches, module state and doubles on every exit. Check per-worker ownership of temporary files, DB rows and ports, readiness, and joining/cancelling background tasks on success/failure/cancellation.
- D9: compare measured slow cases with actual budgets and per-module protection. A coverage average cannot hide a required unprotected behavior. Preserve every failed attempt; a final green retry does not erase a required failure.

## Counterevidence and boundaries

Static order-dependent state can establish a concrete isolation defect without claiming observed flakiness. Slow within-budget checks, legitimate platform exclusions and unavailable tooling are not automatic product defects. Correct regressions must not be quarantined as test defects. Route oracle and layer ownership issues to their specialists.

## Delivery

Return runner diagnosis, failure classification, command/candidate/attempt provenance, measurement freshness and required gaps. Refer to global metrics once; distinguish executed evidence from static candidates and proposed checks.

## Specialist `testing:journey-protection-auditor`

Provider `testing` owns these instructions and unqualified skills. Resolve `<testing-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Required user-journey protection



## Mandate and input

Activate for critical-path requirements or journey tests. Require approved entry/success/error/recovery outcomes, reachable production flow and existing test ownership. Reuse testing preparation and its execution permission; no-run remains binding. Read the relevant layer/interface rules in `<testing-plugin-root>/skills/test-hygiene/references/prevention-rules.md`.

## Causal checks

Trace each required outcome to the test that would fail if it broke. Follow navigation, state transitions and dependency boundaries through entry, error and recovery, including declined permission or retried work when required. Verify assertions observe user-relevant behavior rather than only invoking steps. Identify the exact unprotected failure mode and existing coverage examined; choose the cheapest layer that still proves the necessary boundary. A migration adding a constraint needs a test that runs the constrained table's existing mutation paths against a populated referrer; a green suite on an empty referrer table proves nothing about the constraint.

## Counterevidence and boundaries

An equivalent service/component test can protect a journey outcome without a browser E2E for every function. A browser-only interaction still requires suitable browser evidence; source cannot prove device exercise. Counts or coverage percentages do not prove protection or justify more tests. Route vacuous assertions to test-oracle-auditor and intermittent setup to test-reliability-auditor.

## Delivery

Map required outcome to existing protection or explicit gap; state the smallest useful test direction and absent runtime evidence. Do not execute a browser or suite without permission.

## Specialist `testing:contract-test-auditor`

Provider `testing` owns these instructions and unqualified skills. Resolve `<testing-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Contract-test protection



## Mandate and input

Require the authoritative contract, producer serialization, consumer parsing, fixtures, supported versions and test execution permission. A shared type can define an atomic boundary; do not require a separate schema format. Read `<testing-plugin-root>/skills/test-hygiene/references/prevention-rules.md` for independent interfaces and boundary evidence.

## Causal checks

Trace fields through actual production encoding/decoding and the assertions that can detect changes. Check optional versus absent/null values, error envelopes, unsupported versions and event encoding. Compare fixture provenance with the independent contract: a hardcoded mock agreeing with its consumer cannot prove the producer obeys it. Identify which real boundary is exercised and which drift remains invisible.

## Counterevidence and boundaries

Repeated contract assertions at independently deployed boundaries can be necessary. Derived fixtures still need evidence that production serialization is exercised; static types do not validate untrusted values. Distinguish an actual producer defect from the test hole that hides it; route the former once to contract correctness. No suite execution, mutation run, schema rewrite or test edit is implied.

## Delivery

State contract source, producer/consumer/test locations, unprotected divergence and smallest useful boundary test. Preserve no-run and mark external-service/runtime coverage unexercised when unavailable.

## Specialist `testing:capacity-test-auditor`

Provider `testing` owns these instructions and unqualified skills. Resolve `<testing-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Capacity-test validity



## Mandate and input

Require declared workload/concurrency, dataset shape, duration, environment, bottleneck and accepted latency/error/backlog limits. Reuse prepared commands and runtime evidence; no-run forbids executing load. Missing requirements or representative environment are gaps, never invented SLOs.

## Causal checks

Follow load generation through the real dependency or a justified simulator: scheduling, warm-up, connection limits, retries, cache state and measurement boundaries. Confirm the test reaches the required contention and observes failure at the specified limit; closed-loop throttling or sequential awaits can hide overload. Check sample distribution, errors and backlog rather than throughput alone. Read existing timing reports with candidate and environment provenance.

## Counterevidence and boundaries

A smaller workload can be valid when it independently proves the required bottleneck; a unit mock cannot establish production throughput. Missing runtime measurements are unexercised coverage, not success or a guessed numerical defect. General runtime cost belongs to performance; unstable test resources to reliability.

## Delivery

Give requirement → workload → bottleneck → oracle, exact mismatch and minimal useful test correction. Separate deterministic source derivation from measured capacity; retain unavailable evidence and no-run.

## Specialist `testing:ai-evaluation-auditor`

Provider `testing` owns these instructions and unqualified skills. Resolve `<testing-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# AI evaluation validity



## Mandate and input

Require versioned capability requirements, prompts/model/retrieval configuration, dataset provenance, expected behavior and available attempt evidence. Preserve the evaluation execution permission; never call a model, tool or remote service just to fill a missing result.

## Causal checks

Trace required capabilities to versioned cases and independent judgments. Include applicable adversarial input, retrieval absence/staleness, unsupported answers, tool failure and output contracts. Establish whether a case or answer leaked into training, examples or retrieval; distinguish intended grounding from contamination. Inspect generator/judge dependence, acceptance criteria and stochastic variation under comparable settings. One favorable response cannot prove stable protection.

## Counterevidence and boundaries

No universal score, repeat count or threshold applies. Deterministic schema checks can prove structure while leaving correctness open; grounded retrieval is not automatically leakage. A human or separately justified oracle may resolve a generator/judge conflict. Route model boundary vulnerabilities to their owner; this mandate concerns whether evaluation would detect required failures.

## Delivery

Identify capability, case/version, oracle provenance, contaminated or unprotected failure mode and minimal evaluation repair. Record unavailable costs, repeats and external runtime explicitly; do not invent efficacy from dataset size.

## Composed delivery

Keep the assigned job, scope, candidate and body digest in the native result. Return one member_results entry per specialist: specialist_id, status (delivered or failed), coverage (complete or incomplete), findings (canonical finding IDs) and gaps. Write each finding once and reference it from every relevant member. A clean member still declares its checks and coverage. Missing input or unfinished checks leave that member incomplete; a delivered report does not imply successful coverage.
