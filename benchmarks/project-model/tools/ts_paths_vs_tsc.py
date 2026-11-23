"""How far Daodan's TypeScript path reader is from `tsc`, on the recorded fixtures.

Reads `results/native_tsc.json` (`tsc --showConfig` per tsconfig, recorded on Modal) and calls
`import_resolution.ts_path_config` on `fixtures/<name>`. It only reads JSON and runs no project code.
Per tsc unit and pattern: same, different, missing (tsc only) or extra (Daodan only).
Writes `results/ts_paths_vs_tsc.json`.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
sys.path.insert(0, str(BENCH.parents[1] / "daodan/core"))
import import_resolution

RECORDED = BENCH / "results/native_tsc.json"
RESULT = BENCH / "results/ts_paths_vs_tsc.json"
CLASSES = ("same", "different", "missing", "extra")


def daodan_paths(fixture: Path, unit_root: str) -> dict[str, list[str]]:
    """The `paths` of the nearest config folder at or above the unit root, targets relative to the fixture."""
    fixture = fixture.resolve()
    configs = import_resolution.ts_path_config(fixture)["configs"]
    folder = (fixture / unit_root).resolve()
    while True:
        if folder.as_posix() in configs:
            found = configs[folder.as_posix()].get("paths") or {}
            return {pattern: [Path(os.path.relpath(os.path.normpath(t), fixture)).as_posix() for t in targets]
                    for pattern, targets in found.items()}
        if folder == fixture or fixture not in folder.parents:
            return {}
        folder = folder.parent


def classify(tsc: dict, daodan: dict) -> dict[str, str]:
    result = {}
    for pattern in sorted(set(tsc) | set(daodan)):
        if pattern not in daodan:
            result[pattern] = "missing"
        elif pattern not in tsc:
            result[pattern] = "extra"
        else:
            result[pattern] = "same" if tsc[pattern] == daodan[pattern] else "different"
    return result


def has_tree(folder: Path) -> bool:
    """The real-* fixtures keep only expected.json and source.json here: their tree is not in the repository."""
    return any(f.name not in ("expected.json", "source.json") for f in folder.rglob("*") if f.is_file())


def compare() -> dict:
    recorded = json.loads(RECORDED.read_text())
    named, quiet, errors, absent = {}, 0, 0, 0
    counts = dict.fromkeys(CLASSES, 0)
    for name, run in sorted(recorded["fixtures"].items()):
        folder = BENCH / "fixtures" / name
        if not has_tree(folder):
            absent += 1
            continue
        errors += bool(run.get("error"))
        units = {}
        for unit in sorted((run.get("output") or {}).get("units", []), key=lambda u: u["root"]):
            tsc = unit["config"].get("paths") or {}
            daodan = daodan_paths(folder, unit["root"])
            if not tsc and not daodan:
                continue
            units[unit["root"]] = {p: {"class": c, "tsc": tsc.get(p), "daodan": daodan.get(p)}
                                   for p, c in classify(tsc, daodan).items()}
            for c in units[unit["root"]].values():
                counts[c["class"]] += 1
        if units:
            named[name] = {"tsc_error": run["error"], "units": units} if run.get("error") else {"units": units}
        else:
            quiet += 1
    return {"tsc": recorded["version"], "daodan": "import_resolution.ts_path_config", "counts": counts,
            "fixtures_without_local_tree": absent, "tsc_errors": errors, "fixtures_without_paths": quiet, "fixtures": named}


def main() -> None:
    result = compare()
    RESULT.write_text(json.dumps(result, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"{len(result['fixtures'])} fixtures with paths, {result['fixtures_without_paths']} without; "
          f"tsc errors: {result['tsc_errors']}; " + ", ".join(f"{c} {n}" for c, n in result["counts"].items()))
    for name, data in result["fixtures"].items():
        for root, patterns in data["units"].items():
            for p, c in patterns.items():
                if c["class"] != "same":
                    print(f"  {name} [{root}] {p}: {c['class']}")


if __name__ == "__main__":
    main()
