"""What the recipes need from the base image, on the image before and on `preparation.IMAGE` (`T3.A`).

    modal run benchmarks/egress/modal_image.py

The same three cases on Debian's slim image (the base before) and on `preparation.IMAGE`, each in a Modal container
of that image behind Daodan's own proxy (`container.PROXY_SCRIPT`, open to `container.REGISTRIES`), with the
preparation's environment (`preparation.ENV`, `container.proxy_environment`): `apt` is `NEEDS["git"]`'s own line;
`xz` is `NEEDS["rust"]` (its `.tar.xz` archives, downloaded and checked as the host does); `go` is `NEEDS["go"]`, then
`go mod download` of a module from the Go proxy (the CA certificates). Writes `results/image.json`; exits 1 unless
every case succeeds on `preparation.IMAGE` and the proxy refused nothing there.
"""
from __future__ import annotations

import json
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] if len(HERE.parents) > 1 else HERE  # in Modal's container this file sits at /root
BEFORE = "debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2"
NOW = "buildpack-deps:noble@sha256:890e8b5c0040e1deff5cc7dc7b4414e67069f79e3301afc4ec5bd49d64ef13e5"
MODULE = ("golang.org/x/text", "v0.21.0")


def image_of(name: str) -> modal.Image:
    return (modal.Image.from_registry(name, add_python="3.13")
            .pip_install("certifi")  # the host's download, outside the image: its own CA bundle
            .add_local_dir(REPO / "daodan/core", "/daodan/map/core", copy=True, ignore=["**/__pycache__/**"])
            .add_local_dir(REPO / "daodan/data", "/daodan/map/data", copy=True))


app = modal.App("daodan-egress-image")


def cases(name: str) -> dict:
    import hashlib, os, ssl, subprocess, sys, urllib.request  # noqa: E401
    import certifi
    sys.path[:0] = ["/daodan/map/core"]
    import container
    import preparation
    proxy = subprocess.Popen([sys.executable, "-I", "-c", container.PROXY_SCRIPT, "0", *container.REGISTRIES],
                             stdout=subprocess.PIPE, text=True)
    port = int(proxy.stdout.readline().split()[1])
    env = {**os.environ, **preparation.ENV, **container.proxy_environment(f"http://127.0.0.1:{port}")}
    head = f'set -u; mkdir -p {preparation.T}/bin "$HOME" {preparation.IN} /tmp/m'

    def fetched(needs):  # as the host does: each file by its sha256, carried into IN
        for url, sha, file in preparation.setup(needs)["files"]:
            trust = ssl.create_default_context(cafile=certifi.where())
            data = urllib.request.urlopen(url, timeout=600, context=trust).read()
            assert hashlib.sha256(data).hexdigest() == sha, file
            os.makedirs(preparation.IN, exist_ok=True)
            Path(preparation.IN, file).write_bytes(data)

    def run(script: str) -> dict:
        done = subprocess.run(["sh", "-c", f"{head}\n{script}"], env=env, capture_output=True, text=True, timeout=1200)
        log = (done.stdout + done.stderr).strip()
        return {"ok": done.returncode == 0 and "DAODAN-MISSING" not in log, "exit": done.returncode,
                "log": log[-600:]}
    rows = {"image": name, "is_preparation_image": name == preparation.IMAGE,
            "has": run("ls /etc/ssl/certs/ca-certificates.crt; command -v xz git || true")["log"]}
    rows["apt"] = run("\n".join(preparation.setup(["git"])["lines"]) + "\ngit --version")
    fetched(["rust"])
    rows["xz"] = run("\n".join(preparation.setup(["rust"])["lines"]) + "\nrustc --version && cargo --version")
    fetched(["go"])
    rows["go"] = run("\n".join(preparation.setup(["go"])["lines"]) + f"\ncd /tmp/m && printf 'module m\\ngo 1.22\\n"
                     f"require {MODULE[0]} {MODULE[1]}\\n' > go.mod && go mod download {MODULE[0]} && go version")
    proxy.kill()
    rows["refused"] = [line for line in proxy.stdout.read().splitlines() if "refused" in line]
    return rows


@app.function(image=image_of(BEFORE), timeout=3600)
def before() -> dict:
    return cases(BEFORE)


@app.function(image=image_of(NOW), timeout=3600)
def now() -> dict:
    return cases(NOW)


@app.local_entrypoint()
def main():
    results = [before.remote(), now.remote()]
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "image.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    for row in results:
        print(row["image"].split("@")[0], {case: row[case]["ok"] for case in ("apt", "xz", "go")},
              "refused:", row["refused"])
    last = results[-1]
    if not (last["is_preparation_image"] and all(last[case]["ok"] for case in ("apt", "xz", "go"))
            and not last["refused"]):
        raise SystemExit(1)
