# Pre-map

`scripts/premap/` writes `premap.json` (`daodan/premap/v1`) beside the
manifest, in Daodan's store, never in the project: what the project holds and
what each unit's analysis needs, before any indexer. The indexer stage and the
container read it and decide nothing on their own. It holds the project's
structure (units, workspaces and their members, the edges between units,
source roots and configuration, languages, excluded files) and the toolchain
versions the project declares, with the gaps. It never holds the libraries a
unit uses: each analyzer's build tool resolves them in the container while it
indexes, and a source that states them fails.
`premap.ensure(manifest, runner=None)` returns it, derived again when the
snapshot or a source version changed, or when a runner is given and the model
commands have not run; `premap.state(manifest, runner=None)` says `fresh`,
`stale`, `missing` or `corrupt`.

## Sources

A source is a thin adapter in `scripts/premap/` (`NAME`, `VERSION`, `RANK`)
that states facts in the shape below; Daodan detects nothing on its own. A
reader reads files and runs nothing (`run(context)`). A model source is a
build system's own command, run in Daodan's container: `commands(context)`
describes it as data, `{tool, argv, cwd, env, network}` (`cwd` relative to the
project's root; `network` `registries` for the preparation, `none` for the
run), the caller's `runner(commands)` executes it and answers
`{returncode, stdout, stderr, root}` per command (`root` the project's absolute
path in the container), and `read(context, commands, results)` reads the
answers. The readers run first: a runner that takes `toolchains` gets the
toolchains they state, and its preparation installs the ones each tool runs on
at that version, so a model command runs on the project's Go or Node, not
Daodan's; what it could not prepare rides on the answers (`gaps`) and becomes
the source's gaps. Without a runner, or with one that finds no container engine
(`container.Gap`), a model source is `not_run`, with a `model_not_run` gap, and
the next scan with a runner runs it again. A source states only what it read: a command that did not answer leaves
its facts absent, never empty, since an empty value would win the join.
`RANK` is `model`, `reader` or `scanner`.

| Source | Rank | Facts |
|---|---|---|
| `modules.py` | reader | units, workspaces, `depends_on` (`references/modules.md`) |
| `python-build` | reader | `source_roots` of a Python unit where its build configuration declares the package folder: setuptools `package-dir` and `packages.find.where`, hatch's wheel `packages`, poetry `packages[].from`, pdm `package-dir`, uv's `module-root`, `setup.cfg` `package_dir`, a literal `package_dir` in `setup.py`; a backend's default is no fact of the file |
| `requirements` | reader | pip's requirements files (`*requirements*.txt` and `.in`, the files of a `requirements/` folder): a folder whose only Python manifest is one is a `python-project` unit without a name (manifest `requirements.in`, else `requirements.txt`), one beside a `pyproject.toml` or below a Python unit adds to that unit; `-r` includes go with the including unit, `-c` constraints with none, `-e` and local paths are `depends_on`, index URLs are `registries`; a pip-compile output goes with its `.in`; every file in `config.requirements` |
| `npm-files` | reader | install scripts of `package.json` and the dependencies `package-lock.json` marks `hasInstallScript` (a `not_executed` gap: Daodan installs with `--ignore-scripts`); `registries`, the origins of the lockfile's `resolved` URLs |
| `jvm-files` | reader | the wrapper of a Gradle build or a Maven project (`config.wrapper`: `file`, `distribution_url`, `distribution_sha256`; the build tool's version); the Java release and the Kotlin plugin version a pom writes, with `line`; a Gradle build's Java version is a `toolchain_undeclared` gap (only its scripts state it) |
| `gitmodules` | reader | `.gitmodules`: submodules as excluded folders |
| `project-files` | reader | `Package.swift`'s `swift-tools-version` as `swift`; an MSBuild project's or `Directory.Build.props`' `TargetFramework(s)` as `dotnet-target` (the SDK that builds it is `dotnet`, from `global.json`) and `LangVersion` as `c#`, with `line` |
| `renovate` 44.239.1 | reader | `renovate --platform=local --dry-run=extract`, run in the container as a separate program (AGPL-3.0: no code of it in Daodan), reading files only: the toolchains every manager reports (version files, `engines`, `packageManager`, `go`, `requires-python`, wrappers without their own version, the runtime image of a Dockerfile, compose file or devcontainer, a constraint the file writes); it runs on Node 24.22.3 |
| `go-enry` v2.9.6 | scanner | `daodan-enry .` (`premap/enry_facts.go`, built with go-enry): languages in Linguist's spelling, totals, and the files go-enry calls vendored, generated, documentation or binary as `excluded`, a folder whose files share one reason as `folder/`; dot folders stay outside |
| `go` 1.27.3 | model | per `go.mod`, nested ones too: `go env GOPROXY`, `go work edit`, `go mod edit`, `go list -m`, `go list -e ./...`, with `-mod=readonly`, `GOTOOLCHAIN=local`, `CGO_ENABLED=1`, in workspace mode for a module a `go.work` uses: units, packages, files the default build leaves out, cgo, `replace`, workspaces, Go versions, `registries` (`GOPROXY`); a module of the checkout is an edge only through a `replace` to its folder or a `go.work` listing both |
| `cargo` 1.99.1 | model | `cargo metadata --locked`, else `--no-deps`, with `RUSTUP_TOOLCHAIN` pinned: crates, targets, edition, features, build script, `rust-version` as the toolchain `rust` and a written `edition` as `rust-edition` (the workspace root's when inherited), path dependencies as `depends_on`, `registries` (the lockfile's package sources) |
| `uv` 0.11.28 | model | `uv export --frozen` and `uv tree --frozen`, offline, where a `uv.lock` sits: units, workspace members, the edges between them, `registries` (the lock's indexes) |
| `tsc` 6.0.3 | model | `tsc --showConfig -p` per tsconfig: each unit's `config.tsconfig` (its folder's `tsconfig.json`, its references in order, the others) and `config.paths`, the aliases resolved against `baseUrl` or the tsconfig's folder; a tsconfig no unit holds is a `config_outside_units` gap |
| `npm` | model | `npm query ":root, .workspace"`, from the lockfile, else from the manifests: units, from the lockfile only, the workspace with its members and the edges between units (without it npm links none: a `model_partial` gap), each node placed by its `path` since npm answers for the whole workspace from a member's folder; `config.entry_files` from `main`, `module`, `browser`, `bin`, `exports`; labelled with the npm version that answers |
| `cmake` 4.4.5 | model | per top CMakeLists.txt (one no other one's folder holds), a configure with the network closed and a file API `codemodel-v2` query, its reply files printed: a `cmake-target` per target CMake reports, interface libraries included (not `UTILITY` or imported), named by the target, rooted at its folder, its sources' folders, the targets it links as edges, `config.type`, `sources`, `include_dirs`, `build_tags` (compile definitions); `cmake_minimum_required` as a toolchain, and the language standard of each target's compile groups as `c` or `c++`, declared where the target is defined; a CMakeLists.txt no configure reached is a `model_partial` gap |
| `meson` 1.12.1 | model | per top meson.build, `meson setup --wrap-mode nodownload` and `meson introspect --targets --projectinfo` of the build folder, network closed (Ninja 1.13.2 on the path, never run), else `meson introspect meson.build` of the source tree with a `model_partial` gap: a `meson-target` per target, rooted at the folder of the meson.build defining it, its sources, the `-I` folders and `-D` definitions the compiler gets, an edge to a target whose output file another's linker reads |
| `bazel` 9.3.1 | model | where MODULE.bazel, WORKSPACE or WORKSPACE.bazel sits, `bazel query` of every library, binary and test rule of `//...` as streamed JSON protos and `bazel mod graph --output=json`, with the registries and Bazel's hosts open (it fetches the module graph and the rules its BUILD files load): a `bazel-target` per rule, named by its label, rooted at its package, its BUILD file, rule class, sources, `defines` and `local_defines`, its `deps` inside the workspace as edges; the root module as a `bazel-module`; the packages as a `bazel` workspace |
| `make` 4.3 | model | per folder with a GNUmakefile, makefile or Makefile, `make -pnk` (a dry run of the default goal, the image's GNU Make, network closed) and the last database it prints: a `make-target` per explicit, non-phony target whose recipe names it, with a prerequisite, not a standard goal (`all`, `install`, `clean`, `check`, `test`, ...) nor an object file; its project files among the prerequisites, followed through steps, as sources; the targets among them as edges; another dialect or template (`Makefile.msc`, `*.mak`, `Makefile.in`) is a `not_executed` gap |

## The join

Every entry carries `sources`, the `tool@version` of each source stating it.
Two entries are one fact when their identity fields agree, from the strictest
match to the loosest: units `root`+`kind`+`name`+`manifest`, then
`root`+`kind`+`name`, then `root`+`kind`; workspaces `root`+`tool` (two
build systems in one folder are two workspaces); toolchains `tool`+`declared_in`+`version`, then `tool`+`declared_in`;
languages `language`; excluded `path`. Unit names compare after PEP 503
folding. Two entries of one source never merge.
A model source may state the folders where it answers for every unit of a kind (`covers`): there a unit of that kind
no such source states is dropped as a `superseded` gap. When two sources give a field different values, the value of the higher rank
stays (between equal ranks, the earlier source in `SOURCES`) and the other goes
to the entry's `conflicts` as `{field, value, source, kept_from}`; a field one
source does not give is no conflict. `config` joins key by key
(`config.<key>`).

## Record

| Field | Meaning |
|---|---|
| `binding`, `inputs_digest` | the manifest, its logical digest and root; what freshness compares |
| `sources` | per source `{source, rank, state, seconds}`: `ran`, `not_needed` (nothing of its kind), `not_run` (model commands without a runner, with `commands`), `unavailable` (with `reason`, `install`) or `failed` (with `reason`) |
| `languages` | `{language, files, type}` from go-enry, in Linguist's spelling; `type` is go-enry's (`programming`, `data`, `markup`, `prose`, `unknown`); each file's language stays in the snapshot |
| `excluded` | `{path, why}`: `vendored`, `generated`, `documentation`, `binary`, `submodule` |
| `units` | `{name, kind, root, manifest, source_roots, depends_on, config, registries, run}`; `kind` one of `npm-package`, `deno-project`, `nx-project`, `python-project`, `cargo-crate`, `go-module`, `maven-module`, `gradle-project`, `sbt-project`, `dotnet-project`, `cmake-target`, `composer-package`, `gem`, `bundler-project`, `pub-package`, `swift-package`, `mix-project`, `cabal-package`, `dune-project`, `zig-package`, `julia-package`, `terraform-module`; `name` null when no file names the unit; `config` what an indexer reads (`tsconfig`, `paths`, `entry_files`, `packages`, `ignored_files`, `build_script`, `wrapper`, `requirements`, ...); `registries` the origins the preparation reaches, when a source states them |
| `units[].run` | `{executes_project_code, reason}`, below |
| `workspace` | `{tool, root, members}`, members as resolved unit folders; a Gradle build, a Maven reactor or an included build is a workspace with its own `root` |
| `toolchains` | `{tool, version, declared_in, line}`: `declared_in` the file and, after `#`, the field; a toolchain belongs to the nearest unit whose `root` holds `declared_in` |
| `gaps` | `{kind, source, detail, ...}`, below |

A facet or field no source gives is absent, never empty.

## Views for the indexer stage

`premap.python_runs(record)`: one scip-python run per outermost Python root,
a `python-project` unit or a uv workspace that no other one holds; the units
inside fold into it, since a run reads its whole folder. Each run is
`{root, name, manifests, source_roots}`: `root` relative to the checkout (`''`
for its root), `name` the outer unit's (`None` for a virtual workspace),
`manifests` the files declaring the packages of every folded unit (their
manifests, their `config.requirements`, `uv.lock` with the `pyproject.toml`
beside it where uv read one), `source_roots` the declared ones,
relative to the run's root.

## What the run needs

Every analysis runs in Daodan's container. `run.executes_project_code` is
true for a unit of kind `gradle-project`, `maven-module`, `sbt-project`,
`dotnet-project`, `msbuild-project`, `cmake-target`, `meson-target`,
`make-target`, `bazel-target`, `bazel-module`, `swift-package`, `mix-project`
or `xcode-target`: its model or index exists only when the build runs project
code (`EXECUTES` in `premap/__init__.py`, the reason citing the manifest). It
decides nothing about where the unit runs; it explains the preparation and the
`not_executed` gaps. Where Daodan proceeds without running anything, a
`not_executed` gap says what is skipped: a build script Cargo's metadata names,
`setup.py`, npm install scripts. The benchmark's `needs` facet
(`benchmarks/project-model/`) measures something else, whether a project's
facts are literal in its files: the pre-map gives no `needs`.

## Gaps

| Kind | Meaning |
|---|---|
| `source_unavailable`, `source_failed` | a source that could not run (`remedy`) or failed (`detail`); it states nothing |
| `model_not_run` | a model source whose commands have not run yet: its facts are missing until a runner runs them; without a container engine, `detail` names the engine's cause and `remedy` how to have one |
| `model_failed`, `model_partial` | a model command that failed for a folder or answered without resolution (`detail`: the command and its stderr) |
| `superseded` | a unit a reader states in a folder where a model source answers for every unit of that kind (`covers`, today CMake's configured folders) and that the model does not state: dropped, the gap names it and its sources |
| `not_executed` | a file read and not run: what it computes at run time is unknown |
| `config_outside_units` | a tsconfig no package.json, deno.json or project.json above it puts in a unit |
| `toolchain_undeclared` | a toolchain version no file states as a literal: a Gradle build's Java, a pom property the pom does not define |
| `toolchain_unavailable` | a toolchain the readers state that the container's preparation cannot install at that version (`tool`, `version`): a range, a tool mise has no entry for, a second version of one tool, an install that failed; the commands run on what installed |
| `restore_failed` | a dependency restore a model command needs failed (`manager`, its error): the configure runs without it |
| `submodule_absent` | a submodule `.gitmodules` declares whose folder is missing or empty: its code is not in the project |
| `code_outside_units` | `{path, language, files}`: code of a language that no unit able to index it holds, per outermost folder (a Python folder without a manifest Daodan reads); the unit kinds able to index a language are the ones its analyzer declares (`UNIT_KINDS`) |
| `no_analyzer` | `{language, files}`: a language of `type` `programming` that no analyzer lists (`LANGUAGES` of each module of `indexers.analyzers`): its code is in no graph |
| module graph gaps | `manifest_unreadable`, `directory_missing`, `member_missing`, `dependency_unresolved`, ... as `modules.py` states them |
