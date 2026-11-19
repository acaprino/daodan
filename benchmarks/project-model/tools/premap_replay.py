"""The pre-map scored on this PC from recorded tool answers: no tool runs, no cost.

`modal_premap.py --score ... --runs results/premap-runs` keeps, per fixture, every model command the pre-map
asked with the answer the container gave. This replays them: the fixture is laid out as the container laid it
out (a hand-written one copied whole, a real one unpacked from the archive `modal_native.py prepare` stored on
the volume), its snapshot and pre-map are written here, and each command is answered from the recording. A
command the recording lacks (a reader changed what it asks) gets no answer and is listed: that fixture needs a
new run on Modal. The score is `score.py`'s, beside `modules.py` alone, as `modal_premap.py` writes it.

    python -I tools/premap_replay.py --out OUT.json [--real D:/wt/premap-real] [fixture ...]

Real repositories are read from `--real`, one `<name>.tar.gz` per fixture; a missing one is fetched once with
`modal volume get daodan-flow-results project-model/native-real/<name>.tar.gz`.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SCRIPTS = HERE.parents[1] / "daodan/core"
for path in (str(SCRIPTS), str(HERE), str(HERE / "tools")):
    if path not in sys.path:
        sys.path.insert(0, path)

import daodan_modules  # noqa: E402
import modules  # noqa: E402
import premap  # noqa: E402
import score as scorer  # noqa: E402
import snapshot  # noqa: E402

RUNS = HERE / "results/premap-runs"
FACETS = ("units", "units.depends_on", "workspace", "workspace.members", "toolchains", "dependencies",
          "languages", "excluded")
FAMILIES = ("js", "py", "jvm", "sys", "mix", "real")


def family(name: str) -> str:
    return "real" if name.startswith(("real-", "mix-real-")) else name.split("-")[0]


def replayer(recording: dict, missing: list):
    table = {json.dumps(run["command"], sort_keys=True): run["result"] for run in recording["runs"]}

    def run(commands):
        answers = []
        for command in commands:
            key = json.dumps(command, sort_keys=True)
            if key not in table:
                missing.append(command)
            answers.append(table.get(key) or {"returncode": 127, "stdout": "", "root": "",
                                              "stderr": "not recorded: a new run on Modal answers this command"})
        return answers
    return run


def real_project(name: str, cache: Path, work: Path) -> Path:
    archive = cache / f"{name}.tar.gz"
    if not archive.is_file():
        cache.mkdir(parents=True, exist_ok=True)
        environment = {key: value for key, value in os.environ.items()
                       if key.upper() not in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY")}
        environment.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")  # the client prints a check mark
        subprocess.run(["modal", "volume", "get", "daodan-flow-results",
                        f"project-model/native-real/{name}.tar.gz", str(archive)], check=True, env=environment)
    part = work / "part"
    with tarfile.open(archive) as tar:
        tar.extractall(part, filter="tar")
    return part / name


def replay(name: str, cache: Path) -> dict:
    fixture = HERE / "fixtures" / name
    recording = json.loads(gzip.decompress((RUNS / f"{name}.json.gz").read_bytes()).decode("utf-8"))
    expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
    work = Path(tempfile.mkdtemp(prefix=f"replay-{name}-"))
    try:
        if (fixture / "source.json").is_file():
            project = real_project(name, cache, work)
        else:
            project = work / name
            shutil.copytree(fixture, project)  # as the container lays it out, expected.json included
        manifest = work / "out" / "manifest.sqlite"
        snapshot.write_snapshot(project, manifest)
        graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
        missing: list = []
        record = premap.write(manifest, runner=replayer(recording, missing))
        return {"base": scorer.score(expected, daodan_modules.convert(graph)), "premap": scorer.score(expected, record),
                "output": record, "not_recorded": missing}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def totals(results: dict) -> str:
    lines = [f"{'facet':20} {'modules.py':>16} {'pre-map':>22}"]
    for facet in FACETS:
        row = []
        for side in ("base", "premap"):
            found = extra = wrong = expected = given = 0
            for result in results.values():
                entry = (result.get(side) or {}).get(facet) or {}
                expected += entry.get("expected", 0)
                if entry.get("given"):
                    given += 1
                    found += entry.get("found", 0)
                    extra += len(entry.get("extra", []))
                    wrong += len(entry.get("wrong", []))
            row.append(f"{found:>5} +{extra:<4} w{wrong:<3}" if given else "not given")
        lines.append(f"{facet:20} {row[0]:>16} {row[1]:>18} /{expected}")
    worse = []  # a facet the pre-map does not hold (external dependencies are the analyzer's) is not worse
    for facet in [f for f in FACETS[:6] if any(((r.get("premap") or {}).get(f) or {}).get("given")
                                               for r in results.values())]:
        for group in FAMILIES:
            sums = {side: sum(((result.get(side) or {}).get(facet) or {}).get("found", 0)
                              for name, result in results.items() if family(name) == group
                              and ((result.get(side) or {}).get(facet) or {}).get("given"))
                    for side in ("base", "premap")}
            if sums["premap"] < sums["base"]:
                worse.append(f"{facet} {group}: {sums['base']} -> {sums['premap']}")
    lines.append("worse than modules.py: " + (", ".join(worse) if worse else "none"))
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("fixtures", nargs="*")
    parser.add_argument("--out", required=True)
    parser.add_argument("--real", default="D:/wt/premap-real")
    args = parser.parse_args(argv)
    names = args.fixtures or sorted(path.name.removesuffix(".json.gz") for path in RUNS.glob("*.json.gz"))
    results, unrecorded = {}, collections.Counter()
    for name in names:
        try:
            results[name] = replay(name, Path(args.real))
        except Exception as error:  # noqa: BLE001 - a fixture's failure is its result
            results[name] = {"error": f"{type(error).__name__}: {error}"}
            print(f"{name}: {results[name]['error']}", file=sys.stderr)
            continue
        unrecorded[name] = len(results[name]["not_recorded"])
    Path(args.out).write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(totals(results))
    lacking = {name: count for name, count in unrecorded.items() if count}
    print("commands not recorded:", lacking or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
