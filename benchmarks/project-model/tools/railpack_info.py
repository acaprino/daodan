"""Railpack 0.43.0 `railpack info --format json <dir>`, only for the framework and the provider it names.

The versions Railpack resolves are tested by another adapter. Here: `metadata.nodeRuntime` and
`metadata.pythonRuntime` (the framework the provider recognised, e.g. `next`, `django`, `fastapi`) become
frameworks, unless they only name the language (`node`, `python`, ...); the provider list goes to `detail`, with the
rest of the metadata. The tool gives no unit, no evidence file and no service. It runs `mise` (its own binary,
extracted under /tmp) with the project as working directory; the runner's process trace shows it.
"""
from __future__ import annotations

import json
from pathlib import Path

import _fw

VERSION = "0.43.0"
BINARY = _fw.BIN_DIR / "railpack"
LANGUAGE_ONLY = {"node", "python", "ruby", "go", "java", "php", "rust", "elixir", "deno", "bun", "static", "dotnet"}


def run(fixture_dir, work_dir) -> dict:
    root, work = Path(fixture_dir).resolve(), Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    code, text, err = _fw.execute([BINARY, "info", "--format", "json", root], work)
    if code != 0:
        raise RuntimeError(f"railpack info exited {code}: {(err or text)[-400:]}")
    info = json.loads(text)
    metadata = info.get("metadata") or {}
    frameworks = [{"name": value} for key, value in sorted(metadata.items())
                  if key.endswith("Runtime") and value and value not in LANGUAGE_ONLY]
    return {"frameworks": frameworks, "services": [],
            "detail": {"providers": info.get("detectedProviders"), "metadata": metadata, "success": info.get("success"),
                       "warnings": [m["Msg"][:120] for m in info.get("logs", []) if m.get("Level") == "warn"]}}
