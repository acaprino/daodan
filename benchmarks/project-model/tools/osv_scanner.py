"""osv-scanner (OSV-SCALIBR extractors inside): packages from manifests and lockfiles as JSON, read-only.

Default behaviour of v2.7.1: every package is sent to the OSV API for vulnerabilities, manifests such as `pom.xml`
are resolved transitively through deps.dev (`--data-source deps.dev`), and call analysis can build Go and Rust code
(Rust "will run build scripts", says `--help`). Switches here: `--offline` (no network feature: local vulnerability
matching, no deps.dev), `--no-resolve`, `--no-call-analysis=all`, `--all-packages` (list packages, not only the
vulnerable ones). With `--offline` and no local database the vulnerability step fails and the exit code is 127 (or
1), yet the package list is complete and written: the adapter reads the JSON whatever the exit code.

What the answer holds: every package, since osv-scanner tells neither direct from transitive nor the owning unit;
`dependency_groups` as the scope when the word names one (`requires` of Conan names none); the version by the file rule of `_sbom.py` (osv-scanner calls
every source a lockfile, including `go.mod` and `requirements.txt`). No line: the location is the file only.
"""
from __future__ import annotations

import json
from pathlib import Path

import _sbom  # the driver puts tools/ on sys.path

VERSION = "2.7.1"
FLAGS = ["-r", "--format", "json", "--all-packages", "--offline", "--no-resolve", "--no-call-analysis=all",
         "--verbosity", "error"]
COMMAND = "osv-scanner scan source " + " ".join(FLAGS) + " <fixture> > <out>"
STDOUT = True  # the JSON comes on stdout, whatever the exit code
OK = (0, 1, 127, 128)  # 1: vulnerabilities, 127/128: no offline database or no package; the JSON is still written


def command(fixture_dir, work_dir) -> tuple[list, dict, Path]:
    out = Path(work_dir) / "osv.json"
    return ["osv-scanner", "scan", "source", *FLAGS, str(Path(fixture_dir).resolve())], {}, out


def parse(out: Path, fixture_dir) -> dict:
    data = json.loads(Path(out).read_text(encoding="utf-8"))
    deps = []
    for result in data.get("results") or []:
        path = _sbom.rel((result.get("source") or {}).get("path"), fixture_dir)
        for entry in result.get("packages") or []:
            pkg = entry.get("package") or {}
            name = pkg.get("name")
            if pkg.get("ecosystem") == "Maven" and name and ":" not in name and pkg.get("purl"):
                name = _sbom.purl(pkg["purl"]).get("name") or name
            dep = _sbom.place({"name": name}, path, pkg.get("version"))
            groups = [g for g in entry.get("dependency_groups") or [] if g]
            if groups and _sbom.scope(groups[0]):
                dep["scope"] = _sbom.scope(groups[0])
            deps.append(dep)
    return {"dependencies": _sbom.dedupe(deps)}


def run(fixture_dir, work_dir) -> dict:
    argv, env, out = command(fixture_dir, work_dir)
    done = _sbom.sh(argv, work_dir, env)
    out.write_text(done["out"] if done["out"].strip() or done["rc"] != 128 else "{}", encoding="utf-8")
    if done["rc"] not in OK or not out.read_text(encoding="utf-8").strip():
        raise RuntimeError(f"osv-scanner rc={done['rc']}: {done['err'][-800:]}")
    return parse(out, fixture_dir)
