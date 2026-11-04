# Modules

`scripts/modules.py` derives the modules of a snapshot and the relations
between them, beside the manifest: `modules.json` (`daodan/module-graph/v1`)
and its `modules.md` view. `snapshot.py write` and `codebase_map_create_run`
build it (`--no-modules` skips it); `modules.py build MANIFEST [--check]`
repairs or reports it. No Markdown is interpreted and no model is called: the
code reads what build systems declare, verifies what the project and a model
say, and stops there.

## Three provenances, one record

| Provenance | Source | Status |
|---|---|---|
| `build` | the manifests below, read programmatically | `confirmed` |
| `declared` | `codebase-modules.json` at the project root (`{"schema": "daodan/declared-modules/v1", "modules": [...]}`) | `confirmed` when every member resolves, else `incomplete` |
| `proposed` | `proposals.json` beside the manifest, written from a model's answer by `modules.py propose MANIFEST FILE` or `codebase_map_modules(proposals=[...])` | `inferred`, never more; `incomplete` when no member resolves |

A declared or proposed record is `{"name", "responsibility", "members", "evidence"}`.
Members are `path::Symbol` (a symbol of the snapshot, exact name), a file or
a directory. Evidence is `path` or `path#heading`. A proposal with the name of
a declared module is superseded (graph gap `proposal_superseded`); the ledger
keeps it. Promotion is a human copying the record into
`codebase-modules.json`.

Build units: `package.json` workspaces and packages, `pnpm-workspace.yaml`,
`lerna.json`, `deno.json`, Nx `project.json`, `pyproject.toml` (project,
poetry, uv workspace and path sources), `setup.cfg`, `setup.py`,
`Cargo.toml` (workspace, path dependencies), `go.mod` and `go.work`,
`pom.xml` (modules, dependencies, `group:artifact` alias),
`settings.gradle[.kts]` and `build.gradle[.kts]` (`include`, `project(":x")`),
`.sln` and `.csproj/.fsproj/.vbproj` (ProjectReference, AssemblyName),
`composer.json` (path repositories), `Gemfile` and `.gemspec`,
`pubspec.yaml` and `melos.yaml`, `Package.swift`, `mix.exs` (umbrella, path
deps), `CMakeLists.txt` (`add_subdirectory`), `.cabal` and `stack.yaml`,
`build.sbt` (`project in file`, `dependsOn`), `.tf` (local `module` sources),
`build.zig.zon`, Julia `Project.toml`, `dune-project`, Daodan `plugin.toml`
(`schema = "daodan/v1"`). Manifests in one
directory merge into one unit; the first name wins, the others become
aliases, the directory name too. A workspace pattern (`*` inside a segment,
`**` across) registers its member directories, with a `workspace-member` unit
where no manifest exists. A nested unit is excluded from its parent's files.
An unreadable manifest or a unit whose directory the snapshot does not hold is
a graph gap.

## Node

| Field | Meaning |
|---|---|
| `id` | the name's slug when unique, otherwise `slug@directory` or `slug@provenance` |
| `name`, `aliases`, `description` | as declared; the description only when a manifest states one |
| `provenance`, `kind`, `ecosystems` | `build`, `declared` or `proposed`; the manifest kind (`npm-workspace`, `cargo-crate`, `maven-aggregator`, `workspace-member`...) or `responsibility` |
| `responsibility` | the declared or proposed text |
| `members` | each with `kind` (`symbol`, `file`, `directory`), `resolved` and, unresolved, the `reason`: absent from the tree, ignored by Git, inside a dot or dependency directory, a file type the map does not inventory, a symbol not in the snapshot of its file |
| `paths`, `excluded`, `files` | the paths to review and every inventoried file the module owns; for a declared or proposed module a directory enters `paths` only when every inventoried file in it is a member |
| `manifests`, `registered_by`, `evidence` | manifests read, workspace roots listing the unit, cited sites `{path, line}` |
| `dependencies`, `external` | declared names, and those matching no unit |
| `conflicts` | `shared_member`: a member two declared or proposed modules claim |
| `gaps` | `member_missing`, `evidence_missing`, `dependency_unresolved` |
| `status`, `coverage`, `members_digest` | `confirmed`, `inferred`, `incomplete`; counts; what `changes` compares |

## Edges

`declares` (manifest dependency resolved to a unit by name, alias or path),
`contains` (workspace registration), `imports` (resolved static import: the
importing file's owner to the imported file's owner, or to the module owning
the exact symbol the statement names), `calls` (resolved call references
between members, from the semantic store). Build units and responsibility
modules are two layers: edges never cross them; a module's `read_scope` lists
the build units holding its files as `owned_by`. Status `confirmed` between
two confirmed modules, else `inferred`. Each edge keeps up to 20 cited sites.
A missing call edge proves no independence: the lexical resolver does not see
calls through attributes.

## Freshness

The graph binds the snapshot's logical digest and the ledger. A new snapshot
or a changed ledger makes it `stale`; `ensure_graph` rebuilds it and reports
`changes`: `added`, `removed`, `changed` (members or member files differ) and
`unchanged`. Nothing stale is kept: proposals are re-verified against the new
snapshot on every build, and a file edited since the snapshot refuses to
serve as evidence (`source changed since the snapshot`).

## Query

`modules.py query MANIFEST NAME`, `query_manifest` and
`codebase_map_modules(query=NAME)` return `daodan/module-query/v1`: `status`
`resolved` (one confirmed module by name or alias, graph fresh),
`needs_clarification` (several matches, a shared member, or only partial and
path matches), `incomplete` (an inferred or incomplete match, or a stale
graph) or `unknown`; `candidates` with `match` (`exact`, `alias`, `path`,
`partial`), the node fields, `relations` and `read_scope` (related modules
with relation, direction, status and paths). The query never promotes a
candidate and never adds a path the graph does not hold.

## The model loop

`modules.py brief MANIFEST [--symbol-limit N]` or
`codebase_map_modules(brief=true)` prints what a model needs: modules so far,
symbols per file in source order (top level and one level down, 2000 names
then whole files omitted with a hint; a 500-file project needs
`--symbol-limit 6000`, about 190 KB), member format and rule. The model
answers with proposals; `propose` validates them (fields, names, members),
records them and rebuilds; the report says what resolved. Group by
responsibility, not by directory: a build unit already covers the directory.
