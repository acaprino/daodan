# X-ray: an analysis owner and an atomic method

Approved by the user on 12 October 2026. Agents own complex, long activities and
use skills as building blocks; skills become small units loaded only when a step
needs them. `codebase-xray` is the first module. Three goals decide every choice
below: **simple content, simple architecture, maximum token saving.** A review of
the first draft corrected the comment-remediation contract, the load matrix,
mode-aware delivery and the tests, and the user fixed the template rules; all of
it is folded in.

Numbers are words counted at commit `eb8ae49b` (a token is roughly 1.3 to 1.5
words). "About" marks an estimate from moving existing sections; step 1 replaces
estimates with measured budgets.

## Where tokens go

Three costs, and one lever for each.

| Cost | Lever |
|---|---|
| **Duplication**: the same text loaded twice in one context | one home per rule, command and template |
| **Over-loading**: a step loads a whole method to use one part | units loaded per step |
| **Carrying**: every later turn of a context re-reads everything already in it; a cached prefix is cheaper, never free | keep heavy reading out of long-lived coordinators |

The third cost dominates long activities. In the contract pilot's S4 run the
change coordinator's own context accounted for about 25 of the run's 38 million
cache-read tokens; its subagents, together, for the other 13.
Today `senior-review` `team-review` and the project-lifecycle operations run the
X-ray inside their coordinator, which then carries the method and every source
file the X-ray read through all of its remaining turns.

## Principles

1. **An agent owns an activity; skills are its materials.** The owner orders the
   work, keeps state, finishes or names the blocker. A skill states a procedure or
   knowledge and never orchestrates.
2. **Load what the step needs, nothing else.**
3. **One home per rule, command and template.** Copies are generated or absent.
4. **Atomic means one purpose, declared inputs and outputs, loadable alone.** Split
   where a consumer needs part of a unit, never to hit a word count; merge where
   two pieces are always loaded together.
5. **Move before rewriting.** Restructuring and tightening are separate commits.
6. **A runtime body states the rule and at most one line of reason.** History,
   incidents and extended rationale live in the documentation, which no agent
   loads.
7. **Questions stay where the user can answer.** A delegated agent asks nothing.
8. **Guard by construction.** Budgets and single-source tests catch regrowth for
   free; a live run is reported evidence, never the guard.

## Current state

| Component | Kind | Words |
|---|---|---|
| `xray-method` | skill, the whole method in one file | 5,881, plus 6,265 in `references/` and 894 in `templates/` |
| `/codebase-xray:analyze` | workflow, every phase inline | 6,461 |
| `/codebase-xray:team-analyze` | workflow, coordinates workers | 4,250 |
| three partition workers | roles, one each per partition | 1,068 / 1,129 / 1,057 |
| `partition-synthesizer` | role | 1,738 |
| `semantic-interconnect-mapper` | role | 2,540 |

- **Over-loading:** each partition worker and the mapper loads all 5,881 words of
  the method to use the source-reading procedure (465 words) or a few commands.
- **Duplication:** `analyze` carries 6,461 words and loads the method too, over
  12,300 words before any source file. Phase 0 exists twice (87% similar). Phase
  templates exist in four places, and classic and worker versions are only 37 to
  64% similar despite the synthesizer's byte-compatibility promise.
- **Contradictions:** `analyze.md` says to stop "before applying changes" while the
  X-ray never applies any, and reads `--phase N` both as "start at N" and as "run
  only N".
- **A mixed mirror:** publishing copies only the files a run produced over the
  previous mirror, so a partial or lite run leaves another run's files beside its
  own under its `state.json`.
- **Consumers:** eight external bodies load `codebase-xray:xray-method` for four
  purposes (forbidden files, consuming a bound analysis, source-reading commands,
  static context); three plugins run `analyze` inside their own context
  (senior-review `team-review`, project-lifecycle through `lifecycle-method`,
  abstraction-architect `audit`).

## Target

### Eleven units inside one skill

No new skill is registered: each would add a description to every session on
every host, and a dependency to every consumer. Each unit is a file inside
`xray-method`; `SKILL.md` becomes the router.

| Unit | Holds | Words | Loaded by |
|---|---|---|---|
| `SKILL.md` | overview, languages, script directory, the load map, the consumer map | about 600 | everyone |
| `references/run.md` | run identity and registration, concurrency, perimeter, scope confirmation, the publication rule | about 1,000 | `analyze`, `team-analyze` |
| `references/snapshot.md` | every `snapshot.py` command: `scope`, `write` (first write and every refresh with `--reuse`), `diff`, `carry`, `check` | about 500 | `analyze`, `team-analyze`, the analyst, external bodies that refresh a manifest |
| `references/update.md` | re-deriving stale claims and added symbols, extra reads, the completion sections of `changes.md` | about 700 | the analyst, on update runs only |
| `references/evidence.md` | evidence-anchored claims and their statuses, source reading from the bound snapshot, the reading ledger, forbidden files, file classification, the reading tools several roles share (`source_reader.py`, `ast_parser.py` for missing structural detail and single-file diagnosis, `usage_finder.py`, `cascade_scan.py`) | about 1,300 | the analyst, partition workers, mapper; external bodies for forbidden files |
| `references/reading.md` | consuming a finished analysis: binding an exact run and snapshot, mirror versus run, preserving claim statuses, the three coverage figures, which file answers which question | about 500 | mapper, external consumers |
| `references/phase-0.md` | project knowledge discovery, single copy | about 540 | the analyst, `team-analyze` |
| `references/phases-1-2.md` | structure and interfaces: procedure, parser commands, skeletons of `01` and `02` | about 850 | the analyst, structure worker, synthesizer |
| `references/phases-3-4.md` | flows and semantics: procedure, skeletons of `03` and `04`; the semantic references on demand | about 850 | the analyst, behavior worker, synthesizer |
| `references/phases-5-6.md` | risks and documentation health: procedure, `doc_review.py`, the comment rules (only under `--comments`, never applied), skeletons of `05` and `06`; the commenting standard on demand | about 900 | the analyst, quality worker, synthesizer |
| `references/phase-7.md` | the final report skeleton and its coverage figures | about 600 | the analyst, synthesizer |

A phase's procedure and its skeleton share a file because the analyst and the
worker always load them together; that costs the synthesizer about 1,500 words of
procedures it does not use, once per team run, against about 10,000 words saved
per partition. `analysis-templates.md` and `templates/` are folded into the phase
units or retired. Scripts stay in `xray-method/scripts/`, which the router names.

Refreshing a manifest stays with whoever owns the run's snapshot, as today: the
analyst refreshes its own run; a partition worker or the mapper that meets
changed source or a parser mismatch reports the refresh as a delivery gap for its
coordinator and never refreshes the shared manifest itself.

The consumer map in the router replaces the implied contract of the skill's name:
forbidden files come from `evidence.md`; consuming a bound analysis from
`reading.md` (plus `evidence.md` to read source); running an analysis means the
`codebase-xray:analyze` workflow.

### One skeleton per phase file

- Each phase file has one canonical skeleton, in its phase unit, using the classic
  headings.
- Common headings are identical in both modes. Partition scope ("within this
  partition") is stated in the content, never in a heading.
- Each team extension declares its exact heading, the file and mode in which it
  appears, and how the synthesizer aggregates it.
- Team headings that the mapper or another consumer reads are preserved:
  `## Cross-Partition Exports` (02), `## Cross-Partition Flows` (03),
  `## Hidden Contracts (cross-partition)` (04),
  `## Cross-Partition Risk Attribution` (05), and any other found by the consumer
  test.

### The owner: `xray-analyst`

`xray-analyst` runs the phases its brief declares in one isolated context, loading
one unit per phase, keeping `state.json` current and delivering the report path.
One context, as `analyze.md` already decided (one reading of the code costs less
than three); it simply no longer lives in the user's or a coordinator's context.
It asks nothing, edits no source, and under `--comments` records the proposals in
the run, leaving their application to the development or readability owner as
today.

The `analyze` entry keeps the run, the scope confirmation, the incremental
checkpoint, the mode's expected phases, the dispatch, the delivery check and the
publication. **Publishing stays in the entry**: only the coordinator verifies a
delivery and writes the shared mirror. `team-analyze` stays the team coordinator.

### Delivery by mode

Before dispatch the entry records, for every artifact the mode can involve, one of
three statuses: **produced** by this run, **inherited** with its provenance (the
parent run id and the carry record, or the same run on a resume), or **skipped**
with the reason. Recovery only ever considers produced artifacts that are missing;
an inherited or skipped one is never "incomplete".

| Mode | Produced | Inherited | Skipped | Publishes |
|---|---|---|---|---|
| full | `knowledge/`, `01` to `07` | none | none | yes |
| `--depth=lite` | `knowledge/`, `01`, `02`, `05`, condensed `07` | none | `03`, `04`, `06` | yes |
| update | `knowledge/` in full; each of `01` to `06` holding a stale marker or an added symbol, re-derived in place; `07` regenerated; completed `changes.md` | each of `01` to `06` with neither, carried from the parent | none | yes, when no stale marker is left |
| `--docs-only` | `knowledge/`, `06` | none | `01` to `05`, `07` | no |
| `--phase N`, N from 1 to 6 | `knowledge/`, the phase N file | none | every other phase | no |
| `--resume-from [N]` | the run's own produced artifacts from N on | the run's artifacts before N, confirmed by the gate | as the run's mode | as the run's mode |
| `--comments` | adds `comment_health.md` and the recorded proposals to phase 6 | none | none | as the mode |

**`--phase N` runs one phase, by decision of the user.** It derives what it needs
from the snapshot and the source and never invents earlier phase files. `--phase 7`
is refused: the final report summarizes a complete analysis, and an update or
`--resume-from 7` already regenerates it from the files it summarizes.

**`--resume-from [N]` continues an interrupted run,** named with `--run-name`. It
keeps the artifacts before N when the gate confirms them and redoes N onward
according to the run's own mode; without N it starts from the first missing
produced artifact the gate reports. Resuming never changes the run's mode or
flags; a different mode is a new run.

**Only a complete run of a publishing mode publishes, and it replaces the whole
mirror.** `--phase N` and `--docs-only` runs are partial: their results stay in
their run directory, bound by run id. Publishing removes from the mirror every
phase file the run did not produce before copying its own. Today the mirror only
overwrites what the new run has, so a lite run leaves an older run's `03`, `04` and
`06` beside its own files, and a classic run leaves an older team run's
`08-interconnect-map.md`: one mirror describing two analyses under one
`state.json`.

The table lives in code, not in prompts. `snapshot.py check`, already the
publication gate for updates, becomes the single gate for every mode: given the
run's declared mode it reports a produced artifact that is missing or empty, an
inherited one without provenance, an unexpected file, any stale marker left, the
first missing produced artifact, and whether the run may publish. The entry acts
on its answer: publish, re-dispatch from that point, or record the failure. A
stopped or empty delivery is never a delivered result.

### Loads

| Who | Today | After (about) |
|---|---|---|
| user's or coordinator's context during `analyze` | 12,342 plus all source read | entry 1,500 + router 600 + `run.md` 1,000 + `snapshot.md` 500 = 3,600, no source |
| `xray-analyst`, full depth | (inside the above) | role 500 + router 600 + `snapshot.md` 500 + evidence 1,300 + phases 0 to 7 3,740 = 6,640; update +700; `--comments` +1,863; semantic references up to +3,411 |
| each partition worker | about 7,000 | about 3,600 (-49%) |
| mapper | 8,421 | 2,540 + 600 + 1,300 + 500 = 4,940 (-41%) |
| synthesizer | 1,738 | about 1,300 + 600 + 3,200 = 5,100, once per team run |

The certain, large gain is in the long-lived context: it stops carrying the method
and the X-ray's source reading for the rest of its turns. A standalone run's total
falls less, since the analyst still reads every unit and every source file once.

## Refactor plan

Each step is one commit with a `codebase-xray` bump, a marketplace bump and a
`skill-catalog` bump while its index carries provider versions; all five hosts are
rebuilt and every gate runs on an LF extraction.

1. **Structure, by moving text.** Router and units; the incremental execution and
   tool lines leave `analyze.md`; its Phase 0 copy goes. The load-budget test lands
   with measured numbers. A move check proves every moved paragraph exists once.
2. **One skeleton per phase file,** under the rules above; `analyze`, the workers
   and the synthesizer cite their unit. This step decides meaning, heading by
   heading, and lists each change in the commit.
3. **Workers and mapper load only their units.** Budgets drop.
4. **The analyst and a thin entry.** `roles/xray-analyst.md`; `analyze.toml` gets a
   shared `preflight`, a required-isolation `analysis` phase with the analyst, a
   shared `publish`; `snapshot.py check` covers every mode with produced,
   inherited and skipped artifacts; `--phase N` takes its new meaning, `--phase 7`
   is refused and `--resume-from [N]` is added; partial runs stop publishing and
   publishing replaces the whole mirror; the "before applying changes" clause goes. senior-review `team-review`, the project-lifecycle
   workflows that run the X-ray and abstraction-architect `audit` declare
   `codebase-xray/xray-analyst`.
5. **Tighten each unit.** One commit per unit: drop restatements and extra
   examples, move rationale beyond one line into `docs/plugins/codebase-xray.md`,
   keep every rule and invariant. Each commit lowers that unit's budget.

## Tests

- **Move check** (1): every moved paragraph exists in exactly one file.
- **Load budget** (1 onward): for every role and entry, follow the files its body
  loads and every reference they name; check the default load and the worst case
  with all conditional loads. Fail above budget or on a role loading the whole
  method. Budgets only go down.
- **Skeletons and consumers** (2): one skeleton per phase file; common headings
  identical in both modes; every team extension declared with name, mode and
  aggregation; the synthesizer's headings equal skeleton plus declared extensions;
  every heading a consumer body cites (the mapper, `team-analyze`, the synthesizer,
  external plugins) still exists. This protects the contract consumers actually
  read, not only the uniqueness of templates.
- **Gate** (4): `snapshot.py check` fixtures for an empty delivery, a missing
  artifact, an unexpected artifact, an interrupted run resuming at the first
  missing produced artifact, `--resume-from N` keeping confirmed earlier
  artifacts, an inherited artifact accepted with provenance and rejected without,
  `--phase N` and `--docs-only` runs never publishable, `--phase 7` refused, each
  mode's skipped artifacts never reported missing, and a publication that removes
  a stale mirror file (an older team run's `08` after a classic run).
- **Composition** (4): every workflow whose body or loaded method runs
  `codebase-xray:analyze` in its own context declares the analyst and requires
  `codebase-xray`.
- **Host rendering** (4): the analyst dispatched with required isolation on all
  five hosts, confirmations kept in the entry. Structural evidence only.

## Invariants

The `.codebase-xray/` contract, run isolation and publication by the coordinator;
the perimeter owned by `tree_scope.py`; static analysis only, stylesheets parsed
and scanned, the three coverage figures; no mutation of the analyzed source; the
behavioural invariants of `evals/codebase-xray`; `codebase-xray:xray-method` as a
loadable name; the scripts, their command lines and their location.

## Deliberately not done

- **No new registered skills, no separate template files, no commands file:**
  each would add a file or a listing without saving tokens.
- **No content rewrite during steps 1 to 4;** tightening is step 5, unit by unit.
- **No change to team topology,** partitioning or dispatch plan.
- **No runtime or browser step in the X-ray.**
- **Senior-review is the next module,** not this one: S4 loaded
  `review-quality-gates` (4,722 words plus 5,722 of references) for a 40-line
  change.

## Blast radius

`plugins/codebase-xray/`; the sidecars of senior-review `team-review`, the affected
project-lifecycle workflows and abstraction-architect `audit`; new and adjusted
tests; the hand-written part of `docs/plugins/codebase-xray.md`; the regenerated
packages of all five hosts. The latest-state consumers of the mirror
(`senior-review:code-review`, `project-knowledge:guide`, `project-knowledge:instructions`)
see the publication rules of step 4: no partial run in the mirror and no file left
over from an older run.

## Verification

Every step: the repository gates on an LF extraction of the commit plus that
step's tests. Live evidence, by decision: one classic `/codebase-xray:analyze` on
the `humanize` fixture before step 1 and one after step 4, comparing published
files, headings and coverage figures, reported apart from the compiler evidence.

## Decisions

- Classic headings are canonical; team extensions are declared, with the rules
  under "One skeleton per phase file".
- Publishing stays in the entry.
- `--phase N` runs only phase N (after Phase 0) and is never published;
  `--resume-from [N]` is the separate way to continue a run. Both land in step 4
  and replace today's contradictory reading of `--phase N`.
- `--docs-only` is a partial run and never publishes, like `--phase N`.
- `--phase 7` is refused; an update or `--resume-from 7` regenerates a report.
- Publishing replaces the whole mirror, so it always describes exactly one run.
  A lite run no longer leaves an older run's `03`, `04` and `06` in place; a
  latest-state consumer that read those stale files finds them absent instead.
- One live classic run on the `humanize` fixture before step 1 and one after
  step 4 is part of the verification.
