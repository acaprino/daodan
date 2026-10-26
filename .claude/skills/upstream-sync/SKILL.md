---
name: upstream-sync
description: >
  The sync table of every plugin ported from an external repository, the default
  upstream-update strategy (classify each file, preserve local customizations, apply targeted
  Edits), the `gh api` fetch patterns, and the non-obvious per-plugin sync notes.
  TRIGGER WHEN: the user asks for "upstream updates", asks to sync or re-pull a plugin from
  its upstream source, or asks which plugins are upstream-synced and what drifted.
  DO NOT TRIGGER WHEN: vendoring from a repository for the FIRST time (use
  `external-repo-intake`), refreshing a hand-authored plugin that has no upstream (use
  `custom-plugin-refresh`), or mirroring our content outward (use `downstream-exports`).
---

# Upstream-synced plugins

Some plugins are ported from external repositories and should be kept in sync with their upstream source. When asked to update one of these plugins, fetch the latest content from the upstream URL using `gh api` and apply any changes, then follow the standard marketplace update workflow in `CLAUDE.md`.

Local sync targets are neutral kernels: `plugin.toml`, `roles/`, `workflows/` with
TOML sidecars, `skills/`, `contracts/` and `policies/`. Host-specific mechanisms
belong in `adapters/`; `exports/` and root catalogs are generated. Upstream
`agents/` and `commands/` paths describe that upstream's layout, not local source.

Nothing listed under "Deliberately not vendored" in `CLAUDE.md` belongs in the table below. Those areas were removed and delegated on purpose; do not add rows for them on a future pass. The former `obra/superpowers` export row was retired with the VS Code extension and stays retired.

## Default upstream-update strategy

When the user asks for "upstream updates" (or similar), this is the default workflow. Do not blindly overwrite local files - most syncs need targeted merging because local has legitimate customizations.

1. **Check the applicable copied-source sync targets in parallel**. For each copied-source file in the sync table below, diff the upstream against the local version. Office design snapshots are on demand: include them only when the user requests Office upstream review or names the relevant source, not in a generic batch by default. Exclude inspiration-only provenance rows from vendored pull, merge and sync operations; their original local plugins remain eligible for `custom-plugin-refresh`. Spawn Explore agents when there are many files to parallelize the diffing. Focus the reports on: which files differ, what changed, and whether the drift is intentional or worth pulling.

2. **Classify each file** before touching it:
   - **Clear win** - new upstream file missing locally, or a bug/fact fix with no local conflict. Pull directly.
   - **Minor refinement** - small wording/metadata changes. Pull if no local frontmatter or content conflicts.
   - **Hard merge** - upstream rewrote a section we also evolved locally. Layer upstream changes onto local; do not overwrite.
   - **Intentional drift** (do not touch) - local namespace rewrites (upstream `<their-plugin>:` -> local `<our-plugin>:`), local polish (typo fixes, expanded triggers), style conventions (no dash-aside construct per CLAUDE.md; no emojis in some plugins), local-only additions (custom presets, Ecosystem Integration sections), upstream dash-asides rewritten to sentences/parens/colons.

3. **Preserve these local customizations** on every merge:
   - Source attribution lines at the top of files
   - Frontmatter: localized `description` (often multiline with `>`), `tools`, `color`, `version`, `model`
   - Plugin-specific style: no dash-aside construct (rewrite "X — Y — Z" / "X -- Y -- Z" / "X - Y - Z" asides into sentences, parens, or colons), no emojis in some plugins
   - Namespace replacements (upstream `<their-plugin>:X` -> local `<our-plugin>:X`)
   - Local-only sections (e.g., `## Ecosystem Integration` blocks added during earlier syncs)

4. **For unresolved material choices**, ask the user through the host's question mechanism. Reuse the accepted scope and existing decisions:
   - When upstream rewrote a section we also evolved (merge vs keep vs overwrite)
   - When upstream adds a feature that conflicts with local direction
   - When a file is flagged as "major drift"

5. **Apply targeted Edits, not Writes** - prefer surgical edits that fix specific bugs (stale tool names, added items in a list) over replacing whole files. Only use Write for new files or when the entire file is being replaced.

6. **Keep imported behavior host-neutral.** A kernel states ownership, isolated delivery, barriers and evidence requirements without naming native team or tool primitives. Translate upstream spawn/coordination instructions into those obligations and declared phase/dispatch metadata. Put a host-specific mechanism in that host's adapter only when supported by its binding and evidence. Run the host-vocabulary linter after team-related imports; replacing one Claude tool name with another in a kernel does not make it portable.

7. **Version bump and rebuild** - bump each touched plugin's `version` in `plugins/<name>/plugin.toml` and `metadata.version` in `.claude-plugin/marketplace.json`. Rebuild every host with `python scripts/daodan_build.py` and regenerate the component/dependency reference with `python scripts/sync_plugin_docs.py` when a kernel changes; catalog entries and exports are generated, never hand-merged.

8. **Verify and commit** - run `python scripts/daodan_build.py --check`, `python scripts/sync_plugin_docs.py --check` and the required repository gates before publication, check named consumers and bundled paths, then inspect `git status` / `git diff --stat`. If repository workflow skills changed, regenerate their native Codex adaptations with `python scripts/sync_codex_instructions.py` and check parity with `--check`. Commit kernels, regenerated exports/catalogs, documentation references and instruction copies together with a descriptive message like "Sync upstream updates for X and Y (vN.N.N)". Push to master under the task's publication authorization.


The two `codebase-map` rows are inspiration-only provenance, not copied-source sync targets. Keep their source attribution and adoption history here, but exclude them from vendored pull, merge and sync. Their presence does not exclude the original local `codebase-map` plugin from `custom-plugin-refresh`. Existing copied-source rows remain tracked; this inventory does not authorize new vendoring.

| Plugin | Upstream source | Files to sync |
|--------|----------------|---------------|
| `codebase-map` (inspiration) | `gsd-build/get-shit-done` - `agents/gsd-codebase-mapper.md` | `plugins/codebase-map/workflows/analyze.md` (patterns adopted, not direct copy) |
| `react-development` (react-best-practices) | `vercel-labs/agent-skills` - `skills/react-best-practices/` | `plugins/react-development/skills/react-best-practices/SKILL.md`, `plugins/react-development/skills/react-best-practices/references.md`, `plugins/react-development/skills/react-best-practices/rules/*.md` |
| `digital-marketing` (domain-hunter) | `ReScienceLab/opc-skills` - `skills/domain-hunter/` | `plugins/digital-marketing/skills/domain-hunter/SKILL.md`, `plugins/digital-marketing/skills/domain-hunter/references/registrars.md`, `plugins/digital-marketing/skills/domain-hunter/references/spaceship-api.md`, `plugins/digital-marketing/skills/domain-hunter/examples/auto-video-editing-domain.md` |
| `office` (editorial and typography) | `marcmarti9/agentit`, `skills/editorial-design/SKILL.md` and `skills/typography-and-layout/SKILL.md` | `plugins/office/skills/design/references/editorial-design.md` and `references/typography.md`; source pin, modifications and retained Apache/MIT notices in `design/references/agentit-upstream.md` |
| `office` (Theme Factory, retired) | `anthropics/skills`, `skills/theme-factory/` | No shipped copy since the design consolidation: four preset palettes continue as directions Q to T of `plugins/office/skills/design/references/directions.md`; pin, retirement note and Apache notice in `design/references/theme-factory-upstream.md` and `LICENSE-theme-factory-APACHE-2.0.txt`. No sync obligation. |
| `office` (PPT Visual composition snapshot) | `claude-office-skills/skills`, `ppt-visual/SKILL.md` | Region sketches and the sketch-to-specification handoff inside `plugins/office/skills/pptx/references/layout-patterns.md` (Provenance section) and `LICENSE-ppt-visual-MIT.txt`; manual on-demand review only, preserve the pattern mapping and `office:design` palette ownership |

## How to sync a plugin

For copied-source rows only, the sync table above gives the upstream repo and local target files. Inspiration-only rows retain provenance and are not fetched or merged by this procedure. Single-file pattern:

```bash
gh api "repos/<owner>/<repo>/contents/<upstream-path>" --jq '.content' | base64 -d
```

For directories, list children first then iterate:

```bash
gh api "repos/<owner>/<repo>/contents/<dir>" --jq '.[].name' | while read f; do
  gh api "repos/<owner>/<repo>/contents/<dir>/$f" --jq '.content' | base64 -d
done
```

After fetching, compare with the local kernel file, preserve local additions
(attribution headers, frontmatter conventions, namespace replacements,
no-dash-aside style), then follow the version, rebuild, verification and authorized
publication steps above.

**Non-obvious per-plugin sync notes** (read alongside the sync table):

- **`domain-hunter`**: upstream Step 3 uses dedicated Twitter/Reddit Python scripts. Replace with `WebSearch` queries targeting `site:x.com` / `site:reddit.com`.
- **Office editorial/typography**: copied-source adaptations from Agentit, not an import of its harness. Compare original source at the recorded pin before merging. Preserve native DOCX styles and flow, fixed-canvas editable PPTX, installed-font checks, actual saved-file renders, existing Office production ownership and harness image tools. Retain Apache terms and both MIT adaptation notices; inspect upstream lineage changes before advancing the pin. Do not restore unrelated Agentit skill names, extra agents or a second reporting pipeline.
- **Office Theme Factory**: retired as a skill. Do not restore the preset files, the showcase or a palette preset selection; palettes are built per file by `office:design`'s `palette.py`. Only the four seed palettes and their Apache notice remain.
- **Office design snapshots**: editorial/typography, Theme Factory and PPT Visual have no periodic sync obligation and are excluded from generic batch checks. Review manually when explicitly requested or when a concrete defect needs upstream evidence. PPT Visual contributes region sketches inside the layout patterns, not a separate reference, skill, engine or palette. Word's `document-design.md` is original guidance informed by `tivojn/Office`; its provenance is not a copied-source target. Preserve the two format designers and reviewers, the shared `office:design` record, native-object constraints and harness image ownership.

## Historical notes for the retired superpowers port

The following record describes the former `obra/superpowers` VS Code port. Its references to `this port`, retired files, `sp-*` agents and VS Code mechanisms describe decisions made during that pass, not active instructions. Preserve the dated history and attribution; do not reimport the port, recreate its files or reconstruct its extension apparatus.

**Sync notes from the 6.2.0 to 6.3.0 pass (2026-08-20)**, all applied with `git merge-file` against the pinned base rather than by overwriting:

- The two `references/*-tools.md` changes are out of scope as always, and so is the upstream Hermes line in `using-superpowers/SKILL.md`: this port replaces the whole "Platform Adaptation" section with "How skills work here", so there is no list to add a harness to.
- `visual-companion.md`'s 6.3.0 change edits the **Copilot CLI** launch block. This port collapsed all five per-platform blocks into one, so the hunk has no target here and was skipped.
- `render-graphs.js` was converted to ESM upstream, which is correct there (`"type": "module"` in the upstream `package.json`) and broken here: the export ships no `package.json` next to it, so `.js` is CommonJS and `import` would not parse. The two substantive 6.3.0 fixes (`execFileSync` instead of `execSync`, and probing `dot -V` instead of `which dot`, which is not a command on Windows) were taken; the `require` calls were kept, with a comment in the file saying why.
- The upstream "Waiting on dispatched subagents" paragraph in `subagent-driven-development/SKILL.md` assumes detached children and a wait interface. VS Code's `#agent/runSubagent` returns only when the subagent finishes, so it was replaced with a paragraph stating that and keeping the useful half (do local work between dispatches).
- The new "You Do Not Dispatch Subagents" section in the four `*-prompt.md` templates maps onto the `sp-*` agents, which all ship `agents: []`. The section was added in a shortened form that names the empty allowlist as the mechanical reason, rather than mirroring upstream's prose about a risk this platform already forecloses.
- Two graphviz conflicts in `subagent-driven-development/SKILL.md` resolved in favor of upstream's node renames (`Ask human partner which governs` becomes `Rule on the conflict, ledger the ruling`) while keeping this port's fix-round wording, which says a fresh implementer is dispatched every round because VS Code cannot resume a returned subagent.

## Current Kotlin sync note

- **`Jeffallan/claude-skills` (kotlin)**: strip extra upstream frontmatter fields (`license`, `metadata.author`, `version`, `domain`, `triggers`, `role`, `scope`, `output-format`, `related-skills`). Drop the trailing `[Documentation](https://jeffallan.github.io/...)` link. Preserve single-connector em-dashes (`X — Y`) inside code comments; they are not bracketed asides.
