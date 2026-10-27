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

### Delegated executable updates

Worktrunk is maintained as an external executable through
`worktree-manager:worktree-method`, `references/upstream.md`. Include Worktrunk
in generic upstream-update requests and requests naming it. Run its bundled
`worktrunk_runtime.py upstream-check`, compare the pinned release with upstream,
and follow that method's isolated compatibility probes before advancing
`references/upstream.json` or activating a binary. Preserve original Daodan
catalog, review and authorization behavior. Report discovered, supported and
installed versions separately. No Worktrunk source is copied and no copied-source
sync-table row is added; a new release alone never authorizes bypassing tests or
silently replacing the supported runtime. This is on-demand dependency maintenance,
not a scheduled monitor.

### Copied-source updates

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

7. **Version bump and rebuild** - bump each touched plugin's `version` in `plugins/<name>/plugin.toml`; `metadata.version` changes only for a release the user asks for. Rebuild every host with `python scripts/daodan_build.py` and regenerate the component/dependency reference with `python scripts/sync_plugin_docs.py` when a kernel changes; catalog entries and exports are generated, never hand-merged.

8. **Verify and commit** - run `python scripts/daodan_build.py --check`, `python scripts/sync_plugin_docs.py --check` and the required repository gates before publication, check named consumers and bundled paths, then inspect `git status` / `git diff --stat`. If repository workflow skills changed, regenerate their native Codex adaptations with `python scripts/sync_codex_instructions.py` and check parity with `--check`. Commit kernels, regenerated exports/catalogs, documentation references and instruction copies together with a descriptive message like "Sync upstream updates for X and Y (vN.N.N)". Push to master under the task's publication authorization.


Rows marked `(inspiration)` are inspiration-only provenance, not copied-source sync targets. Keep their source attribution and adoption history here, but exclude them from vendored pull, merge and sync. A row that records an upstream commit is also a watch: `custom-plugin-refresh` reads the upstream diff since that commit and advances it (see `external-repo-intake`, step 7). The two `codebase-map` rows predate watches and record no commit. Their presence does not exclude the original local `codebase-map` plugin from `custom-plugin-refresh`. Existing copied-source rows remain tracked; this inventory does not authorize new vendoring.

| Plugin | Upstream source | Files to sync |
|--------|----------------|---------------|
| `codebase-map` (inspiration) | `gsd-build/get-shit-done` - `agents/gsd-codebase-mapper.md` | `plugins/codebase-map/workflows/analyze.md` (patterns adopted, not direct copy) |
| `react-development` (react-best-practices) | `vercel-labs/agent-skills` - `skills/react-best-practices/` | `plugins/react-development/skills/react-best-practices/SKILL.md`, `plugins/react-development/skills/react-best-practices/references.md`, `plugins/react-development/skills/react-best-practices/rules/*.md` |
| `digital-marketing` (domain-hunter) | `ReScienceLab/opc-skills` - `skills/domain-hunter/` | `plugins/digital-marketing/skills/domain-hunter/SKILL.md`, `plugins/digital-marketing/skills/domain-hunter/references/registrars.md`, `plugins/digital-marketing/skills/domain-hunter/references/spaceship-api.md`, `plugins/digital-marketing/skills/domain-hunter/examples/auto-video-editing-domain.md` |
| `docker` (multi-stage-dockerfile) | `github/awesome-copilot` - `skills/multi-stage-dockerfile/SKILL.md` | `plugins/docker/skills/multi-stage-dockerfile/SKILL.md` |
| `codebase-map` (semantic-interconnect-mapper) | `wshobson/agents` - `plugins/agent-orchestration/agents/context-manager.md` (pattern cherry-picked, not a direct copy) | `plugins/codebase-map/roles/semantic-interconnect-mapper.md`. Owned by `senior-review` until marketplace 16.0.0. |
| `typescript-development` (mastering-typescript) | `SpillwaveSolutions/mastering-typescript-skill` - `mastering-typescript/` | `plugins/typescript-development/skills/mastering-typescript/SKILL.md`, `plugins/typescript-development/skills/mastering-typescript/references/*.md`, `plugins/typescript-development/skills/mastering-typescript/scripts/validate-setup.sh`, `plugins/typescript-development/skills/mastering-typescript/assets/tsconfig-template.json`, `plugins/typescript-development/skills/mastering-typescript/assets/eslint-template.js`. Adaptation on sync: SKILL.md frontmatter is rewritten to local convention (keep only `name` and `description`; strip upstream `version`, `category`, `triggers`, `author`, `license`, `tags`). Description uses `description: >` multiline form with explicit TRIGGER WHEN / DO NOT TRIGGER WHEN routing, scoping this skill to enterprise/advanced TS work (advanced type system, JS-to-TS migration, toolchain bootstrap, Zod, deep React + TS, NestJS, LangChain.js) and routing routine TS/JS writes to `typescript-development:typescript-write`, React perf to `react-development:react-best-practices`, and dead-code to `typescript-development:knip`. Without this rewrite the skill failed to auto-activate on its core scenarios because upstream's single-paragraph "Use when..." description loses the router race against `typescript-write` (added in v2.1.0). The local `Source: ...` attribution line at the top of SKILL.md and the body content are NOT subject to upstream-driven frontmatter changes on future syncs. |
| `kotlin-development` (full vendor, MIT) | `Jeffallan/claude-skills` - `skills/kotlin-specialist/` | `plugins/kotlin-development/skills/kotlin-specialist/SKILL.md`, `plugins/kotlin-development/skills/kotlin-specialist/references/{coroutines-flow,multiplatform-kmp,android-compose,ktor-server,dsl-idioms}.md`. Adaptation on sync: strip upstream extra frontmatter fields (`license`, `metadata.author`, `version`, `domain`, `triggers`, `role`, `scope`, `output-format`, `related-skills`); keep only `name` and `description` in local frontmatter; rewrite upstream single-paragraph `description` into local `description: >` multiline form with TRIGGER WHEN / DO NOT TRIGGER WHEN. Add MIT attribution header comment immediately after the frontmatter on SKILL.md and at the top of every reference file. Drop the upstream `[Documentation](https://jeffallan.github.io/...)` link at the bottom of SKILL.md. Single-connector em-dashes ("X - Y") in code comments are preserved as-is (they are NOT bracketed asides). |
| `project-knowledge` (Karpathy principles, MIT) | `multica-ai/andrej-karpathy-skills`: `skills/karpathy-guidelines/SKILL.md` | Principles 1-4 retain upstream attribution in `plugins/project-knowledge/skills/instructions-method/references/working-principles.md`. Their sub-bullets and principle 5 are local. Creation uses the block when equivalent project guidance is absent; maintenance preserves equivalent guidance. Update the canonical reference and the instruction example together when their shared facts change; generated instruction files remain the target project's concern. |
| `office` (editorial and typography) | `marcmarti9/agentit`, `skills/editorial-design/SKILL.md` and `skills/typography-and-layout/SKILL.md` | `plugins/office/skills/design/references/editorial-design.md` and `references/typography.md`; source pin, modifications and retained Apache/MIT notices in `design/references/agentit-upstream.md` |
| `office` (Theme Factory, retired) | `anthropics/skills`, `skills/theme-factory/` | No shipped copy since the design consolidation: four preset palettes continue as directions Q to T of `plugins/office/skills/design/references/directions.md`; pin, retirement note and Apache notice in `design/references/theme-factory-upstream.md` and `LICENSE-theme-factory-APACHE-2.0.txt`. No sync obligation. |
| `office` (PPT Visual composition snapshot) | `claude-office-skills/skills`, `ppt-visual/SKILL.md` | Region sketches and the sketch-to-specification handoff inside `plugins/office/skills/pptx/references/layout-patterns.md` (Provenance section) and `LICENSE-ppt-visual-MIT.txt`; manual on-demand review only, preserve the pattern mapping and `office:design` palette ownership |
| `office` (open-slide PPTX exporter, MIT) | `open-slide/open-slide` - `packages/core/src/app/lib/pptx/` and `packages/core/src/app/lib/sdk.ts` at commit `82349cf2d07d37b75975170503a82fcaacae9298` (`@open-slide/core` 2.3.1) | The eleven verbatim files under `plugins/office/skills/pptx/lib/open-slide-pptx/src/lib/`, with the generated `bundle/open-slide-pptx.js` and `manifest.json`. Pin, notices, exclusions and the refresh protocol are in that directory's `UPSTREAM.md`. The bundle also carries `fflate` and `html-to-image` (MIT) at the versions pinned in `build.deps.json`; check both for fixes on every review. Manual on-demand review only: advance the pin deliberately in `build.deps.json`, re-copy verbatim, run `node rebuild.mjs`, then the conversion fixture and the Office suite. `entry/office-entry.ts`, `driver.mjs`, `rebuild.mjs` and `scripts/pptx_convert_bridge.py` are Office code and a sync never overwrites them. This row exists under an explicit owner authorization scoped to those files. |
| `office` (inspiration, MIT) | `alchaincyf/huashu-design`, `references/design-styles.md`, `references/typography.md` and `references/directions.md`, read at commit `4fc7bfdbd5ec3fa2d43ce7a6433de60976a5e4b1` | Ideas only: the sample/converge/justify palette derivation, OKLCH chroma bands, temperature spread and default-look pitfalls in `plugins/office/skills/design/references/directions.md`; contrast sources, pairings 13 to 18, the overused-face table and display thresholds in `references/font-pairings.md`. Its HTML production, `html2pptx`, animation and web modules are excluded by the native-object contract; nothing is copied or fetched. Watch: `custom-plugin-refresh` reads the diff since that commit and advances it. |
| `office` (inspiration, MIT) | `cathrynlavery/diagram-design`, `skills/diagram-design/references/style-guide.md`, read at commit `97d795138448f6a739a0cebc3d9beb37a42077f1` | Ideas only: role-based diagram colours, seven node treatments, one-accent rule, stroke weights, grid snapping and label hierarchy, re-expressed in points for native shapes in `plugins/office/skills/design/references/diagram-style.md`. Its HTML/SVG pipeline, importers, exporters and web fonts are excluded; a raster export never replaces a required editable diagram. Watch as above. |

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
- **Office design snapshots**: editorial/typography, Theme Factory and PPT Visual have no periodic sync obligation and are excluded from generic batch checks. Review manually when explicitly requested or when a concrete defect needs upstream evidence. PPT Visual contributes region sketches inside the layout patterns, not a separate reference, skill, engine or palette. Word's `docx/references/layout-patterns.md` is original guidance informed by `tivojn/Office`; its provenance is not a copied-source target. Preserve the two format designers and reviewers, shared content/design records, native-object constraints and harness image ownership. See `plugins/office/README.md` for the source and license index.
- **Office open-slide exporter**: the only Office copied-source row and the only bundled engine, so a sync is code work, not prose merging. Advance the pin, and the `fflate`/`html-to-image` versions when they need fixes, in `build.deps.json`, which is the only place the pin is data; re-copy the eleven pinned files verbatim, keep `entry/office-entry.ts`, `driver.mjs`, `rebuild.mjs` and `scripts/pptx_convert_bridge.py` untouched, run `node rebuild.mjs` so `manifest.json` and the bundle move together, update every prose record that states the pin (listed in `UPSTREAM.md`), then convert the fixture in `tests/fixtures/office/pptx-convert/design.html` and run the Office suite. The hash guard fails an edited vendor; a local fix belongs in the Office entry or driver. Excluded upstream stays excluded: `pptx/render.ts`, upstream tests, the application, CLI, Vite plugin and React tree.

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
