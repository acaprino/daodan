"""The runner of the pre-map's model commands: each source's commands in one container run, in Daodan's container.

`runner(manifest)` returns the `runner(commands) -> results` that `premap.derive` calls once per model source.
It runs the commands with `container.run_commands` over a copy of the project (the same runner the JVM and clang
analyzers use): those whose `network` is `registries` in the preparation, behind the proxy that opens only the
package registries (`container.REGISTRIES`) and the hosts a tool names in `TOOLS` (Bazel's), the others with no
network. Before them, one setup command unpacks into `STATE/tools` the files the tool needs (`TOOLS`): each is
downloaded once on the host into Daodan's shared directory and checked by sha256, then carried into the container;
a setup that installs a package from a registry (TypeScript, Renovate, go-enry) runs in the preparation. A run
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
from premap import bazel, cmake, maven, meson, sbt  # noqa: E402

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


def _jar(name: str, folder: str, program: str) -> str:
    """Unpack a zip with the JDK's own `jar` (the JDK image has no unzip) and put its program on the path."""
    return (f"cd {T} && jar xf {IN}/{name} && chmod 755 {T}/{folder}/bin/{program}"
            f" && ln -sf {T}/{folder}/bin/{program} {T}/bin/{program}")


ENRY = (f"mkdir -p {STATE}/enry && cp {IN}/enry_facts.go {STATE}/enry/main.go && cd {STATE}/enry"
        " && go mod init daodan-enry && GOFLAGS=-mod=mod go get github.com/go-enry/go-enry/v2@v2.9.6"
        f" && CGO_ENABLED=0 GOFLAGS=-mod=mod go build -o {T}/bin/daodan-enry .")
TOOLS = {  # tool -> files (url, sha256, name), the setup, whether it needs the registries, extra hosts, memory GB
    "go": {"files": [GO], "setup": [UNPACK["go"]], "runs_on": ("go",)},
    "daodan-enry": {"files": [GO, (None, None, "enry_facts.go")], "setup": [UNPACK["go"], ENRY], "registries": True},
    "cargo": {"files": preparation.NEEDS["rust"]["files"], "setup": preparation.NEEDS["rust"]["setup"],
              "runs_on": ("rust",)},
    "uv": {"files": [preparation.UV],
           "setup": [f"tar -xzf {IN}/uv.tar.gz -C {T} && cp {T}/uv-x86_64-unknown-linux-gnu/uv {T}/bin/"],
           "runs_on": ("python",)},
    "npm": {"files": [NODE], "setup": [UNPACK["node"]], "runs_on": ("node",)},
    "tsc": {"files": [NODE], "setup": [UNPACK["node"], _npm("typescript@6.0.3")], "registries": True,
            "runs_on": ("node",)},
    "renovate": {"files": [NODE], "setup": [UNPACK["node"], _npm("renovate@44.239.1")], "registries": True},
    "cmake": {"files": [(*cmake.DOWNLOAD[0], "cmake.tar.gz"), NINJA],
              "setup": [f"tar -xzf {IN}/cmake.tar.gz -C {T} && mv {T}/cmake-4.4.5-linux-x86_64 {T}/cmake",
                        UNPACK["ninja"]]},
    "meson": {"files": [(*meson.DOWNLOAD[0], "meson.whl"), NINJA],
              "setup": [f"python3 -m zipfile -e {IN}/meson.whl {T}/meson && printf '%s\\n' '#!/bin/sh'"
                        f" 'PYTHONPATH={T}/meson exec python3 -m mesonbuild.mesonmain \"$@\"' > {T}/bin/meson"
                        f" && chmod 755 {T}/bin/meson", UNPACK["ninja"]]},
    "make": {"files": [], "setup": []},  # the image's GNU Make
    # the JVM build tools: on the JDK image (`indexers/jvm.py` IMAGE), each command with Java's proxy settings
    "maven": {"files": [(*maven.DOWNLOAD[0], "maven.zip")], "setup": [_jar("maven.zip", "apache-maven-3.10.0", "mvn")],
              "image": maven.IMAGE, "java": True},
    "gradle": {"files": [("https://services.gradle.org/distributions/gradle-9.9.1-bin.zip",
                          "d8a18a7a841dd5df825d35a685fad6f2d7f12ac0c280e57b67c27b4a520ba228", "gradle.zip")],
               "setup": [_jar("gradle.zip", "gradle-9.9.1", "gradle")], "image": maven.IMAGE, "java": True,
               "hosts": preparation.RESTORES["gradle"]["hosts"], "memory": 3},
    "sbt": {"files": [(*sbt.DOWNLOAD[0], "sbt.tgz")],
            "setup": [f"tar -xzf {IN}/sbt.tgz -C {T} && ln -sf {T}/sbt/bin/sbt {T}/bin/sbt"], "image": sbt.IMAGE,
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
    """`preparation.fetched`; `enry_facts.go` (no URL) is Daodan's own, beside this module."""
    return Path(__file__).with_name(name) if url is None else preparation.fetched(url, sha256, name)


def plan(tool: str, commands: list[dict], stated: list[dict] = ()) -> tuple[dict, list, tuple, list]:
    """The setup command, the files it unpacks, the hosts beside the registries and the gaps known before it runs:
    the tool's own (`TOOLS`), the project's toolchains it runs on (`runs_on`, installed by mise at the version
    `stated`), and what the commands name in `needs` (`preparation.NEEDS`)."""
    spec = TOOLS[tool]
    chains = preparation.toolchains([t for t in stated if t.get("tool") in spec.get("runs_on", ())])
    needs = preparation.setup({n for c in commands for n in c.get("needs", ())})
    network = "registries" if spec.get("registries") or needs["registries"] or chains["lines"] or any(
        c.get("network") == "registries" for c in commands) else "none"
    lines = [f"mkdir -p {T}/bin {ENV['HOME']}", *spec["setup"], *chains["lines"], *needs["lines"]]
    first = {"tool": tool, "argv": ["sh", "-c", " && ".join(f"( {line} )" for line in lines)], "cwd": ".",
             "env": ENV, "network": network}
    return (first, [*spec["files"], *chains["files"], *needs["files"]],
            (*spec.get("hosts", ()), *chains["hosts"], *needs["hosts"]), chains["gaps"])


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
        first, files, hosts, gaps = plan(tool, commands, toolchains)
        ran = [first, *({**c, "env": {**ENV, **spec.get("env", {}), **(c.get("env") or {})},
                         **({"argv": ["sh", "-c", f'{preparation.JAVA_PROXY}; exec "$@"', c["tool"], *c["argv"]]}
                            if spec.get("java") else {})} for c in commands)]
        result = container.run_commands(
            project, ran, image=spec.get("image", IMAGE), out_dir=manifest.parent / "premap-runs" / tool, engine=engine,
            inputs=lambda: {f"{IN}/{name}": fetched(url, sha, name) for url, sha, name in files},
            registries=container.REGISTRIES + tuple(dict.fromkeys(hosts)),
            memory=int(spec.get("memory", 2) * 2**30), timeout=1800)
        if result["state"] == "gap":
            raise container.Gap(result["cause"], result["remedy"])
        answers = result.get("results") or []
        if result["state"] != "done":
            raise RuntimeError(f"the {tool} container run ended {result['state']}: {result.get('cause')}")
        if not answers or answers[0]["returncode"] != 0:
            raise RuntimeError(f"the {tool} setup failed: "
                               f"{(answers[0]['stderr'] if answers else '').strip()[-400:] or 'no answer'}")
        gaps += preparation.missing(answers[0]["stderr"])  # the preparation's gaps ride on the first answer
        return [{**answer, "root": result["root"], **({"gaps": gaps} if n == 0 and gaps else {})}
                for n, answer in enumerate(answers[1:])]

    return run
