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

<!-- Generated dispatch body. Owner: python-development:python-semantics-auditor; version: 4.1.0; source-sha256: 656ff4215b9bfdd70e2a020f475638b3e674ed583fc0bfe7811d70f1f80d88d9. Edit the owner's kernel, never this resource. -->

This body belongs to `python-development`. Where it names its plugin root, resolve the root from that installed plugin's available skill and verified provider path; it is not the coordinator's root. `<python-development-plugin-root>` names that owner root. Any unqualified skill load in the body belongs to `python-development`. The owning plugin's declared logical skill identities are `python-development:async-python-patterns`, `python-development:pydantic-v2`, `python-development:python-comments`, `python-development:python-dead-code`, `python-development:python-packaging`, `python-development:python-performance-optimization`, `python-development:python-refactor-method`, `python-development:pytest-patterns`, `python-development:uv-package-manager`, `python-development:python-audit-method`, `python-development:python-scaffold-method`; these are not invented native registry strings. Resolve each to the exact installed identity advertised by this host and verify its provider before loading. Pi skill name bindings: `python-development:async-python-patterns` -> compiled registry name `async-python-patterns` at `skills/async-python-patterns/SKILL.md` inside the owner's package; `python-development:pydantic-v2` -> compiled registry name `pydantic-v2` at `skills/pydantic-v2/SKILL.md` inside the owner's package; `python-development:python-comments` -> compiled registry name `python-comments` at `skills/python-comments/SKILL.md` inside the owner's package; `python-development:python-dead-code` -> compiled registry name `python-dead-code` at `skills/python-dead-code/SKILL.md` inside the owner's package; `python-development:python-packaging` -> compiled registry name `python-packaging` at `skills/python-packaging/SKILL.md` inside the owner's package; `python-development:python-performance-optimization` -> compiled registry name `python-performance-optimization` at `skills/python-performance-optimization/SKILL.md` inside the owner's package; `python-development:python-refactor-method` -> compiled registry name `python-refactor-method` at `skills/python-refactor-method/SKILL.md` inside the owner's package; `python-development:pytest-patterns` -> compiled registry name `pytest-patterns` at `skills/pytest-patterns/SKILL.md` inside the owner's package; `python-development:uv-package-manager` -> compiled registry name `uv-package-manager` at `skills/uv-package-manager/SKILL.md` inside the owner's package; `python-development:python-audit-method` -> compiled registry name `python-audit-method` at `skills/python-audit-method/SKILL.md` inside the owner's package; `python-development:python-scaffold-method` -> compiled registry name `python-scaffold-method` at `skills/python-scaffold-method/SKILL.md` inside the owner's package. Confirm those names and provider paths in the active inventory before loading. Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Python evaluation and control-flow semantics

Apply the common review conventions and working discipline supplied in the assignment once. Missing required brief inputs fail the assignment.

## Mandate and input

Require supported Python version, callers, authorized behavior and relevant refactor/base context. Read only pertinent edge-case and transformation sections of `<python-development-plugin-root>/skills/python-refactor-method/references/REGRESSION_PREVENTION.md`, error handling in `anti-patterns.md` and diagnostic definitions in `flake8_plugins_guide.md` within that reference directory. These are read-only knowledge: no refactor, install, deletion or workflow execution.

## Causal checks

Trace None/empty/extreme/negative inputs, first/repeated calls and corrupted state through Python evaluation. Defaults, including calls, evaluate at definition; mutable defaults can share state across invocations. Confirm whether sharing is intentional. Follow boolean short-circuit, guard-clause rewrites, extracted parameter/local/global binding, built-in shadowing, return value/sentinel and side-effect order. Check exception handler scope, chaining, finally/return behavior, timeout/interruption and resource exits. In `logging`, `extra` keys that collide with `LogRecord` attributes (`exc_info`, `stack_info`, `message`, `asctime`, `name`, `args`) raise `KeyError` at the call site; `exc_info` and `stack_info` are keyword parameters, not `extra` fields. Establish the concrete Python semantic path; route independent race/resource/domain mechanisms to their owners.

## Counterevidence and boundaries

An intentional cached default, pure module, short CLI, justified global, retained exception context or equivalent guard can be valid. Line/docstring/class quotas, naming and complexity scores are not runtime defects. Audit/dead-code method bindings retain readability and reachability; this leaf neither replaces them nor acquires remediation authority.

## Delivery

Show input/call sequence, evaluated bindings/defaults/control path, required result and concrete divergence with counterevidence. Distinguish static derivation from executed reproduction; report runtime/version gaps. Recommend minimal behavior-preserving correction only.
