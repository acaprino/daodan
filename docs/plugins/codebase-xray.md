# Codebase X-Ray Plugin

> Understand any codebase in minutes. Eight-phase analysis discovers how the project documents itself, maps structure, traces flows, identifies risks, and documents the WHY behind the code, not just what it does. Renamed from `deep-dive-analysis` in plugin 2.0.0 (marketplace 14.0.0); its output artifact directory followed in plugin 4.0.0 and is now `.codebase-xray/`.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Concurrent runs

Every analysis is an isolated run under `.codebase-xray/runs/<run-id>/` with its own `state.json`, registered in `.codebase-xray/runs.json`. Multiple analyses can proceed at the same time (different targets, different sessions, or a re-analysis alongside an older one) without touching each other's files. On completion a run is **published**: its `01..07.md` files (plus `08-interconnect-map.md`, which only a team run produces) are mirrored to the `.codebase-xray/` root, which is the stable contract downstream consumers read (`/senior-review:team-review`, `/senior-review:code-review`, `/project-knowledge:guide`, `/project-knowledge:instructions --create`). Use `--run-name <name>` for explicit run identity; otherwise the run-id derives from the target slug plus a timestamp.

Every run also records the tree it analyzed as `snapshot/manifest.json`: each file in its inventory with its size, mtime and content hash, each symbol with its span and body hash. The inventory has three sets: source in the parsed languages, configuration and documentation, and presentation files no adapter parses (markup and indented Sass, file-level with no symbols; the exact set is `PRESENTATION_EXTENSIONS` in `snapshot.py`). Stylesheets entered the inventory in plugin 4.1.0, after a global dark-theme rule that locked users out of a consent screen sat in a `.css` file no run had ever recorded, and became a parsed language in 4.2.0: CSS, SCSS and LESS carry one symbol per applied rule, so an edit to one rule marks stale the claims about that rule and about the at-rule or parent rule enclosing it, as a class encloses its methods, never those about its siblings. A minified stylesheet, one with any line longer than 10,000 characters, stays file-level with no symbols. Anything else is absent from the manifest, and the final report's metadata states three coverage figures, files in inventory, files read in depth and files exercised at runtime (always none, unless the user supplied runtime evidence), so that a file count is never read as coverage. A later run on the same target detects that snapshot, diffs it against the current worktree with no model tokens spent, and offers an incremental update. This claim-level carry is `/codebase-xray:analyze` only: unaffected claims are carried over verbatim, only the claims citing changed symbols or their direct importers are re-derived, and a mechanical gate refuses to publish while any of them is still marked stale. `/codebase-xray:team-analyze` updates at the coarser partition granularity instead: a partition with no affected file is copied whole from the parent run, and a partition with any affected file is re-analyzed in full, never carried claim by claim. Each run records its parent, so the chain under `.codebase-xray/runs/` is the analysis history, and `changes.md` in each run says what changed in the code and what that did to the claims. `--update` requires that a usable parent run exists and stops rather than falling back to a silent full run when one does not; execution mode is still resolved separately at the scope checkpoint. `--no-update` skips detection entirely. A target that changed too much is reported as needing a full run rather than being updated quietly.

## Reading source from a snapshot

`snapshot/manifest.json` is the single structural index for a bound run.
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

Load `codebase-xray:xray-method` for exact `source_reader.py outline` and `read`
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

Below its target the X-ray never analyzes what Git ignores, any directory whose name starts with a dot, or dependency and build output (`node_modules/`, `dist/`, `build/`, `target/`, `vendor/`, `venv/`, `__pycache__/`). The rule has one owner, `tree_scope.py`, and every script that walks a tree applies it: the snapshot, the cascade scan, the usage search, the comment scan and the documentation review. No script reads more than the snapshot records.

The rule dates from plugin 5.1.0. Tools write beside the code they work on: a lifecycle campaign left its run records under `.daodan/` and its review under `.team-review/`, the next snapshot counted them as project files, and an incremental update of an untouched project asked for a full analysis. A list of known tool directories would have let the next tool's output in, so the rule is general. A parent run recorded before this rule holds paths the perimeter now leaves out. Its first update reports them as removed and retires the claims that cite them: they left the inventory, whether or not they left the disk.

Two properties keep it from hiding anything. The target is analyzed as given: `/codebase-xray:analyze .github/` is how a project's CI gets an X-ray, and a dot file beside analyzed source (`.eslintrc.json`) is not a directory and stays. And the exclusion is declared: `snapshot.py scope <target>` prints it for the scope confirmation, the manifest's `scope` block keeps it (`git_ignore` is `unavailable` when the target is in no work tree, in which case no ignore rule was applied), and the final report's inventory line repeats it. A file Git tracks is never ignored, whatever pattern it matches.

## Agents

### Partition workers

These four agents exist to serve `/codebase-xray:team-analyze` below. The classic `/codebase-xray:analyze` command runs its eight phases inline without spawning these agents; nothing here is used outside the team pipeline.

| Agent | Model | Runs during | Produces (inside the run directory) |
|-------|-------|--------------|----------|
| `partition-structure-worker` | `inherit` | Phase 1 Wave 1: Structure + Interfaces | `partitions/<name>/01-structure.md`, `02-interfaces.md` |
| `partition-behavior-worker` | `inherit` | Phase 1 Wave 2: Flows + Semantics (skipped under `--depth=lite`) | `partitions/<name>/03-flows.md`, `04-semantics.md` |
| `partition-quality-worker` | `inherit` | Phase 1 Wave 2: Risks + Documentation | `partitions/<name>/05-risks.md`, `06-documentation.md` (05 only under `--depth=lite`) |
| `partition-synthesizer` | `inherit` | Phase 2: Consolidation | `01-structure.md` through `07-final-report.md` (consolidated across partitions) |

Each worker owns only its listed output files and never touches another partition's files, the consolidated output, or the `.codebase-xray/` root (other runs may be in flight). Cross-partition references use `<other-partition>::<symbol>` citation notation.

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
| `/codebase-xray:team-analyze` | Phase 3 | `08-interconnect-map.md`, the global cross-partition view |
| `/senior-review:team-review` | Phase 1b | `.team-review/02-interconnect.md`, which every reviewer reads and which `logic-integrity-auditor` requires |
| `/project-knowledge:guide` | Guide preparation, when needed by the file/audience plan | The owned run's interconnect report, cited by the assigned writers and `guide-reviewer` |

**Output sections:** `## Target scope`, `## Call Graph`, `## Contracts` (formal, structural and implicit), `## Invariants` (temporal + structural), `## Domain Rules`, `## Assumptions`, `## Integration Hot-Spots` (HTTP, queue, IPC, env/config), `## Change Impact Radius`, `## Reviewer Hints`. Each section is self-contained so consumers can Grep a single heading and get full context.

Every row carries one of four statuses: `verified` (enforced in code), `documented` (a comment, docstring or project document declares it), `unverified` (the code relies on it but nothing enforces or documents it) or `disputed` (an independent derivation contradicts it, both sides cited). The map opens by declaring itself a **fallible hypothesis index, not ground truth**: a row marked `documented`, `unverified` or `disputed` must be re-derived before it becomes the premise of a finding, and an absent row is not evidence of absence.

Input source differs per pipeline: X-ray output for `team-review`, the consolidated partition set for `team-analyze`, and `codebase-explorer`'s context brief for the `project-knowledge` pipelines. It never proposes fixes; every claim carries a `file:line` citation.

---

## Skills

### `xray-method`

The method itself: structure extraction fused with semantic reading, the concurrent runs model, Phase 0, and the multi-language script suite (Python stdlib-only; optional tree-sitter for Java/JS/TS/Rust fidelity; a stdlib tokenizer for CSS/SCSS/LESS; Python >= 3.10), including `source_reader.py` for validated source blocks and `cascade_scan.py`, which lists the stylesheet rules with global reach that can break a screen. Named `analyze` until plugin 3.0.0, when it shared its name with the command and the command shadowed it on any host that lists both under one identifier.

| | |
|---|---|
| **Load as** | `codebase-xray:xray-method`; the `team-analyze` workers read it directly, and `/codebase-xray:analyze` is the command that applies it |
| **Use for** | Codebase understanding, architecture mapping, onboarding, evidence for a subsequent review |

**Capabilities:**
- Extract code structure (classes, functions, imports)
- Map internal/external dependencies
- Recognize architectural patterns
- Identify anti-patterns and red flags
- Trace data and control flows

---

## Commands

### `/codebase-xray:analyze`

8-phase systematic codebase analysis with per-run state management, output files, and phased execution: project knowledge discovery -> structure -> interfaces -> flows -> semantics -> risks -> documentation -> report.

**Phase 0 (Project Knowledge Discovery)** runs first on every invocation, including `--depth=lite`, `--phase N` and `--docs-only`, and it is a preamble rather than a selectable analysis phase: phases 1 to 7 keep their numbers, so no existing `--phase` invocation changes meaning. It reads the project's own instruction files and indexes and records where the project claims each concept lives, writing `knowledge/navigation.md` and `knowledge/documentation-leads.md`. Both hold **leads, never verified facts**: the phase reads no code, so every row is `documented` or `unverified`. This is the cheap discovery pass, kept deliberately apart from Phase 6, which is the expensive audit of whether those documents are accurate. Conflating the two is what once made lite mode blind to a project's own documentation. `/senior-review:team-review` Phase 1d consumes `knowledge/documentation-leads.md` as one half of its knowledge-provenance join.

**Entry-gating paths** (authentication, onboarding, consent or policy acceptance, first-run setup) are mandatory critical paths in Phase 3 and a `Usability-blocking` category in Phase 5 and in the final risk matrix, since plugin 4.1.0. For client code the trace includes the effective style cascade over the screen, because a global selector that overrode a consent screen's positioning is what once made it impossible to complete on mobile in dark theme, with the component sitting in the inventory the whole time. Since plugin 4.2.0 `cascade_scan.py` does the mechanical half of that cascade reading: it lists every rule whose selector reaches the document root, every element or the root's untargeted children and sets a positioning, scroll, sizing, display or containing-block property, together with the class, id and attribute rules it can override and what decides it in cascade order (`!important`, cascade layer, specificity, source order). Conflicts that define a screen, a fixed or sticky position, a scroll container or a viewport height, come first. When a stylesheet uses Tailwind, the screen-level utilities written in string-literal `class` and `className` attributes count as conflicts too, from Tailwind's `utilities` layer. A rule on the root or mount element itself is reported without overrides, to limit noise, and the report says so rather than implying there are none. Tailwind `@apply` layout utilities count as the declarations they inline, and that is not a detail: on the Phazly stylesheets at commit `d8efc74e147c`, the X-ray's reference, 90% of the applied rules used `@apply` (2,643 of 2,938), all 44 rules of the consent modal's own stylesheet among them, and before the expansion the scan found the dark-theme rule and missed the modal. With it, and with the screen-level utilities read from markup, the same tree reports `.dark #root > div:first-child` beating `.terms-acceptance-modal` on specificity as one of 23 screen-level conflicts, two of them overlays written as `className="fixed ..."` in components, and the tree at the fix commit no longer reports the rule. Whether a candidate and its conflict match the same element depends on the rendered tree, so Phase 5 confirms each one by reading. The X-ray stays static: it names those paths and reports them as not exercised. Exercising them in a browser belongs to the project's own tests or to `frontend-review`, never to this plugin.

```
/codebase-xray:analyze src/core/ --critical
/codebase-xray:analyze src/api --run-name api      # named run, safe to run others concurrently
/codebase-xray:analyze src/                        # second time on the same target: offers an incremental update
/codebase-xray:analyze src/ --update               # require an update base; no usable parent is a hard stop
/codebase-xray:analyze src/ --no-update            # skip detection and run a full analysis
/codebase-xray:analyze src/ --comments             # include the comment quality audit in Phase 6
/codebase-xray:analyze src/ --docs-only            # documentation health only (Phase 6, after Phase 0)
/codebase-xray:analyze src/ --phase 5              # run one phase (here pattern and risk detection)
```

**Output:** `.codebase-xray/runs/<run-id>/` with a `knowledge/` directory from Phase 0, the phase files `01-structure.md` through `06-documentation.md`, the final report `07-final-report.md` (condensed under `--depth=lite`, which also skips 03, 04 and 06), and a `snapshot/manifest.json` recording the tree the run read. A classic run never writes `08-interconnect-map.md`. The phase files and the report are published to the `.codebase-xray/` root on completion; the snapshot, and on an incremental run `changes.json` and `changes.md`, stay in the run directory.

#### Incremental updates

The first X-ray of a target is always a full run, and it writes the snapshot that makes the next one cheap. Every later invocation on the same target starts by finding the last completed classic run for it and diffing that run's snapshot against the current worktree. The diff is mechanical and spends no model tokens: its default content check trusts equal size and mtime, while `--verify` hashes every file and is required for evidence freshness. Parser identity changes invalidate cached structure. A changed symbol is found by comparing the hash of its definition. The scope checkpoint then shows the result before semantic reading:

```
X-ray target: src
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

Accepting the update carries every claim the change set did not touch forward byte for byte, with `file:line` citations renumbered where lines shifted, and re-derives only the claims that cite a changed symbol, a changed file, or a file that imports one. New symbols get new claims, removed symbols lose theirs, and the final report is regenerated from the phase files. A mechanical gate then refuses to publish while any re-derivation is still marked pending, so an incremental result is either finished or not published. `changes.md` in the run directory records what changed in the code and what happened to each affected claim, and `state.json` names the parent run, so the chain of runs under `.codebase-xray/runs/` is the analysis history.

The checkpoint recommends a full run instead, with the reason printed, when more than 40% of the files are affected, when the parent has no snapshot (a run from before this feature), when the parent did not complete, or when the flags differ from the parent's. The incremental option stays selectable in every case: the recommendation is advice and the user decides. Neither `--update` nor `--no-update` skips the checkpoint. `--update` only makes a missing or unusable parent a hard stop rather than a silent full run, which is the form for scripts and pipelines that must not quietly pay for a full analysis. A team run is never a usable parent for the classic command, because its interconnect map is cross-partition output this command has no phase to regenerate; `/codebase-xray:team-analyze` has its own update path at partition granularity, described below.

---

### `/codebase-xray:team-analyze`

Multi-agent variant of `/codebase-xray:analyze` for large or partitioned codebases: auto-detects partitions, runs the structural/behavioral/quality phases in parallel per partition across two waves, then consolidates into the same `01..07.md` layout plus a global cross-partition interconnect map, all inside an isolated run directory.

**Prerequisites:** none beyond the host. Worker dispatch, context isolation and the delivery barrier come from the harness the compiler generates for each host, so the plugin declares no dependency and its bodies name no host primitive.

| | |
|---|---|
| **Invoke** | `/codebase-xray:team-analyze <target> [--critical] [--comments] [--depth=lite\|full] [--partition <path>] [--partition-name <name>] [--skip-interconnect] [--skip-synthesis] [--run-name <name>] [--yes] [--update] [--no-update]` |

`--partition-name <name>` gives the N-th manual `--partition` a symbolic name; without it the name derives from the path basename. `--phase N` and `--docs-only` are rejected with an explicit error that points to `/codebase-xray:analyze`.

**Pipeline:**

0. **Project knowledge discovery**: the same Phase 0 as `/codebase-xray:analyze`, run once inline for the whole run before partition detection. It is global, not per partition, and no worker owns any of its output: `knowledge/navigation.md` and `knowledge/documentation-leads.md`.
1. **Partition detection** (its own Phase 0): explicit workspace manifests (pnpm/npm workspaces, Lerna, Nx, Turbo, Cargo, uv) -> convention-based monorepo layout (`apps/`, `packages/`, `services/`) -> frontend/backend layer split -> language-cluster split -> single-partition fallback. Stylesheets never form a language partition: they stay in the partition of the code they style, because a cascade finding needs the stylesheet and the component tree side by side. Shows the concrete partitions, mode and actual worker count before dispatch. A fresh run proceeds on the invocation's authorization, without requiring `--yes`. An unresolved choice or an explicit request to approve the plan gets a concrete question through a permitted input tool or ordinary chat; normal replies can accept or change the plan. There is no team-creation step: the host harness dispatches each worker and records it as delivered or failed.
2. **Wave 1** (parallel): one `partition-structure-worker` per partition writes structure and interfaces.
3. **Wave 2** (parallel): `partition-behavior-worker` and `partition-quality-worker` per partition write flows/semantics and risks/documentation, each citing sibling partitions' Wave 1 output for cross-partition calls. Under `--depth=lite` the behavior workers are not spawned and quality workers write risks only.
4. **Synthesis**: `partition-synthesizer` consolidates every partition's output into the standard `01-structure.md` through `07-final-report.md` files inside the run directory, flagging any failed partition inline.
5. **Interconnect map**: `codebase-xray:semantic-interconnect-mapper` reads the consolidated output and produces `08-interconnect-map.md`, the global cross-partition contract/invariant map that `/senior-review:team-review` reuses directly.
6. **Publish**: the consolidated set (and interconnect map) is mirrored to the `.codebase-xray/` root for downstream consumers, and the run is closed in `runs.json`.

```
/codebase-xray:team-analyze .                                   # auto-detect, full depth
/codebase-xray:team-analyze . --depth=lite                      # lite mode, fewer agents
/codebase-xray:team-analyze . --partition packages/api --partition packages/web --yes
/codebase-xray:team-analyze .                                   # second time: partitions that did not change are copied, not re-run
/codebase-xray:team-analyze . --update                          # require a usable team parent; none is a hard stop
```

**Incremental updates at partition granularity.** A second team run on the same target diffs the last completed team run's snapshot against the worktree, once for the whole tree, and assigns each affected file to its partition. A partition with no affected file is copied whole from the parent run and gets no worker; a partition with at least one is re-analyzed through both waves exactly as in a fresh run. Synthesis and the interconnect map always run, because both are cross-partition by construction. The partition checkpoint labels each partition `unchanged (copied)` or `re-analyzed (N affected files)` before anything is dispatched, and the completion output repeats that split with a pointer to the `## Partitions` table in `changes.md`. The parent's partition set must match this run's exactly; a partition that appeared, vanished or was renamed forces a full run, with the reason named. The scope preview is always shown; choosing update versus full analysis waits only when the request or earlier answers have not settled it. `--yes` or an ordinary-language instruction to follow the recommendation selects the recommended eligible mode. `--update` still requires a usable parent and stops if none exists.

Resume-safe: re-running against an in-progress run in `runs.json` re-spawns only the missing workers for the phase that stopped.

---

**Related:** [project-knowledge](project-knowledge.md) (owns audience-specific project documentation) | [senior-review](senior-review.md) (code review agents that run after the X-ray)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `5.3.0`. **Source:** [plugin.toml](<../../plugins/codebase-xray/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | None |
| Local closure (1) | [codebase-xray](<codebase-xray.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `codebase-xray:xray-method` | X-ray method: mechanical structure extraction fused with semantic reading into a ground-truth account of WHAT, WHY, HOW and CONSEQUENCES. Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust, CSS/SCSS/LESS. TRIGGER WHEN: encountering an unfamiliar codebase, needing pre-review technical context, before a major refactor, or when documentation is stale or missing. DO NOT TRIGGER WHEN: the user wants human-readable narrative docs (use /project-knowledge:guide), a public-facing README, or a review verdict (senior-review consumes this output instead). | [xray-method](<../../plugins/codebase-xray/skills/xray-method/SKILL.md>) |
| Role | `codebase-xray:partition-behavior-worker` | Runs Flow Tracing and Semantic Understanding over one partition, reading every partition's structure and interface output so flows and contracts can cite cross-partition boundaries, and writing 03-flows.md and 04-semantics.md into its owned partition directory. TRIGGER WHEN: spawned by /codebase-xray:team-analyze in its second wave. | [partition-behavior-worker](<../../plugins/codebase-xray/roles/partition-behavior-worker.md>) |
| Role | `codebase-xray:partition-quality-worker` | Runs Pattern and Risk Detection plus Documentation Health over one partition, writing 05-risks.md and 06-documentation.md into its owned partition directory (05 only in lite mode). TRIGGER WHEN: spawned by /codebase-xray:team-analyze in its second wave. | [partition-quality-worker](<../../plugins/codebase-xray/roles/partition-quality-worker.md>) |
| Role | `codebase-xray:partition-structure-worker` | Runs Structure Extraction and Interface Analysis over one partition, writing 01-structure.md and 02-interfaces.md into its owned partition directory. TRIGGER WHEN: spawned by /codebase-xray:team-analyze in its first wave. DO NOT TRIGGER WHEN: outside that pipeline; /codebase-xray:analyze extracts structure inline without an agent. | [partition-structure-worker](<../../plugins/codebase-xray/roles/partition-structure-worker.md>) |
| Role | `codebase-xray:partition-synthesizer` | Consolidates per-partition X-ray outputs into the standard 01..07.md layout in the run directory, adding cross-partition sections and a team-mode final report, byte-compatible with a classic single-agent run. TRIGGER WHEN: spawned by /codebase-xray:team-analyze in its consolidation phase. DO NOT TRIGGER WHEN: outside that pipeline; /codebase-xray:analyze writes its phase files directly. | [partition-synthesizer](<../../plugins/codebase-xray/roles/partition-synthesizer.md>) |
| Role | `codebase-xray:semantic-interconnect-mapper` | Phase 1b context builder whose output downstream reviewers, doc writers and drift hunters work against. Produces no verdicts of its own. TRIGGER WHEN: spawned by /codebase-xray:team-analyze, /senior-review:team-review or /project-knowledge:guide, or the user explicitly asks to map contracts, invariants, domain rules, call graphs, or integration boundaries. DO NOT TRIGGER WHEN: no prior context artifact exists (neither .codebase-xray/ nor codebase-explorer's context-brief.md), or the task is a surface-level operation that does not need the map. | [semantic-interconnect-mapper](<../../plugins/codebase-xray/roles/semantic-interconnect-mapper.md>) |
| Workflow | `codebase-xray:analyze` | Run an X-ray: document WHAT, WHY, HOW and CONSEQUENCES into phased files, with concurrent-run support. TRIGGER WHEN: the user asks for a deep analysis of an unfamiliar codebase, pre-review context, or a structure-plus-semantics snapshot. DO NOT TRIGGER WHEN: the user wants human-readable narrative docs (use /project-knowledge:guide) or a shallow overview. | [analyze](<../../plugins/codebase-xray/workflows/analyze.md>) |
| Workflow | `codebase-xray:team-analyze` | Multi-agent X-ray for large or multi-workspace codebases: splits the project into its natural units, works them in parallel, and publishes one consolidated result set to the .codebase-xray/ root. TRIGGER WHEN: the user wants X-ray analysis on a monorepo, or a cross-partition interconnection map produced as part of the same flow. DO NOT TRIGGER WHEN: the target is a single small directory, or the user wants a documentation-only audit (use /codebase-xray:analyze, optionally with --docs-only). | [team-analyze](<../../plugins/codebase-xray/workflows/team-analyze.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `codebase-xray:analyze`

**Arguments:** <code>&lt;target path&gt; [--critical] [--comments] [--docs-only] [--phase N] [--depth=lite&#124;full] [--run-name &lt;name&gt;] [--update] [--no-update]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `analyze-completed` |
| Artifacts | `analyze-report` |
| Schemas | None declared |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [analyze.toml](<../../plugins/codebase-xray/workflows/analyze.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

#### `codebase-xray:team-analyze`

**Arguments:** <code>&lt;target&gt; [--critical] [--comments] [--depth=lite&#124;full] [--partition &lt;path&gt;] [--partition-name &lt;name&gt;] [--skip-interconnect] [--skip-synthesis] [--run-name &lt;name&gt;] [--yes] [--update] [--no-update]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `reviewers-use-isolated-contexts`, `every-partition-is-owned-by-one-worker`, `no-worker-writes-outside-its-partition-directory`, `synthesis-runs-after-every-partition-delivered`, `artifacts-published-under-xray-root` |
| Artifacts | `xray-report` |
| Schemas | None declared |
| Declared workers | `codebase-xray/partition-behavior-worker`, `codebase-xray/partition-quality-worker`, `codebase-xray/partition-structure-worker`, `codebase-xray/partition-synthesizer`, `codebase-xray/semantic-interconnect-mapper` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [team-analyze.toml](<../../plugins/codebase-xray/workflows/team-analyze.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `partition-selection` | None | None | `shared` | None declared | `preferred` |
| `structure` | `partition-selection` | `partition-structure-worker`, `per item in selection:partitions` | `required` | `all-delivered` | `preferred` |
| `behavior` | `structure` | `partition-behavior-worker`, `per item in selection:partitions` | `required` | `all-delivered` | `preferred` |
| `quality` | `structure` | `partition-quality-worker`, `per item in selection:partitions` | `required` | `all-delivered` | `preferred` |
| `interconnect` | `behavior` | `semantic-interconnect-mapper` | `required` | None declared | `preferred` |
| `synthesis` | `behavior`, `quality`, `interconnect` | `partition-synthesizer` | `required` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/codebase-xray](<../../exports/claude/plugins/codebase-xray>) | `native` | `analyze: native-team`, `team-analyze: native-team` |
| copilot | [exports/copilot/plugins/codebase-xray](<../../exports/copilot/plugins/codebase-xray>) | `native` | `analyze: parallel-subagents`, `team-analyze: parallel-subagents` |
| codex | [exports/codex/plugins/codebase-xray](<../../exports/codex/plugins/codebase-xray>) | `adapted` | `analyze: parallel-subagents`, `team-analyze: parallel-subagents` |
| pi | [exports/pi/plugins/codebase-xray](<../../exports/pi/plugins/codebase-xray>) | `adapted` | `analyze: parallel-subagents`, `team-analyze: parallel-subagents` |
| opencode | [exports/opencode/plugins/codebase-xray](<../../exports/opencode/plugins/codebase-xray>) | `native` | `analyze: parallel-subagents`, `team-analyze: parallel-subagents` |

### Additional shipped contracts and mechanisms

- Neutral policy: [write-confinement](<../../plugins/codebase-xray/policies/write-confinement.toml>). Enforcement is documented in the policy and host reference.

<!-- daodan:reference:end -->
