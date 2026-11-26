"""Run while an image of `modal_real.py` is built, with the network open: the two things Daodan's own preparation does for a Go project, from
Daodan's own code (the copy at `/daodan/core`).

    python prepare.py go        the Go that `preparation.GO` pins, its sha256 checked, unpacked in /usr/local/go
    python prepare.py restore   `preparation.restores` over the checkout's perimeter (`perimeter_files`), then the line `preparation.restore("go", ...)`
                                writes, with the environment Daodan exports before it (`GOFLAGS=-mod=readonly GOTOOLCHAIN=local`); the answer goes to
                                /prepared.json (folders, seconds, exit, the restore's own failure marks, the size of the module cache)
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, "/daodan/core")
import preparation  # noqa: E402

if sys.argv[1] == "go":
    url, sha256, _name = preparation.GO
    data = urllib.request.urlopen(url, timeout=600).read()
    if hashlib.sha256(data).hexdigest() != sha256:
        sys.exit(f"{url}: sha256 differs from preparation.GO")
    pathlib.Path("/tmp/go.tar.gz").write_bytes(data)
    subprocess.run(["tar", "-xzf", "/tmp/go.tar.gz", "-C", "/usr/local"], check=True)
    os.remove("/tmp/go.tar.gz")
    print(url, "checked")
else:
    files = preparation.perimeter_files(pathlib.Path("/work"))
    folders = preparation.restores(files).get("go", [])
    line = preparation.restore("go", folders)
    env = {**os.environ, "GOFLAGS": "-mod=readonly", "GOTOOLCHAIN": "local", "GOMODCACHE": "/gomod", "GOCACHE": "/tmp/gocache-restore",
           "PATH": "/usr/local/go/bin:" + os.environ["PATH"]}
    started = time.monotonic()
    done = subprocess.run(["sh", "-c", line], cwd="/work", env=env, capture_output=True, text=True)
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _n, fs in os.walk("/gomod") for f in fs if os.path.isfile(os.path.join(d, f)))
    answer = {"folders": folders, "line": line[:600], "seconds": round(time.monotonic() - started, 1), "returncode": done.returncode,
              "failed": [l for l in done.stderr.splitlines() if l.startswith("DAODAN-RESTORE-FAILED")], "stderr_tail": done.stderr[-2000:],
              "gomod_bytes": size, "perimeter_files": len(files)}
    pathlib.Path("/prepared.json").write_text(json.dumps(answer), encoding="utf-8")
    print(json.dumps({k: v for k, v in answer.items() if k != "line"})[:1500])
