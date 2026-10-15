---
name: lifecycle-method
description: >
  Coordinate complete AI development work across code, tests, project knowledge and artifacts.
  TRIGGER WHEN: running project-lifecycle assess, repair, change, verify or consolidate, or explicitly taking responsibility for project coherence.
  DO NOT TRIGGER WHEN: an isolated specialist audit or a single factual answer is sufficient.
---

> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

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

# Project lifecycle

Own the requested outcome and its consequences. Keep the work proportional to risk,
scope and authorization. Load the project-protocol:project-protocol skill first; it owns run
records, snapshots, verification and recovery. This skill owns decisions and dispatch,
not a second set of specialist detection prompts.

## Entry and state

Inputs: operation, project root, objective and intention source; optional target,
focus, depth, run ID, plan ID, output root and prior evidence. Detect existing material
before proposing new files. Read project instructions and distinguish approved intent
from implemented behavior. Code alone cannot settle contradictory requirements.

Use the installed project-protocol run_state.py helper through that skill. Its CLI:
init --project ROOT --payload INPUT.json [--run-id ID] [--out INTERNAL_ROOT];
show or validate --project ROOT --run-id ID [--out INTERNAL_ROOT];
update --project ROOT --run-id ID --expected-revision N --payload PATCH.json;
resume --project ROOT --run-id ID --payload CONTEXT.json [--out INTERNAL_ROOT].
Payload files are run-owned inputs. Never guess a cache path to another plugin.

Initialization payload: operation, objective, scope {paths, focus}, authorizations,
budget, phases, plan, deliveries and required_gates. Preserve the helper's exact
project identity and snapshot. Save the authoritative work.json inside the run.
On resume, supply current authorizations and validate the exact run, workspace,
scope and snapshot. The latest completed Codebase Map or another session's report is not a
resume target.

Preview is the default for assess/repair/retention. --fix authorizes in-scope edits;
--commit additionally authorizes commits. Neither authorizes a push or permanent
artifact deletion by itself. Existing human authorization persists in its scope.
State missing permissions and actual design ambiguities against a concrete plan.

Default assessment depth is quick, one initial audit round, at most five selected workers
in total, including documentary workers from reused methods. Selection is a
budgeted coverage plan; a broad focus does not bypass that cap. Declare unexamined
dimensions and offer a larger explicitly selected depth when needed.
Before dispatch, show scope, selected dimensions, likely expensive steps and gaps.
--depth standard broadens evidence, --depth deep requests comprehensive work.
Prompt budgets are instructions; do not claim the host enforces tokens. Unknown
consumption is unknown. Reuse a delivery only when role version, input fingerprints,
scope and dependencies remain valid.

## Canonical methods

Load the selected skills before their operation: project-knowledge:project-knowledge,
project-knowledge:instructions-method and project-knowledge:readme-craft for knowledge;
senior-review:review-preparation and senior-review:review-consolidation for assessment
evidence; senior-review:review-method for candidate correctness review;
testing:test-preparation and testing:test-remediation-method for suite operations;
abstraction-architect:abstraction-architect for structural diagnosis;
Load the codebase-map:map-method skill for static context.
Load the repo-hygiene:repo-hygiene skill for workspace operations.
Load the clean-code:readability-method skill for readability. Load only methods required
by the requested scope, never a second detector prompt.

| Need | Load or dispatch |
|---|---|
| Static context and exact Codebase Map run binding | codebase-map:analyze preflight and delivery; codebase-map:map-analyst in an isolated context |
| Candidate correctness, including applicable stack specialists | senior-review:review-method |
| Assessment provenance consolidation | senior-review:review-preparation and senior-review:review-consolidation |
| Application subtraction | senior-review:application-cleanup-method |
| Suite preparation and remediation | testing:test-preparation and testing:test-remediation-method |
| Test authoring | testing:test-writer |
| Structural diagnosis | abstraction-architect:abstraction-architect and its auditor |
| Durable instructions | project-knowledge:instructions-method |
| Guide/documentation preparation, audit and apply | project-knowledge:project-knowledge |
| README | project-knowledge:readme-craft |
| Workspace detection and reversible application | repo-hygiene:repo-hygiene |
| Readability | clean-code:readability-method |
| General development planning/execution | superpowers:brainstorming, superpowers:writing-plans, superpowers:executing-plans or superpowers:subagent-driven-development |

For Codebase Map, execute the canonical analyze entry's preflight, answerable
checkpoints, delivery check and publication decision here. Dispatch
`codebase-map:map-analyst` through the consuming workflow's declared host harness
in one isolated context for the phases. Bind the returned run and snapshot;
loading the role as a skill executes no analysis. Do not recursively launch
lifecycle workflows or pretend TOML invoke executes a workflow. Load the
operation reference below; perform its coordinating methods in this context.

## Operation references

- assess: read ${PLUGIN_ROOT}/skills/lifecycle-method/references/assess.md.
- repair: read ${PLUGIN_ROOT}/skills/lifecycle-method/references/repair.md.
- change: read ${PLUGIN_ROOT}/skills/lifecycle-method/references/change.md.
- verify: read ${PLUGIN_ROOT}/skills/lifecycle-method/references/verify.md.
- consolidate: read ${PLUGIN_ROOT}/skills/lifecycle-method/references/consolidate.md.
- Native report conversion: read ${PLUGIN_ROOT}/skills/lifecycle-method/references/native-reports.md.

## Delivery and closure

Keep raw specialist payloads, role/version/input/output hashes, scope, status,
evidence and declared gaps. Schema-valid means structurally valid. Missing evidence
does not become an empty no-findings result. Missing delivery remains missing.
Use native_reports.py to wrap payload provenance; it does not validate their meaning.

Each plan action identifies finding IDs, disposition (retain, correct, merge, retire
or clarify), owner, canonical method, prerequisites, authorization, target paths and
gate. Native seven-way workspace dispositions remain present. Deduplicate by
behavior/concept, retain contradictions, and distinguish corroboration from shared
premise echo. Two reviewers with one inherited premise are not two confirmations.

result.json follows project-protocol's project-result envelope. Reference each
specialist's native report, declared limitations, outstanding actions and evidence
of checks. Account for every expected delivery and required gate before marking the
run complete. Preserve a failed or interrupted state when requirements remain unmet.

For requested HTML or a final report that benefits from navigation or comparison,
the coordinator reads `references/human-view.md` before closing the run. Workers
keep their native deliveries; short results need no additional view.

Validate the final result with run_state.py validate --project ROOT --run-id ID
--result RESULT_PATH. Its record correspondence check is distinct from reading and
verifying the specialist evidence. Add newly discovered mandatory gates to the
append-only required_gates list before executing them; never remove a failed gate.

Reports include requested/read/runtime-exercised coverage separately, checks with
their exact candidate snapshot, decisions, changes, remaining limits and next
actions. Consolidation adds bytes moved and bytes deleted. Never claim runtime
coverage from source inspection, correctness from passing self-generated tests, or
disk recovery from a quarantine move.
