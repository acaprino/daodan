#!/usr/bin/env python3
"""Run one command in a container over a disposable copy of the snapshot perimeter.

`run_in_container` is the one operation the dynamic step, the indexers that must build a
project and the dynamic reviews share (spec `docs/specs/2026-11-12-passo-dinamico.md`,
sections 2-4). Its guarantees:

1. The project's code runs only in the container, never on the host.
2. The container gets a copy of the files the snapshot perimeter walks and of those Git
   tracks, dot directories included, minus the files the snapshot never reads, as a tar
   through `cp -`; what Git ignores stays out, and a link Git tracks is that link only when
   it leads inside the project (`copy_perimeter`). The `.env` files Git tracks are in it, as
   in the CI's checkout: their values are read only in a container of Daodan's
   (`dotenv_values`) and masked in what the run keeps (`masker`); any other file the snapshot
   never reads stays out, a `file_withheld` gap. The project is never mounted or written;
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
gave; the execution starts once every service is ready (`start_services`). The steps a CI job
runs before its tests run at the end of the preparation; with services, the pod is on the
preparation's network while they run, and leaves it, the proxy gone, before the execution.

The engine is reached only through a Docker-compatible command line (`create`, `cp`,
`start`, `rm`, `network`, `volume`), so it can be replaced. On Windows it is always Daodan's
own: Kiri at a pinned version in a WSL 2 distribution of its own under the shared directory,
never through Kiri's Windows app or installer, never the user's Docker, Podman or Kiri. Every
WSL distribution shares the VM's network namespace, where a Kiri builds and removes its
nftables table; Daodan's daemon runs in a namespace of its own, which pasta joins to the
outside with sockets, so it starts beside another Kiri and changes nothing of that shared
namespace. Elsewhere Daodan brings no engine: the user's (`docker`, then `podman`) is used as
found, with no context, no configuration, no option of Daodan's.
`DAODAN_CONTAINER=off` leaves every run without an engine, a gap at once (the test suites).

Standard library only.
"""
from __future__ import annotations

import base64
import contextlib
import contextvars
import fnmatch
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
from source_files import FORBIDDEN_GLOBS  # noqa: E402
from tree_scope import GIT_OPTIONS, Perimeter, git_executable, program  # noqa: E402

RECORD_NAME = "container-runs.jsonl"
WORKDIR = "/work"
STATE = "/daodan/state"  # with WORKDIR, what a preparation hands to execution
HOME = STATE + "/home"
VOLUME_NAME = re.compile(r"daodan-(?:work|state)-[0-9a-f]{12}")  # the only names a run removes
IMAGE_NAME = re.compile(r"daodan-prepared-[0-9a-f]{12}")  # a preparation kept for its execution (`keep_root`)
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
BESIDE = contextvars.ContextVar("beside", default=None)  # `beside`'s services, variables, steps and `Said`
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")  # a variable a shell exports
# A CI step's shell as GitHub's runner runs it: none named, `bash -e` where the image has bash, else `sh -e`
STEP_SHELLS = {None: "$SH", "bash": "bash --noprofile --norc -eo pipefail", "sh": "sh -e"}
CONDITIONS = {"service_started": "to start", "service_healthy": "to be healthy",
              "service_completed_successfully": "to complete"}  # Compose's `depends_on` conditions, as said
HEALTH_EVERY = 30.0  # Docker's and Podman's `--health-interval` when a service declares none, in seconds
DURATION = re.compile(r"(\d+(?:\.\d*)?|\.\d+)(ns|us|µs|ms|s|m|h)")  # Go's `time.ParseDuration`, unsigned
UNITS = {"ns": 1e-9, "us": 1e-6, "µs": 1e-6, "ms": 1e-3, "s": 1.0, "m": 60.0, "h": 3600.0}
REACH = ("import socket, sys\nfor port in sys.argv[1:]:\n"
         "    socket.create_connection(('127.0.0.1', int(port)), 2).close()")  # `reached`: each port answers
DOTENV = (".env", ".env.*")  # of the names Daodan never reads, those the copy carries where Git tracks the file
EXAMPLES = ("example", "sample", "template", "dist")  # the last part of an .env file's name the project publishes
TEXTS = (".log", ".txt")  # the outputs that are a run's text, masked as its logs are (`masker`)
STREAMS = ("stdout", "stderr")  # what a command of `run_commands` printed: a run's text too, never removed
JSONS = (".json",)  # the outputs that are JSON, masked string by string so they stay JSON (`scrubbed`)
UNMASKED = re.compile(r"(?i)true|false|yes|no|on|off|\d{1,5}")  # values the text's own words and ports would be
DOTENV_VALUES = STATE + "/dotenv-values.json"  # in the container of Daodan's helper only (`named`), never an output
PUBLIC_SECONDS = 60  # how long the reader of the .env files looks for their values in the project (`RESOLVE`)
MARKER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_.-]*)\}")  # where a fact names a variable of a tracked .env file
# Runs in a container of Daodan's (`dotenv_values`), in the folder of the copy, over the tracked .env files its
# arguments name: each variable's value as Compose's reader gives it (quotes, comments, references to those
# before it and their defaults), on one line after its mark. With DAODAN_PUBLIC, its seconds, a second line names the
# values the other files under the folder hold, in their path or their content (`.env*` files aside), read by
# pieces of 1 MiB: one pass, bounded in memory by the piece and in time by the seconds.
RESOLVE = r'''import fnmatch, json, os, re, sys, time
LINE = re.compile(r"[ \t]*(?:export[ \t]+)?([A-Za-z_][A-Za-z0-9_.-]*)[ \t]*=[ \t]*(.*)")
REF = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)(?:(:?[-+?])([^}]*))?\}|([A-Za-z_][A-Za-z0-9_]*))")
ESCAPES = {"n": "\n", "t": "\t", "r": "\r"}


def expand(text, known):
    def one(found):
        name, how, other = found.group(1) or found.group(4), found.group(2) or "", found.group(3) or ""
        value = known.get(name)
        unset = value is None or (how.startswith(":") and value == "")
        return (other if unset else value) if how.endswith("-") else ("" if unset else other) if how.endswith(
            "+") else value or ""
    return REF.sub(one, text)


def values(text):
    known, lines, i = {}, text.splitlines(), 0
    while i < len(lines):
        found, i = LINE.fullmatch(lines[i]), i + 1
        if not found:
            continue
        name, rest = found.groups()
        if rest[:1] in ("'", '"'):
            quote, body = rest[0], rest[1:]
            closing = re.compile(r"(?<!\\)" + quote)
            while not closing.search(body) and i < len(lines):  # a value over the next lines
                body, i = body + "\n" + lines[i], i + 1
            end = closing.search(body)
            body = body[:end.start()] if end else body
            known[name] = body if quote == "'" else expand(
                re.sub(r"\\(.)", lambda m: ESCAPES.get(m.group(1), m.group(1)), body), known)
        else:
            known[name] = expand(re.sub(r"[ \t]+#.*$", "", rest).strip(), known)
    return known


def public(found, seconds):
    wanted = {value.encode("utf-8", "replace") for held in found.values() for value in held.values() if value}
    held, until = set(), time.monotonic() + seconds
    for top, _, names in os.walk("."):
        for name in names:
            if not wanted or time.monotonic() >= until:  # what is not read in time stays secret
                return held
            if fnmatch.fnmatch(name.lower(), ".env") or fnmatch.fnmatch(name.lower(), ".env.*"):
                continue
            rel = os.path.relpath(os.path.join(top, name), ".").replace(os.sep, "/")
            seen = {value for value in wanted if value in rel.encode("utf-8", "replace")}
            tail = b""
            try:
                with open(rel, "rb") as handle:
                    while wanted - seen and time.monotonic() < until and (piece := handle.read(1 << 20)):
                        data = tail + piece
                        seen |= {value for value in wanted - seen if value in data}
                        keep = max(map(len, wanted - seen), default=1) - 1
                        tail = data[len(data) - keep:] if keep else b""
            except OSError:  # a file it cannot read publishes nothing
                pass
            held, wanted = held | seen, wanted - seen
    return held


found = {os.path.normpath(path): values(open(path, encoding="utf-8", errors="replace").read()) for path in sys.argv[1:]}
print("@@daodan-dotenv " + json.dumps(found))
if os.environ.get("DAODAN_PUBLIC"):
    print("@@daodan-public " + json.dumps(sorted(value.decode("utf-8", "replace") for value in public(
        found, float(os.environ["DAODAN_PUBLIC"])))))
'''
# Runs in its own container; argv: port, then the allowed hosts, CONNECT to their port 443; a host given as
# `http://<host>` (the apt sources a base image names over plain HTTP) is reached by plain HTTP at its port 80, only
# for a GET or HEAD of apt's archive (`dists/`, `pool/`: apt checks the signed Release files and each package's
# hash), one request a connection. Prints "ready <port>".
PROXY_SCRIPT = r'''
import re, select, socket, sys, threading
allowed = {host.lower() for host in sys.argv[2:] if not host.startswith("http://")}
archives = {host[len("http://"):].lower() for host in sys.argv[2:] if host.startswith("http://")}
ARCHIVE = re.compile(r"(?:/[^/?#\s]+)*/(?:dists|pool)/[^?#\s]*")
HOP = {b"connection", b"proxy-connection", b"keep-alive", b"proxy-authorization", b"te", b"upgrade"}
def fetch(client, method, host, path, head):
    """One request to an apt archive, at its port 80, and its answer back: the next ones never leave."""
    lines = [line for line in head.split(b"\r\n\r\n", 1)[0].split(b"\r\n")[1:]
             if line and line.split(b":", 1)[0].strip().lower() not in HOP | {b"host"}]
    request = b"\r\n".join([method + b" " + path.encode("latin-1") + b" HTTP/1.1", b"Host: " + host.encode("latin-1"),
                            *lines, b"Connection: close", b"", b""])
    try:
        upstream = socket.create_connection((host, 80), timeout=30)
    except OSError:
        client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n"); client.close(); return
    try:
        upstream.settimeout(300)
        upstream.sendall(request)
        while True:
            data = upstream.recv(65536)
            if not data:
                break
            client.sendall(data)
    except OSError:
        pass
    finally:
        upstream.close(); client.close()
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
    if len(words) == 3 and words[0] in (b"GET", b"HEAD") and words[1].startswith(b"http://"):
        place, _, path = words[1].decode("latin-1")[len("http://"):].partition("/")
        path = "/" + path
        if place.lower() in archives and ARCHIVE.fullmatch(path) and "/../" not in path + "/":
            return fetch(client, words[0], place.lower(), path, head)
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
# pasta (`DAEMON`), from Alpine's passt, installed at import by apk in the distribution: from the repositories the
# pinned base names, its signature checked against the keys the base carries, apk's own defaults. Its only network is
# its own sockets in the namespace every WSL distribution shares, closed when it exits; it keeps no cache.
INSTALL_PASTA = ("/sbin/apk", "add", "--no-cache", "passt")
PASTA_RECORD = "pasta-version"  # in the distribution's folder: the version apk installed, written once it has
DISTRO = "daodan-kiri"
SOCKET = "unix:///root/.kiri/run/docker.sock"
# No Windows drives and no Windows programs inside Daodan's distribution.
WSL_CONF = ("[boot]\nsystemd=false\n[automount]\nenabled=false\nmountFsTab=false\n"
            "[interop]\nenabled=false\nappendWindowsPath=false\n[user]\ndefault=root\n")
NETNS = "/run/daodan/net"  # Daodan's network namespace, bound on the distribution's /run: it ends when the distribution does
# The daemon in that namespace: Kiri builds and removes its nftables table, bridges and forwarding there, never in the
# namespace every WSL distribution shares. pasta gives it `eth0` with the VM's address and default route and carries its
# traffic as sockets of the shared namespace, adding no interface, route, table or setting there; it forwards no port
# and maps no address to the VM's loopback, and stays root (`--runas 0`) to join a namespace root made.
# The routers move off 80 and 443, which WSL would forward to the user's localhost.
DAEMON = ("grep -qs ' /sys/fs/cgroup cgroup2 ' /proc/mounts || { echo 'daodan: no cgroup v2 at /sys/fs/cgroup'; exit 3; }; "
          f"mkdir -p /run/daodan && : > {NETNS} && unshare --net={NETNS} true && /usr/bin/pasta --config-net -q "
          f"-t none -u none -T none -U none --no-map-gw --runas 0 --netns {NETNS} "
          "|| { echo 'daodan: no network namespace of its own for the engine'; exit 4; }; "
          f"export HOME=/root KIRI_HTTP_PORT=47080 KIRI_HTTPS_PORT=47443; exec nsenter --net={NETNS} /usr/bin/kiri daemon")
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
    found = program("wsl.exe")
    system = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "wsl.exe"
    return found or (str(system) if system.is_file() else None)


def wsl_program() -> str:
    """wsl.exe where `wsl_executable` finds it, a Gap without it: never the name alone, which Windows looks for in
    the working directory, the analyzed project, first."""
    found = wsl_executable()
    if not found:
        raise Gap("WSL is not installed", WSL_ENABLE)
    return found


def wsl(*args: str, timeout: float = 120) -> subprocess.CompletedProcess:
    """wsl.exe with UTF-8 output; the caller checks the outcome."""
    return subprocess.run([wsl_program(), *args], stdin=subprocess.DEVNULL, capture_output=True,
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
            names[guid], folders[name] = name, folder
    return names.get(default), folders


def same_folder(one: str | Path, other: str | Path) -> bool:
    """Two Windows folders in one form: WSL's `BasePath` and Daodan's own (from LOCALAPPDATA) may each carry the
    `\\\\?\\` prefix of long paths or not."""
    def form(path: str | Path) -> str:
        return os.path.normcase(os.path.abspath(str(path).removeprefix("\\\\?\\")))
    return form(one) == form(other)


def find_engine() -> Engine:
    """On Windows always Daodan's own engine, never one the user has (spec of the dynamic step); elsewhere, where
    Daodan brings none, the user's (`user_engine`). A Gap when none can run, and at once with `DAODAN_CONTAINER=off`
    (the test suites, which start no container)."""
    if os.environ.get("DAODAN_CONTAINER") == "off":
        raise Gap("container engine off (DAODAN_CONTAINER=off)", "unset DAODAN_CONTAINER to run in a container")
    return own_engine() if os.name == "nt" else user_engine()


def user_engine() -> Engine:
    """The user's engine that answers, `docker` then `podman`; a Gap without one."""
    for name, probe in (("docker", ("version", "--format", "{{.Server.Os}}")),
                        ("podman", ("info", "--format", "{{.Host.Os}}"))):
        path = program(name)  # never the project's own, from the working directory
        if not path:
            continue
        try:
            answer = subprocess.run([path, *probe], stdin=subprocess.DEVNULL, capture_output=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if answer.returncode == 0 and answer.stdout.decode("utf-8", "replace").strip() == "linux":
            return Engine(name, (path,))
    raise Gap("no container engine answers: neither docker nor podman",
              "install Docker or Podman; Daodan brings its own engine only on Windows")


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


def ensure_distro(home: Path) -> tuple[bool, str]:
    """Daodan's distribution imported from Alpine plus Kiri, with pasta installed by apk: whether it must go after
    use, and the version of pasta."""
    arch = architecture()
    default, folders = registered_distros()
    # Named by what decides the result: one an older Daodan made another way is imported again.
    made_from = json.dumps([ALPINE[arch], INSTALL_PASTA, KIRI_PACKAGES[arch], WSL_CONF]).encode("utf-8")
    folder = home / f"distro-{hashlib.sha256(made_from).hexdigest()[:12]}"
    current, record = folders.get(DISTRO), folder / PASTA_RECORD
    if current and same_folder(current, folder) and record.is_file():
        return default in (None, DISTRO), record.read_text(encoding="utf-8")
    if current:
        remove_distro()
    url, digest = ALPINE[arch]
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
    return default is None, install_pasta(folder)


def install_pasta(folder: Path) -> str:
    """apk's install of pasta into the distribution just imported at `folder`, and the version apk says it installed,
    kept there (`PASTA_RECORD`); a Gap with apk's words otherwise, the distribution unregistered and its folder gone:
    never one without pasta."""
    try:
        answer = wsl("-d", DISTRO, "--cd", "/", "--exec", *INSTALL_PASTA, timeout=300)
    except subprocess.TimeoutExpired:
        answer = None
    said = " ".join((answer.stdout + answer.stderr).decode("utf-8", "replace").split()) if answer else ""
    installed = re.search(r"Installing passt \(([^)\s]+)\)", said) if answer and answer.returncode == 0 else None
    if installed:
        (folder / PASTA_RECORD).write_text(installed[1], encoding="utf-8")
        return installed[1]
    remove_distro()
    shutil.rmtree(folder, ignore_errors=True)
    if "UNTRUSTED" in said:
        remedy = "retry on another connection; Alpine's index must verify against the keys of Daodan's Alpine base"
    elif not answer or "fetching" in said:
        remedy = "check the connection to dl-cdn.alpinelinux.org and retry"
    else:
        remedy = "update Daodan: the repositories of its Alpine release did not give passt"
    raise Gap(f"apk did not install pasta into Daodan's distribution: {said or 'no answer within 300 s'}", remedy)


def remove_distro() -> None:
    wsl("--unregister", DISTRO)


def distro_argv() -> tuple[str, ...]:
    return (wsl_program(), "-d", DISTRO, "--cd", "/", "--exec")


def own_engine() -> Engine:
    """Daodan's Kiri in its WSL distribution, its daemon started for one operation in a network namespace of its own
    (`DAEMON`), whatever else runs in WSL; a Gap where it cannot run."""
    if os.name != "nt":
        raise Gap("no container engine answers: neither docker nor podman",
                  "install Docker or Podman; Daodan brings its own engine only on Windows")
    wsl_program()  # a Gap without WSL, before anything is downloaded
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
        remove_after, pasta = ensure_distro(home)
        wsl("--terminate", DISTRO)  # what a run that ended without `stop` left: its daemon, pasta, the namespace
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

    engine = Engine(f"daodan-kiri@{KIRI_VERSION}+pasta@{pasta}", (*distro_argv(), "/usr/bin/docker", "-H", SOCKET),
                    stop)
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
        answer = subprocess.run([git, *GIT_OPTIONS, "-C", str(project), "rev-parse", "--is-inside-work-tree"],
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
        listed = subprocess.run([git, *GIT_OPTIONS, "-C", str(project), "ls-files", "-z", "--stage"],
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
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


def dotenv(name: str) -> bool:
    """Whether a file of this name is an `.env` file (`DOTENV`), as Daodan's names are matched: in any case."""
    return any(fnmatch.fnmatchcase(name.lower(), pattern) for pattern in DOTENV)


def example(name: str) -> bool:
    """Whether a file of this name is an example `.env` file the project publishes (`.env.example`,
    `.env.local.sample`: `EXAMPLES`), whose values are no secret (D-291)."""
    return dotenv(name) and name.lower().rsplit(".", 1)[-1] in EXAMPLES


def secret(values: dict[str, dict[str, str]], public=()) -> dict[str, dict[str, str]]:
    """The values of the tracked `.env` files (`dotenv_values`) that are secret: what the masks hide and an output
    must not hold. Those of an `example` file are aside (D-291), and so is a value in `public`, which the project's
    other tracked files hold (`RESOLVE`): the project publishes it (`VERTEX_LOCATION=global` beside
    `globalButtonHaptic.ts`, D-311). A value an example shares with a true file stays, by the true file's
    variable."""
    kept = {path: {name: value for name, value in found.items() if value not in public}
            for path, found in values.items() if not example(posixpath.basename(path))}
    return {path: found for path, found in kept.items() if found}


def _withheld(relative: str, path: Path, mode: int | None) -> dict:
    """The gap of a file the copy leaves out because Daodan never reads it, with the rule its name or content
    meets."""
    pattern = next((glob for glob in FORBIDDEN_GLOBS if fnmatch.fnmatchcase(path.name.lower(), glob)), None)
    rule = f"its name matches {pattern}" if pattern else "its name speaks of secrets and it holds a generated value"
    why = ("Git does not track it, so the CI's checkout has no such file" if mode is None and dotenv(path.name)
           else "only the .env files Git tracks reach the copy")
    return {"kind": "file_withheld", "path": relative,
            "detail": f"{relative} is a file Daodan never reads ({rule}) and {why}: the copy leaves it out, and what "
                      "reads it there finds nothing"}


def carried(project: Path) -> tuple[set[str], list[tuple[str, Path, int | None]], list[tuple[str, Path, str]],
                                    list[dict]]:
    """What the copy of `project` carries (`copy_perimeter`), relative to it: the folders the snapshot perimeter
    walks (`.` the root), the files `(relative, path, mode)`, the `.env` files Git tracks among them, the links Git
    tracks inside it `(relative, path, target)`, and the gaps of what it leaves out: `link_outside`, and
    `file_withheld` for any other file the snapshot never reads."""
    modes = tracked(project)
    folders, files = {"."}, dict.fromkeys(modes)
    for directory, names in Perimeter(project).walk():
        relative = directory.relative_to(project).as_posix()
        folders.add(relative)
        files.update((name if relative == "." else f"{relative}/{name}", None) for name in names)
    kept, links, gaps = [], [], []
    for relative in sorted(files):
        path = project / relative
        mode, sha = modes.get(relative, (None, ""))
        plain = path.is_file() and not path.is_symlink()
        if is_forbidden(path.name, path if plain else None):
            if plain and mode not in (None, LINK) and dotenv(path.name):  # as the CI's checkout holds it
                kept.append((relative, path, mode))
            elif plain or path.is_symlink():
                gaps.append(_withheld(relative, path, mode))
            continue
        link = _link(path, sha) if mode == LINK else None
        if link is not None and _within(relative, link):
            links.append((relative, path, link))
        elif link is not None:
            gaps.append({"kind": "link_outside", "path": relative, "target": link,
                         "detail": f"{relative} is a link Git tracks to {link}, outside the project: the copy leaves "
                                   "it out, and what reads it there finds nothing"})
        elif plain:
            kept.append((relative, path, None if mode == LINK else mode))
    return folders, kept, links, gaps


def copy_perimeter(project: Path, target: Path, inputs: dict[str, Path] | None = None) -> dict:
    """A tar of what a build may need: under `work/`, the files the snapshot perimeter walks and the files Git
    tracks (dot directories included), minus the files the snapshot never reads; `inputs` at their own paths.

    What Git ignores stays out. A tracked file keeps the executable bit Git records, also where the disk has none.
    A link Git tracks whose target lies inside the project is that link in the copy, never followed; one whose
    target lies outside stays out, a `link_outside` gap of the returned `gaps`, which the run's result carries.
    The `.env` files Git tracks are in it, `dotenv` naming them, and `published` the other files Git tracks, where
    their values may stand (`dotenv_values`); any other file the snapshot never reads is a `file_withheld` gap.
    """
    walked, files, tracked_links, gaps = carried(project)
    secrets = [relative for relative, path, _ in files if dotenv(path.name)]
    published = [relative for relative, path, mode in files if mode is not None and not dotenv(path.name)]
    folders = {"work", *(f"work/{folder}" for folder in walked if folder != ".")}
    kept = [(f"work/{relative}", path, mode) for relative, path, mode in files]
    links = [(f"work/{relative}", path, link) for relative, path, link in tracked_links]
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
                "sha256": hashlib.file_digest(handle, "sha256").hexdigest(), "gaps": gaps,
                **({"dotenv": secrets, "published": published} if secrets else {})}


def named(root: str = WORKDIR, values: str | None = None) -> str:
    """POSIX sh that writes in each `.env` file under `root`, the copy in a container, a placeholder in place of
    each value naming the file and the variable, `./daodan-dotenv-<file>-<name>` both in hexadecimal (no colon or
    brace a short syntax of Compose splits on; a path, so a volume's source stays a bind mount), which a tool
    interpolates as it would the value; comments
    and blank lines stay, any other line goes (the rest of a value over several). The pre-map's commands run after
    it (`run_commands`): what they print holds no value of those files. With `values`, a path outside the copy,
    the files' values are written there first (`RESOLVE`, by file), once: the container's own, never an output,
    for Daodan's helper that resolves a placeholder to a path of the checkout (`docker_build`), in its container
    alone (`run_commands`' `values`), where no code of the project runs."""
    awk = ('function hex(s, out, i) { out = ""; for (i = 1; i <= length(s); i++) '
           'out = out sprintf("%02x", ord[substr(s, i, 1)]); return out } '
           'BEGIN { for (i = 1; i < 256; i++) ord[sprintf("%c", i)] = i; file = hex(ENVIRON["REL"]) } '
           '/^[ \\t]*(#.*)?$/ { print; next } '
           'match($0, /^[ \\t]*(export[ \\t]+)?[A-Za-z_][A-Za-z0-9_.-]*[ \\t]*=/) { head = substr($0, 1, RLENGTH); '
           'name = head; sub(/^[ \\t]*(export[ \\t]+)?/, "", name); sub(/[ \\t]*=$/, "", name); '
           'print head "./daodan-dotenv-" file "-" hex(name) }')
    found = "find . -type f \\( -iname .env -o -iname '.env.*' \\)"
    into = shlex.quote(values or "")
    kept = "" if values is None else (
        f"[ -e {into} ] || {{ mkdir -p {shlex.quote(posixpath.dirname(values))} && (cd {shlex.quote(root)} && "
        f"DAODAN_RESOLVE={shlex.quote(RESOLVE)} {found} -exec sh -c 'exec python3 -c \"$DAODAN_RESOLVE\" \"$@\"' sh "
        f"{{}} +) | sed -n 's/^@@daodan-dotenv //p' > {into}; "
        f"[ -s {into} ] || echo '{{}}' > {into}; }}\n")
    return kept + (f"find {shlex.quote(root)} -type f \\( -iname .env -o -iname '.env.*' \\) | while IFS= read -r f; "
                   f"do REL=\"${{f#{root}/}}\" awk '{awk}' \"$f\" > \"$f.daodan\" && mv -f \"$f.daodan\" \"$f\"; done\n")


def dotenv_values(run: Callable, copy: Path, files: list[str], token: str,
                  tracked: list[str] = ()) -> tuple[dict[str, dict[str, str]], set[str]]:
    """The variables of the tracked `.env` files of the copy (`files`, relative to the project), by file, and the
    values the project's other tracked files (`tracked`) hold, which it publishes (`secret`): read in a container
    of Daodan's, `RESOLVE` in the proxy's image with no network, over those files alone at their place under /work,
    within `PUBLIC_SECONDS`; `run` is the engine's command line. The values live in the run, for the services that
    name them (`filled`) and the masks (`masker`), never on record. RuntimeError when the container does not
    answer."""
    box = f"daodan-dotenv-{token}"
    try:
        checked(run("create", "--name", box, "--network", "none", "--memory", str(64 * 2**20), "--pids-limit", "16",
                    "--security-opt", "no-new-privileges", "-e", f"DAODAN_PUBLIC={PUBLIC_SECONDS}", "-w", WORKDIR,
                    PROXY_IMAGE, "python3", "-c", RESOLVE, *files), "create of the reader of the .env files")
        with bound(copy, [[rel, f"{WORKDIR}/{rel}"] for rel in (*files, *tracked)]) as handle:
            checked(run("cp", "-", f"{box}:/", stdin=handle), "cp of the .env files")
        said = run("start", "-a", box, timeout=PUBLIC_SECONDS + 120)
    finally:
        run("rm", "-f", box)
    text = said.stdout.decode("utf-8", "replace")
    return dotenv_answer(text, said.returncode), published(text)


def dotenv_answer(stdout: str, code: int | None) -> dict[str, dict[str, str]]:
    """`RESOLVE`'s answer, the line its mark begins; RuntimeError, saying nothing of what it printed, without one."""
    for line in stdout.splitlines():
        if line.startswith("@@daodan-dotenv "):
            return json.loads(line[len("@@daodan-dotenv "):])
    raise RuntimeError(f"the reader of the tracked .env files answered with code {code} and no values: the run, which "
                       "could not mask them in what it keeps, does not start")


def published(stdout: str) -> set[str]:
    """The values `RESOLVE` found in the project's other files (`DAODAN_PUBLIC`), none without its line."""
    for line in stdout.splitlines():
        if line.startswith("@@daodan-public "):
            return set(json.loads(line[len("@@daodan-public "):]))
    return set()


def _labels(values: dict[str, dict[str, str]]) -> dict[str, list[str]]:
    """Each value `masker` masks, with the `<file>:<name>` of the variables that hold it."""
    labels: dict[str, list[str]] = {}
    for path, found in values.items():
        for name, value in found.items():
            if len(value) >= 4 and not UNMASKED.fullmatch(value):
                labels.setdefault(value, []).append(f"{path}:{name}")
    return labels


def _short(values: dict[str, dict[str, str]]) -> tuple[dict[str, list[str]], list[str]]:
    """The values shorter than four characters `masker` masks only where they stand whole, with the variables that
    hold them, and the variables whose value it does not mask (a boolean word, a number of five digits at most)."""
    short: dict[str, list[str]] = {}
    unmasked = []
    for path, found in values.items():
        for name, value in found.items():
            if value and UNMASKED.fullmatch(value):
                unmasked.append(f"{path}:{name}")
            elif 0 < len(value) < 4:
                short.setdefault(value, []).append(f"{path}:{name}")
    return short, unmasked


def partial(values: dict[str, dict[str, str]]) -> list[dict]:
    """The gap that says once which values of the tracked `.env` files a run may keep (`_short`), none without."""
    short, unmasked = _short(values)
    whole = sorted(label for said in short.values() for label in said)
    if not whole and not unmasked:
        return []

    def named(labels: list[str]) -> str:
        return f"value{'s' if len(labels) > 1 else ''} of {', '.join(sorted(labels))}"

    said = [f"masks the {named(whole)}, shorter than four characters, only where "
            f"{'they stand' if len(whole) > 1 else 'it stands'} as a whole word"] if whole else []
    said += [f"does not mask {'those of ' + ', '.join(sorted(unmasked)) if whole else 'the ' + named(unmasked)}, a "
             "boolean word or a number of five digits at most"] if unmasked else []
    return [{"kind": "mask_partial", "variables": sorted([*whole, *unmasked]),
             "detail": f"Daodan {', and '.join(said)}: what the run keeps may hold them"}]


def masker(values: dict[str, dict[str, str]]) -> Callable[[str], str] | None:
    """A text with each value of the tracked `.env` files (`dotenv_values`) replaced by `[<file>:<name>]`, the names
    of all that hold it, wherever it stands, inside a longer word too; the longer first. One shorter than four
    characters only where it stands whole, as it would mask the text's own words inside longer ones; a boolean word
    or a number of five digits at most stays, as the text's own words and ports would be masked with it (`partial`
    says so). None when no value is masked."""
    short = _short(values)[0]
    labels = {**_labels(values), **short}
    if not labels:
        return None

    def whole(value: str) -> str:
        edge = r"[A-Za-z0-9_]"
        return ((f"(?<!{edge})" if re.fullmatch(edge, value[0]) else "") + re.escape(value)
                + (f"(?!{edge})" if re.fullmatch(edge, value[-1]) else ""))

    pattern = re.compile("|".join(whole(value) if value in short else re.escape(value)
                                  for value in sorted(labels, key=len, reverse=True)))
    return lambda text: pattern.sub(lambda found: f"[{','.join(sorted(labels[found.group()]))}]", text)


def mask_file(path, hide: Callable[[str], str] | None) -> None:
    """A text file of the run written again with `hide`'s masks (`masker`), its bytes otherwise as they were."""
    if hide and path and Path(path).is_file():
        text = Path(path).read_bytes().decode("utf-8", "surrogateescape")
        masked = hide(text)
        if masked != text:
            Path(path).write_bytes(masked.encode("utf-8", "surrogateescape"))


def _mask_json(path: Path, hide: Callable[[str], str]) -> None:
    """A JSON output written again with `hide`'s masks in each of its strings, keys too, so it stays JSON whatever
    escapes a value takes there, and in each number, which becomes the string of its mask where one holds a value;
    one that is not JSON is masked as text."""
    try:
        document = json.loads(path.read_bytes())
    except ValueError:
        return mask_file(path, hide)

    def masked(item):
        if isinstance(item, str):
            return hide(item)
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            return said if (said := hide(json.dumps(item))) != json.dumps(item) else item
        if isinstance(item, list):
            return [masked(part) for part in item]
        return {hide(key): masked(part) for key, part in item.items()} if isinstance(item, dict) else item

    if (written := masked(document)) != document:
        path.write_bytes((json.dumps(written, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def scrubbed(paths: list[str], hide: Callable[[str], str] | None, values: dict[str, dict[str, str]],
             root) -> tuple[list[str], list[dict]]:
    """The outputs `paths` a run keeps, with no secret value of the tracked `.env` files (`secret`) in them. Text is
    masked as the logs are and kept, a text output or what a command printed (`STREAMS`), a JSON one string by
    string and number by number (`_mask_json`): a result is never destroyed for a coincidence. Any other output
    whose bytes hold a value (an index, an object file) is never patched: it is removed, and a gap names it by its
    path under `root` and the variables that hold the value."""
    labels = _labels(values) if hide else {}
    if not labels:
        return list(paths), []
    kept, gaps = [], []
    for item in paths:
        path = Path(item)
        if path.is_file() and (path.name.endswith(TEXTS) or path.name in STREAMS):
            mask_file(path, hide)
        elif path.is_file() and path.name.endswith(JSONS):
            _mask_json(path, hide)
        data = path.read_bytes() if path.is_file() and path.suffix not in (*TEXTS, *JSONS) and (
            path.name not in STREAMS) else b""
        names = sorted({label for value, said in labels.items() if value.encode("utf-8") in data for label in said})
        if not names:
            kept.append(item)
            continue
        path.unlink()
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.name
        gaps.append({"kind": "output_withheld", "path": rel, "variables": names,
                     "detail": f"{rel} holds the value of {', '.join(names)}, which Daodan keeps nowhere: the output "
                               "is not kept"})
    return kept, gaps


def mask_row(row: dict, hide: Callable[[str], str] | None) -> dict:
    """`row` with what the run printed in it, its `cause` and an engine's answer, masked in place (`masker`)."""
    for key in ("cause", "commit_failed"):
        if hide and isinstance(row.get(key), str):
            row[key] = hide(row[key])
    return row


def filled(service: dict, values: dict[str, dict[str, str]]) -> dict:
    """A service whose `dotenv` names the tracked `.env` file of each variable it reads, with each value in place
    of its `${NAME}` (`MARKER`), as Compose interpolates it, in its variables, options and command: only in the run
    that starts it."""
    names = service.get("dotenv") or {}
    if not names:
        return service

    def put(text: str) -> str:
        return MARKER.sub(lambda found: values.get(names[found.group(1)], {}).get(found.group(1), found.group())
                          if found.group(1) in names else found.group(), str(text))

    return {**service, "env": {key: put(value) for key, value in (service.get("env") or {}).items()},
            "args": [put(arg) for arg in service.get("args") or ()],
            "command": [put(word) for word in service.get("command") or ()]}


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


def record_volumes(entry: Path, engine: str, pid: int, names: list[str], images: list[str] = ()) -> None:
    entry.parent.mkdir(parents=True, exist_ok=True)
    partial = entry.with_suffix(".partial")
    partial.write_text(json.dumps({"engine": engine, "pid": pid, "volumes": names,
                                   **({"images": list(images)} if images else {})}), encoding="utf-8")
    os.replace(partial, entry)


def remove_volumes(engine: Engine, entry: Path, pid: int, names: list[str], images: list[str] = ()) -> None:
    """Each volume and image removed by name; the entry keeps only those still there, and goes when none is."""
    left = [name for name in names if cli(engine, "volume", "rm", name).returncode != 0
            and cli(engine, "volume", "inspect", name).returncode == 0]
    kept = [name for name in images if cli(engine, "image", "rm", "-f", name).returncode != 0
            and cli(engine, "image", "inspect", name).returncode == 0]
    if left or kept:
        record_volumes(entry, engine.name, pid, left, kept)
    else:
        entry.unlink(missing_ok=True)


def sweep(engine: Engine) -> None:
    """The volumes and kept images of this engine on record for a process that has ended, removed by name."""
    folder = volume_registry()
    for entry in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            held = json.loads(entry.read_text(encoding="utf-8"))
            if held["engine"] != engine.name or _process_alive(held["pid"]):
                continue
            names = [name for name in held["volumes"] if isinstance(name, str) and VOLUME_NAME.fullmatch(name)]
            images = [name for name in held.get("images") or () if isinstance(name, str)
                      and IMAGE_NAME.fullmatch(name)]
        except (OSError, ValueError, KeyError, TypeError):
            continue
        remove_volumes(engine, entry, held["pid"], names, images)


def phase(engine: Engine, name: str, *, image: str, command: list[str], network: str, env: dict[str, str],
          limits: dict, timeout: float, copy: Path | None, outputs: list[str], out_dir: Path,
          volumes: list[str] = (), commit: str | None = None) -> dict:
    """One container from create to rm, with the `name:path` volumes mounted: its record, with the outputs
    brought back; with `commit`, a container that exited with 0 is first committed as that image (`committed`
    in the record, or `commit_failed` with the engine's answer)."""
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
        if commit and row["outcome"] == "exited" and row["exit_code"] == 0:
            done = cli(engine, "commit", box, commit)
            if done.returncode == 0:
                row["committed"] = commit
            else:
                row["commit_failed"] = (done.stderr or done.stdout or b"").decode("utf-8", "replace").strip()[-400:]
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


class Said(NamedTuple):
    """What the runs within `beside` say: each run's `services` and `ci_steps`, wherever its record lies."""
    services: list
    ci_steps: list


@contextlib.contextmanager
def beside(services: list[dict], env: dict[str, str], steps: list[dict] = ()):
    """Within it every `run_in_container` starts `services` in the pod its execution joins, gives both phases
    `env` under its caller's variables and runs `steps` at the end of its preparation: the dynamic step's, so the
    tests of every observer get the services the project's CI declares, the variables its jobs give them and the
    steps its jobs run before them. Each service is `{name, image, host, env, args, command}` (`args` options of
    `create`, `command` the image's command replaced when not empty), with `aliases`, `wait`, `after` and `files`
    where it has them (`start_services`); the pod's hosts name 127.0.0.1 for a `host` or an alias other than
    localhost (the module's docstring). Each step is `{declared_in, cwd, run}`, with `name`, `env` and `shell`
    where it has them (`steps_script`). It yields a `Said` each run within extends with its result's `services`
    and `ci_steps`."""
    said = Said([], [])
    token = BESIDE.set((list(services), dict(env), list(steps), said))
    try:
        yield said
    finally:
        BESIDE.reset(token)


def steps_script(steps: list[dict], limit: float, token: str) -> str:
    """POSIX sh that runs its arguments (a preparation), then each of `steps` as GitHub's runner runs a `run:` step:
    in its folder under the copy, with `CI=true` and its variables, by its shell (`bash -e`, else `sh -e`, as GitHub
    picks one when the step names none), all of them within `limit` seconds (coreutils' or BusyBox's `timeout`,
    where the image has one); a step that fails does not stop the next. Each step's output lies between two lines of
    `token` that `stepped` reads: its code and its seconds."""
    mark = f"@@daodan-step-{token}"
    lines = ['( "$@" ) || exit $?',
             'if command -v timeout >/dev/null 2>&1; then b() { timeout -k 10 "$@"; }; else b() { shift; "$@"; }; fi',
             'if command -v bash >/dev/null 2>&1; then SH="bash -e"; else SH="sh -e"; fi',
             f"D=$(( $(date +%s) + {int(limit)} ))"]
    for number, step in enumerate(steps):
        exports = "".join(f"export {key}={shlex.quote(str(value))}; "
                          for key, value in {"CI": "true", **(step.get("env") or {})}.items()
                          if IDENTIFIER.fullmatch(str(key)))
        shell = STEP_SHELLS[step.get("shell")]
        lines += [f"s=$(date +%s); l=$((D - s)); echo {mark} begin {number}",
                  f'if [ "$l" -gt 0 ]; then ( cd {shlex.quote(step.get("cwd") or ".")} || exit; {exports}'
                  f'b "$l" {shell} -c {shlex.quote(step["run"])} ) </dev/null; c=$?; e=$(( $(date +%s) - s )); '
                  'if [ "$c" -eq 124 ] || { [ "$c" -gt 128 ] && [ "$e" -ge "$l" ]; }; then c=timeout; fi; '
                  'else c=timeout; e=0; fi',
                  f"echo {mark} end {number} $c $e"]
    return "\n".join(lines) + "\nexit 0\n"


def stepped(text: str, steps: list[dict], token: str, limit: float) -> list[dict]:
    """The record rows of `steps` from a preparation's output `text` (`steps_script`): each `{phase, declared_in,
    name, outcome, exit_code, duration_seconds}`, `outcome` `exited`, `timeout` (it did not end in the `limit`
    seconds the steps have, or found none left) or `not_run` (the preparation ended before it), with `cause`
    where it is not a code 0 (its output's last lines)."""
    mark, ended, output, current = f"@@daodan-step-{token} ", {}, {}, None
    for line in text.splitlines():
        if line.startswith(mark):
            words = line[len(mark):].split()
            if words[:1] == ["begin"] and len(words) == 2 and words[1].isdigit():
                current = int(words[1])
                output[current] = []
            elif words[:1] == ["end"] and len(words) == 4 and words[1].isdigit() and words[3].isdigit():
                ended[int(words[1])], current = (words[2], int(words[3])), None
        elif current is not None:
            output[current].append(line.strip())
    rows = []
    for number, step in enumerate(steps):
        row = {"phase": "ci_step", "declared_in": step["declared_in"], **({"name": step["name"]} if step.get("name")
                                                                          else {})}
        tail = " | ".join(line for line in output.get(number, ()) if line)[-400:]
        code, seconds = ended.get(number, (None, 0))
        if code is None:
            row.update(outcome="not_run", exit_code=None, duration_seconds=0,
                       cause="the preparation ended " + ("while it ran" if number in output else "before it ran"))
        elif code == "timeout":
            row.update(outcome="timeout", exit_code=None, duration_seconds=seconds,
                       cause=f"it did not end in the {int(limit)} s the steps have before the tests"
                             + (f": {tail}" if tail else ""))
        else:
            row.update(outcome="exited", exit_code=int(code), duration_seconds=seconds)
            if row["exit_code"] != 0:
                row["cause"] = f"it exited with code {code}" + (f": {tail}" if tail else "")
        rows.append(row)
    return rows


def leaves(run: Callable, network: str, token: str) -> str | None:
    """None when the engine takes a container off its first network, as the pod leaves the preparation's before
    the tests; otherwise the engine's answer (Kiri 0.2.0 refuses: crates/kiri/src/daemon/engine.rs:2357)."""
    box = f"daodan-probe-{token}"
    try:
        checked(run("create", "--name", box, "--network", network, PROXY_IMAGE, "true"), "create of the probe")
        answer = run("network", "disconnect", network, box)
        said = (answer.stderr or answer.stdout or b"").decode("utf-8", "replace").strip()
        return None if answer.returncode == 0 else said[-300:] or f"code {answer.returncode}"
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        return str(error)
    finally:
        run("rm", "-f", box)


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


def exposed(run: Callable, image: str) -> list[str]:
    """The TCP ports `image` exposes (`EXPOSE`), which GitLab's runner waits for."""
    answer = run("image", "inspect", "--format", "{{json .Config.ExposedPorts}}", image, timeout=120)
    ports = json.loads(answer.stdout or "null") if answer.returncode == 0 else None
    return sorted((key.split("/")[0] for key in ports or {} if key.endswith("/tcp")), key=int)


def reached(run: Callable, network: str, ports: list[str]) -> bool:
    """Whether each of `ports` accepts a connection at the localhost of `network`, asked from a container of the
    pod's own image in it, as GitLab's runner asks from a container beside the service."""
    try:
        return run("run", "--rm", "--network", network, "--memory", str(64 * 2**20), "--pids-limit", "16",
                   "--security-opt", "no-new-privileges", PROXY_IMAGE, "python3", "-c", REACH, *ports,
                   timeout=60).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def bound(copy: Path, files: list[list[str]]):
    """A tar of the project's files a service's bind mounts name (`files`, each `[source in the project, target]`),
    from the copy's `work/` (`copy_perimeter`), each at its target: an empty folder for a source the copy does not
    hold, as the engine makes one for a bind mount's missing source."""
    out = tempfile.TemporaryFile()
    with tarfile.open(copy) as source, tarfile.open(fileobj=out, mode="w") as target:
        members = source.getmembers()
        by_name = {member.name: member for member in members}  # a file at once, a folder by its members
        for origin, destination in files:
            prefix, root = posixpath.normpath(posixpath.join("work", origin)), destination.strip("/")
            one = by_name.get(prefix)
            held = [one] if one is not None and not one.isdir() else [
                member for member in members if member.name == prefix or member.name.startswith(prefix + "/")]
            for member in held:
                target.addfile(member.replace(name=root + member.name[len(prefix):], deep=False),
                               source.extractfile(member) if member.isfile() else None)
            if not held:
                folder = tarfile.TarInfo(root)
                folder.type, folder.mode = tarfile.DIRTYPE, 0o755
                target.addfile(folder)
    out.seek(0)
    return out


def _settle(run: Callable, item: dict, network: str) -> None:
    """`item`'s service awaited until its row has an outcome (`start_services`)."""
    row, box = item["row"], item["box"]

    def failed(cause: str) -> None:
        logs = run("logs", "--tail", "5", box, timeout=60)
        tail = " | ".join(line.strip() for line in (logs.stdout + logs.stderr).decode("utf-8", "replace").splitlines()
                          if line.strip())
        row.update(outcome="failed", cause=f"{cause}: {tail[-400:]}" if tail else cause)

    while "outcome" not in row:
        if item["every"] is not None and time.monotonic() >= item["due"]:
            run("healthcheck", "run", box, timeout=120)  # its code is the check's: the state says it
            item["due"] = time.monotonic() + item["every"]
        said = run("inspect", "--format", SERVICE_STATE, box, timeout=60).stdout.decode("utf-8", "replace")
        status, _, health = said.strip().partition(" ")
        late = time.monotonic() - item["clock"] > SERVICE_WAIT
        if item["once"] and status == "exited":  # one another service waits for to complete
            code = run("inspect", "--format", "{{.State.ExitCode}}", box, timeout=60).stdout.decode().strip()
            if code == "0":
                row["outcome"] = "ready"
            else:
                failed(f"it exited with code {code}")
        elif item["once"] and status == "running":
            if late:
                row.update(outcome="failed", cause=f"still running after {SERVICE_WAIT} s: it never completed")
            else:
                time.sleep(1)
        elif status == "running" and health in ("", "healthy"):
            if item["wait"] == "ports" and item["ports"] is None:
                item["ports"] = exposed(run, row["pinned"])
            if not item["ports"] or reached(run, network, item["ports"]):
                row["outcome"] = "ready"
            elif late:
                row.update(outcome="failed", cause=f"its ports {' '.join(item['ports'])} accepted no connection in "
                                                   f"{SERVICE_WAIT} s")
            else:
                time.sleep(1)
        elif status != "running" or health == "unhealthy":
            failed("its health check failed" if status == "running" else f"it {status or 'is gone'}")
        elif late:
            row.update(outcome="failed", cause=f"still {health} after {SERVICE_WAIT} s: its health check never "
                                               "passed")
        else:
            time.sleep(1)
    row.setdefault("duration_seconds", round(time.monotonic() - item["clock"], 3))


def start_services(run: Callable, services: list[dict], network: str, limits: dict, token: str,
                   scheduled: bool = True, copy: Path | None = None, created: bool = False) -> list[dict]:
    """The pinned `services` (`beside`'s, each with `pinned`) created in `network` and started, then
    awaited as GitHub's runner awaits a service container: ready once running, or once healthy where it has a
    health check, and with `wait` `ports` once the ports its image exposes accept a connection (GitLab's runner,
    `exposed`, `reached`); failed, with the cause, when it stops, turns unhealthy or is still waited for after
    `SERVICE_WAIT` seconds. As Compose's `up` starts them, each starts after those its `after` names have met the
    condition it gives (`CONDITIONS`): started, ready, or, for one another waits for to complete, exited with code
    0; one whose dependency failed does not start. A service's `files` are put in it from the project's `copy`
    (`bound`) before it starts. The containers are `daodan-svc-<token>-<n>`, `n` the service's place in `services`;
    a record row each, in that order. `run(*args, timeout=..., stdin=...)` is the engine's command line. `scheduled`
    False is an engine that may run no check by itself (Podman, on systemd's timers): each check runs from here
    (`healthcheck run`) at its interval, the engine's timer off, its retries counted by the engine. `created`:
    the containers are there from an earlier start (the benchmark driver's, beside the CI's steps), and start
    again as they were, a service another waited for to complete counted ready without running again."""
    index = {service["name"]: number for number, service in enumerate(services)}
    once = {name for service in services for name, condition in (service.get("after") or {}).items()
            if condition == "service_completed_successfully"}
    order: list[int] = []

    def visit(number: int, seen: set) -> None:  # those it depends on first, as Compose orders them
        if number in seen:
            return
        seen.add(number)
        for name in services[number].get("after") or ():
            if name in index:
                visit(index[name], seen)
        order.append(number)

    visited: set = set()
    for number in range(len(services)):
        visit(number, visited)
    items: dict[int, dict] = {}
    for number in order:
        service, box = services[number], f"daodan-svc-{token}-{number}"
        row = {"phase": "service", "name": service["name"], "image": service["image"], "pinned": service["pinned"],
               "network": network}
        items[number] = item = {"row": row, "box": box, "every": None, "due": 0.0, "wait": service.get("wait"),
                                "once": service["name"] in once, "ports": None, "clock": time.monotonic()}
        for name, condition in (service.get("after") or {}).items():
            other = items.get(index.get(name, -1))
            if other is None:  # not among them: `up --no-deps`, or one of a cycle
                continue
            if condition != "service_started":
                _settle(run, other, network)
            if other["row"].get("outcome") == "failed":
                row.update(outcome="failed", cause=f"it waits for {name} {CONDITIONS.get(condition, 'to start')}, "
                                                   "which failed", duration_seconds=0)
                break
        row["started_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if created and item["once"]:
            row.update(outcome="ready", duration_seconds=0)  # it completed in the earlier start
        if "outcome" in row:
            continue
        item["clock"] = time.monotonic()
        env = [word for key, value in (service.get("env") or {}).items() for word in ("-e", f"{key}={value}")]
        args = list(service.get("args", ()))
        if not scheduled and "--health-cmd" in args and "--no-healthcheck" not in args:
            at = args.index("--health-interval") + 1 if "--health-interval" in args[:-1] else None
            item["every"] = seconds(args[at], HEALTH_EVERY) if at else HEALTH_EVERY
            item["due"] = item["clock"]  # Podman runs a check as soon as the container starts, then at each interval
            args = [*args[:at], "disable", *args[at + 1:]] if at else [*args, "--health-interval", "disable"]
        try:
            if not created:
                checked(run("create", "--name", box, "--network", network, "--memory", str(limits["memory"]),
                            "--memory-swap", str(limits["memory"]), "--pids-limit", str(limits["pids"]),
                            "--security-opt", "no-new-privileges", *env, *args, service["pinned"],
                            *service.get("command", ())), "create")
            if service.get("files") and not created:
                if copy is None:
                    raise RuntimeError("its bind mounts name files of the project, and the run has no copy of it")
                with bound(copy, service["files"]) as files:
                    checked(run("cp", "-", f"{box}:/", stdin=files), "cp of its files")
            checked(run("start", box), "start")
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            row.update(outcome="failed", cause=str(error))
    for number in order:
        _settle(run, items[number], network)
    return [items[number]["row"] for number in range(len(services))]


def start_pod(engine: Engine, services: list[dict], network: str, token: str, seconds: float,
              cleanup: list) -> tuple[str | None, str | None]:
    """The pod of `services`: a container that holds their network namespace on `network` (`none` for the tests
    alone, the preparation's internal one while the CI's steps run beside them), with a host per name they are
    reached by, started; its removal and theirs put first in `cleanup`. `(pod, None)`, or `(None, cause)`."""
    pod = f"daodan-pod-{token}"
    cleanup[:0] = [*(("rm", "-f", f"daodan-svc-{token}-{n}") for n in range(len(services))), ("rm", "-f", pod)]
    hosts = sorted({f"--add-host={name}:127.0.0.1" for s in services
                    for name in (s.get("host"), *s.get("aliases", ())) if name not in (None, "localhost")})
    try:
        checked(cli(engine, "create", "--name", pod, "--network", network, *hosts, "--memory", str(64 * 2**20),
                    "--pids-limit", "16", PROXY_IMAGE, "sleep", str(int(seconds) + 600)), "create of the pod")
        checked(cli(engine, "start", pod), "start of the pod")
        return pod, None
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        return None, str(error)


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
                     inputs: dict[str, Path] | Callable[[], dict[str, Path]] | None = None,
                     keep_root: bool = False, dotenv_env: list[tuple[str, str]] = (), blind: bool = False) -> dict:
    """Run `command` in a container over a copy of `project`; `prepare` first, with the registries open.

    `inputs` maps a container path to a host file the copy carries there, or is a function returning that map,
    called once an engine answers, which may raise Gap. With `prepare`, inputs lie under /work or /daodan/state
    and outputs outside them (the engine copies no file out of a volume): ValueError otherwise. `engine` is an
    Engine, "daodan" for Daodan's own, or None to find one. Within `beside`, its services start in the pod the
    execution joins and its variables reach both phases under `env`. The result's `state` is
    `done` (the command exited, `exit_code` says how), `timeout`, `failed` (with `cause`) or `gap`
    (with `cause` and `remedy`); `outputs` lists the files brought back into `out_dir`; `services`, with
    services, each `{name, image, pinned, outcome}`, `outcome` `ready` or `failed` with `cause`: the execution
    runs without a service that failed. Within `beside` with steps, they run at the end of the preparation
    (`steps_script`), with the services beside them where the engine takes the pod off the preparation's network
    before the execution (`leaves`); `ci_steps` gives each one's `{declared_in, name, outcome, exit_code,
    duration_seconds, cause}` (`stepped`). `dotenv_env`, `(name, file)` of tracked .env files, reach both phases
    with their values (`dotenv_values`), never on record and masked in what the run keeps: a Dockerfile stage's
    ARG, in the environment of every RUN after it, as BuildKit gives it. With `keep_root`, execution starts from
    everything the preparation wrote
    (a Dockerfile's build stage installs into the image's own folders: `docker_build.py`): its container committed
    as `daodan-prepared-<token>`, on record before it exists and removed by name as the volumes are; an engine that
    does not commit it is a gap with its answer. `blind`: the command never sees a value of the tracked .env files
    (`run_commands`, over their placeholders): without services or `dotenv_env`, which take the values, none is
    read, and what the run keeps is neither masked nor withheld.
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
    services, variables, steps, said = BESIDE.get() or ((), {}, (), Said([], []))
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
    kept_image: str | None = None  # `keep_root`'s image, on record with the volumes
    hide: Callable[[str], str] | None = None  # the masks of the tracked .env files' values (`masker`)
    result = {"state": "failed", "exit_code": None, "outputs": [], "record": str(record), "engine": found.name}
    try:
        sweep(found)

        def engine_cli(*args: str, timeout: float = 300, stdin=None) -> subprocess.CompletedProcess:
            return cli(found, *args, timeout=timeout, stdin=stdin)

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
            values, public = dotenv_values(engine_cli, copy, digest["dotenv"], token, digest["published"]) if (
                digest.get("dotenv") and not (blind and not services and not dotenv_env)) else ({}, set())
            hidden_values = secret(values, public)  # not an example's, nor a value the project publishes
            hide = masker(hidden_values)
            if said_partial := partial(hidden_values):  # what the masks leave, said once
                result["gaps"] = [*(result.get("gaps") or ()), *said_partial]
            pinned = [filled(item, values) for item in pinned]  # the values only here, never on record
            exported = {name: values[file][name] for name, file in dotenv_env if name in values.get(file, {})}
            run_copy, mounts, env = copy, [], {"HOME": HOME, **(env or {})} if prepare else dict(env or {})
            joined, said_steps, steps = None, [], list(steps)

            def hidden(row: dict) -> dict:  # what the run printed, masked in its log, its outputs and its row
                mask_file(row.get("log"), hide)
                if row.get("outputs"):
                    row["outputs"], withheld = scrubbed(row["outputs"], hide, hidden_values, out_dir)
                    result["gaps"] = [*(result.get("gaps") or ()), *withheld]
                return mask_row(row, hide)

            def unrun(cause: str) -> list[dict]:
                return [{"phase": "ci_step", "declared_in": step["declared_in"],
                         **({"name": step["name"]} if step.get("name") else {}), "outcome": "not_run",
                         "exit_code": None, "duration_seconds": 0, "cause": cause} for step in steps]

            def tell() -> None:  # the steps' rows, and what the dynamic step reads of them
                for item in said_steps:
                    append_record(record, {**mask_row(item, hide), "engine": found.name})
                if said_steps:
                    result["ci_steps"] = [{key: value for key, value in item.items() if key != "phase"}
                                          for item in said_steps]
                    said.ci_steps.extend(result["ci_steps"])

            def unstarted(cause: str) -> list[dict]:
                return [{"phase": "service", "name": s["name"], "image": s["image"], "pinned": s["pinned"],
                         "outcome": "failed", "cause": cause} for s in pinned]

            def report() -> None:  # the services' rows, and what the dynamic step reads of them
                for item in served:
                    append_record(record, {**mask_row(item, hide), "engine": found.name})
                if services:
                    result["services"] = [{key: item[key] for key in ("name", "image", "pinned", "outcome", "cause")
                                           if key in item} for item in served]
                    said.services.extend(result["services"])

            if steps and not prepare:  # they run at the end of a preparation, which this run has not
                said_steps, steps = unrun("the run has no preparation, at whose end Daodan runs the CI's steps"), []
                tell()
            if prepare:
                names = [f"daodan-work-{token}", f"daodan-state-{token}"]
                kept_image = f"daodan-prepared-{token}" if keep_root else None
                held = (volume_registry() / f"{token}.json", names)
                record_volumes(held[0], found.name, os.getpid(), names, [kept_image] if kept_image else ())
                for name in names:
                    checked(cli(found, "volume", "create", name), "volume create")
                mounts = [f"{names[0]}:{WORKDIR}", f"{names[1]}:{STATE}"]
                network, proxy = f"daodan-net-{token}", f"daodan-proxy-{token}"
                checked(cli(found, "network", "create", "--internal", network), "network create")
                cleanup += [("rm", "-f", proxy), ("network", "rm", network)]
                start_proxy(found, proxy, network, tuple(registries))
                refused = leaves(engine_cli, network, token) if steps and pinned else None
                if refused:  # the pod could not leave the network: no step runs beside the services
                    said_steps, steps = unrun(f"{found.name} cannot take the pod of the services off the preparation's "
                                              f"network before the tests, so no step runs beside them: {refused}"), []
                elif steps and pinned:  # the services first, in a pod on the preparation's network
                    pod, failure = start_pod(found, pinned, network, token, prepare_timeout + 2 * timeout, cleanup)
                    if pod:
                        joined = f"container:{pod}"
                        served += start_services(engine_cli, pinned, joined, limits, token, found.name != "podman",
                                                 copy)
                    else:
                        served, pinned = served + unstarted(failure), []
                row = phase(found, "prepare", image=image, network=joined or network,
                            command=["sh", "-c", steps_script(steps, timeout, token), "sh", *prepare] if steps
                            else prepare, env={**env, **exported, **proxy_environment(f"http://proxy:{PROXY_PORT}")},
                            limits=limits, timeout=prepare_timeout + (timeout if steps else 0), copy=copy, outputs=[],
                            out_dir=out_dir, volumes=mounts, commit=kept_image)
                append_record(record, {**hidden(row), "copy": digest})
                if steps:
                    log = Path(row["log"]).read_bytes().decode("utf-8", "replace") if row.get("log") else ""
                    said_steps = stepped(log, steps, token, timeout)
                tell()
                if row["outcome"] != "exited" or row["exit_code"] != 0:
                    result["cause"] = row.get("cause") or (f"preparation {row['outcome']}" + (
                        f" with code {row['exit_code']}" if row["exit_code"] is not None else "") + f"; see {row['log']}")
                    report()
                    return result
                if kept_image and "committed" not in row:
                    raise Gap(f"{found.name} did not commit the preparation's container: {row.get('commit_failed')}",
                              "run Daodan with an engine that commits a container (Docker, Podman)")
                run_copy, based, image = None, image, kept_image or image
                if joined:  # the proxy goes and the pod leaves the network: the tests reach the services, and only them
                    checked(cli(found, "rm", "-f", proxy), "rm of the proxy")
                    checked(cli(found, "network", "disconnect", network, joined.partition(":")[2]),
                            "network disconnect of the pod")
            if pinned and joined is None:
                pod, failure = start_pod(found, pinned, "none", token, timeout, cleanup)
                if pod:
                    joined = f"container:{pod}"
                    served += start_services(engine_cli, pinned, joined, limits, token, found.name != "podman", copy)
                else:
                    served += unstarted(failure)
            joined = joined or "none"
            report()
            row = phase(found, "execute", image=image, command=command, network=joined,
                        env={**env, **exported, **proxy_environment("")}, limits=limits, timeout=timeout,
                        copy=run_copy, outputs=list(outputs), out_dir=out_dir, volumes=mounts)
            append_record(record, {**hidden(row), "copy": digest, **({"from": based} if kept_image else {})})
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
        if hide and isinstance(result.get("cause"), str):
            result["cause"] = hide(result["cause"])
        for args in cleanup:
            try:
                cli(found, *args)
            except (OSError, subprocess.TimeoutExpired):
                pass
        if held:
            try:
                remove_volumes(found, held[0], os.getpid(), held[1], [kept_image] if kept_image else ())
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
                     f"> {folder}/{STREAMS[0]} 2> {folder}/{STREAMS[1]}; echo $? > {folder}/code")
    return "\n".join(lines) + "\nexit 0\n"


def run_commands(project: Path, commands: list[dict], *, image: str, out_dir: Path, values: bool = False,
                 **options) -> dict:
    """Commands as data, each `{tool, argv, cwd, env, network}`, in one container run over a copy of `project`:
    those whose `network` is "registries" in the preparation, the others ("none", the default) in execution.
    `cwd` is relative to the copy. The result of `run_in_container` (`options` are its own), with `root`, the
    copy's folder, and `results`: each command's `returncode` (None when it did not run), `stdout` and `stderr`,
    in the given order. The commands describe the project and see no value of its tracked `.env` files: those
    hold each value's name before they run (`named`), so what they print is kept as printed (`blind`). With
    `values`, for Daodan's helper alone, which runs no code of the project (`daodan-dockerfile`), the true values
    lie beside the copy (`DOTENV_VALUES`) and the run keeps the check."""
    for item in commands:
        target = posixpath.normpath(posixpath.join(WORKDIR, item.get("cwd") or "."))
        inside = target == WORKDIR or target.startswith(WORKDIR + "/")
        if not item.get("argv") or posixpath.isabs(item.get("cwd") or ".") or not inside or (
                item.get("network", "none") not in NETWORKS):
            raise ValueError(f"a command needs an argv, a folder inside the copy and a network in {NETWORKS}: {item}")
    early = [(n, item) for n, item in enumerate(commands) if item.get("network") == "registries"]
    late = [(n, item) for n, item in enumerate(commands) if item.get("network", "none") == "none"]
    kept_results = f"{STATE}/results"
    placed = named(values=DOTENV_VALUES if values else None)
    carry = placed + f"mkdir -p {RESULTS}\n" + (f"cp -R {kept_results}/. {RESULTS}/ 2>/dev/null\n" if early else "")
    out_dir = Path(out_dir)
    shutil.rmtree(out_dir / Path(RESULTS).name, ignore_errors=True)
    result = run_in_container(project, ["sh", "-c", carry + command_lines(late, RESULTS)], image=image,
                              out_dir=out_dir, outputs=[RESULTS], blind=not values, **options,
                              prepare=["sh", "-c", placed + command_lines(early, kept_results)] if early else None)
    folder, results = out_dir / Path(RESULTS).name, []
    for number in range(len(commands)):
        read = {name: (folder / str(number) / name).read_text(encoding="utf-8", errors="replace")
                if (folder / str(number) / name).is_file() else "" for name in ("code", *STREAMS)}
        code = read.pop("code").strip()
        results.append({"returncode": int(code) if code.lstrip("-").isdigit() else None, **read})
    return {**result, "root": WORKDIR, "results": results}
