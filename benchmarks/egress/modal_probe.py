"""The ways out of a preparation, tried on a real container behind Daodan's own proxy (`T0.C.8`).

    modal run benchmarks/egress/modal_probe.py                      # PROXY_SCRIPT: results/<date>.json
    modal run benchmarks/egress/modal_probe.py --proxy script       # T3.A.2: results/proxy-script.json
    modal run benchmarks/egress/modal_probe.py --proxy smokescreen  # T3.A.2: results/proxy-smokescreen.json

Two canaries on Modal, reachable from the Internet over HTTPS through Modal's tunnels, log every request they get:
`allowed` (the host the user approves) answers 301/302 to `/r301` and `/r302` toward the `to` it is given, `outside`
is never approved. In a VM Sandbox with Docker's daemon (as `benchmarks/project-model/modal_engine.py`), `driver.py`
runs `rows.py` as the preparation of a project through `container.run_in_container`: Daodan's `--internal` network,
its `start_proxy` with `PROXY_SCRIPT` (or Smokescreen in its place, `--proxy smokescreen`), its `egress` state; the
`control-` rows (a registry, the approved canary, git from the Debian archive) are as expected when `reached`, the
`measure-` row (the proxy's start, memory, image) when measured. Any other row is as expected when its way out is `blocked` and has
left no mark: no request on a canary for its path, no connection to the VM's listeners, no query with the run's token
on the wire outside the host's own lookup of refused names (`egress.resolve`, on the VM's `eth0`). The approval rows
check the result's `gaps` and the pending requests. Writes `results/<date>.json` and exits 1 on any unexpected row.
"""
from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DOCKER = "https://download.docker.com/linux/static/stable/x86_64/docker-29.10.0.tgz"
CANARY = r'''
import http.server, sys, threading, urllib.parse
def handler(port):
    class Canary(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            with open("/tmp/hits", "a") as hits:
                print(port, self.command, self.path, file=hits, flush=True)
            url = urllib.parse.urlsplit(self.path)
            to = urllib.parse.parse_qs(url.query).get("to", [""])[0]
            if url.path in ("/r301", "/r302") and to:
                self.send_response(int(url.path[2:])); self.send_header("Location", to); self.end_headers()
            else:
                self.send_response(200); self.end_headers(); self.wfile.write(b"canary")
        do_HEAD = do_GET
    return Canary
for port in (8001, 8002):
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), handler(port))
    threading.Thread(target=server.serve_forever).start()
'''

image = (modal.Image.debian_slim(python_version="3.13")
         .apt_install("ca-certificates", "curl", "iptables", "xz-utils", "procps", "git", "tcpdump")
         .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6",
                      "jsonpointer==3.0.0")  # `project_file`, where «Blocca» is kept
         .run_commands(f"curl -fsSL {DOCKER} -o /tmp/d.tgz && mkdir -p /opt/docker && "
                       "tar -xzf /tmp/d.tgz -C /opt/docker --strip-components=1")
         .add_local_dir(REPO / "daodan/core", "/daodan/map/core", copy=True, ignore=["**/__pycache__/**"])
         .add_local_dir(REPO / "daodan/data", "/daodan/map/data", copy=True)
         .add_local_file(HERE / "rows.py", "/daodan/egress/rows.py", copy=True)
         .add_local_file(HERE / "driver.py", "/daodan/egress/driver.py", copy=True))
canary_image = modal.Image.debian_slim(python_version="3.13")
app = modal.App("daodan-egress-probe", image=image)


BRIDGES = ("veth", "br-", "docker")  # the engine's interfaces on the VM: what a container sends passes there
EXPECTED_ALLOWED = {"/control-approved", "/r301", "/r302", "/approval-yes"}  # the canary paths a row may reach


def marks(paths: list[str], hits: list[str]) -> list[str]:
    return [hit for hit in hits if hit.split()[2].split("?")[0] in paths]


def judge(result: dict, hits: list[str]) -> list[dict]:
    """One line a row: expected and measured outcome, the marks it left, and whether it is as expected."""
    lines, wire = [], result["dns_wire"]
    for row in result["ways"]["rows"]:
        expected = ("reached" if row["row"].startswith("control-") else "measured" if row["row"].startswith("measure-")
                    else "blocked")
        lines.append({**row, "expected": expected, "ok": row["outcome"] == expected})
    # Marks: any query with the run's token but the host's own lookup of the refused name (`egress.resolve`)
    host_lookup = [line for line in wire if "refused-" in line and not line.startswith(BRIDGES)]
    lines.append({"row": "mark-dns-wire", "expected": "only the host's lookup of the refused name",
                  "outcome": [line for line in wire if line not in host_lookup], "host_lookup": host_lookup,
                  "ok": all(line in host_lookup for line in wire)})
    lines.append({"row": "mark-vm-listeners", "expected": "no connection", "outcome": result["listener_hits"],
                  "ok": not result["listener_hits"]})
    outside = [hit for hit in hits if hit.startswith("8002 ")]
    lines.append({"row": "mark-canary-outside", "expected": "no request", "outcome": outside, "ok": not outside})
    stray = [hit for hit in hits if hit.startswith("8001 ") and hit.split()[2].split("?")[0] not in EXPECTED_ALLOWED]
    lines.append({"row": "mark-canary-allowed", "expected": f"only {sorted(EXPECTED_ALLOWED)}", "outcome": stray,
                  "ok": not stray})
    ask, yes, block = result["ask"], result["yes"], result["block"]
    kinds = lambda run: sorted({gap.get("kind") for gap in run.get("gaps") or ()})  # noqa: E731
    lines.append({"row": "approval-outside-asks", "expected": "failed, approval_required, pending, no mark",
                  "outcome": [ask["run"]["state"], kinds(ask["run"]), [r["host"] for r in ask["pending"]]],
                  "marks": marks(["/approval-ask"], hits),
                  "ok": ask["run"]["state"] != "done" and "approval_required" in kinds(ask["run"])
                  and any(r["host"] == result["allowed"] for r in ask["pending"])
                  and not marks(["/approval-ask"], hits)})
    lines.append({"row": "approval-after-yes", "expected": "done, canary reached",
                  "outcome": [yes["run"]["state"], yes["run"]["exit_code"], kinds(yes["run"])],
                  "marks": marks(["/approval-yes"], hits),
                  "ok": yes["run"]["state"] == "done" and bool(marks(["/approval-yes"], hits))})
    lines.append({"row": "approval-blacklist", "expected": "failed, host_denied, nothing pending, no mark",
                  "outcome": [block["run"]["state"], kinds(block["run"]), block["pending"]],
                  "marks": marks(["/approval-block"], hits),
                  "ok": block["run"]["state"] != "done" and kinds(block["run"]) == ["host_denied"]
                  and not block["pending"] and not marks(["/approval-block"], hits)})
    return lines


@app.local_entrypoint()
def main(proxy: str = ""):
    if proxy not in ("", "script", "smokescreen"):
        raise SystemExit("--proxy is script or smokescreen")
    boxes = modal.App.lookup("daodan-egress-probe-boxes", create_if_missing=True)
    canary = modal.Sandbox.create("python3", "-u", "-c", CANARY, image=canary_image, app=boxes, timeout=3600,
                                  encrypted_ports=[8001, 8002])
    box = None
    try:
        tunnels = canary.tunnels()
        allowed, outside = tunnels[8001].host, tunnels[8002].host
        print("CANARIES", allowed, outside, flush=True)
        box = modal.Sandbox.create(image=image, app=boxes, cpu=4, memory=8192, timeout=3600,
                                   runtime="vm")
        box.exec("sh", "-c", "PATH=/opt/docker:$PATH nohup dockerd > /tmp/dockerd.log 2>&1 &")
        for _ in range(90):
            if box.exec("/opt/docker/docker", "info", timeout=30).wait() == 0:
                break
            time.sleep(1)
        given = {"allowed": allowed, "outside": outside, "proxy": proxy or "script"}
        process = box.exec("python", "/daodan/egress/driver.py", json.dumps(given), timeout=3300)
        for line in process.stdout:
            print(line.rstrip()[:400], flush=True)
        print("driver exit", process.wait(), process.stderr.read()[-3000:], flush=True)
        written = box.exec("cat", "/runs/result.json").stdout.read()
        result = json.loads(written) if written.strip() else None
        reader = canary.exec("sh", "-c", "cat /tmp/hits 2>/dev/null")
        hits = [line.strip() for line in reader.stdout.read().splitlines() if line.strip()]
    finally:
        canary.terminate()
        if box:
            box.terminate()
    if result is None:
        raise SystemExit("the driver gave no result")
    result.update(allowed=allowed, outside=outside)
    lines = judge(result, hits)
    for line in lines:
        print(json.dumps(line, default=str)[:600])
    out = HERE / "results" / (f"proxy-{proxy}.json" if proxy else f"{date.today().isoformat()}.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"rows": lines, "canary_hits": hits, "driver": result}, indent=1, default=str) + "\n",
                   encoding="utf-8")
    failed = [line["row"] for line in lines if not line["ok"]]
    print(f"{len(lines) - len(failed)} of {len(lines)} as expected" + (f"; not: {', '.join(failed)}" if failed else ""))
    if failed:
        raise SystemExit(1)
