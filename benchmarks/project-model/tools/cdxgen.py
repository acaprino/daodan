"""cdxgen: a CycloneDX 1.7 BOM from manifests and lockfiles, in secure mode with dependency installation off.

Default behaviour of v13.7.0: `--install-deps` is true, so it runs the project's package managers and build tools
(npm, pip, mvn, gradle, go, cargo, ...) to resolve the tree; it may query registries (licenses with FETCH_LICENSE,
Maven Central by SHA-1 with SEARCH_MAVEN_ORG on by default, pkg.go.dev with GO_FETCH_VCS). `CDXGEN_SECURE_MODE=true`
turns installs off and, per docs/PERMISSIONS.md, skips Maven, Gradle, sbt, poetry export, dotnet msbuild and SwiftPM,
reading manifests and lockfiles instead; it refuses to run as root. It still runs `go list` on a Go module (seen on
Modal), so an allowlist that names no real command blocks every child process and one that names only localhost
blocks every host. Secure mode also turns `--fail-on-error` on (bin/cdxgen.js:429-432), so a blocked `go list` ends
the run with exit 1 and no BOM; `--no-fail-on-error` lets it fall back to reading go.mod. Switches here:
CDXGEN_SECURE_MODE=true, --no-install-deps, --no-fail-on-error, FETCH_LICENSE=false, SEARCH_MAVEN_ORG=false,
GO_FETCH_VCS=false, CDXGEN_ALLOWED_COMMANDS=none, CDXGEN_ALLOWED_HOSTS=localhost, --no-progress; non-root user.

What the answer holds: units are the BOM's main component (root ".") and the workspace members cdxgen names
(`metadata.component.components`, `cdx:npm:isWorkspace`, `internal:workspaceRef`) when it gives their folder. A
component is a direct dependency of a unit when the unit's `dependsOn` lists it; a component listed only by other
components is transitive and dropped; one listed by nobody stays without a unit. Scope: a `cdx:pyproject:group`
is `test` or `dev`, `cdx:cargo:dependencyKind` and `cdx:npm:package:development` as they say, CycloneDX `required`
is `runtime`; CycloneDX `optional` means only "not needed at run time" (dev, test, build or an extra), so it leaves
the scope out. The files of `internal:SrcFile` and of the evidence go by the rule of `_sbom.py`.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

import _sbom  # the driver puts tools/ on sys.path

VERSION = "13.7.0"
ENV = {"CDXGEN_SECURE_MODE": "true", "FETCH_LICENSE": "false", "SEARCH_MAVEN_ORG": "false", "GO_FETCH_VCS": "false",
       "CDXGEN_ALLOWED_COMMANDS": "none", "CDXGEN_ALLOWED_HOSTS": "localhost", "NO_COLOR": "1"}
FLAGS = ["--no-install-deps", "--no-fail-on-error", "--no-progress", "--color", "never"]
COMMAND = "cdxgen " + " ".join(FLAGS) + " -o <out> <fixture>, as a non-root user, with " + " ".join(
    f"{k}={v}" for k, v in ENV.items())
USER = "scan"  # the driver runs this tool as that user; cdxgen secure mode exits as root


def command(fixture_dir, work_dir) -> tuple[list, dict, Path]:
    out = Path(work_dir) / "cdxgen.json"
    env = dict(ENV, CDXGEN_TEMP_DIR=str(Path(work_dir) / "cdxgen-tmp"))
    Path(env["CDXGEN_TEMP_DIR"]).mkdir(parents=True, exist_ok=True)
    return ["cdxgen", *FLAGS, "-o", str(out), str(Path(fixture_dir).resolve())], env, out


def _props(item: dict) -> dict:
    return {p.get("name"): p.get("value") for p in item.get("properties") or []}


def _unit_name(item: dict) -> str:
    parts = _sbom.purl(item.get("purl") or item.get("bom-ref") or "")
    if parts.get("name"):
        return parts["name"]
    return _sbom.package_name("", item.get("group"), item.get("name") or "")


def _kind(item: dict) -> str | None:
    return _sbom.KIND.get(_sbom.purl(item.get("purl") or item.get("bom-ref") or "").get("type", ""))


def _canon(ref) -> str:
    """One spelling for a reference: cdxgen writes a member's purl percent-encoded in `internal:workspaceRef`
    and its bom-ref plain."""
    return unquote(ref or "")


def parse(out: Path, fixture_dir) -> dict:
    bom = json.loads(Path(out).read_text(encoding="utf-8"))
    base = Path(out).parent  # cdxgen writes paths relative to its working folder
    main = (bom.get("metadata") or {}).get("component") or {}
    components = bom.get("components") or []
    items = {}  # canonical reference -> component, under its bom-ref and its purl
    for item in [main, *(main.get("components") or []), *components]:
        for key in (item.get("bom-ref"), item.get("purl")):
            if key:
                items.setdefault(_canon(key), item)

    def ref(value) -> str:
        item = items.get(_canon(value))
        return _canon(item.get("bom-ref") or item.get("purl")) if item else _canon(value)

    unit_roots = {}  # canonical bom-ref -> root folder or None
    if main.get("bom-ref"):
        unit_roots[ref(main["bom-ref"])] = "."
    for member in main.get("components") or []:
        unit_roots.setdefault(ref(member.get("bom-ref")), None)
    for comp in components:
        props = _props(comp)
        if "true" in (props.get("cdx:npm:isWorkspace"), props.get("cdx:npm:is_workspace")):
            folder = props.get("cdx:npm:resolvedPath")
            if folder:
                unit_roots[ref(comp.get("bom-ref"))] = _sbom.rel(folder, fixture_dir, base)
            else:
                unit_roots.setdefault(ref(comp.get("bom-ref")), None)
        ws = props.get("internal:workspaceSrcFile")
        if props.get("internal:workspaceRef") and ws:
            folder = str(PurePosixPath(_sbom.rel(ws, fixture_dir, base) or ".").parent)
            unit_roots[ref(props["internal:workspaceRef"])] = folder
    for member in main.get("components") or []:
        props = _props(member)
        path = props.get("cdx:npm:resolvedPath") or props.get("internal:SrcFile")
        if path and unit_roots.get(ref(member.get("bom-ref"))) is None:
            path = _sbom.rel(path, fixture_dir, base)
            unit_roots[ref(member.get("bom-ref"))] = path if not PurePosixPath(path).suffix else str(PurePosixPath(path).parent)
    units, names = [], {}
    for key, root in unit_roots.items():
        item = items.get(key) or {}
        names[key] = _unit_name(item) if item else None
        if root is None or not item:
            continue
        unit = {"name": names[key], "root": root}
        if _kind(item):
            unit["kind"] = _kind(item)
        units.append(unit)
    parents = {}
    for edge in bom.get("dependencies") or []:
        for child in edge.get("dependsOn") or []:
            parents.setdefault(ref(child), set()).add(ref(edge.get("ref")))
    deps = []
    for comp in components:
        key = ref(comp.get("bom-ref"))
        if key in unit_roots:
            continue
        props = _props(comp)
        owners = {p for p in parents.get(key, ()) if p in unit_roots and names.get(p)}
        if props.get("internal:workspaceRef") and ref(props["internal:workspaceRef"]) in unit_roots:
            owners.add(ref(props["internal:workspaceRef"]))
        if parents.get(key) and not owners:
            continue  # listed only by other components: transitive
        dep = {"name": _unit_name(comp)}
        evidence = [m.get("value") for i in (comp.get("evidence") or {}).get("identity") or []
                    for m in i.get("methods") or [] if m.get("value")]
        files = [_sbom.rel(f, fixture_dir, base) for f in [props.get("internal:SrcFile"), *evidence] if f]
        lock = next((f for f in files if _sbom.is_lock(f)), None)
        manifest = next((f for f in files if f and not _sbom.is_lock(f)), None)
        if lock:
            _sbom.place(dep, lock, comp.get("version"))
        if manifest:
            dep["declared_in"] = manifest
            if not lock and comp.get("version"):
                dep["declared"] = comp["version"]
        group = props.get("cdx:pyproject:group")
        if group:  # a Poetry or PEP 735 group is never the runtime set
            dep["scope"] = "test" if _sbom.scope(group) == "test" else "dev"
        elif _sbom.scope(props.get("cdx:cargo:dependencyKind")):
            dep["scope"] = _sbom.scope(props["cdx:cargo:dependencyKind"])
        elif props.get("cdx:npm:package:development") == "true":
            dep["scope"] = "dev"
        elif comp.get("scope") == "required":
            dep["scope"] = "runtime"
        for owner in sorted(o for o in owners if names.get(o)) or [None]:
            deps.append(dict(dep, unit=names[owner]) if owner else dep)
    return {"units": _sbom.dedupe(units), "dependencies": _sbom.dedupe(deps)}


def run(fixture_dir, work_dir) -> dict:
    argv, env, out = command(fixture_dir, work_dir)
    done = _sbom.sh(argv, work_dir, env)
    if done["rc"] != 0 or not out.is_file():
        raise RuntimeError(f"cdxgen rc={done['rc']}: {done['err'][-800:]}")
    return parse(out, fixture_dir)
