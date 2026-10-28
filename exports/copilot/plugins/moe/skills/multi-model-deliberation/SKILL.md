---
name: multi-model-deliberation
description: >
  Coordinates bounded independent proposals and reciprocal critique.
  TRIGGER WHEN: /daodan:get-second-opinion receives a question rather than a file, or explicitly requesting Ultra Nerd, moe, or a multi-model expert debate for a difficult problem.
  DO NOT TRIGGER WHEN: challenging an existing plan only (use peer-review:cross-model-peer-review).
---

> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.
> This plugin declares an MCP server, `moe`, started with `uv run --no-config --no-project --script ${PLUGIN_ROOT}/skills/multi-model-deliberation/scripts/server.py`. This host does not start a plugin-declared MCP server on its own. Before calling this server's tools, register that command under that name in the host's MCP configuration and verify the connection.

<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

# Multi-model deliberation

Execute a deliberation with `references/deliberation.md`. This skill supplies the method;
the `moe` MCP server owns run-directory creation (`.moe/<run-id>/`), payload composition,
identity pinning and `exchange.json` state, while the active harness owns transport
admission, accounting and cancellation.

Load the `peer-review:cross-model-peer-review` skill for its independence and safety
doctrines. Use the `moe` MCP server (`moe_models`, `moe_ask`); do not call `peer_ask`
and do not claim peer-review certification.

## How it works

1. **Freeze the brief (≤ 6000 UTF-8 bytes):** state the problem, constraints, evidence
   locators and success criteria. Discover two distinct models via `moe_models` and
   obtain or confirm user consent for the higher token/latency cost.
2. **Round 1 — Independent proposals:**
   - Call `moe_ask(model=model_a, phase="proposal", brief=brief_text)`. The MCP server
     automatically creates `<run_root>/<run_id>/`, writes `brief.md` and `exchange.json`,
     and returns `run_id` alongside the first proposal.
   - Call `moe_ask(model=model_b, phase="proposal", run_id=run_id)`. The MCP server
     reuses `brief.md`, pins `peer_model` to the first returned identity, rejects
     model collisions, and records the second proposal.
3. **Round 2 — Reciprocal critiques (and optional Round 3):**
   - Call `moe_ask(model=model_a, phase="critique", run_id=run_id)` and
     `moe_ask(model=model_b, phase="critique", run_id=run_id)`. The MCP server
     automatically composes each reciprocal payload from `brief.md` and both previous
     replies, pins `expected_model` and `peer_model`, and updates `exchange.json`.
4. **Verify and synthesize:** check decisive claims against the actual repository or
   available evidence, write `<run_root>/<run_id>/answer.md`, and deliver the synthesized
   recommendation with model identities, completed rounds and observed usage.

## Load map

| Need | Reference |
|---|---|
| Running a deliberation on a question (`/daodan:get-second-opinion`, or an explicit Ultra Nerd or moe request): preparation, managed `moe_ask` calls, failure codes and synthesis | `references/deliberation.md` |
