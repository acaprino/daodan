

## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

# Knowledge input preparation

1. Bind the project root, worktree, run and snapshot. Read durable project
   instructions before executing tooling; honor locally forbidden test commands.
2. Inventory existing README, AGENTS.md, CLAUDE.md, nested instruction files,
   docs, ADRs, product requirements, generated references and documentation config.
   Record owners and intended readers; preserve generated-file boundaries.
   For instruction work, use instructions-method's loading preflight to bind
   actual host/version/configuration, applicable scopes and imports. Distinguish
   present, configured and loaded files; preserve unresolved precedence or
   activation claims rather than certifying them from an inventory.
3. Read manifests, entry points and pertinent source. Use the named
   `codebase-map:map-method` to consume an identified analysis when supplied.
   Bind its exact run and revision; retain claim status and premise provenance.
   Resolve the supplied run directory under `.codebase-map/runs/`, verify its
   recorded target, depth and completed state, and compare its snapshot with the
   relevant current inputs. A latest mirror is not a substitute for that binding.
   Stale or incomplete evidence cannot authorize a factual correction.
   Follow the named owner's source-reading commands; do not resolve its helpers
   through this plugin's package root. Use `snapshot.py diff --verify` to check
   analysis changes with normalized line endings. After every such diff, always
   write or obtain a current manifest in the owned run using
   `snapshot.py write --reuse <previous-manifest>` before passing it to source
   readers, including `none` or LF/CRLF-only differences. Supported parent claims
   do not establish current source bytes. Preserve the parent snapshot and its
   evidence lineage, and pass the exact current
   the exact snapshot path from `snapshot.py resolve <bound-run-dir>` to workers. Select symbols from its outline, read
   validated blocks, and expand to callers, callees, invariants, configuration
   and CSS/markup pertinent to each claim. An outline is discovery metadata;
   retained file/class context is not proof that omitted bodies are irrelevant.
   Record files/ranges actually read separately from inventory and runtime evidence.
   A supplied lifecycle receipt or context packet binds by digest: its fresh cards
   and verified source blocks evidence implemented behavior; stale or unread cards
   are leads; its gaps are documented limits.
4. Profile the audience from supplied intent and observable project signals.
   Record inference/confidence rather than inventing rationale. Ask only for an
   unresolved choice that materially changes the deliverable and cannot be derived.
5. Produce the file/audience plan: path, existing owner, readers, purpose,
   keep/update/create/merge candidate, source of facts, input report and writer.
   Prefer extending existing files. Create a new document only when the current
   owners cannot serve the requested purpose. Explicitly request authorization
   only for decisions outside the scope already given.
6. Set a proportional scope and budget before dispatch. Pass unchanged findings
   and metadata to audit methods; never turn a copied inference into a verified
   requirement. Writer and reviewer output paths belong to the owned run unless
   the plan authorizes specific durable documents.
