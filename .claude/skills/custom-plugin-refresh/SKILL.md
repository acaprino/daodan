---
name: custom-plugin-refresh
description: >
  Maintenance protocol for hand-authored plugins that have no upstream to diff against:
  the four freshness risk classes and their cadences, where hard-coded versions hide, the
  re-research and surgical-edit update protocol, the refresh commit tag, and triage for
  picking what to refresh next.
  TRIGGER WHEN: the user asks to refresh, re-research, or fact-check a plugin that is not in
  the copied-source sync targets of the `upstream-sync` skill; asks which plugins are stale or overdue; or
  asks about version drift in plugin knowledge bases.
  DO NOT TRIGGER WHEN: the plugin has copied-source sync targets (use `upstream-sync` for those targets), the task is a
  first-time vendor of external content (use `external-repo-intake`), or the task is
  mirroring our content outward (use `downstream-exports`).
---

# Custom plugin maintenance

A "custom plugin" has hand-authored or research-grounded content without a copied upstream source to re-pull. Copied-source targets in the `upstream-sync` table use that skill for upstream comparison. Inspiration-only rows retain provenance without excluding the original local plugin from this refresh method: both `codebase-map` rows are inspiration-only, so refresh its local content here. Preserve existing copied-source tracking and history; neither route authorizes new vendoring.

Custom plugins decay differently than vendored ones. There is no upstream commit to diff against. Versions, framework recommendations, breaking-change notes, and "current as of 2026" claims become stale silently. The maintenance protocol below is the antidote.

Refresh the hand-authored kernel under `plugins/<name>/`: `plugin.toml`, `roles/`,
`workflows/` with their TOML sidecars, `skills/`, `contracts/` and `policies/`.
Host mechanisms live under `adapters/`. Exports and root marketplace catalogs are
generated; correct their source and rebuild rather than editing package copies.

## Freshness risk classes

Classify each plugin into one of four classes. The class determines refresh cadence and triage priority.

| Class | What it tracks | Typical cadence | Examples |
|---|---|---|---|
| **Very fast** | Versions bump every few months; breaking changes are common; ecosystem reshuffles | Every 3 months | rag-development (embedding models, rerankers, vector DBs), digital-marketing/ga4-implementation (Consent Mode, GA4 events), react-development (React 19, Vercel guidance) |
| **Fast** | Framework releases 2-3x per year; APIs evolve | Every 6 months | libgdx-development, opentelemetry, tauri-development, stripe (API additions, webhook event types), grabber-development (anti-bot vendor moves), browser-extensions, pwa-expert (browser version churn, WebKit feature rollout, framework PWA library churn), text-humanizer (Wikipedia's signs page and the upstream humanizer both change monthly), business (its `privacy-doc-generator` quotes app store rules and EDPB guidance; see its refresh note below) |
| **Moderate** | Major releases ~yearly; breaking changes rare | Every 12 months | trading-broker-integration, csp (OR-Tools), python-development, typescript-development, messaging (RabbitMQ majors), obsidian-development, abstraction-architect (theory is stable; URL list in further-reading.md decays on a yearly cadence) |
| **Slow** | Workflow knowledge that ages by behavior change, not version bumps | Opportunistic; review only when symptoms appear | project-lifecycle, project-protocol, senior-review, project-knowledge, team pipeline workflows, marketplace-ops, system-utils, learning, research, clean-code, codebase-map, platform-engineering, testing methodology, xterm, app-analyzer |

If unsure, default to "Fast" (6 months). Reclassify after the first refresh based on how much actually changed.

**`ai-tooling` is the exception to its own class.** Its workflow content is Slow, but `agent-sdk-builder` documents an SDK that ships breaking changes between minor releases, which puts that skill in **Very fast** (every 3 months). A 2026-08-10 fact-check found five drifted API claims at once: `fork_session` had changed type, `plugins` had changed from paths to config objects, `thinking` had moved to object-only shapes, the TypeScript V2 preview had been removed outright, and the migration guide's settings-source default had been superseded. Refresh the SDK skill on the fast cadence even when nothing else in the plugin has moved. Since ai-tooling 5.2.0 the same cadence applies to the `prompt-engineering` skill's `references/model-guidance.md` and to the model-class table in its `SKILL.md`: both quote vendor pages (thinking modes, effort names, prefill, cache multipliers, structured-output support, Gemma templates) that the 2026-09-05 refresh found had moved in six places since July.

## Version-sensitive content: refresh the policy, not only the fact

A refresh that corrects today's facts leaves the same trap set for the next reader. Where a plugin documents a fast-moving external API, the durable fix is a source-of-truth policy plus a classification of its own claims, so the content tells the agent which of its statements not to trust. `ai-tooling` 5.0.0 is the worked example: a decision core carrying the tiers (the project's installed SDK, then current official documentation, then the bundled references) with the volatile detail moved into on-demand reference files, and a STABLE / API-SENSITIVE / MODEL-SENSITIVE table.

Two mechanics from that pass are reusable:

- **Mark what you could not confirm.** A claim that fails documentation resolution during a refresh is unconfirmed, not confirmed-absent. Tag it `*(verify)*` in place instead of deleting it or leaving it to read as verified. The tag is also the next refresh's work queue.
- **Prefer relative and substituted paths over repo paths.** `${CLAUDE_PLUGIN_ROOT}/...` and skill-relative `references/...` survive installation; `plugins/<name>/...` resolves only in a checkout of this repo. `python scripts/lint_bundled_paths.py` enforces this against shipped resources; its bundled-path baselines are empty. Cross-plugin consumers load the owner's named skill instead of reaching into its files.

Where a refresh produces a behavioral invariant worth keeping (the frontier is never auto-picked; the installed SDK outranks the bundled reference), add a case to that plugin's harness under `evals/` rather than trusting the next reader to notice. `evals/ai-tooling/` is the pattern.

## Where hard-coded versions hide

Predictable hot spots, in priority order:

1. **Agent body** -- "Core Knowledge" / "Library Landscape" sections list package names and versions
2. **SKILL.md** -- "Quick Start" steps name install commands with versions
3. **References** -- changelog / breaking-changes sections; benchmark numbers; "as of YYYY" lines
4. **Audit command** -- checklists referencing specific version-gated features
5. **plugin.toml description** -- if the description name-drops versions (e.g. "RabbitMQ 4.x coverage"); catalogs derive it from this declaration

The agent and SKILL.md are the highest-value targets per minute of refresh effort. Reference files matter less for typical users (progressively disclosed) but matter most for power users.

## Update protocol

Steps to refresh a custom plugin. Same protocol regardless of risk class; only the cadence differs.

1. **Re-research the domain** with `research:deep-researcher`. Prioritize primary and recency sources in `Source families` at minimum. Prompt template (the spawn-block fields the agent's INPUT section expects, filled):
   ```
   Role: researcher
   Objective: <framework> current version, breaking changes since <version-in-plugin>, recommended
   baseline versions of dependencies, deprecations, ecosystem changes. Focus on facts that would
   change recommendations in an existing knowledge base.
   Boundaries: none
   Source families: official/primary docs and changelogs, recency (release notes, migration guides)
   Domain hint: <framework/domain>
   Backend: auto
   Budget: 15 searches / 12 pages / 4 rounds
   Return format: the researcher report
   ```
   Optional: add community sources to `Source families` if real-world usage patterns are part of what you cover.

2. **Diff the findings against the plugin**. Spawn Explore agents to grep the plugin for the specific version strings and section titles that came up in research. For each, decide:
   - **Clear win**: outdated fact with a confirmed replacement, apply Edit
   - **Subtle shift**: framework changed defaults but old approach still works, mention both
   - **No change**: research confirmed our content is still accurate
   - **Open question**: research was inconclusive, leave a comment and revisit next cycle

3. **Surgical Edits only**. Do not rewrite whole files. Replace specific lines and sentences. Preserve structure so future refreshes have stable anchors.

4. **Bump versions**. Bump `version` in each changed kernel's `plugin.toml`: patch for fact updates (`1.2.3 -> 1.2.4`), minor if a new section, file, or reference was added (`1.2.3 -> 1.3.0`). Bump `metadata.version` in `.claude-plugin/marketplace.json` too (patch is fine unless the marketplace shape itself changed). This metadata field is the compiler's version input; the catalog entries remain generated. Rebuild every host with `python scripts/daodan_build.py` and regenerate the component/dependency reference with `python scripts/sync_plugin_docs.py` when a kernel changes. Before publication, run `python scripts/daodan_build.py --check`, `python scripts/sync_plugin_docs.py --check` and the required repository gates.

5. **Retain the evidence, not only the conclusion.** A refresh retains three files under `docs/superpowers/specs/`, beside its design record and named for the same date: the research prompt as it was run, the researcher's report verbatim, and a per-source verification file saying which sources were checked against their primary pages, which were corrected, and which were not verified at all. Each carries the sha256 of its body.

   This is a retention rule, not a courtesy, and it exists because a refresh's design record cannot carry it. A record states in one line that the sources were verified; only a per-source file can tell a later maintainer that five of them were not, and that one of those five still carries a claim in a shipped body. Without it, the next reader has to trust an aggregate or repeat the source review. The research run's own output directory does not count: `.peer-review/` and the scratchpad are both outside git, so a fresh clone has neither. A source that failed verification is marked `*(verify)*` where it is cited, and the verification file is where a reader learns that the mark is not decoration.

6. **Commit only with current task authorization**, using a refresh tag. Format:
   ```
   Refresh <plugin-name> for <framework> v<new-version> (v<plugin-version>)
   ```
   Commit the changed kernels, evidence and all regenerated exports/catalogs and documentation references together. If repository workflow skills changed, regenerate their native Codex adaptations with `python scripts/sync_codex_instructions.py` and check parity with `--check`. This makes the git log a searchable record of which plugins got attention when. Use this to decide what to refresh next: anything not touched in a full risk-class cadence is overdue.

## Triage on demand

When you sit down to do a refresh pass and don't know where to start:

```bash
# Plugins not refreshed in the last 6 months
git log --since="6 months ago" --name-only --pretty=format: -- plugins/ \
  | grep -v "^$" | awk -F/ '{print $2}' | sort -u > /tmp/recently-touched.txt

# Compare against plugins/*/plugin.toml, the authoritative kernel inventory.
# The difference is your work queue.
```

Refresh the "Very fast" and "Fast" classes first if any are on the work queue; defer "Moderate" and "Slow" classes unless something specific prompted the review.

## Per-plugin refresh notes

### business: `privacy-doc-generator`

The role runs its own research at generation time (Phase 0 regulatory delta, Recency Validation, vendor pages fetched in Codebase Evidence), so a fact the user's run re-fetches does not need a refresh. The refresh covers what runtime research never touches: the hard-coded lists and the document identifiers the body cites. Cadence: store block every 3 months, normative block every 6, in `plugins/business/roles/privacy-doc-generator.md`.

**What to check, by speed of change:**

1. **Store rules** (sections "App Store Privacy Disclosures Structure", "App checks", "App distribution"). Compare the data type lists, purpose lists, URL requirements, account deletion rules and deadlines, App Tracking Transparency wording and the list of SDKs that need an Apple privacy manifest against the primary pages: Play Console Help articles 10787469 (Data safety), 10144311 (User Data policy), 13327111 (account deletion), the Google Play SDK Index, Apple App Store Review Guidelines 5.1.1 and 5.1.2, Apple "App privacy details", the privacy manifest documentation and `developer.apple.com/support/third-party-SDK-requirements/`. An article number that stopped resolving is a finding: replace it, never leave it.
2. **EDPB and Garante guidance** (section "KEY NORMATIVE SOURCES"). For each guideline cited, confirm the current version number and adoption date on edpb.europa.eu; look for new guidelines on consent, dark patterns, transfers, DPIA, legitimate interest and Art. 5(3) ePrivacy. On garanteprivacy.it check the cookie guidance, the DPIA list and the yearly provvedimenti the body names. Cross-check with ico.org.uk and cnil.fr only to notice what the EDPB has not yet written.
3. **Transfers**: validity of the EU-US Data Privacy Framework (Decision 2023/1795), new adequacy decisions, SCC revisions (Decision 2021/914), CJEU rulings on curia.europa.eu.
4. **Non-EU modules**: CPRA regulations, LGPD and FADP amendments, new US state laws the module does not yet cover.
5. **Sector facts**: telemedicine, TULPS art. 109, e-commerce D.Lgs. 70/2003, Directive 2019/770, the ePrivacy Regulation if it is ever adopted, the Italian Codice Privacy on normattiva.it.

**Sources, in order of authority:** legal texts (EUR-Lex, normattiva.it, fedlex.admin.ch), authorities (edpb.europa.eu, garanteprivacy.it, then ico.org.uk and cnil.fr), the court (curia.europa.eu), store primary pages, the SDK vendor's own privacy page. Never a third-party aggregator, a law firm summary or an SDK list kept by someone else.

**Procedure:** run the update protocol above with `research:deep-researcher` scoped to the five themes, then edit only the lists and identifiers that moved, record each new fact with its source and date in the body's bracketed citation style, keep `docs/plugins/business.md` aligned and bump `business` by a minor version when a list changes, a patch version when only an identifier or date does.

## When an external owner overlaps with a custom plugin

Evaluate declared delegation or original local inspiration through
`external-repo-intake`. Standing policy forbids new vendored copies: do not add a
sync-table row or copy upstream text during refresh. Check the provider's actual
availability, canonical contract and execution on the active host. Preserve
existing licenses, attribution, tracked rows and retirement history; changing
their disposition requires a separate scoped authorization.
