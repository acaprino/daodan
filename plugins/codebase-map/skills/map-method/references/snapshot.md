# Snapshot

Progressive analysis and intervention scopes: [scope](scope.md).

After scope confirmation, the coordinator writes the current snapshot before Phase 0.
Classic refresh ownership then transfers to the isolated analyst; team ownership
stays with the coordinator. Other workers report gaps. Preserve parent bytes and
preflight lineage; copy this snapshot's own `git` into state through the resolver.

## Incremental Update Commands

### 14. Count scope and write

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" scope <target>
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.sqlite
```

`scope` counts languages/exclusions without parsing. Storage defaults to SQLite.
Explicit JSON:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" write <target> \
  --format json --out <run-dir>/snapshot/manifest.json
```

Choose one file per run. After writing, set `state.json -> snapshot`:
`{"format":"sqlite","path":"snapshot/manifest.sqlite","storage_version":1}`,
or format `json` with `snapshot/manifest.json`.
Legacy runs without this record are JSON only; never rewrite them.

Use `snapshot.py resolve` for current, existing and parent runs:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" resolve <run-dir>
```

It returns `path`, `format`, `storage_version`, `file_count` and small `metadata`
(including `git`), never the inventory. Retain `path` as `source_manifest`.
Missing, linked, ambiguous or misdeclared files fail; the mirror supplies no binding.

Resolve `parent_manifest` before same-target reuse, including selected full analysis:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" write <target> \
  --format "$snapshot_format" --out "$source_manifest" --reuse "$parent_manifest"
```

New runs default to `snapshot_format=sqlite`.
Parent/child formats may differ. Resume preserves format/path; changing them requires
a new run/extraction. Same-path reuse closes its reader before Windows replacement.

Bind root, target and run. Reuse hashes every inventoried file regardless of
size/mtime and retains structure only for matching bytes/parser identity.
Root/target/fingerprint mismatch rebuilds; malformed input preserves the output.

### 15. Diff and carry

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" diff \
  <parent-run-dir> <target> --out <run-dir> --verify [--threshold 0.4] [--flags '{"depth":"full"}']
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" carry <parent-run-dir> <run-dir>
```

Require `--verify` for freshness: it hashes every file. `--threshold` is the affected
ratio recommending full analysis. Diff normalizes line endings; before reading
source, always obtain a current `write --reuse`, including `none` and LF/CRLF-only
changes. Supported parent claims do not prove current bytes. Returning supported
analysis without source reading needs no new full analysis.

Carry follows the initial current snapshot and precedes preparation. `carry.json`
records source/copied hashes and provenance. A caller-bound classic
`--stop-after 4` child may set `parent_phases: [1,2,3,4]` to carry only those files
from a verified partial/team parent. Classic never carries team `08`.

### 16. Prepare, check and publish

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" register $RUN_DIR
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" prepare $RUN_DIR \
  [--phase N] [--stop-after N]
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" prepare $RUN_DIR \
  --resume-from [N] --run-name <exact-id> [--mode classic|team] [--flags '<JSON>']
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" check $RUN_DIR --json
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" publish $RUN_DIR
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" unregister $RUN_DIR
```

Register after state initialization; unregister on cancellation, partial delivery
or failure. Only the coordinator prepares/publishes; workers read declarations and
write results. `prepare` writes `state.json -> delivery` schema 1: immutable
mode/flags, artifact declarations and `run_phases`/`stop_after`/`resume_from`.
Artifacts are produced, inherited with provenance, or skipped with reasons.
Knowledge requires both Phase 0 files. Never invent the helper's mode table.

`--phase N` accepts 1–6 and selects 0 plus N; 7 is refused. Docs-only selects 0/6.
Neither publishes. `--stop-after N` accepts 1–6, conflicts with docs/single-phase
controls and leaves later work pending; it is not a mode flag.
Resume requires the exact name, verifies earlier artifacts/current source, preserves
mode/flags, drops the stop and starts at N (1–7) or first incomplete phase.
Missing inherited provenance never becomes fresh work silently.

`check --json` reports `missing`, `empty`, `unexpected`, `invalid_inherited`,
`stale`, `undocumented_added`, `not_yet_produced`, `first_incomplete_phase`,
`complete`, `may_publish` and errors. Exit 0 means invocation delivery, including
intentional stops; 1 means gaps; 2 means invalid binding. Skipped/verified inherited
work is never missing produced work. Deferred stale markers remain pending.

Publish requires `complete`/`may_publish`, no stale markers and requested human views.
Team `08-interconnect-map.md` is required unless mode-skipped. Full-depth comments
require classic `comment_health.md` or each team's `06-documentation.md` Comment
Quality section. Publication rechecks delivery, replaces all known mirror phases/state
with locked rollback protection, updates only this registry/latest pointer and
preserves archives/unrelated files. Never hand-copy partial output.

## Prerequisites

Python >= 3.12 and stdlib suffice; below it the entry scripts refuse, because `ast`
parses with the running grammar. Optional Java/JS/TS/Rust/Go Tree-sitter parsers:

```bash
pip install -r "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/requirements.txt"
# alternatively:
uv pip install -r "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/requirements.txt"
```

Python uses stdlib `ast`, SQL/PL-SQL regex DDL, CSS/SCSS/LESS the tokenizer.
Parser notes name the engine or fallback; missing grammars report
`tree-sitter unavailable: <error>`. For optional offline embedding, read
`references/embeddings.md` before invoking `embedding_worker.py`.
Python engine passes write `<run-dir>/snapshot/engine-edges.sqlite` via
`resolve_edges.py <manifest> --compact --report-out <report.json>`, read by `edge_view.py`.

Tree-sitter supplies definition ends; regex ends at the next symbol. Shared
lines can require whole-file reading. Diagnosis never applies changes.
