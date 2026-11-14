"""Trivy `fs`: packages from manifests and lockfiles as Trivy JSON, in its read-only configuration.

Default behaviour of v0.76.2: it downloads the vulnerability database on the first run (the `vuln` scanner is on by
default), checks for a new version and announcements, sends anonymous telemetry, downloads the Java index database
when it meets a jar, and for `pom.xml` asks the remote Maven repositories for parents and versions. Development
dependencies are left out of the report. Switches here: `--scanners license` (local files only; the vulnerability
scanner and its database stay off), `--offline-scan`, `--skip-db-update`, `--skip-java-db-update`,
`--skip-vex-repo-update`, `--skip-version-check`, `--disable-telemetry`, `--include-dev-deps`, cache in the work
directory.

What the answer holds: Trivy marks each package `root`, `workspace`, `direct` or `indirect` for the formats where
it builds the graph. `indirect` packages are dropped; `root` and `workspace` packages become units when they have a
name; a `direct` package gets as unit each named root or workspace whose `DependsOn` lists it. A package without a
relationship stays (Trivy does not tell). `Dev: true` is scope `dev`; Trivy gives no other scope. `line` is the
first line of the package in its file when Trivy reports it.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

import _sbom  # the driver puts tools/ on sys.path

VERSION = "0.76.2"
FLAGS = ["--format", "json", "--list-all-pkgs", "--scanners", "license", "--include-dev-deps", "--offline-scan",
         "--skip-db-update", "--skip-java-db-update", "--skip-vex-repo-update", "--skip-version-check",
         "--disable-telemetry", "--quiet"]
COMMAND = "trivy fs " + " ".join(FLAGS) + " --cache-dir <work>/trivy-cache -o <out> <fixture>"


def command(fixture_dir, work_dir) -> tuple[list, dict, Path]:
    out = Path(work_dir) / "trivy.json"
    argv = ["trivy", "fs", *FLAGS, "--cache-dir", str(Path(work_dir) / "trivy-cache"), "-o", str(out),
            str(Path(fixture_dir).resolve())]
    return argv, {}, out


def parse(out: Path, fixture_dir) -> dict:
    data = json.loads(Path(out).read_text(encoding="utf-8"))
    deps, units = [], []
    for result in data.get("Results") or []:
        if result.get("Class") != "lang-pkgs":
            continue
        target = _sbom.rel(result.get("Target"), fixture_dir)
        packages = result.get("Packages") or []
        owners = {}  # package ID -> names of the root or workspace packages that list it
        for pkg in packages:
            if pkg.get("Relationship") in ("root", "workspace"):
                if pkg.get("Name"):
                    unit = {"name": _name(pkg, result)}
                    kind = _sbom.KIND.get(result.get("Type", ""), None) or _sbom.KIND.get(
                        {"npm": "npm", "yarn": "npm", "pnpm": "npm", "bun": "npm", "pip": "pypi", "poetry": "pypi",
                         "uv": "pypi", "pipenv": "pypi", "cargo": "cargo", "gomod": "golang", "pom": "maven",
                         "gradle": "maven", "composer": "composer", "nuget": "nuget", "dotnet-core": "nuget",
                         "bundler": "gem", "pub": "pub", "swift": "swift", "hex": "hex"}.get(result.get("Type", "")))
                    if kind:
                        unit["kind"] = kind
                    if pkg.get("Relationship") == "root" and target and not _sbom.is_lock(target):
                        unit["manifest"] = target
                        unit["root"] = str(PurePosixPath(target).parent)
                        units.append(unit)  # a unit without its folder cannot be placed: it stays out
                for child in pkg.get("DependsOn") or []:
                    owners.setdefault(child, []).append(_name(pkg, result) if pkg.get("Name") else None)
        for pkg in packages:
            relation = pkg.get("Relationship")
            if relation in ("root", "workspace", "indirect"):
                continue
            base = {"name": _name(pkg, result)}
            _sbom.place(base, target, pkg.get("Version"))
            if pkg.get("Dev"):
                base["scope"] = "dev"
            lines = [loc.get("StartLine") for loc in pkg.get("Locations") or [] if loc.get("StartLine")]
            if lines:
                base["line"] = lines[0]
            named = [u for u in owners.get(pkg.get("ID"), []) if u]
            for unit in named or [None]:
                deps.append(dict(base, unit=unit) if unit else base)
    return {"units": _sbom.dedupe(units), "dependencies": _sbom.dedupe(deps)}


def _name(pkg: dict, result: dict) -> str:
    name = pkg.get("Name") or pkg.get("ID") or ""
    if result.get("Type") in ("pom", "gradle", "jar", "sbt") and ":" not in name and "/" in name:
        name = name.replace("/", ":")
    return name


def run(fixture_dir, work_dir) -> dict:
    argv, env, out = command(fixture_dir, work_dir)
    done = _sbom.sh(argv, work_dir, env)
    if done["rc"] != 0 or not out.is_file():
        raise RuntimeError(f"trivy rc={done['rc']}: {done['err'][-800:]}")
    return parse(out, fixture_dir)
