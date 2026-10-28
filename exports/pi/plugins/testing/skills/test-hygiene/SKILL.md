---
name: test-hygiene
description: >
  Rules for writing, placing and judging tests, and the remediation ladder they feed. A rulebook that test writers, auditors and the maintenance method load; it does not maintain a suite.
  TRIGGER WHEN: creating or placing test files, deciding whether to extend an existing test or add a new file, or judging test-suite structure against the rules.
  DO NOT TRIGGER WHEN: a user asks to clean up, consolidate or reduce an existing suite (start /daodan:maintain-tests, whose method loads these rules), TDD workflow mechanics (use mattpocock-skills:tdd) or browser E2E page objects/waiting (use developer-essentials:e2e-testing-patterns).
---

<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
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

# Test-Suite Hygiene

Rules and workflows that keep a test suite small, trustworthy, and navigable while agents and humans keep adding to it.

## Why suites degrade under agentic coding

For an agent, writing a new test file costs nearly nothing; understanding the existing suite costs context. The dominant strategy becomes "create a new one", and the implicit goal is "task closed, CI green", never "suite healthy". Nobody measures suite health, so nobody optimizes it. The result compounds fast: parallel test files for the same module, the same behavior asserted at three layers, implementation-coupled tests that break on every refactor and get replaced instead of repaired, and skip markers that quietly turn the safety net into decoration. These rules exist to make the healthy move the cheap move.

## The binding rules

For new or changed behavior, identify the introduced failure modes and the smallest
meaningful checks that protect them. Reuse sufficient existing protection; extend
it where needed. Trivial changes need no ceremonial test. Report unverified
behavior and remaining risk.

Test ownership: source at unit; behavior at integration, contract and e2e.

Full protocol with per-rule detail in `references/prevention-rules.md`. The condensed form:

1. **Review before adding.** Locate and read the existing owner for the intended layer and behavioral scope. Map protection before adding any case: reuse, update or justify the gap. Zero additions is valid. A parallel file requires a justified scope split.
2. **Deterministic ownership per layer.** Unit tests: one primary test file per source file, mirroring the source path (`src/foo/bar.py` maps to `tests/unit/foo/test_bar.py`), following the project's established convention and documenting justified scope splits. Integration, contract, and e2e tests are behavior-owned: one primary file per behavioral scope (a flow, an endpoint, a contract), legitimately spanning several source modules. The violation at those layers is an unexplained second file for the same scope, not multi-module reach.
3. **Explicit layers** (unit, integration, contract, e2e) with runtime budgets, identified through the project's directories, colocated paths or runner markers. A new test goes in the lowest layer that can prove its contract without hiding the relevant boundary.
4. **Behavior through justified interfaces.** Prefer observable contracts. Internal access, boundary doubles and ordering checks require a named boundary or diagnostic regression; inspect their purpose before rewriting them.
5. **No skip markers to get green.** Classify product, oracle, environment and intermittent failures before repair or accepted temporary quarantine. A tracked reason alone does not justify losing regression protection.

Assertion protection: Preserve assertions for approved behavior; correct a wrong oracle only with independent authority and evidence, while keeping valid product protection active.

Test retirement: Retire tests only for retired behavior or verified equivalent replacement protection in the same candidate; counts, coverage, age and refactoring alone are insufficient.

Refactors, renames and migrations preserve and retarget meaningful protection.
Resource-dependent tests follow the isolation and reproduction checklist in
`references/prevention-rules.md`, rule 9.

## The remediation ladder

When the suite has already degraded, rules alone do not repair it. Bonify in layers, opportunistically, alongside normal development. Full mechanics in `references/remediation-workflow.md`.

1. **Measure first.** The audit mode of `testing:test-remediation-method` produces a versioned `TEST_AUDIT.md`: counts, runtime, skipped, failing, flaky, orphans, layer distribution, slowest tests, per-module coverage. Metrics guide investigation; they do not establish behavioral value or correctness.
2. **Classify before quarantine.** Load the `testing:test-remediation-method` skill: product defects, wrong oracles, environment failures, intermittence and unknown causes have different owners. Temporary quarantine has explicit evidence, remaining risk, return condition and owner; a green suite alone does not become trustworthy.
3. **Consolidate per module.** Inventory protected behavior, independent failure modes and bugfix provenance before rewrite. Accepted replacements and removal share one candidate and authorized commit.
4. **Verify.** Every protected inventory row maps to a justified surviving check. Coverage and counts support the assessment but cannot prove equivalence.

Order remediation by risk (production bugs, then churn from git log), not by how messy a module looks.

## Layer model and budgets

Defaults; a project's own convention overrides them.

| Layer | Contains | Budget (default) |
|---|---|---|
| `unit` | Isolated behavior, controlled doubles at justified boundaries, no real external I/O | Individual test under 100ms; whole layer under 60s |
| `integration` | Real boundaries (DB, HTTP, filesystem) via containers or fixtures | Whole layer under 5min |
| `e2e` | Critical user flows only | Project-defined runtime budget; justified critical flows and failure modes, no test quota |

A behavior's primary proof lives at ONE layer. Cross-layer overlap is duplication only when two tests protect substantially the same failure mode through the same observable contract without adding independent risk coverage; a calculation checked at unit, its persistence at integration, and the user flow at e2e are three behaviors, not one repeated. A test that crosses a real database boundary belongs in integration. A controlled database-port double can isolate service behavior at unit, but cannot prove SQL, transactions or persistence; those contracts require the real boundary in an appropriate test lane.

## Related knowledge

Source revisions, license notices and delegation boundaries are indexed in
`references/upstream.md`; read it for provenance or integration maintenance.

Required upstream skills need a capability preflight on the active host: resolve
and load the actual installed skill before accepting an action that needs it.
Dependency metadata and five-host rendering do not establish that an external
marketplace runs on all five hosts. If unavailable, record the affected action
open and give the current host's supported installation guidance; do not substitute
another prompt or claim the upstream method ran. Claude-specific install examples
below apply only on that host.

- Writing the test content (red-to-green workflow, behavior-first design, mocking discipline): load the `mattpocock-skills:tdd` skill. It ships in the upstream mattpocock/skills plugin, a hard dependency of this plugin; if it is unavailable, stop and tell the user to install it (`claude plugin marketplace add mattpocock/skills`, then `claude plugin install mattpocock-skills@mattpocock`).
- Browser E2E patterns (page objects, fixtures, waiting, network mocking): load the `developer-essentials:e2e-testing-patterns` skill. It ships in the upstream wshobson/agents marketplace, a hard dependency of this plugin; if it is unavailable, stop and tell the user to install it (`claude plugin marketplace add wshobson/agents`, then `claude plugin install developer-essentials@claude-code-workflows`).
- Runner detection and measurement commands for the audit workflows: `references/runner-playbook.md`.
