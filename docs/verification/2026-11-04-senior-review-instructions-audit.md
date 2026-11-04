# Senior Review instructions audit (2026-11-04)

Static audit of `plugins/senior-review` Markdown against `docs/research/prompt-engineering-and-brevity.md` §3 (load graph per executor, one owner per obligation with one delivery per context, verifiable wording). No file in the plugin was modified. Script: `sr_audit.py` (Temp, not retained); counts are words of whole files, diagnostics only.

Scope: 7 skills, 33 references, 42 role files, 8 compositions, 7 contracts, `plugin.toml`, `README.md`.

## A. Load resolution

| Check | Result |
|---|---|
| `plugin.toml` roles (50) = 42 files + 8 compositions; skills = 7 dirs; composition members | all resolve |
| `references/<variant>.md` convention (review-method, preparation, consolidation) | 6 variant files loaded by convention, not by name: not orphans |
| Cross-skill `references/*.md` mentions | all name the owning skill in the same or previous line |
| `## Section` of file references | all found |
| `references/reviewer-catalog.json` (review-preparation SKILL.md:34) | **absent**; README.md:21 already declares it a generated export artifact |
| `references/locate.md` (investigation-method SKILL.md:29) | resolves to `codebase-map:map-method` |

## B. Roles

### B1. Shape
- 36 roles on one of two equivalent templates (`Mandate and input` or `Mandate and activation` + `Required input`, then `Causal checks`, `Counterevidence`, `Boundaries and output`), 254–640 words.
- 6 free-form roles: `api-contract` 996, `resource-lifecycle` 898, `temporal-resilience` 954, `chicken-egg` 589, `logic-integrity` 644, `ui-race` 549, `premise` 1480 words.
- 41 roles load `reviewer-common.md`; `premise-auditor` does not and instead carries its own `## Assigned knowledge inputs` block (~170 words) restating `reviewer-common.md` `## Context economy and coverage`.
- Persona text in two places: `premise-auditor.md:16` ("You exist because…") and `review-preparation/references/code-review.md:3` ("You are a thorough code reviewer…").

### B2. Verbatim duplication across roles
Only the taxonomy load sentence ("Load only applicable sections of …") in 16 roles. No domain check is repeated verbatim; no role sentence shares ≥2 six-word shingles with `reviewer-common.md`. Roles are already one class each; no merge or split candidate found.

### B3. Hand-offs to owners that do not exist
Role boundary sentences route a class to an owner absent from the catalog:

| Role:line | Routed to | Status |
|---|---|---|
| `api-contract-auditor.md:71`, `:64` | "test-suite reviewer", "logic/test review" | gap declared only in `review-method/references/team-review.md:117`; not in code-review, pr-review, light |
| `application-reachability-auditor.md:40` | "workspace", "testing" | no owner, no declared gap |
| `dependency-usage-auditor.md:39` | "dependency audit" | gap declared in `stack-dimensions.md` dependencies row |
| `accessible-navigation`, `browser-security`, `release-compatibility`, `ui-race` | "platform", "React owner" | declared gaps in `stack-dimensions.md` |

A hand-off to a missing owner drops the class silently (§3.2: unresolved stays unknown, never zero).

## C. Obligation with three owners: finding fields
`premise`, `premise_provenance`, `trigger`, `counterevidence_checked`, `introduced_by_candidate`, `evidence_class` are defined in:
1. `contracts/evidenced-finding.toml` (schema, comments),
2. `review-quality-gates/references/reviewer-common.md` `## Deliver once` (list + one-line semantics),
3. `review-method/references/code-review.md` `### Shared Instructions for All Agents` (semantics + examples, ~430 words), pasted into every worker prompt and referenced by `pr-review.md:14` and `team-review.md`.

Every role context receives 2 and 3 together (role loads 1-hop `reviewer-common`; prompt pastes the block). Same obligation, two deliveries into one context, different wording. A cross-variant rule also lives in a variant file.

## D. Static load per executor (words, whole files, upper bound)
- Single role: 830–975 (no taxonomy) or 2 036–2 990 (role + common 576 + one taxonomy file 895–1 774); `logic-integrity` 4 128. "Load only applicable sections" of taxonomy is not enforceable statically; whole-file figure is the bound.
- Compositions: `security` 10 roles 3 505; `code-auditor` 29 leaf roles 11 735 + common; the rest 653–2 437.
- Coordinator: `light` 2 853; `pr-review` 3 711; `code-review` 5 492; `team-review` 8 092 (SKILL.md of 4 skills + variant files), before Codebase Map output and project instructions.

## E. Wording
Regex over 24 markers: 51 hits, 20 of which `actually`. Non-flag, non-technical adjectives: `thorough` (persona, C above), `honest` ×3 (`premise-auditor.md:60`, `temporal-resilience:24`, `service-resilience:25`, `review-preparation/team-review.md:199`), `genuinely` ×3, `detailed` ×2. No `comprehensive`, `careful`, `robust`, `best practice`, praise instructions.

## Outcome (after MoE deliberation `deepseek-v4-pro` + `gpt-6-astra`, 2 rounds; record in `plugins/senior-review/.jcode/local/ultra-nerd/run-20261104-161754-2921eb/answer.md`)

| # | Decision | Why |
|---|---|---|
| 1 | reduced to persona removal | `reviewer-common.md` says "Maps … supply leads; cite used map anchors": loading it into the blind Mode 1 adds a conflicting instruction and +376 words; the knowledge block is that role's only delivery of those obligations |
| 2 | applied | `composition.md:43-55` binds `reviewer-common.md` (`common`) to every job, so the owner is delivered to every worker; the same `Premise declaration` text was also in `review-method/references/team-review.md:90-104` (fourth copy) |
| 3 | rejected | F3 was incomplete: testing/workspace gaps are already declared at dispatch in `review-method/references/team-review.md:23,33,117`, `code-review-agents.md:44,46`, `candidate-grounding.md:144-145`; roles name classes, not catalog entries |
| 4 | applied | output owned by `code-review-output.md`, `--auto-comment` by `code-review-delivery.md` |
| 5 | applied as a gap declaration | `review_roster.py:437-469` reads only `id`/`members`/`kind`, derivable from `plugin.toml`; `composition.md:24,62` also needs the compiled JSON and `scripts/composition.py`, which does not exist |

Post-edit checks: load resolution unchanged (only `reviewer-catalog.json`, declared); removed text has 0 remaining hits; `reviewer-common.md` 576 → 728 words, code-review worker prompt −~300, team-review worker prompt −~130, coordinator code-review 5 492 → 5 291, team-review 8 092 → 8 019.

## Proposals (as audited, before deliberation)

| # | Change | Kind | Impact |
|---|---|---|---|
| 1 | `premise-auditor` loads `reviewer-common.md` and drops `## Assigned knowledge inputs`; remove the "You exist because" paragraph | duplicate removal, persona | −~200 words per Lens 0 / Phase 1c context; Mode 1 blindness unaffected (common has no project content) |
| 2 | Finding-field semantics: one owner. Keep contract as schema; move the `Shared Instructions` definitions into `reviewer-common.md` `## Deliver once` (or `code-review-agents.md`); `code-review.md` pastes only intent + diff-scope tiers | one owner / one delivery per context (§3.4); migration, not plumbing (§3.3) | −~250 words per worker prompt; inventory old→new required |
| 3 | Declare missing owners once: `stack-dimensions.md` rows for `testing` and `workspace` as declared gaps (like platform/react); roles keep their hand-off wording | unresolved → explicit unknown | 2 rows |
| 4 | `review-preparation/references/code-review.md:3`: drop persona sentence | wording | 1 line |
| 5 | `reviewer-catalog.json`: either generate it in this base or make `review-preparation/SKILL.md:34` point to `plugin.toml` compositions as the catalog | unresolved load | decision needed |

Not proposed: merging roles, shortening the 6 free-form roles for length alone, touching `defect-taxonomy` (loaded by section, out of this audit's measure).

## Limits
Static text only; no behavioral test, no tokenizer measurement, no check of dynamically retrieved content (Codebase Map output, evidence packs). Residual risk: obligations phrased without the markers searched.
