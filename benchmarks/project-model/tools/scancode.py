"""ScanCode toolkit, package detection only (`--package`): packages and their dependencies from manifests and
lockfiles, as ScanCode JSON.

Default behaviour of v32.5.0: it reads files and starts no build tool; it has no network feature in `--package`
(license detection uses the index built at install time, `scancode-reindex-licenses` in the image). Its cost is the
start: loading the license index and the plugin set. Switches here: `--package` only, `--strip-root`, one process
(`-n 1`), `--quiet`, a 300 s timeout per file.

What the answer holds: units are the packages ScanCode assembles from a manifest (name, kind from the package
type, manifest and its folder). Dependencies are those ScanCode marks `is_direct`, with the unit of
`for_package_uid`; the declared value is `extracted_requirement` (for a pip requirement without the leading name);
the resolved version comes from the same-named entry ScanCode reads from a lockfile for the same unit, or from the
version of the entry when the dependency itself comes from a lockfile. Maven entries of `dependencyManagement` and
BOM `import` are dropped: ScanCode itself scopes them so. Scope from ScanCode's scope word; a runtime or unnamed
scope ScanCode marks `is_optional` is `optional` (an extra's name is the scope word there).
"""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

import _sbom  # the driver puts tools/ on sys.path

VERSION = "32.5.0"
FLAGS = ["--package", "--strip-root", "-n", "1", "--quiet", "--timeout", "300"]
COMMAND = "scancode " + " ".join(FLAGS) + " --json <out> <fixture>"
NOT_DEPENDENCIES = {"dependencymanagement", "import"}  # Maven: versions managed for others, BOMs imported


def command(fixture_dir, work_dir) -> tuple[list, dict, Path]:
    out = Path(work_dir) / "scancode.json"
    return ["scancode", *FLAGS, "--json", str(out), str(Path(fixture_dir).resolve())], {}, out


def _requirement(kind: str, text):
    if text is None:
        return None
    text = str(text).strip()
    if kind == "pypi":
        text = re.sub(r"^[A-Za-z0-9][A-Za-z0-9._-]*\s*(\[[^\]]*\])?\s*", "", text)
        return text or None
    return text or None


def parse(out: Path, fixture_dir) -> dict:
    data = json.loads(Path(out).read_text(encoding="utf-8"))
    units, unit_of = [], {}
    for pkg in data.get("packages") or []:
        name = _sbom.package_name(pkg.get("type"), pkg.get("namespace"), pkg.get("name") or "")
        unit_of[pkg.get("package_uid")] = name
        manifest = _sbom.rel((pkg.get("datafile_paths") or [None])[0], fixture_dir)
        unit = {"name": name}
        if _sbom.KIND.get(pkg.get("type", "")):
            unit["kind"] = _sbom.KIND[pkg["type"]]
        if manifest:
            unit["manifest"] = manifest
            unit["root"] = str(PurePosixPath(manifest).parent)
        units.append(unit)
    entries = data.get("dependencies") or []
    pinned = {}  # (unit uid or folder, name) -> version read from a lockfile
    for entry in entries:
        path = _sbom.rel(entry.get("datafile_path"), fixture_dir)
        parts = _sbom.purl(entry.get("purl") or "")
        version = parts.get("version") or (entry.get("resolved_package") or {}).get("version")
        if _sbom.is_lock(path) and version:
            owner = entry.get("for_package_uid") or str(PurePosixPath(path).parent)
            pinned.setdefault((owner, parts.get("name")), version)
    deps = []
    for entry in entries:
        if not entry.get("is_direct") or str(entry.get("scope") or "").lower() in NOT_DEPENDENCIES:
            continue
        path = _sbom.rel(entry.get("datafile_path"), fixture_dir)
        parts = _sbom.purl(entry.get("purl") or "")
        dep = {"name": parts.get("name")}
        if entry.get("for_package_uid") in unit_of:
            dep["unit"] = unit_of[entry["for_package_uid"]]
        if _sbom.is_lock(path):
            _sbom.place(dep, path, parts.get("version") or (entry.get("resolved_package") or {}).get("version"))
        else:
            _sbom.place(dep, path, None, _requirement(parts.get("type", ""), entry.get("extracted_requirement")))
            owner = entry.get("for_package_uid") or str(PurePosixPath(path or ".").parent)
            if (owner, parts.get("name")) in pinned:
                dep["resolved"] = pinned[(owner, parts.get("name"))]
        word = _sbom.scope(entry.get("scope"))
        if word in (None, "runtime") and entry.get("is_optional"):
            word = "optional"  # an extra's name, or ScanCode's own optional flag
        elif word is None and entry.get("is_runtime"):
            word = "runtime"
        if word:
            dep["scope"] = word
        deps.append(dep)
    return {"units": _sbom.dedupe(units), "dependencies": _sbom.dedupe(deps)}


def run(fixture_dir, work_dir) -> dict:
    argv, env, out = command(fixture_dir, work_dir)
    done = _sbom.sh(argv, work_dir, env)
    if done["rc"] != 0 or not out.is_file():
        raise RuntimeError(f"scancode rc={done['rc']}: {done['err'][-800:]}")
    return parse(out, fixture_dir)
