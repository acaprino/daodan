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

# Creative providers and scope

This method combines Office's built-in slide design library (`design-library.md`)
and PPTX compatibility rules (`pptx-compatibility.md`) with optional external
creative guidance, without copying upstream content or creating another renderer.
The external providers are declared as optional in Office's manifest. They are not
required by SlidePoise, DeckCraft or the base Office method, and none of them
implements a PPTX engine:

| Provider | Canonical skill | Presentation use |
|---|---|---|
| `impeccable@impeccable` | `impeccable:impeccable` | Typography, colour, spatial hierarchy and critique criteria |
| `taste-skill@taste-skill` | `taste-skill:design-taste-frontend` | Art direction, authored typography, purposeful imagery and critique |

Read `pptx-compatibility.md` and `design-library.md` before consulting a provider.
Give each selected provider the fixed slide canvas, actual font choices,
engine-supported native objects and required editability. Translate its advice
into the slide-object specification in the designer's report, before
reference-image generation or native construction.

## Select at most one provider per role

Choose by the gap `design-library.md` leaves, not by availability alone:

- **Designer**: `taste` for art direction, authored typography and purposeful
  imagery.
- **Reviewer**: `impeccable` for critique criteria, or `taste` for critique
  references. Pick one.

Do not load overlapping advice into one assignment: at most one provider per
worker, and never two providers with the same role above. Honor the user's
requested selection when given. When nothing is selected, Office's built-in
library and the selected engine's guidance are sufficient and complete; never
open a provider merely because it is installed.

For each selected provider, resolve its actual installed skill identity on the
active host, read its canonical body, then only relevant references. Record
whether each declared provider was consulted, unavailable or unselected with the
reason. Installation is not evidence of consultation. Do not copy upstream skills
into Office.

These providers primarily address web interfaces. Impeccable explicitly excludes
general non-UI workflows. Here consult its transferable visual guidance as
reference material for slide composition and critique; do not invoke application
bootstrap, context CLI, page implementation or unrelated product-document writes.
Office owns the slide workflow, editability, source fidelity and render evidence.
This scoped consultation does not claim any provider implements a PPTX engine or
that its full UI workflow ran.

Taste's full workflow builds and inspects websites or app screens. Consult only
its transferable typography, layout, colour, imagery and critique references
through the resolved installed skill. Do not run its direction-selection,
asset-search, scene or browser-inspection scripts, or import motion and image
quotas into slide requirements. This reference consultation requires no Taste
Node/browser runtime. Use Office's harness image contract for generated or edited
imagery. Do not turn provider output into HTML/CSS and assume a faithful
conversion to editable PPTX.

When the optional provider is unavailable, skip its contribution and continue
Office's built-in `design-library.md` criteria and the selected engine's
guidance. Required designer and reviewer deliveries remain required. Do not
install a provider automatically. If the user explicitly requires a named
provider, report its unavailability and the active host's supported setup route;
keep that requested contribution unfulfilled until resolved, while continuing
independent work. Never claim the missing provider was used or substitute an
unrelated skill or another host's installation command. Reading guidance does
not establish image access, isolation or rendering capabilities.

Use real content to establish a direction, then vary composition with each page's
communication job: orient, explain, compare, show evidence or request a decision.
Preserve brand constraints and readable labels. Offer alternatives only to resolve
a material choice. Reusable page types demonstrate native editable content.

Provenance: separating identity, style, layout and deck purpose is also informed
by [PPT Master](https://github.com/hugohe3/ppt-master) (MIT). No code, prompts,
template library or installation workflow from that project is bundled.
SlidePoise retains its upstream profiles and composition method.

Taste reference identity was checked against the upstream 2.1.4 manifests and
canonical skill (MIT). Its maintained web workflow is not a tested PPTX adapter;
runtime-script safety and installed-host execution are not established by reading
the references. Sources: [manifest](https://github.com/Leonxlnx/taste-skill/blob/main/.claude-plugin/marketplace.json),
[skill](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/SKILL.md),
[license](https://github.com/Leonxlnx/taste-skill/blob/main/LICENSE).
