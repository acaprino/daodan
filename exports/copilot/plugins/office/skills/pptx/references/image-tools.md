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

# Harness image generation contract

When an Office document or presentation needs generated or edited imagery, the coordinator must use
the image-generation tool exposed by the active harness. Discover the actual tool
name, input schema, supported references, transparency and returned artifact form
in this session. A skill, shell, SDK or provider name is not proof that the tool
is callable. Verify image inspection separately.

## Choose the asset source

For both DOCX and PPTX, visual assets may be supplied or reused, found through
available search tools, or generated/edited through the active harness image
tool. Choose per asset according to the brief, shared theme and intended purpose;
search is not a prerequisite for generation. Do not force a generation call or
an image quota when existing approved assets or native objects serve the task.

The designer records the intended source route, subject/purpose, target document
block or slide, style, aspect ratio, crop, resolution and any transparency needs.
For generation/editing, include prompt intent and reference assets for the
coordinator's actual tool schema. For searched assets, retain the source URL,
license/usage evidence and required attribution; search visibility alone does
not establish reuse rights. For generated assets, retain the actual tool, prompt,
references and returned artifact identity. Inspect every selected asset before
insertion, including consistency with the accepted theme and factual content.

Use supplied or verified official logos and exact brand assets when identity must
be preserved. Generated illustrations cannot replace verified evidence or invent
data. Required editable charts, tables, labels and diagram relationships stay
native and traceable to their sources; a generated visual is not proof of them.

## Generate or edit through the harness

Preserve the prompt and reference order when mapping a request to the tool's
real schema. A designer returns image intent, composition constraints and reference paths; it does not invent tool
arguments or claim generation. Inspect references before editing and follow the
tool's actual reference-input rules.

Only a context with the exposed tool may invoke it. A restricted worker returns
its image request to the coordinator. If the coordinator lacks the tool, ask the
parent harness to perform the call when that handoff is available; otherwise
record the missing capability and block the dependent image step. Continue
independent source, outline or preservation work. Do not assume another agent
inherits an unavailable tool.

Do not use an API-key script, external image CLI, browser service or different
model as an automatic fallback. Manual image exchange or an external provider
requires the user's explicit choice. No generation call is required for a
text-only edit or a deck using only existing approved assets.

Retain request identity, references, actual tool, returned local artifact or
supported resource identity, document block or slide association and inspection outcome. Use native
returned media and supported file handoff; do not guess a download endpoint or
claim an image is saved when only a preview exists. Verify the engine can consume
the artifact before insertion.

Icons are searched or supplied assets: take them from an open-licensed icon set,
record the set, version and license, and keep one set and stroke weight across the
deck. Insert them in a raster or metafile format the engine draws (PNG or EMF for
DeckCraft at its reference version, which does not render SVG), at the size they
appear. A native preset shape can replace an icon when it carries the same meaning.

Generated page or slide compositions remain design references until implemented
through the selected native production path (WordCraft or DeckCraft). Requested editable text, charts and tables must be native
objects; do not substitute a whole-slide image for an editable presentation or a
whole-page image for an editable document.
