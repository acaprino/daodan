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

# Audience Adaptation

Documentation must reflect the project it describes and serve the people who will actually read it. A security CLI and a consumer mobile app should not read the same way. This reference defines the Project Profile (what the explorer infers about a project) and the register model (how every writer calibrates tone, depth, and structure to that profile). All project-knowledge writers read this file on demand, not upfront.

## Project Profile (schema)

The `codebase-explorer` produces this profile as the first section of `context-brief.md`. Every writer consumes it. Fields:

- **Project type / domain**: the closest of security or infrastructure tool, developer library or SDK, CLI tool, consumer web or mobile app, internal line-of-business app, data or ML pipeline, game, framework, API or backend service. Add a domain tag (for example banking, healthcare, devtools, e-commerce).
- **Primary audience**: the main reader (for example backend engineers, mobile developers, banking operators, data scientists, end users, stakeholders).
- **Secondary audiences**: other readers to serve at the plain-language layer (for example PMs, QA, designers, new hires, clients).
- **Register**: a point on the spectrum from `technical-precise` through `balanced` to `accessible-vivid`.
- **Purpose / problem solved**: one short paragraph. The WHY: what problem this solves and for whom.
- **Scope**: what the project does.
- **Non-goals**: what it deliberately does not do.
- **Maturity**: prototype, active, production, or maintenance.
- **Confidence + signals**: for each inference above, a confidence (high, medium, low) and the signals it rests on (dependencies, naming, README framing, UI presence, distribution channel, domain vocabulary, git history). Low-confidence items are surfaced at the confirm step.

## Register matrix

How the profile maps to output parameters:

| Register | Tone | Jargon policy | Example style | Diagram emphasis | Depth split | Plain layer and glossary |
|---|---|---|---|---|---|---|
| Technical-precise (tool, library, CLI, infra) | Exact, terse, contract-aware | Use freely, define on first use | API calls, config snippets, signatures | Architecture, sequence, data model | Internals deep, plain layer brief | Short executive summary, glossary for domain terms |
| Balanced (service, API, internal app) | Clear, explanatory | Use but explain | Request and response, workflows | Architecture plus workflows | Even | Moderate executive summary, full glossary |
| Accessible-vivid (consumer app, game) | Friendly, benefit-led, concrete | Avoid, explain everything in plain words | User flows, screenshots, scenarios | Flowcharts, mindmaps | Internals light, plain layer is the centerpiece | Prominent executive summary, full plain-language glossary |

The register is a dial, not three buckets. Pick the nearest column and lean toward the profile.

## Archetypes

Concrete calibrations. Match by the signals line, then write per the how line.

**Technical or infrastructure tool** (security tool, library, SDK, CLI)
- Signals: no end-user UI; distributed via a package registry or a binary; the dependency list is developer tooling; the README addresses developers; the vocabulary is technical.
- How: precise and complete. Lead with contracts, invariants, threat surface, and exact interfaces. Internals go deep. The plain layer is a short hand-off, not the focus.

**Consumer app** (web or mobile, end-user facing)
- Signals: a UI framework is present; distribution is an app store or the web; product or landing copy lives in the repo; feature names are user-facing.
- How: benefit-led and vivid. Lead with what the user can do and why it matters. Use user-flow framing and scenarios. Keep internals light. The plain layer is the centerpiece.

**Domain or business app** (internal line-of-business)
- Signals: heavy domain vocabulary; integrations with internal systems; role and permission models; the README assumes domain knowledge.
- How: glossary-heavy and workflow-led. Frame everything around the business process and the operator's task. Define every domain term.

**Data or ML pipeline**
- Signals: dataset handling, model code, batch or stream processing, notebooks, training or evaluation scripts.
- How: dataset-and-transform framing. Lead with data lineage: where data comes from, how it is transformed, where it lands. Document schemas, evaluation, and cost.

**Game**
- Signals: a game loop, rendering, physics or asset libraries, scene or entity systems.
- How: core-loop and mechanics framing. Lead with what the player does and how the loop runs, then the systems (input, render, state).

## Accessible entry points

Serve the readers in the file/audience plan. A plain introduction or glossary
belongs in an existing document when it serves that reader; a separate summary
or glossary is created only when the authorized plan justifies it. Technical,
consumer and mixed-audience projects need different amounts of explanation.
No named document is required merely because a template contains it.

## How writers apply this

- `overview-writer`: owns the planned introduction, overview and feature material; leads with attributed purpose for accessible profiles.
- `tech-writer`: the depth of tech-stack and architecture scales with register; uses plain analogies for accessible profiles.
- `flow-writer`: workflow and data-model framing follows the archetype (user-flow, data-lineage, or core-loop).
- `onboarding-writer`: getting-started tone matches the primary audience; non-technical readers get orientation, not only commands.
- `ops-writer`: operational reference and configuration recipes use the audience's vocabulary while retaining exact commands and defaults.
- `guide-reviewer`: audits the planned files for register, factual consistency and appropriate reader navigation; it does not create a required document set.
