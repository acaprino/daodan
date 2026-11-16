# Pre-map

`scripts/premap/` writes `premap.json` (`daodan/premap/v1`) beside the
manifest, in Daodan's store, never in the project: what the project holds and
what each unit's analysis needs, before any indexer. The indexer stage and the
container read it and decide nothing on their own. It holds the project's
structure (units, workspaces and their members, the edges between units,
source roots and configuration, languages, excluded files), the toolchain
versions the project declares and the command it declares for its tests, with
the gaps. It never holds the libraries a
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
the source's gaps. A command that fails where its answer names hosts the
project's build declares (a source's `retry`: the repositories of Gradle's
settings, where a `pluginManagement` plugin comes from) runs once more reaching
them; one that fails again is a `declared_hosts_failed` gap naming them.
Without a runner, or with one that finds no container engine
(`container.Gap`), a model source is `not_run`, with a `model_not_run` gap, and
the next scan with a runner runs it again. A source states only what it read: a command that did not answer leaves
its facts absent, never empty, since an empty value would win the join.
`RANK` is `model`, `reader` or `scanner`.

| Source | Rank | Facts |
|---|---|---|
| `modules.py` | reader | units, workspaces, `depends_on` (`references/modules.md`) |
| `python-build` | reader | `source_roots` of a Python unit where its build configuration declares the package folder: setuptools `package-dir` and `packages.find.where`, hatch's wheel `packages`, poetry `packages[].from`, pdm `package-dir`, uv's `module-root`, `setup.cfg` `package_dir`, a literal `package_dir` in `setup.py`; a backend's default is no fact of the file; `registries`, the origins of the URLs its requirements name (`project.dependencies`, extras, `dependency-groups`, setup.cfg's), of uv's and Poetry's indexes and of their git and URL sources |
| `requirements` | reader | pip's requirements files (`*requirements*.txt` and `.in`, the files of a `requirements/` folder): a folder whose only Python manifest is one is a `python-project` unit without a name (manifest `requirements.in`, else `requirements.txt`), one beside a `pyproject.toml` or below a Python unit adds to that unit; `-r` includes go with the including unit, `-c` constraints with none, `-e` and local paths are `depends_on`, the origins of index and `--find-links` URLs and of the URL a requirement names (`name @ URL`, a VCS URL, `-e URL`) are `registries`; a pip-compile output goes with its `.in`; every file in `config.requirements` |
| `python-tests` | reader | how a Python project says its tests run, as `tests` entries. pytest where the project declares or configures it: a pytest configuration (`pytest.ini`, `.pytest.ini`, `pytest.toml`, `.pytest.toml`, `[tool.pytest]` in `pyproject.toml`, `[pytest]` in `tox.ini`, `[tool:pytest]` in `setup.cfg`) or pytest or a plugin of it (`pytest-*`) among the dependencies a manifest declares (the lists of `pyproject.toml`, a requirements file) gives the folder pytest runs in; a `conftest.py` under no such folder gives the folder pytest is given (`args`), run from the nearest folder above it with a Python manifest, else from the root (the outermost `conftest.py` only). unittest only where a file writes the command: a `python -m unittest ...` line of `tox.ini` or a makefile, with its arguments (`{posargs}` dropped; a line with a variable states nothing), and not in a folder where pytest is declared. Test files alone declare nothing |
| `npm-files` | reader | install scripts of `package.json` and the dependencies `package-lock.json` marks `hasInstallScript` (a `not_executed` gap: Daodan installs with `--ignore-scripts`); `registries`, the origins its install reaches: the URLs `package-lock.json` (`resolved`), `pnpm-lock.yaml` and `yarn.lock` record, the registries `.yarnrc.yml` names, the URLs of `package.json`'s dependencies and npm's shorthands for a hosted git repository (`github:`, `owner/repo`, `gitlab:`, `bitbucket:`, `gist:`) |
| `npm-tests` | reader | how a Node package says its tests run, as `tests` entries: the `test` script of its `package.json` and the runner it names, `jest` (also `react-scripts test`), `vitest`, `mocha`, `node:test` (`node --test`), `bun` (`bun test`), `turbo` (`turbo run test`), read through a script of the package it runs (`npm run x`, `yarn x`, `pnpm x`); a script that names none of them has the runner `npm`; npm's placeholder (`no test specified`) and a package without the script state nothing; a runner the package's other scripts start in a folder (a `cd` before it) where `test` starts none is an entry too, through the script with the fewest arguments after the runner that does not watch (a watch mode from the runner's documentation, Vitest without `run`, Node waiting for a debugger), and where every one watches they are a `tests_not_declared` gap |
| `jvm-files` | reader | the wrapper of a Gradle build or a Maven project (`config.wrapper`: `file`, `distribution_url`, `distribution_sha256`; the build tool's version); the Java release and the Kotlin plugin version a pom writes, with `line`; a Gradle build's Java version is a `toolchain_undeclared` gap (only its scripts state it) |
| `gitmodules` | reader | `.gitmodules`: submodules as excluded folders |
| `project-files` | reader | `Package.swift`'s `swift-tools-version` as `swift`; an MSBuild project's or `Directory.Build.props`' `TargetFramework(s)` as `dotnet-target` (the SDK that builds it is `dotnet`, from `global.json`) and `LangVersion` as `c#`, with `line` |
| `renovate` 44.239.1 | reader | `renovate --platform=local --dry-run=extract`, run in the container as a separate program (AGPL-3.0: no code of it in Daodan), reading files only: the toolchains every manager reports (version files, `engines`, `packageManager`, `go`, `requires-python`, wrappers without their own version, the runtime image of a Dockerfile, compose file or devcontainer with the version its tag holds as Renovate's docker versioning reads it (`22-alpine`: 22), a constraint the file writes); where a workflow of `.github/workflows` names `services:` or has a `run:` step, or `.gitlab-ci.yml` names it, includes files or has a `script:`, each of them read by the YAML library Renovate carries (`yaml`, its command line) as the `services` its jobs declare (GitLab's `extends`, `default:`, `inherit` and variables as its runner expands them), a file it cannot read a `model_failed` gap with the library's message; the steps of a workflow, and the npm test scripts the `tests` entries name with their `pre` scripts, that run `docker compose up`, themselves or in the shell scripts of the checkout they run (three levels), as `compose` (`compose.invocations`: the shell's words), one whose words hold a variable or a substitution, or a script that changes folder, a `compose_not_read` gap; the steps of the job that runs a `tests` entry before its test step as `ci_steps`; it runs on Node 24.22.3 |
| `buildkit` v0.34.2 | model | with no network, BuildKit's own Dockerfile frontend (its parser, `instructions.Parse`, its shell lexer) built into Daodan's helper `premap/dockerfile_stages.go`: per folder's Compose file (`compose.yaml`, `compose.yml`, `docker-compose.yaml`, `docker-compose.yml`, the first), Compose 5.6.1 itself resolves each service's `build` (`config --format json`, run by the helper: context, Dockerfile, arguments; a tracked `.env` variable is read from the values the container keeps beside the copy and never reaches a fact) and the helper reads that Dockerfile with them; any other `Dockerfile` with its folder as the context and no argument; each a `docker_builds` entry, a Dockerfile or Compose file not read `model_failed`, with Compose's error and the variables it found unset |
| `compose` 5.6.1 | model | per `compose` entry, `docker-compose <its options> config --format json <its services>` where it runs, with no network and no engine (Compose's static binary, Apache-2.0): the services that `up` starts, those they depend on included, as Compose finds, merges and interpolates the files (`.env`, the step's variables), each a `services` entry; a tracked `.env` holds in the container each value's name in place of the value (`container.named`), so a value Compose takes from it is `${NAME}` in the entry and `dotenv` names its file; a Compose that does not read them is `model_failed` (a name where Compose wants a number or a duration among the causes), a variable it does not find `model_partial` |
| `go-enry` v2.9.6 | scanner | `daodan-enry .` (`premap/enry_facts.go`, built with go-enry): languages in Linguist's spelling, totals, and the files go-enry calls vendored, generated, documentation or binary as `excluded`, a folder whose files share one reason as `folder/`; dot folders stay outside |
| `go` 1.27.3 | model | per `go.mod`, nested ones too: `go env GOPROXY`, `go work edit`, `go mod edit`, `go list -m`, `go list -e ./...`, with `-mod=readonly`, `GOTOOLCHAIN=local`, `CGO_ENABLED=1`, in workspace mode for a module a `go.work` uses: units, packages, files the default build leaves out, cgo, `replace`, workspaces, Go versions, `registries` (`GOPROXY`); a module of the checkout is an edge only through a `replace` to its folder or a `go.work` listing both |
| `cargo` 1.99.1 | model | `cargo metadata --locked`, else `--no-deps`, with `RUSTUP_TOOLCHAIN` pinned: crates, targets, edition, features, build script, `rust-version` as the toolchain `rust` and a written `edition` as `rust-edition` (the workspace root's when inherited), path dependencies as `depends_on`, `registries` (the lockfile's package sources) |
| `uv` 0.11.28 | model | `uv export --frozen` and `uv tree --frozen`, offline, where a `uv.lock` sits: units, workspace members, the edges between them, `registries` (the origins the lock fetches from: indexes, files, git sources, archives) |
| `tsc` 6.0.3 | model | `tsc --showConfig -p` per tsconfig: each unit's `config.tsconfig` (its folder's `tsconfig.json`, its references in order, the others) and `config.paths`, the aliases resolved against `baseUrl` or the tsconfig's folder; a tsconfig no unit holds is a `config_outside_units` gap |
| `npm` | model | `npm query ":root, .workspace"`, from the lockfile, else from the manifests: units, from the lockfile only, the workspace with its members and the edges between units (without it npm links none: a `model_partial` gap), each node placed by its `path` since npm answers for the whole workspace from a member's folder; `config.entry_files` from `main`, `module`, `browser`, `bin`, `exports`; labelled with the npm version that answers |
| `cmake` 4.4.5 | model | per top CMakeLists.txt (one no other one's folder holds), a configure with the network closed and a file API `codemodel-v2` query, its reply files printed: a `cmake-target` per target CMake reports, interface libraries included (not `UTILITY` or imported), named by the target, rooted at its folder, its sources' folders, the targets it links as edges, `config.type`, `sources`, `include_dirs`, `build_tags` (compile definitions); `cmake_minimum_required` as a toolchain, and the language standard of each target's compile groups as `c` or `c++`, declared where the target is defined; a CMakeLists.txt no configure reached is a `model_partial` gap |
| `meson` 1.12.1 | model | per top meson.build, `meson setup --wrap-mode nodownload` and `meson introspect --targets --projectinfo` of the build folder, network closed (Ninja 1.13.2 on the path, never run), else `meson introspect meson.build` of the source tree with a `model_partial` gap: a `meson-target` per target, rooted at the folder of the meson.build defining it, its sources, the `-I` folders and `-D` definitions the compiler gets, an edge to a target whose output file another's linker reads |
| `bazel` 9.3.1 | model | where MODULE.bazel, WORKSPACE or WORKSPACE.bazel sits, `bazel query` of every library, binary and test rule of `//...` as streamed JSON protos and `bazel mod graph --output=json`, with the registries and Bazel's hosts open (it fetches the module graph and the rules its BUILD files load): a `bazel-target` per rule, named by its label, rooted at its package, its BUILD file, rule class, sources, `defines` and `local_defines`, its `deps` inside the workspace as edges; the root module as a `bazel-module`; the packages as a `bazel` workspace |
| `make` 4.3 | model | per folder with a GNUmakefile, makefile or Makefile, `make -pnk` (a dry run of the default goal, the image's GNU Make, network closed) and the last database it prints: a `make-target` per explicit, non-phony target whose recipe names it, with a prerequisite, not a standard goal (`all`, `install`, `clean`, `check`, `test`, ...) nor an object file; its project files among the prerequisites, followed through steps, as sources; the targets among them as edges; another dialect or template (`Makefile.msc`, `*.mak`, `Makefile.in`) is a `not_executed` gap |
| `autotools` | reader | the outermost `configure.ac` (or `configure.in`) of a folder, read from disk, as an `autotools-project` unit named as `AC_INIT` names it, its sources the files the `Makefile.am` of its folders list in a `_SOURCES` variable (conditional ones included); the C and C++ analyzer runs `autoreconf`, the configure in a build folder of its own and make under Bear; make's `not_executed` gap leaves out such a build's `Makefile.am` and `Makefile.in` |

## The join

Every entry carries `sources`, the `tool@version` of each source stating it.
Two entries are one fact when their identity fields agree, from the strictest
match to the loosest: units `root`+`kind`+`name`+`manifest`, then
`root`+`kind`+`name`, then `root`+`kind`; workspaces `root`+`tool` (two
build systems in one folder are two workspaces); toolchains `tool`+`declared_in`+`version`, then `tool`+`declared_in`;
languages `language`; excluded `path`; tests `root`+`runner`. Unit names compare after PEP 503
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
| `units` | `{name, kind, root, manifest, source_roots, depends_on, config, registries, run}`; `kind` one of `npm-package`, `deno-project`, `nx-project`, `python-project`, `cargo-crate`, `go-module`, `maven-module`, `gradle-project`, `sbt-project`, `dotnet-project`, `cmake-target`, `autotools-project`, `composer-package`, `gem`, `bundler-project`, `pub-package`, `swift-package`, `mix-project`, `cabal-package`, `dune-project`, `zig-package`, `julia-package`, `terraform-module`; `name` null when no file names the unit; `config` what an indexer reads (`tsconfig`, `paths`, `entry_files`, `packages`, `ignored_files`, `build_script`, `wrapper`, `requirements`, ...); `registries` the origins the preparation reaches, when a source states them (a lock, a manifest, a build's model: Maven's and Gradle's repositories, NuGet's feeds), without credentials; two sources' add up |
| `units[].run` | `{executes_project_code, reason}`, below |
| `workspace` | `{tool, root, members}`, members as resolved unit folders; a Gradle build, a Maven reactor or an included build is a workspace with its own `root` |
| `toolchains` | `{tool, version, declared_in, line}`: `declared_in` the file and, after `#`, the field; a toolchain belongs to the nearest unit whose `root` holds `declared_in` |
| `tests` | `{root, runner, declared_in, args}`: the command the project declares for the tests of a folder, `python -m <runner> <args>` run in `root` (`runner` `pytest` or `unittest`), or `npm run` there of the script `declared_in` names, `npm test` for `test` (`runner` `jest`, `vitest`, `mocha`, `node:test`, `bun`, `turbo` or `npm`, from `npm-tests`); the dynamic step runs it and no other, and a project with no entry has a `no_test_command` gap there. A Python entry has `deps` (`{declared_in, requirements, extras, groups}`) where the tests' dependencies are declared apart from what the folder's restore installs: the tox environment that runs the runner, else the dependency group, extra or requirements file that names pytest |
| `services` | read also by `service_registry.py`, which recognizes each image as a technology of the project; `{name, image, declared_in, host, env, ports, options, command, entrypoint, volumes, job_env}`: a service container a GitHub Actions job declares (`declared_in` `<workflow>#jobs.<job>.services.<name>`), its keys as the workflow writes them; `host` is where the job's steps reach it (`localhost` on the runner, its name from a job `container`), `job_env` the variables the workflow and the job give the steps. A service a GitLab job runs with (`declared_in` `.gitlab-ci.yml#<job>.services.<index>`) as GitLab's runner gives it: `host` and `aliases` the names the job reaches it by, `env` the job's variables and its own, `job_env` the job's, `computed` those that reference a variable the file does not define, `entrypoint` and `command` as lists, `wait` `ports` (the runner awaits the ports its image exposes). A service Compose starts for a `compose` entry (`declared_in` `<its declared_in>.services.<name>`, from `compose`): `host` localhost, `env` its `environment`, `ports` as `published:target`, `healthcheck`, `command` and `entrypoint` as Compose gives them, `after` its `depends_on` (each name with its condition), `binds` its bind mounts (relative to the project where they lie inside it), `build` the folder Compose builds its image from, `ignored` the keys it sets that no option applies, `dotenv` the tracked `.env` file of each `${NAME}` it holds, whose value the container that starts it reads (`container.filled`); the dynamic step starts it beside the tests (`dynamic.services`) |
| `docker_builds` | `{dockerfile, context, args, stages, declared_in, target, dockerignore, excluded, dotenv}`: a Dockerfile as BuildKit reads it, with its build context and build arguments (`declared_in` `<compose file>#services.<name>.build` and its `target` where Compose declares the build; `dockerignore` the ignore file BuildKit reads, the Dockerfile's own `<Dockerfile>.dockerignore` before the context's `.dockerignore`, and `excluded` what it leaves out of the context by BuildKit's own matcher, relative to the context, a folder ending in `/`; `dotenv` `{name: file}` for each variable of a tracked `.env` the build reads, an argument keeping `${NAME}`, a context or Dockerfile the tracked path it gives); each stage `{name, base, base_stage, line, platform, commands}` (`base_stage` the earlier stage it starts from), each command `{kind, line, end_line, original, unmatched}` with its words expanded by the Dockerfile's ARG and ENV values (`unmatched` the names neither gives) and its own fields: `cmd`, `shell`, `files` (heredocs), `mounts`, `network`, `security`, `flags` for RUN; `sources`, `dest`, `from`, `chown`, `chmod`, `flags` for COPY and ADD; `env`, `args` (a value or null), `path`, `user`, `shell_form`. An analyzer whose unit only a Dockerfile builds runs its build stage (`docker_build.py`) |
| `compose` | `{declared_in, cwd, argv, env, job_env}`: a command that starts Docker Compose for the tests, in a GitHub Actions step (`declared_in` `<workflow>#jobs.<job>.steps.<index>`), an npm test script (`<package.json>#scripts.<name>`) or a shell script one of them runs (its path): where it runs, its words from the variables it sets on, the variables the workflow writes for the step (`env`, no expression) and the job's (`job_env`) |
| `ci_steps` | `{declared_in, tests, name, cwd, run, env, shell}`, `{declared_in, tests, name, cause}` or `{declared_in, tests, name, test, env, computed}`: a step a GitHub Actions job runs before its test step (`declared_in` `<workflow>#jobs.<job>.steps.<index>`), or the lines a GitLab job runs before its test line, one step in the project's folder with the job's variables (`.gitlab-ci.yml#<job>.<before_script|script>.<index>` of its first line; a `cause` where one starts Docker Compose), the first step that runs the `tests` entry `tests` names (an npm script that starts what the entry's starts, or the entry's runner, in the shell scripts it runs too); its folder, its text, the variables of the workflow, the job and the step, its shell where declared; `cause` for one Daodan does not run (an action other than the checkout and a toolchain's setup, `if:`, an expression of the CI, a shell other than bash and sh, Docker Compose on its services). A test step that runs the entry inside a Compose service's container (`docker compose run` or `exec`) is an entry with its `cause`, naming the service and the command, and so is each step before it: Daodan runs no step of that job. The checkout, a setup action and Compose's `up` and `down` are none; the dynamic step runs the others at the end of the preparation (`dynamic.ci_steps`). The test step itself is an entry with `test` and, when it gives the tests variables, `env`: the workflow's, the job's, the step's and those the commands that run the entry set for their program (FastAPI's `FASTAPI_ENV=development coverage run -m pytest`), `computed` naming those the shell computes; the tests the dynamic step runs get them, but those, an expression of the CI and one two test steps give apart (`ci_step_incomplete`); a test entry the dynamic step runs that no entry names, where the jobs run other tests, is a `tests_not_in_ci` gap |
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
`make-target`, `autotools-project`, `bazel-target`, `bazel-module`, `swift-package`, `mix-project`
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
| `toolchain_undeclared` | a toolchain version no file states as a literal: a Gradle build's Java, a pom property the pom does not define, an Android plugin value Gradle's model gives none of (an add-on's target: no SDK platform is installed) |
| `toolchain_unavailable` | a toolchain the readers state that the container's preparation cannot install at that version (`tool`, `version`): a range, a tool mise has no entry for, a second version of one tool (not of Go's go.mod and go.work lines, minimums: the highest runs), an install that failed; the commands run on what installed |
| `tests_not_declared` | `{path, runner, scripts}`: scripts of a `package.json` that start a test runner in a folder where its `test` script starts none, each in a watch mode or waiting for a debugger: a run that never ends, so the dynamic step runs none of them |
| `restore_failed` | a dependency restore a model command needs failed (`manager`, its error): the configure runs without it |
| `compose_not_read` | `{path}`: a step, a test script or a GitLab job that runs Docker Compose in a way the reader does not read (a variable, a substitution, a folder outside the checkout; in a GitLab job, on the Docker the job starts), or a `make` command whose target reaches Compose, read from the Makefile's text (variables, prerequisites, a recipe's `$(MAKE)`; `path` `<Makefile>#<target>` of the recipe that runs it): the services it starts do not start |
| `include_not_read` | `{path, include}`: a file `.gitlab-ci.yml` includes (`include`, as written), which the reader does not read: the services its jobs declare do not start |
| `submodule_absent` | a submodule `.gitmodules` declares whose folder is missing or empty: its code is not in the project |
| `code_outside_units` | `{path, language, files}`: code of a language that no unit able to index it holds, per outermost folder (a Python folder without a manifest Daodan reads); the unit kinds able to index a language are the ones its analyzer declares (`UNIT_KINDS`) |
| `no_analyzer` | `{language, files}`: a language of `type` `programming` that no analyzer lists (`LANGUAGES` of each module of `indexers.analyzers`): its code is in no graph. Not raised for a language whose every file is a build definition (CMake, Starlark, a makefile or manifest the snapshot records by name: `enry.build_definition`): what it declares is the pre-map's |
| module graph gaps | `manifest_unreadable`, `directory_missing`, `member_missing`, `dependency_unresolved`, ... as `modules.py` states them |
