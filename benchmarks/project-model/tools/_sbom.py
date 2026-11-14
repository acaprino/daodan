"""Shared pieces of the `sbom` adapters (syft, trivy, osv_scanner, cdxgen, scancode). Not an adapter.

One rule for every tool, so the five answers compare, by the kind of file the tool names for a package (never by
reading the file): from a lockfile the tool's version is `resolved` and the file goes to `lockfile` (not scored: a
lockfile is not where a dependency is declared); from `pom.xml` the version is `resolved` (what the tools give
there is the effective version, after properties, parent and BOM) and the file is `declared_in`; from `go.mod` the
version is both (Go's minimal version selection builds with the listed version); from any other manifest the
version is `declared`. `declared` holds the text as written only where the tool gives it (`with_text`). `unit`,
`scope` and the direct/transitive split come only from what the tool itself says. Standard library.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

LOCKFILES = {
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock", "bun.lockb", "deno.lock",
    "poetry.lock", "uv.lock", "pdm.lock", "pipfile.lock", "pylock.toml", "cargo.lock", "go.sum", "gradle.lockfile",
    "buildscript-gradle.lockfile", "composer.lock", "gemfile.lock", "packages.lock.json", "pubspec.lock",
    "package.resolved", "mix.lock", "conan.lock", "vcpkg-lock.json", ".terraform.lock.hcl", "conda-lock.yml",
    "verification-metadata.xml", "cabal.project.freeze", "stack.yaml.lock", "flake.lock", "manifest.toml",
}
# The unit kind of SCHEMA.md for a package type as the tools name it (purl types and tool-specific names).
KIND = {"npm": "npm-package", "pypi": "python-project", "python": "python-project", "cargo": "cargo-crate",
        "rust-crate": "cargo-crate", "golang": "go-module", "go-module": "go-module", "gomod": "go-module",
        "maven": "maven-module", "java-archive": "maven-module", "pom": "maven-module", "nuget": "dotnet-project",
        "composer": "composer-package", "gem": "gem", "pub": "pub-package", "swift": "swift-package",
        "hex": "mix-project", "cocoapods": "swift-package"}
# Scope words of the tools, to the scopes of SCHEMA.md; a word not here leaves the scope out.
SCOPE = {"dev": "dev", "development": "dev", "devdependencies": "dev", "dev-dependencies": "dev", "dev_dependencies": "dev",
         "test": "test", "tests": "test", "testing": "test", "build": "build", "build-dependencies": "build",
         "optional": "optional", "optionaldependencies": "optional", "peer": "peer", "peerdependencies": "peer",
         "runtime": "runtime", "dependencies": "runtime", "install": "runtime", "compile": "runtime",
         "require": "runtime", "required": "runtime", "provided": "provided", "compileonly": "provided",
         "main": "runtime", "default": "runtime"}


def sh(argv, cwd, env: dict | None = None, timeout: int = 900) -> dict:
    """Run a command without a shell; never raises. `env` replaces nothing: it is added to the inherited one."""
    full = dict(os.environ)
    full.update({k: v for k, v in (env or {}).items() if v is not None})
    try:
        done = subprocess.run([str(c) for c in argv], cwd=str(cwd), env=full, capture_output=True, text=True,
                              errors="replace", timeout=timeout)
        return {"rc": done.returncode, "out": done.stdout, "err": done.stderr}
    except subprocess.TimeoutExpired:
        return {"rc": -1, "out": "", "err": f"timeout after {timeout}s"}
    except OSError as exc:
        return {"rc": -2, "out": "", "err": f"{type(exc).__name__}: {exc}"}


def rel(path, fixture, base=None) -> str | None:
    """A tool's path as POSIX relative to the fixture: absolute, `/`-rooted (syft), prefixed with the fixture's
    folder name (scancode) or relative to the tool's working folder `base` (cdxgen) all come back the same; None
    when it is outside."""
    if not path:
        return None
    s = str(path).replace("\\", "/")
    root = Path(fixture).resolve().as_posix().rstrip("/")
    if base is not None and not s.startswith("/") and (Path(base) / s).exists():
        s = (Path(base) / s).resolve().as_posix()
    if s == root:
        return "."
    if s.startswith(root + "/"):
        return s[len(root) + 1:]
    if s.startswith("/") and Path(s).is_absolute() and Path(s).exists():
        return None  # a real absolute path outside the fixture
    s = s.lstrip("/")
    while s.startswith("./"):
        s = s[2:]
    name = Path(fixture).name
    if s.startswith(name + "/") and not (Path(fixture) / s).exists():
        s = s[len(name) + 1:]
    return s or "."


def is_lock(path) -> bool:
    return bool(path) and PurePosixPath(str(path)).name.lower() in LOCKFILES


RESOLVED_MANIFESTS = {"pom.xml"}  # the tool's version from these files is the effective one
BOTH_MANIFESTS = {"go.mod"}  # declared and selected at once


def place(dep: dict, path, version, with_text=None) -> dict:
    """The file and version of one package by the file rule of this module; `with_text` is the requirement as the
    tool says it is written, which is `declared` whatever the file."""
    has = version not in (None, "")
    if path:
        base = PurePosixPath(str(path)).name.lower()
        if is_lock(path):
            dep["lockfile"] = path
        else:
            dep["declared_in"] = path
        if has and (is_lock(path) or base in RESOLVED_MANIFESTS or base in BOTH_MANIFESTS):
            dep["resolved"] = str(version)
        if has and not is_lock(path) and base not in RESOLVED_MANIFESTS:
            dep["declared"] = str(version)
    if with_text is not None:
        dep["declared"] = with_text
    return dep


def scope(word) -> str | None:
    """A tool's scope word as a scope of SCHEMA.md, or None for a word that names none (an extra, a group)."""
    if word is None:
        return None
    return SCOPE.get(str(word).strip().lower().replace(" ", ""))


def purl(value: str) -> dict:
    """pkg:type/namespace/name@version?qualifiers#subpath as its parts; names as SCHEMA.md writes them."""
    m = re.match(r"^pkg:([^/]+)/(.+?)(?:@([^?#]*))?(?:\?([^#]*))?(?:#.*)?$", value or "")
    if not m:
        return {}
    kind, path, version, qualifiers = m.group(1).lower(), m.group(2), m.group(3), m.group(4) or ""
    parts = [unquote(p) for p in path.split("/")]
    name, namespace = parts[-1], "/".join(parts[:-1])
    return {"type": kind, "namespace": namespace, "name": package_name(kind, namespace, name),
            "version": unquote(version) if version else None,
            "qualifiers": dict(q.split("=", 1) for q in qualifiers.split("&") if "=" in q)}


def package_name(kind: str, namespace: str | None, name: str) -> str:
    kind = (kind or "").lower()
    if not namespace:
        return name
    if kind == "maven":
        return f"{namespace}:{name}"
    if kind == "npm" and not namespace.startswith("@"):
        return f"@{namespace}/{name}"
    return f"{namespace}/{name}"


def dedupe(items: list[dict]) -> list[dict]:
    seen, out = set(), []
    for item in items:
        key = tuple(sorted((k, str(v)) for k, v in item.items()))
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out
