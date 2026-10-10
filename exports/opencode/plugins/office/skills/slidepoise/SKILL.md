---
name: slidepoise
description: >
  Create and revise professional, editable PowerPoint presentations through the
  external SlidePoise framework, with visual design, native reconstruction and
  rendered review. TRIGGER WHEN: the user asks for a PPTX, pitch deck, consulting
  presentation, branded slides, a presentation from research or a workbook, or
  SlidePoise. DO NOT TRIGGER WHEN: the requested deliverable is only an Excel
  workbook (use office:xlsx) or an image without an editable presentation.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/`, `agents/` and `commands/`. The loader substitutes it in every body it registers; in any other file, resolve it once from where that file was loaded.

# Editable presentations

Produce a usable editable `.pptx` whose argument, visual design and rendered pages
meet the user's brief. The local integration delegates presentation construction
to [SlidePoise](https://github.com/henryhyw/slidepoise), an MIT-licensed external
framework. Its skill, references, schemas and runtime remain upstream-owned and
are read from the installed runtime. Read `references/runtime.md` before setup or
the first presentation. Daodan installation alone does not install that runtime.

## Establish the outcome

Infer audience, purpose, language, presentation length, delivery context, source
material and brand from the request. Ask only for material missing decisions.
Develop a clear narrative: what the audience should understand or decide, what
supports the recommendation, and which assumptions remain uncertain. Preserve
the user's accepted wording, actual figures, exact logos and required sources.
Keep source attribution and dates attached to claims. Never invent customer
results, market figures or citations to make a deck look complete.

Match interaction to the request. A sample can resolve uncertainty about style;
a fully autonomous request authorizes routine design decisions and corrections.
Do not introduce per-slide permission gates. Changes to scope, source meaning,
brand identity or a paid generation budget require a real user decision.

## Discover and load the external method

Run the bundled bridge using the host's Python executable:

```text
python "<plugin-root>/skills/slidepoise/scripts/slidepoise_bridge.py" discover
python "<plugin-root>/skills/slidepoise/scripts/slidepoise_bridge.py" cli doctor
```

Respect `SLIDEPOISE_HOME`, or pass the bridge's `--home` option before its command.
Read the `SKILL.md` at the returned `skill_root` and the relevant references it
names. Use absolute installed paths for those reads. Discover and inspect the
current image-generation and image-viewing interfaces before creative work.
Load the selected external Profile, configuration and Library Sets through the
runtime. Host installation support and a successful doctor do not prove that an
image tool or preview renderer is available.

The external skill is authoritative for its runtime contracts and CLI syntax.
Use its packaged schemas and command help rather than recreating their layouts.
Execute installed scripts through the bridge's `script` command, which resolves
them against the discovered external skill. Paths passed as script arguments
remain relative to the current presentation workspace, so use absolute paths
when operations span slide directories.

```text
python "<plugin-root>/skills/slidepoise/scripts/slidepoise_bridge.py" script slidepoise_runtime.py --help
```

If discovery fails, resolve the explicit missing prerequisite from the runtime
reference. Continue useful brief and source preparation. Do not claim a PPTX was
constructed, rendered or visually reviewed without the corresponding evidence.

## Design, reconstruct and inspect

Follow the installed SlidePoise method from deck planning through generation,
semantic mapping, measured reconstruction, assembly and final inspection.

- Keep one authoritative outline and shared visual direction. Each slide has a
  communication job, supported message, stable ID and source obligations.
- Inspect relevant visual references and actual assets. Let comparisons,
  relationships and evidence determine the composition. Use a coherent hierarchy,
  typography and color system while allowing slide layouts to vary.
- Generate from the runtime's compiled request using the user's selected image
  tool. Preserve its prompt and reference ordering. Manual image exchange is an
  explicit choice when creative generation is unavailable; it cannot supply a
  missing reconstruction engine or visual reader.
- Reconstruct selected designs through the upstream semantic map, OpenCV evidence
  and constructor-scene pipeline. Native text, tables, charts, shapes and
  connectors must remain editable where their meaning requires it. Photographs,
  textures and illustrations may remain distinct image objects.
- Inspect the actual rendered PPTX pages against both the brief and the selected
  designs. Check text clipping, figure labels, connector direction, alignment,
  contrast, brand fidelity, sources and deck-wide consistency. A contact sheet
  helps compare pages; full-resolution inspection resolves material details.
- Correct routine defects within the accepted brief, rebuild affected pages and
  inspect the changed renders. Package validity, object counts and a reference
  image alone do not establish design quality or faithful reconstruction.

For a deck based on Excel, load the `office:xlsx` skill to read the actual workbook,
verify the intended figures and retain native chart data. Keep workbook formulas
and their calculation status visible in the source evidence. Do not substitute
screenshots for requested editable charts or tables.

## Deliver

Deliver the editable `.pptx`, a useful preview and a concise account of material
raster content or unresolved limitations. Verify that the package opens and that
requested native objects exist. State the render engine and whether every page
was inspected. If rendering is unavailable, clearly label the delivered file as
unreviewed and do not describe the presentation as visually verified.

The work directory and construction contracts support iteration; the user should
receive the presentation and usable previews without managing those internals.
