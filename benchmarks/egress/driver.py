"""Runs INSIDE the VM Sandbox of `modal_probe.py`, where a real Docker daemon answers: each way out of `rows.py`, run as
a preparation through Daodan's own `container.run_in_container` (its `--internal` network and `start_proxy` with
`PROXY_SCRIPT`, or Smokescreen in its place: `T3.A.2`), and the approval rows through `egress` (`respond`, `reply`, the
shared files). argv[1] is a JSON object with the canary hosts `allowed` and `outside` and the `proxy` ("script" or
"smokescreen"). Smokescreen stands where `start_proxy` stands: its image by digest, an ACL (`action: enforce`) of the
same hosts `start_proxy` opens, given with `cp`, and its JSON log read as `egress.refused` reads the script's. The
proxy's container resolves two approved names to internal addresses (`--add-host`, row a); Daodan's Debian image
installs git as `preparation.NEEDS["git"]` does (row d); the proxy's start, memory and image size are measured (row g).
Beside the runs it keeps the marks a way out would leave on this VM:
every DNS query on the wire (`tcpdump`, with its interface) and every connection to two listeners, one on all the VM's
addresses (8099) and one on its loopback (8098). Then, with the script, the execution's rows (`execute`, `T1.F.3`),
answered by a thread as the app's page answers. Writes `/runs/result.json`.
"""
import json
import os
import shutil
import tempfile
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
import preparation  # noqa: E402

ARGS = json.loads(sys.argv[1])
ALLOWED, OUTSIDE, PROXY = ARGS["allowed"], ARGS["outside"], ARGS.get("proxy", "script")
TOKEN = uuid.uuid4().hex[:10]
HITS = []  # (listener, peer) of every connection to this VM's listeners
SMOKESCREEN = "ghcr.io/stripe/smokescreen@sha256:e62052a184ce5ef97c32b00a32583fc5376d4ca5d9ec941cf9a4566eef0556e8"
# Row a: approved names that the proxy's own container resolves to an internal address, no resolver of its own.
INTERNAL = {"10x": ("probe-internal-10x.example.com", "10.0.0.1"),
            "metadata": ("probe-internal-metadata.example.com", "169.254.169.254")}
CLI, REFUSED = container.cli, egress.refused
PROXY_LOGS = []  # Smokescreen's logs as read, kept in the result


def cli(engine, *args, **options):
    """The engine's CLI, with row a's `--add-host` on the create of a preparation's proxy, whichever it is."""
    if args[:2] == ("create", "--name") and str(args[2]).startswith("daodan-proxy-"):
        args = ("create", *(f"--add-host={name}:{address}" for name, address in INTERNAL.values()), *args[1:])
    if PROXY == "smokescreen" and args[:1] == ("logs",):  # its decisions go to stderr: read with what it prints
        options = {**options, "stderr": subprocess.STDOUT}
    return CLI(engine, *args, **options)


def start_smokescreen(engine, box, network, registries, project, ask=False):
    """`container.start_proxy` with Smokescreen: the same hosts, filtered by `egress.decide` as it filters them, in an
    ACL with `action: enforce`; the role is missing (no client certificate), so its `default` rule decides. It holds
    no connection (`ask`): the rows of the execution run with `PROXY_SCRIPT` only."""
    state, answers = egress.load(project), egress.session(project)
    hosts = [host.removeprefix("http://") for host in dict.fromkeys([*registries, *state["always"],
                                                                     *answers["allow"]])
             if egress.decide(host, project, state, answers) == "allow"]
    folder = Path(tempfile.mkdtemp())
    acl = {"version": "v1", "services": [], "default": {"project": "daodan", "action": "enforce",
                                                        "allowed_domains": sorted(set(hosts))}}
    (folder / "acl.yaml").write_text(json.dumps(acl), encoding="utf-8")  # JSON is YAML
    (folder / "config.yaml").write_text(json.dumps({"allow_missing_role": True, "acl_file": "/acl.yaml"}),
                                        encoding="utf-8")
    container.checked(cli(engine, "create", "--name", box, "--memory", str(128 * 2**20), "--pids-limit", "64",
                          SMOKESCREEN, "--config-file", "/config.yaml", "--listen-ip", "0.0.0.0", "--listen-port",
                          str(container.PROXY_PORT)), "create of the proxy")
    for name in ("acl.yaml", "config.yaml"):
        container.checked(cli(engine, "cp", str(folder / name), f"{box}:/{name}"), f"cp of {name}")
    container.checked(cli(engine, "network", "connect", "--alias", "proxy", network, box), "network connect")
    container.checked(cli(engine, "start", box), "start of the proxy")
    for _ in range(50):  # it says nothing when it listens: running, and a first line of its log
        logs = cli(engine, "logs", box)
        if cli(engine, "inspect", "--format", "{{.State.Running}}", box).stdout.strip() != b"true":
            raise RuntimeError("Smokescreen did not start: " + logs.stdout.decode()[-500:])
        if logs.stdout:
            return
        time.sleep(0.2)


def smokescreen_refused(log):
    """`egress.refused` over Smokescreen's log: the `{host, port}` of each decision with `allow: false`."""
    found = REFUSED(log)
    PROXY_LOGS.append(log[-6000:])
    for line in log.splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and entry.get("allow") is False and entry.get("requested_host"):
            host, _, port = str(entry["requested_host"]).rpartition(":")
            host, port = (host, port) if port.isdigit() else (str(entry["requested_host"]), "80")
            row = {"host": host.strip("[]").lower(), "port": port}
            if row not in found:
                found.append(row)
    return found


container.cli = cli
if PROXY == "smokescreen":
    container.start_proxy, egress.refused = start_smokescreen, smokescreen_refused


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


def apt_git(folder):
    """Row d: git from the Debian archive in Daodan's base image, by `preparation.NEEDS["git"]`'s own line."""
    out = Path("/runs") / folder.name
    setup = " && ".join(preparation.NEEDS["git"]["setup"])
    result = container.run_in_container(folder, ["true"], image=preparation.IMAGE, out_dir=out,
                                        prepare=["sh", "-c", f"{setup} && git --version"], timeout=60,
                                        prepare_timeout=600, memory=1024 * 2**20)
    log = (out / "prepare.log").read_text(encoding="utf-8", errors="replace") if (out / "prepare.log").is_file() else ""
    reached = result.get("state") == "done" and "git version" in log
    return {"row": "control-apt-git", "kind": "apt", "outcome": "reached" if reached else "blocked",
            "detail": f"{result.get('state')} {result.get('refused')} {log[-300:]}"}


def measure():
    """Row g: seconds from create to ready, memory once ready, the image's size; on a network of its own."""
    engine, token = container.find_engine(), uuid.uuid4().hex[:8]
    network, box = f"daodan-net-measure-{token}", f"daodan-proxy-measure-{token}"
    container.internal_network(engine, network)
    began = time.monotonic()
    try:
        container.start_proxy(engine, box, network, container.REGISTRIES, "measure")
        seconds = round(time.monotonic() - began, 2)
        time.sleep(2)
        memory = CLI(engine, "stats", "--no-stream", "--format", "{{.MemUsage}}", box).stdout.decode().strip()
        image = CLI(engine, "inspect", "--format", "{{.Image}}", box).stdout.decode().strip()
        size = CLI(engine, "image", "inspect", "--format", "{{.Size}}", image).stdout.decode().strip()
        return {"row": "measure-proxy", "kind": "measure", "outcome": "measured",
                "detail": {"start_seconds": seconds, "memory": memory, "image_bytes": int(size or 0)}}
    finally:
        CLI(engine, "rm", "-f", box)
        CLI(engine, "network", "rm", network)


started = time.monotonic()
listen("0.0.0.0", 8099)
listen("127.0.0.1", 8098)
capture = subprocess.Popen(["tcpdump", "-i", "any", "-n", "-l", "port", "53"], stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, text=True)
wire = []
threading.Thread(target=lambda: wire.extend(capture.stdout), daemon=True).start()
host_ip = own_address()
outside_ip = socket.gethostbyname(OUTSIDE)
common = {"allowed": ALLOWED, "outside": OUTSIDE, "outside_ip": outside_ip, "host_ip": host_ip, "token": TOKEN,
          "internal": {label: name for label, (name, _) in INTERNAL.items()}}
print("ENGINE", container.find_engine().argv, "PROXY", PROXY, "HOST", host_ip, "OUTSIDE", outside_ip, "TOKEN", TOKEN,
      flush=True)

# The proxy under test: the approved canary and row a's names are approved for this analysis, as "once" makes them.
ways = project("ways")
for host in (ALLOWED, *(name for name, _ in INTERNAL.values())):
    egress.respond(host, str(ways), "once")
ways_run, ways_rows, ways_log = run(ways, {**common, "mode": "rows"})
ways_rows += [apt_git(project("apt")), measure()]

# Approval: a host outside the list asks and the step fails; after "once" (the app's `egress.reply`) it is reached.
asking = project("asking")
ask_run, _, ask_log = run(asking, {**common, "mode": "fetch", "url": f"https://{ALLOWED}/approval-ask"})
pending = egress.pending(str(asking))
try:
    egress.reply(str(asking), [ALLOWED], "once")
except ValueError:  # no request waits: the ask row says so; the answer is given as the app would after one
    egress.respond(ALLOWED, str(asking), "once")
yes_run, _, yes_log = run(asking, {**common, "mode": "fetch", "url": f"https://{ALLOWED}/approval-yes"})

# Approval: a blocked host is refused with no request.
blocked = project("blocked/c/source")  # laid out as the app's checkout: «Blocca» is kept in its project file
egress.respond(OUTSIDE, str(blocked), "block")
block_run, _, block_log = run(blocked, {**common, "mode": "fetch", "url": f"https://{OUTSIDE}/approval-block"})
block_pending = egress.pending(str(blocked))


# The execution behind the firewall, as a PC's firewall asks (`T1.F.3`): the command is the execution of a run with no
# preparation, in a process where a person answers (`egress.ANSWERS`); the person is a thread that answers as the app's
# page does (`egress.reply`), what it saw kept. The rows above ran with nobody to answer: the proxy refused at once.
def execute(folder, url, timeout=60, reply=None, after=0.0):
    """`url` fetched by the execution within `timeout` seconds of its own; with `reply`, the person answers it `after`
    seconds once the request waits. The result, the seconds, the executions on record and what the person saw."""
    out, name, seen = Path("/runs") / folder.name, str(folder), {}
    box = {}
    worker = threading.Thread(target=lambda: box.update(result=container.run_in_container(
        folder, ["python3", "/work/rows.py", json.dumps({**common, "mode": "fetch", "url": url})],
        image=container.PROXY_IMAGE, out_dir=out, timeout=timeout, memory=512 * 2**20)))
    began = time.monotonic()
    worker.start()
    if reply:
        while worker.is_alive() and not [row for row in egress.pending(name) if row["host"] == urlhost(url)]:
            time.sleep(0.2)
        seen.update(asked_after=round(time.monotonic() - began, 1),
                    held=[row.get("held") for row in egress.pending(name) if row["host"] == urlhost(url)])
        time.sleep(after)
        seen.update(alive=worker.is_alive(), answered_at=round(time.monotonic() - began, 1))
        try:
            egress.reply(name, [urlhost(url)], reply)
        except ValueError as error:  # nothing waits: the row says so
            seen["reply_refused"] = str(error)
    worker.join(900)
    result = box.get("result") or {"state": "no result"}
    record = out / container.RECORD_NAME
    rows = [json.loads(line) for line in record.read_text(encoding="utf-8").splitlines()] if record.is_file() else []
    log = (out / "execute.log").read_text(encoding="utf-8", errors="replace") if (out / "execute.log").is_file() else ""
    return {"run": {key: result.get(key) for key in ("state", "exit_code", "cause", "refused", "asked", "gaps")},
            "seconds": round(time.monotonic() - began, 1), "executions": sum(row.get("phase") == "execute" for row in rows),
            "pending": egress.pending(name), "seen": seen, "log": log[-1500:]}


def urlhost(url):
    return url.split("/")[2].lower()


executed = {}
if PROXY == "script":
    os.environ[egress.ANSWERS] = "app"
    executed = {
        "canonical": execute(project("exec-canonical"), "https://pypi.org/simple/"),
        # the command's own limit is 5 s; the person answers 8 s after the request, within urllib's 15 s: it passes
        "yes": execute(project("exec-yes"), f"https://{ALLOWED}/exec-yes", timeout=5, reply="once", after=8),
        # nobody answers for 30 s: urllib gives up at 15 s and the run waits for the answer; then a "no" ends it
        "waiting": execute(project("exec-waiting"), f"https://{OUTSIDE}/exec-waiting", timeout=5, reply="no",
                           after=30),
        # beyond the four: the tool gave up (urllib, 15 s) before the yes (25 s): the run goes once more, reaching it
        "rerun": execute(project("exec-rerun"), f"https://{ALLOWED}/exec-rerun", timeout=5, reply="once", after=25),
    }
    blocked_exec = project("exec-blocked/c/source")  # a checkout of the app: «Blocca» is kept in its project file
    egress.respond(OUTSIDE, str(blocked_exec), "block")
    executed["blocked"] = execute(blocked_exec, f"https://{OUTSIDE}/exec-blocked")
    os.environ.pop(egress.ANSWERS, None)

time.sleep(2)
capture.terminate()
Path("/runs/result.json").write_text(json.dumps({
    "proxy": PROXY, "token": TOKEN, "host_ip": host_ip, "outside_ip": outside_ip,
    "ways": {"run": ways_run, "rows": ways_rows, "log": ways_log},
    "ask": {"run": ask_run, "pending": pending, "log": ask_log},
    "yes": {"run": yes_run, "log": yes_log},
    "block": {"run": block_run, "pending": block_pending, "log": block_log}, "exec": executed,
    "proxy_logs": PROXY_LOGS, "listener_hits": HITS, "dns_wire": [line.rstrip() for line in wire if TOKEN in line],
    "dns_wire_lines": len(wire), "dns_wire_sample": [line.rstrip() for line in wire[:40]],
    "egress_state": egress.load(str(blocked)), "seconds": round(time.monotonic() - started, 1)}, default=str),
    encoding="utf-8")
