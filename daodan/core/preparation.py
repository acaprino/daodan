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

from itertools import takewhile
import json
from pathlib import Path
import posixpath
import re
import shlex

from tree_scope import Perimeter, workspace_glob

STATE = "/daodan/state"
IN, T = f"{STATE}/in", f"{STATE}/tools"
# The base every container run starts from: what a language needs beside it, its toolchain and its tools, comes
# into the run as an input. The image the other languages already run on (`container_runner.IMAGE`, Ubuntu
# 24.04, glibc 2.39), pinned by digest: it has what the recipes and restores need, the CA certificates https clients
# read (`go mod download`, cargo, git, mise) and `xz` (`tar -xJf`). Debian's slim image, the base before, has
# neither (`benchmarks/egress/README.md`, `modal_image.py`); installing them in each run would ask the archive anew.
IMAGE = "buildpack-deps:noble@sha256:890e8b5c0040e1deff5cc7dc7b4414e67069f79e3301afc4ec5bd49d64ef13e5"
# Temurin's JDK 17 (17.0.21+9), the release asset and the sha256 Adoptium publishes for it: the JDK of scip-java
# and of the pre-map's JVM build tools.
TEMURIN = ("https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.21%2B9/"
           "OpenJDK17U-jdk_x64_linux_hotspot_17.0.21_9.tar.gz",
           "8b9b611d917e3dfd8419d3566b5949226f69b052fed7e109c1368add1dfe8711")
JDK_IN, JDK_HOME = f"{IN}/temurin-17.tar.gz", f"{STATE}/jdk"
GITHUB = ("github.com", "codeload.github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com")
UV = ("https://github.com/astral-sh/uv/releases/download/0.11.28/uv-x86_64-unknown-linux-gnu.tar.gz",
      "e490a6464492183c5d4534a5527fb4440f7f2bb2f228162ad7e4afe076dc0224", "uv.tar.gz")
PATH = ":".join([f"{T}/bin", f"{T}/node/bin", f"{T}/npm/bin", f"{T}/go/bin", f"{T}/rust/bin", f"{T}/cmake/bin",
                 "/opt/java/openjdk/bin",  # Temurin's java and jar, linked there (`UNPACK_JDK`)
                 "/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin"])
ENV = {"PATH": PATH, "HOME": f"{STATE}/home", "GOPATH": f"{STATE}/go", "GOCACHE": f"{STATE}/go-build",
       "GOTELEMETRY": "off", "CARGO_HOME": f"{STATE}/cargo", "UV_CACHE_DIR": f"{STATE}/uv",
       "npm_config_cache": f"{STATE}/npm-cache", "npm_config_update_notifier": "false",
       "VCPKG_ROOT": f"{T}/vcpkg", "VCPKG_DISABLE_METRICS": "1", "VCPKG_BINARY_SOURCES": "clear",
       "CONAN_HOME": f"{STATE}/conan-home"}  # what every container command of the preparation and after runs with
NODE = ("https://nodejs.org/dist/v24.22.3/node-v24.22.3-linux-x64.tar.gz",
        "061ec3e3062115705b56b51fa9cc330ab50d34b6969387d4e4b1a50c6809acc2", "node.tar.gz")  # `renovate.NODE`
GO = ("https://go.dev/dl/go1.27.3.linux-amd64.tar.gz",
      "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40", "go.tar.gz")  # `engine_tools.GO_VERSION`
RUST = [("https://static.rust-lang.org/dist/2026-10-15/rustc-1.99.1-x86_64-unknown-linux-gnu.tar.xz",
         "2ff05ff9c08a90861e7f6e4065b40a8b87463b4576186fd613871c3e37f2091f", "rustc.tar.xz"),
        ("https://static.rust-lang.org/dist/2026-10-15/cargo-1.99.1-x86_64-unknown-linux-gnu.tar.xz",
         "53f3521949404d595efb06a55c12c5658d4ed1c75566f33d3d514eaebe70bd8a", "cargo.tar.xz")]
UNPACK_UV = f"mkdir -p {T}/uvc {T}/bin && tar -xzf {IN}/uv.tar.gz -C {T}/uvc && ln -sf {T}/uvc/*/uv {T}/bin/uv"


def unpacked(archive: str, home: str, program: str, link: str) -> str:
    """Shell lines that unpack `archive`, a .tar.gz with one top folder, into `home` in the state volume once and
    remove it, then link `home` at `link`: the volume carries `home` from the preparation to the execution, the
    container's own root, where `link` is, does not."""
    return (f"if [ ! -x {home}/{program} ] && [ -f {archive} ]; then\n"
            f"  mkdir -p {home} && tar -xzf {archive} -C {home} --strip-components=1 && rm -f {archive}\n"
            f"fi\nmkdir -p {posixpath.dirname(link)} && ln -sfn {home} {link}\n")


UNPACK_JDK = unpacked(JDK_IN, JDK_HOME, "bin/java", "/opt/java/openjdk")  # where `PATH` and the scripts look
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
    # The image's own git (VCS requirements need it; Python's Debian image has none), from its archive by the plain
    # HTTP its sources name: apt checks the signed Release files and each package's hash, and the proxy opens only a
    # GET or HEAD of `dists/` and `pool/` of a canonical archive (`http://deb.debian.org`, the Ubuntu ones). Not
    # https: a slim image without ca-certificates cannot verify it, and getting them would need this HTTP first.
    "git": {"files": [], "setup": [
        'export DEBIAN_FRONTEND=noninteractive && apt-get -qq -o Acquire::http::Proxy="$HTTP_PROXY"'
        ' -o Acquire::Languages=none update && apt-get -qq -o Acquire::http::Proxy="$HTTP_PROXY"'
        ' install -y --no-install-recommends git'],
        "hosts": ("http://deb.debian.org",), "version": "debian"},
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
    # java: the catalog of vendor builds (`mise-java.jdx.dev`, src/plugins/core/java.rs) and Temurin's, GitHub's
    "node": ("nodejs.org",), "go": ("go.dev", "dl.google.com"), "python": GITHUB, "java": ("mise-java.jdx.dev",
    "api.adoptium.net", *GITHUB), "ruby": GITHUB, "rust": ("static.rust-lang.org", "sh.rustup.rs"),
    "dotnet": ("dot.net", "builds.dotnet.microsoft.com", "dotnetcli.azureedge.net"),
    "swift": ("download.swift.org",),
    "zig": ("ziglang.org",), "bun": GITHUB, "deno": GITHUB, "cmake": GITHUB, "bazel": GITHUB, "uv": GITHUB,
    "maven": GITHUB, "gradle": ("services.gradle.org", *GITHUB)}
MISE_OWN = ("mise-versions.jdx.dev", *GITHUB)
EXACT = re.compile(r"^v?\d+(\.\d+){0,2}([-.+][0-9A-Za-z.]+)?$")  # a version mise installs as written, no range
# The vendors of Gradle's `JvmVendorSpec` (`KnownJvmVendor`, gradle/gradle, platforms/jvm/jvm-services): the name a
# build's `toolchainVendor` holds (the key), the name its messages print (`display`), the vendor of mise's JDK
# catalog (`mise ls-remote java`, mise-java.jdx.dev) that is that distribution, and the hosts its archives come from
# beside those of `MISE_HOSTS["java"]`, redirects followed (tests/fixtures/premap/mise-java-vendors.json). The
# catalog holds no AdoptOpenJDK, Apple or HP-UX build (`mise` None): a build asking for one is a gap.
JDK_VENDORS = {
    "ADOPTIUM": {"display": "Eclipse Temurin", "mise": "temurin", "hosts": ()},
    "ADOPTOPENJDK": {"display": "AdoptOpenJDK", "mise": None, "hosts": ()},
    "AMAZON": {"display": "Amazon Corretto", "mise": "corretto", "hosts": ("corretto.aws",)},
    "APPLE": {"display": "Apple", "mise": None, "hosts": ()},
    "AZUL": {"display": "Azul Zulu", "mise": "zulu", "hosts": ("cdn.azul.com",)},
    "BELLSOFT": {"display": "BellSoft Liberica", "mise": "liberica", "hosts": ()},
    "GRAAL_VM": {"display": "GraalVM Community", "mise": "graalvm-community", "hosts": ()},
    "HEWLETT_PACKARD": {"display": "HP-UX", "mise": None, "hosts": ()},
    "IBM": {"display": "IBM", "mise": "semeru-openj9", "hosts": ()},
    "JETBRAINS": {"display": "JetBrains", "mise": "jetbrains",
                  "hosts": ("cache-redirector.jetbrains.com", "d2xrhe97vsfxuc.cloudfront.net")},
    "MICROSOFT": {"display": "Microsoft", "mise": "microsoft",
                  "hosts": ("aka.ms", "download.visualstudio.microsoft.com")},
    "ORACLE": {"display": "Oracle", "mise": "oracle", "hosts": ("download.oracle.com",)},
    "SAP": {"display": "SAP SapMachine", "mise": "sapmachine", "hosts": ()},
    "TENCENT": {"display": "Tencent", "mise": "kona", "hosts": ()},
}


def jdk_vendor(name) -> str | None:
    """The key of `JDK_VENDORS` a vendor stands for, as a build writes it (`JETBRAINS`) or Gradle prints it
    (`JetBrains`), in any case; None when it is neither."""
    text = str(name or "").strip().casefold()
    return next((key for key, row in JDK_VENDORS.items() if text in (key.casefold(), row["display"].casefold())), None)


def vendor_label(name) -> str:
    """A vendor as Gradle prints it: the display name of one of the table, else the words as given."""
    key = jdk_vendor(name)
    return JDK_VENDORS[key]["display"] if key else str(name)


def asked_vendor(words) -> str | None:
    """The vendor Gradle's words name, as printed; None when they name none (`vendor=any vendor`)."""
    text = str(words or "").strip()
    return None if not text or text.casefold().startswith("any") else text


def vendor_key(name) -> str:
    """The vendor of a JDK as mise names it, so two names of one are equal: a vendor of the table by its mise name
    (`jetbrains`), one it does not hold as written, and no vendor, which is mise's default (`java@21` is Temurin's,
    as the image's JDK is)."""
    key = jdk_vendor(name)
    return (JDK_VENDORS[key]["mise"] or key) if key else str(name or "temurin").strip().casefold()


def mise_version(item: dict) -> str:
    """What mise installs for a stated toolchain: its version, and for a JDK of a vendor of the table the vendor
    before it (`jetbrains-21`)."""
    row = JDK_VENDORS.get(jdk_vendor(item.get("vendor")) or "") if item.get("tool") == "java" else None
    return f"{row['mise']}-{item['version']}" if row and row["mise"] else str(item.get("version") or "")


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
    fails prints `DAODAN-MISSING tool@version` on stderr and the run goes on with what installed. A JDK of a
    vendor (`vendor`, a name of `JDK_VENDORS`) is installed under the vendor's name in mise's catalog
    (`jetbrains-21`) and reaches the hosts of its archives; a vendor mise has no JDK of is a gap naming it."""
    wanted, least, second, gaps, hosts_of = {}, {}, [], [], []
    for item in stated:
        tool, version = item.get("tool"), str(item.get("version") or "")
        vendor = item.get("vendor") if tool == "java" else None
        row = JDK_VENDORS.get(jdk_vendor(vendor) or "")
        minimum = posixpath.basename(str(item.get("declared_in") or "").split("#")[0]) in MINIMUMS.get(tool, ())
        if minimum and tool == "go":
            version = version.removeprefix("go")  # a toolchain line names goV
        why = ("no installer for this tool" if tool not in MISE_HOSTS else
               "a range, not a version to install" if not EXACT.match(version) else
               f"mise has no JDK of the vendor {vendor}" if vendor and not (row and row["mise"]) else None)
        if why:
            gaps.append({"kind": "toolchain_unavailable", "tool": tool, "version": version,
                         **({"vendor": vendor} if vendor else {}), "path": item.get("declared_in"),
                         "detail": f"{tool} {version}: {why}"})
            continue
        version = mise_version(item) if vendor else version
        if minimum:
            least[tool] = max(least.get(tool, version), version, key=_release)
        elif wanted.setdefault(tool, version.lstrip("v")) != version.lstrip("v"):
            second.append((item, version))
        elif row:
            hosts_of += row["hosts"]
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
    hosts = tuple(dict.fromkeys([*MISE_OWN, *(h for tool in sorted(wanted) for h in MISE_HOSTS[tool]), *hosts_of]))
    return {"files": [MISE], "lines": lines, "hosts": hosts, "gaps": gaps}


def jdk_major(version) -> int | None:
    """The major of a JDK version as a project states it: `21`, `21.0.2`, `21-ea`, `1.8` (8); None when it starts with
    no number. The one parser of the pre-map's runner and the JVM indexer. Hand-written: `packaging.version` was weighed
    and does not fit, it is no dependency here, it rejects `21-ea` and `21-open` and reads Java's `1.8` as major 1."""
    head = str(version or "").strip().removeprefix("1.")
    digits = "".join(takewhile(str.isdigit, head))
    return int(digits) if digits else None


def jdk_named(least: int, said: str, stated=(), who: str = "the build", vendor=None) -> tuple[dict, dict | None]:
    """The JDK a build runs again on when `who` said in `said` that it needs one of `least` or newer: the newest of the
    pre-map's `stated` toolchains at or above that version, else the version named, with a `jdk_from_build_error` gap:
    the project states no such JDK, and the build ran on the one its error names. `vendor`, when the words name one
    (Gradle prints it, `any vendor` for none), is part of the request: a stated JDK is the one only if it is of that
    vendor, and the JDK named carries the vendor, as the table names it (`JDK_VENDORS`) or as printed."""
    asked = asked_vendor(vendor)
    newer = [t for t in stated or () if t.get("tool") == "java" and (jdk_major(t.get("version")) or 0) >= least
             and (not asked or vendor_key(t.get("vendor")) == vendor_key(asked))]
    if newer:
        return max(newer, key=lambda t: jdk_major(t["version"])), None
    key = jdk_vendor(asked)
    kind = f"{vendor_label(asked)} JDK" if asked else "JDK"
    return {"tool": "java", "version": str(least), **({"vendor": key or asked} if asked else {}),
            "declared_in": f"{who}'s error"}, {
        "kind": "jdk_from_build_error", "detail": f"{who} said `{said}` and the project states no {kind} "
        f"at or above {least}: the build ran again on {kind} {least}, the version {who}'s error names"}


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
NPM_LOCKS = ("package-lock.json", "npm-shrinkwrap.json")  # npm's lockfiles: the one place that names them
RESTORES = {  # manager -> the files that mark where its build starts, its own restore, what in its output is an
    # error (`error`) or a failure it reports with success (`failed`), the hosts beside the registries
    "gradle": {"marks": ("settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts"),
               "line": "gradle --no-daemon --console=plain -q dependencies",  # every project's configurations
               "failed": " FAILED$", "error": " FAILED$|What went wrong|Could not ", "before": JAVA_PROXY,
               "hosts": ("plugins.gradle.org", "plugins-artifacts.gradle.org", "services.gradle.org",
                         "dl.google.com", "maven.google.com")},
    "maven": {"marks": ("pom.xml",), "error": r"^\[ERROR\]", "before": JAVA_PROXY, "hosts": (),
              "line": "mvn -B -q org.apache.maven.plugins:maven-dependency-plugin:3.8.1:go-offline"},
    # Node: one family, `package.json` marks the folders, the lockfile names the manager (none: npm, the `default`);
    # scripts off (`restore` with `scripts` runs the install with them first)
    "npm": {"marks": ("package.json",), "family": "node", "locks": NPM_LOCKS, "default": True,
            "error": "^npm (error|ERR!)", "hosts": (),
            "line": f"if {' || '.join(f'[ -f {lock} ]' for lock in NPM_LOCKS)};"
                    " then npm ci --ignore-scripts --no-audit --no-fund;"
                    " else npm install --ignore-scripts --no-audit --no-fund; fi"},
    # Lerna before 7 links and installs the packages `lerna.json` names with its own `bootstrap`, after the root's install
    # put it in `node_modules` (`node_prepare`); its `--ignore-scripts` keeps the packages' lifecycle scripts off
    "lerna": {"marks": ("lerna.json",), "family": "lerna", "error": "lerna (ERR!|error)", "hosts": (),
              "line": "node_modules/.bin/lerna bootstrap --ignore-scripts"},
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
    # `alone`: a folder whose only mark is a requirements file is a project of its own at any depth: pip installs it
    # where it is (`pip install -r`), and no workspace names one (uv's and Poetry's members are pyproject projects)
    "pip": {"marks": PYTHON, "family": "python", "alone": ("requirements.txt",), "needs": ["uv"], "before": UV_ENV,
            "error": f"^error|No solution|not found|{UV_CAUSES}", "hosts": (),
            "line": f'r=requirements.txt; [ -f $r ] || r=pyproject.toml; uv venv -q --python python3 "{VENVS}/$f"'
                    f' && uv pip install -q --python "{VENVS}/$f" -r "$r"',
            "without": f'r=requirements.txt; [ -f $r ] || r=pyproject.toml; uv pip install -q --python "{VENVS}/$f"'
                       f' -r "$r" --overrides {WITHOUT}'},
    "go": {"marks": ("go.mod",), "nested": True, "needs": ["go"], "error": "go: |go.mod:|error", "hosts": (),
           "line": "go mod download"},  # each module is its own; the toolchain go.mod names comes from its proxy
    "dotnet": {"marks": (), "suffixes": (".sln", ".slnx", ".csproj", ".fsproj", ".vbproj"), "needs": ["dotnet"],
               "before": "export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1",
               # a folder's solution, else its one project; a solution that does not restore (one project needs
               # what the container lacks, a workload) restores each project it lists, and its failure stays a gap
               "error": "error", "hosts": (),
               "line": "{ s=$(ls *.slnx *.sln 2>/dev/null | head -n 1); dotnet restore $s || { [ -n \"$s\" ] &&"
                       " dotnet sln \"$s\" list | tail -n +3 | tr '\\\\' / | while read -r p; do dotnet restore"
                       " \"$p\"; done; false; }; }"},
    # A `Cargo.lock` is written at the root of a Cargo workspace: a crate below another with its own is a workspace of
    # its own, restored where it sits; one without is a member the root restores.
    "cargo": {"marks": ("Cargo.toml",), "locks": ("Cargo.lock",), "default": True, "needs": ["rust"],
              "error": "^error|^Caused by|^  ", "hosts": (),

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
    marked folder of a manager that is `nested` (each Go module is its own) or marked only by its `alone` files (a
    `requirements.txt`), and each folder with a lockfile of its own (npm's too: `NPM_LOCKS`); within a family, the folder's lockfile names the manager, and the `default` one, else
    the one without `locks`, is the manager of a folder without."""
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
        default = next(name for name in managers if RESTORES[name].get("default") or not RESTORES[name].get("locks"))
        alone, held = {m for name in managers for m in RESTORES[name].get("alone", ())}, {}
        for rel in files if alone else ():
            if posixpath.basename(rel) in marks:
                held.setdefault(_folder(rel), set()).add(posixpath.basename(rel))
        for folder in marked:
            nested = any(RESTORES[name].get("nested") for name in managers)
            own = bool(held.get(folder)) and held[folder] <= alone
            if nested or own or folder in locked or not any(o != folder and _inside(folder, o) for o in marked):
                out.setdefault(locked.get(folder, default), []).append(folder)
    return out


def perimeter_files(project) -> list[str]:
    """The files of a project's perimeter, relative and sorted: the ones a container is given a copy of (git-ignored untracked files are left
    out) and every restore reads. What a command decides from the files of the project, the manager of a folder by its lockfile first, it
    decides from this set, so that it and the restore pick the same."""
    return sorted((directory / name).relative_to(project).as_posix() for directory, names in Perimeter(project).walk() for name in names)


def python_locks(files, exists) -> list[str]:
    """The lockfiles of the Python managers that the checkout holds beside a Python manifest of `files` (the snapshot keeps none):
    `exists(rel)` says whether one is there."""
    locks = {posixpath.join(posixpath.dirname(rel), lock) for rel in files if posixpath.basename(rel) in PYTHON
             for manager in RESTORES.values() if manager.get("family") == "python" for lock in manager.get("locks", ())}
    return sorted(lock for lock in locks - set(files) if exists(lock))


def python_environments(files, exists=None) -> dict[str, str]:
    """`{folder: manager}` of the Python environments the restore makes (`restores`) from `files`, and from the lockfiles `exists` says
    the checkout holds beside them where the files are the snapshot's, which keeps none: the root, a folder with a lockfile of its own, and
    a marked folder no other marked folder holds. A uv workspace is one environment, at its root, with its members' dependencies."""
    files = [*files, *(python_locks(files, exists) if exists else ())]
    return {folder: manager for manager, folders in restores(files).items()
            if RESTORES[manager].get("family") == "python" for folder in folders}


def python_environment(held, folder) -> str | None:
    """The folder whose environment a command in `folder` runs in: the nearest one of `held` at or above it, the root when none is
    nearer; None where none is above."""
    above = [env for env in held if env == "." or folder == env or folder.startswith(env + "/")]
    return max(above, key=lambda env: (env != ".", len(env))) if above else None


def python_interpreter(env, manager, workdir) -> str:
    """The shell word of the Python of the environment restored for the folder `env`: `<VENVS>/<env>/bin/python`, and for Poetry, whose
    environment lives in its own cache, what `poetry env info -e` says in that folder (`workdir` is where the project is)."""
    if manager == "poetry":
        return f'"$(cd {shlex.quote(posixpath.join(workdir, env))} && poetry env info -e)"'
    return shlex.quote(f"{VENVS}/{env}/bin/python")


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
            locked = any(posixpath.normpath(f"{folder}/{lock}") in files for lock in RESTORES[manager]["locks"])
            free = not locked and "unlocked" in RESTORES.get(other, {})
            out.setdefault((other, True) if free else (manager, False), []).append(folder)
    return [(manager, folders, unlocked) for (manager, unlocked), folders in out.items()]


DECLARED = ("dependencies", "devDependencies", "optionalDependencies")  # what a Node restore installs


def _workspaces(manifest: dict, yaml: str, manager: str) -> list[str]:
    """The member patterns the restore of `manager` reads in a Node folder: pnpm's, its `pnpm-workspace.yaml`'s
    `packages`; npm's and Yarn's, the manifest's `workspaces` (a list, or `packages` of an object). Each ignores the
    other's declaration."""
    if manager != "pnpm":
        declared = manifest.get("workspaces")
        patterns = declared.get("packages") if isinstance(declared, dict) else declared
        return [str(p) for p in patterns if isinstance(p, str)] if isinstance(patterns, list) else []
    block = re.search(r"^packages:[ \t]*\n((?:[ \t]+-.*\n?)+)", yaml, re.MULTILINE)
    return re.findall(r"-\s*['\"]?([^'\"#\n]+?)['\"]?\s*(?:#.*)?$", block.group(1), re.MULTILINE) if block else []


LERNA_PACKAGES = ["packages/*"]  # what Lerna reads when `lerna.json` names no `packages` (lerna.js.org, configuration)


def _lerna(text: str) -> list[str]:
    """The package patterns of a `lerna.json`: its `packages`, Lerna's default without them; none for a file JSON does
    not read."""
    try:
        data = json.loads(text)
    except ValueError:
        return []
    patterns = data.get("packages", LERNA_PACKAGES) if isinstance(data, dict) else []
    return [str(p) for p in patterns if isinstance(p, str)] if isinstance(patterns, list) else []


def _names(patterns: list[str], rel: str) -> bool:
    """Whether workspace `patterns` name the folder `rel`, relative to their root: `*` within a folder name,
    `**` across folders, a `!` pattern excludes."""
    def match(pattern: str) -> bool:
        return workspace_glob(pattern.strip().strip("/").removeprefix("./")).fullmatch(rel) is not None
    return any(match(p) for p in patterns if not p.startswith("!")) and not any(
        match(p[1:]) for p in patterns if p.startswith("!"))


def node_prepare(files, read, stated=()) -> dict:
    """`{restores, lines, hosts, gaps}` for the Node packages among `files`, `read(rel)` a file's text: per
    manager the folders its restore runs in (`node_restores`; a manifest's `packageManager`, the field corepack
    reads, names the manager), the shell lines that restore them with their lifecycle scripts (`restore`), each
    whole on its own (pnpm's and Yarn's install the corepack they run, `COREPACK_INSTALL`), the hosts they reach
    beside npm's registry, and a `restore_failed` gap for each package
    folder that declares dependencies no restore installs: one inside a restore's folder whose workspaces do not
    name it, unless the `lerna.json` of such a folder names it: then Lerna's `bootstrap` installs it there, after the
    root's restore (`RESTORES["lerna"]`). A folder holding a local dependency outside the copy
    (`local_dependencies`, and the pre-map's `stated` gaps, `refusals`: the `yarn.lock` entries Yarn's parser reads
    in the container) does not restore. Project code: for a container's preparation only."""
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
    def covered(folder: str, roots: dict[str, str]) -> bool:
        """Whether the restore of one of `roots` (folder -> manager) above `folder` installs it: the workspaces the
        root's manager reads name it."""
        def names(root: str, manager: str) -> bool:
            yaml = posixpath.normpath(f"{root}/pnpm-workspace.yaml")
            return _names(_workspaces(manifests.get(root, {}), read(yaml) if yaml in files else "", manager),
                          folder if root == "." else folder[len(root) + 1:])

        return any(root != folder and _inside(folder, root) and names(root, manager) for root, manager in roots.items())

    found = node_restores(files, named)
    # A folder a workspace above names is restored by that root, a lockfile of its own left in it or not: from the
    # outermost folder inward, so a root another installs names no members of its own.
    roots: dict[str, str] = {}
    for manager, folder in sorted(((m, f) for m, folders, _unlocked in found for f in folders),
                                  key=lambda item: (0 if item[1] == "." else item[1].count("/") + 1, item[1])):
        if not covered(folder, roots):
            roots[folder] = manager
    found = [(manager, [f for f in folders if f in roots], unlocked) for manager, folders, unlocked in found]
    found = [row for row in found if row[1]]
    # A restore that would install a local dependency outside the copy, or at an absolute path, does not run.
    local = local_dependencies(files, read, "node")
    blocked = refused({folder for _manager, folders, _unlocked in found for folder in folders}, [*local, *stated])
    found = [(manager, kept, unlocked) for manager, folders, unlocked in found
             for kept in [[f for f in folders if f not in blocked]] if kept]
    plan: dict[str, list[str]] = {}
    for manager, folders, _unlocked in found:
        plan[manager] = sorted(plan.get(manager, []) + folders)
    lines = [(f"{COREPACK_INSTALL}; " if RESTORES[manager].get("before") == COREPACK else "")
             + (f"{YARN_PROXY}; " if manager == "yarn" else "") + restore(manager, folders, unlocked, scripts=True)
             for manager, folders, unlocked in found]
    owner = {folder: manager for manager, folders in plan.items() for folder in folders}
    lerna = {_folder(rel): _lerna(read(rel)) for rel in files if posixpath.basename(rel) == "lerna.json"}
    gaps, bootstrap = list(local), set()
    for folder, manifest in sorted(manifests.items()):
        if folder in owner or not any(manifest.get(field) for field in DECLARED) or any(
                _inside(folder, b) for b in blocked):
            continue
        if covered(folder, owner):
            continue
        root = next((root for root in sorted(lerna, key=len, reverse=True) if root in owner and root != folder
                     and _inside(folder, root) and _names(lerna[root], folder if root == "." else folder[len(root) + 1:])),
                    None)
        if root is not None:  # a package of a Lerna root a restore installs: its bootstrap installs it
            bootstrap.add(root)
            continue
        root = max((o for o in owner if _inside(folder, o)), key=len, default=None)
        gaps.append({"kind": "restore_failed", "manager": owner.get(root), "path": folder,
                     "detail": "its packages are not installed: no workspace above names this folder"})
    if bootstrap:
        plan["lerna"] = sorted(bootstrap)
        lines.append(restore("lerna", sorted(bootstrap)))
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


def python_vcs(files, read) -> dict:
    """The VCS requirements the Python manifests among `files` declare (`read(rel)`, a file's text): `{names,
    hosts}`, their names and the hosts their URLs name, the only hosts a preparation reaches for them beside
    the registries, as a CI fetches them. Each manifest is read by its own format's reader
    (`premap.requirements.vcs_requirements`: pip's parser, `packaging`, `tomllib`, `configparser`, `ast`)."""
    from urllib.parse import urlsplit
    from premap.requirements import vcs_requirements
    names, hosts = set(), set()
    for rel in files:
        base = posixpath.basename(rel)
        if base not in ("pyproject.toml", "setup.cfg", "setup.py") and not (
                base.endswith((".txt", ".in")) and "requirements" in rel):
            continue
        for name, url in vcs_requirements(rel, read(rel) or ""):
            names.add(name)
            try:
                hosts.add(urlsplit(url).hostname or "")
            except ValueError:
                continue
    return {"names": sorted(names - {""}), "hosts": sorted(hosts - {""})}


NODE_LOCAL = ("file:", "link:", "portal:")  # npm's, pnpm's and Yarn's protocols for a folder (npm-package-arg, Yarn)
PYTHON_LOCAL = ("pyproject.toml", "uv.lock", "poetry.lock")


def _escapes(folder: str, target: str) -> str | None:
    """Why the path `target`, written in a file of `folder`, is refused: absolute, or outside the copy of the
    project once joined to `folder`; None for a path inside the copy (a workspace, a member: legitimate)."""
    if target.startswith(("/", "~", "\\")) or target[1:3] in (":/", ":\\"):  # POSIX, home, Windows
        return "an absolute path"
    joined = posixpath.normpath(posixpath.join(folder, target))
    return "outside the copy of the project" if joined == ".." or joined.startswith("../") else None


def _node_local(rel: str, text: str) -> list[tuple[str, str, str]]:
    """`(entry, folder the path is from, path)` of each local dependency a Node file states: a manifest's
    dependency with a folder protocol or a path (JSON); `package-lock.json`'s linked packages (`link`, `resolved`,
    npm's documented format, JSON); `pnpm-lock.yaml`'s importers whose version is `link:` or `file:` and its
    packages resolved from a `directory` (YAML). Yarn's lockfile repeats the manifests' specs: they are read there."""
    import yaml
    name, folder = posixpath.basename(rel), _folder(rel)
    found = []
    try:
        data = yaml.safe_load(text) if name == "pnpm-lock.yaml" else json.loads(text)
    except (ValueError, yaml.YAMLError):
        return []
    data = data if isinstance(data, dict) else {}
    if name == "package.json":
        for field in DECLARED:
            for key, spec in (data.get(field) or {}).items() if isinstance(data.get(field), dict) else ():
                if isinstance(spec, str) and spec.startswith((*NODE_LOCAL, ".", "/", "~")):
                    path = spec.split(":", 1)[1] if spec.startswith(NODE_LOCAL) else spec
                    found.append((f"{field}.{key}: {spec}", folder, path.removeprefix("//")))
    elif name == "package-lock.json":
        for key, entry in (data.get("packages") or {}).items() if isinstance(data.get("packages"), dict) else ():
            resolved = entry.get("resolved") if isinstance(entry, dict) else None
            if isinstance(resolved, str) and (entry.get("link") or resolved.startswith("file:")):  # a folder, a tarball
                found.append((f"packages.{key}: {resolved}", folder, resolved.removeprefix("file:")))
    elif name == "pnpm-lock.yaml":
        importers = data.get("importers") if isinstance(data.get("importers"), dict) else {".": data}
        for importer, deps in importers.items():
            for field in DECLARED:
                table = deps.get(field) if isinstance(deps, dict) else None
                for key, value in table.items() if isinstance(table, dict) else ():
                    version = value.get("version") if isinstance(value, dict) else value
                    if isinstance(version, str) and version.startswith(("link:", "file:")):
                        found.append((f"importers.{importer}.{field}.{key}: {version}",
                                      posixpath.normpath(posixpath.join(folder, str(importer))),
                                      version.split(":", 1)[1]))
        for key, entry in (data.get("packages") or {}).items() if isinstance(data.get("packages"), dict) else ():
            resolution = entry.get("resolution") if isinstance(entry, dict) else None
            if isinstance(resolution, dict) and isinstance(resolution.get("directory"), str):
                found.append((f"packages.{key}", folder, resolution["directory"]))
    return found


def _python_local(rel: str, text: str) -> list[tuple[str, str, str]]:
    """`(entry, folder the path is from, path)` of each local dependency a Python file states: requirements files
    and `pyproject.toml` by `premap.requirements.local_requirements`; `uv.lock`'s `directory`, `editable` and `path`
    sources and `poetry.lock`'s `directory` and `file` ones (`tomllib`, the formats uv and Poetry document)."""
    import tomllib
    from premap.requirements import local_requirements
    name, folder = posixpath.basename(rel), _folder(rel)
    if name not in ("uv.lock", "poetry.lock"):
        return [(entry, folder, path) for entry, path in local_requirements(rel, text)]
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return []
    found = []
    for package in data.get("package") or [] if isinstance(data.get("package"), list) else []:
        source = package.get("source") if isinstance(package, dict) else None
        if not isinstance(source, dict):
            continue
        if name == "uv.lock":
            found += [(f"{package.get('name')}: {key} = {source[key]}", folder, source[key])
                      for key in ("directory", "editable", "path") if isinstance(source.get(key), str)]
        elif source.get("type") in ("directory", "file") and isinstance(source.get("url"), str):
            found.append((f"{package.get('name')}: {source['type']} = {source['url']}", folder, source["url"]))
    return found


def local_dependencies(files, read, family: str) -> list[dict]:
    """A `local_dependency_refused` gap for each local dependency of the `family` (`node` or `python`) that a file
    among `files` (`read(rel)`, its text) states with an absolute path or one outside the copy of the project
    (decision of the owner for T3.A): its folder's restore does not run (`refused`). A path inside the copy, a
    workspace or a member, is legitimate; a `git+` or URL address is no local dependency (its host is approved,
    T0.C)."""
    gaps = []
    for rel in files:
        base = posixpath.basename(rel)
        if family == "node" and base in ("package.json", "package-lock.json", "pnpm-lock.yaml"):
            reader = _node_local
        elif family == "python" and (base in PYTHON_LOCAL or (base.endswith((".txt", ".in")) and "requirements" in rel)):
            reader = _python_local
        else:
            continue
        try:
            text = read(rel)
        except OSError:
            continue
        gaps += [gap for entry, folder, path in reader(rel, text or "") for gap in [refusal(rel, entry, folder, path)]
                 if gap]
    return gaps


def refusal(rel: str, entry: str, folder: str, path: str) -> dict | None:
    """The `local_dependency_refused` gap of the local dependency `entry` the file `rel` states at `path`, written
    from `folder`, when the path is absolute or outside the copy (`_escapes`); None for one inside the copy."""
    why = _escapes(folder, path)
    return {"kind": "local_dependency_refused", "path": _folder(rel), "file": rel, "entry": entry,
            "detail": f"{rel}: {entry} is a local dependency at {why}: the restore of "
                      f"{_folder(rel)} does not run (only paths inside the copy are restored)"} if why else None


def refusals(record: dict) -> list[dict]:
    """The `local_dependency_refused` gaps of the pre-map `record` (`premap/renovate.py`: `yarn.lock` read with
    Yarn's parser), which `node_prepare` takes as `stated`."""
    return [gap for gap in record.get("gaps") or () if gap.get("kind") == "local_dependency_refused"]


def refused(folders, gaps: list[dict]) -> set[str]:
    """The restore folders among `folders` whose restore does not run: one holding the folder of a
    `local_dependency_refused` gap (`local_dependencies`), whose restore would install it."""
    held = [gap["path"] for gap in gaps if gap["kind"] == "local_dependency_refused"]
    return {folder for folder in folders if any(_inside(path, folder) for path in held)}


def python_restores(files, read) -> dict:
    """`{restores, gaps}`: per Python manager the folders its restore runs in (`restores`), less those `refused`
    for a local dependency outside the copy, with their `local_dependency_refused` gaps."""
    gaps = local_dependencies(files, read, "python")
    plan = {manager: folders for manager, folders in restores(files).items() if RESTORES[manager].get("family") == "python"}
    blocked = refused({f for folders in plan.values() for f in folders}, gaps)
    plan = {manager: kept for manager, folders in plan.items() for kept in [[f for f in folders if f not in blocked]]
            if kept}
    return {"restores": plan, "gaps": gaps}


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
