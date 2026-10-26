# Theme Factory upstream (retired preset skill)

Adapted from [anthropics/skills](https://github.com/anthropics/skills/tree/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/theme-factory),
revision `dbd4588f9e1033efb41dad4bef2f7947c8993d44` (2026-10-09),
source directory `skills/theme-factory/`.
Apache-2.0 terms and Copyright 2026 Anthropic, PBC. are retained in
`LICENSE-theme-factory-APACHE-2.0.txt`. Office's MIT license does not replace
the bundled source terms.

Office no longer ships the Theme Factory skill, its ten `themes/*.md` presets
or `theme-showcase.pdf`. Four preset palettes (Desert Rose, Midnight Galaxy,
Golden Hour, Sunset Boulevard) continue as directions `Q` to `T` of
`directions.md`, rebuilt with Office text roles and contrast-checked ink,
surface and muted colours; the other six were already covered in character by
directions `A` to `P`. The notes below describe the adaptation as it stood
before that consolidation.

The upstream `SKILL.md` before modification has SHA-256
`c35893e221e28895c52143cc11bf30e41a44817796b39d4b15727dadc9796552`.
The ten `themes/*.md` files, `LICENSE.txt` and `theme-showcase.pdf` are preserved
byte for byte. The showcase is 124,310 bytes, SHA-256
`3e126eca9fe99088051f7cb984c97cedb31c7d9e09ce0ba5d61bd01e70a0d253`,
Git blob `24495d145c95917aba3a3445f7105444b6f7cfcc`.
The package contains font names and an illustrative PDF, not installable fonts.

## Intentional adaptation

Modified the skill body to honor existing brands, templates, session selections
and autonomous-design authorization instead of requiring a repeated selection
gate. Added an available-viewer requirement, a clearly labeled text alternative,
native Word/PowerPoint style mapping, installed-font and contrast checks, saved
artifact review, and the existing harness image-tool ownership. Editorial and
typographic layout remain with Office's companion guides and production methods.
Both format designers consume one shared accepted theme specification before
making document/slide-specific layout decisions. This local handoff does not
alter the preserved preset files or showcase.

For updates, compare the whole scoped upstream directory at this pin, including
asset additions and removals. Merge source guidance while preserving Office
ownership and authorization. Keep unmodified assets exact, retain all applicable
notices and update this provenance only after inspecting the new source. A theme
preview does not establish fidelity of a generated DOCX or PPTX.
