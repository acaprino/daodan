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

# Diagram style for native shapes

Rules for diagrams built from native shapes, connectors and text in DOCX and
PPTX under the assigned proposal or selected `DESIGN.md`. They apply to flows,
architectures, timelines, org charts, matrices and any figure whose boxes and
arrows the recipient may edit. `office:content` owns what the diagram says and
which relationships it must show; the format designer owns composition; the
coordinator builds the shapes through WordCraft or DeckCraft. A diagram
rendered elsewhere and inserted as an image is an illustration, bound by
`${PLUGIN_ROOT}/skills/pptx/references/image-tools.md`, and never
replaces a required editable diagram.

## Colour roles derived from the direction

The direction's palette supplies five values (`background`, `ink`, `surface`,
`accent`, `muted`). A diagram needs four more, derived rather than invented, and
recorded once in the design record:

| Role | Derivation | Use |
|---|---|---|
| `paper` | the direction background | Canvas and default node fill |
| `paper-2` | the direction surface | Container and secondary fill |
| `ink` | the direction ink | Node names and primary strokes |
| `muted` | the direction muted | Secondary text, default connector stroke |
| `soft` | muted mixed about 30% towards paper, still at least 4.5:1 on paper as text | Sublabels, boundary labels, legend |
| `accent` | the direction accent | The focal element: one, at most two per diagram |
| `accent-tint` | accent at 8 to 10% over paper | Focal node fill |
| `link` | the second data colour, or a cool hue from the derived palette | External calls, API arrows, cross-boundary edges |
| `rule` | ink at 15 to 20% opacity | Hairlines, container borders, gridlines |

Every text colour, `soft`, `link` and `accent` included, passes 4.5:1 on the
surface it sits on; a stroke or marker that carries meaning passes 3:1. A tint
is checked after composition over its surface, not as the opaque colour.

On a dark direction (`I`, `R`, or a brand's dark variant) swap `paper` and
`ink`, keep every opacity, and lift the accent a step in lightness so it holds
3:1 on the dark ground. A dark variant is a second record, not a tint of the
light one.

## Node treatments

Meaning is carried by fill, stroke and dash together, never by colour alone.
Use these seven treatments and no others; a legend is required when a diagram
uses more than two of them.

| Treatment | Fill | Stroke | Meaning |
|---|---|---|---|
| focal | `accent-tint` | `accent`, 1.25 pt | The one or two elements the slide is about |
| backend | `paper` | `ink`, 1 pt | Internal services, steps, owned components |
| store | ink at 5% | `muted`, 1 pt | Databases, queues, files, persisted state |
| external | ink at 3% | ink at 30%, 1 pt | Third parties, systems outside the boundary |
| input | muted at 10% | `soft`, 1 pt | Actors, triggers, entry points |
| optional | ink at 2% | ink at 20%, 1 pt, dash 4/3 | Planned, conditional or future elements |
| security | accent at 5% | accent at 50%, 1 pt, dash 4/4 | Trust boundaries, controls, audited paths |

Containers are opt-in: a `paper-2` fill with a `rule` border and a 6 pt corner
radius, used when a grouping is part of the message. Do not box every node.

## Strokes, grid and spacing

- Stroke weights: 0.75 pt thin (gridlines, ties), 1 pt default, 1.25 pt strong
  (focal stroke, primary flow). No shadows, no glows, no gradients on shapes.
- Corner radius: 3 pt small, 4.5 pt medium, 6 pt large; one radius per diagram.
- Snap every position, size and gap to one grid step chosen for the canvas
  (for example 0.05 in on a 13.333 in slide, 2 mm on an A4 page), and align
  shared edges exactly. The engine's reported coordinates are the proof; a
  rendered preview that looks aligned is not.
- Connectors are native connectors attached to shape anchors, stroked in
  `muted` by default and `link` for external edges, with one arrowhead style
  per diagram. Edges cross as little as possible; reorder nodes before adding
  a bend.

## Labels

| Role | Face | Size on a slide | Size on a page | Weight and case |
|---|---|---|---|---|
| node name | the direction's body sans | 12 pt minimum | 9 pt minimum | 600, sentence case |
| sublabel (port, protocol, path) | monospace when the direction has one, else the body sans | 9 pt | 7.5 pt | 400 |
| eyebrow (type tag, axis) | monospace or body sans | 8 pt | 7 pt | 500, uppercase, tracked 0.15 em |
| edge label | monospace or body sans | 8 pt | 7 pt | 400 |
| callout | the direction's heading face, italic where it exists | 14 pt | 10 pt | 400 |

Monospace is for technical strings only; names stay in the sans. A name that
does not fit at the minimum size is shortened, not shrunk. Non-Latin names use
the matching Noto family from `font-pairings.md` and drop uppercase and
tracking. Label boxes are sized from measured text in the actual face, with the
padding rounded up to the grid step.

## What a diagram does not do

- Two accents: the focal signal disappears. Mark a second emphasis with a
  treatment, not a colour.
- A rainbow of node colours: keep paper, ink and one accent; every other
  category becomes a muted variant or a treatment.
- More than three font families, counting the monospace.
- Chart series colours on a diagram; they belong to native charts only.
- Pure white paper under a warm direction; take the direction's actual
  background.
- A raster or SVG export substituted for required editable boxes and arrows.

## Provenance

Original Office guidance adopting ideas from
[cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)
(MIT), read at commit `97d795138448f6a739a0cebc3d9beb37a42077f1`: its role-based
skin, seven node treatments, one-accent rule, hairline strokes, 4-unit grid and
label hierarchy. Values are re-expressed in points for native shapes and derived
from the Office direction instead of a fixed skin; no upstream text, token
file, template, script or HTML/SVG pipeline is copied. Its importers, exporters
and web fonts are out of scope: Office diagrams are native objects.
