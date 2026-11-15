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
import posixpath
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from premap import bazel, cmake, meson  # noqa: E402

IMAGE = "buildpack-deps:noble@sha256:890e8b5c0040e1deff5cc7dc7b4414e67069f79e3301afc4ec5bd49d64ef13e5"  # gcc, make,
# python3, git, xz: what the tools and their setup use (`indexers/clang.py` IMAGE)
STATE = "/daodan/state"
IN, T = f"{STATE}/in", f"{STATE}/tools"
PATH = ":".join([f"{T}/bin", f"{T}/node/bin", f"{T}/npm/bin", f"{T}/go/bin", f"{T}/rust/bin", f"{T}/cmake/bin",
                 "/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin"])
ENV = {"PATH": PATH, "HOME": f"{STATE}/home", "GOPATH": f"{STATE}/go", "GOCACHE": f"{STATE}/go-build",
       "GOTELEMETRY": "off", "CARGO_HOME": f"{STATE}/cargo", "UV_CACHE_DIR": f"{STATE}/uv",
       "npm_config_cache": f"{STATE}/npm-cache", "npm_config_update_notifier": "false"}
NODE = ("https://nodejs.org/dist/v24.22.3/node-v24.22.3-linux-x64.tar.gz",
        "061ec3e3062115705b56b51fa9cc330ab50d34b6969387d4e4b1a50c6809acc2", "node.tar.gz")  # `renovate.NODE`
GO = ("https://go.dev/dl/go1.27.3.linux-amd64.tar.gz",
      "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40", "go.tar.gz")  # `engine_tools.GO_ASSETS`
NINJA = (*meson.DOWNLOAD[1], "ninja.whl")
UNPACK = {
    "node": f"tar -xzf {IN}/node.tar.gz -C {T} && mv {T}/node-v24.22.3-linux-x64 {T}/node",
    "go": f"tar -xzf {IN}/go.tar.gz -C {T}",
    "ninja": f"python3 -m zipfile -e {IN}/ninja.whl {T}/ninja-whl"
             f" && cp {T}/ninja-whl/ninja-*.data/scripts/ninja {T}/bin/ && chmod 755 {T}/bin/ninja",
}


def _npm(package: str) -> str:
    return f"npm install -g --prefix {T}/npm --ignore-scripts --no-audit --no-fund --loglevel=error {package}"


ENRY = (f"mkdir -p {STATE}/enry && cp {IN}/enry_facts.go {STATE}/enry/main.go && cd {STATE}/enry"
        " && go mod init daodan-enry && GOFLAGS=-mod=mod go get github.com/go-enry/go-enry/v2@v2.9.6"
        f" && CGO_ENABLED=0 GOFLAGS=-mod=mod go build -o {T}/bin/daodan-enry .")
TOOLS = {  # tool -> files (url, sha256, name), the setup, whether it needs the registries, extra hosts, memory GB
    "go": {"files": [GO], "setup": [UNPACK["go"]]},
    "daodan-enry": {"files": [GO, (None, None, "enry_facts.go")], "setup": [UNPACK["go"], ENRY], "registries": True},
    "cargo": {"files": [("https://static.rust-lang.org/dist/2026-10-15/rustc-1.99.1-x86_64-unknown-linux-gnu.tar.xz",
                         "2ff05ff9c08a90861e7f6e4065b40a8b87463b4576186fd613871c3e37f2091f", "rustc.tar.xz"),
                        ("https://static.rust-lang.org/dist/2026-10-15/cargo-1.99.1-x86_64-unknown-linux-gnu.tar.xz",
                         "53f3521949404d595efb06a55c12c5658d4ed1c75566f33d3d514eaebe70bd8a", "cargo.tar.xz")],
              "setup": [f"for c in rustc cargo; do mkdir -p {T}/x && tar -xJf {IN}/$c.tar.xz -C {T}/x"
                        f" && cp -R {T}/x/$c-*/$c/. {T}/rust/ && rm -rf {T}/x; done"]},
    "uv": {"files": [("https://github.com/astral-sh/uv/releases/download/0.11.28/uv-x86_64-unknown-linux-gnu.tar.gz",
                      "e490a6464492183c5d4534a5527fb4440f7f2bb2f228162ad7e4afe076dc0224", "uv.tar.gz")],
           "setup": [f"tar -xzf {IN}/uv.tar.gz -C {T} && cp {T}/uv-x86_64-unknown-linux-gnu/uv {T}/bin/"]},
    "npm": {"files": [NODE], "setup": [UNPACK["node"]]},
    "tsc": {"files": [NODE], "setup": [UNPACK["node"], _npm("typescript@6.0.3")], "registries": True},
    "renovate": {"files": [NODE], "setup": [UNPACK["node"], _npm("renovate@44.239.1")], "registries": True},
    "cmake": {"files": [(*cmake.DOWNLOAD[0], "cmake.tar.gz"), NINJA],
              "setup": [f"tar -xzf {IN}/cmake.tar.gz -C {T} && mv {T}/cmake-4.4.5-linux-x86_64 {T}/cmake",
                        UNPACK["ninja"]]},
    "meson": {"files": [(*meson.DOWNLOAD[0], "meson.whl"), NINJA],
              "setup": [f"python3 -m zipfile -e {IN}/meson.whl {T}/meson && printf '%s\\n' '#!/bin/sh'"
                        f" 'PYTHONPATH={T}/meson exec python3 -m mesonbuild.mesonmain \"$@\"' > {T}/bin/meson"
                        f" && chmod 755 {T}/bin/meson", UNPACK["ninja"]]},
    "bazel": {"files": [(*bazel.DOWNLOAD[0], "bazel")],
              "setup": [f"cp {IN}/bazel {T}/bin/bazel && chmod 755 {T}/bin/bazel"],
              "hosts": ("bcr.bazel.build", "github.com", "objects.githubusercontent.com",
                        "release-assets.githubusercontent.com", "mirror.bazel.build", "codeload.github.com"),
              "memory": 3},
}


def fetched(url: str | None, sha256: str | None, name: str) -> Path:
    """The file at `url`, downloaded once into the shared directory and checked by sha256; `enry_facts.go` is
    Daodan's own, beside this module."""
    if url is None:
        return Path(__file__).with_name(name)
    import container
    from engine_tools import download, shared_engine_dir
    target = shared_engine_dir("premap") / sha256[:16] / posixpath.basename(url)
    try:
        if not target.is_file():
            download(url, target, sha256=sha256)
    except (OSError, ValueError) as error:
        raise container.Gap(f"{url} could not be downloaded and verified: {error}", "check the network") from error
    return target


def setup(tool: str, commands: list[dict]) -> dict:
    spec = TOOLS[tool]
    network = "registries" if spec.get("registries") or any(c.get("network") == "registries" for c in commands) \
        else "none"
    lines = [f"mkdir -p {T}/bin {ENV['HOME']}", *spec["setup"]]
    return {"tool": tool, "argv": ["sh", "-c", " && ".join(f"( {line} )" for line in lines)], "cwd": ".",
            "env": ENV, "network": network}


def runner(manifest: Path, engine=None):
    """`runner(commands) -> results` for `premap.derive`: see the module's docstring."""
    import container
    from snapshot_store import open_snapshot
    manifest = Path(manifest).resolve()
    with open_snapshot(manifest) as store:
        project = Path(store["root"])

    def run(commands: list[dict]) -> list[dict]:
        tool = commands[0]["tool"]
        if tool not in TOOLS or any(c["tool"] != tool for c in commands):
            raise ValueError(f"no container setup for the tool {tool}")
        spec = TOOLS[tool]
        first = setup(tool, commands)
        ran = [first, *({**c, "env": {**ENV, **(c.get("env") or {})}} for c in commands)]
        result = container.run_commands(
            project, ran, image=IMAGE, out_dir=manifest.parent / "premap-runs" / tool, engine=engine,
            inputs=lambda: {f"{IN}/{name}": fetched(url, sha, name) for url, sha, name in spec["files"]},
            registries=container.REGISTRIES + tuple(spec.get("hosts", ())),
            memory=int(spec.get("memory", 2) * 2**30), timeout=1800)
        if result["state"] == "gap":
            raise container.Gap(result["cause"], result["remedy"])
        answers = result.get("results") or []
        if result["state"] != "done":
            raise RuntimeError(f"the {tool} container run ended {result['state']}: {result.get('cause')}")
        if not answers or answers[0]["returncode"] != 0:
            raise RuntimeError(f"the {tool} setup failed: "
                               f"{(answers[0]['stderr'] if answers else '').strip()[-400:] or 'no answer'}")
        return [{**answer, "root": result["root"]} for answer in answers[1:]]

    return run
