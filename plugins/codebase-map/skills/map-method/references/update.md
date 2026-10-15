# Incremental update

## Incremental Updates

`scripts/snapshot.py` mechanically prepares snapshot, change-set, carry and gate
inputs. `snapshot/manifest.json` records file size/mtime/content hashes, symbol
spans/body hashes and git metadata. A method edit also changes its enclosing
class hash. Phase 1 in `references/phases-1-2.md` owns inventory categories,
file-level formats and exclusions.

`snapshot.py write --reuse` still walks the current perimeter and hashes every
inventoried file. Structural reuse requires matching content, recorded root/target,
helper/runtime fingerprint and effective parser profile; missing legacy identity
or a mismatch reparses. Reuse proves neither model reading nor understanding.

`changes.json`, from `snapshot.py diff`, compares the parent manifest with the
current worktree, classifies files/symbols, resolves the one-hop import blast radius
and finds every affected claim in parent phase files. Default checks trust equal
size/mtime; `--verify` hashes every file and is
required for evidence reuse. Changed helper/runtime fingerprints or parser profiles
invalidate cached structure. Recommendations are `incremental`, `none`, or `full`
with reasons: too much changed, no parent manifest, incomplete parent or changed
flags. The current tree is authoritative, never a Git range; git is metadata.
The blast radius never exceeds one hop.

Diff normalizes line endings even with `--verify`: `none` can support parent claims
despite LF/CRLF byte changes. Before source reading after a verified diff, write or
obtain a current owned manifest with `snapshot.py write --reuse <previous-manifest>`.
Readers check exact bytes. Preserve parent evidence, provenance and manifest;
never infer byte freshness from unchanged normalized claims.

`snapshot.py carry` copies parent phase files except the final report, renumbers
surviving-symbol citations and marks affected claims with
`<!-- xray:stale reason=... cites=... -->`. Unmarked claims remain inherited.
`snapshot.py check` checks every mode's declared delivery, stale markers and added
symbols. Only a complete publishing mode without stale markers may publish.
Stops leave later work pending, never skipped; inherited claims retain carry
provenance.

### Incremental depth (an update accepted at the checkpoint)

The entry already wrote the current snapshot, carried the accepted parent and
prepared delivery (`references/snapshot.md`). The analyst owns subsequent snapshot
refreshes; never repeat carry or prepare mode declarations. Phase numbering stays
unchanged.

1. **Run Phase 0 in full when selected**, overwriting carried `knowledge/`.
   Resume inherits confirmed earlier knowledge instead of rerunning it.
2. **Process selected produced phases 1 to 6 in order, only where work exists.**
   Re-derive each marked claim through this run's manifest/source blocks, then
   delete its marker. `symbol-removed` or `file-removed` retires both claim and
   marker. Write added-symbol claims assigned to this phase (`01` and `02` always; `03` to `06` at full
   depth). Leave unmarked claims unchanged. **A phase without markers or added
   symbols is inherited and never opened.** Missing parent files are produced
   obligations when their phase is selected.
3. **Read only `changes.json -> affected_files`.** Log an extra file required by
   a flow/contract under `## Extra reads` in `changes.md`, naming the claim that
   required it. **Re-derive a whole flow if it cites one affected symbol.** Flows
   cite every step; changed steps can affect later ones.
4. **Regenerate selected Phase 7** from the mode's phase files; never carry the
   parent's final report. A stop bounds this invocation only: later claims stay
   marked until resume, including claims in inherited files.
5. **Write `changes.md` completion sections:** `## Claims confirmed`,
   `## Claims revised` (old/new text, one row each), `## Claims retired`,
   `## Claims added`, `## Extra reads`. Report pending phases on an intentional
   stop.
6. **Check delivery** through the snapshot unit, report gaps and complete selected
   work. An invocation's passing gate does not authorize publication: only the
   entry applies `complete`, `may_publish` and requested-view gates and publishes
   the whole mirror.

Single-phase/docs-only requests are fresh partial runs. Resume preserves the
original mode/flags and parent; a changed mode requires a new run.
