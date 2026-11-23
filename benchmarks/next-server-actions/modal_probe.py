"""`next analyze` on Modal, in a container with the network blocked: does a record of its graph say that `pay` is a server action?

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/next-server-actions/modal_probe.py

One image with the packages of `benchmarks/system-map/real-paths/next-shop` restored from its lockfile (`npm ci`, while the image
is built: the one moment the network is open). Then, with the network blocked, in a copy of the fixture for each variant:
`typegen` (what the tool of task 13a writes: the baseline), `intact` (`next analyze -o`, then `next analyze export`) and
`no-directive` (the same, with `"use server"` taken out of `app/checkout/actions.ts`: only the difference between the two says
whether the directive leaves a trace in a record). Every answer goes to `results/<variant>.json`. The project's code
(`next.config.ts`, `node_modules`) runs only in the container.

Nothing here reads a record for a meaning: the filters keep what names `checkout` and the modules one step before and after
those, and the raw export is kept (cut at `RAW_LIMIT`, with its size and sha256).
"""
import hashlib
import json
import os
import pathlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()  # in a container this file lies at /root: nothing below that reads the checkout runs there
REPO = HERE.parents[1] if LOCAL else HERE
FIXTURE = REPO / "benchmarks/system-map/real-paths/next-shop"
OUT = HERE / "results"
ACTIONS = "app/checkout/actions.ts"
WORD = "checkout"  # the records kept: those with a string that holds it
NEXT = ["npx", "--no-install", "next"]
OFFLINE = {"npm_config_offline": "true", "NEXT_TELEMETRY_DISABLED": "1", "NO_COLOR": "1", "CI": "1"}
RAW_LIMIT = 2_000_000  # characters of an export kept whole
TEXT_LIMIT = 60_000
LISTING_LIMIT = 3000
MANIFEST_NAMES = ("route-summaries.json", "history.json", "metadata.json")

image = modal.Image.from_registry("node:24-bookworm", add_python="3.12")
if LOCAL:
    image = (image.add_local_file(FIXTURE / "package.json", "/fix/package.json", copy=True)
             .add_local_file(FIXTURE / "package-lock.json", "/fix/package-lock.json", copy=True)
             .run_commands("cd /fix && npm ci --no-audit --no-fund 2>&1 | tail -5")
             .add_local_dir(FIXTURE, "/fix", ignore=["**/package-lock.json", "**/package.json", "**/node_modules/**"]))
app = modal.App("next-server-actions", image=image)


def _no_directive(root: pathlib.Path) -> None:
    file = root / ACTIONS
    text = file.read_text(encoding="utf-8")
    edited = text.replace('"use server";\n', "", 1)
    if edited == text:
        raise RuntimeError(f'{ACTIONS} has no `"use server";` line: the variant would be the fixture itself')
    file.write_text(edited, encoding="utf-8")


VARIANTS = {"typegen": None, "intact": None, "no-directive": _no_directive}


def _variant(name: str) -> str:
    """A copy of the fixture under /work, with its packages (really copied: Turbopack's root is the project folder)."""
    import shutil

    target = f"/work/{name}"
    shutil.copytree("/fix", target, symlinks=True)
    if VARIANTS[name]:
        VARIANTS[name](pathlib.Path(target))
    return target


def _run(argv: list[str], cwd: str, whole: bool = False) -> dict:
    """One command with the network blocked. The text of its standard output is cut at `RAW_LIMIT`, with its size and sha256;
    `whole` keeps the text uncut under `stdout_whole` (the caller takes it out)."""
    import subprocess
    import time

    started = time.monotonic()
    try:
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=600, env={**os.environ, **OFFLINE})
        answer = {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
    except subprocess.TimeoutExpired:
        answer = {"returncode": "timeout", "stdout": "", "stderr": ""}
    text = answer["stdout"]
    out = {"argv": argv, "returncode": answer["returncode"], "stderr": answer["stderr"][-4000:],
           "stdout": text[:RAW_LIMIT], "stdout_bytes": len(text.encode("utf-8")),
           "stdout_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "seconds": round(time.monotonic() - started, 2)}
    return {**out, "stdout_whole": text} if whole else out


def _listing(project: str) -> dict:
    """Every file of `.next` with its size (the first `LISTING_LIMIT`, in path order)."""
    base, files = os.path.join(project, ".next"), {}
    for directory, _names, names in os.walk(base):
        for name in names:
            path = os.path.join(directory, name)
            files[os.path.relpath(path, base).replace("\\", "/")] = os.path.getsize(path)
    shown = dict(sorted(files.items())[:LISTING_LIMIT])
    return {"files": len(files), "listed": shown}


def _texts(project: str) -> dict:
    """The text of what could say a function is a server action or which routes were analyzed: the manifests under
    `.next/server`, the three small files of the analysis, and the JSON header of each `.data` (its first four bytes, big
    endian, are said to be its length: a guess, recorded with its error when it fails)."""
    base, out = os.path.join(project, ".next"), {}
    for directory, _names, names in os.walk(base):
        for name in names:
            path = os.path.join(directory, name)
            rel = os.path.relpath(path, base).replace("\\", "/")
            manifest = "manifest" in name and name.endswith((".json", ".js")) and rel.startswith("server/")
            if (name in MANIFEST_NAMES or manifest) and os.path.getsize(path) <= TEXT_LIMIT:
                out[rel] = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
            elif name.endswith(".data"):
                try:
                    head = pathlib.Path(path).read_bytes()[:TEXT_LIMIT]
                    size = int.from_bytes(head[:4], "big")
                    out[rel + "#header"] = head[4:4 + size].decode("utf-8", errors="replace")[:4000]
                except OSError as error:
                    out[rel + "#header"] = f"unreadable: {error}"
    return out


def _route_keys(project: str) -> list[str]:
    """The keys of `route-summaries.json` that hold `WORD`; its shape is not known, so `/checkout` is the fallback."""
    for directory, _names, names in os.walk(os.path.join(project, ".next")):
        if "route-summaries.json" in names:
            try:
                data = json.loads(pathlib.Path(directory, "route-summaries.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            items = list(data) if isinstance(data, dict) else [d.get("route") if isinstance(d, dict) else d for d in data]
            found = [key for key in items if isinstance(key, str) and WORD in key]
            if found:
                return found
    return ["/" + WORD]


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for inner in value.values():
            yield from _strings(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from _strings(inner)


def _filtered(text: str) -> dict:
    """The records of a JSON Lines export that hold `WORD` in any string, the modules one step in and one step out of the
    modules among them, and the outputs and groups that hold one of their idents; the count of each type of record."""
    records = []
    for line in text.splitlines():
        try:
            records.append(json.loads(line))
        except ValueError:
            records.append({"type": "_unparsed", "line": line[:300]})
    counts: dict = {}
    for record in records:
        counts[record.get("type")] = counts.get(record.get("type"), 0) + 1
    named = [r for r in records if any(WORD in s for s in _strings(r))]
    taken = {id(r) for r in named}
    idents = {r["ident"] for r in named if r.get("type") == "module" and isinstance(r.get("ident"), str)}
    modules = [r for r in records if r.get("type") == "module" and id(r) not in taken]
    reached = {s for r in named if r.get("type") == "module" for s in _strings(r.get("dependencies"))}
    return {"counts": counts, "named": named[:200],
            "one_step_in": [r for r in modules if any(s in idents for s in _strings(r.get("dependencies")))][:200],
            "one_step_out": [r for r in modules if r.get("ident") in reached][:200],
            "outputs_and_groups": [r for r in records if r.get("type") in ("output", "group") and id(r) not in taken
                                   and any(s in idents for s in _strings(r))][:200]}


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def probe(names: list[str]) -> dict:
    import subprocess

    def say(argv):
        return subprocess.run(argv, capture_output=True, text=True).stdout.strip()

    out = {"_env": {"node": say(["node", "--version"]), "npm": say(["npm", "--version"]), "git": say(["git", "--version"]),
                    "next": json.load(open("/fix/node_modules/next/package.json"))["version"],
                    "next_native": sorted(os.listdir("/fix/node_modules/@next")) if os.path.isdir("/fix/node_modules/@next") else []}}
    for name in names:
        project = _variant(name)
        if name == "typegen":
            out[name] = {"commands": [_run([*NEXT, "typegen"], project)], "dot_next": _listing(project)}
            continue
        commands = [_run([*NEXT, "--version"], project), _run([*NEXT, "analyze", "--help"], project),
                    _run([*NEXT, "analyze", "export", "--help"], project),
                    _run([*NEXT, "analyze", "-o", "--snapshot", "probe"], project)]
        exported = _run([*NEXT, "analyze", "export", "--snapshot", "probe"], project, whole=True)
        whole = exported.pop("stdout_whole")
        routes = {key: _run([*NEXT, "analyze", "export", "--snapshot", "probe", "--route", key], project)
                  for key in _route_keys(project)}
        out[name] = {"commands": commands, "export": exported, "export_by_route": routes, "filtered": _filtered(whole),
                     "dot_next": _listing(project), "texts": _texts(project)}
    return out


def _idents(answer: dict) -> set[str]:
    return {r["ident"] for r in answer.get("filtered", {}).get("named", ()) if r.get("type") == "module" and "ident" in r}


@app.local_entrypoint()
def main():
    names = (os.environ.get("VARIANTS") or ",".join(VARIANTS)).split(",")
    OUT.mkdir(exist_ok=True)
    answers = probe.remote(names)
    for name, answer in answers.items():
        (OUT / f"{'00_env' if name == '_env' else name}.json").write_bytes(
            (json.dumps(answer, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps(answers["_env"], indent=1))
    for name in names:
        answer = answers[name]
        for command in answer["commands"]:
            print(f"$ {' '.join(command['argv'])} -> exit {command['returncode']} in {command['seconds']} s")
            if command["stderr"].strip():
                print("--- stderr:", command["stderr"].strip()[:400])
        print(f"=== {name}: {answer['dot_next']['files']} files in .next")
        if "filtered" in answer:
            print("    records:", answer["filtered"]["counts"], "| holding", WORD, ":", len(answer["filtered"]["named"]))
    if "intact" in answers and "no-directive" in answers:  # the one comparison that says whether the directive leaves a trace
        a, b = _idents(answers["intact"]), _idents(answers["no-directive"])
        print("idents only with the directive:", sorted(a - b))
        print("idents only without it:", sorted(b - a))
