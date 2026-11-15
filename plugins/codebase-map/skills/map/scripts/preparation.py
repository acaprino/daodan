"""What a container run needs before its commands: the tools, the project's toolchains and its dependencies.

A command, of the pre-map or of an analyzer, names what it needs (`needs`: names of `NEEDS`); `setup(names)` gives
the files to carry into the container (each downloaded once into Daodan's shared directory and checked by sha256),
the shell lines that unpack or install them under `T`, whether those lines reach a registry, and the hosts the
preparation may reach beside the package registries. What a line cannot install it names on stderr
(`DAODAN-MISSING tool@version`) and the preparation goes on; `missing` turns those into gaps. The installers
are existing tools: mise for the toolchains a project declares (`toolchains`), each package manager for its own
restore (vcpkg, Conan); Daodan keeps a pin only where none of them has the thing (`NEEDS`: vcpkg's own tool, the
Arm GNU Toolchain). `COMPILERS` names, for a compiler a CMake
toolchain file or a Meson cross file sets, the need that brings it: one it does not name stays the configure's
gap, which names the compiler.
"""
from __future__ import annotations

from pathlib import Path
import posixpath
import re

STATE = "/daodan/state"
IN, T = f"{STATE}/in", f"{STATE}/tools"
GITHUB = ("github.com", "codeload.github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com")
UV = ("https://github.com/astral-sh/uv/releases/download/0.11.28/uv-x86_64-unknown-linux-gnu.tar.gz",
      "e490a6464492183c5d4534a5527fb4440f7f2bb2f228162ad7e4afe076dc0224", "uv.tar.gz")
PATH = ":".join([f"{T}/bin", f"{T}/node/bin", f"{T}/npm/bin", f"{T}/go/bin", f"{T}/rust/bin", f"{T}/cmake/bin",
                 "/opt/java/openjdk/bin",  # the JDK image's java and jar
                 "/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin"])
ENV = {"PATH": PATH, "HOME": f"{STATE}/home", "GOPATH": f"{STATE}/go", "GOCACHE": f"{STATE}/go-build",
       "GOTELEMETRY": "off", "CARGO_HOME": f"{STATE}/cargo", "UV_CACHE_DIR": f"{STATE}/uv",
       "npm_config_cache": f"{STATE}/npm-cache", "npm_config_update_notifier": "false",
       "VCPKG_ROOT": f"{T}/vcpkg", "VCPKG_DISABLE_METRICS": "1", "VCPKG_BINARY_SOURCES": "clear",
       "CONAN_HOME": f"{STATE}/conan-home"}  # what every container command of the preparation and after runs with
NODE = ("https://nodejs.org/dist/v24.22.3/node-v24.22.3-linux-x64.tar.gz",
        "061ec3e3062115705b56b51fa9cc330ab50d34b6969387d4e4b1a50c6809acc2", "node.tar.gz")  # `renovate.NODE`
GO = ("https://go.dev/dl/go1.27.3.linux-amd64.tar.gz",
      "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40", "go.tar.gz")  # `engine_tools.GO_ASSETS`
RUST = [("https://static.rust-lang.org/dist/2026-10-15/rustc-1.99.1-x86_64-unknown-linux-gnu.tar.xz",
         "2ff05ff9c08a90861e7f6e4065b40a8b87463b4576186fd613871c3e37f2091f", "rustc.tar.xz"),
        ("https://static.rust-lang.org/dist/2026-10-15/cargo-1.99.1-x86_64-unknown-linux-gnu.tar.xz",
         "53f3521949404d595efb06a55c12c5658d4ed1c75566f33d3d514eaebe70bd8a", "cargo.tar.xz")]
UNPACK_UV = f"mkdir -p {T}/uvc {T}/bin && tar -xzf {IN}/uv.tar.gz -C {T}/uvc && ln -sf {T}/uvc/*/uv {T}/bin/uv"
NEEDS = {
    "node": {"files": [NODE], "setup": [f"tar -xzf {IN}/node.tar.gz -C {T} && mv {T}/node-v24.22.3-linux-x64 {T}/node"],
             "version": "24.22.3"},
    "go": {"files": [GO], "setup": [f"tar -xzf {IN}/go.tar.gz -C {T}"], "version": "1.27.3"},
    "dotnet": {"files": [("https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.404/dotnet-sdk-10.0.404-linux-x64.tar.gz",
                          "c0610757a818fde4b960d27a0ac421f273068a05dc5ec7abafc01dbf84e9cb4d", "dotnet.tar.gz")],
               "setup": [f"mkdir -p {T}/dotnet && tar -xzf {IN}/dotnet.tar.gz -C {T}/dotnet"
                         f" && ln -sf {T}/dotnet/dotnet {T}/bin/dotnet"], "version": "10.0.404"},
    "rust": {"files": RUST, "setup": [f"for c in rustc cargo; do mkdir -p {T}/x && tar -xJf {IN}/$c.tar.xz -C {T}/x"
                                      f" && cp -R {T}/x/$c-*/$c/. {T}/rust/ && rm -rf {T}/x; done"],
             "version": "1.99.1"},
    "vcpkg": {  # the tool, Microsoft's build; the registry is cloned at its default branch, blobs on demand
        "files": [("https://github.com/microsoft/vcpkg-tool/releases/download/2026-10-29/vcpkg-glibc",
                   "8b10d43c1392a2d51622b1e439cb952289dcf56cbb595eb935847e79fe00d303", "vcpkg")],
        "setup": [f"git clone -q --filter=blob:none https://github.com/microsoft/vcpkg {T}/vcpkg"
                  f" && cp {IN}/vcpkg {T}/vcpkg/vcpkg && chmod 755 {T}/vcpkg/vcpkg && touch {T}/vcpkg/.vcpkg-root"
                  f" && ln -sf {T}/vcpkg/vcpkg {T}/bin/vcpkg"],
        "registries": True, "hosts": GITHUB, "version": "2026-10-29"},  # ports: sources where portfiles say
    "uv": {"files": [UV], "setup": [UNPACK_UV], "version": "0.11.28"},
    "conan": {"files": [UV], "setup": [  # the image's Python has no pip: uv makes the environment
        f"{UNPACK_UV} && uv venv -q --python python3 {T}/conan && uv pip install -q --python {T}/conan conan==2.34.0"
        f" && ln -sf {T}/conan/bin/conan {T}/bin/conan"],
              "registries": True, "hosts": ("center2.conan.io",), "version": "2.34.0"},
    "poetry": {"files": [UV], "setup": [
        f"{UNPACK_UV} && uv venv -q --python python3 {T}/poetry && uv pip install -q --python {T}/poetry"
        f" poetry==2.1.3 && ln -sf {T}/poetry/bin/poetry {T}/bin/poetry"], "registries": True, "version": "2.1.3"},
    "arm-none-eabi": {
        "files": [("https://developer.arm.com/-/media/Files/downloads/gnu/15.2.rel1/binrel/"
                   "arm-gnu-toolchain-15.2.rel1-x86_64-arm-none-eabi.tar.xz",
                   "597893282ac8c6ab1a4073977f2362990184599643b4c5ee34870a8215783a16", "arm-none-eabi.tar.xz")],
        "setup": [f"tar -xJf {IN}/arm-none-eabi.tar.xz -C {T} && ln -sf {T}/arm-gnu-toolchain-*/bin/* {T}/bin/"],
        "version": "15.2.rel1"},
}
COMPILERS = {f"arm-none-eabi-{c}": "arm-none-eabi" for c in ("gcc", "g++", "cc", "c++")}
MISE = ("https://github.com/jdx/mise/releases/download/v2026.11.8/mise-v2026.11.8-linux-x64",
        "32b6abe844efa43d37d7ac4ed21d2ec41e9479d66feb19b0db8d2c548cd6e36d", "mise")
MISE_HOSTS = {  # mise's tool -> the hosts its backend downloads from, beside mise's own version lists
    "node": ("nodejs.org",), "go": ("go.dev", "dl.google.com"), "python": GITHUB, "java": ("api.adoptium.net",
    *GITHUB), "ruby": GITHUB, "rust": ("static.rust-lang.org", "sh.rustup.rs"),
    "dotnet": ("builds.dotnet.microsoft.com", "dotnetcli.azureedge.net"), "swift": ("download.swift.org",),
    "zig": ("ziglang.org",), "bun": GITHUB, "deno": GITHUB, "cmake": GITHUB, "bazel": GITHUB, "uv": GITHUB,
    "maven": GITHUB, "gradle": ("services.gradle.org", *GITHUB)}
MISE_OWN = ("mise-versions.jdx.dev", *GITHUB)
EXACT = re.compile(r"^v?\d+(\.\d+){0,2}([-.+][0-9A-Za-z.]+)?$")  # a version mise installs as written, no range


def setup(names) -> dict:
    """`{files, lines, registries, hosts}` for the needs `names`, in `NEEDS` order."""
    chosen = [NEEDS[name] for name in NEEDS if name in set(names)]
    return {"files": [f for spec in chosen for f in spec["files"]],
            "lines": [f"{{ {line} ; }} >&2 || echo 'DAODAN-MISSING {name}@{NEEDS[name]['version']}' >&2"
                      for name in NEEDS if name in set(names) for line in NEEDS[name]["setup"]],
            "registries": any(spec.get("registries") for spec in chosen),
            "hosts": tuple(dict.fromkeys(h for spec in chosen for h in spec.get("hosts", ())))}


def toolchains(stated: list[dict]) -> dict:
    """`{files, lines, hosts, gaps}` that install with mise the toolchains the pre-map's `toolchains` facet states,
    each at the version it states: never one mise would pick. A tool mise has no entry for here, or a version that
    is a range, is a gap naming both; an install that fails prints `DAODAN-MISSING tool@version` on stderr and the
    run goes on with what installed."""
    wanted, gaps = {}, []
    for item in stated:
        tool, version = item.get("tool"), str(item.get("version") or "")
        why = ("no installer for this tool" if tool not in MISE_HOSTS else
               "a range, not a version to install" if not EXACT.match(version) else
               f"{tool} {wanted[tool]} runs these commands: one version per tool per run"
               if wanted.get(tool, version.lstrip("v")) != version.lstrip("v") else None)
        if why:
            gaps.append({"kind": "toolchain_unavailable", "tool": tool, "version": version,
                         "path": item.get("declared_in"), "detail": f"{tool} {version}: {why}"})
        else:
            wanted[tool] = version.lstrip("v")
    if not wanted:
        return {"files": [], "lines": [], "hosts": (), "gaps": gaps}
    mise = f"MISE_DATA_DIR={T}/mise MISE_YES=1 {IN}/mise"
    lines = [f"chmod 755 {IN}/mise"]
    for tool, version in sorted(wanted.items()):  # each program behind `mise x`, which sets what it needs (rustup's)
        wrap = (f"for d in $({mise} bin-paths {tool}@{version}); do for b in \"$d\"/*; do n=${{b##*/}};"
                f" printf '#!/bin/sh\\nexec env {mise} x {tool}@{version} -- %s \"$@\"\\n' \"$n\" > {T}/bin/$n"
                f" && chmod 755 {T}/bin/$n; done; done")
        lines.append(f"{{ {mise} install {tool}@{version} >&2 && {wrap}; }}"
                     f" || echo 'DAODAN-MISSING {tool}@{version}' >&2")
    hosts = tuple(dict.fromkeys([*MISE_OWN, *(h for tool in sorted(wanted) for h in MISE_HOSTS[tool])]))
    return {"files": [MISE], "lines": lines, "hosts": hosts, "gaps": gaps}


# The JVM ignores HTTPS_PROXY: Java tools get the preparation's proxy as system properties, Maven also in its
# settings (the same lines as `indexers.jvm.PREPARE`).
JAVA_PROXY = (r'if [ -n "${HTTPS_PROXY:-}" ]; then a=${HTTPS_PROXY#*://}; a=${a%%/*}; h=${a%:*}; p=${a##*:};'
              r' export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:-} -Duser.home=$HOME -Dhttps.proxyHost=$h'
              r' -Dhttps.proxyPort=$p -Dhttp.proxyHost=$h -Dhttp.proxyPort=$p"; mkdir -p "$HOME/.m2";'
              r' printf "%s\n" "<settings><proxies>"'
              r' "<proxy><id>https</id><protocol>https</protocol><host>$h</host><port>$p</port></proxy>"'
              r' "<proxy><id>http</id><protocol>http</protocol><host>$h</host><port>$p</port></proxy>"'
              r' "</proxies></settings>" > "$HOME/.m2/settings.xml"; fi')
COREPACK = "export COREPACK_ENABLE_DOWNLOAD_PROMPT=0 NODE_USE_ENV_PROXY=1"  # corepack: the pnpm or Yarn named
PYTHON = ("pyproject.toml", "requirements.txt")
VENVS = f"{STATE}/venvs"  # a Python project's environment, per folder
UV_ENV = "export UV_PYTHON_DOWNLOADS=never UV_NO_PROGRESS=1"
RESTORES = {  # manager -> the files that mark where its build starts, its own restore, what in its output is an
    # error (`error`) or a failure it reports with success (`failed`), the hosts beside the registries
    "gradle": {"marks": ("settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts"),
               "line": "gradle --no-daemon --console=plain -q dependencies",  # every project's configurations
               "failed": " FAILED$", "error": " FAILED$|What went wrong|Could not ", "before": JAVA_PROXY,
               "hosts": ("plugins.gradle.org", "plugins-artifacts.gradle.org", "services.gradle.org",
                         "dl.google.com", "maven.google.com")},
    "maven": {"marks": ("pom.xml",), "error": r"^\[ERROR\]", "before": JAVA_PROXY, "hosts": (),
              "line": "mvn -B -q org.apache.maven.plugins:maven-dependency-plugin:3.8.1:go-offline"},
    # Node: one family, `package.json` marks the folders, the lockfile names the manager (none: npm); scripts off
    "npm": {"marks": ("package.json",), "family": "node", "error": "^npm (error|ERR!)", "hosts": (),
            "line": "if [ -f package-lock.json ] || [ -f npm-shrinkwrap.json ];"
                    " then npm ci --ignore-scripts --no-audit --no-fund;"
                    " else npm install --ignore-scripts --no-audit --no-fund; fi"},
    "pnpm": {"marks": ("package.json",), "family": "node", "locks": ("pnpm-lock.yaml",), "error": "ERR_PNPM|ERROR",
             "before": COREPACK, "hosts": (), "line": "corepack pnpm install --frozen-lockfile --ignore-scripts"},
    "yarn": {"marks": ("package.json",), "family": "node", "locks": ("yarn.lock",), "before": COREPACK,
             "error": "^error|YN0[0-9]+: .*Error", "hosts": (),
             "line": "if [ -f .yarnrc.yml ]; then corepack yarn install --immutable --mode=skip-build;"
                     " else corepack yarn install --frozen-lockfile --ignore-scripts; fi"},
    # Python: one family, the lockfile names the manager (none: pip); the environment lives outside the project, and
    # a Python the project needs comes from the toolchains, never from uv's own downloads
    "uv": {"marks": PYTHON, "family": "python", "locks": ("uv.lock",), "needs": ["uv"], "before": UV_ENV,
           "error": "^error|needs to be updated|No solution", "hosts": (),
           "line": f'UV_PROJECT_ENVIRONMENT="{VENVS}/$f" uv sync --locked --all-packages --no-install-project'},
    "poetry": {"marks": PYTHON, "family": "python", "locks": ("poetry.lock",), "needs": ["poetry"],
               "error": "poetry.lock|Error|error", "hosts": (),
               "line": "poetry install --no-root --no-interaction"},
    "pip": {"marks": PYTHON, "family": "python", "needs": ["uv"], "before": UV_ENV,
            "error": "^error|No solution|not found", "hosts": (),
            "line": f'r=requirements.txt; [ -f $r ] || r=pyproject.toml; uv venv -q --python python3 "{VENVS}/$f"'
                    f' && uv pip install -q --python "{VENVS}/$f" -r "$r"'},
    "go": {"marks": ("go.mod",), "nested": True, "needs": ["go"], "error": "go: |go.mod:|error", "hosts": (),
           "line": "go mod download"},  # each module is its own; the toolchain go.mod names comes from its proxy
    "dotnet": {"marks": (), "suffixes": (".sln", ".slnx", ".csproj", ".fsproj", ".vbproj"), "needs": ["dotnet"],
               "before": "export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1",
               "error": "error", "hosts": (),  # a folder's solution, else its one project
               "line": "dotnet restore $(ls *.slnx *.sln 2>/dev/null | head -n 1)"},
    "cargo": {"marks": ("Cargo.toml",), "needs": ["rust"], "error": "^error|^Caused by|^  ", "hosts": (),
              "line": "if [ -f Cargo.lock ]; then cargo fetch --locked; else cargo fetch; fi"},
}
LOG = "/tmp/daodan-restore.log"


def _folder(rel: str) -> str:
    return posixpath.dirname(rel) or "."


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def restores(files) -> dict[str, list[str]]:
    """Per manager, the folders where its restore runs: each folder with a mark of its family that no other such
    folder holds (a Gradle build, a Maven reactor, a Node workspace restore their projects from their root), every
    marked folder of a manager that is `nested` (each Go module is its own), and each folder with a lockfile of its
    own; within a family, the folder's lockfile names the manager, and the
    manager without `locks` is the default."""
    files = list(files)
    families: dict[str, list[str]] = {}
    for manager, spec in RESTORES.items():
        families.setdefault(spec.get("family", manager), []).append(manager)
    out: dict[str, list[str]] = {}
    for managers in families.values():
        marks = {m for name in managers for m in RESTORES[name]["marks"]}
        suffixes = tuple(x for name in managers for x in RESTORES[name].get("suffixes", ()))
        marked = sorted({_folder(rel) for rel in files if posixpath.basename(rel) in marks
                         or (suffixes and rel.endswith(suffixes))}, key=lambda f: (f.count("/"), f))
        locked = {_folder(rel): name for name in managers for rel in files
                  if posixpath.basename(rel) in RESTORES[name].get("locks", ())}
        default = next(name for name in managers if not RESTORES[name].get("locks"))
        for folder in marked:
            nested = any(RESTORES[name].get("nested") for name in managers)
            if nested or folder in locked or not any(o != folder and _inside(folder, o) for o in marked):
                out.setdefault(locked.get(folder, default), []).append(folder)
    return out


def restore(manager: str, folders: list[str]) -> str:
    """The shell line restoring `manager`'s dependencies in each of `folders`: a folder that fails prints
    `DAODAN-RESTORE-FAILED manager folder`, its error lines, `DAODAN-RESTORE-END` on stderr; the line goes on."""
    spec = RESTORES[manager]
    failed = f" && ! grep -Eq '{spec['failed']}' {LOG}" if spec.get("failed") else ""
    report = (f"{{ printf 'DAODAN-RESTORE-FAILED {manager} %s\\n' \"$f\"; {{ grep -E '{spec['error']}' {LOG}"
              f" || tail -n 30 {LOG}; }} | head -n 30; echo DAODAN-RESTORE-END; }} >&2")
    names = " ".join(f"'{f}'" for f in folders)
    before = f"{spec['before']}; " if spec.get("before") else ""
    return (f"{before}for f in {names}; do ( cd \"$f\" && {spec['line']} ) > {LOG} 2>&1{failed} || {report};"
            " done; true")


RESTORE = re.compile(r"DAODAN-RESTORE-FAILED (\S+) (.+)\n((?:.*\n)*?)DAODAN-RESTORE-END")


def restore_gaps(stderr: str) -> list[dict]:
    """The `restore_failed` gaps a restore line printed: the manager, the folder, the tool's error lines."""
    return [{"kind": "restore_failed", "manager": manager, "path": folder,
             "detail": " | ".join(line.strip() for line in lines.splitlines() if line.strip())[:600]}
            for manager, folder, lines in RESTORE.findall(stderr or "")]


MISSING = re.compile(r"DAODAN-MISSING (\S+)@(\S+)")


def missing(stderr: str) -> list[dict]:
    """The `toolchain_unavailable` gaps a preparation's output names: what it could not install."""
    return [{"kind": "toolchain_unavailable", "tool": tool, "version": version,
             "detail": f"{tool} {version}: the preparation could not install it (its output is in the run's log)"}
            for tool, version in dict.fromkeys(MISSING.findall(stderr or ""))]


def fetched(url: str, sha256: str, name: str) -> Path:
    """The file at `url`, downloaded once into the shared directory and checked by sha256."""
    import container
    from engine_tools import download, shared_engine_dir
    target = shared_engine_dir("preparation") / sha256[:16] / posixpath.basename(url)
    try:
        if not target.is_file():
            download(url, target, sha256=sha256)
    except (OSError, ValueError) as error:
        raise container.Gap(f"{url} could not be downloaded and verified: {error}", "check the network") from error
    return target
