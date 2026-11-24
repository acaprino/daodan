"""How many of the endpoints of the pinned Noir does Daodan bind to one function, on real public applications, on Modal. Nothing of an application runs:
no install, no build, no framework command; only Noir (a scanner that reads text) and Daodan's own snapshot code read the checkout.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NOIR_BINDING_EVIDENCE=<a folder outside the repository> uv run --no-project --with modal modal run benchmarks/noir-binding/modal_binding.py
    ... modal_binding.py --only shhh,bookstack         some applications of `apps.APPS`
    ... modal_binding.py --mode nodes                   the node level (`nodes.py`): where the routes the binder ties end in the links; `$NOIR_BINDING_EVIDENCE/<name>.nodes.json`
    ... modal_binding.py --mode after                   the tree's own binder, nothing substituted (`after.py`): `$NOIR_BINDING_EVIDENCE/<name>.after.json`

For each application the image is built with the network open: Python 3.12, the pins of `daodan/core/requirements.txt` (the snapshot's own readers), the Noir
that `premap/noir.py` pins (sha256 checked), a copy of the working tree's `daodan/core` and `daodan/data` (`DAODAN_CODE` names another folder: a copy made at
the start of a measurement, so that another edit of the tree does not change what is measured), the grammars Daodan's own loader places and verifies
(`languages/_treesitter.py`, each language checked here), and the checkout of `apps.APPS` at its commit at `/work`. Then, with the network blocked,
`measure.py` runs in the container. The answer of each application (the facts of every endpoint) goes to `$NOIR_BINDING_EVIDENCE/<name>.json`: it holds
the endpoints of Noir's report and is not kept in the repository; `summarize.py` reads it and writes the counts and the examples to `results/`.
"""
import concurrent.futures
import json
import os
import pathlib
import shlex
import sys
import tempfile
import zlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()  # in a container this file lies at /root: nothing below that reads the checkout runs there
sys.path.insert(0, str(HERE))
import apps  # noqa: E402  (also in the container: the image holds it at /root/apps.py, for the names of the functions)
REPO = HERE.parents[1] if LOCAL else HERE
CODE = pathlib.Path(os.environ.get("DAODAN_CODE") or REPO / "daodan")
EVIDENCE = pathlib.Path(os.environ.get("NOIR_BINDING_EVIDENCE") or pathlib.Path(tempfile.gettempdir()) / "noir-binding-evidence")
NAMES = tuple(apps.APPS)


def _image(name: str) -> modal.Image:
    if not LOCAL:
        return modal.Image.from_registry("buildpack-deps:noble", add_python="3.12")
    _framework, repository, commit, _licence, _file, _note = apps.APPS[name]
    ignore = ["**/__pycache__/**", "**/tests/**", "**/*.pyc"]
    return (modal.Image.from_registry("buildpack-deps:noble", add_python="3.12")
            .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
            .run_commands(f"curl -fsSL -o /usr/local/bin/noir {shlex.quote(apps.NOIR[0])} && echo '{apps.NOIR[1]}  /usr/local/bin/noir' | sha256sum -c - && chmod +x /usr/local/bin/noir")
            .env({"DAODAN_SHARED_DIR": "/daodan-shared", "PYTHONDONTWRITEBYTECODE": "1"})
            .add_local_dir(CODE / "core", "/daodan/core", copy=True, ignore=ignore)
            .add_local_dir(CODE / "data", "/daodan/data", copy=True)
            .add_local_file(HERE / "measure.py", "/daodan/measure/measure.py", copy=True)
            .add_local_file(HERE / "warm.py", "/daodan/measure/warm.py", copy=True)
            .run_commands("python /daodan/measure/warm.py")
            .run_commands(f"mkdir -p /work && curl -fsSL https://codeload.github.com/{repository}/tar.gz/{commit} | tar xz -C /work --strip-components=1")
            .add_local_file(HERE / "nodes.py", "/daodan/measure/nodes.py")
            .add_local_file(HERE / "after.py", "/daodan/measure/after.py")
            .add_local_file(HERE / "apps.py", "/root/apps.py"))  # last: files added at run time cannot be followed by a command


IMAGES = {name: _image(name) for name in NAMES}
app = modal.App("noir-binding")


CHUNK = 6000  # bytes: a call that is not a generator cannot return more than about 8 KB here (the blob store a larger answer goes to is out of reach with the network blocked)


def _runner(name: str, mode: str = "evidence"):
    def run():
        sys.path.insert(0, "/daodan/measure")
        import traceback
        try:
            if mode == "nodes":
                import nodes
                answer = nodes.run(name)
            elif mode == "after":
                import after
                answer = after.run(name)
            else:
                import measure
                answer = measure.run(name)
        except BaseException:  # the cause comes back as data
            answer = {"name": name, "failed": traceback.format_exc()[-3000:]}
        payload = zlib.compress(json.dumps(answer).encode("utf-8"), 9)
        print(name, "answer", len(payload), "bytes compressed", flush=True)
        for start in range(0, len(payload), CHUNK):
            yield payload[start:start + CHUNK]
    run.__name__ = run.__qualname__ = {"nodes": "nodes_", "after": "after_"}.get(mode, "run_") + name.replace("-", "_")
    globals()[run.__name__] = function = app.function(image=IMAGES[name], timeout=3600, block_network=True, memory=12288, cpu=4)(run)
    return function


RUNNERS = {name: _runner(name) for name in NAMES}
NODE_RUNNERS = {name: _runner(name, "nodes") for name in NAMES}
AFTER_RUNNERS = {name: _runner(name, "after") for name in NAMES}


def _collect(name: str, mode: str) -> dict:
    return json.loads(zlib.decompress(b"".join({"nodes": NODE_RUNNERS, "after": AFTER_RUNNERS}.get(mode, RUNNERS)[name].remote_gen())))


@app.local_entrypoint()
def main(only: str = "", mode: str = "evidence"):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    chosen = [n for n in NAMES if not only or n in only.split(",")]
    with concurrent.futures.ThreadPoolExecutor(len(chosen)) as pool:  # all of them at once: each runs in its own container
        calls = {name: pool.submit(_collect, name, mode) for name in chosen}
        for name, call in calls.items():
            try:
                answer = call.result()
            except Exception as error:  # a container that failed is a missing answer with its cause, not the end of the others
                answer = {"name": name, "failed": f"{type(error).__name__}: {str(error)[-600:]}"}
            (EVIDENCE / (f"{name}.{mode}.json" if mode != "evidence" else f"{name}.json")).write_text(json.dumps(answer, indent=1), encoding="utf-8", newline="\n")
            noir = answer.get("noir") or {}
            print(name, answer.get("failed") or f"files={answer.get('files')} snapshot={answer.get('snapshot_seconds')}s noir={noir.get('returncode')} "
                  f"endpoints={noir.get('endpoints')} http_rows={answer.get('http_rows')}")
