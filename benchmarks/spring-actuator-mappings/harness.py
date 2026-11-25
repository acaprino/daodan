"""What the Modal probes of this folder share: one command run with its time, its peak memory, the sockets that listened
while it ran and who held each, and the java processes it left."""
import os
import pathlib


def listening() -> dict[int, tuple[int, str]]:
    """The container's TCP sockets in LISTEN: inode -> (port, local address as the kernel writes it)."""
    found = {}
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            for line in open(table).read().splitlines()[1:]:
                fields = line.split()
                if fields[3] == "0A":  # LISTEN
                    address, port = fields[1].rsplit(":", 1)
                    found[int(fields[9])] = (int(port, 16), address)
        except OSError:
            pass
    return found


def owner(inode: int) -> str:
    """The process that holds a socket: its pid and command line, from the descriptors under /proc."""
    import glob

    for descriptor in glob.glob("/proc/[0-9]*/fd/*"):
        try:
            if os.readlink(descriptor) == f"socket:[{inode}]":
                pid = descriptor.split("/")[2]
                command = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode("utf-8", "replace")
                return f"{pid} {command[:120]}"
        except OSError:
            continue
    return "unknown"


def knock(port: int, record: dict) -> None:
    """As soon as a socket is seen listening: connect to it on the loopback, ask for `/actuator/mappings`, record what comes back."""
    import socket

    try:
        with socket.create_connection(("127.0.0.1", port), timeout=3) as connection:
            record["poke"] = {"connect": "ok"}
            connection.settimeout(3)
            connection.sendall(b"GET /actuator/mappings HTTP/1.0" + bytes([13, 10]) + b"Host: x" + bytes([13, 10, 13, 10]))
            try:
                record["poke"]["reply"] = connection.recv(120).decode("utf-8", "replace").splitlines()[:1] or "closed by the peer, nothing sent"
            except OSError as error:
                record["poke"]["reply"] = f"nothing within 3 s ({type(error).__name__})"
    except OSError as error:
        record["poke"] = {"connect": f"{type(error).__name__}: {error}"}


def run(argv: list[str], cwd: str, env: dict | None = None, out_file: str | None = None, keep: int = 3000, poke: bool = False,
         watch_sockets: bool = True) -> dict:
    """One command: time, peak memory (the child's, `wait4`), the sockets that listened while it ran and who held
    them (and, with `poke`, what a connection to each answered), the java processes left."""
    import subprocess
    import tempfile
    import threading
    import time

    before, seen, done = set(listening()), {}, threading.Event()

    def watch():
        while not done.is_set():
            for inode, (port, address) in listening().items():
                if inode not in before and inode not in seen:
                    seen[inode] = {"port": port, "address": address, "owner": owner(inode), "at_s": round(time.monotonic() - started, 3)}
                    if poke:
                        threading.Thread(target=knock, args=(port, seen[inode]), daemon=True).start()
            now = listening()
            for inode, record in seen.items():
                if inode not in now and "gone_s" not in record:
                    record["gone_s"] = round(time.monotonic() - started, 3)  # no longer in LISTEN
            time.sleep(0.002 if poke else 0.01)

    watcher = threading.Thread(target=watch, daemon=True)
    started = time.monotonic()
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        if watch_sockets:
            watcher.start()
        process = subprocess.Popen(argv, cwd=cwd, stdout=stdout, stderr=stderr, env={**os.environ, "NO_COLOR": "1", **(env or {})})
        _, status, usage = os.wait4(process.pid, 0)
        seconds = round(time.monotonic() - started, 2)
        done.set()
        if watch_sockets:
            watcher.join()
        stdout.seek(0), stderr.seek(0)
        out, err = stdout.read().decode("utf-8", "replace"), stderr.read().decode("utf-8", "replace")
    left = subprocess.run(["ps", "-eo", "pid,comm,args"], capture_output=True, text=True).stdout
    written = pathlib.Path(out_file).read_text(encoding="utf-8") if out_file and os.path.isfile(out_file) else None
    return {"argv": argv, "returncode": os.waitstatus_to_exitcode(status), "seconds": seconds,
            "peak_memory_mb": round(usage.ru_maxrss / 1024), "listeners": sorted(seen.values(), key=lambda item: item["at_s"]),
            "java_left": [l.strip()[:160] for l in left.splitlines()[1:] if l.split()[1:2] == ["java"]],  # "[java] <defunct>": gone, not yet reaped
            "stdout": out[-(keep if status == 0 else keep * 8):], "stderr": err[-keep:],  # a failure keeps eight times as much
            "written": written[:200000] if written else None, "written_bytes": len(written) if written else 0}


def trim_javap(text: str, keep: set | None = None) -> str:
    """`javap -l -p -s` reduced to what `place_check.py` reads: the file, the class, and each member (with `keep`, a set of
    `(name, descriptor)`, only those) with its descriptor and the first line of its `LineNumberTable`; no local variables."""
    import re

    first = re.compile(r"      line \d+: \d+")
    out, block, table, taken = [], [], False, False

    def flush():
        if block:
            name = block[0].strip().rstrip(";")
            name = name.split("(")[0].split()[-1] if "(" in name else name
            descriptor = next((line.strip()[len("descriptor: "):] for line in block if line.strip().startswith("descriptor:")), None)
            if keep is None or (name, descriptor) in keep:
                out.extend(block)
            block.clear()

    for line in text.splitlines():
        indent = len(line) - len(line.lstrip(" "))
        if line.startswith("    LineNumberTable:"):
            table, taken = True, False
            block.append(line)
            continue
        if table and first.fullmatch(line):
            if not taken:
                block.append(line)
                taken = True
            continue
        table = False
        if indent == 2 and line.rstrip().endswith(";"):
            flush()
            block.append(line)
        elif indent == 4 and line.lstrip().startswith("descriptor:"):
            block.append(line)
        elif line.startswith("Compiled from") or (indent == 0 and line):
            flush()
            out.append(line)
    flush()
    return chr(10).join(out) + chr(10)


def slim(answer, keep_failure: int = 1500, keep_error: int = 800):
    """What a stored answer needs of the output of its commands: the tail of a failing command's, none of a successful one's."""
    if isinstance(answer, dict):
        if "argv" in answer and "stdout" in answer:
            ok = answer.get("returncode") == 0
            answer["stdout"] = "" if ok else answer["stdout"][-keep_failure:]
            answer["stderr"] = "" if ok else answer["stderr"][-keep_error:]
        for key, value in answer.items():
            if key.endswith("_log_tail") and isinstance(value, str):
                answer[key] = value[-keep_failure:]
            else:
                slim(value, keep_failure, keep_error)
    elif isinstance(answer, list):
        for item in answer:
            slim(item, keep_failure, keep_error)
    return answer
