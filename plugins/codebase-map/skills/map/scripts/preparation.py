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
NEEDS = {
    "vcpkg": {  # the tool, Microsoft's build; the registry is cloned at its default branch, blobs on demand
        "files": [("https://github.com/microsoft/vcpkg-tool/releases/download/2026-10-29/vcpkg-glibc",
                   "8b10d43c1392a2d51622b1e439cb952289dcf56cbb595eb935847e79fe00d303", "vcpkg")],
        "setup": [f"git clone -q --filter=blob:none https://github.com/microsoft/vcpkg {T}/vcpkg"
                  f" && cp {IN}/vcpkg {T}/vcpkg/vcpkg && chmod 755 {T}/vcpkg/vcpkg && touch {T}/vcpkg/.vcpkg-root"
                  f" && ln -sf {T}/vcpkg/vcpkg {T}/bin/vcpkg"],
        "registries": True, "hosts": GITHUB, "version": "2026-10-29"},  # ports: sources where portfiles say
    "conan": {"files": [UV], "setup": [  # the image's Python has no pip: uv makes the environment
        f"mkdir -p {T}/uvc && tar -xzf {IN}/uv.tar.gz -C {T}/uvc && u=$(echo {T}/uvc/*/uv)"
        f" && $u venv -q --python /usr/bin/python3 {T}/conan && $u pip install -q --python {T}/conan conan==2.34.0"
        f" && ln -sf {T}/conan/bin/conan {T}/bin/conan"],
              "registries": True, "hosts": ("center2.conan.io",), "version": "2.34.0"},
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
    lines = [f"chmod 755 {IN}/mise"] + [
        f"{mise} install {tool}@{version} >&2 || echo 'DAODAN-MISSING {tool}@{version}' >&2" for tool, version in
        sorted(wanted.items())]
    lines.append(f"for d in {T}/mise/installs/*/*/bin; do [ -d \"$d\" ] && ln -sf \"$d\"/* {T}/bin/; done; true")
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
RESTORES = {  # manager -> the files that mark where its build starts, its own restore, what in its output is an
    # error (`error`) or a failure it reports with success (`failed`), the hosts beside the registries
    "gradle": {"marks": ("settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts"),
               "line": "gradle --no-daemon --console=plain -q dependencies",  # every project's configurations
               "failed": " FAILED$", "error": " FAILED$|What went wrong|Could not ", "before": JAVA_PROXY,
               "hosts": ("plugins.gradle.org", "plugins-artifacts.gradle.org", "services.gradle.org",
                         "dl.google.com", "maven.google.com")},
    "maven": {"marks": ("pom.xml",), "error": r"^\[ERROR\]", "before": JAVA_PROXY, "hosts": (),
              "line": "mvn -B -q org.apache.maven.plugins:maven-dependency-plugin:3.8.1:go-offline"},
}
LOG = "/tmp/daodan-restore.log"


def _folder(rel: str) -> str:
    return posixpath.dirname(rel) or "."


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def restores(files) -> dict[str, list[str]]:
    """Per manager, the folders where its restore runs: each folder with one of its marks that no other such
    folder holds (a Gradle build or a Maven reactor restores its projects from its root)."""
    out = {}
    for manager, spec in RESTORES.items():
        marked = sorted({_folder(rel) for rel in files if posixpath.basename(rel) in spec["marks"]},
                        key=lambda f: (f.count("/"), f))
        tops = [f for f in marked if not any(o != f and _inside(f, o) for o in marked)]
        if tops:
            out[manager] = tops
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
