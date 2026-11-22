"""Replay the package checker on Renovate's archived responses, without reading or running the analyzed projects."""
from __future__ import annotations

import argparse
import gzip
import io
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def measure(core, excluded, repetitions):
    sys.path.insert(0, str(core))
    from premap import renovate
    import service_registry

    # The archived response already has the package names and files. No source text or CI steps are supplied.
    context = SimpleNamespace(inventory=SimpleNamespace(text=lambda _: ""), stated={})
    entries = service_registry.load()["entries"]
    cases, recordings = {}, 0
    for path in sorted((HERE / "results/premap-runs").glob("*.json.gz")):
        name = path.name.removesuffix(".json.gz")
        if name in excluded:
            continue
        recordings += 1
        runs = json.loads(gzip.decompress(path.read_bytes()))["runs"]
        results = [r["result"] for r in runs if r["command"]["argv"][:1] == ["renovate"]
                   and r["result"]["returncode"] == 0]
        packages = set()
        for result in results:
            facts = renovate.read(context, [], [result])["facts"]
            packages.update((p["ecosystem"], p["name"], p["declared_in"], None, None)
                            for p in facts.get("packages", []) if p["ecosystem"] == "pypi")
        if packages:
            cases[name] = service_registry.Project(sorted(packages), [], lambda _: [])

    elapsed = []
    for _ in range(repetitions):
        start = time.perf_counter()
        signs = {name: sorted({(ident, package, path) for ident, package, path, _line in
                               service_registry.check_packages(entries, case)["signs"]})
                 for name, case in cases.items()}
        elapsed.append(time.perf_counter() - start)
    return {"recordings": recordings, "cases": len(cases), "package_file_pairs": sum(len(c.packages) for c in cases.values()),
            "matched": sum(len(values) for values in signs.values()), "median_seconds": statistics.median(elapsed),
            "seconds": elapsed, "signs": signs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", help="use the core and registry at this git revision; default is the working tree")
    parser.add_argument("--exclude", action="append", default=[], metavar="FIXTURE")
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    with tempfile.TemporaryDirectory() as folder:
        root = REPO
        if args.revision:
            archive = subprocess.check_output(["git", "archive", "--format=zip", args.revision, "--", "daodan/core",
                                               "daodan/data/service-registry.json"], cwd=REPO)
            root = Path(folder)
            with zipfile.ZipFile(io.BytesIO(archive)) as files:
                files.extractall(root)
        result = measure(root / "daodan/core", set(args.exclude), args.repeat)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print({k: v for k, v in result.items() if k != "signs"})


if __name__ == "__main__":
    main()
