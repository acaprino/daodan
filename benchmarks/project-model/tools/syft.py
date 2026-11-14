"""Syft: packages from manifests and lockfiles as syft-json, in its read-only configuration.

Default behaviour of v1.57.1 (measured on Modal and read in the source): it checks for an update at start
(network), and `golang.use-packages-lib` is true (cmd/syft/internal/options/golang.go:106 "this defaults to true",
catalog.go:208), so on a Go module it runs `go list` from PATH, which may download modules. Remote license lookups
(golang, javascript, python), `java.use-network` and `enrich` are off; JavaScript dev dependencies are left out.
Switches here: every one of those set explicitly off, dev dependencies on, the cache inside the work directory.

What the answer holds: every package syft reports, since syft tells neither direct from transitive nor the unit
that owns a package (its `dependency-of` edges link packages, not manifests), and it has no scope. The version goes
to `resolved` or `declared` by the file rule of `_sbom.py`; for a pip requirement the declared value is syft's
`versionConstraint`, the text as written. `line` is never given: syft locates a package by file only.
"""
from __future__ import annotations

import json
from pathlib import Path

import _sbom  # the driver puts tools/ on sys.path

VERSION = "1.57.1"
ENV = {
    "SYFT_CHECK_FOR_APP_UPDATE": "false",
    "SYFT_GOLANG_USE_PACKAGES_LIB": "false",
    "SYFT_GOLANG_SEARCH_REMOTE_LICENSES": "false",
    "SYFT_GOLANG_SEARCH_LOCAL_MOD_CACHE_LICENSES": "false",
    "SYFT_JAVASCRIPT_SEARCH_REMOTE_LICENSES": "false",
    "SYFT_PYTHON_SEARCH_REMOTE_LICENSES": "false",
    "SYFT_JAVA_USE_NETWORK": "false",
    "SYFT_JAVA_RESOLVE_TRANSITIVE_DEPENDENCIES": "false",
    "SYFT_JAVASCRIPT_INCLUDE_DEV_DEPENDENCIES": "true",
    "SYFT_ENRICH": "",
}
COMMAND = "syft scan dir:<fixture> -o syft-json=<out> -q, with " + " ".join(f"{k}={v}" for k, v in ENV.items())
SKIP_VERSIONS = {"", "UNKNOWN", "(devel)"}


def command(fixture_dir, work_dir) -> tuple[list, dict, Path]:
    out = Path(work_dir) / "syft.json"
    env = dict(ENV, SYFT_CACHE_DIR=str(Path(work_dir) / "syft-cache"))
    return ["syft", "scan", f"dir:{Path(fixture_dir).resolve()}", "-o", f"syft-json={out}", "-q"], env, out


def parse(out: Path, fixture_dir) -> dict:
    data = json.loads(Path(out).read_text(encoding="utf-8"))
    deps = []
    for art in data.get("artifacts", []):
        meta = art.get("metadata") or {}
        version = None if art.get("version") in SKIP_VERSIONS else art.get("version")
        name = art.get("name")
        if art.get("type") == "java-archive" and meta.get("pomProperties"):
            pom = meta["pomProperties"]
            name = f"{pom.get('groupId')}:{pom.get('artifactId')}" if pom.get("groupId") else name
        elif (art.get("purl") or "").startswith("pkg:maven/"):
            name = _sbom.purl(art["purl"]).get("name") or name
        for loc in art.get("locations", [])[:1]:
            path = _sbom.rel(loc.get("path"), fixture_dir)
            dep = {"name": name}
            text = meta.get("versionConstraint") if art.get("metadataType") == "python-pip-requirements-entry" else None
            _sbom.place(dep, path, version, text)
            dep["type"] = art.get("type")
            deps.append(dep)
    return {"dependencies": _sbom.dedupe(deps)}


def run(fixture_dir, work_dir) -> dict:
    argv, env, out = command(fixture_dir, work_dir)
    done = _sbom.sh(argv, work_dir, env)
    if done["rc"] != 0 or not out.is_file():
        raise RuntimeError(f"syft rc={done['rc']}: {done['err'][-800:]}")
    return parse(out, fixture_dir)
