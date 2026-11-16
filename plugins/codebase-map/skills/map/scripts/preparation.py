"""What a container run needs before its commands: the tools, the project's toolchains and its dependencies.

A command, of the pre-map or of an analyzer, names what it needs (`needs`: names of `NEEDS`); `setup(names)` gives
the files to carry into the container (each downloaded once into Daodan's shared directory and checked by sha256),
the shell lines that unpack or install them under `T`, whether those lines reach a registry, and the hosts the
preparation may reach beside the package registries. What a line cannot install it names on stderr
(`DAODAN-MISSING tool@version`, then why when the line knows) and the preparation goes on; `missing` turns those
into gaps. The installers are existing tools: mise for the toolchains a project declares (`toolchains`), Google's
sdkmanager for the Android SDK packages its build declares (`android`), each package manager for its own
restore (vcpkg, Conan); Daodan keeps a pin only where none of them has the thing (`NEEDS`: vcpkg's own tool,
sdkmanager, the Arm GNU Toolchain). `COMPILERS` names, for a compiler a CMake
toolchain file or a Meson cross file sets, the need that brings it: one it does not name stays the configure's
gap, which names the compiler.
"""
from __future__ import annotations

import json
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
ANDROID_HOME = f"{T}/android"  # the Android SDK: sdkmanager where Google's layout puts it, the packages it installs
SDKMANAGER = f"{ANDROID_HOME}/cmdline-tools/latest/bin/sdkmanager"  # it reads HTTPS_PROXY itself
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
    "git": {"files": [], "setup": [  # the Debian image's own, from its archive over https: VCS requirements need it
        "sed -i 's|http://|https://|' /etc/apt/sources.list.d/debian.sources && export DEBIAN_FRONTEND=noninteractive"
        ' && apt-get -qq -o Acquire::https::Proxy="$HTTPS_PROXY" -o Acquire::Languages=none update && apt-get -qq'
        ' -o Acquire::https::Proxy="$HTTPS_PROXY" install -y --no-install-recommends git'],
        "hosts": ("deb.debian.org",), "version": "debian"},
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
    "cmdline-tools": {  # Google's Android SDK command-line tools, under the Android Software Development Kit License
        # Agreement (developer.android.com/studio/terms), unpacked by the JDK image's `jar`; the SDK's licences
        # are accepted as a CI accepts them, then sdkmanager installs what a build declares (`android`)
        "files": [("https://dl.google.com/android/repository/commandlinetools-linux-15859902_latest.zip",
                   "4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583", "cmdline-tools.zip")],
        "setup": [f"mkdir -p {ANDROID_HOME}/cmdline-tools && (cd {ANDROID_HOME}/cmdline-tools && jar xf"
                  f" {IN}/cmdline-tools.zip && mv cmdline-tools latest && chmod 755 latest/bin/*)"
                  f" && yes | {SDKMANAGER} --licenses > /dev/null"],
        "registries": True, "hosts": ("dl.google.com",), "version": "15859902"},
}
COMPILERS = {f"arm-none-eabi-{c}": "arm-none-eabi" for c in ("gcc", "g++", "cc", "c++")}
MISE = ("https://github.com/jdx/mise/releases/download/v2026.11.8/mise-v2026.11.8-linux-x64",
        "32b6abe844efa43d37d7ac4ed21d2ec41e9479d66feb19b0db8d2c548cd6e36d", "mise")
MISE_HOSTS = {  # mise's tool -> the hosts its backend downloads from, beside mise's own version lists
    "node": ("nodejs.org",), "go": ("go.dev", "dl.google.com"), "python": GITHUB, "java": ("api.adoptium.net",
    *GITHUB), "ruby": GITHUB, "rust": ("static.rust-lang.org", "sh.rustup.rs"),
    "dotnet": ("dot.net", "builds.dotnet.microsoft.com", "dotnetcli.azureedge.net"),
    "swift": ("download.swift.org",),
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


# The files whose version their tool's documentation makes a minimum: a go.mod or go.work's go line is the least Go
# its module or workspace needs, its toolchain line (goV) the toolchain it prefers, and the go command runs its own
# toolchain when that is at least as new as both, else the newer one they name (go.dev/doc/toolchain).
MINIMUMS = {"go": ("go.mod", "go.work")}


def _release(version: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.match(r"v?(\d+(?:\.\d+)*)", version).group(1).split("."))


def toolchains(stated: list[dict]) -> dict:
    """`{files, lines, hosts, gaps}` that install with mise the toolchains the pre-map's `toolchains` facet states,
    each at the version it states: never one mise would pick. A tool mise has no entry for here, or a version that
    is a range, is a gap naming both; so is a second version of a tool, but for minimums (`MINIMUMS`): the highest
    of them runs, which builds every module, or the version a file pins when that is newer still. An install that
    fails prints `DAODAN-MISSING tool@version` on stderr and the run goes on with what installed."""
    wanted, least, second, gaps = {}, {}, [], []
    for item in stated:
        tool, version = item.get("tool"), str(item.get("version") or "")
        minimum = posixpath.basename(str(item.get("declared_in") or "").split("#")[0]) in MINIMUMS.get(tool, ())
        if minimum and tool == "go":
            version = version.removeprefix("go")  # a toolchain line names goV
        why = ("no installer for this tool" if tool not in MISE_HOSTS else
               "a range, not a version to install" if not EXACT.match(version) else None)
        if why:
            gaps.append({"kind": "toolchain_unavailable", "tool": tool, "version": version,
                         "path": item.get("declared_in"), "detail": f"{tool} {version}: {why}"})
        elif minimum:
            least[tool] = max(least.get(tool, version), version, key=_release)
        elif wanted.setdefault(tool, version.lstrip("v")) != version.lstrip("v"):
            second.append((item, version))
    for tool, version in least.items():
        if tool not in wanted or _release(wanted[tool]) < _release(version):
            wanted[tool] = version.lstrip("v")
    gaps += [{"kind": "toolchain_unavailable", "tool": item["tool"], "version": version,
              "path": item.get("declared_in"), "detail": f"{item['tool']} {version}: {item['tool']}"
              f" {wanted[item['tool']]} runs these commands: one version per tool per run"} for item, version in second]
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


ANDROID = {"android-sdk": "platforms;android-{}", "android-build-tools": "build-tools;{}"}  # toolchain -> package
SDK_LOG = "/tmp/daodan-sdkmanager.log"


def android(stated: list[dict]) -> dict:
    """`{files, lines, hosts, gaps}` that install the Android SDK packages the pre-map's `toolchains` facet states
    (`ANDROID`: the platform of a `compileSdk`, the build tools an Android plugin runs), each once, with sdkmanager
    (`NEEDS["cmdline-tools"]`, the licences accepted first). A version no package name can hold is a gap; a
    package sdkmanager does not install prints `DAODAN-MISSING tool@version package: its error` on stderr and
    the run goes on."""
    wanted, gaps = [], []
    for item in stated:
        tool, version = item.get("tool"), str(item.get("version") or "")
        if tool not in ANDROID:
            continue
        if not re.fullmatch(r"[\w.-]+", version):
            gaps.append({"kind": "toolchain_unavailable", "tool": tool, "version": version,
                         "path": item.get("declared_in"), "detail": f"{tool} {version}: no SDK package has that name"})
        elif (tool, version) not in wanted:
            wanted.append((tool, version))
    if not wanted:
        return {"files": [], "lines": [], "hosts": (), "gaps": gaps}
    tools = setup(["cmdline-tools"])
    # sdkmanager's own words, on one line: its progress bar redraws with carriage returns
    said = (f"tr '\\r' '\\n' < {SDK_LOG} > {SDK_LOG}.txt; {{ grep -oE '(Error|Warning): .*|[^ ]*Exception.*|.*not"
            f" found.*' {SDK_LOG}.txt || tail -n 3 {SDK_LOG}.txt; }} | uniq | head -n 3 | tr -s '\\n' ' '")
    lines = list(tools["lines"])
    for tool, version in wanted:
        package = ANDROID[tool].format(version)
        lines.append(f"{{ {SDKMANAGER} '{package}' > {SDK_LOG} 2>&1 && [ -d {ANDROID_HOME}/{package.replace(';', '/')}"
                     f" ]; }} || echo \"DAODAN-MISSING {tool}@{version} {package}: $({said})\" >&2")
    return {"files": tools["files"], "lines": lines, "hosts": tools["hosts"], "gaps": gaps}


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
# The corepack a Node ships may predate npm's registry key of January 2025, which corepack carries from 0.31.0, and
# then cannot verify a package manager published since ("Cannot find matching keyid"); from Node 25 none ships.
# Corepack's remedy is a newer one from npm: installed apart and first on the path, from 0.31.0 to the newest known,
# npm takes the newest whose engines take the Node that runs it, and refuses a Node none takes (`--engine-strict`):
# that Node's own corepack then runs, verifying as it does, and `missing` names what the preparation lacked.
COREPACK_INSTALL = (f"export PATH={T}/corepack/bin:$PATH; [ -x {T}/corepack/bin/corepack ] || {{ npm install -g"
                    f" --prefix {T}/corepack --engine-strict --no-audit --no-fund --loglevel=error"
                    f" \"corepack@>=0.31.0 <=0.36.0\" >&2 || echo 'DAODAN-MISSING corepack@>=0.31.0' >&2; }}")
PYTHON = ("pyproject.toml", "requirements.txt")
VENVS = f"{STATE}/venvs"  # a Python project's environment, per folder
UV_ENV = "export UV_PYTHON_DOWNLOADS=never UV_NO_PROGRESS=1"
UV_SYNC = f'UV_PYTHON_DOWNLOADS=automatic UV_PROJECT_ENVIRONMENT="{VENVS}/$f"'  # uv sync: its own Python, $f's venv
UV_CAUSES = "^ *[×│├╰]|^ *Caused by"  # uv's lines under an error: the requirement, then each cause
WITHOUT = f"{STATE}/without-vcs.txt"  # the project's VCS requirements, as uv overrides no environment matches
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
    # (`restore` with `scripts` runs the install with them first)
    "npm": {"marks": ("package.json",), "family": "node", "error": "^npm (error|ERR!)", "hosts": (),
            "line": "if [ -f package-lock.json ] || [ -f npm-shrinkwrap.json ];"
                    " then npm ci --ignore-scripts --no-audit --no-fund;"
                    " else npm install --ignore-scripts --no-audit --no-fund; fi"},
    # `unlocked`: the restore of a folder that names the manager (`packageManager`) and has no lockfile yet
    "pnpm": {"marks": ("package.json",), "family": "node", "locks": ("pnpm-lock.yaml",), "error": "ERR_PNPM|ERROR",
             "before": COREPACK, "hosts": (), "line": "corepack pnpm install --frozen-lockfile --ignore-scripts",
             "unlocked": "corepack pnpm install --no-frozen-lockfile --ignore-scripts"},
    "yarn": {"marks": ("package.json",), "family": "node", "locks": ("yarn.lock",), "before": COREPACK,
             "error": "^error|YN0[0-9]+: .*Error", "hosts": ("repo.yarnpkg.com",),  # corepack: Yarn 2 and later
             "line": "if [ -f .yarnrc.yml ]; then corepack yarn install --immutable --mode=skip-build;"
                     " else corepack yarn install --frozen-lockfile --ignore-scripts; fi",
             "unlocked": "if [ -f .yarnrc.yml ]; then corepack yarn install --mode=skip-build;"
                         " else corepack yarn install --ignore-scripts; fi"},
    # Python: one family, the lockfile names the manager (none: pip); the environment lives outside the project. uv
    # picks the Python of a folder it restores as `uv sync` does (a version file, else requires-python), downloading
    # it from its host when no interpreter installed has it; the others' Python comes from the toolchains. `without`
    # is the install again without the project's VCS requirements (`restore`)
    "uv": {"marks": PYTHON, "family": "python", "locks": ("uv.lock",), "needs": ["uv"], "before": UV_ENV,
           "error": f"^error|needs to be updated|No solution|{UV_CAUSES}", "hosts": ("releases.astral.sh",),
           "line": f'{UV_SYNC} uv sync --locked --all-packages --no-install-project',
           "without": f'{UV_SYNC} uv sync --locked --all-packages --no-install-project'
                      f" $(sed 's/ .*//; s/^/--no-install-package /' {WITHOUT})"},
    "poetry": {"marks": PYTHON, "family": "python", "locks": ("poetry.lock",), "needs": ["poetry"],
               "error": "poetry.lock|Error|error", "hosts": (),
               "line": "poetry install --no-root --no-interaction"},
    "pip": {"marks": PYTHON, "family": "python", "needs": ["uv"], "before": UV_ENV,
            "error": f"^error|No solution|not found|{UV_CAUSES}", "hosts": (),
            "line": f'r=requirements.txt; [ -f $r ] || r=pyproject.toml; uv venv -q --python python3 "{VENVS}/$f"'
                    f' && uv pip install -q --python "{VENVS}/$f" -r "$r"',
            "without": f'r=requirements.txt; [ -f $r ] || r=pyproject.toml; uv pip install -q --python "{VENVS}/$f"'
                       f' -r "$r" --overrides {WITHOUT}'},
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


OFF = (" --ignore-scripts", " --mode=skip-build")  # what turns a Node manager's lifecycle scripts off in its line
LIMIT = 600  # the seconds a folder's install with its lifecycle scripts may take


def restore(manager: str, folders: list[str], unlocked: bool = False, scripts: bool = False) -> str:
    """The shell line restoring `manager`'s dependencies in each of `folders` (`unlocked`: none has a lockfile, the
    manager resolves): a folder that fails prints `DAODAN-RESTORE-FAILED manager folder`, its error lines,
    `DAODAN-RESTORE-END` on stderr; the line goes on. With `scripts`, project code and so for a container only,
    a folder's install runs first with the manager's lifecycle scripts, where a framework generates what its
    compiler reads (a dependency's `postinstall`, the package's `postinstall` and `prepare`): one that fails or
    outlasts `LIMIT` prints `DAODAN-GENERATE-FAILED manager folder`, its error lines, `DAODAN-GENERATE-END`, and
    the folder is restored without them. A Python folder whose install fails, in a project that declares VCS
    requirements (`WITHOUT`, written by `without`), is installed again without them: one that then succeeds prints
    `DAODAN-VCS-FAILED manager folder`, the first install's error lines, `DAODAN-VCS-END`; one that fails again
    prints the restore's mark with the error lines of both."""
    spec = RESTORES[manager]
    line = full = spec["unlocked" if unlocked else "line"]
    for flag in OFF:
        full = full.replace(flag, "")
    failed = f" && ! grep -Eq '{spec['failed']}' {LOG}" if spec.get("failed") else ""

    def report(mark: str, log: str = LOG) -> str:
        return (f"{{ printf 'DAODAN-{mark}-FAILED {manager} %s\\n' \"$f\"; {{ grep -E '{spec['error']}' {log}"
                f" || tail -n 30 {log}; }} | head -n 30; echo DAODAN-{mark}-END; }} >&2")

    attempt = f"( cd \"$f\" && {line} ) > {LOG} 2>&1{failed} || {report('RESTORE')}"
    if spec.get("without"):
        first = f"{LOG}.vcs"
        attempt = (f"( cd \"$f\" && {line} ) > {LOG} 2>&1 || if [ -s {WITHOUT} ]; then mv {LOG} {first};"
                   f" ( cd \"$f\" && {spec['without']} ) > {LOG} 2>&1 && {report('VCS', first)}"
                   f" || {{ cat {LOG} >> {first}; {report('RESTORE', first)}; }}; else {report('RESTORE')}; fi")
    if scripts and full != line:
        attempt = (f"( cd \"$f\" && timeout {LIMIT} sh -c '{full}' ) > {LOG} 2>&1"
                   f" || {{ {report('GENERATE')}; {attempt}; }}")
    names = " ".join(f"'{f}'" for f in folders)
    before = f"{spec['before']}; " if spec.get("before") else ""
    return f"{before}for f in {names}; do {attempt}; done; true"


NODE_REGISTRIES = ("registry.npmjs.org", "registry.yarnpkg.com")  # npm's, under its two names
# Yarn 2 and later read the proxy from their own settings, never from HTTPS_PROXY.
YARN_PROXY = ('if [ -n "${HTTPS_PROXY:-}" ]; then export YARN_HTTPS_PROXY="$HTTPS_PROXY"'
              ' YARN_HTTP_PROXY="$HTTPS_PROXY"; fi')


def node_restores(files, named=None) -> list[tuple[str, list[str], bool]]:
    """The Node restores among `files` (`restores`), each `(manager, folders, unlocked)`: a folder without a
    lockfile goes to the manager its manifest names (`named`: folder -> manager, its `packageManager`), which
    resolves there (`unlocked`); without either, npm."""
    files, out = set(files), {}
    for manager, folders in restores(files).items():
        for folder in folders if RESTORES[manager].get("family") == "node" else ():
            other = (named or {}).get(folder)
            locked = manager != "npm" or any(posixpath.normpath(f"{folder}/{lock}") in files
                                             for lock in ("package-lock.json", "npm-shrinkwrap.json"))
            free = not locked and "unlocked" in RESTORES.get(other, {})
            out.setdefault((other, True) if free else (manager, False), []).append(folder)
    return [(manager, folders, unlocked) for (manager, unlocked), folders in out.items()]


DECLARED = ("dependencies", "devDependencies", "optionalDependencies")  # what a Node restore installs


def _workspaces(manifest: dict, yaml: str) -> list[str]:
    """The member patterns a Node restore folder declares: its manifest's `workspaces` (a list, or `packages` of
    an object) and its `pnpm-workspace.yaml`'s `packages`."""
    declared = manifest.get("workspaces")
    patterns = declared.get("packages") if isinstance(declared, dict) else declared
    block = re.search(r"^packages:[ \t]*\n((?:[ \t]+-.*\n?)+)", yaml, re.MULTILINE)
    found = re.findall(r"-\s*['\"]?([^'\"#\n]+?)['\"]?\s*(?:#.*)?$", block.group(1), re.MULTILINE) if block else []
    return [str(p) for p in patterns if isinstance(p, str)] + found if isinstance(patterns, list) else found


def _names(patterns: list[str], rel: str) -> bool:
    """Whether workspace `patterns` name the folder `rel`, relative to their root: `*` within a folder name,
    `**` across folders, a `!` pattern excludes."""
    def match(pattern: str) -> bool:
        regex = re.escape(pattern.strip().strip("/").removeprefix("./"))
        return re.fullmatch(regex.replace(r"\*\*", ".*").replace(r"\*", "[^/]*"), rel) is not None
    return any(match(p) for p in patterns if not p.startswith("!")) and not any(
        match(p[1:]) for p in patterns if p.startswith("!"))


def node_prepare(files, read) -> dict:
    """`{restores, lines, hosts, gaps}` for the Node packages among `files`, `read(rel)` a file's text: per
    manager the folders its restore runs in (`node_restores`; a manifest's `packageManager`, the field corepack
    reads, names the manager), the shell lines that restore them with their lifecycle scripts (`restore`), each
    whole on its own (pnpm's and Yarn's install the corepack they run, `COREPACK_INSTALL`), the hosts they reach
    beside npm's registry, and a `restore_failed` gap for each package
    folder that declares dependencies no restore installs: one inside a restore's folder whose workspaces do not
    name it. Project code: for a container's preparation only."""
    files, named, manifests = list(files), {}, {}
    for rel in files:
        if posixpath.basename(rel) == "package.json":
            try:
                manifest = json.loads(read(rel))
            except (OSError, ValueError):
                manifest = None
            manifest = manifest if isinstance(manifest, dict) else {}
            manifests[_folder(rel)] = manifest
            manager = str(manifest.get("packageManager") or "").split("@")[0]
            if manager:
                named[_folder(rel)] = manager
    found = node_restores(files, named)
    plan: dict[str, list[str]] = {}
    for manager, folders, _unlocked in found:
        plan[manager] = sorted(plan.get(manager, []) + folders)
    lines = [(f"{COREPACK_INSTALL}; " if RESTORES[manager].get("before") == COREPACK else "")
             + (f"{YARN_PROXY}; " if manager == "yarn" else "") + restore(manager, folders, unlocked, scripts=True)
             for manager, folders, unlocked in found]
    owner = {folder: manager for manager, folders in plan.items() for folder in folders}
    gaps = []
    for folder, manifest in sorted(manifests.items()):
        if folder in owner or not any(manifest.get(field) for field in DECLARED):
            continue
        root = max((o for o in owner if _inside(folder, o)), key=len, default=None)
        yaml = posixpath.normpath(f"{root}/pnpm-workspace.yaml")
        if root is not None and _names(_workspaces(manifests.get(root, {}), read(yaml) if yaml in files else ""),
                                       folder if root == "." else folder[len(root) + 1:]):
            continue
        gaps.append({"kind": "restore_failed", "manager": owner.get(root), "path": folder,
                     "detail": "its packages are not installed: no workspace above names this folder"})
    return {"restores": plan, "lines": lines, "gaps": gaps,
            "hosts": tuple(dict.fromkeys(host for manager in plan for host in RESTORES[manager]["hosts"]))}


RESTORE = re.compile(r"DAODAN-RESTORE-FAILED (\S+) (.+)\n((?:.*\n)*?)DAODAN-RESTORE-END")


VCS_FAILED = re.compile(r"DAODAN-VCS-FAILED (\S+) (.+)\n((?:.*\n)*?)DAODAN-VCS-END")


def restore_gaps(stderr: str) -> list[dict]:
    """The `restore_failed` gaps a restore line printed: the manager, the folder, the tool's error lines; and the
    `vcs_not_installed` ones, of a folder installed without its project's VCS requirements, with the error lines
    of the install with them (`restore`)."""
    def said(lines: str) -> str:
        return " | ".join(line.strip() for line in lines.splitlines() if line.strip())[:600]

    return [*({"kind": "restore_failed", "manager": manager, "path": folder, "detail": said(lines)}
              for manager, folder, lines in RESTORE.findall(stderr or "")),
            *({"kind": "vcs_not_installed", "manager": manager, "path": folder,
               "detail": f"installed without the VCS requirements the project declares: {said(lines)}"}
              for manager, folder, lines in VCS_FAILED.findall(stderr or ""))]


# A VCS requirement: `name @ git+https://...` (PEP 508) or pip's `git+https://...#egg=name`, and the `{ git = "..." }`
# source of uv and Poetry.
VCS_URL = re.compile(r"(?:([A-Za-z0-9][\w.-]*)\s*(?:\[[^\]]*\])?\s*@\s*)?\b((?:git|hg|svn|bzr)\+[a-z]+://[^\s\"',;]+)")
VCS_SOURCE = re.compile(r"^\s*\"?([A-Za-z0-9][\w.-]*)\"?\s*=\s*\{[^}\n]*\bgit\s*=\s*\"([^\"]+)\"", re.M)


def python_vcs(files, read) -> dict:
    """The VCS requirements the Python manifests among `files` declare (`read(rel)`, a file's text): `{names,
    hosts}`, their names and the hosts their URLs name, the only hosts a preparation reaches for them beside
    the registries, as a CI fetches them."""
    from urllib.parse import urlsplit
    names, hosts = set(), set()
    for rel in files:
        base = posixpath.basename(rel)
        if base not in ("pyproject.toml", "setup.cfg", "setup.py") and not (
                base.endswith((".txt", ".in")) and "requirements" in rel):
            continue
        text = read(rel) or ""
        for name, url in [(name or "".join(re.findall(r"#egg=([\w.-]+)", url)[:1]), url.split("+", 1)[1])
                          for name, url in VCS_URL.findall(text)] + VCS_SOURCE.findall(text):
            names.add(name)
            hosts.add(urlsplit(url).hostname or "")
    return {"names": sorted(names - {""}), "hosts": sorted(hosts - {""})}


def without(names: list[str]) -> str:
    """The line that writes `WITHOUT`: each of the VCS requirements `names` (`python_vcs`) as a uv override no
    environment matches, so an install with it takes everything else."""
    return f"printf '%s ; sys_platform == \"never\"\\n' {' '.join(names)} > {WITHOUT}"


def declared(record: dict) -> dict:
    """The hosts a project declares its dependencies come from, the pre-map units' `registries` (an index, a
    repository, a feed, a VCS host), which a preparation reaches beside the registries as a CI does; github.com
    with the hosts GitHub serves its downloads from (`GITHUB`), where npm fetches a GitHub dependency.
    `{hosts, where}`: `where` gives each host the manifests of the units that declare it."""
    from urllib.parse import urlsplit
    where: dict[str, set] = {}
    for unit in record.get("units") or ():
        for url in unit.get("registries") or ():
            try:
                host = urlsplit(url).hostname
            except ValueError:
                continue
            for name in GITHUB if host == "github.com" else (host,) if host else ():
                where.setdefault(name, set()).add(unit.get("manifest") or unit["root"])
    return {"hosts": tuple(sorted(where)), "where": {host: sorted(files) for host, files in sorted(where.items())}}


# A tool's words for a host it could not reach: no name, no connection, a refusal, a timeout.
UNREACHED = re.compile(r"dns error|lookup address|no such host|name resolution|Name or service not known|"
                       r"resolve host|UnknownHost|ENOTFOUND|"
                       r"EAI_AGAIN|ECONNREFUSED|ECONNRESET|ETIMEDOUT|Connection refused|Connection reset|timed out|"
                       r"Connect to |client error \(Connect\)|tunnel|proxy|403 Forbidden|status code 403|"
                       r"Unable to load the service index", re.I)


def unreached(gaps: list[dict], declared: dict) -> list[dict]:
    """A `host_unreachable` gap for each declared host (`declared`) a failed restore's words name and say it could
    not reach, with the files that declare it."""
    return [{"kind": "host_unreachable", "host": host, "declared_in": files, "path": gap["path"],
             "detail": f"the restore of {gap['path']} could not reach {host}, declared in {', '.join(files)}: "
                       f"{gap['detail'][:400]}"}
            for gap in gaps
            if gap["kind"] in ("restore_failed", "vcs_not_installed") and UNREACHED.search(gap["detail"])
            for host, files in declared["where"].items()
            if re.search(rf"(?<![\w.-]){re.escape(host)}(?![\w-])", gap["detail"])]


GENERATE = re.compile(r"DAODAN-GENERATE-FAILED (\S+) (.+)\n((?:.*\n)*?)DAODAN-GENERATE-END")


def generation_gaps(stderr: str) -> list[dict]:
    """The `generation_failed` gaps a restore with lifecycle scripts printed: the manager, the folder, the error
    lines of the install whose scripts failed; the folder was then restored without them. A folder whose restore
    failed without them too has that gap only (`restore_gaps`): its scripts were not the cause."""
    failed = {(manager, folder) for manager, folder, _lines in RESTORE.findall(stderr or "")}
    return [{"kind": "generation_failed", "manager": manager, "path": folder,
             "detail": " | ".join(line.strip() for line in lines.splitlines() if line.strip())[:600]}
            for manager, folder, lines in GENERATE.findall(stderr or "") if (manager, folder) not in failed]


MISSING = re.compile(r"DAODAN-MISSING (\S+)@(\S+)(?: (.+))?")


def missing(stderr: str) -> list[dict]:
    """The `toolchain_unavailable` gaps a preparation's output names: what it could not install, and why when the
    line says it after the version."""
    said: dict[tuple[str, str], str] = {}
    for tool, version, why in MISSING.findall(stderr or ""):
        said.setdefault((tool, version), why.strip())
    return [{"kind": "toolchain_unavailable", "tool": tool, "version": version, "detail": f"{tool} {version}: "
             + (why[:600] or "the preparation could not install it (its output is in the run's log)")}
            for (tool, version), why in said.items()]


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
