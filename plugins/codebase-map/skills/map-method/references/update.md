# Incremental update

## Incremental Updates

A second Codebase Map of the same target rebuilds from nothing only if nobody asked what changed. The mechanism that asks is `scripts/snapshot.py`, and every part of it runs outside the model.

**The snapshot** (`snapshot/manifest.json`, written by every run) records each file with its size, mtime and content hash, and each symbol with its line span and a hash of its body, plus the git commit as metadata. A class span encloses its methods, so editing a method moves both hashes. Inventory categories, file-level formats and exclusions are defined in `references/phases-1-2.md`, Phase 1.

The manifest is also the single source-reading index. `snapshot.py write --reuse`
may reuse an unchanged file's parsed structure after checking its content hash,
the recorded root/target, helper/runtime fingerprint and effective parser profile.
It still walks the current perimeter and hashes every inventoried file. Missing
legacy fingerprints or a changed identity force parsing again. Reuse saves
repeated parsing; it does not establish that the model read or understood a file.

**The change set** (`changes.json`, written by `snapshot.py diff`) compares that manifest with the current worktree. Its default content check trusts equal size and mtime; `--verify` hashes every file and is required when binding source evidence for reuse. A changed helper/runtime fingerprint or parser profile invalidates cached structure. It classifies files and symbols, resolves the one-hop blast radius from the manifest's import edges, and scans the parent's phase files for every claim citing anything it touched. It recommends `incremental`, `full` (with reasons: too much changed, no parent manifest, an incomplete parent, flags differing from the parent's) or `none`.

Diff hashes normalize line endings to classify analysis changes, including with
`--verify`. A result of `none` can therefore retain the parent's analysis while
the source bytes changed from LF to CRLF. Before passing a manifest to source
readers after a verified diff, always write or obtain a current owned snapshot
with `snapshot.py write --reuse <previous-manifest>`. The reader checks exact
bytes. Keep the parent evidence and its provenance; do not modify its manifest
or infer byte freshness from unchanged normalized claims.

**The carry** (`snapshot.py carry`) copies the parent's phase files, except the final report, which is never carried and is always regenerated. It renumbers every citation whose symbol survived, and marks every affected claim with `<!-- xray:stale reason=... cites=... -->`. The model then reads only the affected files and re-derives only the marked claims.

**The gate** (`snapshot.py check`) checks every mode's declared delivery and the update's stale markers and added symbols. Only a complete publishing mode with no stale marker left may publish. A stop leaves later work pending, never skipped. Inherited claims retain their carry provenance.

Two things this deliberately does not do. It never uses a git range as the source of truth, because the tree a developer wants re-analyzed is usually dirty and sometimes not in a repository at all; git is metadata. And it never widens the blast radius past one hop, because the transitive closure of imports is, on most codebases, the whole tree.

### Incremental depth (an update accepted at the checkpoint)

The phases and their numbering are unchanged. What changes is that most claims are already on disk and only the affected ones are re-derived.

The entry already wrote the current snapshot, carried the accepted parent and
prepared delivery (`references/snapshot.md`). The analyst owns any subsequent
snapshot refresh; it never repeats carry or prepares new mode declarations.

1. **Phase 0 runs in full** when selected, overwriting carried `knowledge/`.
   A resume inherits confirmed earlier knowledge rather than rerunning it.
2. **Selected produced phases 1 to 6 run in order, only where work exists.** For
   each marked claim re-derive it through source blocks from this run's manifest,
   then delete its marker. A `symbol-removed` or `file-removed` marker retires the
   claim: delete both. Write claims for added symbols assigned to this phase
   (`01` and `02` always, `03` to `06` at full depth). **A phase with no marker
   and no added symbol is inherited and not opened at all.** Missing parent
   files are produced obligations; create them when their phase is selected.
3. **Read only affected files** from `changes.json -> affected_files`. A flow or
   contract requiring an extra file logs it under `## Extra reads` in `changes.md`,
   naming the claim that required it. **A flow citing one affected symbol is
   re-derived whole.** Flows cite every step; changed steps can affect later ones.
4. **Regenerate Phase 7** when selected, from the mode's phase files. Never
   carry the parent's final report. A stop bounds only this invocation; leave
   later claims marked until resume completes them, including in inherited files.
5. **Write the completion sections of `changes.md`**: `## Claims confirmed`,
   `## Claims revised` (old and new text, one row each), `## Claims retired`,
   `## Claims added`, `## Extra reads`. Report pending phases on an intentional stop.
6. **Check delivery** using the snapshot unit. Report its gaps and complete
   selected work. Passing an invocation's gate does not itself authorize
   publication; only the entry applies `complete`, `may_publish` and requested
   view gates and publishes the whole mirror.

Single-phase and docs-only requests are fresh partial runs. Resuming preserves
the original mode/flags and parent; a changed mode is a new run.
