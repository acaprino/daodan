"""Each host of `daodan/data/package-managers.json` reached through Daodan's preparation proxy, on Modal.

    python benchmarks/registry-hosts/modal_probe.py

In a Modal function with the network, `container.PROXY_SCRIPT` runs with `container.REGISTRIES`, as a preparation's
proxy does. Through it: an HTTPS GET of `/` of each host (any HTTP answer is a reached host, a redirect too, which is
not followed: its target is another host; a 403 of the proxy or no answer is not), apt's `dists/noble/Release` of each
`http://` archive, and the hosts that must stay out (GitHub and its API, Docker Hub, GitHub's container registry),
which the proxy must refuse. The client prints one JSON row a host and writes it to `results/<date>.json`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROXIES = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")
OUTSIDE = ("github.com", "api.github.com", "raw.githubusercontent.com", "ghcr.io", "registry-1.docker.io")

if __name__ == "__main__":  # the launcher: Modal's client does not go through a proxy of this shell
    environment = {key: value for key, value in os.environ.items() if key not in PROXIES}
    raise SystemExit(subprocess.run(["modal", "run", str(Path(__file__).resolve())], env=environment).returncode)

import modal  # noqa: E402

REPO = HERE.parents[1] if modal.is_local() else HERE  # in the container the file sits in /root
image = modal.Image.debian_slim(python_version="3.13").pip_install("tree-sitter==0.26.0", "PyYAML>=6")
if modal.is_local():
    image = (image.add_local_dir(REPO / "daodan/core", "/daodan/core", ignore=["**/__pycache__/**"])
             .add_local_dir(REPO / "daodan/data", "/daodan/data"))
app = modal.App("daodan-registry-hosts", image=image)


def ask(proxy: str, host: str) -> dict:
    """The answer to one request through the proxy at `proxy`: `http://` hosts by plain HTTP, the others by HTTPS."""
    import urllib.error
    import urllib.request
    url = f"{host}/ubuntu/dists/noble/Release" if host.startswith("http://") else f"https://{host}/"
    class Stay(urllib.request.HTTPRedirectHandler):  # a redirect is the host's answer; its target is another host
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}), Stay)
    try:
        with opener.open(urllib.request.Request(url, method="GET"), timeout=30) as answer:
            return {"host": host, "status": answer.status}
    except urllib.error.HTTPError as error:
        return {"host": host, "status": error.code}
    except OSError as error:  # the proxy's 403 to a CONNECT is a tunnel error, not an HTTP answer
        return {"host": host, "status": None, "error": str(error)[:200]}


@app.function(cpu=1, memory=1024, timeout=900)
def probe() -> list:
    sys.path.insert(0, "/daodan/core")
    import container
    server = subprocess.Popen([sys.executable, "-I", "-c", container.PROXY_SCRIPT, "0", *container.REGISTRIES],
                              stdout=subprocess.PIPE, text=True)
    try:
        proxy = f"http://127.0.0.1:{int(server.stdout.readline().split()[1])}"
        rows = [{**ask(proxy, host), "expected": "reached"} for host in container.REGISTRIES]
        rows += [{**ask(proxy, host), "expected": "refused"} for host in OUTSIDE]
    finally:
        server.kill()
    for row in rows:
        reached = row["status"] is not None and not (row["status"] == 403 and "error" in row)
        row["ok"] = reached == (row["expected"] == "reached")
    return rows


@app.local_entrypoint()
def main() -> None:
    rows = probe.remote()
    for row in rows:
        print(json.dumps(row))
    out = HERE / "results" / f"{date.today().isoformat()}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    failed = [row["host"] for row in rows if not row["ok"]]
    print(f"{len(rows) - len(failed)} of {len(rows)} as expected" + (f"; not: {', '.join(failed)}" if failed else ""))
    if failed:
        raise SystemExit(1)
