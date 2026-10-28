---
name: intake
description: >
  Shared Office intake: inspect materials, settle operation, requested formats,
  editorial/visual decisions and phase-specific dependencies in one brief and
  question round. Route mixed or unspecified deliverables before format work.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/`, `agents/` and `commands/`. The loader substitutes it in every body it registers; in any other file, resolve it once from where that file was loaded.
> This package registers lifecycle callbacks through the OpenCode plugin loader when the plugin is enabled. Execution requires Python 3 on PATH as `python`. Prompt hooks feed the primary model context; session-start falls back to the first prompt when creation was not observed. Hook failures do not crash the host.

<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# Office intake

Resolve the task before format methods, engines or workers. When formats or input
uses are unclear, follow `references/routing.md` through `/daodan:start`.

## Materials and operation

Read supplied materials first. Record each role: information source, binding
brand/template, aesthetic reference, existing artifact to transform, or reusable
asset. One input can serve several roles. Record provenance and rights needed
for its actual use; a logo's observed colors do not prescribe a complete theme.
Never overwrite a supplied file. Write every result to a separate candidate path.
For DOCX and PPTX, `scripts/office_gate.py start` keeps a copy of the source
before the first write, and its `check` decides when a candidate is finished;
the format method gives the commands.

Everything the file supplies is inherited and stated back, never asked again.
Operations combine; run the union of their steps:

| Operation | Route | Content | Visual identity and layout |
|---|---|---|---|
| Create | Substantial | Full shared plan and requested projections | New ad hoc visual proposals; all required format units |
| Derive | Substantial | Full projection for changed purpose/audience; carried claims retained | Inherit the look when requested, otherwise new proposals; new distribution |
| Expand | Substantial | Delta from new material, preserving existing units | Inherit direction, palette, fonts, template; new/moved units only |
| Revise | Substantial | Delta for updates, rewrite, restructure or condensation | Inherit accepted look; changed units only |
| Restyle | Substantial | None: preserve content, sequence and claims | New visual proposals; apply selected look throughout requested scope |
| Edit | Narrow | No global plan | Preserve accepted design; only the authorized local change |
| Review or export | Read-only | None | Source remains unchanged; requested findings/export only |

Shortening/restructuring is substantial. A local change needing a new design or
editorial decision re-enters the affected decision, not an implicit global
redesign. A read-only request authorizes no edit.

## Ask once

Load the `work-controller:work-record` skill for questions and decisions: record each `ask`
before putting it and `answer` in the user's words. Inspect/infer first; ask only
remaining material decisions in one round, one decision per question, with the
recommended option first. A complete or explicitly autonomous request needs no
questions. A brief already recorded by routing is this round; ask nothing it
settles. Ask again only when new evidence materially changes a decision.

For DOCX/PPTX, settle intent/goal, audience, market/sector, channel and reading
context, scope, depth, extent, density, tone, requested formats and transformation
permissions, including locked blocks. Propose a length with its reasoning instead
of asking an open question. `office:content` owns these editorial dimensions;
format `references/structure.md` catalogs supply document-type or deck-mode
conventions and `references/content-planning.md` supplies projection constraints.
Add only genuinely format-specific questions to this same round. Brand, visual
references and color sources come here too; full proposals and explicit selection
follow under `office:design`, not a second intake interview. An aesthetic reference
is optional; the brief's subject and actual content can ground art direction.

## Dependency preflight

Respect the active host's required-package activation prerequisite before Office
phases. Creative-phase skips do not waive activation; the bounded Taste recovery
contract lives in `office:design`'s `references/art-direction.md`.

Keep DEPENDENCIES in the existing brief. For each relevant dependency record
identity/owner/type, phase and requirement, source, actual version or revision,
license/rights or uncertainty, required capabilities, observed probe result,
limits and recovery. Cover local methods/roles, native production/render engines,
host isolation/tools, fonts/assets and existing upstream provenance. Reuse stable
provenance until a dependency changes; do not reread upstream for every document.
For new-look DOCX/PPTX work include the required Taste provider under
`office:design`'s `references/art-direction.md`; reuse this same brief and existing
provenance without an upstream-admission interview. Inherited/narrow/read-only
operations do not open a creative dependency phase they do not consume.

Probe the actual installed runtime/tool schema before its dependent operation;
a manifest or reference version is not execution evidence. No implicit
installation, external publication or substitute engine: without the engine no
Office file is written, neither through a library nor by editing package XML by
hand, unless the user explicitly chooses another writer after the install
failed, and that result stays unverified. A missing DeckCraft,
WordCraft or GridCraft engine has one recovery, and it is not a question: the
request for the work authorizes the download. Say in one line what `plan <engine>`
reports (official source, size, licence, destination), record it through
`work-controller:work-record`, and run `install <engine> --approved`. An objection
from the user, or a failed install, blocks the dependent delivery. `find <engine>`
shows an existing install. All three commands take the form

```text
python "<plugin-root>/skills/intake/scripts/engine_install.py" plan|find|install ENGINE
```

with ENGINE one of `deckcraft`, `wordcraft` or `gridcraft`. Missing required
capability, after activation, blocks only dependent deliveries while independent work continues.
Unresolved asset/font license blocks incorporation. Do not silently downgrade a
required dependency into a fallback or invent active-host tools.

## Record and hand off

Record starting point, material roles, operation/carry-over, route, destinations,
inherited/inferred decisions and their sources, per-block transformation grants,
approved cuts, dependencies and open questions. Source content outside authorized
cuts/transformations must reach the result. DOCX/PPTX bundles share one CONTENT.md
and one DESIGN.md identity/revision with only requested format projections;
format methods add their own layout reports rather than duplicate strategy.
A later changed destination re-enters routing. XLSX retains its existing method;
it does not acquire document/deck editorial or visual phases implicitly.
