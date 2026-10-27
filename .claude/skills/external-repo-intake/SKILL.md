---
name: external-repo-intake
description: >
  Evaluate a new external capability through declared delegation or original local
  inspiration: owner selection, licensing, availability, host compatibility,
  local wiring, provenance and authorized delivery.
  TRIGGER WHEN: the user asks to "import", "pull", "vendor", "cherry-pick", or "borrow from"
  an external GitHub repository that is not already registered in the sync table of the
  `upstream-sync` skill.
  DO NOT TRIGGER WHEN: re-syncing a repository already registered in that sync table (use
  `upstream-sync`), refreshing a hand-authored plugin with no upstream (use
  `custom-plugin-refresh`), or mirroring our content outward to another host (use
  `downstream-exports`).
---

# External-repository intake

When the user asks to "import", "pull", "vendor", "cherry-pick", or "borrow from" an external GitHub repository (anything not already registered in the sync table of the `upstream-sync` skill), follow this workflow before touching any local file. This skill covers the *first* intake. Re-syncing repositories already registered uses the separate `upstream-sync` skill.

## 1. Classify the operation

Standing policy since 2026-08-04 forbids new vendored copies. An instruction to
import or borrow content does not waive that policy. Resolve the requested
capability through one of these modes before writing:

| Mode | Use | Ownership |
|---|---|---|
| **Delegation** | An external owner already supplies the capability | Declare its required dependency and load its canonical method; verify availability, the input/output contract and execution on the active host |
| **Original local inspiration** | A distinct local method is justified by workflow ideas | Write original content without copying upstream text; attribute the ideas and explain the local responsibility |

Runtime references to local plugins require `[dependencies].required`; local
optional dependencies and generic fallbacks for required providers are forbidden.
An unavailable provider needs an explicit recovery path for the active host.
Local source lives under `plugins/<name>/`; host mechanisms live in `adapters/`.
Native packages under `exports/` and root catalogs remain generated.

Historical intake modes are retained as provenance, not options for new work:
`kotlin-development` used full vendoring; `wshobson/agents` used cherry-picking,
hybrid sections and new files. Its generic multi-agent core, reverse-engineering
vendor and e2e-testing-patterns were later delegated upstream; the latter changed
in marketplace 18.0.0, and codebase-cleanup was retired in 19.0.0.
`codebase-map` adopted ideas from `gsd-build/get-shit-done` with original content.
Preserve existing licenses, attribution, sync records and retirement history.

## 2. Resolve the four dimensions

Use the task's existing authorization; ask only for a material unresolved choice.

| Dimension | Decision |
|---|---|
| **Capability** | Which requirement is missing, and which canonical owner supplies it? |
| **Integration** | Delegation or distinct original local inspiration? Avoid competing owners. |
| **Availability** | Required provider identity, active-host installation/recovery and executable method contract |
| **Provenance** | Preserve attribution and licensing; record the ideas adopted without starting a new vendor. Original inspiration adds only the watch row of step 7 |

## 3. License compliance gate

Before retaining any upstream text or code, inspect its license. Delegation copies no upstream content; original inspiration must remain original. License permission never waives the no-new-vendor policy. For existing derived material, retain these protections:

1. Read the upstream `LICENSE` file. The four expected outcomes:
   - **MIT / BSD / ISC / Apache-2.0**: proceed; preserve attribution header in every derived file.
   - **MPL-2.0**: proceed for documentation-only content; flag to the user before importing source code.
   - **GPL-2.0 / GPL-3.0 / AGPL**: STOP. Ask the user explicitly; the marketplace is MIT and incompatible licensing must be a conscious decision.
   - **No license / proprietary**: STOP. Do not import.
2. For Apache-2.0 specifically, check whether upstream has a `NOTICE` file. If it does, preserve its contents alongside the derived files.
3. Attribution header on every derived file (new or merged section):
   ```
   <!--
   Portions of this file are derived from <owner>/<repo>
   (https://github.com/<owner>/<repo>), <SPDX-license> License.
   Snapshot YYYY-MM-DD.
   -->
   ```

## 4. Fetch and inspect (read-only)

Inspect the canonical owner and its public license through supported read-only tools. Keep any authorized research output in an owned run. Read the selected method and its contract before wiring it; measure the relevant overlap and explain why delegation or original inspiration serves the request. Inspection grants no permission to copy upstream content.

### 4.1 Evaluated candidate: Taste v2 for Office

Read-only intake record, not an approved copied-source target. Source:
[Leonxlnx/taste-skill v2.1.5](https://github.com/Leonxlnx/taste-skill/tree/12af471f627f866411b4bd785b19646d3672784c),
commit `12af471f627f866411b4bd785b19646d3672784c`, MIT with complete license
and copyright notice. The current no-new-vendor policy still applies. Do not
copy or add a sync row until a scoped copied-source policy is authorized.

The useful capability is the chain from subject-specific material to idea,
direction, complete content and rendered critique. It is not the frontend build
engine. The proposed selective scope is:

| Upstream scope | Office use and intentional boundary |
|---|---|
| `references/copy.md` | Shared content: argument before composition, claims with proof, no filler and complete content at the required density. Keep Office source fidelity. Do not import permission to invent plausible sample details, website headline limits or web calls to action. |
| `library/directions.json` | Candidate visual-direction records for `office:design`: subject, tone, needs, idea, typography, colour, imagery, richness and pitfalls. Adapt selected records into existing Office directions and `DESIGN.md`; do not import the full library, CSS, viewport geometry or random deal. |
| `references/type.md`, `references/colour.md` | Few distinct type roles, scale contrast, semantic colour roles, deliberate proportions, contrast and image treatment. Enrich existing Office guidance only where different; retain native point sizes, font discovery/embedding and brand exceptions. Do not transfer px/vw constants or palette bans as universal Office rules. |
| `references/layout.md` | Shared-edge discipline, deliberate negative space, composition beyond the opening, rhythm and avoidance of accidental repetition. DOCX and PPTX designers translate these independently; there is no shared page/slide geometry and no universal ban on repeated document layouts. |
| `references/critique.md` | Render-only critique: first glance, focal point, squint, cover-the-brand specificity, edges, frame, type, colour, imagery, sameness, substance and collisions. Keep existing independent reviewers, candidate identity and severity gates. Do not import Awwwards weights, score caps, mandatory photography/motion or the three-round loop as a second contract. |
| `references/tells.md` | A dated prompt to question default devices and generic copy, plus the principle that removal without a real idea produces empty work. Select only Office-relevant anti-patterns. Do not import bans on numbering, hairlines, monospace, italic serif, colour families or other legitimate brand/editorial choices. |

A proposed first direction set for later authorization is `one-motif`,
`editorial-report`, `page-is-the-object`, `quiet-instrument` and
`colour-chapters`. Each needs a native DOCX/PPTX interpretation and a real
content case. `research.md` and `websites.json` are upstream web-study evidence,
not evidence that a numeric rule transfers to Office.

Exclude `scripts/`, Node/browser tooling, `library/heroes.json`,
`library/sections.json`, `app.json`, `motions.json`, `scenes/`, `photos.json`,
mobile viewport rules, app/dashboard rules, mandatory motion or photo quotas,
and open-collection harvesting. Keep Office intake, brand authority, image
ownership, native producers, existing layout catalogs and reviewer contracts.
The upstream's reported build time and token budget are not an Office target.

### 4.2 Evaluated candidates: huashu-design and diagram-design for Office

Read-only intake record of 2026-10-27, resolved as original local inspiration
(step 1), not delegation and not a copied source. Both are MIT.

| Candidate | Read at | Verdict |
|---|---|---|
| [alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design) v3.0 | `4fc7bfdbd5ec3fa2d43ce7a6433de60976a5e4b1` | HTML-native design skill; its PPTX is converted from rendered HTML (`html2pptx`), which the Office native-object contract excludes. Adopted as ideas only: the sample/converge/justify palette protocol, OKLCH chroma bands, temperature spread and default-look pitfalls in `office`'s `references/directions.md`; contrast sources, six further pairings, the overused-face table and display thresholds in `references/font-pairings.md`. Its style library, scripts, animation and web modules are out of scope. |
| [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) | `97d795138448f6a739a0cebc3d9beb37a42077f1` | Draws diagrams as HTML+SVG; DeckCraft does not render SVG and a raster export never replaces a required editable diagram. Adopted as ideas only: role-based colours, seven node treatments, one accent, hairline strokes, grid snapping and label hierarchy, re-expressed in points for native shapes in `office`'s `references/diagram-style.md`. Its pipeline, importers, exporters and web fonts are out of scope. |

Each has a watch row in the `upstream-sync` table and a paragraph under the
README's "Upstream projects and inspiration". Do not add either as a dependency
or a copied-source sync target without a new, scoped authorization.

## 5. Adapt to local conventions

For original local content and dependency wiring, apply these conventions while preserving existing attribution:

- **Dash-aside construct** ("X — Y — Z" / "X -- Y -- Z" / "X - Y - Z" bracketing a clause): replace with sentences, parentheses, or colons. Never substitute one dash form for another.
- **Emoji**: remove if the destination plugin's existing files have none.
- **References**: bind local references to shipped paths. Delegate by the owner's registered component identity and method contract, without rewriting or copying its body.
- **Namespace prefixes**: retain the external provider's actual registered identity. Declare its required dependency rather than inventing a local equivalent.
- **Host tool primitives** in team-related imports: express isolated dispatch, file ownership, delivery status, barriers and report ownership in neutral Markdown and workflow sidecars. The host adapter supplies its native mechanism. Do not replace an upstream Claude tool name with another native tool name in a kernel; run the host-vocabulary linter.

## 6. Wire the new content into existing roles and workflows

Give original local content and delegated methods an evidenced consumer:

1. Keep runtime references and helpers under `skills/<skill>/` and index them in that skill's `SKILL.md` with a one-line topic description. Kernel-root references, scripts and MCP directories are not shipped.
2. Update roles or workflows that consult the material. Own-plugin paths use `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/...` or skill-relative `references/...`. Cross-plugin consumers load the owner's named skill, with its required dependency declared; they never reach into another plugin's files by path. Declare role bindings in the workflow's phases or dispatch table when a loaded method needs them.
3. Apply the [component-authoring method](../../../plugins/work-controller/skills/work-record/SKILL.md#authoring-components) to new or revised components, including helpers, for any language, framework or activity. Wire applicable shared obligations before execution; load detailed task-specific references on demand. State each consumption path in the wiring text.

## 7. Preserve provenance and existing tracking

Delegation adds no sync-table row and no fetch loop: the provider's updates reach
users through its own installation. Original inspiration adds exactly two records:
an inspiration-only row in the `upstream-sync` table naming the upstream path, its
license and the upstream commit whose ideas were read, and a paragraph with link and
license under the README's "Upstream projects and inspiration". That row is a watch,
never a sync target: `custom-plugin-refresh` reads the upstream diff since the
recorded commit, adopts ideas by rewriting them and advances the commit. Nothing is
pulled, merged or copied. Record the canonical provider and the ideas adopted. Existing tracked copies,
licenses, merged sections and retirement records remain intact until a separately
authorized disposition. Areas under "Deliberately not vendored" in `CLAUDE.md`
remain delegated to their upstream owners.

## 8. Version and authorized delivery

- Bump each changed kernel's `plugin.toml` version and the marketplace metadata version.
- Rebuild all hosts and regenerate plugin documentation when kernels change.
  Regenerate native Codex instruction copies when their Claude-side sources change.
- Preserve research evidence and attribution alongside the accepted changes.
- Commit or push only when the current task explicitly authorizes it. If authorized,
  deliver the source, required version bumps and generated outputs together.

## 9. Verification before push

- Inspect original local content and wiring for unresolved references, stale tool names and dash-aside constructs.
- Before publication, run `python scripts/daodan_build.py --check`, `python scripts/sync_plugin_docs.py --check`, `python scripts/sync_codex_instructions.py --check` and the repository's required dependency, bundled-path, registration, fact-anchor, host-vocabulary and test gates.
- `git status` shows nothing in `.upstream-scratch/` staged.
- `git diff --stat` to sanity-check scope.
