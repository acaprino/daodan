# Unified Office content and visual design implementation plan

Approved requirement: [Office evolution relation](2026-10-26-office-unified-system.md), as corrected and approved in this conversation. Execution is authorized. Workspace: existing `master` checkout, sequential product changes, with preexisting edits protected. Commit and publication remain outside the recorded fix grant.

## Outcome and constraints

Produce one shared editorial method, an explicitly validated `CONTENT.md` and `DESIGN.md`, a real-content HTML comparison of complete visual proposals, and independent DOCX/PPTX composition using the existing native producers. Preserve the existing PPTX plan schema, inspectors, palette mathematics, font tools, native template kit, five roles, candidate identity and independent rendered review.

New work designs its visual identity from its brief. Revisions inherit accepted decisions. Separate DOTX/POTX generation is optional unless a reusable template is requested. No new upstream source or engine is copied, installed or selected. Existing licenses remain bundled. New contributions wait for the paired vertical proof and an evidenced gap.

Use Python standard library and current project conventions. Shared helper contracts below are implementation decisions within the approved requirements, not additional product scope.

## Acceptance examples

- A technical brief, actual project logo and source-backed claims produce a shared editorial record, distinct document and deck projections, two visual proposals on identical real samples, an explicit selected design, native DOCX/PPTX candidates and inspected saved renders.
- A DOCX-only request produces no implicit PPTX projection or sample. A local edit retains accepted content/design and does not enter visual selection.
- Duplicate/unknown source, claim or unit IDs, missing core-claim destinations, incomplete design fields, stale projection bindings, invalid colours/CSS inputs, input/output aliasing and existing output files fail without replacing artifacts.
- Structural validation binds records and mappings. It does not establish semantic source fidelity, native editability, target-application fidelity or visual quality.

## 1. Shared editorial and record contracts

Files: new `plugins/office/skills/content/SKILL.md`, `references/records.md`, `scripts/office_records.py`; new `tests/test_office_records.py`.

The content skill owns editorial dimensions, source/claim ledger, transformation permissions, logical sequence and format projections. It loads only the requested format projection reference. Existing `content-strategist` will consume this method in step 3.

`office_records.py` owns record serialization and structural validation. Public interfaces:

```python
load_record(path: Path) -> dict
validate_content(record: dict, *, pptx_plan: dict | None = None) -> list[str]
validate_design(record: dict, *, require_selected: bool = True) -> list[str]
write_record(record: dict, path: Path) -> None
```

JSON input and a single fenced JSON object in Markdown use the same record. Reject duplicate JSON keys, non-finite numbers, oversized/malformed records and unsafe output replacement. CLI `validate INPUT [--pptx-plan PLAN]`; `write INPUT --out RECORD.md` writes a new artifact only. Serialize actual data, without a second manually synchronized schema or report authority.

`office/content/v1`: `project_id`, positive integer `revision`, editorial `brief` (operation, intent, goal, audience, market, channel, formats, scope, depth, extent, density, tone, transformation), `sources` (stable ID, path, SHA-256, role), `claims` (ID, text, priority, source-ID/locator pairs, locked flag, conditions/conflicts), `units` (ID, message/text, claim IDs, relationship, detail, transformation), `sequence`, `projections`, `transformations`, `gaps` and approved `exclusions`.

DOCX projection: structure plus sections with stable IDs, titles and unit IDs. PPTX projection: path/hash of the existing plan and slide-to-unit placements; validate referenced slide/claim IDs against the supplied plan, without introducing a second slide schema. Core claims reach every requested format except an explicitly authorized exclusion. Validate IDs, references, transformation modes, requested-format coverage, mappings and revision linkage.

`office/design/v1`: `project_id`, positive `revision`, `content` identity/revision, `formats`, `direction` (name, idea, principles), `palette` (existing helper role/value output plus provenance/proportions), `typography` (heading/body/caption font roles and fallbacks), `spacing`, `imagery`, `data`, `components`, `adaptations` and `selection`. Selected records require candidate ID, authority (`user` or `autonomous`) and decision source. Proposal validation may omit selection; final record validation may not. Validate structure, requested formats, required visual roles and safe colour/font/style values without claiming runtime capability.

Verification: behavioral record tests exercise valid paired/single-format records, malformed and inconsistent references, locked transformations, core coverage, plan linkage, missing theme roles, selection authority, file preservation and parser boundaries. Run the failing new tests before implementation and retain the failure evidence.

## 2. Full visual-system comparison

Files: new `plugins/office/skills/design/scripts/design_compare.py`, `plugins/office/skills/design/references/records.md`, `tests/test_office_design_compare.py`. Reuse step 1's helper through its bundled sibling skill; retain `palette.py` and `palette_preview.py` as their current independent tools.

Input `office/design-candidates/v1`: shared `project_id`, requested `formats`, real `sample` (title, lead, dense body, source note and source-linked comparison/data table; local image when supplied), and two or three uniquely identified proposals carrying `office/design/v1` records. Every proposal uses the same sample. Typography, hierarchy, spacing, image/data treatment and palette must visibly differ according to the proposal, while requested brand constraints remain recorded. A complete comparison demonstrates dense text, evidence and comparison/table treatment. Missing material is an explicit gap, never invented data.

CLI: `design_compare.py INPUT --out COMPARE.html`; selection: `design_compare.py INPUT --select ID --authority user|autonomous --source TEXT --out DESIGN.md`. Selection is an explicit command from the coordinator after the user's answer or authorized autonomy; browser highlighting alone records no approval. The chosen record carries its exact candidate identity. A requested compatible combination becomes a new explicitly authored candidate with parent candidate IDs and a new revision; validate and preview that combined record before selecting its ID. No automatic merge invents design decisions.

Output is a self-contained, keyboard-accessible HTML comparison using reusable fixed presentation code and validated proposal data. Render only requested format samples, escape content, constrain CSS values and local image handling, preserve files on errors/aliasing, and retain a clear preview-only statement. No invented metrics, stock sample claims, remote dependency, browser automation or external font fetch is introduced.

Verification: same-content comparison; requested-format-only output; actual font/direction/style differences; safe text/font/colour/image handling; missing samples/records; explicit/autonomous choice; no overwrite; no implied saved-Office fidelity. Exercise the HTML in the available browser and inspect both formats.

Test authoring uses the canonical `testing:test-writer` role in separate sequential deliveries before the corresponding Python implementation. The Python specialist consumes the failing behavioral tests and writes production helpers and their owning guidance only. Existing instruction-contract test updates follow workflow integration, preserving their independent protections.

## 3. Wire ownership, naming and existing workflows

Product files: `plugins/office/plugin.toml`; content strategist; both designers/reviewers; intake and routing; design method and editorial/typography references; DOCX/PPTX methods and projection references; WordCraft/DeckCraft reader handoffs; Daodan `document`, `presentation`, `start` and `theme` entries and their required dispatch sidecars.

- Register `content`; reuse the existing content-strategist for both formats and add it to document dispatch. Combined delivery reuses content/design identities and prepares only required projections. Skip replanning on restyle/edit/review/export.
- Reduce design to visual-system decisions and the shared HTML/selected-design record. Content owns logical strategy, while format designers finalize composition/patterns/geometry. Keep required source reading and independent review.
- Move DOCX `document-types.md` to `structure.md` and `document-design.md` to `layout-patterns.md`. Split PPTX `design-library.md` into `structure.md` and its existing `layout-patterns.md`. Preserve native recipes, constraints, object contracts and attribution. Update all operational callers; remove superseded copies.
- Preserve palette extraction, custom seed generation, previews, fonts and template tools. Native producers consume the selected records, materialize their styles/themes/masters, and retain separate-candidate, reopen, preservation, embedding and exact-render review requirements.
- Record operation/material roles and phase-specific dependency availability, actual versions, licenses, capability probes and recovery in the existing brief. Resolve blockers only for dependent deliveries.

Preserve independent existing tests. Update only assertions invalidated by the approved ownership/name/template change. Add all-five-host tests through actual rendered entries, roles, nested references and dispatch resources, including negative isolation/capability cases. Scope product edits sequentially, with exact file ownership per worker handoff.

Canonical upstream provenance references affected by path relocation need a separate scoped auxiliary work record for `.claude/skills/upstream-sync/SKILL.md` and its generated `.agents` adaptation, because those files are outside the main record's immutable scope. This does not open a copied-source target. Run instruction parity before and after; protect preexisting canonical/Codex instruction edits.

## 4. Licensing, review and publication candidate

Add `plugins/office/README.md` indexing existing copied adaptations, original inspiration and delegated runtimes with paths, pins, licenses, modifications and retained texts. Keep full notices under shipped skill references. Align `docs/plugins/office.md` and the relation's final-delivery list, adding the HTML comparison explicitly.

Bump Office minor version for the new skill/contracts, bump Daodan for its changed dispatch/entry contract and increment marketplace metadata. Build all five hosts through the compiler, regenerate plugin docs and check reproducibility/parity. Preserve unrelated edits; verify protected bytes rather than restoring from HEAD.

Run affected record/renderer tests and the full Office suite with an owned temporary directory. Then run the repository's consistency commands and full suite against this actual candidate, retaining bounded logs and reporting unavailable checks. Compute review rosters using the canonical helper; independently review the plan and final candidate, resolving eligible findings before delivery. Structural/compiler evidence stays distinct from installed-host execution.

## 5. Paired vertical proof

Use the repository's real Office technical material and existing Daodan logo. Bind sources by hash and locators. Generate the shared content record, a DOCX section projection, the preserved PPTX plan, two ad hoc visual proposals, one comparison HTML and an explicitly autonomous selection for this engineering verification (not an implied user design preference).

Installed WordCraft/DeckCraft are 0.8.0. Use the preflight's verified argv transport and command schemas. Produce native editable candidates with meaningful real content, a source-backed table and logo. Reopen and inspect saved files, render every page/slide, obtain independent content/layout review and retain exact hashes and engine versions. Microsoft application fidelity and embedding need their own actual evidence; unavailable evidence remains a named limit.

Compare with an equivalent baseline using the same source material and meaningful outcomes. Record available construction/render timings, context bytes/read sets, revisions and actual token telemetry when available. Do not substitute character counts for token/cost measurements or claim savings from unobserved data. New upstream adoption remains deferred if the proof establishes no justified gap; missing acceptance evidence keeps completion open.
