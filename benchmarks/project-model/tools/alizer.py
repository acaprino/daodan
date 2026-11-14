"""devfile/alizer, the Go CLI: `alizer analyze <path>` (languages with their frameworks) and `alizer component <path>`.

Version tested: 1.10.0, the last release with binaries (the 1.11.0 release of 2026-10-19 has no assets; its tag has
no `v` prefix). `component --no-port-detection` lists the components of the tree: name, path, languages by weight.
Normalisation: a component is a unit (name and root; the tool gives no kind and no manifest); the languages are the
distinct names of `analyze` (totals, no per-file language); the frameworks of a component are the framework names of
its languages, each with the component as unit and no evidence (the tool names none). Alizer lists a framework under
several names (`Next` and `Next.js`); an entry whose name plus `js` is another entry of the same list is dropped as
the same framework (FOLDED in `detail`). Tools and ports go to `detail`. The tool names no service.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import _fw

VERSION = "1.10.0"
BINARY = _fw.BIN_DIR / "alizer"


def _flat(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def fold(names: list[str]) -> tuple[list[str], list[str]]:
    flat = {n: _flat(n) for n in names}
    kept, dropped = [], []
    for name in dict.fromkeys(names):
        if any(other != name and flat[other] in (flat[name] + "js", flat[name] + "jsx") for other in names):
            dropped.append(name)
        else:
            kept.append(name)
    return kept, dropped


def run(fixture_dir, work_dir) -> dict:
    root, work = Path(fixture_dir).resolve(), Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    out = {}
    for command, argv in (("analyze", ["analyze", root]), ("component", ["component", root, "--no-port-detection"])):
        code, text, err = _fw.execute([BINARY, *argv], work)
        if code != 0:
            raise RuntimeError(f"alizer {command} exited {code}: {(err or text)[-400:]}")
        out[command] = json.loads(text) or []
    languages = list(dict.fromkeys(item["Name"] for item in out["analyze"]))
    units, frameworks, folded, tools = [], [], [], {}
    for component in out["component"]:
        directory = _fw.relative(component["Path"], root)
        units.append({"name": component["Name"], "root": directory})
        names = [f for language in component["Languages"] for f in language.get("Frameworks") or []]
        kept, dropped = fold(names)
        folded += dropped
        frameworks += [{"name": name, "unit": component["Name"]} for name in kept]
        tools[directory] = sorted({t for language in component["Languages"] for t in language.get("Tools") or []})
    return {"languages": [{"language": name} for name in languages], "units": units, "frameworks": frameworks,
            "services": [],
            "detail": {"folded": folded, "tools": tools,
                       "analyze_frameworks": sorted({f for item in out["analyze"] for f in item.get("Frameworks") or []})}}
