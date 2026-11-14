"""microsoft/component-detection: packages from manifests and lockfiles as its scan manifest, read-only.

Default behaviour of v9.1.0 (docs/environment-variables.md, docs/detectors/maven.md and pip.md): it runs
`mvn dependency:tree` beside every root pom.xml (writing bcde.mvndeps there), `go list -m all`, `cargo metadata`,
and `pip install --report` against PyPI for setup.py and requirements.txt; the legacy pip detectors, which run
setup.py, are off by default. Switches here: CD_MAVEN_DISABLE_CLI=true, DisableGoCliScan=true,
DisableRustCliScan=true, PipReportOverrideBehavior=SourceCodeScan (read setup.py and requirements.txt, no feed);
logs in the work directory.

What the answer holds: a component is direct when a dependency graph lists it among its explicitly referenced
components; the graph's key is the file it came from, which goes to `declared_in` or `lockfile` by the rule of
`_sbom.py`. A component in no graph keeps its first location. Components that only other components bring in are
dropped. Scope: `isDevelopmentDependency` is dev, the Maven `dependencyScope` maps to runtime, test or provided.
No unit: the tool names files, not projects.
"""
from __future__ import annotations

import json
from pathlib import Path

import _sbom  # the driver puts tools/ on sys.path

VERSION = "9.1.0"
ENV = {"CD_MAVEN_DISABLE_CLI": "true", "DisableGoCliScan": "true", "DisableRustCliScan": "true",
       "PipReportOverrideBehavior": "SourceCodeScan", "DOTNET_CLI_TELEMETRY_OPTOUT": "1"}
COMMAND = ("component-detection scan --SourceDirectory <fixture> --ManifestFile <out> --Output <work>/cd-logs, with "
           + " ".join(f"{k}={v}" for k, v in ENV.items()))
MAVEN_SCOPE = {"mavencompile": "runtime", "mavenruntime": "runtime", "maventest": "test", "mavenprovided": "provided"}


def command(fixture_dir, work_dir) -> tuple[list, dict, Path]:
    out = Path(work_dir) / "cd.json"
    logs = Path(work_dir) / "cd-logs"
    logs.mkdir(parents=True, exist_ok=True)
    return ["component-detection", "scan", "--SourceDirectory", str(Path(fixture_dir).resolve()), "--ManifestFile",
            str(out), "--Output", str(logs)], dict(ENV), out


def _name(component: dict) -> str | None:
    if component.get("groupId"):
        return f"{component['groupId']}:{component.get('artifactId')}"
    return component.get("name") or component.get("repositoryUrl")


def parse(out: Path, fixture_dir) -> dict:
    data = json.loads(Path(out).read_text(encoding="utf-8"))
    direct = {}  # component id -> files of the graphs that reference it explicitly
    dev = set()
    for key, graph in (data.get("dependencyGraphs") or {}).items():
        for cid in graph.get("explicitlyReferencedComponentIds") or []:
            direct.setdefault(cid, []).append(_sbom.rel(key, fixture_dir))
        dev.update(graph.get("developmentDependencies") or [])
    deps = []
    for found in data.get("componentsFound") or []:
        component = found.get("component") or {}
        cid = component.get("id")
        files = direct.get(cid)
        if files is None:
            if found.get("topLevelReferrers") and not any(r.get("id") == cid for r in found["topLevelReferrers"]):
                continue  # brought in by another component only
            files = [_sbom.rel(p, fixture_dir) for p in (found.get("locationsFoundAt") or [])[:1]] or [None]
        version = component.get("version") or component.get("commitHash")
        for path in files:
            dep = _sbom.place({"name": _name(component)}, path, version)
            if found.get("isDevelopmentDependency") or cid in dev:
                dep["scope"] = "dev"
            elif MAVEN_SCOPE.get(str(found.get("dependencyScope") or "").lower()):
                dep["scope"] = MAVEN_SCOPE[str(found["dependencyScope"]).lower()]
            deps.append(dep)
    return {"dependencies": _sbom.dedupe(deps)}


def run(fixture_dir, work_dir) -> dict:
    argv, env, out = command(fixture_dir, work_dir)
    done = _sbom.sh(argv, work_dir, env)
    if done["rc"] != 0 or not out.is_file():
        raise RuntimeError(f"component-detection rc={done['rc']}: {done['err'][-800:]}")
    return parse(out, fixture_dir)
