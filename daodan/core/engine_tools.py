"""What the pass installs on first use into the shared directory, outside every project: indexers
(`shared_engine_dir`), the Go and Rust toolchains, Maven artifacts, and the project's declared Python packages
(`python_environment`), from manifests only and without running the project's code; with the machine's platform
and free memory, which decide what runs."""
from __future__ import annotations

import hashlib
import http.client
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
    """Where Daodan installs a tool on first use, shared across projects."""
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
    """The machine's platform key in Daodan's pins: `win-x64`, `linux-arm64`, `osx-x64` and so on.

    From `sys.platform` and the process's architecture (`PROCESSOR_ARCHITECTURE` on Windows, `os.uname`
    elsewhere). Never from `platform`: it asks Windows through WMI and, when WMI fails, runs `ver` through the
    shell.
    """
    system = {"win32": "win", "linux": "linux", "darwin": "osx"}.get(sys.platform, sys.platform)
    machine = os.environ.get("PROCESSOR_ARCHITECTURE", "") if sys.platform == "win32" else os.uname().machine
    return f"{system}-{'arm64' if machine.lower() in ('arm64', 'aarch64') else 'x64'}"


def node_environment() -> dict:
    """Where npm and Node keep their caches for a process Daodan starts: in the shared directory."""
    cache = shared_cache_dir()
    return {"npm_config_cache": str(cache / "npm-cache"), "NODE_COMPILE_CACHE": str(cache / "node-compile-cache")}


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



RUST_VERSION = "1.99.1"


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
    """Fetch a file into the shared directory through a partial file of its own (another process may fetch the
    same file at once), verified, with three attempts."""
    target.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(3):
        descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".partial", dir=target.parent)
        os.close(descriptor)
        partial = Path(name)
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
        except (OSError, ValueError, http.client.HTTPException) as error:  # a cut-off body is not an OSError
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
                        [uv, "export", "--frozen", "--no-build", "--no-emit-project", "--no-emit-workspace",
                         "--all-groups", "--all-extras", "--no-hashes", "--no-header", "--format", "requirements-txt",
                         *uv_options()], cwd=copy, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                        timeout=600)
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


UV_VERSION = "0.11.28"  # the pre-map's pin (`premap/uv.py`), the containers' (`preparation.UV`)
# The release's own checksums, per platform key of `_platform()`: (asset, sha256).
UV_ASSETS = {
    "linux-x64": ("uv-x86_64-unknown-linux-gnu.tar.gz",
                  "e490a6464492183c5d4534a5527fb4440f7f2bb2f228162ad7e4afe076dc0224"),
    "linux-arm64": ("uv-aarch64-unknown-linux-gnu.tar.gz",
                    "03e9fe0a81b0718d0bc84625de3885df6cc3f89a8b6af6121d6b9f6113fb6533"),
    "win-x64": ("uv-x86_64-pc-windows-msvc.zip", "0a23463216d09c6a72ff80ef5dc5a795f07dc1575cb84d24596c2f124a441b7b"),
    "osx-arm64": ("uv-aarch64-apple-darwin.tar.gz", "33540eb7c883ab857eff79bd5ac2aa31fe27b595abecb4a9c003a2c998447232"),
    "osx-x64": ("uv-x86_64-apple-darwin.tar.gz", "2ad79983127ffca7d77b77ce6a24278d7e4f7b817a1acf72fea5f8124b4aac5e"),
}


def uv_binary(fetch: bool = True) -> Path | None:
    """uv at Daodan's pin, unpacked once into the shared directory and checked against the release's sha256: never
    the uv on the PATH, from a release Daodan cannot vouch for. With `fetch` False, None until it is installed.
    OSError when it cannot be had."""
    home = shared_engine_dir("uv") / UV_VERSION
    binary = home / executable_name("uv")
    if binary.is_file() or not fetch:
        return binary if binary.is_file() else None
    if _platform() not in UV_ASSETS:
        raise OSError(f"Daodan pins no uv {UV_VERSION} build for {_platform()}")
    asset, digest = UV_ASSETS[_platform()]
    print(f"installing uv {UV_VERSION} into {home} (first use)", flush=True)

    def fill(partial: Path) -> None:
        archive = download(f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/{asset}", partial / asset,
                           sha256=digest)
        unpack(archive, partial)
        archive.unlink()
        os.replace(next(partial.rglob(executable_name("uv"))), partial / executable_name("uv"))

    try:
        publish(home, fill, UV_VERSION)
    except (ValueError, StopIteration) as error:
        raise OSError(f"uv {UV_VERSION} was not installed: {error or 'its archive holds no uv'}") from error
    return binary


def publish(home: Path, fill, installed: str) -> None:
    """`fill` a folder of its own beside `home`, then publish it whole as `home`, marked `.installed`: an
    interrupted install leaves nothing usable, and of two at once (the server and the pass, two workers) the first
    published stays and the other's is dropped."""
    home.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(tempfile.mkdtemp(prefix=f".{home.name}.", suffix=".partial", dir=home.parent))
    try:
        fill(partial)
        (partial / ".installed").write_text(installed, encoding="utf-8")
        try:
            os.replace(partial, home)
        except OSError:
            if (home / ".installed").is_file():
                return  # another install published first
            shutil.rmtree(home, ignore_errors=True)  # an interrupted install's
            os.replace(partial, home)
    finally:
        shutil.rmtree(partial, ignore_errors=True)


def uv_options() -> list[str]:
    """What makes a uv run Daodan's own: no configuration file read (the project's, the user's: an index, a mirror
    for the interpreter it downloads, a setting for builds), its cache in Daodan's shared directory, where no wheel
    built elsewhere from a source distribution is found for `--only-binary`. It runs outside the project too."""
    return ["--no-config", "--cache-dir", str(shared_cache_dir() / "uv")]


def _inert(environment: Path) -> None:
    """What an interpreter of `environment` would run as it starts, by `site`'s rules, removed: a `.pth` file's
    import lines, `sitecustomize` and `usercustomize`, code of the packages it holds. uv starts that interpreter at
    each install and the analyzers to ask it its paths: none of the project's environment runs on the host. The
    folders a `.pth` file names stay."""
    for site in [*Path(environment).glob("lib/python*/site-packages"), *Path(environment).glob("Lib/site-packages")]:
        for path in site.iterdir():
            if path.name.split(".", 1)[0] in ("sitecustomize", "usercustomize"):
                shutil.rmtree(path) if path.is_dir() else path.unlink()
            elif path.suffix == ".pth" and path.is_file():
                try:
                    lines = path.read_bytes().decode("utf-8-sig").splitlines()
                except UnicodeDecodeError:  # `site` would read it in the locale's encoding: none of it is kept
                    path.unlink()
                    continue
                kept = [line for line in lines if not line.startswith(("import ", "import\t"))]
                if kept != lines:
                    path.write_text("".join(f"{line}\n" for line in kept), encoding="utf-8")


def python_environment(project_root: Path, names, python: str | None = None) -> Path | None:
    """The project's declared Python packages in an environment of the shared directory.

    Built once per set of manifests and interpreter, from wheels only, by Daodan's own
    uv (`uv_binary`, `uv_options`; OSError without it): no package build script and no
    project code runs, and nothing is written into the project; what its interpreter
    would run as it starts is removed (`_inert`). A requirement uv could not install,
    one without a wheel among them, is in its `daodan-environment.json` (`failed`), with
    uv's words.
    The interpreter is Daodan's, else `python`, the Python the project states, which
    uv resolves as `uv sync` does (an installed one that matches, else its download):
    a project that declares no package then gets the interpreter alone, and one uv
    cannot provide fails with uv's words. None when the project declares no package,
    the disk is short or no package could be installed.
    """
    project_root = Path(project_root).resolve()
    manifests = python_manifests(project_root, names)
    if not (manifests or python):
        return None
    uv = str(uv_binary())
    version = python or f"{sys.version_info.major}.{sys.version_info.minor}"
    digest = hashlib.sha256(f"{version}\0{_platform()}\0".encode("utf-8"))
    for name in manifests:
        digest.update(name.encode("utf-8") + b"\0" + (project_root / name).read_bytes() + b"\0")
    destination = shared_cache_dir() / "python" / digest.hexdigest()[:16]
    marker = destination / "daodan-environment.json"
    if marker.is_file():
        _inert(destination)  # one built before it was made inert
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(destination.parent).free
    if free < ENVIRONMENT_MIN_FREE:
        print(f"the project's Python packages were not installed: {free / 2**30:.1f} GB free in "
              f"{destination.parent}, at least {ENVIRONMENT_MIN_FREE / 2**30:.0f} GB are needed", flush=True)
        return None
    requirements = _declared_requirements(project_root, manifests, uv) if manifests else []
    if not (requirements or python):
        return None
    print(f"installing the project's Python packages into {destination} (first use)", flush=True)
    shutil.rmtree(destination, ignore_errors=True)

    def run(*arguments, timeout=1800):
        return subprocess.run([uv, *arguments, *uv_options()], cwd=destination.parent, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=timeout)

    failed: list[dict] = []

    def install(*arguments, timeout=1800) -> bool:
        """Wheels only (`--only-binary :all:`): uv builds no source distribution, so none of a package's code runs;
        a requirement it cannot install is recorded with its words."""
        _inert(destination)  # uv starts the environment's interpreter first (`-I`: with `site`)
        done = run("pip", "install", "--python", str(destination), "--only-binary", ":all:", *arguments,
                   timeout=timeout)
        if done.returncode != 0 and arguments[0] != "-r":
            failed.append({"requirement": arguments[0], "cause": " ".join(done.stderr.split())[-400:]})
        return done.returncode == 0

    made = run("venv", str(destination), "--python", version)
    if made.returncode != 0:
        if python:
            raise subprocess.SubprocessError(f"uv could not provide Python {python}: {made.stderr.strip()[-400:]}")
        return None
    installed = len(requirements)
    if requirements:
        listed = destination / "daodan-requirements.txt"
        listed.write_text("\n".join(requirements) + "\n", encoding="utf-8")
        if not install("-r", str(listed)):
            # One package without a wheel must not cost the others.
            installed = sum(1 for requirement in requirements if install(requirement, timeout=600))
    _inert(destination)
    if installed == 0 and not python:
        shutil.rmtree(destination, ignore_errors=True)
        return None
    marker.write_text(json.dumps({"manifests": manifests, "requirements": len(requirements), "installed": installed,
                                  "python": version, "failed": failed}) + "\n", encoding="utf-8")
    print(f"installed {installed} of {len(requirements)} declared Python packages", flush=True)
    return destination
