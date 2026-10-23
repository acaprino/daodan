# Creative providers and scope

This method delegates creative knowledge without copying upstream content or
creating another renderer. Optional external providers are declared in Office's
manifest; none is required by SlidePoise, DeckCraft or the base Office method:

| Provider | Canonical skill | Presentation use |
|---|---|---|
| `frontend-design@claude-plugins-official` | `frontend-design:frontend-design` | Distinct direction, deliberate typography, composition and imagery |
| `impeccable@impeccable` | `impeccable:impeccable` | Typography, color, spatial hierarchy and visual critique criteria |
| `taste-skill@taste-skill` | `taste-skill:design-taste-frontend` | Art direction, authored typography, purposeful imagery and critique |

Read `pptx-compatibility.md` before consulting a provider. Give each selected
provider the fixed slide canvas, actual font choices, engine-supported native
objects and required editability. Translate its advice into the slide-object
specification in the designer's report, before reference-image generation.

Choose only the providers useful to the brief and actually available. Honor
the user's requested selection; otherwise use an available provider only when its
guidance helps the assignment. Do not require multiple providers for overlapping advice.
For each selected provider, resolve its actual installed skill identity on the
active host, read its canonical body, then only relevant references. Record
consulted, unavailable and unselected providers with the reason. Installation is
not evidence of consultation. Do not copy these skills into Office.

These providers primarily address web interfaces. Impeccable explicitly excludes
general non-UI workflows. Here consult its transferable visual guidance as
reference material for slide composition and critique; do not invoke application
bootstrap, context CLI, page implementation or unrelated product-document writes.
Frontend Design supplies direction, not HTML as the requested deliverable.
Office owns the slide workflow, editability, source fidelity and render evidence.
This scoped consultation does not claim any provider implements a PPTX engine
or that its full UI workflow ran.

Taste's full workflow builds and inspects websites or app screens. Consult only
its relevant typography, layout, colour, imagery and critique references through
the resolved installed skill. Do not run its direction-selection, asset-search,
scene or browser-inspection scripts, or import motion and image quotas into slide
requirements. This reference consultation requires no Taste Node/browser runtime.
Use Office's harness image contract for generated or edited imagery. Do not turn
provider output into HTML/CSS and assume a faithful conversion to editable PPTX.

When an optional provider is unavailable, skip its contribution and continue the
base Office method and the selected engine's guidance. Required designer and
reviewer deliveries remain required. Do not install a provider automatically.
If the user explicitly requires a named provider, report its unavailability and
the active host's supported setup route; keep that requested contribution
unfulfilled until resolved, while continuing independent work. Never claim the
missing provider was used or substitute an unrelated skill or another host's
installation command. Reading guidance does not establish image access,
isolation or rendering capabilities.

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
