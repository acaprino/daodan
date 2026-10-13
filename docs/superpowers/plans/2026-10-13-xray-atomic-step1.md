# X-ray atomic method, step 1: structure by moving text

Spec: `docs/superpowers/specs/2026-10-12-xray-atomic-method-design.md`, refactor
plan step 1. One commit. No behaviour change: every sentence that leaves
`SKILL.md` or `analyze.md` lands in exactly one unit, and every body that read a
moved section reads it at its new path.

## Scope of this step

In: the router and the eleven units; the incremental execution, tool lines,
forbidden files, perimeter, source reading and Phase 0 copies leave `analyze.md`;
every pointer to a moved section is repointed; the move check; the load-budget
test with measured numbers.

Out, left to later steps: phase skeletons and the fold of
`references/analysis-templates.md` and `templates/` (step 2); narrowing worker and
mapper loads (step 3); the `xray-analyst` role, the thin entry, `snapshot.py
check` for every mode, `--phase N`, `--resume-from`, mirror replacement (step 4);
tightening any unit's prose (step 5).

`AI_ANALYSIS_METHODOLOGY.md`, `SEMANTIC_PATTERNS.md` and
`ANTIREZ_COMMENTING_STANDARDS.md` (5,274 words) stay where they are. No body loads
them by default today; the router lists them as on-demand references, and step 5
decides whether they survive.

## Section map

Source line ranges are at `8ac97a7a`. Words are measured.

### `skills/xray-method/SKILL.md`

| Lines | Section | Words | Destination |
|---|---|---|---|
| 11-34 | Overview, Language Support | 321 | `SKILL.md` (router) |
| 35-86 | Prerequisites, Capabilities | 425 | `references/evidence.md` |
| 87-92 | How This Skill Is Invoked | 91 | router, rewritten as the load map |
| 93-123 | Concurrent Runs Model | 520 | `references/run.md` |
| 124-152 | Incremental Updates | 661 | `references/update.md` |
| 153-178 | Evidence-anchored output, mandatory rules, two roles of documents | 469 | `references/evidence.md` |
| 179-233 | Phase 0 | 548 | `references/phase-0.md` |
| 234-249 | Output Usage Guide | 160 | `references/reading.md` |
| 250-259 | Perimeter | 339 | `references/run.md` |
| 260-263 | Forbidden Files | 45 | `references/evidence.md` |
| 264-321 | Script commands 1-3 | 210 | `references/evidence.md` |
| 322-352 | Documentation diagnosis commands 4-7 | 83 | `references/phases-5-6.md` |
| 353-389 | Comment quality commands 9-13 | 101 | `references/phases-5-6.md` |
| 390-438 | Incremental update commands 14-15 | 296 | `references/snapshot.md` |
| 439-501 | Source Reading from the Bound Snapshot | 472 | `references/evidence.md` |
| 502-514 | File Classification Criteria | 93 | `references/evidence.md` |
| 515-536 | Five Layers, Pattern Recognition | 148 | `references/phases-3-4.md` |
| 537-555 | Red Flags to Identify | 78 | `references/phases-5-6.md` |
| 556-575 | AI Analysis Workflow, Analysis Loop | 150 | `references/evidence.md` |
| 576-582 | Best practices, source code | 55 | `references/evidence.md` |
| 583-588 | Best practices, documentation | 39 | `references/phases-5-6.md` |
| 589-612 | Team Mode Integration, choosing classic or team | 265 | `references/run.md` |
| 613-643 | References, Resources | 256 | router |

### `workflows/analyze.md`

| Lines | Section | Words | Destination |
|---|---|---|---|
| 11-19 | CRITICAL RULES | 97 | stays |
| 20-41 | Tool Integration | 373 | merged into `references/evidence.md` |
| 42-53 | Forbidden Files | 72 | merged into `references/evidence.md` |
| 54-59 | Perimeter | 116 | merged into `references/run.md`, one pointer line stays |
| 60-193 | Pre-flight 1, 1b, 2, 3 | 1,290 | stays (entry flow, thinned in step 4) |
| 194-217 | Execution Order | 289 | stays; snapshot write lines 198-208 move to `references/snapshot.md` |
| 218-239 | Source reading in every code phase | 197 | merged into `references/evidence.md` |
| 240-256 | Full and lite depth | 244 | stays |
| 257-295 | Incremental depth | 474 | merged into `references/update.md` |
| 296-301 | Overrides | 19 | stays |
| 302-356 | Phase 0 copy | 512 | deleted after its differences are merged into `references/phase-0.md` |
| 357-442 | Phases 1-2 | 416 | `references/phases-1-2.md` |
| 443-550 | Phases 3-4 | 669 | `references/phases-3-4.md` |
| 551-615 | Phases 5-6 | 373 | `references/phases-5-6.md` |
| 616-703 | Phase 7 | 611 | `references/phase-7.md` |
| 704-795 | Publish, Completion, examples, code review integration | 643 | stays (publishing stays in the entry, by decision) |

Each moved phase leaves one load line in `analyze.md`:
`Read ${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/<unit>.md and run it.`

### Merges

Five sections exist twice. Each merge keeps the canonical copy and carries over
only sentences the other copy has and the canonical lacks; the move check lists
every dropped duplicate sentence with its surviving twin.

1. Phase 0: `SKILL.md` 179-233 is canonical (87% similar to `analyze.md` 302-356).
   The `--phase 0` preamble line (`analyze.md` 308) goes to the entry, beside the
   flag parsing.
2. Forbidden files: `SKILL.md` 260-263 plus `analyze.md` 42-53.
3. Perimeter: `SKILL.md` 250-259 canonical, `analyze.md` 54-59.
4. Tool lines: `SKILL.md` 264-321 canonical, `analyze.md` 20-41 (its Phase 5
   `cascade_scan.py` line goes to `phases-5-6.md`).
5. Source reading: `SKILL.md` 439-501 canonical, `analyze.md` 218-239.

## Pointers to repoint

| File | Line | Now | After |
|---|---|---|---|
| `codebase-xray/workflows/team-analyze.md` | 55 | `## Concurrent Runs Model` in the skill | `references/run.md` |
| `codebase-xray/workflows/team-analyze.md` | 146 | `## Perimeter` in the skill | `references/run.md` |
| `codebase-xray/workflows/team-analyze.md` | 269, 314 | worker and synthesizer briefs read `SKILL.md` | router plus every unit (same content as today; step 3 narrows) |
| `codebase-xray/workflows/analyze.md` | 22, 36, 56, 64, 353 | sections of the skill | their units |
| `codebase-xray/roles/partition-structure-worker.md` | 47, 51 | perimeter, source reading | `run.md`, `evidence.md` |
| `codebase-xray/roles/partition-behavior-worker.md` | 46 | source reading | `evidence.md` |
| `codebase-xray/roles/partition-quality-worker.md` | 49-50 | scripts, tool lines | `evidence.md`, `phases-5-6.md` |
| `codebase-xray/roles/semantic-interconnect-mapper.md` | 70 | owner commands | `snapshot.md`, `reading.md` |
| `codebase-xray/skills/xray-method/references/AI_ANALYSIS_METHODOLOGY.md` | 426 | loads the skill | `reading.md` |
| `project-knowledge` (`codebase-explorer.md:24`, `guide-method.md:21`, `preparation.md:13`, `instructions-method/SKILL.md:34`) | | load the skill to consume an analysis | unchanged text; the router's consumer map sends them to `reading.md` and `evidence.md` |
| `project-lifecycle` (`lifecycle-method:60`, `handover-method:39`, `maintainer-method:42`) | | same | unchanged text, same route |
| `senior-review/.../review-preparation/references/team-review.md` | 249 | names the skill as the method | unchanged |

External consumers keep loading `codebase-xray:xray-method`; the loadable name is
an invariant. Their text does not change in this step, so only `codebase-xray`
is bumped among the consumers.

## Tasks

1. **Move check script** (scratchpad, not shipped): split the two sources at
   `8ac97a7a` and the new tree into normalized paragraphs (whitespace collapsed,
   code fences kept whole); report every source paragraph found zero times or
   more than once in the new tree, minus the declared merge list. Pass condition:
   empty report. Its output goes in the commit message.
2. **Create the units** by cutting the sections above verbatim; headings shift
   one level where a unit starts with its own `#` title. No sentence is edited
   except the cross-references the move breaks.
3. **Merges** in the order above, each checked by the move script.
4. **Router**: overview, languages, script directory, load map (unit, holds,
   loaded by, from the spec's table), consumer map (forbidden files from
   `evidence.md`; consuming a bound analysis from `reading.md` plus `evidence.md`;
   running one is the `codebase-xray:analyze` workflow), on-demand references.
5. **Thin `analyze.md`** to the rows marked stays, plus load lines.
6. **Repoint** every row of the pointer table.
7. **Tests**:
   - `tests/test_xray_method_units.py`: no normalized paragraph appears twice
     across `xray-method/SKILL.md`, its `references/` units and
     `workflows/analyze.md` (the permanent half of the move check); every unit
     the router's load map names exists; every unit is named by the load map.
   - `tests/test_xray_load_budget.py`: for `analyze`, `team-analyze`, each
     partition worker brief, the synthesizer and the mapper, follow every
     `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/...` and `references/*.md` named
     in the body, sum words, fail above the measured budget. Budgets recorded
     after this step; the test comment says they only go down.
   - Adjust `tests/test_daodan_host_rendering.py` and the X-ray suites where they
     assert text that moved.
8. **Release**: codebase-xray 5.3.4 to 5.4.0, skill-catalog patch, marketplace
   32.10.4 to 32.11.0; `python scripts/daodan_build.py`, `sync_plugin_docs.py`,
   `sync_codex_instructions.py`; every consistency gate on an LF extraction
   (`git -c core.autocrlf=false archive`); commit, push, watch publication.

## Expected loads after the step

| Reader | Before | After step 1 |
|---|---|---|
| `analyze` entry | 6,461 + 5,881 skill | about 2,700 entry + units it runs (the full method, same total) |
| router alone (external consumer's first read) | 5,881 | about 820 |
| external consumer reading an analysis | 5,881 | router + `reading.md` + `evidence.md`, about 3,200 |
| partition worker, synthesizer, mapper | unchanged | unchanged (step 3) |

Unit sizes after moving, before any tightening: run 1,124; snapshot about 400;
update about 1,000; evidence about 2,100; reading 160; phase-0 548; phases-1-2
416; phases-3-4 817; phases-5-6 about 750; phase-7 611. Evidence and run are over
the spec's targets; step 5 brings them down.

## Live evidence

Baseline: one classic `/codebase-xray:analyze .` on `D:/Projects/humanize`
(branch `pilot/base`, 32 files in scope) with codebase-xray 5.3.4 installed,
headless, transcript under `.daodan/responsibility-assessment/xray-baseline/`.
The second run comes after step 4, as decided.
