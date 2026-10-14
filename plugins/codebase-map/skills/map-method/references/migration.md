# Output-root compatibility

Coordinators run preflight before root lookup, writer confinement and dispatch.
Workers only resolve supplied bindings afterward. Resolve the project root
independently of the analysis target. The owning method supplies this helper:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/migrate_root.py" --project <project-root>
```

Inspect its JSON and exit code. `absent`, `current`, `migrated` or `recovered` permit
continuation under `.codebase-map/`. `blocked` stops the dependent operation:
finish or explicitly conclude active legacy runs, or reconcile conflicting roots
without overwriting either. Never fall back to starting a fresh analysis because
the new root was absent before preflight. `--check` inspects without writing.

For a caller-supplied legacy `xray_path` or retained run binding, resolve it after
preflight and propagate the returned `path` to every helper and consumer:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/migrate_root.py" resolve --project <project-root> <bound-analysis-path>
```

Preserve run IDs, lineage, manifests, blobs, reports and historical citations.
The helper moves bytes intact and records the relocation. Translate a historical
analysis-root prefix through this resolver; never rewrite stored evidence or
translate source-file paths. An immutable run binding remains that same run.
The legacy directory contains only relocation metadata afterward. Legacy tools
must use updated compatibility entries and never write a second archive.
Original cache executables are not public APIs; locate helpers through the method.
