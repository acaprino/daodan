# Codebase Map migration

Codebase Map is the canonical name and `codebase-map` is its plugin identity.
New analysis output lives in `.codebase-map/`. The former `codebase-xray`
compatibility plugin is removed from the kernels, catalogs and all five host
exports. Its commands, skills and worker identities are no longer registered.

## Existing installations

Update Daodan through your host's ordinary marketplace or package update path.
Remove the old `codebase-xray` installation or selection and enable `codebase-map`.
Use `/codebase-map:analyze` or `/codebase-map:team-analyze` through the host's
native workflow entry. Pi's repository package and the OpenCode catalog contain
only the canonical plugin. An explicit OpenCode `options.plugins` selection must
name `codebase-map`; the removed name is not an alias.

Removing the old plugin does not remove analysis archives. Current producers and
consumers migrate before their first output-root lookup and resolve the project's
root independently of an analysis subtarget. The old `xray_path` input key and
existing report names and run-state fields remain accepted as data contracts.

## Inspect or migrate a repository

Locate the installed `codebase-map:map-method` skill through the active host's
skill registry. Its `scripts/migrate_root.py` is a stdlib Python helper:

```bash
python <installed-map-method>/scripts/migrate_root.py --project <repository> --check
python <installed-map-method>/scripts/migrate_root.py --project <repository>
python <installed-map-method>/scripts/migrate_root.py resolve --project <repository> .codebase-xray/runs/<run-id>
```

The inspection command does not write. The migration command moves the complete
idle `.codebase-xray/` directory to `.codebase-map/`, preserving every artifact's
bytes, run ID, parent lineage, snapshot manifest and source blob. An explicit
project-bound relocation record accompanies the move. The legacy root contains
only relocation metadata afterward, so the updated resolver can translate retained
analysis-root prefixes. Stored reports, citations, snapshots and source-file
paths are never globally replaced. Callers propagate the resolver's returned
path while retaining the same immutable run ID.

JSON statuses `absent`, `current`, `migrated` and `recovered` permit continuation.
`migration_required` and `recovery_required` describe inspection results.
`blocked` exits nonzero and names the condition that needs resolution.

## Conflicts and recovery

- Active or unfinished legacy runs: finish or explicitly conclude them before
  retrying. Do not remove an active registry entry merely to pass migration.
- Both roots contain analysis data: preserve both and reconcile ownership and
  run IDs explicitly. The helper never merges or overwrites either archive.
- Linked roots, junctions, linked legacy contents or foreign/traversing bound
  paths: migration or resolution refuses them rather than following them.
- Synchronous move/redirect failure: the helper attempts to restore the original
  layout and reports any remaining recovery requirement. An interrupted move
  retains a bound origin record so a later call can complete its redirect.

Stop original legacy writers before migration. Old binaries that ignore the
redirect record do not gain a filesystem alias; use the canonical Codebase Map
entries. Raw executable paths inside an old plugin cache are not a public helper
API. This migration covers `.codebase-xray/`, including its older flat layout;
the historical `.deep-dive/` archive predating marketplace 27 requires a separate
explicit migration and is never silently selected.

Only `.codebase-map/` receives new analysis writes. The Copilot guard's
`xray-guard` implementation ID remains stable, while its output-root invocation
uses the canonical directory. Agent confinement remains prompt-level on all
five hosts; helper path checks apply to the migration helper's operations.
