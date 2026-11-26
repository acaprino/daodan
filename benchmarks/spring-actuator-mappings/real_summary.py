"""What the real applications say, from `modal_real.py`'s answers and the sources at the pinned commits (text only, fetched on the host
into a folder outside the repository and never run): per application, the routes of the launcher, how many resolve to one file
and line (`place_check.py` over the snapshot's java parse), the gaps and their causes, and the routes of the pinned Noir against
them. Writes `results/real/<name>-summary.json` and prints it.

    python -I benchmarks/spring-actuator-mappings/real_summary.py <a folder outside the repository: the sources are fetched into it at the commits recorded in the answers>
"""
import collections
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import place_check  # noqa: E402

RESULTS = pathlib.Path(os.environ.get("REAL_RESULTS") or HERE / "results" / "real")
PREFERENCE = ("actuator", "actuator-port0", "handler-methods", "aot", "service-actuator", "service-handler-methods", "service-aot", "lazy", "lazy-handler-methods")


def module_file(module: str) -> str:
    return module.replace("/", "_") or "root"


def keys(row: dict) -> list[tuple[str, str]]:
    return [(method, pattern) for method in (row["methods"] or ["ANY"]) for pattern in row["patterns"]]


def fetch(name: str, real: dict, root: pathlib.Path) -> pathlib.Path:
    """The sources at the recorded commit, as text, into `root/<name>` (untrusted: only read, never run)."""
    import io
    import tarfile
    import urllib.request

    destination = root / name
    if not destination.exists():
        data = urllib.request.urlopen(f"https://codeload.github.com/{real['repository']}/tar.gz/{real['commit']}", timeout=120).read()
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            members = archive.getmembers()
            top = members[0].name.split("/")[0]
            for member in members:
                member.name = member.name[len(top):].lstrip("/")
            destination.mkdir(parents=True)
            archive.extractall(destination, members=[member for member in members if member.name], filter="data")
    return destination


def summarize(name: str, sources: pathlib.Path) -> dict:
    real = json.loads((RESULTS / f"{name}-real.json").read_text(encoding="utf-8"))
    sources = fetch(name, real, sources)
    files = collections.defaultdict(list)  # the last two parts of a path -> the files of the snapshot that end so
    for path in sources.rglob("*.java"):
        files[path.name].append(path.relative_to(sources).as_posix())
    parsed = {}

    def declared(rel: str):
        if rel not in parsed:
            parsed[rel] = place_check.declarations((sources / rel).read_text(encoding="utf-8", errors="replace"), rel)
        return parsed[rel]

    placed_total, rows_total, causes = 0, 0, collections.Counter()
    actuator_keys, handler_of = {}, {}
    modules = []
    for module in real.get("modules", ()):
        runs = {run["label"]: run for run in module["runs"]}
        best = next((runs[label] for label in PREFERENCE if label in runs and runs[label]["routes"]), None)
        entry = {"module": module["module"] or ".", "start_class": module["start_class"], "boot_version": module["boot_version"],
                 "runs": [{"label": run["label"], "exit": run["returncode"], "seconds": run["seconds"], "peak_memory_mb": run["peak_memory_mb"],
                           "rows": len(run["routes"]), "listeners": [(l["port"], l.get("gone_s")) for l in run["listeners"]],
                           "error": (run["error"] or "")[:300] or None} for run in module["runs"]]}
        if best is None:
            modules.append(entry)
            continue
        javap = RESULTS / f"{name}-javap-{module_file(module['module'])}.txt"
        classes = place_check.javap_classes(javap.read_text(encoding="utf-8")) if javap.is_file() else {}

        def source(rel: str, hint=module["module"]) -> list:
            candidates = [path for path in files.get(rel.rpartition("/")[2], ()) if path == rel or path.endswith("/" + rel)]
            near = [path for path in candidates if hint and path.startswith(hint + "/")]
            return [(path, declared(path)) for path in (near or candidates)]

        project, framework, functions = [], 0, 0
        for row in best["routes"]:
            if "class" not in row:
                functions += 1
                continue
            if not any(binary.replace("$", ".") == row["class"] for binary in classes):
                framework += 1
                continue
            project.append(row)
        gaps = collections.Counter()
        per_key = {}
        for row in project:
            where = place_check.place(row, classes, source)
            for key in keys(row):
                per_key[key] = where
                if "gap" in where:
                    gaps[where["gap"]] += 1
        for key, where in per_key.items():
            actuator_keys[key] = where
        entry.update({"used": best["label"], "rows": len(best["routes"]), "project_rows": len(project), "framework_rows": framework,
                      "function_rows": functions, "routes": len(per_key),
                      "placed": sum("file" in where for where in per_key.values()), "gaps": dict(gaps)})
        modules.append(entry)
        for where in per_key.values():
            rows_total += 1
            placed_total += "file" in where
            if "gap" in where:
                causes[where["gap"]] += 1
    noir = real.get("noir", {})
    endpoints = noir.get("endpoints", [])
    prefix = f"/work/{name}/"
    java, java_without_handler = {}, []
    other = collections.Counter()
    for endpoint in endpoints:
        handler = endpoint.get("handler") or {}
        where = ((endpoint.get("code_paths") or [{}])[0].get("path") or "").removeprefix(prefix)
        if handler.get("path", "").endswith(".java"):
            java[(endpoint["method"], endpoint["url"])] = {"file": handler["path"].removeprefix(prefix), "line": handler.get("line"), "name": handler.get("name")}
        elif where.endswith(".java"):  # a route Noir cites in a Java file and names no handler for
            java_without_handler.append([endpoint["method"], endpoint["url"], where])
        else:
            other[where.rpartition("/")[2] if where.endswith(("pom.xml", ".yml", ".yaml", ".properties")) else "a file of the project that is not code (static)"] += 1
    both = sorted(set(actuator_keys) & set(java))
    agree = {"file": 0, "line_in_span": 0, "same_line": 0}
    differ = []
    for key in both:
        mine, theirs = actuator_keys[key], java[key]
        if "file" not in mine:
            continue
        agree["file"] += mine["file"] == theirs["file"]
        inside = theirs["line"] is not None and mine["span"][0] <= theirs["line"] <= mine["span"][1]
        agree["line_in_span"] += mine["file"] == theirs["file"] and inside
        agree["same_line"] += mine["file"] == theirs["file"] and theirs["line"] == mine["line"]
        if mine["file"] != theirs["file"] or not inside:
            differ.append({"route": key, "launcher": [mine["file"], mine["line"]], "noir": [theirs["file"], theirs["line"]]})
    used = sorted({module.get("used") for module in modules if module.get("used")})
    summary = {"name": name, "repository": real["repository"], "commit": real["commit"], "licence": real["licence"],
               "launcher_answers_used": used, "needs_a_service": any(label.startswith("service-") for label in used),
               "restore_rc": real.get("restore_rc"), "built_rc": real.get("built_rc"),
               "build_offline_after_restore": {"rc": real.get("build", {}).get("returncode"), "seconds": real.get("build", {}).get("seconds"),
                                               "missing": len(real.get("build", {}).get("missing_have", {}))},
               "build_again_offline": {"rc": real.get("build_again", {}).get("returncode"), "seconds": real.get("build_again", {}).get("seconds")},
               "modules": modules,
               "launcher_routes": len(actuator_keys), "placed": sum("file" in where for where in actuator_keys.values()),
               "gap_causes": dict(causes),
               "noir": {"seconds": noir.get("seconds"), "peak_memory_mb": noir.get("peak_memory_mb"), "endpoints": len(endpoints),
                        "with_java_handler": len(java), "in_java_without_handler": java_without_handler, "other": dict(other)},
               "compare": {"both": len(both), "only_launcher": len(set(actuator_keys) - set(java)), "only_noir_java": len(set(java) - set(actuator_keys)),
                           "agree": agree, "differ": differ[:20]},
               "only_launcher_examples": sorted(set(actuator_keys) - set(java))[:15],
               "only_noir_examples": sorted(set(java) - set(actuator_keys))[:15],
               "left_behind": real.get("left_behind"), "prep_left_behind": real.get("prep_left_behind")}
    (RESULTS / f"{name}-summary.json").write_bytes((json.dumps(summary, indent=1, ensure_ascii=False, default=list) + "\n").encode("utf-8"))
    return summary


def fixture() -> dict:
    """Noir over the fixture against the routes Spring gives (`place-check.json`, written by `place_check.py` from `modal_probe.py`'s answers).
    Two overloads on one method and path are two handlers of one route: the route's handlers are a set."""
    noir = json.loads((RESULTS / "fixture-noir.json").read_text(encoding="utf-8"))
    checked = json.loads((HERE / "results" / "place-check.json").read_text(encoding="utf-8"))
    mine, theirs = collections.defaultdict(set), collections.defaultdict(set)
    for row in checked["rows"]:
        if "file" in row:
            mine[(row["method"], row["path"])].add((row["file"], row["line"]))
    for endpoint in noir["endpoints"]:
        handler = endpoint.get("handler") or {}
        found = theirs[(endpoint["method"], endpoint["url"])]
        if handler.get("path"):
            found.add((handler["path"].removeprefix("/fixture-src/main/java/"), handler.get("line")))
    both = sorted(set(mine) & set(theirs))
    summary = {"launcher_routes": len(mine), "noir_routes": len(theirs), "both": len(both),
               "both_with_a_handler_in_noir": sum(bool(theirs[key]) for key in both),
               "same_handlers": sum(theirs[key] == mine[key] for key in both),
               "route_without_handler_in_noir": [key for key in both if not theirs[key]],
               "only_launcher": sorted(set(mine) - set(theirs)), "only_noir": sorted(set(theirs) - set(mine))}
    (RESULTS / "fixture-summary.json").write_bytes((json.dumps(summary, indent=1, ensure_ascii=False, default=list) + chr(10)).encode("utf-8"))
    return summary


if __name__ == "__main__":
    root = pathlib.Path(sys.argv[1])
    for app in ("petclinic", "ruoyi", "microservices"):
        if (RESULTS / f"{app}-real.json").is_file():
            print(json.dumps(summarize(app, root), indent=1, ensure_ascii=False, default=list)[:6000])
    if (RESULTS / "fixture-noir.json").is_file() and (HERE / "results" / "place-check.json").is_file():
        print(json.dumps(fixture(), ensure_ascii=False, default=list))
