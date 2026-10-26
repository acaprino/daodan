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

# Testing upstream provenance

Intake inspected on 2026-10-26. Both providers are already required by
`testing/plugin.toml`. This record retains delegation and supplies provenance;
it does not import an upstream method or create a copied-source sync target.
The full retained license notices below belong to their respective authors;
Daodan's MIT license does not replace them.

## TDD: Matt Pocock

Repository: [mattpocock/skills](https://github.com/mattpocock/skills).
Inspected commit: `5beb35b040e3de97e54fa9e386d7e42d15c295c2`.
Read [`skills/engineering/tdd/SKILL.md`](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/tdd/SKILL.md),
its `tests.md` and `mocking.md`, and the repository's
[`LICENSE`](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/LICENSE).
License: MIT, Copyright (c) 2026 Matt Pocock. Retained unmodified in
`LICENSE-mattpocock-skills-MIT.txt` in this directory.
Notice SHA-256: `0e7ac423bf2c6e223b7c5b156f8cf72da49d748e56a1641402c31f22ad07dbb5`.

Required identity: `mattpocock-skills@mattpocock`; method:
`mattpocock-skills:tdd`. Its owner supplies the test-first loop and public-contract,
oracle and mocking guidance. The inspected method also consults its owner's
`codebase-design` knowledge when interface design needs it. Keep that provider
reference with its owner rather than inventing a local TDD method.

Daodan supplies its own inventory, placement, review of existing protection,
cause classification, scope acceptance and snapshot-bound gates. Preserve
justified real-boundary and diagnostic regressions: a test's internal access,
mock or ordering check requires inspecting its actual contract before disposal.
An accepted contract/boundary decision is reused; ask only for an unresolved
decision. Automated TDD returns observed red evidence to the implementation
owner; only explicitly selected interactive teaching waits for human code.

## Browser E2E: Seth Hobson

Repository: [wshobson/agents](https://github.com/wshobson/agents).
Inspected commit: `0874a27b17a22e2b7c2e2bcd725768e0803cad06`.
Read [`plugins/developer-essentials/skills/e2e-testing-patterns/SKILL.md`](https://github.com/wshobson/agents/blob/0874a27b17a22e2b7c2e2bcd725768e0803cad06/plugins/developer-essentials/skills/e2e-testing-patterns/SKILL.md)
and the repository's
[`LICENSE`](https://github.com/wshobson/agents/blob/0874a27b17a22e2b7c2e2bcd725768e0803cad06/LICENSE).
License: MIT, Copyright (c) 2024 Seth Hobson. Retained unmodified in
`LICENSE-wshobson-agents-MIT.txt` in this directory.
Notice SHA-256: `f89abb55d9f073f38f1703e4518f0613c788c6174be7f13b8dfe48a1c076c746`.

Required identity: `developer-essentials@claude-code-workflows`; method:
`developer-essentials:e2e-testing-patterns`. Its owner supplies browser-test
techniques and nested examples. Load those examples only when needed. Daodan
keeps independent failure-mode protection, real-boundary verification and
causal diagnosis before quarantine. No browser runner, dependency installation,
retry policy or mutation job is introduced by this intake.

## Availability and maintenance

On the active host, resolve and load the actual provider before its method is
needed. Dependency registration and generated packages do not establish that a
host can run the provider. Missing providers leave dependent actions open;
recover through that host's supported installation mechanism as specified by
`test-hygiene`. Keep independent static diagnosis available. The local Codex
catalog exposes both methods at intake; this is availability evidence, not an
installed-host execution probe for all five hosts.

Inspected source revisions are evidence references; provider installations
receive updates independently. Recheck their canonical sources and licenses
when refreshing this integration. No upstream implementation was modified or
copied; no copied-source sync row is added. The local TDD and E2E copies retired
in marketplace 18.0.0 remain retired. This reference and the two full notices
live under the skill so all five host packages ship them.
