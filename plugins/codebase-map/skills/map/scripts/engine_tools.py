"""What the pass installs on first use into the shared directory, outside every project: language
servers and indexers (`shared_engine_dir`), the Go and Rust toolchains, Maven artifacts, and the project's declared
JavaScript and Python packages (`npm_modules`, `python_environment`), from manifests only and without running the
project's code; with the machine's platform and free memory, which decide what runs."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath

from embedding_worker import shared_cache_dir


def shared_engine_dir(name: str) -> Path:
    """Where Daodan installs a language server on first use, shared across projects."""
    return shared_cache_dir() / "engines" / name


def free_memory() -> int | None:
    """Bytes of memory available to a new process, or None when the system does not say (macOS).

    On Windows the smaller of free physical memory and free commit: a process gets only what the page file
    can still back, which can be far less than the free physical memory. On Linux `MemAvailable`.
    """
    if os.name == "nt":
        import ctypes

        class Status(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                        ("total", ctypes.c_ulonglong), ("available", ctypes.c_ulonglong),
                        ("page_total", ctypes.c_ulonglong), ("page_free", ctypes.c_ulonglong),
                        ("virtual_total", ctypes.c_ulonglong), ("virtual_free", ctypes.c_ulonglong),
                        ("extended", ctypes.c_ulonglong)]

        status = Status()
        status.length = ctypes.sizeof(Status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None
        return min(status.available, status.page_free)
    try:
        with open("/proc/meminfo", encoding="ascii") as meminfo:
            for row in meminfo:
                if row.startswith("MemAvailable:"):
                    return int(row.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    return None


def _platform() -> str:
    """The platform key multilspy uses in its pins: `win-x64`, `linux-arm64`, `osx-x64` and so on.

    From `sys.platform` and the process's architecture (`PROCESSOR_ARCHITECTURE` on Windows, `os.uname`
    elsewhere). Never from `platform`: it asks Windows through WMI and, when WMI fails, runs `ver` through the
    shell.
    """
    system = {"win32": "win", "linux": "linux", "darwin": "osx"}.get(sys.platform, sys.platform)
    machine = os.environ.get("PROCESSOR_ARCHITECTURE", "") if sys.platform == "win32" else os.uname().machine
    return f"{system}-{'arm64' if machine.lower() in ('arm64', 'aarch64') else 'x64'}"


def npm_manifests(root: Path) -> list[Path]:
    """The files that decide a JavaScript project's packages: root manifest, lockfile, workspace manifests."""
    root = Path(root)
    package = root / "package.json"
    if not package.is_file():
        return []
    found = [package, *[root / name for name in ("package-lock.json", "npm-shrinkwrap.json")
                        if (root / name).is_file()]]
    try:
        workspaces = json.loads(package.read_text(encoding="utf-8")).get("workspaces") or []
    except (OSError, ValueError):
        workspaces = []
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages") or []
    for pattern in workspaces if isinstance(workspaces, list) else []:
        for directory in root.glob(str(pattern)):
            manifest = directory / "package.json"
            if manifest.is_file() and "node_modules" not in manifest.relative_to(root).parts:
                found.append(manifest)
    return sorted(set(found))


def npm_key(root: Path) -> str | None:
    manifests = npm_manifests(root)
    if not manifests:
        return None
    # The second field changes when the installation itself changes (type packages added).
    digest = hashlib.sha256(b"npm-install\0types-1\0")
    for manifest in manifests:
        digest.update(manifest.relative_to(root).as_posix().encode("utf-8") + b"\0" + manifest.read_bytes() + b"\0")
    return digest.hexdigest()[:16]


def _declares_types(package: Path) -> bool:
    """Whether an installed package carries its own type declarations."""
    try:
        data = json.loads((package / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if data.get("types") or data.get("typings") or "types" in json.dumps(data.get("exports") or {}):
        return True
    return (package / "index.d.ts").is_file()


def missing_type_packages(directory: Path) -> list[str]:
    """`@types/...` names for the declared packages installed without their own types.

    A JavaScript project rarely declares them, and without them the engine cannot
    tell what `res.send` or `request(app).get` is: the call stays unanswered
    instead of external.
    """
    try:
        data = json.loads((directory / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    declared = set()
    for table in ("dependencies", "devDependencies", "optionalDependencies"):
        if isinstance(data.get(table), dict):
            declared |= set(data[table])
    wanted = []
    for name in sorted(declared):
        if name.startswith("@types/"):
            continue
        typed = "@types/" + name.lstrip("@").replace("/", "__")
        installed = directory / "node_modules" / name
        if typed in declared or not installed.is_dir() or _declares_types(installed):
            continue
        if not (directory / "node_modules" / typed).is_dir():
            wanted.append(typed)
    return wanted


def _install_type_packages(npm: str, directory: Path) -> int:
    """Install the missing type packages beside the others, without scripts; one that does
    not exist must not cost the rest. Returns how many were installed."""
    wanted = missing_type_packages(directory)
    if not wanted:
        return 0
    base = [npm, "install", "--no-save", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error",
            "--package-lock=false"]

    def run(names, timeout):
        return subprocess.run([*base, *names], cwd=directory, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, timeout=timeout, shell=os.name == "nt",
                              env={**os.environ, **node_environment()}).returncode == 0

    if run(wanted, 900):
        return len(wanted)
    return sum(1 for name in wanted if run([name], 300))


def _without_local_packages(manifest: Path) -> str | None:
    """A package.json without the packages it takes from a local path, or None when it has none.

    `file:`, `link:`, `workspace:` and bare paths point at the project's own code, which
    the manifest-only copy does not hold: npm would fail on every other package too.
    """
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    dropped = False
    for table in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        packages = data.get(table)
        if not isinstance(packages, dict):
            continue
        for name, spec in list(packages.items()):
            if isinstance(spec, str) and spec.startswith(("file:", "link:", "workspace:", ".", "/", "~/")):
                del packages[name]
                dropped = True
    return json.dumps(data, indent=2) + "\n" if dropped else None


def package_directories(root: Path, limit: int = 8) -> list[Path]:
    """Directories of the project with their own package.json and no installed packages, nearest first.

    The members of a workspace are served by its root, and a directory under an
    installed `node_modules` by that installation.
    """
    root = Path(root).resolve()
    served = {manifest.parent.resolve() for manifest in npm_manifests(root)} - {root}
    found = []
    for current, directories, files in os.walk(root):
        here = Path(current)
        directories[:] = sorted(name for name in directories if name != "node_modules" and not name.startswith("."))
        if "package.json" in files and here.resolve() not in served and not (here / "node_modules").is_dir():
            found.append(here)
            served |= {manifest.parent.resolve() for manifest in npm_manifests(here)}
    return sorted(found, key=lambda path: (len(path.relative_to(root).parts), path.as_posix()))[:limit]


def node_environment() -> dict:
    """Where npm and Node keep their caches for a process Daodan starts: in the shared directory."""
    cache = shared_cache_dir()
    return {"npm_config_cache": str(cache / "npm-cache"), "NODE_COMPILE_CACHE": str(cache / "node-compile-cache")}


def npm_modules(root: Path) -> Path | None:
    """The project's packages installed once into the shared directory, without running any package script.

    Only the manifests are copied there, so npm never sees the project's code; the
    lockfile is honoured when there is one. Every project with the same manifests
    shares the installation, and npm's own cache spares repeated downloads. None
    when the project has no package.json, npm is missing or the install fails.
    """
    root = Path(root).resolve()
    key, npm = npm_key(root), shutil.which("npm")
    if key is None or npm is None:
        return None
    destination = shared_cache_dir() / "npm" / key
    if (destination / "daodan-modules.json").is_file():
        return destination / "node_modules"
    print(f"installing the project's JavaScript packages into {destination} (first use)", flush=True)
    partial = destination.with_name(f".{key}.partial")
    shutil.rmtree(partial, ignore_errors=True)
    manifests = npm_manifests(root)
    local = False
    for manifest in manifests:
        target = partial / manifest.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        text = _without_local_packages(manifest) if manifest.name == "package.json" else None
        if text is None:
            shutil.copyfile(manifest, target)
        else:
            target.write_text(text, encoding="utf-8")
            local = True
    # A lockfile that still names the local packages cannot be honoured to the letter.
    locked = not local and any(manifest.name in ("package-lock.json", "npm-shrinkwrap.json") for manifest in manifests)
    command = [npm, "ci" if locked else "install", "--ignore-scripts", "--no-audit", "--no-fund",
               "--loglevel=error", *([] if locked else ["--package-lock=false"])]
    completed = subprocess.run(command, cwd=partial, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                               timeout=1800, shell=os.name == "nt", env={**os.environ, **node_environment()})
    if completed.returncode != 0 and locked:
        # A lockfile out of step with its manifest still leaves the manifest to install from.
        command = [npm, "install", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error"]
        completed = subprocess.run(command, cwd=partial, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                   timeout=1800, shell=os.name == "nt", env={**os.environ, **node_environment()})
    if completed.returncode != 0 or not (partial / "node_modules").is_dir():
        print(f"the project's JavaScript packages were not installed: {(completed.stderr or '')[-300:]}", flush=True)
        shutil.rmtree(partial, ignore_errors=True)
        return None
    try:
        typed = _install_type_packages(npm, partial)
    except (OSError, subprocess.SubprocessError):
        typed = 0
    if typed:
        print(f"installed {typed} type packages for declared JavaScript packages without their own", flush=True)
    (partial / "daodan-modules.json").write_text(json.dumps({"manifests": [m.relative_to(root).as_posix()
                                                                           for m in manifests],
                                                             "type_packages": typed}), encoding="utf-8")
    shutil.rmtree(destination, ignore_errors=True)
    os.replace(partial, destination)
    return destination / "node_modules"


RUST_ANALYZER_RELEASE = "2026-11-09"


# The release's own checksums, per platform key of `_platform()`: (asset, sha256).
RUST_ANALYZER_ASSETS = {
    "win-x64": ("x86_64-pc-windows-msvc.zip", "973ab11e84955a7f8e3cf01ccd98a33f3ecbd6d4a14bf59bb164aa9e831c6fef"),
    "win-arm64": ("aarch64-pc-windows-msvc.zip", "ca0770b76d3881642221d0437f7535e324f22a9499bcd00bbebeb0228617249e"),
    "linux-x64": ("x86_64-unknown-linux-gnu.gz", "8c039b25cb338b3970c731646677a4c9d4e9dd7a92c9ab9ae459c71467fbf4a9"),
    "linux-arm64": ("aarch64-unknown-linux-gnu.gz", "813ca3cec78ac6dab99c7bc9d51e63578f6d401b994ecf29cc0dcad86f9b2cd4"),
    "osx-x64": ("x86_64-apple-darwin.gz", "abf410a54e33e9f8b2d37f76dde8884db86a030d6a9cc70c0e3f87a77c084c5c"),
    "osx-arm64": ("aarch64-apple-darwin.gz", "e43a65008f8f4291320f33c0545dd577ad7623a7407b584a27155833d3722dfb"),
}


GO_VERSION = "1.27.3"


GO_ASSETS = {
    "win-x64": ("go1.27.3.windows-amd64.zip", "f26081f438319757f8a1b46d7d0b2c5ec7583d4038e485e0aa725cfde7885fff"),
    "win-arm64": ("go1.27.3.windows-arm64.zip", "c507872ff21f8a7cd3c1c217b059c6f7271a4a9d8e692810ef9dd3e1f601197c"),
    "linux-x64": ("go1.27.3.linux-amd64.tar.gz", "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40"),
    "linux-arm64": ("go1.27.3.linux-arm64.tar.gz", "a06e99309dbcbdca1a8ccd2282c3ee146e55930886e26b4f1193269587165f49"),
    "osx-x64": ("go1.27.3.darwin-amd64.tar.gz", "b6f8e931e4ab497fcde6da8ae4499a58f9d258e55c8a80824a516eae5950a750"),
    "osx-arm64": ("go1.27.3.darwin-arm64.tar.gz", "dd3908cf20959d798c1e06ebe5b72213f0505ce01373b40ce3110975a6cd99c2"),
}




def unpack(archive: Path, destination: Path) -> None:
    """Extract a zip or a gzip tarball into `destination`."""
    if archive.name.endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(destination)
    else:
        import tarfile
        with tarfile.open(archive) as bundle:
            bundle.extractall(destination, filter="data")


def executable_name(name: str) -> str:
    return name + (".exe" if os.name == "nt" else "")


def go_jobs() -> str:
    """How many compilers `go install` runs at once: one per CPU, at most 4, since each holds its own memory."""
    return str(min(os.cpu_count() or 1, 4))


def user_config(folder: Path) -> dict:
    """The variable a tool's user configuration folder comes from (Go's `os.UserConfigDir`), set to `folder`."""
    if os.name == "nt":
        return {"APPDATA": str(folder)}
    if sys.platform == "darwin":
        return {"HOME": str(folder)}  # $HOME/Library/Application Support
    return {"XDG_CONFIG_HOME": str(folder)}


def go_toolchain() -> Path:
    """The Go release Daodan pins, unpacked once into the shared directory: its GOROOT."""
    home = shared_engine_dir("go") / GO_VERSION
    root = home / "go"
    if (root / "bin" / executable_name("go")).is_file():
        return root
    asset, digest = GO_ASSETS[_platform()]
    print(f"installing Go {GO_VERSION} into {home} (first use)", flush=True)
    partial = home.with_name(f".{GO_VERSION}.partial")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    archive = download(f"https://go.dev/dl/{asset}", partial / asset, sha256=digest)
    unpack(archive, partial)
    archive.unlink()
    shutil.rmtree(home, ignore_errors=True)
    os.replace(partial, home)
    return root



def go_environment() -> dict:
    """Go's variables, every folder Go writes in the shared directory, its telemetry turned off there."""
    root = go_toolchain()
    cache = shared_cache_dir() / "go"
    environment = {"GOROOT": str(root), "GOPATH": str(cache / "path"), "GOCACHE": str(cache / "build"),
                   "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=readonly", **user_config(cache / "config"),
                   "PATH": str(root / "bin") + os.pathsep + os.environ.get("PATH", "")}
    # Go reads its telemetry mode from its configuration folder only: GOTELEMETRY is read-only.
    off = cache / "config" / ".daodan-telemetry-off"
    if not off.is_file():
        done = subprocess.run([str(root / "bin" / executable_name("go")), "telemetry", "off"],
                              env={**os.environ, **environment}, stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=120)
        if done.returncode == 0:
            off.parent.mkdir(parents=True, exist_ok=True)
            off.touch()
    return environment

RUST_VERSION = "1.99.1"


RUST_TARGETS = {"win-x64": "x86_64-pc-windows-msvc", "win-arm64": "aarch64-pc-windows-msvc",
                "linux-x64": "x86_64-unknown-linux-gnu", "linux-arm64": "aarch64-unknown-linux-gnu",
                "osx-x64": "x86_64-apple-darwin", "osx-arm64": "aarch64-apple-darwin"}


def rust_toolchain() -> Path | None:
    """The directory whose `bin` holds cargo and rustc and whose sysroot holds the standard library's sources.

    The toolchain on PATH when it is complete; otherwise cargo, rustc and rust-src
    at the pinned release, downloaded from static.rust-lang.org into the shared
    directory and checked against the sha256 of the release manifest. Without the
    standard library's sources every call into `std` stays unresolved (semver:
    88.8% instead of 97.7%). None when the download fails.
    """
    cargo, rustc = shutil.which("cargo"), shutil.which("rustc")
    if cargo and rustc:
        try:
            sysroot = subprocess.run([rustc, "--print", "sysroot"], capture_output=True, text=True, timeout=60,
                                     stdin=subprocess.DEVNULL).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            sysroot = ""
        if sysroot and (Path(sysroot) / "lib" / "rustlib" / "src" / "rust" / "library").is_dir():
            return Path(cargo).parent.parent
    home = shared_engine_dir("rust") / RUST_VERSION
    if (home / ".installed").is_file():
        return home
    import tomllib
    import tarfile
    print(f"installing Rust {RUST_VERSION} (cargo, rustc, rust-src) into {home} (first use)", flush=True)
    partial = home.with_name(f".{RUST_VERSION}.partial")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    try:
        with open_url(f"https://static.rust-lang.org/dist/channel-rust-{RUST_VERSION}.toml",
                      timeout=120) as response:
            packages = tomllib.loads(response.read().decode("utf-8"))["pkg"]
        target = RUST_TARGETS[_platform()]
        for component in ("rustc", "cargo", "rust-src"):
            entry = packages[component]["target"]
            entry = entry.get(target) or entry["*"]
            archive = download(entry["xz_url"], partial / f"{component}.tar.xz", sha256=entry["xz_hash"])
            unpacked = partial / f"unpack-{component}"
            with tarfile.open(archive, "r:xz") as bundle:
                bundle.extractall(unpacked, filter="data")
            archive.unlink()
            top = next(child for child in unpacked.iterdir() if child.is_dir())
            shutil.copytree(top / component, partial, dirs_exist_ok=True)
            shutil.rmtree(unpacked, ignore_errors=True)
        (partial / ".installed").write_text(RUST_VERSION, encoding="utf-8")
        shutil.rmtree(home, ignore_errors=True)
        os.replace(partial, home)
    except Exception as error:
        print(f"the Rust toolchain was not installed: {type(error).__name__}: {error}", flush=True)
        shutil.rmtree(partial, ignore_errors=True)
        return None
    return home


# The Kotlin Analysis API in standalone mode with the platform it runs on, as KSP publishes it on
# Maven Central, and the compiler that builds the resolver against it once.
KOTLIN_ANALYSIS = "com.google.devtools.ksp:symbol-processing-aa:2.3.13"


KOTLIN_RUNTIME = ("com.google.devtools.ksp:symbol-processing-common-deps:2.3.13",
                  "org.jetbrains.kotlin:kotlin-stdlib:2.4.21",
                  "org.jetbrains.kotlinx:kotlinx-coroutines-core-jvm:1.10.2")


KOTLIN_COMPILER = ("org.jetbrains.kotlin:kotlin-compiler-embeddable:2.4.21",
                   "org.jetbrains.kotlin:kotlin-build-tools-api:2.4.21",
                   "org.jetbrains.kotlin:kotlin-stdlib:2.4.21",
                   "org.jetbrains.kotlin:kotlin-script-runtime:2.4.21",
                   "org.jetbrains.kotlin:kotlin-reflect:1.6.10",
                   "org.jetbrains.kotlin:kotlin-daemon-embeddable:2.4.21",
                   "org.jetbrains.kotlinx:kotlinx-coroutines-core-jvm:1.8.0",
                   "org.jetbrains:annotations:13.0")


KOTLIN_OPT_INS = ("KaExperimentalApi", "KaPlatformInterface", "KaImplementationDetail", "KaIdeApi")


MAVEN_CENTRAL = "https://repo1.maven.org/maven2"


def maven_central_dir() -> Path:
    """The shared Maven-layout store: Coursier's cache of Maven Central, also where Daodan puts its own jars."""
    return shared_cache_dir() / "coursier" / "https" / "repo1.maven.org" / "maven2"


USER_AGENT = "daodan"  # Python's default agent is refused by some hosts: the Temurin API answers 403


def open_url(url: str, timeout: float):
    """A URL opened with Daodan's own agent name."""
    import urllib.request
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout)


def download(url: str, target: Path, *, sha256: str | None = None, sha1_url: str | None = None) -> Path:
    """Fetch a file into the shared directory through a partial file, verified, with three attempts."""
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".partial")
    last = None
    for attempt in range(3):
        try:
            expected = sha256
            if sha1_url:
                with open_url(sha1_url, timeout=60) as response:
                    expected = response.read().decode("ascii", "replace").split()[0].lower()
            digest = hashlib.sha1() if sha1_url else hashlib.sha256()
            with open_url(url, timeout=600) as response, partial.open("wb") as handle:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    digest.update(chunk)
                    handle.write(chunk)
            if expected and digest.hexdigest() != expected:
                raise ValueError(f"checksum mismatch for {url}")
            os.replace(partial, target)
            return target
        except (OSError, ValueError) as error:
            last = error
            partial.unlink(missing_ok=True)
            time.sleep(2 * (attempt + 1))
    raise last


def maven_artifact(coordinate: str) -> Path:
    """A Maven artifact's jar: the local Maven repository first, then the shared store, else Maven Central."""
    group, artifact, version = coordinate.split(":")
    relative = Path(*group.split("."), artifact, version, f"{artifact}-{version}.jar")
    for repository in (Path.home() / ".m2" / "repository", maven_central_dir()):
        if (repository / relative).is_file():
            return repository / relative
    target = maven_central_dir() / relative
    print(f"downloading {coordinate} into {target.parent}", flush=True)
    url = f"{MAVEN_CENTRAL}/{relative.as_posix()}"
    return download(url, target, sha1_url=url + ".sha1")


ENVIRONMENT_MIN_FREE = 3 * 2**30


_REQUIREMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[^\]]*\])?\s*([<>=!~].*)?$")


def python_manifests(project_root: Path, names) -> list[str]:
    """The snapshot's files that declare Python packages: lockfiles, pyproject and requirements files."""
    found = []
    for name in names:
        base = PurePosixPath(name).name
        if base in ("pyproject.toml", "uv.lock") or (base.startswith("requirements") and base.endswith(".txt")):
            if (project_root / name).is_file():
                found.append(name)
    return sorted(found)


def _declared_requirements(project_root: Path, manifests: list[str], uv: str) -> list[str]:
    """Requirement lines the manifests declare, read without running anything of the project.

    A lockfile is exported from a copy of its two files; a pyproject without one gives
    its dependency tables; a requirements file gives its package lines. Editable
    installs, local paths, URLs and includes are left out: they are project code or
    need it.
    """
    import tomllib
    lines: list[str] = []
    for name in manifests:
        path, base = project_root / name, PurePosixPath(name).name
        if base == "uv.lock":
            continue
        if base == "pyproject.toml":
            exported = None
            if (path.parent / "uv.lock").is_file():
                with tempfile.TemporaryDirectory(prefix="daodan-lock-") as copy:
                    for item in ("pyproject.toml", "uv.lock"):
                        shutil.copyfile(path.parent / item, Path(copy) / item)
                    done = subprocess.run(
                        [uv, "export", "--frozen", "--no-emit-project", "--no-emit-workspace", "--all-groups",
                         "--all-extras", "--no-hashes", "--no-header", "--format", "requirements-txt"],
                        cwd=copy, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)
                    exported = done.stdout.splitlines() if done.returncode == 0 else None
            if exported is None:
                try:
                    data = tomllib.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    data = {}
                project = data.get("project") or {}
                exported = list(project.get("dependencies") or [])
                for table in (project.get("optional-dependencies") or {}, data.get("dependency-groups") or {}):
                    for values in table.values():
                        exported += [value for value in values if isinstance(value, str)]
                poetry = ((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}
                exported += [package for package in poetry if package.lower() != "python"]
            lines += exported
        else:
            try:
                lines += path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                pass
    kept = []
    for line in lines:
        line = line.split(" #")[0].strip()
        if line and not line.startswith(("#", "-", ".", "/")) and "://" not in line and " @ " not in line \
                and _REQUIREMENT.match(line.split(";")[0].strip()):
            kept.append(line)
    return sorted(set(kept))


def python_environment(project_root: Path, names) -> Path | None:
    """The project's declared Python packages in an environment of the shared directory.

    Built once per set of manifests and interpreter, from wheels only: no package
    build script and no project code runs, and nothing is written into the project.
    None when the project declares no package, uv is missing, the disk is short or
    no package could be installed.
    """
    project_root = Path(project_root).resolve()
    manifests = python_manifests(project_root, names)
    uv = shutil.which("uv")
    if not manifests or uv is None:
        return None
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    digest = hashlib.sha256(f"{version}\0{_platform()}\0".encode("utf-8"))
    for name in manifests:
        digest.update(name.encode("utf-8") + b"\0" + (project_root / name).read_bytes() + b"\0")
    destination = shared_cache_dir() / "python" / digest.hexdigest()[:16]
    marker = destination / "daodan-environment.json"
    if marker.is_file():
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(destination.parent).free
    if free < ENVIRONMENT_MIN_FREE:
        print(f"the project's Python packages were not installed: {free / 2**30:.1f} GB free in "
              f"{destination.parent}, at least {ENVIRONMENT_MIN_FREE / 2**30:.0f} GB are needed", flush=True)
        return None
    requirements = _declared_requirements(project_root, manifests, uv)
    if not requirements:
        return None
    print(f"installing the project's Python packages into {destination} (first use)", flush=True)
    shutil.rmtree(destination, ignore_errors=True)

    def run(*arguments, timeout=1800):
        return subprocess.run([uv, *arguments], stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              timeout=timeout)

    if run("venv", str(destination), "--python", version).returncode != 0:
        return None
    install = ("pip", "install", "--python", str(destination), "--only-binary", ":all:")
    listed = destination / "daodan-requirements.txt"
    listed.write_text("\n".join(requirements) + "\n", encoding="utf-8")
    installed = len(requirements)
    if run(*install, "-r", str(listed)).returncode != 0:
        # One package without a wheel must not cost the others.
        installed = sum(1 for requirement in requirements if run(*install, requirement, timeout=600).returncode == 0)
    if installed == 0:
        shutil.rmtree(destination, ignore_errors=True)
        return None
    marker.write_text(json.dumps({"manifests": manifests, "requirements": len(requirements), "installed": installed,
                                  "python": version}) + "\n", encoding="utf-8")
    print(f"installed {installed} of {len(requirements)} declared Python packages", flush=True)
    return destination


def fetch_rust_analyzer(partial: Path) -> None:
    """The rust-analyzer release Daodan pins, for this platform, into `partial`, verified."""
    asset, digest = RUST_ANALYZER_ASSETS[_platform()]
    archive = download("https://github.com/rust-lang/rust-analyzer/releases/download/"
                       f"{RUST_ANALYZER_RELEASE}/rust-analyzer-{asset}", partial / asset, sha256=digest)
    binary = partial / executable_name("rust-analyzer")
    if archive.suffix == ".zip":
        unpack(archive, partial)
    else:
        import gzip
        with gzip.open(archive) as source, binary.open("wb") as target:
            shutil.copyfileobj(source, target)
        binary.chmod(0o755)
    archive.unlink()
