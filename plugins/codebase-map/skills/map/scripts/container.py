#!/usr/bin/env python3
"""Run one command in a container over a disposable copy of the snapshot perimeter.

`run_in_container` is the one operation the dynamic step, the indexers that must build a
project and the dynamic reviews share (spec `docs/specs/2026-11-12-passo-dinamico.md`,
sections 2-4). Its guarantees:

1. The project's code runs only in the container, never on the host.
2. The container gets a copy of the files the snapshot perimeter walks, minus the files the
   snapshot never reads, as a tar through `cp -`. The project is never mounted or written;
   declared outputs come back through `cp <container>:<path> -` into a folder outside it.
3. Execution runs with `--network none`; an optional preparation runs on an internal
   network whose only way out is a proxy that opens CONNECT to package registries on port
   443, and is committed into the image execution starts from. Memory, swap, processes
   and time are limited, and no host variable reaches the container: only the `env` given,
   and the proxy variables set explicitly so the CLI's own proxy configuration adds none.
4. Every phase appends a record (command, image, engine, limits, copy digest, duration,
   outcome) to `container-runs.jsonl` in the output folder.
5. Without an engine that can run, the operation returns a declared gap with cause and
   remedy, and never falls back to the host.

The engine is reached only through a Docker-compatible command line (`create`, `cp`,
`start`, `commit`, `rm`, `network`), so it can be replaced. An engine the user already has
(`docker`, then `podman`) is used as found: no context, no configuration, no option of
Daodan's. Otherwise, on Windows, Daodan runs Kiri at a pinned version in a WSL 2
distribution of its own under the shared directory, never through Kiri's Windows app or
installer. Kiri engines in one WSL VM share its network namespace and each rebuilds and
removes the same nftables table, so Daodan's engine never starts beside another one.

Standard library only.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import lzma
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, NamedTuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from resolve_edges import _platform, download, free_memory, shared_engine_dir  # noqa: E402
from snapshot import is_forbidden  # noqa: E402
from tree_scope import Perimeter  # noqa: E402

RECORD_NAME = "container-runs.jsonl"
WORKDIR = "/work"
# The registries a preparation may reach, by host; everything else is refused by the proxy.
REGISTRIES = (
    "registry.npmjs.org", "registry.yarnpkg.com", "pypi.org", "files.pythonhosted.org",
    "repo1.maven.org", "repo.maven.apache.org", "plugins.gradle.org", "proxy.golang.org",
    "sum.golang.org", "index.crates.io", "static.crates.io", "api.nuget.org", "rubygems.org",
)
# Set on every container, empty when closed: the CLI adds its configured proxies only to unset names.
PROXY_VARIABLES = ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "FTP_PROXY", "ALL_PROXY",
                   "http_proxy", "https_proxy", "no_proxy", "ftp_proxy", "all_proxy")
PROXY_IMAGE = "python:3.13-alpine@sha256:9ef1a599f863231c3d91e941389bfdc4a2d6070557243d54df1a4e57015b960e"
PROXY_PORT = 3128
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
    """The user's engine that answers (`docker`, then `podman`), else Daodan's own; a Gap when none can run."""
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


def copy_perimeter(project: Path, target: Path) -> dict:
    """A tar under `work/` of the files the snapshot perimeter walks, minus those the snapshot never reads."""
    count = 0
    with tarfile.open(target, "w", format=tarfile.PAX_FORMAT) as bundle:
        for directory, names in Perimeter(project).walk():
            relative = directory.relative_to(project).as_posix()
            folder = tarfile.TarInfo("work" if relative == "." else f"work/{relative}")
            folder.type, folder.mode = tarfile.DIRTYPE, 0o755
            bundle.addfile(folder)
            for name in names:
                path = directory / name
                if path.is_symlink() or not path.is_file() or is_forbidden(name, path):
                    continue
                status = path.stat()
                info = tarfile.TarInfo(f"{folder.name}/{name}")
                info.size, info.mtime = status.st_size, int(status.st_mtime)
                info.mode = 0o644 if os.name == "nt" else status.st_mode & 0o777
                with path.open("rb") as handle:
                    bundle.addfile(info, handle)
                count += 1
    with target.open("rb") as handle:
        return {"files": count, "sha256": hashlib.file_digest(handle, "sha256").hexdigest()}


def proxy_environment(address: str) -> dict[str, str]:
    return {name: ("" if name.lower() == "no_proxy" or not address else address) for name in PROXY_VARIABLES}


def append_record(record: Path, row: dict) -> None:
    with record.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def phase(engine: Engine, name: str, *, image: str, command: list[str], network: str, env: dict[str, str],
          limits: dict, timeout: float, copy: Path | None, outputs: list[str], out_dir: Path,
          commit: str | None = None) -> dict:
    """One container from create to rm: its record, with the outputs brought back."""
    box = f"daodan-{uuid.uuid4().hex[:12]}"
    args = ["create", "--name", box, "--network", network, "--memory", str(limits["memory"]),
            "--memory-swap", str(limits["memory"]), "--pids-limit", str(limits["pids"]),
            "--security-opt", "no-new-privileges", "-w", WORKDIR]
    if limits.get("cpus"):
        args += ["--cpus", str(limits["cpus"])]
    for key, value in env.items():
        args += ["-e", f"{key}={value}"]
    row = {"phase": name, "engine": engine.name, "image": image, "command": list(command), "network": network,
           "limits": {**limits, "seconds": timeout},
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
        for path in outputs:
            row["outputs"] += fetch(engine, box, path, out_dir)
        if commit and row["outcome"] == "exited" and row["exit_code"] == 0:
            checked(cli(engine, "commit", box, commit), "commit")
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        row["outcome"], row["cause"] = "failed", str(error)
    finally:
        cli(engine, "rm", "-f", box)
        row["duration_seconds"] = round(time.monotonic() - started, 3)
    return row


def fetch(engine: Engine, box: str, path: str, out_dir: Path) -> list[str]:
    """A declared output brought out as a tar and unpacked with the data filter; nothing when it is missing."""
    with tempfile.TemporaryFile() as archive:
        if cli(engine, "cp", f"{box}:{path}", "-", stdout=archive).returncode != 0:
            return []
        archive.seek(0)
        try:
            with tarfile.open(fileobj=archive) as bundle:
                members = [member for member in bundle.getmembers() if member.isfile()]
                bundle.extractall(out_dir, filter="data")
        except tarfile.TarError as error:
            raise RuntimeError(f"output {path} refused: {error}") from error
    return [str(out_dir / member.name) for member in members]


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


def run_in_container(project: Path, command: list[str], *, image: str, out_dir: Path, prepare: list[str] | None = None,
                     outputs: list[str] = (), env: dict[str, str] | None = None, timeout: float = 600,
                     prepare_timeout: float = 1800, memory: int = 2 * 2**30, pids: int = 1024,
                     cpus: float | None = None, registries: tuple[str, ...] = REGISTRIES,
                     engine: Engine | str | None = None) -> dict:
    """Run `command` in a container over a copy of `project`; `prepare` first, with the registries open.

    `engine` is an Engine, "daodan" for Daodan's own, or None to find one. The result's `state` is
    `done` (the command exited, `exit_code` says how), `timeout`, `failed` (with `cause`) or `gap`
    (with `cause` and `remedy`); `outputs` lists the files brought back into `out_dir`.
    """
    project, out_dir = Path(project).resolve(), Path(out_dir).resolve()
    if out_dir == project or project in out_dir.parents:
        raise ValueError("the output folder must be outside the project")
    out_dir.mkdir(parents=True, exist_ok=True)
    record = out_dir / RECORD_NAME
    limits = {"memory": int(memory), "pids": int(pids), "cpus": cpus}
    try:
        free = free_memory()
        if free is not None and free < memory:
            raise Gap(f"{free / 2**30:.1f} GB of memory free; the container's limit is {memory / 2**30:.1f} GB",
                      "close programs or lower the memory limit")
        found = engine if isinstance(engine, Engine) else own_engine() if engine == "daodan" else find_engine()
    except Gap as gap:
        append_record(record, {"phase": "execute", "image": image, "command": list(command), "outcome": "gap",
                               "cause": gap.cause, "remedy": gap.remedy, "duration_seconds": 0,
                               "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
        return {"state": "gap", "cause": gap.cause, "remedy": gap.remedy, "exit_code": None, "outputs": [],
                "record": str(record)}
    token = uuid.uuid4().hex[:12]
    cleanup: list[tuple[str, ...]] = []
    result = {"state": "failed", "exit_code": None, "outputs": [], "record": str(record), "engine": found.name}
    try:
        with tempfile.TemporaryDirectory(prefix="daodan-copy-") as scratch:
            copy = Path(scratch) / "copy.tar"
            digest = copy_perimeter(project, copy)
            run_image, run_copy = image, copy
            if prepare:
                network, proxy, prepared = f"daodan-net-{token}", f"daodan-proxy-{token}", f"daodan-prepared:{token}"
                checked(cli(found, "network", "create", "--internal", network), "network create")
                cleanup += [("rm", "-f", proxy), ("network", "rm", network), ("rmi", "-f", prepared)]
                start_proxy(found, proxy, network, tuple(registries))
                row = phase(found, "prepare", image=image, command=prepare, network=network,
                            env={**(env or {}), **proxy_environment(f"http://proxy:{PROXY_PORT}")}, limits=limits,
                            timeout=prepare_timeout, copy=copy, outputs=[], out_dir=out_dir, commit=prepared)
                append_record(record, {**row, "copy": digest})
                if row["outcome"] != "exited" or row["exit_code"] != 0:
                    result["cause"] = row.get("cause") or (f"preparation {row['outcome']}" + (
                        f" with code {row['exit_code']}" if row["exit_code"] is not None else "") + f"; see {row['log']}")
                    return result
                run_image, run_copy = prepared, None
            row = phase(found, "execute", image=run_image, command=command, network="none",
                        env={**(env or {}), **proxy_environment("")}, limits=limits, timeout=timeout,
                        copy=run_copy, outputs=list(outputs), out_dir=out_dir)
            append_record(record, {**row, "copy": digest})
            result.update(exit_code=row.get("exit_code"), outputs=row["outputs"],
                          state={"exited": "done", "timeout": "timeout"}.get(row["outcome"], "failed"))
            if "cause" in row:
                result["cause"] = row["cause"]
            return result
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        result["cause"] = str(error)
        return result
    finally:
        for args in cleanup:
            try:
                cli(found, *args)
            except (OSError, subprocess.TimeoutExpired):
                pass
        found.stop()
