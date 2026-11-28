"""`next analyze` on Modal, in a container with the network blocked: does a record of its graph say that `pay` is a server action?

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/next-server-actions/modal_probe.py

One image with the packages of `benchmarks/system-map/real-paths/next-shop` restored from its lockfile (`npm ci`, while the image
is built: the one moment the network is open). Then, with the network blocked, in a copy of the fixture for each variant:
`typegen` (what the tool of task 13a writes: the baseline), `intact` (`next analyze -o`, then `next analyze export`) and
`no-directive` (the same, with `"use server"` taken out of `app/checkout/actions.ts`: only the difference between the two says
whether the directive leaves a trace in a record). Every answer goes to `results/<variant>.json`. The project's code
(`next.config.ts`, `node_modules`) runs only in the container.

A fourth variant, `noir`, runs OWASP Noir (the binary and the digest Daodan's pre-map pins in `daodan/core/entry_points/noir.py`) over a copy of
the fixture without its packages, as `entry_points/noir.py` does, and keeps its JSON report: whether the `server-action` row names the
function and the line of its declaration.

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

def _noir_install() -> str:
    """The command that downloads Noir as `entry_points/noir.py` pins it (url, sha256): the file is loaded for its constants, not imported."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("daodan_noir_pin", REPO / "daodan/core/entry_points/noir.py")
    pin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pin)
    url, sha256, _name = pin.DOWNLOAD
    return (f"curl -fsSL -o /usr/local/bin/noir {url} && echo '{sha256}  /usr/local/bin/noir' | sha256sum -c -"
            " && chmod 755 /usr/local/bin/noir")


image = modal.Image.from_registry("node:24-bookworm", add_python="3.12")
if LOCAL:
    image = (image.add_local_file(FIXTURE / "package.json", "/fix/package.json", copy=True)
             .add_local_file(FIXTURE / "package-lock.json", "/fix/package-lock.json", copy=True)
             .run_commands("cd /fix && npm ci --no-audit --no-fund 2>&1 | tail -5")
             .run_commands(_noir_install())
             .add_local_dir(FIXTURE, "/fix", ignore=["**/package-lock.json", "**/package.json", "**/node_modules/**"]))
app = modal.App("next-server-actions", image=image)


def _no_directive(root: pathlib.Path) -> None:
    file = root / ACTIONS
    text = file.read_text(encoding="utf-8")
    edited = text.replace('"use server";\n', "", 1)
    if edited == text:
        raise RuntimeError(f'{ACTIONS} has no `"use server";` line: the variant would be the fixture itself')
    file.write_text(edited, encoding="utf-8")


VARIANTS = {"typegen": None, "intact": None, "no-directive": _no_directive, "noir": None}


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
    `whole` keeps the text uncut under `stdout_whole` (the caller takes it out). `max_rss_kb` is the largest resident set that the
    kernel (`wait4`) gives for one process of the command's tree (`npx`, `node`, the native binding): not their sum, not the container's."""
    import subprocess
    import tempfile
    import time

    started = time.monotonic()
    with tempfile.TemporaryFile() as out_file, tempfile.TemporaryFile() as err_file:
        process = subprocess.Popen(argv, cwd=cwd, stdout=out_file, stderr=err_file, env={**os.environ, **OFFLINE})
        code, usage = "timeout", None
        while time.monotonic() - started < 600:
            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                code = os.waitstatus_to_exitcode(status)
                break
            time.sleep(0.05)
        else:
            process.kill()
            os.wait4(process.pid, 0)
        seconds = round(time.monotonic() - started, 2)
        out_file.seek(0)
        err_file.seek(0)
        text, error = out_file.read().decode("utf-8", errors="replace"), err_file.read().decode("utf-8", errors="replace")
    out = {"argv": argv, "returncode": code, "stderr": error[-4000:], "stdout": text[:RAW_LIMIT],
           "stdout_bytes": len(text.encode("utf-8")), "stdout_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
           "seconds": seconds, "max_rss_kb": usage.ru_maxrss if usage else None}
    return {**out, "stdout_whole": text} if whole else out


def _noir() -> dict:
    """Noir over a copy of the fixture without its packages (what Daodan hands it: the project's files), with the lines of the
    file the `server-action` row should point at, numbered as an editor numbers them."""
    import shutil

    source = "/work/noir-source"
    shutil.copytree("/fix", source, symlinks=True, ignore=shutil.ignore_patterns("node_modules", ".next"))
    commands = [_run(["noir", "--version"], source), _run(["noir", "scan", source, "-f", "json", "--no-log"], source, whole=True)]
    scan = commands[1].pop("stdout_whole")
    try:
        report = json.loads(scan)
    except ValueError as error:
        report = {"unparsed": str(error)}
    numbered = {file: [f"{number}: {line}" for number, line in enumerate(
        pathlib.Path(source, file).read_text(encoding="utf-8").splitlines(), 1)] for file in (ACTIONS, "app/checkout/page.tsx")}
    return {"commands": commands, "source": source, "report": report, "numbered": numbered}


def _types(project: str) -> dict:
    """The text of every file `next typegen` writes under `.next/types` (a few KB each): what the task 13a tool says."""
    base = os.path.join(project, ".next", "types")
    return {name: pathlib.Path(base, name).read_text(encoding="utf-8") for name in sorted(os.listdir(base))}


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


CHUNK = 1_000_000  # bytes per message: the container's network is blocked, so an answer over Modal's inline limit cannot be uploaded


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def probe(names: list[str]):
    """Yields `(name, index, count, bytes)`: the answer of each variant, as JSON, deflated, in pieces of `CHUNK` bytes."""
    import subprocess
    import zlib

    def say(argv):
        return subprocess.run(argv, capture_output=True, text=True).stdout.strip()

    def pieces(name, answer):
        data = zlib.compress(json.dumps(answer, ensure_ascii=False, sort_keys=True).encode("utf-8"), 9)
        count = max(1, -(-len(data) // CHUNK))
        for index in range(count):
            yield name, index, count, data[index * CHUNK:(index + 1) * CHUNK]

    yield from pieces("_env", {"node": say(["node", "--version"]), "npm": say(["npm", "--version"]), "git": say(["git", "--version"]),
                               "next": json.load(open("/fix/node_modules/next/package.json"))["version"],
                               "next_native": sorted(os.listdir("/fix/node_modules/@next")) if os.path.isdir("/fix/node_modules/@next") else [],
                               "cpu_count": os.cpu_count()})
    for name in names:
        if name == "noir":
            yield from pieces(name, _noir())
            continue
        project = _variant(name)
        if name == "typegen":
            commands = [_run([*NEXT, "typegen"], project)]
            yield from pieces(name, {"commands": commands, "dot_next": _listing(project), "types": _types(project)})
            continue
        commands = [_run([*NEXT, "--version"], project), _run([*NEXT, "analyze", "--help"], project),
                    _run([*NEXT, "analyze", "export", "--help"], project),
                    _run([*NEXT, "analyze", "-o", "--snapshot", "probe"], project)]
        exported = _run([*NEXT, "analyze", "export", "--snapshot", "probe"], project, whole=True)
        whole = exported.pop("stdout_whole")
        routes = {key: _run([*NEXT, "analyze", "export", "--snapshot", "probe", "--route", key], project)
                  for key in _route_keys(project)}
        yield from pieces(name, {"commands": commands, "export": exported, "export_by_route": routes, "filtered": _filtered(whole),
                                 "dot_next": _listing(project), "texts": _texts(project)})


def _idents(answer: dict) -> set[str]:
    return {r["ident"] for r in answer.get("filtered", {}).get("named", ()) if r.get("type") == "module" and "ident" in r}


def _records(answer: dict) -> set[str]:
    return {json.dumps(json.loads(line), sort_keys=True) for line in answer["export"]["stdout"].splitlines()}


@app.local_entrypoint()
def main():
    import zlib

    names = (os.environ.get("VARIANTS") or ",".join(VARIANTS)).split(",")
    OUT.mkdir(exist_ok=True)
    received: dict = {}
    for name, index, count, data in probe.remote_gen(names):
        received.setdefault(name, {})[index] = data
        if len(received[name]) == count:
            received[name] = json.loads(zlib.decompress(b"".join(received[name][i] for i in range(count))))
    answers = received
    for name, answer in answers.items():
        (OUT / f"{'00_env' if name == '_env' else name}.json").write_bytes(
            (json.dumps(answer, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps(answers["_env"], indent=1))
    for name in names:
        answer = answers[name]
        for command in answer["commands"]:
            print(f"$ {' '.join(command['argv'])} -> exit {command['returncode']} in {command['seconds']} s, "
                  f"peak {command['max_rss_kb']} KB")
            if command["stderr"].strip():
                print("--- stderr:", command["stderr"].strip()[:400])
        if "dot_next" in answer:
            print(f"=== {name}: {answer['dot_next']['files']} files in .next")
        if "filtered" in answer:
            print("    records:", answer["filtered"]["counts"], "| holding", WORD, ":", len(answer["filtered"]["named"]))
    if "intact" in answers and "no-directive" in answers:  # the one comparison that says whether the directive leaves a trace
        a, b = _idents(answers["intact"]), _idents(answers["no-directive"])
        print("idents only with the directive:", sorted(a - b))
        print("idents only without it:", sorted(b - a))
        # every record of the two exports, whatever it holds: the set difference, no record interpreted
        whole = all(len(answers[v]["export"]["stdout"].encode("utf-8")) == answers[v]["export"]["stdout_bytes"] for v in ("intact", "no-directive"))
        ra, rb = _records(answers["intact"]), _records(answers["no-directive"])
        (OUT / "diff.json").write_bytes((json.dumps(
            {"exports_whole": whole, "records": {"intact": len(ra), "no-directive": len(rb)},
             "only_intact": sorted((json.loads(r) for r in ra - rb), key=json.dumps),
             "only_no_directive": sorted((json.loads(r) for r in rb - ra), key=json.dumps)},
            indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        print("records only with the directive:", len(ra - rb), "| only without it:", len(rb - ra))
    if "noir" in answers:
        report = answers["noir"]["report"]
        print("noir endpoints:", json.dumps(report.get("endpoints"), indent=1, ensure_ascii=False)[:3000])
