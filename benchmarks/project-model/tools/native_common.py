"""Plumbing shared by the native adapters: run a build tool's own command and keep what each call did.

The driver (`modal_native.py`) sets `WRAP` (a prefix such as `unshare -rn` for a run without network),
`TRACE` (a directory: every call then runs under strace, one file per call) and `ENV` (HOME and caches),
then reads `CALLS`: per call the argv, exit code, seconds, peak memory of every process the call started,
the files it wrote inside the project copy and the processes it left running. An adapter only calls `run`.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path

CALLS: list[dict] = []
NOTES: dict = {}  # an adapter's errors and raw facts beside its output
WRAP: list[str] = []
TRACE: str | None = None
TRACE_CALLS = "execve,connect"  # a diagnostic run may ask for more (sendto, openat)
ENV: dict[str, str] = {}
WATCH: str | None = None  # the project copy: files a call writes there are recorded
CANARY: str | None = None  # the directory canary lines write markers into
TIMEOUT = 900
PRUNE = {"node_modules", "vendor", "target", "build", "dist", "out", "testdata", "__pycache__", "obj", "bin"}


def reset() -> None:
    CALLS.clear()
    NOTES.clear()


def tree(root) -> dict[str, str]:
    """`{relative path: size and mtime}` of every file under root (links by target text), `.git` left out:
    a stat per file, so a large clone is walked in seconds; a write changes the mtime."""
    root = Path(root)
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            path = Path(base) / name
            rel = path.relative_to(root).as_posix()
            try:
                if path.is_symlink():
                    out[rel] = "link:" + os.readlink(path)
                else:
                    stat = path.stat()
                    out[rel] = f"{stat.st_size}:{stat.st_mtime_ns}"
            except OSError:
                out[rel] = "unreadable"
        for name in dirs:
            path = Path(base) / name
            if path.is_symlink():
                out[path.relative_to(root).as_posix() + "/"] = "link:" + os.readlink(path)
    return out


def changes(before: dict, after: dict) -> dict:
    return {"added": sorted(set(after) - set(before)), "deleted": sorted(set(before) - set(after)),
            "modified": sorted(k for k in set(before) & set(after) if before[k] != after[k])}


class _Sampler(threading.Thread):
    """Resident memory of the processes a call starts, summed, every 50 ms; daemons included."""

    def __init__(self):
        super().__init__(daemon=True)
        self.peak, self.stopped, self.remote = 0, threading.Event(), set()
        try:
            import psutil
            self.psutil = psutil
            self.baseline = set(psutil.pids())
        except ImportError:
            self.psutil = None

    def run(self):
        tick = 0
        while self.psutil and not self.stopped.is_set():
            total = 0
            for proc in self.psutil.process_iter(["pid", "memory_info"]):
                if proc.info["pid"] not in self.baseline and proc.info["memory_info"]:
                    total += proc.info["memory_info"].rss
            self.peak = max(self.peak, total)
            if tick % 4 == 0:  # open internet sockets, every 200 ms: a coarse view where strace cannot follow
                try:
                    for conn in self.psutil.net_connections("inet"):
                        if conn.raddr and conn.pid not in self.baseline and                                 not str(conn.raddr.ip).startswith(("127.", "::1", "::ffff:127.")):
                            self.remote.add(f"{conn.raddr.ip}:{conn.raddr.port}")
                except Exception:  # noqa: BLE001 - not available in this sandbox
                    pass
            tick += 1
            self.stopped.wait(0.05)

    def finish(self) -> tuple[int, list[str]]:
        """Peak MB and the processes still alive, which are killed so the next call starts clean."""
        self.stopped.set()
        self.join(2)
        left = []
        if self.psutil:
            for proc in self.psutil.process_iter(["pid", "name", "cmdline"]):
                if proc.info["pid"] not in self.baseline and proc.info["pid"] != os.getpid():
                    left.append(" ".join((proc.info["cmdline"] or [proc.info["name"] or "?"])[:4])[:160])
                    try:
                        proc.kill()
                    except Exception:  # noqa: BLE001 - already gone
                        pass
        return round(self.peak / 2**20), left


def run(argv, cwd, *, env: dict | None = None, timeout: int | None = None, name: str | None = None,
        stdin: str | None = None) -> subprocess.CompletedProcess:
    argv = [str(a) for a in argv]
    full = list(argv)
    trace = None
    if TRACE:
        trace = Path(TRACE) / f"{len(CALLS):03d}.trace"
        full = ["strace", "-f", "-qq", "--seccomp-bpf", "-e", f"trace={TRACE_CALLS}", "-s", "256",
                *(["-tt", "-yy"] if TRACE_CALLS != "execve,connect" else []),
                "-o", str(trace)] + full
    full = WRAP + full
    environment = {**os.environ, **ENV, **(env or {})}
    before = tree(WATCH) if WATCH else None
    marks = set(os.listdir(CANARY)) if CANARY and os.path.isdir(CANARY) else set()
    sampler = _Sampler()
    sampler.start()
    started = time.time()
    # Output to files, not pipes: a daemon the tool leaves behind (Gradle, Bazel, MSBuild) would hold a pipe open
    # and keep the call waiting past its time limit. On timeout the whole process group is killed.
    import signal
    import tempfile
    with tempfile.TemporaryFile() as fo, tempfile.TemporaryFile() as fe:
        try:
            proc = subprocess.Popen(full, cwd=str(cwd), stdout=fo, stderr=fe, env=environment, start_new_session=True,
                                    stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL)
            try:
                proc.communicate(input=stdin.encode("utf-8") if stdin is not None else None, timeout=timeout or TIMEOUT)
                code, timed_out = proc.returncode, False
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    proc.kill()
                proc.wait()
                code, timed_out = -9, True
            fo.seek(0)
            fe.seek(0)
            out = fo.read().decode("utf-8", "replace")
            err = fe.read().decode("utf-8", "replace") + ("\n[timeout]" if timed_out else "")
        except OSError as error:
            code, out, err = -1, "", f"{type(error).__name__}: {error}"
    seconds = round(time.time() - started, 2)
    peak, left = sampler.finish()
    record = {"name": name or " ".join(argv[:4]), "argv": argv, "cwd": str(cwd), "rc": code, "seconds": seconds,
              "peak_mb": peak, "stderr": err[-2000:], "stdout_head": out[:600], "left_running": left,
              "trace": str(trace) if trace else None, "sockets": sorted(sampler.remote)[:20]}
    if WATCH:
        record["writes"] = changes(before, tree(WATCH))
    if CANARY and os.path.isdir(CANARY):
        record["canaries"] = sorted(set(os.listdir(CANARY)) - marks)
    CALLS.append(record)
    return subprocess.CompletedProcess(argv, code, out, err)


def find(root, names, *, prune=PRUNE, skip_underscore=False) -> list[str]:
    """Relative POSIX paths of the files named `names` under root; dot directories and `prune` skipped."""
    root = Path(root)
    found = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in prune
                         and not (skip_underscore and d.startswith("_")))
        for name in sorted(files):
            if name in names or any(n.startswith("*") and name.endswith(n[1:]) for n in names):
                found.append((Path(base) / name).relative_to(root).as_posix())
    return found


def rel(path, root) -> str:
    """POSIX path relative to root; the root itself is `.`."""
    try:
        value = Path(os.path.normpath(str(path))).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return Path(str(path)).as_posix()
    return value or "."


def parent(relpath: str) -> str:
    return relpath.rsplit("/", 1)[0] if "/" in relpath else "."


def join(base: str, name: str) -> str:
    return name if base in ("", ".") else f"{base}/{name}"


def json_or_none(text: str):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def json_stream(text: str) -> list:
    """Concatenated JSON values (JSON lines or objects written one after another)."""
    decoder, out, index = json.JSONDecoder(), [], 0
    while True:
        match = re.compile(r"\S").search(text, index)
        if not match:
            return out
        try:
            value, index = decoder.raw_decode(text, match.start())
        except ValueError:
            line_end = text.find("\n", match.start())
            if line_end < 0:
                return out
            index = line_end + 1
            continue
        out.append(value)


def error_of(done: subprocess.CompletedProcess) -> str:
    lines = [line for line in (done.stderr or done.stdout or "").strip().splitlines() if line.strip()]
    return f"exit {done.returncode}: " + " | ".join(lines[-4:])[:600]
