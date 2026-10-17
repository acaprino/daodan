# Codebase Map Plugin

> Understand any codebase in minutes. Eight-phase analysis discovers how the project documents itself, maps structure, traces flows, identifies risks, and documents the WHY behind the code, not just what it does. Renamed from `deep-dive-analysis` in plugin 2.0.0 (marketplace 14.0.0); its output artifact directory followed in plugin 4.0.0 and is now `.codebase-map/`.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Concurrent runs

Every analysis is an isolated run under `.codebase-map/runs/<run-id>/` with its own `state.json`, registered in `.codebase-map/runs.json`. Multiple analyses can proceed at the same time (different targets, different sessions, or a re-analysis alongside an older one) without touching each other's files. Use `--run-name <name>` for explicit run identity; otherwise the run-id derives from the target slug plus a timestamp.

Only an eligible completed run is **published**: the coordinator requires `complete` and `may_publish` from the delivery gate and every requested view before replacing the whole known phase-file mirror and `state.json` at `.codebase-map/`. The mirror contains the files declared for that mode, including `08-interconnect-map.md` only when a team run produces it; older files outside that set are removed. Partial, stopped, docs-only and single-phase runs stay in their own directory. Downstream workflows consuming a specific invocation retain that run directory and snapshot; the mutable root mirror serves latest-state consumers.

By default, every run also records the tree it analyzed as `snapshot/manifest.sqlite`: each file in its inventory with its size, mtime and content hash, each symbol with its span and body hash. The inventory has three sets: source in the parsed languages, configuration and documentation, and presentation files no adapter parses (markup and indented Sass, file-level with no symbols; the exact set is `PRESENTATION_EXTENSIONS` in `snapshot.py`). Stylesheets entered the inventory in plugin 4.1.0, after a global dark-theme rule that locked users out of a consent screen sat in a `.css` file no run had ever recorded, and became a parsed language in 4.2.0: CSS, SCSS and LESS carry one symbol per applied rule, so an edit to one rule marks stale the claims about that rule and about the at-rule or parent rule enclosing it, as a class encloses its methods, never those about its siblings. A minified stylesheet, one with any line longer than 10,000 characters, stays file-level with no symbols. Anything else is absent from the manifest, and the final report's metadata states three coverage figures, files in inventory, files read in depth and files exercised at runtime (always none, unless the user supplied runtime evidence), so that a file count is never read as coverage. A later run on the same target detects that snapshot, diffs it against the current worktree with no model tokens spent, and offers an incremental update. This claim-level carry is `/codebase-map:analyze` only: unaffected claims are carried over verbatim, only the claims citing changed symbols or their direct importers are re-derived, and a mechanical gate refuses to publish while any of them is still marked stale. `/codebase-map:team-analyze` updates at the coarser partition granularity instead: a partition with no affected file is copied whole from the parent run, and a partition with any affected file is re-analyzed in full, never carried claim by claim. Each run records its parent, so the chain under `.codebase-map/runs/` is the analysis history, and `changes.md` in each run says what changed in the code and what that did to the claims. `--update` requires that a usable parent run exists and stops rather than falling back to a silent full run when one does not; execution mode is still resolved separately at the scope checkpoint. `--no-update` skips detection entirely. A target that changed too much is reported as needing a full run rather than being updated quietly.

## Reading source from a snapshot

New runs default to SQLite. `--format json` (CLI or workflow) and MCP
`format="json"` select the upstream compatibility format explicitly.
`state.json -> snapshot` binds format/path/storage version; `snapshot.py resolve
<run-dir>` returns the exact path and small metadata. Parent runs keep their
original bytes and format, including legacy JSON without the binding. Formats
may differ across a parent/child pair; ambiguous or mismatched files fail.
Indexed semantic facts and graph diagnostics remain static, source-bound evidence.
Workflow per-file analysis uses `analyze_file.py --snapshot <resolved-path>`;
bounded packets retain full counts, explicit truncation and coverage. Binary
storage is local: the model receives targeted text, never database/base64 bytes.
No percentage of token savings is inferred from disk size. Format selection is
independent of full/lite depth and the filename extension. State, events and
protocol responses remain JSON; reports remain Markdown. SQLite indexes may use
more disk space than a compact JSON manifest. See the
[35.0.0 verification record](../superpowers/reports/2026-10-16-codebase-map-binary-storage.md)
for executed checks and limits.

The resolved snapshot is the single structural index for a bound run.
`snapshot.py write <target> --out <new-manifest> --reuse <previous-manifest>`
checks current file hashes and root/target plus helper/runtime and effective
parser identity before reusing unchanged parsed structure. It still walks the
perimeter and hashes the files; legacy or mismatched identity rebuilds structure.
Keep the parent snapshot and write the current one into the owned run. Use
`snapshot.py diff --verify` for analysis changes; its hashes normalize line
endings. After every such diff, always write or obtain a current owned manifest
with `snapshot.py write --reuse` before passing it to source readers, even for
`none` or LF/CRLF-only differences. Parent analysis can remain supported while
its recorded bytes differ from current source. Returning that analysis without
source reading does not require a new full run.

Load `codebase-map:map-method` for exact `source_reader.py outline` and `read`
commands. Outline lists metadata to help choose paths and exact qualified
symbols; it does not validate current source or establish deep reading. Read
checks the requested file's content and parser identity, then emits selected
definitions or line ranges with shared file/class context outside function and
method intervals, plus start/end lines of Java/JavaScript/TypeScript/Rust
callables to retain globals or fields sharing those boundary lines. Legacy or
unreliable spans fall back to the whole file, including single-line, overlapping
or class-boundary spans and long lines.
Minified or shared-line definitions may also need whole-file fallback despite
exact end lines, keeping class declarations and static fields on those lines.

The agent chooses symbols from the question and expands to callers, callees,
invariants, configuration and applicable CSS/markup until the evidence is
sufficient. Context retained around a block cannot establish that omitted
function bodies or implicit relationships are irrelevant. A changed or deleted
source file or changed parser identity requires a current manifest. Record the
exact run and manifest downstream, and distinguish inventoried files, source
read in depth and runtime evidence. The feature does not establish model
latency or installed-host loading.

## Perimeter

Below its target the Codebase Map never analyzes what Git ignores, any directory whose name starts with a dot, or dependency and build output (`node_modules/`, `dist/`, `build/`, `target/`, `vendor/`, `venv/`, `__pycache__/`). The rule has one owner, `tree_scope.py`, and every script that walks a tree applies it: the snapshot, the cascade scan, the usage search, the comment scan and the documentation review. No script reads more than the snapshot records.

The rule dates from plugin 5.1.0. Tools write beside the code they work on: a lifecycle campaign left its run records under `.daodan/` and its review under `.team-review/`, the next snapshot counted them as project files, and an incremental update of an untouched project asked for a full analysis. A list of known tool directories would have let the next tool's output in, so the rule is general. A parent run recorded before this rule holds paths the perimeter now leaves out. Its first update reports them as removed and retires the claims that cite them: they left the inventory, whether or not they left the disk.

Two properties keep it from hiding anything. The target is analyzed as given: `/codebase-map:analyze .github/` is how a project's CI gets a Codebase Map, and a dot file beside analyzed source (`.eslintrc.json`) is not a directory and stays. A target that a repository ignores, itself or through a directory above it, is not that repository's: it is analyzed whole as its own root, its paths start at the target, and no commit, branch or dirty flag is borrowed from the repository that ignores it. A snapshot recorded for such a target before codebase-map 7.0.1 is bound to the enclosing repository, so an incremental update refuses it ("snapshot root differs from the target's repository binding") and a full analysis replaces it. And the exclusion is declared: `snapshot.py scope <target>` prints it for the scope confirmation, the manifest's `scope` block keeps it (`git_ignore` is `unavailable` when no work tree holds the target, in which case no ignore rule was applied), and the final report's inventory line repeats it. A file Git tracks is never ignored, whatever pattern it matches.

## Agents

### `map-analyst`

The classic `/codebase-map:analyze` coordinator dispatches one isolated `codebase-map:map-analyst` after resolving scope and preparing the run and current snapshot. The analyst reads source, loads only the selected phase procedures and writes its run's declared analysis artifacts. It asks no questions, never edits analyzed source and never publishes. The coordinator owns choices, delivery verification, requested views and publication. Required context isolation is a capability gate; an unavailable binding stops the run.

### Partition workers

These four agents serve `/codebase-map:team-analyze` below. Classic `/codebase-map:analyze` uses `map-analyst` instead; it does not dispatch these partition roles.

| Agent | Model | Runs during | Produces (inside the run directory) |
|-------|-------|--------------|----------|
| `partition-structure-worker` | `inherit` | Phase 1 Wave 1: Structure + Interfaces | `partitions/<name>/01-structure.md`, `02-interfaces.md` |
| `partition-behavior-worker` | `inherit` | Phase 1 Wave 2: Flows + Semantics (skipped under `--depth=lite`) | `partitions/<name>/03-flows.md`, `04-semantics.md` |
| `partition-quality-worker` | `inherit` | Phase 1 Wave 2: Risks + Documentation | `partitions/<name>/05-risks.md`, `06-documentation.md` (05 only under `--depth=lite`) |
| `partition-synthesizer` | `inherit` | Phase 2: Consolidation | `01-structure.md` through `07-final-report.md` (consolidated across partitions) |

Each partition worker owns only its listed output files and never touches another partition's files, the consolidated output, or the `.codebase-map/` root (other runs may be in flight). The synthesizer owns the consolidated files inside the run and leaves publication to the coordinator. Cross-partition references use `<other-partition>::<symbol>` citation notation.

### `semantic-interconnect-mapper`

Context-builder that produces a structured map of a codebase's contracts, invariants, domain rules, assumptions, integration hot-spots, and call graph. Unlike the partition workers, it is shared across the whole marketplace: it serves three pipelines and is the reason this plugin sits at the root of the dependency graph. It lived in `senior-review` until plugin 2.1.0 (marketplace 16.0.0).

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Glob, Grep, Bash |
| **Use for** | Building the structured-facts artifact that downstream reviewers and writers cite instead of paraphrasing code |

**Consumers:**

| Pipeline | Phase | Artifact produced |
|---|---|---|
| `/codebase-map:team-analyze` | Phase 3 | `08-interconnect-map.md`, the global cross-partition view |
| `/senior-review:team-review` | Phase 1b | `.team-review/02-interconnect.md`, which every reviewer reads and which `logic-integrity-auditor` requires |
| `/project-knowledge:guide` | Guide preparation, when needed by the file/audience plan | The owned run's interconnect report, cited by the assigned writers and `guide-reviewer` |

**Output sections:** `## Target scope`, `## Call Graph`, `## Contracts` (formal, structural and implicit), `## Invariants` (temporal + structural), `## Domain Rules`, `## Assumptions`, `## Integration Hot-Spots` (HTTP, queue, IPC, env/config), `## Change Impact Radius`, `## Reviewer Hints`. Each section is self-contained so consumers can Grep a single heading and get full context.

Every row carries one of four statuses: `verified` (enforced in code), `documented` (a comment, docstring or project document declares it), `unverified` (the code relies on it but nothing enforces or documents it) or `disputed` (an independent derivation contradicts it, both sides cited). The map opens by declaring itself a **fallible hypothesis index, not ground truth**: a row marked `documented`, `unverified` or `disputed` must be re-derived before it becomes the premise of a finding, and an absent row is not evidence of absence.

Input source differs per pipeline: Codebase Map output for `team-review`, the consolidated partition set for `team-analyze`, and `codebase-explorer`'s context brief for the `project-knowledge` pipelines. It never proposes fixes; every claim carries a `file:line` citation.

---

## Skills

### `map-method`

The method itself: structure extraction fused with semantic reading, the concurrent runs model, Phase 0, and the multi-language script suite (Python stdlib-only; optional tree-sitter for Java/JS/TS/Rust fidelity; a stdlib tokenizer for CSS/SCSS/LESS; Python >= 3.10), including `source_reader.py` for validated source blocks and `cascade_scan.py`, which lists the stylesheet rules with global reach that can break a screen. Named `analyze` until plugin 3.0.0, when it shared its name with the command and the command shadowed it on any host that lists both under one identifier.

| | |
|---|---|
| **Load as** | `codebase-map:map-method`; the `team-analyze` workers read it directly, and `/codebase-map:analyze` is the command that applies it |
| **Use for** | Codebase understanding, architecture mapping, onboarding, evidence for a subsequent review |

**Capabilities:**
- Extract code structure (classes, functions, imports)
- Map internal/external dependencies
- Recognize architectural patterns
- Identify anti-patterns and red flags
- Trace data and control flows

The semantic phases also document contracts and invariants and assess quality and
maintainability. Phase 6 diagnoses documentation drift, broken links, stale indexes
and references, and comment quality; it records proposals without applying them.
These outputs support understanding unfamiliar code, onboarding, review context
and explanations of why code works. Human-facing documentation and remediation
remain with their separately authorized owners.

#### Parser implementation layout

Within the plugin, `skills/map-method/scripts/languages/` holds the adapters. `base.py` defines shared dataclasses and the `LanguageAdapter` protocol; `__init__.py` provides extension dispatch through `detect_language` and `get_adapter`; `comments.py` contains the per-language comment lexer and rustdoc postprocessor; `_treesitter.py` loads optional tree-sitter with fallbacks. Language modules are `python.py`, `java.py`, `javascript.py`, `typescript.py`, `sql.py`, `plsql.py`, `rust.py` and `stylesheet.py`.

---

## Commands

### `/codebase-map:analyze`

8-phase systematic codebase analysis with per-run state management, output files, and phased execution: project knowledge discovery -> structure -> interfaces -> flows -> semantics -> risks -> documentation -> report.

**Phase 0 (Project Knowledge Discovery)** starts every fresh run, including `--depth=lite`, `--phase N` and `--docs-only`; a resume can inherit its confirmed knowledge files. The isolated analyst owns it in classic mode, and the team entry runs it once for team mode. It is a preamble rather than a selectable analysis phase. Phases 1 to 7 keep their numbers: `--phase N` accepts 1 through 6 and selects Phase 0 plus N only; `--phase 0` and `--phase 7` are refused. `--docs-only` selects Phase 0 plus 6.

Phase 0 reads the project's own instruction files and indexes and records where the project claims each concept lives, writing `knowledge/navigation.md` and `knowledge/documentation-leads.md`. Both hold **leads, never verified facts**: the phase reads no code, so every row is `documented` or `unverified`. This is the cheap discovery pass, kept deliberately apart from Phase 6, which is the expensive audit of whether those documents are accurate. Conflating the two is what once made lite mode blind to a project's own documentation. `/senior-review:team-review` Phase 1d consumes `knowledge/documentation-leads.md` as one half of its knowledge-provenance join.

**Entry-gating paths** (authentication, onboarding, consent or policy acceptance, first-run setup) are mandatory critical paths in Phase 3 and a `Usability-blocking` category in Phase 5 and in the final risk matrix, since plugin 4.1.0. For client code the trace includes the effective style cascade over the screen, because a global selector that overrode a consent screen's positioning is what once made it impossible to complete on mobile in dark theme, with the component sitting in the inventory the whole time. Since plugin 4.2.0 `cascade_scan.py` does the mechanical half of that cascade reading: it lists every rule whose selector reaches the document root, every element or the root's untargeted children and sets a positioning, scroll, sizing, display or containing-block property, together with the class, id and attribute rules it can override and what decides it in cascade order (`!important`, cascade layer, specificity, source order). Conflicts that define a screen, a fixed or sticky position, a scroll container or a viewport height, come first. When a stylesheet uses Tailwind, the screen-level utilities written in string-literal `class` and `className` attributes count as conflicts too, from Tailwind's `utilities` layer. A rule on the root or mount element itself is reported without overrides, to limit noise, and the report says so rather than implying there are none. Tailwind `@apply` layout utilities count as the declarations they inline, and that is not a detail: on the Phazly stylesheets at commit `d8efc74e147c`, the Codebase Map's reference, 90% of the applied rules used `@apply` (2,643 of 2,938), all 44 rules of the consent modal's own stylesheet among them, and before the expansion the scan found the dark-theme rule and missed the modal. With it, and with the screen-level utilities read from markup, the same tree reports `.dark #root > div:first-child` beating `.terms-acceptance-modal` on specificity as one of 23 screen-level conflicts, two of them overlays written as `className="fixed ..."` in components, and the tree at the fix commit no longer reports the rule. Whether a candidate and its conflict match the same element depends on the rendered tree, so Phase 5 confirms each one by reading. The Codebase Map stays static: it names those paths and reports them as not exercised. Exercising them in a browser belongs to the project's own tests or to `frontend-review`, never to this plugin.

```
/codebase-map:analyze src/core/ --critical
/codebase-map:analyze src/ --format sqlite        # explicit default
/codebase-map:analyze src/ --format json          # upstream compatibility format
/codebase-map:analyze src/api --run-name api      # named run, safe to run others concurrently
/codebase-map:analyze src/                        # second time on the same target: offers an incremental update
/codebase-map:analyze src/ --update               # require an update base; no usable parent is a hard stop
/codebase-map:analyze src/ --no-update            # skip detection and run a full analysis
/codebase-map:analyze src/ --comments             # include the comment quality audit in Phase 6
/codebase-map:analyze src/ --docs-only            # documentation health only (Phase 6, after Phase 0)
/codebase-map:analyze src/ --phase 5              # Phase 0 plus pattern and risk detection only
/codebase-map:analyze src/ --run-name core --stop-after 2
/codebase-map:analyze src/ --run-name core --resume-from
```

**Output:** `.codebase-map/runs/<run-id>/` holds the selected phases, Phase 0's `knowledge/` directory and a current `snapshot/manifest.sqlite` by default (`snapshot/manifest.json` for explicit JSON). A full run produces `01-structure.md` through `06-documentation.md` and `07-final-report.md`. Lite selects 0, 1, 2, 5 and a condensed 7, omitting 03, 04 and 06. Single-phase and docs-only runs produce no final report and never publish. A classic run never writes `08-interconnect-map.md`. Only eligible complete full or lite delivery replaces the root mirror; snapshots, and an update's `changes.json` and `changes.md`, stay in the run directory.

`--stop-after N` accepts 1 through 6 and stops that invocation while retaining the selected mode's later obligations as pending. It cannot combine with single-phase or docs-only controls. Resume uses `--resume-from [N] --run-name <exact-id>` on the same interrupted run, with unchanged mode, flags, target and verified source binding. N accepts 1 through 7; omitting it selects the first incomplete produced phase. Resume drops the invocation's stop, preserves confirmed earlier and inherited artifacts, and re-executes declared produced work from the selected phase onward.

#### Incremental updates

A full classic run writes the snapshot that makes a later update possible. Unless `--no-update`, resume, docs-only or single-phase controls apply, the coordinator looks for a completed same-target classic run with a usable manifest and diffs that snapshot against the current worktree. The diff is mechanical and spends no model tokens: its default content check trusts equal size and mtime, while `--verify` hashes every file and is required for evidence freshness. Parser identity changes invalidate cached structure. A changed symbol is found by comparing the hash of its definition. The scope checkpoint then shows the result before semantic reading:

```
Codebase Map target: src
Run: src-20260904-101500   parent: src-20260901-101200 (d5a11cef, 3 days ago)
Since parent: 2 modified, 1 added, 0 removed files; 3 symbols changed, 1 added, 0 removed
Blast radius: 2 importing files
Affected claims: 11 (03-flows: 5, 02-interfaces: 4, 05-risks: 2)
Files affected: 5 of 41
Not analyzed: 1 dot directories (src/.storybook), 3 paths Git ignores (ignore rules: applied)

1. Incremental update from src-20260901-101200 (5 affected files)
2. Full analysis (41 inventoried files; source reading follows the claims)
3. Cancel
```

Accepting the update carries every claim the change set did not touch forward byte for byte, with `file:line` citations renumbered where lines shifted, and re-derives only the claims that cite a changed symbol, a changed file, or a file that imports one. New symbols get new claims, removed symbols lose theirs, and the final report is regenerated from the phase files. A mechanical gate then refuses to publish while any re-derivation is still marked pending, so an incremental result is either finished or not published. `changes.md` in the run directory records what changed in the code and what happened to each affected claim, and `state.json` names the parent run, so the chain of runs under `.codebase-map/runs/` is the analysis history.

Change detection follows the current worktree because re-analysis often targets
dirty files and sometimes directories outside Git. A commit records lineage
without defining the changed source. The one-hop limit bounds re-derivation work:
an import graph's transitive closure can span the whole target.

The verified diff recommends a full run with reasons, including when more than 40% of files are affected. A recommendation is advice: with an eligible parent, the coordinator resolves update versus full from the request or earlier answers and asks only when undecided. The scope preview remains visible with `--update` and `--no-update`; it does not require repeated approval when authorization already settles the choice. `--update` makes a missing or unusable parent a hard stop. Ordinary parent selection requires a completed classic run for the same target with a manifest.

A composed caller may bind a partial or team parent for a bounded classic `--stop-after 4` child only when the gate verifies the parent's declared 01 through 04 deliveries, project, target, common flags and snapshot. That child carries only 01 through 04 into a new classic run, never a team's 08 or a changed-mode resume. Ordinary classic updates still require a completed classic parent; `/codebase-map:team-analyze` has its separate partition-level update path below.

---

### `/codebase-map:team-analyze`

Multi-agent variant of `/codebase-map:analyze` for large or partitioned codebases: auto-detects partitions, runs the structural/behavioral/quality phases in parallel per partition across two waves, then consolidates into the same `01..07.md` layout plus a global cross-partition interconnect map, all inside an isolated run directory.

**Prerequisites:** the required providers listed in the generated reference below, including `report-rendering`. Worker dispatch, context isolation and the delivery barrier come from the harness the compiler generates for each host; no separate team runtime is required. The kernel bodies name no host coordination primitive.

| | |
|---|---|
| **Invoke** | `/codebase-map:team-analyze <target> [--format sqlite\|json] [--critical] [--comments] [--depth=lite\|full] [--partition <path>] [--partition-name <name>] [--skip-interconnect] [--skip-synthesis] [--run-name <name>] [--yes] [--update] [--no-update]` |

`--partition-name <name>` gives the N-th manual `--partition` a symbolic name; without it the name derives from the path basename. `--phase N` and `--docs-only` are rejected with an explicit error that points to `/codebase-map:analyze`.

**Pipeline:**

0. **Project knowledge discovery**: the same Phase 0 as `/codebase-map:analyze`, run once inline for the whole run before partition detection. It is global, not per partition, and no worker owns any of its output: `knowledge/navigation.md` and `knowledge/documentation-leads.md`.
1. **Partition detection** (its own Phase 0): explicit workspace manifests (pnpm/npm workspaces, Lerna, Nx, Turbo, Cargo, uv) -> convention-based monorepo layout (`apps/`, `packages/`, `services/`) -> frontend/backend layer split -> language-cluster split -> single-partition fallback. Stylesheets never form a language partition: they stay in the partition of the code they style, because a cascade finding needs the stylesheet and the component tree side by side. Shows the concrete partitions, mode and actual worker count before dispatch. A fresh run proceeds on the invocation's authorization, without requiring `--yes`. An unresolved choice or an explicit request to approve the plan gets a concrete question through a permitted input tool or ordinary chat; normal replies can accept or change the plan. There is no team-creation step: the host harness dispatches each worker and records it as delivered or failed.
2. **Wave 1** (parallel): one `partition-structure-worker` per partition writes structure and interfaces.
3. **Wave 2** (parallel): `partition-behavior-worker` and `partition-quality-worker` per partition write flows/semantics and risks/documentation, each citing sibling partitions' Wave 1 output for cross-partition calls. Under `--depth=lite` the behavior workers are not spawned and quality workers write risks only.
4. **Synthesis**: `partition-synthesizer` consolidates every partition's output into the standard `01-structure.md` through `07-final-report.md` files inside the run directory, flagging any failed partition inline.
5. **Interconnect map**: `codebase-map:semantic-interconnect-mapper` reads the consolidated output and produces `08-interconnect-map.md`, the global cross-partition contract/invariant map that `/senior-review:team-review` reuses directly.
6. **Publish**: the coordinator requires every worker's accounted delivery, a gate result with `complete` and `may_publish`, and every requested view before replacing the root mirror with the declared consolidated set. Failed or missing partition or worker delivery prevents publication even if synthesis wrote warning reports; those reports stay in the run. `--skip-interconnect` omits 08 by declaration, while `--skip-synthesis` also skips interconnect and keeps all results run-local.

```
/codebase-map:team-analyze .                                   # auto-detect, full depth
/codebase-map:team-analyze . --depth=lite                      # lite mode, fewer agents
/codebase-map:team-analyze . --partition packages/api --partition packages/web --yes
/codebase-map:team-analyze .                                   # second time: partitions that did not change are copied, not re-run
/codebase-map:team-analyze . --update                          # require a usable team parent; none is a hard stop
```

**Incremental updates at partition granularity.** A second team run on the same target diffs the last completed team run's snapshot against the worktree, once for the whole tree, and assigns each affected file to its partition. A partition with no affected file is copied whole from the parent run and gets no worker; a partition with at least one is re-analyzed through both waves exactly as in a fresh run. Synthesis and the interconnect map always run, because both are cross-partition by construction. The partition checkpoint labels each partition `unchanged (copied)` or `re-analyzed (N affected files)` before anything is dispatched, and the completion output repeats that split with a pointer to the `## Partitions` table in `changes.md`. The parent's partition set must match this run's exactly; a partition that appeared, vanished or was renamed forces a full run, with the reason named. The scope preview is always shown; choosing update versus full analysis waits only when the request or earlier answers have not settled it. `--yes` or an ordinary-language instruction to follow the recommendation selects the recommended eligible mode. `--update` still requires a usable parent and stops if none exists.

Resume-safe: re-running against an in-progress run in `runs.json` re-spawns only the missing workers for the phase that stopped.

---

**Related:** [project-knowledge](project-knowledge.md) (owns audience-specific project documentation) | [senior-review](senior-review.md) (code review agents that run after the Codebase Map)

## Atomic method and output contracts

Each phase has one canonical skeleton. Team workers use the same common headings and only the extensions declared for their writer; synthesis follows their placement and aggregation. Classic and partition state ownership remain distinct.

Method loads tables describe bounded reads by role and mode. A path mentioned for provenance or in a worker brief is not a coordinator load. Static budgets measure declared instructions, not runtime enforcement or billed tokens.

Optional methodology, patterns and comment taxonomy have declared on-demand reads, including nested reading guidance. The guard checks every combination, deduplicating shared sections. It reports unchanged core caps separately from the frozen optional baselines of the pre-refactor resources; those optional loads existed before this guard measured them.

### Runtime rationale

Classic analysis keeps its selected phases together in one isolated `map-analyst` context. The coordinator presents scope, resolves mode and flags, prepares the run and initial current snapshot, then dispatches the analyst. It does not read analyzed source or execute phase procedures. The analyst follows the declared phase loads in order and owns snapshot refresh during analysis; the coordinator checks the resulting artifacts, recovers incomplete produced work, verifies requested views and publishes only eligible delivery. An empty response or stopped worker is not a delivery.

The invocation and prior answers supply authorization. Present the scope without pausing merely because a checkpoint exists; ask only for an unresolved material choice or an explicitly requested approval. For a large, multi-language or multi-workspace target, recommend `/codebase-map:team-analyze` before dispatch and resolve the mode choice from that authorization or an answer. Classic remains one isolated analysis context; missing required isolation is a concrete capability gap.

The three coverage lines are mandatory, in the condensed lite report as well. A single file count read as coverage is how a blocking defect in an inventoried component once went unreported: the component was in the inventory, the stylesheet that broke it was not, and nothing had exercised the path. The inventory line names what the perimeter left out for the same reason: `.github/` or a generated client is exactly what a reader assumes was read.

## Local MCP integration

The bundled `codebase-map` server exposes 14 tools for project-bound snapshots,
verified source reads, run checkpoints, persistent events, resume, stop and
publication. Request progress reports deterministic operations. The host owns
analysis workers, their lifetime and continuation. Existing shell workflows remain
available independently of the MCP connection. The process that starts the server
may bind a custom project-relative store with `--store`; it carries a
`.codebase-map-store.json` marker so `snapshot.py` commands given a run directory
in it bind the same project. Shell workflows and `migrate_root.py resolve` keep
naming `.codebase-map/`, which stays the default.

See the [MCP contract](../../plugins/codebase-map/skills/map-method/references/mcp.md)
for startup, tool schemas, event cursors and the Tri-Tech Code integration boundary.

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `7.0.1`. **Source:** [plugin.toml](<../../plugins/codebase-map/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [report-rendering](<report-rendering.md>) |
| Direct external | None |
| Local closure (2) | [codebase-map](<codebase-map.md>), [report-rendering](<report-rendering.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `contexts.isolate`, `roles.dispatch`, `mcp.servers`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `codebase-map:map-method` | Static codebase mapping: structure, purpose, integrations and change consequences. Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust, CSS/SCSS/LESS. TRIGGER WHEN: unfamiliar codebases, pre-review context, major refactors, or stale documentation. DO NOT TRIGGER WHEN: the user wants human-readable narrative docs (use /project-knowledge:guide), a public-facing README, or a review verdict (senior-review consumes this output instead). | [map-method](<../../plugins/codebase-map/skills/map-method/SKILL.md>) |
| Role | `codebase-map:map-analyst` | Owns the declared classic Codebase Map phases in one isolated context, reading the bound snapshot and writing only its run's analysis artifacts. TRIGGER WHEN: dispatched by an analysis coordinator with a prepared classic run and resolved scope. | [map-analyst](<../../plugins/codebase-map/roles/map-analyst.md>) |
| Role | `codebase-map:partition-behavior-worker` | Runs Flow Tracing and Semantic Understanding over one partition, reading every partition's structure and interface output so flows and contracts can cite cross-partition boundaries, and writing 03-flows.md and 04-semantics.md into its owned partition directory. TRIGGER WHEN: spawned by /codebase-map:team-analyze in its second wave. | [partition-behavior-worker](<../../plugins/codebase-map/roles/partition-behavior-worker.md>) |
| Role | `codebase-map:partition-quality-worker` | Runs Pattern and Risk Detection plus Documentation Health over one partition, writing 05-risks.md and 06-documentation.md into its owned partition directory (05 only in lite mode). TRIGGER WHEN: spawned by /codebase-map:team-analyze in its second wave. | [partition-quality-worker](<../../plugins/codebase-map/roles/partition-quality-worker.md>) |
| Role | `codebase-map:partition-structure-worker` | Runs Structure Extraction and Interface Analysis over one partition, writing 01-structure.md and 02-interfaces.md into its owned partition directory. TRIGGER WHEN: spawned by /codebase-map:team-analyze in its first wave. DO NOT TRIGGER WHEN: outside that team pipeline. Classic /codebase-map:analyze dispatches isolated codebase-map:map-analyst. | [partition-structure-worker](<../../plugins/codebase-map/roles/partition-structure-worker.md>) |
| Role | `codebase-map:partition-synthesizer` | Consolidates per-partition Codebase Map outputs into 01..07.md in the run directory with cross-partition sections and a team-mode final report. TRIGGER WHEN: spawned by /codebase-map:team-analyze in its consolidation phase. DO NOT TRIGGER WHEN: outside that team pipeline. Classic /codebase-map:analyze dispatches isolated codebase-map:map-analyst. | [partition-synthesizer](<../../plugins/codebase-map/roles/partition-synthesizer.md>) |
| Role | `codebase-map:semantic-interconnect-mapper` | Phase 1b context builder mapping contracts, invariants, domain rules, call graphs and integration boundaries for downstream reviewers and doc writers. TRIGGER WHEN: spawned by /codebase-map:team-analyze, /senior-review:team-review or /project-knowledge:guide, or asked to map contracts, invariants, domain rules or integration boundaries. DO NOT TRIGGER WHEN: no prior context artifact exists yet (run /codebase-map:analyze or codebase-explorer first). | [semantic-interconnect-mapper](<../../plugins/codebase-map/roles/semantic-interconnect-mapper.md>) |
| Workflow | `codebase-map:analyze` | Run a Codebase Map: document WHAT, WHY, HOW and CONSEQUENCES into phased files, with concurrent-run support. TRIGGER WHEN: the user asks for a deep analysis of an unfamiliar codebase, pre-review context, or a structure-plus-semantics snapshot. DO NOT TRIGGER WHEN: the user wants human-readable narrative docs (use /project-knowledge:guide) or a shallow overview. | [analyze](<../../plugins/codebase-map/workflows/analyze.md>) |
| Workflow | `codebase-map:team-analyze` | Multi-agent Codebase Map for monorepos and multi-workspace projects: analyzes partitions in parallel and publishes consolidated results to .codebase-map/. TRIGGER WHEN: running Codebase Map analysis on a monorepo or generating a cross-partition interconnection map. DO NOT TRIGGER WHEN: single small directory or documentation-only audit (use /codebase-map:analyze). | [team-analyze](<../../plugins/codebase-map/workflows/team-analyze.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `codebase-map:analyze`

**Arguments:** <code>&lt;target path&gt; [--format sqlite&#124;json] [--critical] [--comments] [--docs-only] [--phase N] [--depth=lite&#124;full] [--run-name &lt;name&gt;] [--update] [--no-update] [--resume-from [N]] [--stop-after N]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `analyze-completed` |
| Artifacts | `analyze-report` |
| Schemas | None declared |
| Declared workers | `codebase-map/map-analyst` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [analyze.toml](<../../plugins/codebase-map/workflows/analyze.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `preflight` | None | None | `shared` | None declared | `preferred` |
| `analysis` | `preflight` | `map-analyst` | `required` | None declared | `preferred` |
| `publish` | `analysis` | None | `shared` | None declared | `preferred` |

#### `codebase-map:team-analyze`

**Arguments:** <code>&lt;target&gt; [--format sqlite&#124;json] [--critical] [--comments] [--depth=lite&#124;full] [--partition &lt;path&gt;] [--partition-name &lt;name&gt;] [--skip-interconnect] [--skip-synthesis] [--run-name &lt;name&gt;] [--yes] [--update] [--no-update]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `reviewers-use-isolated-contexts`, `every-partition-is-owned-by-one-worker`, `no-worker-writes-outside-its-partition-directory`, `synthesis-runs-after-every-partition-delivered`, `artifacts-published-under-xray-root` |
| Artifacts | `xray-report` |
| Schemas | None declared |
| Declared workers | `codebase-map/partition-behavior-worker`, `codebase-map/partition-quality-worker`, `codebase-map/partition-structure-worker`, `codebase-map/partition-synthesizer`, `codebase-map/semantic-interconnect-mapper` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [team-analyze.toml](<../../plugins/codebase-map/workflows/team-analyze.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `partition-selection` | None | None | `shared` | None declared | `preferred` |
| `structure` | `partition-selection` | `partition-structure-worker`, `per item in selection:partitions` | `required` | `all-delivered` | `preferred` |
| `behavior` | `structure` | `partition-behavior-worker`, `per item in selection:partitions` | `required` | `all-delivered` | `preferred` |
| `quality` | `structure` | `partition-quality-worker`, `per item in selection:partitions` | `required` | `all-delivered` | `preferred` |
| `synthesis` | `behavior`, `quality` | `partition-synthesizer` | `required` | None declared | `preferred` |
| `interconnect` | `synthesis` | `semantic-interconnect-mapper` | `required` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/codebase-map](<../../exports/claude/plugins/codebase-map>) | `native` | `analyze: native-team`, `team-analyze: native-team` |
| copilot | [exports/copilot/plugins/codebase-map](<../../exports/copilot/plugins/codebase-map>) | `adapted` | `analyze: parallel-subagents`, `team-analyze: parallel-subagents` |
| codex | [exports/codex/plugins/codebase-map](<../../exports/codex/plugins/codebase-map>) | `adapted` | `analyze: parallel-subagents`, `team-analyze: parallel-subagents` |
| pi | [exports/pi/plugins/codebase-map](<../../exports/pi/plugins/codebase-map>) | `adapted` | `analyze: parallel-subagents`, `team-analyze: parallel-subagents` |
| opencode | [exports/opencode/plugins/codebase-map](<../../exports/opencode/plugins/codebase-map>) | `adapted` | `analyze: parallel-subagents`, `team-analyze: parallel-subagents` |

### Additional shipped contracts and mechanisms

- Neutral policy: [write-confinement](<../../plugins/codebase-map/policies/write-confinement.toml>). Enforcement is documented in the policy and host reference.
- MCP server `codebase-map`: `uv`, `run`, `--no-config`, `--no-project`, `--script`, `${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/mcp_server.py`. Host registration differs; see the host reference.

<!-- daodan:reference:end -->

## Role-local method reads

Partition workers load common evidence and their owned phase unit. Quality reads
Phase 6 at full depth and comment commands only when that phase runs with comments;
lite retains the risk taxonomy without loading documentation procedures. The mapper
loads evidence and bound-analysis reading, while snapshot refresh remains with its
caller. Tests protect each role's core/optional resource closure and required
sections, and reject invalid conditions or missing resources even on inactive paths.

Step 3 measures source words, not runtime tokens: structure 4,514, behavior 4,521,
quality 4,359 at full depth without comment/document verification and 4,087 in lite,
mapper 5,575. Core caps are 4,514 / 4,521 / 5,299 / 5,575 respectively; existing
optional allowances remain separate and unchanged. These are static load measurements,
not a live-run cost or an installed-host execution claim.

---

## Static analysis engine (`skills/map-method/scripts/`)

The helpers extract structure, resolve internal imports, distinguish static
references from candidates and classify files. They perform static analysis only.
Parser availability, source freshness and unresolved bindings limit what the
resulting graph can say. An empty caller list does not establish that a symbol
is unused.

### Parsing and structural detail

Python uses the standard library AST. Java, JavaScript, TypeScript/TSX and Rust
use Tree-sitter when their grammar is available and identify regex fallback in
`ParseResult.notes` otherwise. SQL and PL/SQL use lexical masking and structural
patterns. CSS, SCSS and LESS retain their stylesheet parser and cascade scanner,
including Tailwind `@apply` expansion.

Optional Tree-sitter changes structural fidelity as follows; its availability is
reported separately from installation:

| Language | Higher-fidelity examples | Regex fallback retains |
|---|---|---|
| Java | Nested classes, generic parameters, annotations and multiline declarations | Top-level classes, methods, imports and constants |
| JavaScript / TypeScript | Arrow functions in object/class properties, decorators, template literals and JSX | Top-level declarations, ES6 import/export and CommonJS require |
| Rust | Lifetimes, generic where bounds, trait-bounded impl blocks and attribute macros | Top-level fns, structs/enums/traits/impls/mods, use declarations and UPPER_CASE constants |

A grammar pack may be installed yet unavailable after a failed download or version
mismatch. The active-backend notes identify the fallback rather than treating
installation as evidence of a working parser.

Tree-sitter grammars are shared across threads; mutable parsers and queries are
cached per thread. `get_parser.cache_clear()` invalidates existing thread caches.
TypeScript extends JavaScript extraction from the same parsed root, avoiding a
second parse of TS/TSX files.

Types and their members use the existing `ClassInfo`, `FunctionInfo`, `bases` and
`class_variables` fields. This includes TypeScript interfaces, type aliases,
enums, namespaces, abstract classes and heritage; Java records, annotations,
nested types and enum members; and Rust modules, fields, variants, implementations,
traits, constants, aliases and macros. Recognized JavaScript component wrappers
retain their callable binding; a callback passed to an ordinary collection
operation does not turn its result into a function.

Syntax errors remain explicit. An intact declaration in a damaged source file
can remain in the manifest, with `status = "parse-error"`; source reading still
returns the full file rather than trusting a partial selection.

`FunctionInfo.calls_made` contains distinct outgoing call names in source order.
Native AST queries cover JavaScript/TypeScript, Java and Rust, including
construction and Rust macro calls. Nested callable bodies are attributed to their
own callable. File-level `external_calls` use actual call nodes when a native
parse is available, excluding call-like text in comments and string literals.
These are syntactic call names, not dynamically resolved runtime targets.

### Source-bound references and callsites

`ParseResult.semantic` is optional additive metadata, extracted from the existing
Python AST or shared native JavaScript/TypeScript tree. It contains version,
backend, status, notes, scopes, declarations, imports, exports and references.
Regex fallback and damaged native syntax leave this payload absent; other
language adapters retain their existing structural extraction.

Reference spans are `[start_line, start_column, end_line, end_column]`: lines are
one-based, columns are zero-based UTF-8 byte offsets, and ends are exclusive. A
callsite spans its callee expression and records its closest callable owner.
Repeated calls retain separate locations. Comments and literal text are excluded;
formatted-string and template substitutions remain code. Source-local declaration
IDs are qualified as `file::source_id` in the project index. These IDs identify
one snapshot, not a declaration across revisions.

Storage-backed semantic resolution follows the same conservative binding rules
as the explicit in-memory `semantic_index.build_semantic_index` API.
Only unique lexical function/class bindings and direct internal named, default
or namespace imports receive declaration targets. Parameters, assignments and
other binding sites prevent lookup from bypassing shadowing or rebinding.
Uncertain scopes, dynamic receivers, computed properties, type-only imports,
constants, unsupported export chains and ambiguous declarations retain explicit
unresolved reasons. This is a bounded binding layer, without compiler type
inference or project execution.

The snapshot stores semantic payloads beside `raw_hash` under its parser/helper
fingerprint. Production extraction uses `write_snapshot` and an explicit
`SnapshotStore`: derived facts and hashes are persisted, then observed source
bytes and parse payloads are released. Semantic bindings and graph indexes are
derived in the owned staging store.
Queries validate permitted live sources, hashes, fingerprint, payload shape,
scope links and spans. Stale, excluded, malformed or unbound entries cannot supply
resolved references. Unavailable backends retain explicitly lexical candidates.

`build_manifest(..., source_observations=...)` remains an explicit in-memory API
for legacy callers and fixtures; the progressive writer does not call it.
Its optional observations bind one operation's bytes, not later filesystem
freshness. An old parser snapshot can remain historical evidence without
qualifying current-source queries or incremental reuse.

`analyze_file.py` exposes `semantic_analysis` even without `--find-usages`. Its
public view contains declarations, outgoing `callsites`, resolved `incoming_calls`,
the target's source identity, coverage status and project coverage counts.
`counts` separates total, resolved and unresolved callsites, incoming calls and
project unresolved calls. Optional symbol lookup inspects all permitted semantic
references, including aliases whose callsites omit the original spelling.
`resolved_count`, `ast_candidate_count` and `lexical_candidate_count` remain
separate; the legacy usage total includes candidates. Per-location `precision`,
`span`, `caller`, `target_id` and `reason` expose the supporting fact. Neither AST
candidates nor lexical matches assert a declaration target or runtime execution.

### Graph-guided mapping from the current snapshot

`source_reader.py graph <source_manifest> --path src/service.py --hops 3 --limit 100`
queries the supplied snapshot without reparsing or creating another authoritative
index. Repeat exact-file seeds, or omit `--path` for the inventoried scope. Resolved
symbol edges expand toward both callers and callees; unresolved calls never drive
expansion. Imports, cycles, reverse reachability and PageRank remain separate
reading aids. Queries verify source hashes, parser identity and the current
perimeter; stale or malformed evidence requires a caller-owned snapshot refresh.
Unavailable semantic backends remain explicit coverage gaps.

The `xray/source-graph/v1` packet binds the canonical manifest digest and query,
returns callsite/declaration identities and spans, and exposes section totals and
truncation. Its `requests` can feed `source_reader.py read --requests` when saved
at an owned run-artifact path. Select the evidence relevant to the phase question;
the packet does not require reading every returned file. Graph/outline metadata
does not count as deep reading, and resolved links do not verify contracts.

Mapping instructions require this query before structural, call and flow mapping,
including partition workers and the semantic interconnect mapper. Usage search
supplements dynamic, uncovered or ambiguous cases. Phase reports retain graph
coverage and actual source-reading provenance separately. This is a tested
instruction contract; no installed-host execution enforcement is asserted.

### Import graph and classification

`ts_path_config(target)` reads bounded JSONC configuration, including relative
`extends`, `baseUrl`, `paths`, package-local configurations and workspace package
entry points. Configuration outside the selected target, ignored content and
excluded directories cannot expand the analysis perimeter. Package-based external
`extends` and runtime bundler hooks are not executed.

`module_targets(manifest, config=None)` returns resolved internal target paths
for every importing file. It shares resolution between incremental blast radius,
usage discovery and fan-in. Relative imports, configured aliases and workspace
exports resolve against files actually present in the manifest. An unresolved
external package does not become an internal dependency merely because a source
file has the same basename.

`compute_fan_in(target_dir, perimeter=None, manifest=None)` counts distinct
importing files, excluding self-imports. `classify_directory` shares one graph
across its files. Classification retains its existing categories: at eight
importers a small hub requires high-complexity verification; at fifteen it is
critical. `imported_by_count` is the observed count, not a numeric importance
score. Existing critical-pattern rules still apply.

`analyze_file.py` reports fan-in even without `--find-usages`, independently of
which exported symbols the optional usage query selects. JSON adds
`imported_by_count` and callable `calls_made` without removing existing fields.
The target's bytes and parse feed the same manifest through `parse_results`;
classification and optional batched usage discovery reuse that manifest.

### Transitive import diagnostics

`dependency_graph.dependency_graph_metrics` consumes the existing confined graph,
with edges from importing file to dependency. It returns sorted nodes/edges,
`import_cycles` as strongly connected components (including self-imports), and
PageRank. Cycle traversal is iterative, so long import chains do not consume the
Python call stack. The module performs no source reads.

`transitive_importers(reverse_index, seeds)` returns records shaped as
`{file, depth, via, seed}`. `depth` is the shortest hop count; `via` is the immediate
predecessor and `seed` the originating changed file, allowing a witness path to be
reconstructed. Sorted seeds and neighbors make equal-length choices deterministic.
Seeds are excluded from results, and missing files receive no invented edges.

File analysis adds a `dependency_graph` view with graph counts, target cycle
components, project cycle count, transitive importers and target PageRank. Change
reports add `import_cycles`, `transitive_importers`, `transitive_seeds` and graph
metadata. Existing one-hop `importers`, `affected_files`, claim invalidation and
update recommendations retain their behavior; transitive diagnostics do not
silently broaden them.

PageRank uses uniform teleportation, distributes dangling-node mass, and defaults
to damping `0.85`, L1 tolerance `1e-10` and at most `100` iterations. The returned
`pagerank_converged`, `pagerank_iterations`, `pagerank_damping`,
`pagerank_tolerance` and `pagerank_max_iterations` describe the final iterate,
including non-convergence. Rank is an aid to choosing what to read, not a new
criticality threshold or evidence that a change propagates at runtime.

### Bounded work and performance

The writer still inventories and hashes its target. Unchanged entries reuse
structure only after source and parser checks. Production storage writes one
file record at a time and releases its parse; readers use explicit iterators,
lookups and operation-owned connections instead of rebuilding a global manifest.
The in-memory compatibility API is a separate path, not the production memory
contract.

Semantic lookup and graph queries use persisted facts and indexes. JSON readers
build an operation-owned temporary semantic index when needed and remove it on
close. Bounded responses expose exact totals and truncation; lexical fallback
reads one permitted file at a time. Separate lexical search helpers retain their
ripgrep/grep/Python backends. Multiple symbol requests reuse the bound store,
not a new project parse or a retained collection of every source text.

Semantic extraction enriches eligible snapshots by default. It avoids another
parse but adds traversal time and payload size. The following historical
per-file adapter sample predates the SQLite storage change; it does not measure
SQLite extraction, refresh, query latency or database size. The Windows sample used
Python 3.13.14, Tree-sitter 0.26.0 and language-pack 1.13.5, warm grammars and nine
repetitions per mode. Medians compare the same adapter with and without its
semantic hook; they measure added extraction cost, not a speedup:

| Input | Source bytes | Compact UTF-8 metadata bytes | Parse with metadata, ms | Without semantic hook, ms |
|---|---:|---:|---:|---:|
| Python adapter source, 466 lines | 15,953 | 87,907 | 34.543 | 26.961 |
| Generated JS, 200 exported functions | 19,730 | 219,339 | 51.149 | 33.862 |
| Equivalent TS with string annotations | 22,930 | 220,139 | 62.344 | 37.549 |

The JS/TS workload imports `save as persist` and repeats functions that assign a
local parameter value and call `persist` directly and inside a template
substitution. These samples show a material size and time cost for richer static
evidence; they do not establish performance for other projects. Tests distinguish
read/parse reuse from elapsed-time or token savings. Application runtime coverage
remains none; semantic embeddings, new language backends and host-native graph
integration are outside this increment.
