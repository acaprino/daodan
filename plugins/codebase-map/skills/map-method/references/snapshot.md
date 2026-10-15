# Snapshot

After scope confirmation and before Phase 0, the coordinator writes every run's
initial current manifest. Classic refresh ownership then transfers to the isolated
analyst; team ownership remains with the coordinator. Partition workers and the
mapper report refresh gaps rather than changing its manifest.

The manifest records file sizes, mtimes and content hashes, symbol spans/body
hashes, and the git commit as metadata, making this run a possible parent.
Immediately copy its own `git` field into state; retain preflight's real parent,
base snapshot time and incremental counts. Preserve parent snapshots.

## Incremental Update Commands

### 14. Count the scope, then write a structural snapshot

```bash
# what a run would analyze, and what its perimeter leaves out; parses nothing
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" scope <target>

python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.json
```

`scope` reports counts by set/language and the manifest's `scope` block without
parsing. For a same-target candidate parent, add
`--reuse .codebase-map/runs/<parent-id>/snapshot/manifest.json` even when full
analysis was selected. Subsequent same-target writes reuse the previous manifest:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.json \
  --reuse <parent-run-dir>/snapshot/manifest.json
```

Write into the owned run. Bind the recorded root, target and run before reuse.
`--reuse` scans/hashes the inventory and verifies current bytes even when size and
mtime match, retaining structure only with matching parser identity. A fingerprint,
root or target mismatch rebuilds structure; malformed reuse input fails without
replacing the output.

### 15. Diff and carry an update

```bash
# what changed since a parent run, and which of its claims that affects
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" diff \
  <parent-run-dir> <target> --out <run-dir> --verify [--threshold 0.4] [--flags '{"depth":"full"}']

# copy the parent's phase files, renumber citations, mark the stale claims
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" carry <parent-run-dir> <run-dir>

```

`--verify` hashes every file rather than trusting size/mtime; require it when
checking a bound analysis against current inputs. `--threshold` is the affected-file
ratio above which full analysis is recommended. Diff normalizes line endings;
for every path that reads source, follow the verified diff with current
`snapshot.py write --reuse`, even for `none` or LF/CRLF-only differences. Supported
parent claims do not establish current source bytes. Returning the supported parent
without reading source requires no new full analysis.

The coordinator carries an accepted parent after the initial current snapshot and
before delivery preparation. `carry.json` records source/copied hashes and parent
provenance. A composed caller's bounded classic child sets
`state.json -> parent_phases: [1,2,3,4]` to carry only those canonical files from a
bound partial or team parent. Classic children never carry a team's `08`.

### 16. Prepare, check and publish every mode

```bash
# after initializing state, register or refresh only this run's active entry
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" register $RUN_DIR

# effective mode/flags are in state.json; add applicable invocation controls
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" prepare $RUN_DIR \
  [--phase N] [--stop-after N]

# continue the named interrupted run, preserving its mode and flags
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" prepare $RUN_DIR \
  --resume-from [N] --run-name <exact-id> [--mode classic|team] [--flags '<JSON>']

# the single native-delivery gate for full, lite, updates and partial modes
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" check $RUN_DIR --json

# only the coordinator calls this after native and requested-view gates
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" publish $RUN_DIR

# on cancellation, partial delivery or failure; preserves the latest pointer
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" unregister $RUN_DIR
```

Only the coordinator prepares declarations; workers read them and write results.
`prepare` writes `state.json -> delivery` schema 1: immutable mode/flags, artifact
declarations and invocation controls (`run_phases`, `stop_after`, `resume_from`).
Artifacts are produced, inherited with parent/carry or same-run provenance, or
skipped with a reason. Knowledge requires both Phase 0 files. The helper owns the
mode table; callers never invent expected files.

`--phase N` accepts 1 through 6, selects Phase 0 plus N and refuses 7. Docs-only
selects 0 and 6. Both stay in their run. `--stop-after N` accepts 1 through 6,
conflicts with docs/single-phase modes and leaves later work pending; it is not a
mode flag. Resume requires the exact run name, verifies earlier artifacts/current
source, preserves mode/flags and drops the stop. It starts at N (1 through 7), or
the first incomplete produced phase when omitted. Missing inherited provenance
never silently becomes fresh work.

`check --json` reports `missing`, `empty`, `unexpected`, `invalid_inherited`,
`stale`, `undocumented_added`, `not_yet_produced`, `first_incomplete_phase`,
`complete`, `may_publish` and errors. Exit 0 means this invocation delivered,
including an intentional stop, not that it may publish. Exit 1 reports delivery
gaps; exit 2 reports invalid binding. Skipped and verified inherited artifacts are
never missing produced work. After a stop, later artifacts remain
`not_yet_produced`; their stale markers are pending, not completed.

Only complete publishing modes with no stale marker may publish. Declared team
`08-interconnect-map.md` is required unless skipped by the mode. Comments with
full-depth Phase 6 require classic `comment_health.md` or each team partition's
Comment Quality section in `06-documentation.md`. The entry also verifies requested
human views. `publish` rechecks delivery, replaces all known mirror phase files
plus state with locked rollback protection, updates only its registry entry/latest
pointer and preserves run archives/unrelated root files. Never hand-copy a partial
set over a previous mirror.

## Prerequisites

Python >= 3.10 and stdlib suffice. Optional Tree-sitter improves Java/JavaScript/
TypeScript/Rust parsing:

```bash
# Optional: install for higher-fidelity parsing
pip install -r "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/requirements.txt"
# or
uv pip install -r "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/requirements.txt"
```

Python uses stdlib `ast`; SQL/PL-SQL use regex DDL extraction; CSS/SCSS/LESS use the
stylesheet tokenizer. Tree-sitter does not change them.

`ParseResult.notes` and CLI output report `parser=stdlib-ast`, `parser=tree-sitter`,
`parser=regex-fallback` or `parser=stylesheet`. Installed does not mean working:
an unavailable grammar falls back to regex with `tree-sitter unavailable: <error>`.

Tree-sitter reports each symbol's definition end line; regex supplies starts only,
so snapshots end a symbol where the next begins. Endpoints remain line-granular:
minified/shared-line definitions can require whole-file reading because a line
also holds another definition, class declaration or static field.

Documentation/comment diagnosis proposes changes; it never applies them.
