#!/usr/bin/env python3
"""Run one command in a container over a disposable copy of the snapshot perimeter.

`run_in_container` is the one operation the dynamic step, the indexers that must build a
project and the dynamic reviews share (spec `docs/specs/2026-11-12-passo-dinamico.md`,
sections 2-4). Its guarantees:

1. The project's code runs only in the container, never on the host.
2. The container gets a copy of the files the snapshot perimeter walks and of those Git
   tracks, dot directories included, minus the files the snapshot never reads, as a tar
   through `cp -`; what Git ignores stays out, and a link Git tracks is that link only when
   it leads inside the project (`copy_perimeter`). The project is never mounted or written;
   declared outputs come back through `cp <container>:<path> -` into a folder outside it.
3. Execution runs with `--network none`; an optional preparation runs before it on an
   internal network whose only way out is a proxy that opens CONNECT to package registries
   on port 443. The preparation hands execution only two named volumes, the copy at `/work`
   and the state at `/daodan/state` (`HOME` is there unless the caller gives one), made for
   the run and removed by name; execution starts from the same image, so anything else the
   preparation wrote is gone, and the engine keeps no image or layer of the run. Each volume
   name is on record in Daodan's cache before the volume exists: the next run removes by name
   those a killed run left, never what a listing finds. Memory, swap, processes and time are
   limited, and no host variable reaches the container: only the `env` given, and the proxy
   variables set explicitly so the CLI's own proxy configuration adds none.
4. Every phase appends a record (command, image, engine, limits, copy digest, duration,
   outcome) to `container-runs.jsonl` in the output folder.
5. Without an engine that can run, the operation returns a declared gap with cause and
   remedy, and never falls back to the host.

The services a run's tests reach (`beside`: the dynamic step's, for every observer) run beside
the execution in the shape of a Kubernetes pod: a pod container with `--network none` holds one network namespace, each
service and the execution join it (`--network container:<pod>`), so the tests reach a
service at localhost, or at the name the pod's hosts give it, and nothing outside. Each
image is pulled by the engine before the preparation and runs by the digest its registry
gave; the execution starts once every service is ready (`start_services`).

The engine is reached only through a Docker-compatible command line (`create`, `cp`,
`start`, `rm`, `network`, `volume`), so it can be replaced. An engine the user already has
(`docker`, then `podman`) is used as found: no context, no configuration, no option of
Daodan's. Otherwise, on Windows, Daodan runs Kiri at a pinned version in a WSL 2
distribution of its own under the shared directory, never through Kiri's Windows app or
installer. Kiri engines in one WSL VM share its network namespace and each rebuilds and
removes the same nftables table, so Daodan's engine never starts beside another one.
`DAODAN_CONTAINER=off` leaves every run without an engine, a gap at once (the test suites).

Standard library only.
"""
from __future__ import annotations

import base64
import contextlib
import contextvars
import hashlib
import io
import json
import lzma
import os
import posixpath
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Callable, NamedTuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from embedding_worker import shared_cache_dir  # noqa: E402
from resolve_edges import _platform, _process_alive, download, free_memory, shared_engine_dir  # noqa: E402
from snapshot import is_forbidden  # noqa: E402
from tree_scope import Perimeter, git_executable  # noqa: E402

RECORD_NAME = "container-runs.jsonl"
WORKDIR = "/work"
STATE = "/daodan/state"  # with WORKDIR, what a preparation hands to execution
HOME = STATE + "/home"
VOLUME_NAME = re.compile(r"daodan-(?:work|state)-[0-9a-f]{12}")  # the only names a run removes
RESULTS = "/daodan/out/results"  # each command's code and streams, brought back by `run_commands`
NETWORKS = ("none", "registries")
OUTPUT_CAP = 2**30  # what the declared outputs of a run may hold together
RUN_FILES = (RECORD_NAME, "prepare.log", "execute.log")  # the run's own files, never an output's name
STREAM_SLACK = 2**26  # what tar headers and padding may add to the files' bytes, and far more
HEADER_CAP = 2**13  # a pax or GNU long-name header: a 4096-byte path and the times fit
# A member name no system may receive as written: a Windows device, a character Windows refuses or a control.
UNSAFE_PART = re.compile(r'(?is)(con|prn|aux|nul|com[0-9]|lpt[0-9])(\..*)?|.*[\x00-\x1f\\:*?"<>|].*|.*[. ]')
# The registries a preparation may reach, by host; everything else is refused by the proxy.
REGISTRIES = (
    "registry.npmjs.org", "registry.yarnpkg.com", "pypi.org", "files.pythonhosted.org",
    "repo1.maven.org", "repo.maven.apache.org", "plugins.gradle.org", "proxy.golang.org",
    "sum.golang.org", "index.crates.io", "static.crates.io", "api.nuget.org", "rubygems.org",
    "plugins-artifacts.gradle.org",
)
# Set on every container, empty when closed: the CLI adds its configured proxies only to unset names.
PROXY_VARIABLES = ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "FTP_PROXY", "ALL_PROXY",
                   "http_proxy", "https_proxy", "no_proxy", "ftp_proxy", "all_proxy")
PROXY_IMAGE = "python:3.13-alpine@sha256:9ef1a599f863231c3d91e941389bfdc4a2d6070557243d54df1a4e57015b960e"
PROXY_PORT = 3128
SERVICE_WAIT = 600  # the seconds a service may stay `starting`: GitHub's runner waits as long as its health check
SERVICE_STATE = "{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}"
BESIDE = contextvars.ContextVar("beside", default=None)  # `beside`'s services, variables and outcomes
HEALTH_EVERY = 30.0  # Docker's and Podman's `--health-interval` when a service declares none, in seconds
DURATION = re.compile(r"(\d+(?:\.\d*)?|\.\d+)(ns|us|µs|ms|s|m|h)")  # Go's `time.ParseDuration`, unsigned
UNITS = {"ns": 1e-9, "us": 1e-6, "µs": 1e-6, "ms": 1e-3, "s": 1.0, "m": 60.0, "h": 3600.0}
# Runs in its own container; argv: port, then the allowed hosts. Prints "ready <port>".
PROXY_SCRIPT = r'''
import select, socket, sys, threading
allowed = {host.lower() for host in sys.argv[2:]}
def relay(a, b):
    try:
        while True:
            ready, _, _ = select.select([a, b], [], [], 300)
            if not ready:
                return
            for side in ready:
                data = side.recv(65536)
                if not data:
                    return
                (b if side is a else a).sendall(data)
    except OSError:
        pass
    finally:
        a.close(); b.close()
def serve(client):
    head = b""
    while b"\r\n\r\n" not in head and len(head) < 8192:
        chunk = client.recv(4096)
        if not chunk:
            client.close(); return
        head += chunk
    words = head.split(b"\r\n", 1)[0].split()
    host, _, port = words[1].decode("latin-1").rpartition(":") if len(words) == 3 and words[0] == b"CONNECT" else ("", "", "")
    if host.lower() not in allowed or port != "443":
        print("refused", words[:2], flush=True)
        client.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n"); client.close(); return
    try:
        upstream = socket.create_connection((host, 443), timeout=30)
    except OSError:
        client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n"); client.close(); return
    client.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
    relay(client, upstream)
server = socket.create_server(("0.0.0.0", int(sys.argv[1])))
print("ready", server.getsockname()[1], flush=True)
while True:
    connection, _ = server.accept()
    threading.Thread(target=serve, args=(connection,), daemon=True).start()
'''

KIRI_VERSION = "0.2.0"
# The full package of the release, for the docker CLI that `kiri-lite` leaves out: (asset, sha256 of SHA256SUMS).
KIRI_PACKAGES = {
    "x64": ("kiri-0.2.0-1.x86_64.rpm", "3ad06c95fc7d5383fdea067599c594eae37d052828982ef8925973ed1248c067"),
    "arm64": ("kiri-0.2.0-1.aarch64.rpm", "868c837a321df294826833e4496fa00127355936dac7d45c4c3dc67777632f96"),
}
KIRI_URL = "https://github.com/libracoder/kiri/releases/download/v" + KIRI_VERSION + "/{asset}"
KIRI_FILES = {"usr/bin/kiri": "kiri", "usr/bin/kiri-init": "kiri-init", "usr/libexec/kiri/bin/docker": "docker"}
ALPINE = {
    "x64": ("https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/x86_64/alpine-minirootfs-3.24.4-x86_64.tar.gz",
            "cdaa38cb8de3537967ee5b6c9b6cd00cc962da2b018e6eea48696bb274923012"),
    "arm64": ("https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/aarch64/alpine-minirootfs-3.24.4-aarch64.tar.gz",
              "4b14c18f7e90a063b61462ea1462a5732c154bf6adad594974fe6487cd98a8de"),
}
DISTRO = "daodan-kiri"
SOCKET = "unix:///root/.kiri/run/docker.sock"
# No Windows drives and no Windows programs inside Daodan's distribution.
WSL_CONF = ("[boot]\nsystemd=false\n[automount]\nenabled=false\nmountFsTab=false\n"
            "[interop]\nenabled=false\nappendWindowsPath=false\n[user]\ndefault=root\n")
# The routers move off 80 and 443, which WSL would forward to the user's localhost.
DAEMON = ("grep -qs ' /sys/fs/cgroup cgroup2 ' /proc/mounts || { echo 'daodan: no cgroup v2 at /sys/fs/cgroup'; exit 3; }; "
          "export HOME=/root KIRI_HTTP_PORT=47080 KIRI_HTTPS_PORT=47443; exec /usr/bin/kiri daemon")
LXSS = r"Software\Microsoft\Windows\CurrentVersion\Lxss"
# Engine, Alpine base, the import's temporary rootfs and the distribution's disk before any image.
ENGINE_DISK_MIN = 2**30
WSL_ENABLE = "enable WSL 2 once, as administrator: wsl --install --no-distribution, then restart Windows"


class Gap(Exception):
    """No engine can run here: what is missing and what makes it possible."""

    def __init__(self, cause: str, remedy: str):
        super().__init__(cause)
        self.cause, self.remedy = cause, remedy


class Engine(NamedTuple):
    """A Docker-compatible command line: its name in records, the argv prefix, what ends it."""
    name: str
    argv: tuple[str, ...]
    stop: Callable[[], None] = lambda: None


def cli(engine: Engine, *args: str, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout: float | None = 300) -> subprocess.CompletedProcess:
    return subprocess.run([*engine.argv, *args], stdin=stdin or subprocess.DEVNULL, stdout=stdout,
                          stderr=stderr, timeout=timeout)


def checked(completed: subprocess.CompletedProcess, what: str) -> subprocess.CompletedProcess:
    if completed.returncode != 0:
        detail = (completed.stderr or b"").decode("utf-8", "replace").strip().splitlines()
        raise RuntimeError(f"{what} failed with code {completed.returncode}: {detail[-1] if detail else 'no message'}")
    return completed


def architecture() -> str:
    return _platform().split("-")[1]


def engine_home() -> Path:
    return shared_engine_dir("kiri") / KIRI_VERSION


def wsl_executable() -> str | None:
    found = shutil.which("wsl.exe")
    system = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "wsl.exe"
    return found or (str(system) if system.is_file() else None)


def wsl(*args: str, timeout: float = 120) -> subprocess.CompletedProcess:
    """wsl.exe with UTF-8 output; the caller checks the outcome."""
    return subprocess.run([wsl_executable() or "wsl.exe", *args], stdin=subprocess.DEVNULL, capture_output=True,
                          timeout=timeout, env={**os.environ, "WSL_UTF8": "1"})


def registered_distros() -> tuple[str | None, dict[str, str]]:
    """The default WSL distribution and every registered one with its folder, read from the registry."""
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, LXSS)
    except OSError:
        return None, {}
    names, folders = {}, {}
    with key:
        try:
            default = winreg.QueryValueEx(key, "DefaultDistribution")[0]
        except OSError:
            default = None
        index = 0
        while True:
            try:
                guid = winreg.EnumKey(key, index)
            except OSError:
                break
            index += 1
            with winreg.OpenKey(key, guid) as entry:
                try:
                    name = winreg.QueryValueEx(entry, "DistributionName")[0]
                    folder = winreg.QueryValueEx(entry, "BasePath")[0]
                except OSError:
                    continue
            names[guid], folders[name] = name, folder.removeprefix("\\\\?\\")
    return names.get(default), folders


def find_engine(*, own: bool = True) -> Engine:
    """The user's engine that answers (`docker`, then `podman`), else Daodan's own; a Gap when none can run, and
    at once with `DAODAN_CONTAINER=off` (the test suites, which start no container)."""
    if os.environ.get("DAODAN_CONTAINER") == "off":
        raise Gap("container engine off (DAODAN_CONTAINER=off)", "unset DAODAN_CONTAINER to run in a container")
    for name, probe in (("docker", ("version", "--format", "{{.Server.Os}}")),
                        ("podman", ("info", "--format", "{{.Host.Os}}"))):
        path = shutil.which(name)
        if not path:
            continue
        try:
            answer = subprocess.run([path, *probe], stdin=subprocess.DEVNULL, capture_output=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if answer.returncode == 0 and answer.stdout.decode("utf-8", "replace").strip() == "linux":
            return Engine(name, (path,))
    if not own:
        raise Gap("no container engine answers: neither docker nor podman", "start Docker or Podman")
    return own_engine()


def kiri_files(home: Path) -> Path:
    """Kiri's engine and the docker CLI of its release, verified and unpacked once into `home/bin`."""
    binaries = home / "bin"
    if all((binaries / name).is_file() for name in KIRI_FILES.values()):
        return binaries
    asset, digest = KIRI_PACKAGES[architecture()]
    partial = home / ".bin.partial"
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    print(f"installing Kiri {KIRI_VERSION} into {home} (first use)", flush=True)
    try:
        package = download(KIRI_URL.format(asset=asset), partial / asset, sha256=digest)
        rpm_extract(package, {source: partial / name for source, name in KIRI_FILES.items()})
        package.unlink()
    except (OSError, ValueError) as error:
        shutil.rmtree(partial, ignore_errors=True)
        raise Gap(f"Kiri {KIRI_VERSION} could not be downloaded: {error}",
                  "check the connection to github.com and retry") from error
    shutil.rmtree(binaries, ignore_errors=True)
    os.replace(partial, binaries)
    return binaries


def rpm_extract(package: Path, wanted: dict[str, Path]) -> None:
    """Copy named files out of an rpm whose payload is xz-compressed cpio, without installing it."""
    with package.open("rb") as raw:
        start = raw.read(1 << 20).find(b"\xfd7zXZ\x00")
        if start < 0:
            raise ValueError(f"{package.name} has no xz payload")
        raw.seek(start)
        with lzma.open(raw) as payload:
            remaining = dict(wanted)
            while remaining:
                header = payload.read(110)
                if header[:6] != b"070701":
                    raise ValueError(f"{package.name} payload is not cpio")
                size, name_size = int(header[54:62], 16), int(header[94:102], 16)
                name = payload.read(name_size)[:-1].decode("utf-8").removeprefix("./")
                payload.read(-(110 + name_size) % 4)
                if name == "TRAILER!!!":
                    break
                target = remaining.pop(name, None)
                with (target.open("wb") if target else open(os.devnull, "wb")) as out:
                    for left in range(size, 0, -(1 << 20)):
                        out.write(payload.read(min(left, 1 << 20)))
                payload.read(-size % 4)
    if remaining:
        raise ValueError(f"{package.name} lacks {', '.join(sorted(remaining))}")


def ensure_distro(home: Path) -> bool:
    """Daodan's distribution imported from Alpine plus Kiri; True when it must go after use."""
    default, folders = registered_distros()
    folder = home / "distro"
    current = folders.get(DISTRO)
    if current and os.path.normcase(os.path.abspath(current)) == os.path.normcase(str(folder)):
        return default in (None, DISTRO)
    if current:
        remove_distro()
    url, digest = ALPINE[architecture()]
    base = home / Path(url).name
    try:
        if not base.is_file():
            download(url, base, sha256=digest)
    except (OSError, ValueError) as error:
        raise Gap(f"the Alpine base could not be downloaded: {error}",
                  "check the connection to dl-cdn.alpinelinux.org and retry") from error
    rootfs = home / "rootfs.tar"
    binaries = kiri_files(home)
    owned = {"mode": 0o755, "uid": 0, "gid": 0, "uname": "root", "gname": "root", "deep": False}
    try:
        with tarfile.open(base, "r:gz") as alpine, tarfile.open(rootfs, "w") as out:
            for member in alpine:
                out.addfile(member, alpine.extractfile(member) if member.isfile() else None)
            conf = tarfile.TarInfo("etc/wsl.conf")
            conf.size, conf.mode = len(WSL_CONF), 0o644
            out.addfile(conf, io.BytesIO(WSL_CONF.encode("ascii")))
            for name in KIRI_FILES.values():
                out.add(binaries / name, arcname=f"usr/bin/{name}", filter=lambda info: info.replace(**owned))
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
        imported = wsl("--import", DISTRO, str(folder), str(rootfs), "--version", "2", timeout=300)
    finally:
        rootfs.unlink(missing_ok=True)
    if imported.returncode != 0:
        message = imported.stdout.decode("utf-8", "replace").strip() or imported.stderr.decode("utf-8", "replace").strip()
        raise Gap(f"WSL 2 could not import Daodan's distribution: {message}", WSL_ENABLE)
    return default is None


def remove_distro() -> None:
    wsl("--unregister", DISTRO)


def distro_argv() -> tuple[str, ...]:
    return (wsl_executable() or "wsl.exe", "-d", DISTRO, "--cd", "/", "--exec")


def own_engine() -> Engine:
    """Daodan's Kiri in its WSL distribution, its daemon started for one operation; a Gap where it cannot run."""
    if os.name != "nt":
        raise Gap("no container engine answers: neither docker nor podman",
                  "install Docker or Podman; Daodan brings its own engine only on Windows")
    if not wsl_executable():
        raise Gap("WSL is not installed", WSL_ENABLE)
    running = wsl("-l", "--running", "-q")
    others = [name for name in running.stdout.decode("utf-8", "replace").split() if "kiri" in name.lower() and name != DISTRO]
    if others:
        raise Gap(f"another Kiri engine runs in WSL ({', '.join(others)}); Daodan's would reset its network rules",
                  "open that Kiri so that `docker` answers, or stop it with wsl --terminate " + others[0])
    home = engine_home()
    home.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(home).free
    if free < ENGINE_DISK_MIN:
        raise Gap(f"{free / 2**20:.0f} MB free on the disk of {home}; Daodan's engine needs {ENGINE_DISK_MIN / 2**30:.0f} GB",
                  f"free space on {home.anchor or home}")
    lock = (home / "engine.lock").open("a+b")
    try:
        import msvcrt
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock.close()
        raise Gap("Daodan's container engine is busy with another operation", "wait until it ends and retry")
    try:
        remove_after = ensure_distro(home)
        log = (home / "daemon.log").open("wb")
        daemon = subprocess.Popen([*distro_argv(), "/bin/sh", "-c", DAEMON], stdin=subprocess.DEVNULL,
                                  stdout=log, stderr=subprocess.STDOUT, env={**os.environ, "WSL_UTF8": "1"})
    except BaseException:
        lock.close()
        raise

    def stop() -> None:
        wsl("--terminate", DISTRO)
        try:
            daemon.wait(timeout=30)
        except subprocess.TimeoutExpired:
            daemon.kill()
        log.close()
        if remove_after:
            remove_distro()
        lock.close()

    engine = Engine(f"daodan-kiri@{KIRI_VERSION}", (*distro_argv(), "/usr/bin/docker", "-H", SOCKET), stop)
    for _ in range(60):
        if daemon.poll() is not None:
            break
        answer = cli(engine, "version", "--format", "{{.Server.Os}}", timeout=30)
        if answer.returncode == 0 and answer.stdout.strip() == b"linux":
            return engine
        time.sleep(0.5)
    stop()
    tail = (home / "daemon.log").read_text(encoding="utf-8", errors="replace").strip().splitlines()[-1:] or ["no output"]
    if "cgroup v2" in tail[0]:
        raise Gap("Kiri needs cgroup v2 and this WSL kernel mounts another tree", "update WSL: wsl --update")
    raise Gap(f"Daodan's Kiri did not start: {tail[0]}", f"see {home / 'daemon.log'}")


def work_tree_git(project: Path) -> str | None:
    """Git for `project` when a `.git` is at or above it, None outside every work tree; a Gap when Git is not
    there or does not answer for it: without Git the copy would carry what Git ignores."""
    marker = next((folder / ".git" for folder in (project, *project.parents) if (folder / ".git").exists()), None)
    if marker is None:
        return None
    remedy = "install Git, or let it read this repository (git config --global --add safe.directory)"
    git = git_executable()
    if git is None:
        raise Gap(f"{marker} is there and no Git is on PATH: the copy cannot leave out what Git ignores", remedy)
    try:
        answer = subprocess.run([git, "-C", str(project), "rev-parse", "--is-inside-work-tree"],
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as error:
        raise Gap(f"Git did not answer for {project} ({error}): the copy cannot leave out what Git ignores",
                  remedy) from error
    if answer.returncode != 0:
        said = answer.stderr.decode("utf-8", "replace").strip()[-300:]
        raise Gap(f"Git refuses {project} ({said}): the copy cannot leave out what Git ignores", remedy)
    return git


LINK = 0o120000  # the mode Git records for a symbolic link


def tracked(project: Path) -> dict[str, tuple[int, str]]:
    """The files Git tracks under `project`, dot directories included, with the mode Git records (`LINK` for a
    link) and the id of their content; none outside a work tree. A Gap when Git does not answer inside one
    (`work_tree_git`)."""
    git = work_tree_git(project)
    if git is None:
        return {}
    try:
        listed = subprocess.run([git, "-C", str(project), "ls-files", "-z", "--stage"], stdin=subprocess.DEVNULL,
                                capture_output=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as error:
        raise Gap(f"Git did not list {project} ({error})", "install Git") from error
    if listed.returncode != 0:
        raise Gap(f"Git did not list {project}: {listed.stderr.decode('utf-8', 'replace').strip()[-300:]}",
                  "install Git, or let it read this repository")
    modes = {}
    for entry in listed.stdout.split(b"\0"):
        info, _, name = entry.partition(b"\t")
        mode, sha = (info.split() + [b"", b""])[:2]
        if mode in (b"100644", b"100755", b"120000"):
            modes[name.decode("utf-8", "surrogateescape")] = ({b"100755": 0o755, b"120000": LINK}.get(mode, 0o644),
                                                              sha.decode("ascii"))
    return modes


def _link(path: Path, sha: str) -> str | None:
    """The target of a link Git tracks at `path`, as Git records it: the link's own, or the content of the small file
    Git checks out where it makes no links (`core.symlinks` false), which keeps the id Git records; None when the
    work tree holds another file there."""
    if path.is_symlink():
        return os.readlink(path).replace(os.sep, "/")
    content = path.read_bytes() if path.is_file() else b""
    digest = hashlib.new("sha1" if len(sha) == 40 else "sha256", b"blob %d\0" % len(content) + content)
    return content.decode("utf-8", "surrogateescape") if digest.hexdigest() == sha else None


def _within(relative: str, target: str) -> bool:
    """Whether a link at `relative` to `target` leads inside the project: no root, no drive, never above it."""
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(relative), target))
    return not PureWindowsPath(target).anchor and resolved != ".." and not resolved.startswith("../")


def copy_perimeter(project: Path, target: Path, inputs: dict[str, Path] | None = None) -> dict:
    """A tar of what a build may need: under `work/`, the files the snapshot perimeter walks and the files Git
    tracks (dot directories included), minus the files the snapshot never reads; `inputs` at their own paths.

    What Git ignores stays out. A tracked file keeps the executable bit Git records, also where the disk has none.
    A link Git tracks whose target lies inside the project is that link in the copy, never followed; one whose
    target lies outside stays out, a `link_outside` gap of the returned `gaps`, which the run's result carries.
    """
    modes = tracked(project)
    folders, files = {"work"}, dict.fromkeys(modes)
    for directory, names in Perimeter(project).walk():
        relative = directory.relative_to(project).as_posix()
        folders.add("work" if relative == "." else f"work/{relative}")
        files.update((name if relative == "." else f"{relative}/{name}", None) for name in names)
    kept, links, gaps = [], [], []
    for relative in sorted(files):
        path = project / relative
        mode, sha = modes.get(relative, (None, ""))
        link = _link(path, sha) if mode == LINK and not is_forbidden(path.name) else None
        if link is not None and _within(relative, link):
            links.append((f"work/{relative}", path, link))
        elif link is not None:
            gaps.append({"kind": "link_outside", "path": relative, "target": link,
                         "detail": f"{relative} is a link Git tracks to {link}, outside the project: the copy leaves "
                                   "it out, and what reads it there finds nothing"})
        elif not (path.is_symlink() or not path.is_file() or is_forbidden(path.name, path)):
            kept.append((f"work/{relative}", path, None if mode == LINK else mode))
    for destination, path in sorted((inputs or {}).items()):
        kept.append((destination.strip("/"), Path(path), 0o644))
    for name, _, _ in (*kept, *links):
        folders.update(parent.as_posix() for parent in Path(name).parents if parent != Path("."))
    with tarfile.open(target, "w", format=tarfile.PAX_FORMAT) as bundle:
        for folder in sorted(folders):
            entry = tarfile.TarInfo(folder)
            entry.type, entry.mode = tarfile.DIRTYPE, 0o755
            bundle.addfile(entry)
        for name, path, mode in kept:
            status = path.stat()
            entry = tarfile.TarInfo(name)
            entry.size, entry.mtime = status.st_size, int(status.st_mtime)
            entry.mode = (mode or 0o644) if os.name == "nt" else status.st_mode & 0o777
            with path.open("rb") as handle:
                bundle.addfile(entry, handle)
        for name, path, link in links:  # last: no file of the copy is written through one
            entry = tarfile.TarInfo(name)
            entry.type, entry.linkname, entry.mode = tarfile.SYMTYPE, link, 0o777
            entry.mtime = int(path.lstat().st_mtime)
            bundle.addfile(entry)
    with target.open("rb") as handle:
        return {"files": len(kept) - len(inputs or {}), "inputs": len(inputs or {}), "links": len(links),
                "sha256": hashlib.file_digest(handle, "sha256").hexdigest(), "gaps": gaps}


def proxy_environment(address: str) -> dict[str, str]:
    return {name: ("" if name.lower() == "no_proxy" or not address else address) for name in PROXY_VARIABLES}


def append_record(record: Path, row: dict) -> None:
    with record.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def kept(path: str) -> bool:
    """Whether a container path lies in the volumes a preparation hands to execution."""
    path = posixpath.normpath(path)
    return any(path == root or path.startswith(root + "/") for root in (WORKDIR, STATE))


def volume_registry() -> Path:
    """One file per run holding volumes: the engine, the process and the volume names."""
    return shared_cache_dir() / "container-volumes"


def record_volumes(entry: Path, engine: str, pid: int, names: list[str]) -> None:
    entry.parent.mkdir(parents=True, exist_ok=True)
    partial = entry.with_suffix(".partial")
    partial.write_text(json.dumps({"engine": engine, "pid": pid, "volumes": names}), encoding="utf-8")
    os.replace(partial, entry)


def remove_volumes(engine: Engine, entry: Path, pid: int, names: list[str]) -> None:
    """Each volume removed by name; the entry keeps only those still there, and goes when none is."""
    left = [name for name in names if cli(engine, "volume", "rm", name).returncode != 0
            and cli(engine, "volume", "inspect", name).returncode == 0]
    if left:
        record_volumes(entry, engine.name, pid, left)
    else:
        entry.unlink(missing_ok=True)


def sweep(engine: Engine) -> None:
    """The volumes of this engine on record for a process that has ended, removed by name."""
    folder = volume_registry()
    for entry in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            held = json.loads(entry.read_text(encoding="utf-8"))
            if held["engine"] != engine.name or _process_alive(held["pid"]):
                continue
            names = [name for name in held["volumes"] if isinstance(name, str) and VOLUME_NAME.fullmatch(name)]
        except (OSError, ValueError, KeyError, TypeError):
            continue
        remove_volumes(engine, entry, held["pid"], names)


def phase(engine: Engine, name: str, *, image: str, command: list[str], network: str, env: dict[str, str],
          limits: dict, timeout: float, copy: Path | None, outputs: list[str], out_dir: Path,
          volumes: list[str] = ()) -> dict:
    """One container from create to rm, with the `name:path` volumes mounted: its record, with the outputs
    brought back."""
    box = f"daodan-{uuid.uuid4().hex[:12]}"
    args = ["create", "--name", box, "--network", network, "--memory", str(limits["memory"]),
            "--memory-swap", str(limits["memory"]), "--pids-limit", str(limits["pids"]),
            "--security-opt", "no-new-privileges", "-w", WORKDIR]
    if limits.get("cpus"):
        args += ["--cpus", str(limits["cpus"])]
    for key, value in env.items():
        args += ["-e", f"{key}={value}"]
    for mount in volumes:
        args += ["-v", mount]
    row = {"phase": name, "engine": engine.name, "image": image, "command": list(command), "network": network,
           "limits": {**limits, "seconds": timeout}, "volumes": list(volumes),
           "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "outputs": []}
    started = time.monotonic()
    try:
        checked(cli(engine, *args, image, *command), "create")
        if copy is not None:
            with copy.open("rb") as handle:
                checked(cli(engine, "cp", "-", f"{box}:/", stdin=handle), "cp of the copy")
        log = out_dir / f"{name}.log"
        row["log"] = str(log)
        with log.open("wb") as handle:
            try:
                row["exit_code"] = cli(engine, "start", "-a", box, stdout=handle, stderr=subprocess.STDOUT,
                                       timeout=timeout).returncode
                row["outcome"] = "exited"
            except subprocess.TimeoutExpired:
                cli(engine, "kill", box)
                row["exit_code"], row["outcome"] = None, "timeout"
        budget = OUTPUT_CAP
        for path in outputs:
            files, size = fetch(engine, box, path, out_dir, budget)
            row["outputs"] += files
            budget -= size
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        row["outcome"], row["cause"] = "failed", str(error)
    finally:
        cli(engine, "rm", "-f", box)
        row["duration_seconds"] = round(time.monotonic() - started, 3)
    return row


class Header(tarfile.TarInfo):
    """A tar header read with the refusals CPython's reader lacks in some supported releases: a negative size,
    which before its fix of CVE-2025-8194 sends the reader back to the same header forever, and a pax header over
    `HEADER_CAP`, which before 3.12.6 it parses with backtracking (CVE-2024-6232). A GNU long name over the cap
    is refused too: no output needs one."""

    def _block(self, count):
        if count < 0:
            raise tarfile.ReadError("a header gives a negative size")
        return super()._block(count)

    def _proc_pax(self, archive):
        self.capped()
        return super()._proc_pax(archive)

    def _proc_gnulong(self, archive):
        self.capped()
        return super()._proc_gnulong(archive)

    def capped(self) -> None:
        if self.size > HEADER_CAP:
            raise tarfile.ReadError(f"a header of {self.size} bytes, over the {HEADER_CAP} a name and its times need")


def member_parts(name: str) -> list[str] | None:
    """The folders and file name of an archive member below its folder, or None for a name that could leave the
    folder or that some system cannot hold as written (the same rule everywhere)."""
    parts = [part for part in name.split("/") if part not in ("", ".")]
    if not parts or name.startswith("/") or any(part == ".." or UNSAFE_PART.fullmatch(part) for part in parts):
        return None
    return parts


def unpack(bundle: tarfile.TarFile, members: list[tarfile.TarInfo], folder: Path, path: str) -> None:
    """Every member written by Daodan into the empty `folder`, never by tarfile's extraction: names checked
    first, folders made, regular files copied from their content and created, never opened over a file."""
    placed = []
    for member in members:
        parts = member_parts(member.name)
        if parts is None:
            raise RuntimeError(f"output {path} refused: the member name {member.name!r} leaves its folder or is "
                               "not a file name on every system")
        placed.append((member, folder.joinpath(*parts)))
    for member, target in placed:
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with bundle.extractfile(member) as source, target.open("xb") as handle:
            shutil.copyfileobj(source, handle, 2**20)


def fetch(engine: Engine, box: str, path: str, out_dir: Path, budget: int) -> tuple[list[str], int]:
    """A declared output brought out as a plain tar, read only up to `budget` bytes of files with `Header`:
    regular files and folders only, their sizes summed before anything is written, then written by `unpack`
    into a fresh empty folder and moved into `out_dir`, never over a file already there. Nothing when it is
    missing."""
    with tempfile.TemporaryFile() as archive:
        process = subprocess.Popen([*engine.argv, "cp", f"{box}:{path}", "-"], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        size = 0
        for chunk in iter(lambda: process.stdout.read(2**20), b""):
            size += len(chunk)
            if size > budget + STREAM_SLACK:
                process.kill()
                process.wait()
                raise RuntimeError(f"output {path} is over the {budget} bytes the run may still bring back")
            archive.write(chunk)
        if process.wait() != 0:
            return [], 0
        archive.seek(0)
        try:
            with tarfile.open(fileobj=archive, mode="r:", tarinfo=Header) as bundle:
                members = bundle.getmembers()
                odd = [member.name for member in members if not (member.isfile() or member.isdir())]
                if odd:
                    raise RuntimeError(f"output {path} refused: {', '.join(odd[:3])} are not regular files or folders")
                total = sum(member.size for member in members if member.isfile())
                if total > budget:
                    raise RuntimeError(f"output {path} holds {total} bytes, over the {budget} the run may still "
                                       "bring back")
                fresh = Path(tempfile.mkdtemp(prefix=".incoming-", dir=out_dir))
                try:
                    unpack(bundle, members, fresh, path)
                    for item in sorted(fresh.iterdir()):
                        if item.name in RUN_FILES or (out_dir / item.name).exists():
                            raise RuntimeError(f"output {path} refused: it would replace {out_dir / item.name}")
                    for item in sorted(fresh.iterdir()):
                        shutil.move(str(item), str(out_dir / item.name))
                finally:
                    shutil.rmtree(fresh, ignore_errors=True)
        except (tarfile.TarError, OSError) as error:
            raise RuntimeError(f"output {path} refused: {error}") from error
    return [str(out_dir / member.name) for member in members if member.isfile()], total


def start_proxy(engine: Engine, box: str, network: str, registries: tuple[str, ...]) -> None:
    source = base64.b64encode(PROXY_SCRIPT.encode("utf-8")).decode("ascii")
    checked(cli(engine, "create", "--name", box, "--memory", str(128 * 2**20), "--pids-limit", "64",
                PROXY_IMAGE, "python", "-c", f"import base64;exec(base64.b64decode('{source}'))",
                str(PROXY_PORT), *registries), "create of the proxy")
    checked(cli(engine, "network", "connect", "--alias", "proxy", network, box), "network connect of the proxy")
    checked(cli(engine, "start", box), "start of the proxy")
    for _ in range(50):
        if b"ready" in cli(engine, "logs", box).stdout:
            return
        time.sleep(0.2)
    raise RuntimeError("the registry proxy did not start")


@contextlib.contextmanager
def beside(services: list[dict], env: dict[str, str]):
    """Within it every `run_in_container` starts `services` in the pod its execution joins and gives both phases
    `env` under its caller's variables: the dynamic step's, so the tests of every observer get the services the
    project's CI declares and the variables its jobs give them. Each service is `{name, image, host, env, args,
    command}` (`args` options of `create`, `command` the image's command replaced when not empty); the pod's hosts
    name 127.0.0.1 for a `host` other than localhost (the module's docstring). It yields the list each run within
    extends with its result's `services`, wherever its record lies."""
    started: list[dict] = []
    token = BESIDE.set((list(services), dict(env), started))
    try:
        yield started
    finally:
        BESIDE.reset(token)


def qualified(image: str) -> str:
    """`image` with the registry Docker reads into a short name (Docker Hub, `library/` for an official image):
    Podman resolves a short name only through its own configuration, and never without a terminal."""
    first, slash, _rest = image.partition("/")
    if slash and ("." in first or ":" in first or first == "localhost"):
        return image
    return f"docker.io/{image}" if slash else f"docker.io/library/{image}"


def pin(run: Callable, image: str, timeout: float) -> str:
    """`image` pulled by the engine, with the engine's own network, and named by the digest its registry gave;
    `run(*args, timeout=...)` is the engine's command line (`cli`). RuntimeError with the engine's message when
    it cannot be pulled."""
    reference = qualified(image)
    checked(run("pull", reference, timeout=timeout), f"pull of {reference}")
    answer = checked(run("image", "inspect", "--format", "{{json .RepoDigests}}", reference, timeout=120),
                     f"image inspect of {reference}")
    digests = json.loads(answer.stdout or "null") or []
    if not digests:
        raise RuntimeError(f"{reference} has no digest of its registry after the pull")
    return digests[0]


def seconds(duration: str, default: float) -> float:
    """A Go duration (`5s`, `1m30s`, `500ms`), as the engines read `--health-interval`, in seconds; `default` for
    one that is not."""
    parts = DURATION.findall(duration)
    return sum(float(number) * UNITS[unit] for number, unit in parts) \
        if parts and not DURATION.sub("", duration) else default


def start_services(run: Callable, services: list[dict], network: str, limits: dict, token: str,
                   scheduled: bool = True) -> list[dict]:
    """The pinned `services` (`beside`'s, each with `pinned`) created in `network` and started, then
    awaited as GitHub's runner awaits a service container: ready once running, or once healthy where it has a
    health check; failed, with the cause, when it stops, turns unhealthy or is still starting after
    `SERVICE_WAIT` seconds. The containers are `daodan-svc-<token>-<n>`; a record row each. `scheduled` False is
    an engine that may run no check by itself (Podman, on systemd's timers): each check runs from here
    (`healthcheck run`) at its interval, the engine's timer off, its retries counted by the engine."""
    rows = []
    for number, service in enumerate(services):
        box = f"daodan-svc-{token}-{number}"
        row = {"phase": "service", "name": service["name"], "image": service["image"], "pinned": service["pinned"],
               "network": network, "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        clock = time.monotonic()
        env = [item for key, value in (service.get("env") or {}).items() for item in ("-e", f"{key}={value}")]
        args, every = list(service.get("args", ())), None
        if not scheduled and "--health-cmd" in args and "--no-healthcheck" not in args:
            at = args.index("--health-interval") + 1 if "--health-interval" in args[:-1] else None
            every = seconds(args[at], HEALTH_EVERY) if at else HEALTH_EVERY
            args = [*args[:at], "disable", *args[at + 1:]] if at else [*args, "--health-interval", "disable"]
        try:
            checked(run("create", "--name", box, "--network", network, "--memory", str(limits["memory"]),
                        "--memory-swap", str(limits["memory"]), "--pids-limit", str(limits["pids"]),
                        "--security-opt", "no-new-privileges", *env, *args, service["pinned"],
                        *service.get("command", ())), "create")
            checked(run("start", box), "start")
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            row.update(outcome="failed", cause=str(error))
        rows.append((row, box, clock, every))
    for row, box, clock, every in rows:
        due = clock  # Podman runs a check as soon as the container starts, then at each interval
        while "outcome" not in row:
            if every is not None and time.monotonic() >= due:
                run("healthcheck", "run", box, timeout=120)  # its code is the check's: the state says it
                due = time.monotonic() + every
            said = run("inspect", "--format", SERVICE_STATE, box, timeout=60).stdout.decode("utf-8", "replace")
            status, _, health = said.strip().partition(" ")
            if status == "running" and health in ("", "healthy"):
                row["outcome"] = "ready"
            elif status != "running" or health == "unhealthy":
                logs = run("logs", "--tail", "5", box, timeout=60)
                tail = " | ".join(line.strip() for line in (logs.stdout + logs.stderr).decode("utf-8", "replace")
                                  .splitlines() if line.strip())
                cause = "its health check failed" if status == "running" else f"it {status or 'is gone'}"
                row.update(outcome="failed", cause=f"{cause}: {tail[-400:]}" if tail else cause)
            elif time.monotonic() - clock > SERVICE_WAIT:
                row.update(outcome="failed", cause=f"still {health} after {SERVICE_WAIT} s: its health check "
                                                   "never passed")
            else:
                time.sleep(1)
        row["duration_seconds"] = round(time.monotonic() - clock, 3)
    return [row for row, *_ in rows]


def declared(record: Path, image: str, command: list[str], gap: Gap) -> dict:
    """The result of a run that cannot happen, recorded."""
    append_record(record, {"phase": "execute", "image": image, "command": list(command), "outcome": "gap",
                           "cause": gap.cause, "remedy": gap.remedy, "duration_seconds": 0,
                           "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    return {"state": "gap", "cause": gap.cause, "remedy": gap.remedy, "exit_code": None, "outputs": [],
            "record": str(record)}


def run_in_container(project: Path, command: list[str], *, image: str, out_dir: Path, prepare: list[str] | None = None,
                     outputs: list[str] = (), env: dict[str, str] | None = None, timeout: float = 600,
                     prepare_timeout: float = 1800, memory: int = 2 * 2**30, pids: int = 1024,
                     cpus: float | None = None, registries: tuple[str, ...] = REGISTRIES,
                     engine: Engine | str | None = None,
                     inputs: dict[str, Path] | Callable[[], dict[str, Path]] | None = None) -> dict:
    """Run `command` in a container over a copy of `project`; `prepare` first, with the registries open.

    `inputs` maps a container path to a host file the copy carries there, or is a function returning that map,
    called once an engine answers, which may raise Gap. With `prepare`, inputs lie under /work or /daodan/state
    and outputs outside them (the engine copies no file out of a volume): ValueError otherwise. `engine` is an
    Engine, "daodan" for Daodan's own, or None to find one. Within `beside`, its services start in the pod the
    execution joins and its variables reach both phases under `env`. The result's `state` is
    `done` (the command exited, `exit_code` says how), `timeout`, `failed` (with `cause`) or `gap`
    (with `cause` and `remedy`); `outputs` lists the files brought back into `out_dir`; `services`, with
    services, each `{name, image, pinned, outcome}`, `outcome` `ready` or `failed` with `cause`: the execution
    runs without a service that failed.
    """
    project, out_dir = Path(project).resolve(), Path(out_dir).resolve()
    if out_dir == project or project in out_dir.parents:
        raise ValueError("the output folder must be outside the project")
    if prepare and any(kept(path) for path in outputs):
        raise ValueError(f"with a preparation, outputs lie outside {WORKDIR} and {STATE}: the engine copies no "
                         "file out of a volume")
    out_dir.mkdir(parents=True, exist_ok=True)
    record = out_dir / RECORD_NAME
    limits = {"memory": int(memory), "pids": int(pids), "cpus": cpus}
    services, variables, started = BESIDE.get() or ((), {}, [])
    env = {**variables, **(env or {})}
    try:
        free = free_memory()
        if free is not None and free < memory:
            raise Gap(f"{free / 2**30:.1f} GB of memory free; the container's limit is {memory / 2**30:.1f} GB",
                      "close programs or lower the memory limit")
        found = engine if isinstance(engine, Engine) else own_engine() if engine == "daodan" else find_engine()
    except Gap as gap:
        return declared(record, image, command, gap)
    token = uuid.uuid4().hex[:12]
    cleanup: list[tuple[str, ...]] = []
    held: tuple[Path, list[str]] | None = None
    result = {"state": "failed", "exit_code": None, "outputs": [], "record": str(record), "engine": found.name}
    try:
        sweep(found)

        def engine_cli(*args: str, timeout: float = 300) -> subprocess.CompletedProcess:
            return cli(found, *args, timeout=timeout)

        pinned, served = [], []
        for service in services:  # pulled with the engine's network, before anything of the project runs
            try:
                pinned.append({**service, "pinned": pin(engine_cli, service["image"], prepare_timeout)})
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                served.append({"phase": "service", "name": service["name"], "image": service["image"],
                               "outcome": "failed", "cause": str(error)})
        with tempfile.TemporaryDirectory(prefix="daodan-copy-") as scratch:
            copy = Path(scratch) / "copy.tar"
            given = inputs() if callable(inputs) else inputs
            if prepare and not all(kept(path) for path in given or {}):
                raise ValueError(f"with a preparation, inputs lie under {WORKDIR} or {STATE}, which execution sees")
            digest = copy_perimeter(project, copy, given)
            if digest["gaps"]:  # what the copy left out of the project (`copy_perimeter`)
                result["gaps"] = digest["gaps"]
            run_copy, mounts, env = copy, [], {"HOME": HOME, **(env or {})} if prepare else dict(env or {})
            if prepare:
                names = [f"daodan-work-{token}", f"daodan-state-{token}"]
                held = (volume_registry() / f"{token}.json", names)
                record_volumes(held[0], found.name, os.getpid(), names)
                for name in names:
                    checked(cli(found, "volume", "create", name), "volume create")
                mounts = [f"{names[0]}:{WORKDIR}", f"{names[1]}:{STATE}"]
                network, proxy = f"daodan-net-{token}", f"daodan-proxy-{token}"
                checked(cli(found, "network", "create", "--internal", network), "network create")
                cleanup += [("rm", "-f", proxy), ("network", "rm", network)]
                start_proxy(found, proxy, network, tuple(registries))
                row = phase(found, "prepare", image=image, command=prepare, network=network,
                            env={**env, **proxy_environment(f"http://proxy:{PROXY_PORT}")}, limits=limits,
                            timeout=prepare_timeout, copy=copy, outputs=[], out_dir=out_dir, volumes=mounts)
                append_record(record, {**row, "copy": digest})
                if row["outcome"] != "exited" or row["exit_code"] != 0:
                    result["cause"] = row.get("cause") or (f"preparation {row['outcome']}" + (
                        f" with code {row['exit_code']}" if row["exit_code"] is not None else "") + f"; see {row['log']}")
                    return result
                run_copy = None
            joined = "none"
            if pinned:
                pod = f"daodan-pod-{token}"
                cleanup[:0] = [*(("rm", "-f", f"daodan-svc-{token}-{n}") for n in range(len(pinned))),
                               ("rm", "-f", pod)]
                hosts = sorted({f"--add-host={s['host']}:127.0.0.1" for s in pinned
                                if s.get("host") not in (None, "localhost")})
                try:
                    checked(cli(found, "create", "--name", pod, "--network", "none", *hosts, "--memory",
                                str(64 * 2**20), "--pids-limit", "16", PROXY_IMAGE, "sleep", str(int(timeout) + 600)),
                            "create of the pod")
                    checked(cli(found, "start", pod), "start of the pod")
                    joined = f"container:{pod}"
                    served += start_services(engine_cli, pinned, joined, limits, token, found.name != "podman")
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                    served += [{"phase": "service", "name": s["name"], "image": s["image"], "pinned": s["pinned"],
                                "outcome": "failed", "cause": str(error)} for s in pinned]
            for row in served:
                append_record(record, {**row, "engine": found.name})
            if services:
                result["services"] = [{key: row[key] for key in ("name", "image", "pinned", "outcome", "cause")
                                       if key in row} for row in served]
                started += result["services"]
            row = phase(found, "execute", image=image, command=command, network=joined,
                        env={**env, **proxy_environment("")}, limits=limits, timeout=timeout,
                        copy=run_copy, outputs=list(outputs), out_dir=out_dir, volumes=mounts)
            append_record(record, {**row, "copy": digest})
            result.update(exit_code=row.get("exit_code"), outputs=row["outputs"],
                          state={"exited": "done", "timeout": "timeout"}.get(row["outcome"], "failed"))
            if "cause" in row:
                result["cause"] = row["cause"]
            return result
    except Gap as gap:
        return {**declared(record, image, command, gap), "engine": found.name}
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        result["cause"] = str(error)
        return result
    finally:
        for args in cleanup:
            try:
                cli(found, *args)
            except (OSError, subprocess.TimeoutExpired):
                pass
        if held:
            try:
                remove_volumes(found, held[0], os.getpid(), held[1])
            except (OSError, subprocess.TimeoutExpired):
                pass
        found.stop()


def command_lines(commands: list[tuple[int, dict]], into: str) -> str:
    """POSIX sh: each command in a subshell from its folder under the copy, its code and streams in `into/<n>/`."""
    lines = []
    for number, item in commands:
        folder = f"{into}/{number}"
        cwd = posixpath.normpath(posixpath.join(WORKDIR, item.get("cwd") or "."))
        words = ["env", *(f"{key}={value}" for key, value in (item.get("env") or {}).items()), *item["argv"]]
        lines.append(f"mkdir -p {folder}; (cd {shlex.quote(cwd)} && exec {shlex.join(map(str, words))}) "
                     f"> {folder}/stdout 2> {folder}/stderr; echo $? > {folder}/code")
    return "\n".join(lines) + "\nexit 0\n"


def run_commands(project: Path, commands: list[dict], *, image: str, out_dir: Path, **options) -> dict:
    """Commands as data, each `{tool, argv, cwd, env, network}`, in one container run over a copy of `project`:
    those whose `network` is "registries" in the preparation, the others ("none", the default) in execution.
    `cwd` is relative to the copy. The result of `run_in_container` (`options` are its own), with `root`, the
    copy's folder, and `results`: each command's `returncode` (None when it did not run), `stdout` and `stderr`,
    in the given order."""
    for item in commands:
        target = posixpath.normpath(posixpath.join(WORKDIR, item.get("cwd") or "."))
        inside = target == WORKDIR or target.startswith(WORKDIR + "/")
        if not item.get("argv") or posixpath.isabs(item.get("cwd") or ".") or not inside or (
                item.get("network", "none") not in NETWORKS):
            raise ValueError(f"a command needs an argv, a folder inside the copy and a network in {NETWORKS}: {item}")
    early = [(n, item) for n, item in enumerate(commands) if item.get("network") == "registries"]
    late = [(n, item) for n, item in enumerate(commands) if item.get("network", "none") == "none"]
    kept_results = f"{STATE}/results"
    carry = f"mkdir -p {RESULTS}\n" + (f"cp -R {kept_results}/. {RESULTS}/ 2>/dev/null\n" if early else "")
    out_dir = Path(out_dir)
    shutil.rmtree(out_dir / Path(RESULTS).name, ignore_errors=True)
    result = run_in_container(project, ["sh", "-c", carry + command_lines(late, RESULTS)], image=image,
                              out_dir=out_dir, prepare=["sh", "-c", command_lines(early, kept_results)] if early else None,
                              outputs=[RESULTS], **options)
    folder, results = out_dir / Path(RESULTS).name, []
    for number in range(len(commands)):
        read = {name: (folder / str(number) / name).read_text(encoding="utf-8", errors="replace")
                if (folder / str(number) / name).is_file() else "" for name in ("code", "stdout", "stderr")}
        code = read.pop("code").strip()
        results.append({"returncode": int(code) if code.lstrip("-").isdigit() else None, **read})
    return {**result, "root": WORKDIR, "results": results}
