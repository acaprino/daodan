# Harness image generation contract

When a presentation needs generated or edited imagery, the coordinator must use
the image-generation tool exposed by the active harness. Discover the actual tool
name, input schema, supported references, transparency and returned artifact form
in this session. A skill, shell, SDK or provider name is not proof that the tool
is callable. Verify image inspection separately.

For SlidePoise, use its compiled generation request. Preserve the prompt and
reference order when mapping to the tool's real schema. A designer returns image
intent, composition constraints and reference paths; it does not invent tool
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
supported resource identity, slide association and inspection outcome. Use native
returned media and supported file handoff; do not guess a download endpoint or
claim an image is saved when only a preview exists. Verify the engine can consume
the artifact before reconstruction or insertion.

Generated slide compositions remain design references until reconstructed by
SlidePoise. Requested editable text, charts and tables must be native objects;
do not substitute a whole-slide image for the editable presentation.
