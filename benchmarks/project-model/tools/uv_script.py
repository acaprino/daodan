"""uv on PEP 723 inline script metadata: `uv tree --script <file> --depth 0 --no-build` for every .py file.

uv reads the `# /// script` block itself; the adapter hands it every .py file of the project and lets it say which
ones carry a block (no detection here). `uv tree` resolves the block against the index (PyPI by default), so it
needs the network unless its cache already holds the packages; `--no-build` makes building an sdist an error
instead of running its build backend. The interpreter is given (UV_PYTHON) and downloads of Python are off, so uv
does not fetch one. Cache in the work directory, empty at every run.

What the answer holds: the roots of each script's tree (its direct requirements), with the file as `declared_in` and the
version uv resolved as `resolved` (a resolution of the day against the index, not a version the project fixes,
unless the block sets `exclude-newer`). uv tree prints no requirement text, so `declared` is not given.
"""
from __future__ import annotations

import re
from pathlib import Path

import _sbom  # the driver puts tools/ on sys.path

VERSION = "0.13.8"
ENV = {"UV_PYTHON": "/usr/local/bin/python3.12", "UV_PYTHON_DOWNLOADS": "never", "UV_NO_PROGRESS": "1",
       "NO_COLOR": "1"}
COMMAND = ("for each .py: uv tree --script <file> --depth 0 --no-build --cache-dir <work>/uv-cache, with "
           + " ".join(f"{k}={v}" for k, v in ENV.items()))
STDOUT = True
CWD = "project"
CANARY = True
MARK = "### uv-script "


def command(fixture_dir, work_dir) -> tuple[list, dict, Path]:
    out = Path(work_dir) / "uv.txt"
    cache = Path(work_dir) / "uv-cache"
    files = sorted(p.relative_to(fixture_dir).as_posix() for p in Path(fixture_dir).rglob("*.py"))
    loop = ('for f in "$@"; do echo "' + MARK + '$f"; /usr/local/bin/uv tree --script "$f" --depth 0 --no-build '
            f'--cache-dir "{cache}" 2>&1; echo "{MARK}rc=$?"; done')
    return ["/bin/sh", "-c", loop, "sh", *files], dict(ENV), out


def _blocks(text: str) -> dict:
    """{file: (lines, rc)} from the marked output."""
    out, current, lines = {}, None, []
    for line in text.splitlines():
        if line.startswith(MARK):
            rest = line[len(MARK):]
            if rest.startswith("rc=") and current:
                out[current] = (lines, int(rest[3:] or 1))
                current, lines = None, []
            else:
                current, lines = rest, []
        elif current:
            lines.append(line)
    return out


def parse(out: Path, fixture_dir) -> dict:
    deps = []
    for path, (lines, rc) in _blocks(Path(out).read_text(encoding="utf-8")).items():
        if rc != 0:
            continue
        for line in lines:
            m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])? v(\S+)", line)
            if m:
                deps.append({"name": m.group(1), "resolved": m.group(2), "declared_in": path})
    return {"dependencies": _sbom.dedupe(deps)}


def honesty(out: Path, fixture_dir) -> dict:
    blocks = _blocks(Path(out).read_text(encoding="utf-8"))
    names = [d["name"] for d in parse(out, fixture_dir)["dependencies"]]
    return {"undeclared": [], "packages": sorted(set(names)),
            "findings": [{"file": f, "rc": rc, "head": lines[:3]} for f, (lines, rc) in blocks.items()]}


def run(fixture_dir, work_dir) -> dict:
    argv, env, out = command(fixture_dir, work_dir)
    done = _sbom.sh(argv, fixture_dir, env)
    out.write_text(done["out"], encoding="utf-8")
    return parse(out, fixture_dir)
