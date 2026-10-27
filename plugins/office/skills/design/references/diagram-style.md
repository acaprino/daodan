# Diagram style for native shapes

Rules for diagrams built from native shapes, connectors and text in DOCX and
PPTX under the assigned proposal or selected `DESIGN.md`. They apply to flows,
architectures, timelines, org charts, matrices and any figure whose boxes and
arrows the recipient may edit. `office:content` owns what the diagram says and
which relationships it must show; the format designer owns composition; the
coordinator builds the shapes through WordCraft or DeckCraft. A diagram
rendered elsewhere and inserted as an image is an illustration, bound by
`${CLAUDE_PLUGIN_ROOT}/skills/pptx/references/image-tools.md`, and never
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
