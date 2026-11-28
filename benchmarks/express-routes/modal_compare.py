"""Express's module (`entry_points/express.py`) against the pinned Noir, on Modal: the measure of the README's decision rule (`T1.C.9`).

    modal run benchmarks/express-routes/modal_compare.py                         every application of `cases.CASES`
    modal run benchmarks/express-routes/modal_compare.py --only tududi           some of them

(behind the session's proxy, with `modal[api-proxy-support]`; `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`.)

One image per application, as `noir-binding/modal_binding.py` builds it: Python 3.12, the pins of the snapshot's readers, the Noir that
`entry_points/noir.py` pins (sha256 checked), Daodan's `core` and `data`, the grammars checked (`noir-binding/warm.py`), and the checkout at
`/work`. Then (`measure.run`, which `hono-routes/modal_probe.py --compare` shares), with the network blocked and nothing of the project run: Daodan's snapshot (`snapshot.read_project`), `noir scan` as
`noir.commands` gives it, its answer recorded and bound as the step does (`entry_points.write` with Noir alone), and the module's rows
(`express.rows`) bound by `binder.bind` on new `flows.Facts`; on `tududi` also the links with its `offre` rule alone (`flows.link_facts`).
`counts.compare` counts; `results/<application>.json` keeps the counts, the rows (no source text) and the times.
"""
import concurrent.futures
import json
import pathlib
import sys
import zlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()  # in a container this file lies at /root: nothing below that reads the checkout runs there
REPO = HERE.parents[1] if LOCAL else HERE
MEASURE = "/daodan/measure"
NAMES = ("node-express-boilerplate", "anything-llm", "juice-shop", "tududi")
if LOCAL:
    sys.path.insert(0, str(HERE))
    import cases  # noqa: E402
    assert tuple(cases.CASES) == NAMES
    sys.path.append(str(REPO / "benchmarks/noir-binding"))
    import apps  # noqa: E402  (noir-binding's: the pinned Noir)
    NOIR = apps.NOIR
DEPS = ("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
IGNORE = ["**/__pycache__/**", "**/*.pyc"]
CHUNK = 6000  # bytes: a call with the network blocked cannot return more than about 8 KB at once


def _image(name: str) -> modal.Image:
    if not LOCAL:
        return modal.Image.debian_slim()
    repository, commit, _licence = cases.CASES[name]
    return (modal.Image.from_registry("buildpack-deps:noble", add_python="3.12")
            .pip_install(*DEPS)
            .run_commands(f"curl -fsSL -o /usr/local/bin/noir {NOIR[0]} && echo '{NOIR[1]}  /usr/local/bin/noir' | sha256sum -c - "
                          "&& chmod +x /usr/local/bin/noir")
            .env({"DAODAN_SHARED_DIR": "/daodan-shared", "PYTHONDONTWRITEBYTECODE": "1"})
            .add_local_dir(REPO / "daodan/core", "/daodan/core", copy=True, ignore=IGNORE)
            .add_local_dir(REPO / "daodan/data", "/daodan/data", copy=True)
            .add_local_file(REPO / "benchmarks/noir-binding/warm.py", f"{MEASURE}/warm.py", copy=True)
            .run_commands(f"python {MEASURE}/warm.py")
            .run_commands(f"mkdir -p /work && curl -fsSL https://codeload.github.com/{repository}/tar.gz/{commit} | tar xz -C /work --strip-components=1")
            .add_local_file(HERE / "counts.py", f"{MEASURE}/counts.py")
            .add_local_file(HERE / "measure.py", f"{MEASURE}/measure.py"))


app = modal.App("express-routes")


def _function(name: str):
    def run(rules: list[dict], wanted: list | None = None):
        import traceback
        try:
            sys.path.insert(0, MEASURE)
            import measure
            answer = measure.lines(wanted) if wanted is not None else measure.run(name, ("express",), rules)
        except BaseException:  # the cause comes back as data
            answer = {"name": name, "failed": traceback.format_exc()[-3000:]}
        payload = zlib.compress(json.dumps(answer).encode("utf-8"), 9)
        for start in range(0, len(payload), CHUNK):
            yield payload[start:start + CHUNK]
    run.__name__ = run.__qualname__ = "read_" + name.replace("-", "_")
    globals()[run.__name__] = function = app.function(image=_image(name), timeout=3600, block_network=True, memory=12288, cpu=4)(run)
    return function


FUNCTIONS = {name: _function(name) for name in NAMES}


def _collect(name: str, rules: list[dict], wanted: list | None = None) -> dict:
    return json.loads(zlib.decompress(b"".join(FUNCTIONS[name].remote_gen(rules, wanted))))


@app.local_entrypoint()
def main(only: str = "", mode: str = "compare"):
    if mode == "sample":
        import counts
        results = {name: json.loads((HERE / "results" / f"{name}.json").read_text(encoding="utf-8")) for name in NAMES}
        return counts.show(results, lambda name, wanted: _collect(name, [], wanted)["lines"])
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    chosen = [n for n in NAMES if not only or n in only.split(",")]
    offre = [rule for rule in json.loads((REPO / cases.RULES).read_text(encoding="utf-8"))["rules"] if rule["link"] == "offre"]
    with concurrent.futures.ThreadPoolExecutor(len(chosen)) as pool:
        calls = {name: pool.submit(_collect, name, offre if name == "tududi" else []) for name in chosen}
        for name, call in calls.items():
            try:
                answer = call.result()
            except Exception as error:  # a container that failed is a missing answer with its cause, not the end of the others
                answer = {"name": name, "failed": f"{type(error).__name__}: {str(error)[-800:]}"}
            answer["application"] = dict(zip(("repository", "commit", "licence"), cases.CASES[name]))
            (out / f"{name}.json").write_bytes((json.dumps(answer, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
            compared = answer.get("compare") or {}
            print("===", name, answer.get("failed") or "", json.dumps({k: v for k, v in compared.items() if not k.startswith("only_")}),
                  json.dumps({k: v for k, v in (answer.get("rule") or {}).items() if not k.startswith("only_")}))
