"""The runner of the commands of the steps (the pre-map's model sources, those of framework that `find_entry_points` will
take): each source's commands in one container run, in Daodan's container. The analyzers (`link_calls`) and the observers
(`run_and_observe`) take only `IMAGE` and `TOOLS` from it: their runs go through `container.run_in_container`, which with
`egress.preflight` is the service every step shares.

`runner(manifest)` returns the `runner(commands) -> results` that `premap.derive` and `entry_points.derive` call once per model
source.
It runs the commands with `container.run_commands` over a copy of the project (the same runner the JVM and clang
analyzers use): those whose `network` is `registries` in the preparation, behind the proxy that opens only the
package registries (`container.REGISTRIES`) and the hosts a tool names in `TOOLS` (Bazel's) that the user approved
(`egress`), the others with no network. Before them, one setup command unpacks into `STATE/tools` the files the tool needs (`TOOLS`): each is
downloaded once on the host into Daodan's shared directory and checked by sha256, then carried into the container;
a setup that installs a package from a registry (TypeScript, Renovate) runs in the preparation. A tool
that reads what the project's packages hold (`restores`: tsc, whose tsconfigs extend installed and generated
files; next, whose command is one of them) has them restored by the setup, the project's own way
(`preparation.node_prepare`); a restore or a generation that fails, and a package folder no restore installs, is a
gap on the first answer, and the commands run. The hosts the project declares for its build (the repositories of
Gradle's settings, where a `pluginManagement` plugin comes from) open only once the user approved them (`egress`): a
command that fails reaching one has the `approval_required` gap of the run; the repositories a Gradle build declares
that nobody decided (`gradle.retry`) are requests with a gap on the answer, its result standing. A host of the tool
that nobody decided stops the run before it starts (`egress.preflight`): the source is not run, with that gap. A run
that does not happen (no engine, too little memory) or a setup that fails raises: the source states nothing and
its gap says why. Each run's record lands in `premap-runs/<tool>/` beside the manifest.
"""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPTS = SCRIPT_DIR / "entry_points"  # Daodan's own files a tool carries (no URL: the `.mjs` scripts), beside their sources
BUILD_SCRIPTS = SCRIPT_DIR / "premap"  # the same, beside the pre-map's sources (`dockerfile_stages.go`)

import preparation  # noqa: E402
import node_preparation  # noqa: E402
from entry_points import noir  # noqa: E402
from premap import bazel, cmake, compose, dockerfile, gradle, maven, meson, sbt  # noqa: E402

IMAGE = "buildpack-deps:noble@sha256:890e8b5c0040e1deff5cc7dc7b4414e67069f79e3301afc4ec5bd49d64ef13e5"  # gcc, make,
# python3, git, xz: what the tools and their setup use (`indexers/clang.py` IMAGE)
STATE, IN, T = preparation.STATE, preparation.IN, preparation.T
PATH, ENV = preparation.PATH, preparation.ENV
NODE, GO = preparation.NODE, preparation.GO
NINJA = (*meson.DOWNLOAD[1], "ninja.whl")
UNPACK = {
    "node": preparation.NEEDS["node"]["setup"][0],
    "go": preparation.NEEDS["go"]["setup"][0],
    "ninja": f"python3 -m zipfile -e {IN}/ninja.whl {T}/ninja-whl"
             f" && cp {T}/ninja-whl/ninja-*.data/scripts/ninja {T}/bin/ && chmod 755 {T}/bin/ninja",
}


def _npm(package: str) -> str:
    return f"npm install -g --prefix {T}/npm --ignore-scripts --no-audit --no-fund --loglevel=error {package}"

JDK = (*preparation.TEMURIN, preparation.JDK_IN.rsplit("/", 1)[1])  # carried by the JVM build tools


def _jar(name: str, folder: str, program: str) -> str:
    """Unpack a zip with the JDK's own `jar` (the base has no unzip) and put its program on the path."""
    return (f"cd {T} && jar xf {IN}/{name} && chmod 755 {T}/{folder}/bin/{program}"
            f" && ln -sf {T}/{folder}/bin/{program} {T}/bin/{program}")


DOCKERFILE = (f"mkdir -p {STATE}/dockerfile && cp {IN}/dockerfile_stages.go {STATE}/dockerfile/main.go"
              f" && cd {STATE}/dockerfile && go mod init daodan-dockerfile"
              f" && GOFLAGS=-mod=mod go get github.com/moby/buildkit@{dockerfile.VERSION}"
              f" && CGO_ENABLED=0 GOFLAGS=-mod=mod go build -o {T}/bin/daodan-dockerfile .")
TOOLS = {  # tool -> files (url, sha256, name), the setup, whether it needs the registries, extra hosts, memory GB
    "noir": {"files": [noir.DOWNLOAD], "setup": [f"install -m 755 {IN}/noir {T}/bin/noir"]},
    "go": {"files": [GO], "setup": [UNPACK["go"]], "runs_on": ("go",)},
    # `values`: the true values of the tracked .env files beside the copy (`container.run_commands`), which Daodan's
    # helper alone reads, for Compose: it builds Daodan's own Go and runs BuildKit's parser and Compose's `config`,
    # no code of the project (D-311)
    "daodan-dockerfile": {"files": [GO, (None, None, "dockerfile_stages.go"), (*compose.DOWNLOAD, "docker-compose")],
                          "setup": [UNPACK["go"], DOCKERFILE, f"cp {IN}/docker-compose {T}/bin/docker-compose"
                                                              f" && chmod 755 {T}/bin/docker-compose"],
                          "registries": True, "values": True},
    "cargo": {"files": preparation.NEEDS["rust"]["files"], "setup": preparation.NEEDS["rust"]["setup"],
              "runs_on": ("rust",)},
    # uv reads the lock with no interpreter (`premap.uv`): it runs on no Python of the project
    "uv": {"files": [preparation.UV],
           "setup": [f"tar -xzf {IN}/uv.tar.gz -C {T} && cp {T}/uv-x86_64-unknown-linux-gnu/uv {T}/bin/"]},
    "npm": {"files": [NODE], "setup": [UNPACK["node"]], "runs_on": ("node",)},
    # a tsconfig extends files of the installed packages and files their install generates: `restores`, the
    # family of `preparation.RESTORES` whose packages the setup restores first, their lifecycle scripts after with no network
    "tsc": {"files": [NODE], "setup": [UNPACK["node"], _npm("typescript@6.0.3")], "registries": True,
            "runs_on": ("node",), "restores": "node", "memory": 3},
    # the project's own `next` is in the packages the setup restores: no install of its own, but a preparation, where
    # an analysis' shared restore is taken (`node_preparation.clone`)
    "next": {"files": [NODE], "setup": [UNPACK["node"]], "registries": True, "runs_on": ("node",),
             "restores": "node", "memory": 3},
    # the project's own `react-router` or `remix` command (`@react-router/dev`, `@remix-run/dev`) is in the packages the setup
    # restores: no install of its own, and a preparation, where an analysis' shared restore is taken (`entry_points/react_router.py`)
    "react-router": {"files": [NODE], "setup": [UNPACK["node"]], "registries": True, "runs_on": ("node",),
                     "restores": "node", "memory": 3},
    # the project's own `nuxt` is in the packages the setup restores (its `postinstall`, `nuxt prepare`, ran there too, on the
    # whole project): no install of its own, and a preparation, where an analysis' shared restore is taken; Daodan's script (beside
    # this module) calls `loadNuxt` of the project's `@nuxt/kit`, run as `daodan-nuxt` (`entry_points/nuxt.py`). measured: the peak
    # memory of either command on the two fixtures is 0.4 GB at most (`benchmarks/nuxt-routes/README.md`); `memory` is Next.js's, not
    # measured on a project with many modules
    "nuxt": {"files": [NODE, (None, None, "nuxt_pages.mjs")],
             "setup": [UNPACK["node"], f"cp {IN}/nuxt_pages.mjs {T}/nuxt_pages.mjs"
                                       f" && printf '%s\\n' '#!/bin/sh' 'exec node {T}/nuxt_pages.mjs \"$@\"' > {T}/bin/daodan-nuxt"
                                       f" && chmod 755 {T}/bin/daodan-nuxt"],
             "registries": True, "runs_on": ("node",), "restores": "node", "memory": 3},
    # the project's own `svelte-kit` (`@sveltejs/kit`) is in the packages the setup restores (its `prepare` script, which is usually
    # `svelte-kit sync`, ran there too): no install of its own, and a preparation (`entry_points/sveltekit.py`)
    "sveltekit": {"files": [NODE], "setup": [UNPACK["node"]], "registries": True, "runs_on": ("node",),
                  "restores": "node", "memory": 3},
    # the project's own `@angular/compiler` is in the packages the setup restores: Daodan's script (beside this module)
    # calls its `parseTemplate`, run as `daodan-angular` (`entry_points/angular.py`)
    "angular": {"files": [NODE, (None, None, "angular_templates.mjs")],
                "setup": [UNPACK["node"], f"cp {IN}/angular_templates.mjs {T}/angular_templates.mjs"
                                          f" && printf '%s\\n' '#!/bin/sh' 'exec node {T}/angular_templates.mjs \"$@\"' > {T}/bin/daodan-angular"
                                          f" && chmod 755 {T}/bin/daodan-angular"],
                "registries": True, "runs_on": ("node",), "restores": "node", "memory": 3},
    # the compiler the project's own `astro` depends on is in the packages the setup restores: Daodan's script calls its `parse`,
    # run as `daodan-astro` (`entry_points/astro.py`)
    "astro": {"files": [NODE, (None, None, "astro_templates.mjs")],
              "setup": [UNPACK["node"], f"cp {IN}/astro_templates.mjs {T}/astro_templates.mjs"
                                        f" && printf '%s\\n' '#!/bin/sh' 'exec node {T}/astro_templates.mjs \"$@\"' > {T}/bin/daodan-astro"
                                        f" && chmod 755 {T}/bin/daodan-astro"],
              "registries": True, "runs_on": ("node",), "restores": "node", "memory": 3},
    # Daodan's script (beside this module) loads the application with the project's own Flask, run by the Python of the environment
    # the setup restores for each folder (`_python`, `entry_points/flask_app.py`); measured on Modal, `benchmarks/flask-routes/README.md`, which
    # says why the source is not in `entry_points.SOURCES`
    "flask": {"files": [(None, None, "flask_routes.py")], "setup": [f"cp {IN}/flask_routes.py {T}/flask_routes.py"],
              "registries": True, "restores": "python", "memory": 3},
    "renovate": {"files": [NODE], "setup": [UNPACK["node"], _npm("renovate@44.239.1")], "registries": True},
    "compose": {"files": [(*compose.DOWNLOAD, "docker-compose")],  # Compose's own binary: it reads, no engine runs
                "setup": [f"cp {IN}/docker-compose {T}/bin/docker-compose && chmod 755 {T}/bin/docker-compose"]},
    "cmake": {"files": [(*cmake.DOWNLOAD[0], "cmake.tar.gz"), NINJA],
              "setup": [f"tar -xzf {IN}/cmake.tar.gz -C {T} && mv {T}/cmake-4.4.5-linux-x86_64 {T}/cmake",
                        UNPACK["ninja"]]},
    "meson": {"files": [(*meson.DOWNLOAD[0], "meson.whl"), NINJA],
              "setup": [f"python3 -m zipfile -e {IN}/meson.whl {T}/meson && printf '%s\\n' '#!/bin/sh'"
                        f" 'PYTHONPATH={T}/meson exec python3 -m mesonbuild.mesonmain \"$@\"' > {T}/bin/meson"
                        f" && chmod 755 {T}/bin/meson", UNPACK["ninja"]]},
    "make": {"files": [], "setup": []},  # the image's GNU Make
    # the JVM build tools: on the base with Temurin's JDK (`preparation.UNPACK_JDK`, first), each command with
    # Java's proxy settings
    "maven": {"files": [JDK, (*maven.DOWNLOAD[0], "maven.zip")],
              "setup": [preparation.UNPACK_JDK, _jar("maven.zip", "apache-maven-3.10.0", "mvn")],
              "image": preparation.IMAGE, "java": True},
    "gradle": {"files": [JDK, ("https://services.gradle.org/distributions/gradle-9.9.1-bin.zip",
                               "d8a18a7a841dd5df825d35a685fad6f2d7f12ac0c280e57b67c27b4a520ba228", "gradle.zip")],
               "setup": [preparation.UNPACK_JDK, _jar("gradle.zip", "gradle-9.9.1", "gradle")],
               "image": preparation.IMAGE, "java": True,
               "hosts": preparation.RESTORES["gradle"]["hosts"], "memory": 3, "asks": gradle.asked_jdk},
    "sbt": {"files": [JDK, (*sbt.DOWNLOAD[0], "sbt.tgz")],
            "setup": [preparation.UNPACK_JDK, f"tar -xzf {IN}/sbt.tgz -C {T} && ln -sf {T}/sbt/bin/sbt {T}/bin/sbt"],
            "image": preparation.IMAGE,
            "java": True, "hosts": ("repo.scala-sbt.org", "scala.jfrog.io"), "memory": 3},
    "dotnet": {"files": preparation.NEEDS["dotnet"]["files"], "setup": preparation.NEEDS["dotnet"]["setup"],
               "env": {"DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1",
                       "DOTNET_SYSTEM_GLOBALIZATION_INVARIANT": "1"}, "runs_on": ("dotnet",)},
    "bazel": {"files": [(*bazel.DOWNLOAD[0], "bazel")],
              "setup": [f"cp {IN}/bazel {T}/bin/bazel && chmod 755 {T}/bin/bazel"],
              "hosts": ("bcr.bazel.build", "github.com", "objects.githubusercontent.com",
                        "release-assets.githubusercontent.com", "mirror.bazel.build", "codeload.github.com"),
              "memory": 3},
}


def fetched(url: str | None, sha256: str | None, name: str) -> Path:
    """`preparation.fetched`; a file with no URL is Daodan's own, beside the sources that use it (`SCRIPTS`, `BUILD_SCRIPTS`)."""
    if url is None:
        return next((folder / name for folder in (SCRIPTS, BUILD_SCRIPTS) if (folder / name).is_file()), SCRIPTS / name)
    return preparation.fetched(url, sha256, name)



def plan(tool: str, commands: list[dict], stated: list[dict] = (), restores=(), needs=()) -> tuple:
    """The setup command, the files it unpacks, the hosts beside the registries, the gaps known before it runs and the
    tools that install as root before it (`container.tool_phase`, `T3.A.6b`): the tool's own (`TOOLS`), the project's
    toolchains it runs on (`runs_on`, installed by mise at the version `stated`), what the commands name in `needs`
    (`preparation.NEEDS`), then the lines that restore the project's packages (`restores`). The setup runs as
    `container.NOBODY`; a need that installs into the image (`preparation.IMAGE_NEEDS`) keeps the preparation one, as
    root (tools None)."""
    spec = TOOLS[tool]
    chains = preparation.toolchains([t for t in stated if t.get("tool") in spec.get("runs_on", ())])
    asked = {*needs, *(n for c in commands for n in c.get("needs", ()))}
    needs = preparation.setup(asked)
    network = "registries" if spec.get("registries") or needs["registries"] or chains["lines"] or restores or any(
        c.get("network") == "registries" for c in commands) else "none"
    tools = None if asked & set(preparation.IMAGE_NEEDS) else {"lines": needs["lines"], "caps": needs["caps"]}
    lines = [f"mkdir -p {T}/bin {ENV['HOME']}", *spec["setup"], *chains["lines"],
             *(needs["lines"] if tools is None else ()), *restores]
    first = {"tool": tool, "argv": ["sh", "-c", " && ".join(f"( {line} )" for line in lines)], "cwd": ".",
             "env": ENV, "network": network}
    return (first, [*spec["files"], *chains["files"], *needs["files"]],
            (*spec.get("hosts", ()), *chains["hosts"], *needs["hosts"]), chains["gaps"], tools)


def _node(project: Path, refused=()) -> dict:
    """The restore of the Node packages the copy of the project holds (`preparation.node_prepare`), from the
    manifests and lockfiles the snapshot perimeter walks: the snapshot itself keeps no `yarn.lock`; a folder the
    pre-map `refused` (`preparation.refusals`: a `yarn.lock` entry outside the copy) does not restore."""
    return preparation.node_prepare(preparation.perimeter_files(project),
                                    lambda rel: (project / rel).read_text(encoding="utf-8", errors="replace"), refused)


def _python(project: Path) -> dict:
    """The restore of the Python environments the copy of the project holds, one per folder (`preparation.restores`, the
    family `python`: uv, Poetry or pip by the folder's lockfile), as the Node packages are restored: `{lines, needs, hosts, gaps}`,
    the lines that make each folder's environment under `preparation.VENVS`, the tools they need, the hosts beside the registries."""
    files = preparation.perimeter_files(project)
    # shortcut: no VCS requirement is overridden (`preparation.python_vcs`, `without`) and no host a project declares is added
    # (`preparation.declared`), which ask the user (`egress`): a folder whose install needs them is a `restore_failed` gap; when one is met, take them as the analyzers do
    # a folder whose restore would install a local dependency outside the copy does not restore: a gap
    planned = preparation.python_restores(files, lambda rel: (project / rel).read_text(encoding="utf-8", errors="replace"))
    managers = planned["restores"]
    # measured on Modal (`benchmarks/flask-routes/results/venv-dir.json`): `uv venv "<venvs>/."`, the root folder's environment, fails
    # when `<venvs>` is not there (`uv venv <venvs>/api` makes it): the setup makes `tools/bin` and `home`, not `venvs`
    return {"lines": [f"mkdir -p {preparation.VENVS}", *(preparation.restore(manager, folders) for manager, folders in managers.items())]
            if managers else [],
            "needs": [n for manager in managers for n in preparation.RESTORES[manager].get("needs", ())],
            "hosts": tuple(dict.fromkeys(h for manager in managers for h in preparation.RESTORES[manager]["hosts"])),
            "gaps": planned["gaps"]}


def runner(manifest: Path, engine=None, toolchains: list[dict] = ()):
    """`runner(commands, toolchains) -> results` for `premap.derive`: see the module's docstring. `toolchains`,
    entries of the pre-map's facet, are installed by mise first where the tool runs on them; `toolchains` given
    here is the default when the caller passes none (an analyzer, which holds the pre-map)."""
    import container
    from snapshot_store import open_snapshot
    manifest = Path(manifest).resolve()
    with open_snapshot(manifest) as store:
        project = Path(store["root"])

    default = toolchains

    def run(commands: list[dict], toolchains: list[dict] = (), refused: list[dict] = ()) -> list[dict]:
        toolchains = toolchains or default
        tool = commands[0]["tool"]
        if tool not in TOOLS or any(c["tool"] != tool for c in commands):
            raise ValueError(f"no container setup for the tool {tool}")
        spec = TOOLS[tool]
        # a command may carry files, `{name: text}`: what the container is given at `IN/name` beside the tool's own (a list too
        # long for an argument); the engine is asked to run the command alone
        carried = {name: text for c in commands for name, text in (c.get("inputs") or {}).items()}
        if any("/" in name or name in ("", ".", "..") for name in carried):
            raise ValueError(f"a file a command carries is a name, not a path: {sorted(carried)}")
        commands = [{k: v for k, v in c.items() if k != "inputs"} for c in commands]
        restored = (_node(project, refused) if spec.get("restores") == "node" else _python(project)
                    if spec.get("restores") == "python" else {"lines": [], "hosts": (), "gaps": []})
        restore_lines, shared = (node_preparation.options(restored, toolchains) if spec.get("restores") == "node"
                                 else (restored["lines"], {}))
        first, files, hosts, gaps, tools = plan(tool, commands, toolchains, restore_lines, restored.get("needs", ()))
        gaps += restored["gaps"]  # a package folder no restore installs
        hosts = (*hosts, *restored["hosts"])
        ran = [first, *({**c, "env": {**ENV, **spec.get("env", {}), **(c.get("env") or {})},
                         **({"argv": ["sh", "-c", f'{preparation.UNPACK_JDK}{preparation.JAVA_PROXY}; exec "$@"',
                                     c["tool"], *c["argv"]]}
                            if spec.get("java") else {})} for c in commands)]
        def contained(given: list[dict], allowed: tuple, out: str) -> dict:
            with tempfile.TemporaryDirectory(prefix="daodan-inputs-") as scratch:
                written = {}
                for name, text in carried.items():
                    (Path(scratch) / name).write_bytes(text.encode("utf-8"))
                    written[f"{IN}/{name}"] = Path(scratch) / name
                return container.run_commands(
                    project, given, image=spec.get("image", IMAGE), out_dir=manifest.parent / "premap-runs" / out,
                    values=spec.get("values", False), engine=engine,
                    inputs=lambda: {**{f"{IN}/{name}": fetched(url, sha, name) for url, sha, name in files}, **written},
                    registries=container.REGISTRIES + tuple(dict.fromkeys(allowed)),
                    memory=int(spec.get("memory", 2) * 2**30), timeout=1800, tools=tools, **shared)

        import egress
        waiting, said = egress.preflight(str(project.resolve()), hosts)  # a host of the tool nobody decided: no run
        if waiting:
            raise container.Gap(said[0]["detail"], "answer in the app, then analyze again", said)
        result = contained(ran, hosts, tool)
        if result["state"] == "gap":
            raise container.Gap(result["cause"], result["remedy"], result.get("gaps") or ())
        answers = result.get("results") or []
        if result["state"] != "done":
            raise RuntimeError(f"the {tool} container run ended {result['state']}: {result.get('cause')}")
        if not answers or answers[0]["returncode"] != 0:
            raise RuntimeError(f"the {tool} setup failed: "
                               f"{(answers[0]['stderr'] if answers else '').strip()[-400:] or 'no answer'}")
        # the preparation's gaps ride on the first answer, the tools' and the lifecycle scripts' (`generate`, with no
        # network) on the log of the preparation
        began = Path(result["record"]).parent / "prepare.log" if result.get("record") else None
        said = began.read_text(encoding="utf-8", errors="replace") if began and began.is_file() else ""
        gaps += ((preparation.missing(said) if tools else []) + preparation.missing(answers[0]["stderr"])
                 + preparation.restore_gaps(answers[0]["stderr"])
                 + preparation.generation_gaps(f"{answers[0]['stderr']}\n{said}")
                 + list(result.get("gaps") or ()))  # and what the copy left out (`container.copy_perimeter`)
        if tool == "gradle":  # the repositories its builds declare (`gradle.retry`) that nobody decided: asked, the result stands
            waiting, _ = egress.preflight(str(project.resolve()), tuple(h for a in answers[1:] for h in gradle.retry(a)))
            gaps += egress.approval_gap(waiting, "ran")
        roots = [result["root"]] * len(answers)
        # A command whose build needs a newer JVM than the image's (`asks`) runs once more on the JDK it names:
        # mise installs it in the setup, and the command runs with it as JAVA_HOME.
        asked = [(n, spec["asks"](answers[n]["stderr"] + answers[n]["stdout"], toolchains))
                 for n, answer in enumerate(answers) if n and answer["returncode"] != 0] if spec.get("asks") else []
        asked = [(n, found) for n, found in asked if found]
        if asked:
            (jdk, said), chains = asked[0][1], preparation.toolchains([asked[0][1][0]])
            files.extend(item for item in chains["files"] if item not in files)
            home = (f'for j in {T}/mise/installs/java/*/bin/java; do [ -x "$j" ] && JAVA_HOME="${{j%/bin/java}}"; '
                    "done; export JAVA_HOME; ")
            setup = {**ran[0], "network": "registries", "argv": ["sh", "-c", " && ".join(
                [ran[0]["argv"][2], *(f"( {line} )" for line in chains["lines"])])]}
            again = contained([setup, *({**ran[n], "argv": [*ran[n]["argv"][:2], home + ran[n]["argv"][2],
                                                            *ran[n]["argv"][3:]]} for n, _ in asked)],
                              (*hosts, *chains["hosts"]), f"{tool}-jdk")
            gaps += chains["gaps"] + ([{**said, "path": ran[asked[0][0]]["cwd"]}] if said else [])
            if again["state"] != "done" or len(again.get("results") or []) != len(asked) + 1:
                gaps.append({"kind": "jdk_from_build_error", "detail": f"{tool}: the run again on JDK "
                             f"{jdk['version']}, which the build asks for, did not happen: {again.get('cause')}"})
            else:
                gaps += preparation.missing(again["results"][0]["stderr"])
                for (n, _), answer in zip(asked, again["results"][1:]):
                    answers[n], roots[n] = answer, again["root"]
        return [{**answer, "root": roots[n + 1], **({"gaps": gaps} if n == 0 and gaps else {})}
                for n, answer in enumerate(answers[1:])]

    def by_tool(commands: list[dict], toolchains: list[dict] = (), refused: list[dict] = ()) -> list[dict]:
        import egress
        with egress.asking(commands[0]["tool"] if commands else ""):  # the tool's hosts are asked about together
            return run(commands, toolchains, refused)

    by_tool.uses_default_container = engine is None
    return by_tool
