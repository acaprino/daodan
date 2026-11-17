"""The runner of the pre-map's model commands: each source's commands in one container run, in Daodan's container.

`runner(manifest)` returns the `runner(commands) -> results` that `premap.derive` calls once per model source.
It runs the commands with `container.run_commands` over a copy of the project (the same runner the JVM and clang
analyzers use): those whose `network` is `registries` in the preparation, behind the proxy that opens only the
package registries (`container.REGISTRIES`) and the hosts a tool names in `TOOLS` (Bazel's), the others with no
network. Before them, one setup command unpacks into `STATE/tools` the files the tool needs (`TOOLS`): each is
downloaded once on the host into Daodan's shared directory and checked by sha256, then carried into the container;
a setup that installs a package from a registry (TypeScript, Renovate, go-enry) runs in the preparation. A tool
that reads what the project's packages hold (`restores`: tsc, whose tsconfigs extend installed and generated
files) has them restored by the setup, the project's own way (`preparation.node_prepare`); a restore or a
generation that fails, and a package folder no restore installs, is a gap on the first answer, and the commands
run. A command that fails where its own answer names hosts the project declares for its build (`retry`: the
repositories of Gradle's settings, where a `pluginManagement` plugin comes from) runs once more, reaching them; one
that fails again is a `declared_hosts_failed` gap naming them. A run
that does not happen (no engine, too little memory) or a setup that fails raises: the source states nothing and
its gap says why. Each run's record lands in `premap-runs/<tool>/` beside the manifest.
"""
from __future__ import annotations

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import preparation  # noqa: E402
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


ENRY = (f"mkdir -p {STATE}/enry && cp {IN}/enry_facts.go {STATE}/enry/main.go && cd {STATE}/enry"
        " && go mod init daodan-enry && GOFLAGS=-mod=mod go get github.com/go-enry/go-enry/v2@v2.9.6"
        f" && CGO_ENABLED=0 GOFLAGS=-mod=mod go build -o {T}/bin/daodan-enry .")
DOCKERFILE = (f"mkdir -p {STATE}/dockerfile && cp {IN}/dockerfile_stages.go {STATE}/dockerfile/main.go"
              f" && cd {STATE}/dockerfile && go mod init daodan-dockerfile"
              f" && GOFLAGS=-mod=mod go get github.com/moby/buildkit@{dockerfile.VERSION}"
              f" && CGO_ENABLED=0 GOFLAGS=-mod=mod go build -o {T}/bin/daodan-dockerfile .")
TOOLS = {  # tool -> files (url, sha256, name), the setup, whether it needs the registries, extra hosts, memory GB
    "go": {"files": [GO], "setup": [UNPACK["go"]], "runs_on": ("go",)},
    "daodan-enry": {"files": [GO, (None, None, "enry_facts.go")], "setup": [UNPACK["go"], ENRY], "registries": True},
    "daodan-dockerfile": {"files": [GO, (None, None, "dockerfile_stages.go"), (*compose.DOWNLOAD, "docker-compose")],
                          "setup": [UNPACK["go"], DOCKERFILE, f"cp {IN}/docker-compose {T}/bin/docker-compose"
                                                              f" && chmod 755 {T}/bin/docker-compose"],
                          "registries": True},
    "cargo": {"files": preparation.NEEDS["rust"]["files"], "setup": preparation.NEEDS["rust"]["setup"],
              "runs_on": ("rust",)},
    "uv": {"files": [preparation.UV],
           "setup": [f"tar -xzf {IN}/uv.tar.gz -C {T} && cp {T}/uv-x86_64-unknown-linux-gnu/uv {T}/bin/"],
           "runs_on": ("python",)},
    "npm": {"files": [NODE], "setup": [UNPACK["node"]], "runs_on": ("node",)},
    # a tsconfig extends files of the installed packages and files their install generates: `restores`, the
    # family of `preparation.RESTORES` whose packages the setup restores first, lifecycle scripts included
    "tsc": {"files": [NODE], "setup": [UNPACK["node"], _npm("typescript@6.0.3")], "registries": True,
            "runs_on": ("node",), "restores": "node", "memory": 3},
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
               "hosts": preparation.RESTORES["gradle"]["hosts"], "memory": 3, "retry": gradle.retry,
               "asks": gradle.asked_jdk},
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
    """`preparation.fetched`; `enry_facts.go` and `dockerfile_stages.go` (no URL) are Daodan's own, beside this
    module."""
    return Path(__file__).with_name(name) if url is None else preparation.fetched(url, sha256, name)


def plan(tool: str, commands: list[dict], stated: list[dict] = (), restores=()) -> tuple[dict, list, tuple, list]:
    """The setup command, the files it unpacks, the hosts beside the registries and the gaps known before it runs:
    the tool's own (`TOOLS`), the project's toolchains it runs on (`runs_on`, installed by mise at the version
    `stated`), what the commands name in `needs` (`preparation.NEEDS`), then the lines that restore the project's
    packages (`restores`)."""
    spec = TOOLS[tool]
    chains = preparation.toolchains([t for t in stated if t.get("tool") in spec.get("runs_on", ())])
    needs = preparation.setup({n for c in commands for n in c.get("needs", ())})
    network = "registries" if spec.get("registries") or needs["registries"] or chains["lines"] or restores or any(
        c.get("network") == "registries" for c in commands) else "none"
    lines = [f"mkdir -p {T}/bin {ENV['HOME']}", *spec["setup"], *chains["lines"], *needs["lines"], *restores]
    first = {"tool": tool, "argv": ["sh", "-c", " && ".join(f"( {line} )" for line in lines)], "cwd": ".",
             "env": ENV, "network": network}
    return (first, [*spec["files"], *chains["files"], *needs["files"]],
            (*spec.get("hosts", ()), *chains["hosts"], *needs["hosts"]), chains["gaps"])


def _node(project: Path) -> dict:
    """The restore of the Node packages the copy of the project holds (`preparation.node_prepare`), from the
    manifests and lockfiles the snapshot perimeter walks: the snapshot itself keeps no `yarn.lock`."""
    from tree_scope import Perimeter
    files = sorted((directory / name).relative_to(project).as_posix()
                   for directory, names in Perimeter(project).walk() for name in names)
    return preparation.node_prepare(files, lambda rel: (project / rel).read_text(encoding="utf-8", errors="replace"))


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

    def run(commands: list[dict], toolchains: list[dict] = ()) -> list[dict]:
        toolchains = toolchains or default
        tool = commands[0]["tool"]
        if tool not in TOOLS or any(c["tool"] != tool for c in commands):
            raise ValueError(f"no container setup for the tool {tool}")
        spec = TOOLS[tool]
        restored = _node(project) if spec.get("restores") == "node" else {"lines": [], "hosts": (), "gaps": []}
        first, files, hosts, gaps = plan(tool, commands, toolchains, restored["lines"])
        gaps += restored["gaps"]  # a package folder no restore installs
        hosts = (*hosts, *restored["hosts"])
        ran = [first, *({**c, "env": {**ENV, **spec.get("env", {}), **(c.get("env") or {})},
                         **({"argv": ["sh", "-c", f'{preparation.UNPACK_JDK}{preparation.JAVA_PROXY}; exec "$@"',
                                     c["tool"], *c["argv"]]}
                            if spec.get("java") else {})} for c in commands)]
        def contained(given: list[dict], allowed: tuple, out: str) -> dict:
            return container.run_commands(
                project, given, image=spec.get("image", IMAGE), out_dir=manifest.parent / "premap-runs" / out,
                engine=engine, inputs=lambda: {f"{IN}/{name}": fetched(url, sha, name) for url, sha, name in files},
                registries=container.REGISTRIES + tuple(dict.fromkeys(allowed)),
                memory=int(spec.get("memory", 2) * 2**30), timeout=1800)

        result = contained(ran, hosts, tool)
        if result["state"] == "gap":
            raise container.Gap(result["cause"], result["remedy"])
        answers = result.get("results") or []
        if result["state"] != "done":
            raise RuntimeError(f"the {tool} container run ended {result['state']}: {result.get('cause')}")
        if not answers or answers[0]["returncode"] != 0:
            raise RuntimeError(f"the {tool} setup failed: "
                               f"{(answers[0]['stderr'] if answers else '').strip()[-400:] or 'no answer'}")
        # the preparation's gaps ride on the first answer
        gaps += (preparation.missing(answers[0]["stderr"]) + preparation.restore_gaps(answers[0]["stderr"])
                 + preparation.generation_gaps(answers[0]["stderr"])
                 + list(result.get("gaps") or ()))  # and what the copy left out (`container.copy_perimeter`)
        roots = [result["root"]] * len(answers)
        # A command that failed resolving from hosts its own answer declares (`retry`) runs again reaching them.
        failed = [n for n, answer in enumerate(answers) if n and answer["returncode"] != 0]
        more = sorted({h for n in failed for h in spec["retry"](answers[n])} - {*container.REGISTRIES, *hosts}
                      ) if spec.get("retry") else []
        if more:
            again = contained([ran[0], *(ran[n] for n in failed)], (*hosts, *more), f"{tool}-again")
            said = ", ".join(more)
            if again["state"] != "done" or len(again.get("results") or []) != len(failed) + 1:
                gaps.append({"kind": "declared_hosts_failed", "detail": f"{tool}: the second run, reaching the "
                             f"hosts the build declares ({said}), did not happen: {again.get('cause')}"})
            else:
                for n, answer in zip(failed, again["results"][1:]):
                    answers[n], roots[n] = answer, again["root"]
                    if answer["returncode"] != 0:
                        gaps.append({"kind": "declared_hosts_failed", "path": ran[n]["cwd"], "hosts": more,
                                     "detail": f"{tool} failed again reaching the hosts the build declares ({said}):"
                                               f" {(answer['stderr'] or '').strip()[-300:]}"})
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
                              (*hosts, *more, *chains["hosts"]), f"{tool}-jdk")
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

    return run
