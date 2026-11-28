"""Cache the execution of declared test commands independently of the edges that could be placed."""
from __future__ import annotations

import hashlib
import json
from functools import cache
from pathlib import Path

from run_store import _write_json_atomic


@cache
def recorder_fingerprint(module: str) -> str:
    """Hash the installed observer, its recorder assets and the shared execution and join code once per process."""
    folder = Path(__file__).resolve().parent
    core = folder.parent
    files = {folder / "__init__.py", folder / "execution_cache.py", core / "container.py", core / "preparation.py",
             core / "code_graph.py", core / "edge_store.py"}
    name = module.rpartition(".")[2]
    if name.isidentifier() and (folder / f"{name}.py").is_file():
        files.add(folder / f"{name}.py")
        for asset in folder.glob(f"{name}_record*"):
            if asset.is_file():
                files.add(asset)
            elif asset.is_dir():
                files.update(path for path in asset.rglob("*") if path.is_file())
    if name in ("clang", "rust"):
        files.update((folder / "callgrind.py", folder / "callgrind_sites.py"))
    if name == "javascript":
        files.update((folder / "control_coverage.js", folder / "playwright_controls.cjs",
                      folder / "playwright_prepare.cjs", core / "node_preparation.py"))
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.relative_to(core).as_posix().encode() + b"\0")
        digest.update(hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).digest())
    return digest.hexdigest()


def key(binding: dict, graphs: dict, languages: list[str], observer, plan: dict) -> str:
    inputs = [binding["manifest_digest"], binding["parser_fingerprint"], binding["resolver_version"],
              observer.NAME, observer.VERSION, recorder_fingerprint(getattr(observer, "__name__", "")),
              [(language, graphs[language]["engine"], graphs[language].get("version"),
                graphs[language].get("adapter_digest")) for language in languages],
              plan]
    return hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read(path: Path, expected: str, coverage: dict, runs: int) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if (value["key"] != expected or not isinstance(value["tests"], list) or len(value["tests"]) != runs or
                any(test is not None and not isinstance(test, dict) for test in value["tests"]) or
                not isinstance(value["outcomes"], dict) or type(value["attempt"]) is not int or
                set(value["outcomes"]) != set(coverage)):
            return {}
        # A static analyzer can rebuild its graph on the same snapshot and replace the observed rows.
        for language, outcome in value["outcomes"].items():
            if outcome["state"] == "observed" and coverage[language].get("observed", {}).get("at") != value["at"]:
                return {}
        return value
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {}


def finished(test: dict | None) -> bool:
    return bool(test and (test.get("equivalent_completed") or
                          test.get("state") == "ran" and test.get("exit_code") in (None, 0)))


def update_tests(tests: list, retry: list[int], planned: list[dict], result: dict) -> None:
    """Observers may reorder receipts or skip alternative build tools that run the same suite."""
    unassigned = set(range(len(planned)))
    for test in result["runs"]:
        if len(planned) == len(result["runs"]) == 1:
            candidates = [0]
        else:
            candidates = [index for index in sorted(unassigned) if all(planned[index][key] == test[key]
                          for key in ("root", "declared_in", "runner", "tool", "project", "argv", "python_request")
                          if key in planned[index] and key in test)]
        if candidates:
            index = candidates[0]
            tests[retry[index]] = with_prior_documents(test, tests[retry[index]])
            unassigned.discard(index)
    for index in result.get("equivalent_completed", ()):
        if index in unassigned:
            tests[retry[index]] = {"equivalent_completed": True}


def with_prior_documents(test: dict, prior: dict | None) -> dict:
    """A retried browser suite opens new documents. Keep earlier counts and the originating attempt's records."""
    old = (prior or {}).get("controls") or {}
    if not old.get("documents"):
        return test
    current = test.get("controls") or {}
    counts = {key: old[key] + current.get(key, 0) for key in ("documents", "observed", "pending")}
    counts["status"] = "observed" if old["status"] == current.get("status") == "observed" else "partial"
    return {**test, "controls": counts}


def merge_sites(old: list[dict], new: list[dict]) -> list[dict]:
    if not old:
        return new
    # The same call can have multiple real destinations. A retry can observe a different one.
    sites = {}
    for site in [*old, *new]:
        place = tuple(site[field] for field in ("file", "line", "column", "name", "role"))
        record, callees = sites.setdefault(place, (site, {}))
        for callee in site["callees"]:
            callees[json.dumps(callee, sort_keys=True)] = callee
    return [{**site, "callees": list(callees.values())} for site, callees in sites.values()]


def save(path: Path, expected: str, tests: list, outcomes: dict, at: str, sites: list, attempt: int,
         ui_gaps: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cache = {"key": expected, "tests": tests, "outcomes": outcomes, "at": at, "attempt": attempt, "ui_gaps": ui_gaps}
    # Completed commands only need their summary. Keep raw observations across an incomplete batch until the
    # retry can join the union on the original static graph, including evidence from a timed-out process.
    if not all(finished(test) for test in tests):
        cache.update(sites=sites)
    _write_json_atomic(path, cache)
