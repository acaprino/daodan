# Snapshot

**Every run writes a snapshot.** Right after scope confirmation, before Phase 0:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" write \
  <target> --out $RUN_DIR/snapshot/manifest.json
```

The snapshot records the tree this run is about to read: every file with its size, mtime and content hash, every symbol with its span and a hash of its body, and the git commit as metadata. It is what makes this run a possible parent for the next one. A full run writes it too.

When a same-target candidate parent exists, add
`--reuse .codebase-map/runs/<parent-id>/snapshot/manifest.json` to this write,
including when full analysis was selected. Reuse checks current bytes and parser
identity before retaining structure; it still scans and hashes the inventory.
Preserve the parent manifest.
For every path that reads source, perform this current write after the verified
diff even when it reports `none` or only LF/CRLF bytes changed. That result can
support the parent's claims without making its recorded source bytes current.

Immediately after, copy the manifest's own `git` field into `$RUN_DIR/state.json`'s `git` field. This is the only new `state.json` field this step fills: `parent_run`, `base_snapshot_created_at` and `incremental` were already written with their real values when `state.json` was created, in pre-flight step 2 of the `analyze` workflow, because its step 1b change set already existed by then.

## Incremental Update Commands

### 14. Count the scope, then write a structural snapshot

```bash
# what a run would analyze, and what its perimeter leaves out; parses nothing
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" scope <target>

python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.json
```

`scope` prints the file count by set and by language, and the `scope` block the manifest will carry. `write` records the tree a run analyzed. Every run writes one, which is what makes it a possible parent.

For a subsequent snapshot of the same target, reuse the previous manifest:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.json \
  --reuse <parent-run-dir>/snapshot/manifest.json
```

Write the current manifest in the owned run; preserve the parent snapshot.
`--reuse` verifies bytes even when size and mtime match. A fingerprint, root or
target mismatch rebuilds structure safely; malformed reuse input fails without
replacing the output. Bind the recorded root, target and run before reuse.

### 15. Diff, carry and check an update

```bash
# what changed since a parent run, and which of its claims that affects
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" diff \
  <parent-run-dir> <target> --out <run-dir> --verify [--threshold 0.4] [--flags '{"depth":"full"}']

# copy the parent's phase files, renumber citations, mark the stale claims
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" carry <parent-run-dir> <run-dir>

# publication gate: no marker left, no undocumented new symbol
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" check <run-dir>
```

`--verify` hashes every file instead of trusting size and mtime. Use it when
checking whether current inputs still support a bound analysis. `--threshold`
is the affected-file ratio above which a full run is recommended instead.
This check uses normalized line endings. Always follow it with a current
`snapshot.py write --reuse` before source-block reading, even when the result
is `none` or only line-ending bytes differ. Returning the supported parent
analysis without reading source does not require a new full analysis.

## Prerequisites

The scripts require Python >= 3.10 and work **out of the box** with just the stdlib. Tree-sitter is optional and improves accuracy for Java / JavaScript / TypeScript / Rust:

```bash
# Optional: install for higher-fidelity parsing
pip install -r "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/requirements.txt"
# or
uv pip install -r "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/requirements.txt"
```

What changes when tree-sitter is installed:

- **Java**: nested classes, generic type parameters, annotations, multi-line declarations parsed correctly. Without it, the regex fallback still finds top-level classes, methods, imports, and constants.
- **JavaScript / TypeScript**: arrow functions in object/class properties, decorators, template literals, JSX elements parsed correctly. Without it, the regex fallback handles top-level declarations, ES6 `import`/`export`, and CommonJS `require`.
- **Rust**: lifetimes, generic bounds (`where` clauses), impl blocks with trait bounds, attribute macros parsed correctly. Without it, the regex fallback still finds top-level fns, structs/enums/traits/impls/mods, use declarations, and UPPER_CASE constants.
- **Java / JavaScript / TypeScript / Rust**: every symbol carries the parser's reported end line, preserving its definition's line endpoints. A regex fallback gives start lines only, and the snapshot then ends each symbol where the next one begins.

Exact end lines remain line-granular. Minified or shared-line definitions can
require whole-file reading even with exact parser endpoints, because a line can
also hold another definition, class declaration or static field.
- **Python / SQL / PL-SQL / CSS**: no change. Python always uses stdlib `ast`; SQL/PL-SQL always use the regex DDL extractor; CSS, SCSS and LESS always use the stylesheet tokenizer.

The active parser is reported in `ParseResult.notes` and in the CLI output: `parser=stdlib-ast`, `parser=tree-sitter`, `parser=regex-fallback`, or `parser=stylesheet`. Installed is not the same as working: when the pack is installed but hands back no parser (a grammar download that failed, a version mismatch), the regex fallback runs and the notes add `tree-sitter unavailable: <error>`.

### Capabilities

**Mechanical Analysis (Scripts):**
- Extract code structure (classes, functions, imports)
- Map dependencies (internal/external)
- Find symbol usages across the codebase
- Classify files by criticality

**Semantic Analysis:**
- Recognize architectural and design patterns
- Identify red flags and anti-patterns
- Trace data and control flows
- Document contracts and invariants
- Assess quality and maintainability

**Documentation Diagnosis:**
- Inspect documentation drift and broken links (Phase 6)
- Report stale indexes and references
- Analyze comment quality and propose changes; analysis does not apply them

**Use this skill when:**
- Analyzing a codebase you're unfamiliar with
- Generating documentation that explains WHY, not just WHAT
- Identifying architectural patterns and anti-patterns
- Building technical ground truth before a code review
- Onboarding to a new project
