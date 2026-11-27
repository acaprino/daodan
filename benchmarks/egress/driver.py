"""Runs INSIDE the VM Sandbox of `modal_probe.py`, where a real Docker daemon answers: each way out of `rows.py`, run as
a preparation through Daodan's own `container.run_in_container` (its `--internal` network and `start_proxy` with
`PROXY_SCRIPT`), and the approval rows through `egress` (`respond`, `reply`, the shared files). argv[1] is a JSON object
with the canary hosts `allowed` and `outside`. Beside the runs it keeps the marks a way out would leave on this VM:
every DNS query on the wire (`tcpdump`, with its interface) and every connection to two listeners, one on all the VM's
addresses (8099) and one on its loopback (8098). Writes `/runs/result.json`.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

sys.path[:0] = ["/daodan/map/core"]
os.environ["PATH"] = "/opt/docker:" + os.environ["PATH"]
os.environ["DAODAN_SHARED_DIR"] = "/runs/shared"
os.environ.pop("DAODAN_CONTAINER", None)

import container  # noqa: E402
import egress  # noqa: E402

ARGS = json.loads(sys.argv[1])
ALLOWED, OUTSIDE = ARGS["allowed"], ARGS["outside"]
TOKEN = uuid.uuid4().hex[:10]
HITS = []  # (listener, peer) of every connection to this VM's listeners


def listen(address, port):
    server = socket.create_server((address, port))

    def serve():
        while True:
            link, peer = server.accept()
            HITS.append({"listener": f"{address}:{port}", "peer": list(peer)})
            link.close()
    threading.Thread(target=serve, daemon=True).start()


def own_address():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.connect(("8.8.8.8", 53))  # UDP: no packet leaves, the kernel picks the route
        return probe.getsockname()[0]


def project(name):
    """A project of one file, `rows.py`, tracked by Git as `copy_perimeter` wants."""
    folder = Path("/work") / name
    folder.mkdir(parents=True)
    shutil.copy("/daodan/egress/rows.py", folder / "rows.py")
    for command in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "probe"]):
        subprocess.run(command, cwd=folder, check=True)
    return folder


def run(folder, args):
    out = Path("/runs") / folder.name
    result = container.run_in_container(folder, ["true"], image=container.PROXY_IMAGE, out_dir=out,
                                        prepare=["python3", "/work/rows.py", json.dumps(args)], timeout=60,
                                        prepare_timeout=600, memory=512 * 2**20)
    log = (out / "prepare.log").read_text(encoding="utf-8", errors="replace") if (out / "prepare.log").is_file() else ""
    rows = [json.loads(line[4:]) for line in log.splitlines() if line.startswith("ROW ")]
    keep = {key: result.get(key) for key in ("state", "exit_code", "cause", "refused", "asked", "gaps")}
    return keep, rows, log[-2000:]


started = time.monotonic()
listen("0.0.0.0", 8099)
listen("127.0.0.1", 8098)
capture = subprocess.Popen(["tcpdump", "-i", "any", "-n", "-l", "port", "53"], stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, text=True)
wire = []
threading.Thread(target=lambda: wire.extend(capture.stdout), daemon=True).start()
host_ip = own_address()
outside_ip = socket.gethostbyname(OUTSIDE)
common = {"allowed": ALLOWED, "outside": OUTSIDE, "outside_ip": outside_ip, "host_ip": host_ip, "token": TOKEN}
print("ENGINE", container.find_engine().argv, "HOST", host_ip, "OUTSIDE", outside_ip, "TOKEN", TOKEN, flush=True)

# The proxy of today: the approved canary is approved for this analysis, as the user's "once" makes it.
ways = project("ways")
egress.respond(ALLOWED, str(ways), "once")
ways_run, ways_rows, ways_log = run(ways, {**common, "mode": "rows"})

# Approval: a host outside the list asks and the step fails; after "once" (the app's `egress.reply`) it is reached.
asking = project("asking")
ask_run, _, ask_log = run(asking, {**common, "mode": "fetch", "url": f"https://{ALLOWED}/approval-ask"})
pending = egress.pending(str(asking))
egress.reply(str(asking), [ALLOWED], "once")
yes_run, _, yes_log = run(asking, {**common, "mode": "fetch", "url": f"https://{ALLOWED}/approval-yes"})

# Approval: a blocked host is refused with no request.
blocked = project("blocked")
egress.respond(OUTSIDE, str(blocked), "block")
block_run, _, block_log = run(blocked, {**common, "mode": "fetch", "url": f"https://{OUTSIDE}/approval-block"})
block_pending = egress.pending(str(blocked))

time.sleep(2)
capture.terminate()
Path("/runs/result.json").write_text(json.dumps({
    "token": TOKEN, "host_ip": host_ip, "outside_ip": outside_ip,
    "ways": {"run": ways_run, "rows": ways_rows, "log": ways_log},
    "ask": {"run": ask_run, "pending": pending, "log": ask_log},
    "yes": {"run": yes_run, "log": yes_log},
    "block": {"run": block_run, "pending": block_pending, "log": block_log},
    "listener_hits": HITS, "dns_wire": [line.rstrip() for line in wire if TOKEN in line],
    "dns_wire_lines": len(wire), "dns_wire_sample": [line.rstrip() for line in wire[:40]],
    "egress_state": egress.load(), "seconds": round(time.monotonic() - started, 1)}, default=str), encoding="utf-8")
