"""Helpers shared by the framework and service adapters (standard library only).

An adapter is `run(fixture_dir, work_dir) -> dict` in the shape of SCHEMA.md plus a `detail` key (not scored: what
the tool said beyond the shape). The runner wraps the whole process in strace or in a network namespace, so
adapters never wrap their own commands.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path, PurePosixPath

NODE_MODULES = Path(os.environ.get("PM_NODE_MODULES", "/opt/tools/node_modules"))
BIN_DIR = Path(os.environ.get("PM_BIN_DIR", "/opt"))
TIMEOUT = 600

# Manifest file name -> unit kind of SCHEMA.md.
MANIFEST_KINDS = {
    "package.json": "npm-package", "deno.json": "deno-module", "deno.jsonc": "deno-module",
    "pyproject.toml": "python-project", "setup.py": "python-project", "setup.cfg": "python-project",
    "Pipfile": "python-project", "requirements.txt": "python-project",
    "Cargo.toml": "cargo-crate", "go.mod": "go-module", "pom.xml": "maven-module",
    "build.gradle": "gradle-project", "build.gradle.kts": "gradle-project", "build.sbt": "sbt-project",
    "composer.json": "composer-package", "Gemfile": "gem", "pubspec.yaml": "pub-package",
    "Package.swift": "swift-package", "mix.exs": "mix-project", "CMakeLists.txt": "cmake-project",
    "meson.build": "meson-project", "main.tf": "terraform-module", "Chart.yaml": "helm-chart",
}


def execute(argv, cwd, env=None, timeout=TIMEOUT):
    """(returncode, stdout, stderr) of one command; a missing program or a timeout is a returncode of -1."""
    try:
        done = subprocess.run([str(a) for a in argv], cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
                              env={**os.environ, **(env or {})}, encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired) as error:
        return -1, "", f"{type(error).__name__}: {error}"
    return done.returncode, done.stdout, done.stderr


def posix(path: str) -> str:
    """A relative POSIX path: `\\` as `/`, no leading `./` or `/`, no trailing `/`; the root is `.`."""
    text = str(path).replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    text = text.strip("/")
    return text or "."


def relative(path: str, root) -> str:
    """`path` relative to `root` when it lies under it (absolute inputs); otherwise as `posix` leaves it."""
    base = str(root).replace("\\", "/").rstrip("/")
    text = str(path).replace("\\", "/")
    if text == base or text == base + "/":
        return "."
    if text.startswith(base + "/"):
        text = text[len(base) + 1:]
    return posix(text)


def unit_kind(manifest: str) -> str | None:
    name = PurePosixPath(manifest).name
    if name in MANIFEST_KINDS:
        return MANIFEST_KINDS[name]
    if name.endswith((".csproj", ".fsproj", ".vbproj")):
        return "dotnet-project"
    return None


def parent(path: str) -> str:
    return PurePosixPath(path).parent.as_posix()


def package_name(fixture: Path, directory: str) -> str | None:
    """`name` of the package.json in `directory`, read from the project's own file; None when there is none."""
    try:
        return json.loads((Path(fixture) / directory / "package.json").read_text(encoding="utf-8")).get("name")
    except (OSError, ValueError, AttributeError):
        return None
