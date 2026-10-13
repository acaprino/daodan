# Snapshot

**Every run writes a snapshot.** Right after scope confirmation, before Phase 0:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py" write \
  <target> --out $RUN_DIR/snapshot/manifest.json
```

The snapshot records the tree this run is about to read: every file with its size, mtime and content hash, every symbol with its span and a hash of its body, and the git commit as metadata. It is what makes this run a possible parent for the next one. A full run writes it too.

When a same-target candidate parent exists, add
`--reuse .codebase-xray/runs/<parent-id>/snapshot/manifest.json` to this write,
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
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py" scope <target>

python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.json
```

`scope` prints the file count by set and by language, and the `scope` block the manifest will carry. `write` records the tree a run analyzed. Every run writes one, which is what makes it a possible parent.

For a subsequent snapshot of the same target, reuse the previous manifest:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py" write <target> \
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
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py" diff \
  <parent-run-dir> <target> --out <run-dir> --verify [--threshold 0.4] [--flags '{"depth":"full"}']

# copy the parent's phase files, renumber citations, mark the stale claims
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py" carry <parent-run-dir> <run-dir>

# publication gate: no marker left, no undocumented new symbol
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py" check <run-dir>
```

`--verify` hashes every file instead of trusting size and mtime. Use it when
checking whether current inputs still support a bound analysis. `--threshold`
is the affected-file ratio above which a full run is recommended instead.
This check uses normalized line endings. Always follow it with a current
`snapshot.py write --reuse` before source-block reading, even when the result
is `none` or only line-ending bytes differ. Returning the supported parent
analysis without reading source does not require a new full analysis.
