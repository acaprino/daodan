"""Magika (Google): the type of a file from its content, with a small neural model, whatever its name.

`Magika().identify_paths` labels each file (python, typescript, cpp, shell, markdown, png, ...). The label is
mapped to Linguist's spelling where Linguist has such a language; a label that is not a language (an image, an
archive, `unknown`) gives no language. A file the model does not call text is reported as `binary`, the only
reason it can give. It reads no .gitattributes and has no idea of vendored or generated files, so `excluded` is
partial. The python package is the pinned version; the `magika` command on the PATH is the Rust build bundled in
the wheel.
"""
from __future__ import annotations

from pathlib import Path

from _lang import canon, files, known

VERSION = "1.0.3"
NAMES = {
    "cs": "C#", "cpp": "C++", "objectivec": "Objective-C", "tomlfile": "TOML", "txt": "Text", "proto": "Protocol Buffer",
    "rst": "reStructuredText", "latex": "TeX", "batch": "Batchfile", "gemfile": "Ruby", "gemspec": "Ruby",
    "ignorefile": "Ignore List", "csproj": "XML", "vcxproj": "XML", "powershell": "PowerShell", "ipynb": "Jupyter Notebook",
    "javascript": "JavaScript", "typescript": "TypeScript", "tsx": "TSX", "jsx": "JavaScript", "shell": "Shell",
    "dockerfile": "Dockerfile", "makefile": "Makefile", "markdown": "Markdown", "unknown": None, "empty": None,
    "randomascii": None, "randombytes": None, "symlink": None, "symlinktext": None,
}


def _package():
    """The magika package, not this file: the folder of the adapters may be on the path under the same name."""
    import importlib
    import sys

    here = Path(__file__).resolve().parent
    held = sys.modules.get("magika")
    if held is not None and Path(getattr(held, "__file__", "") or "").resolve() == Path(__file__).resolve():
        del sys.modules["magika"]
    saved = list(sys.path)
    sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != here]
    try:
        return importlib.import_module("magika")
    finally:
        sys.path[:] = saved


def run(fixture_dir, work_dir) -> dict:
    Magika = _package().Magika
    root = Path(fixture_dir)
    names = files(root)
    results = Magika().identify_paths([root / n for n in names])
    languages, excluded, unmapped = [], [], {}
    for name, result in zip(names, results):
        if not result.ok:
            unmapped[f"error:{result.status}"] = unmapped.get(f"error:{result.status}", 0) + 1
            continue
        output = result.output
        label = getattr(output.label, "value", str(output.label))
        if not output.is_text and label not in ("empty", "symlink", "unknown"):
            excluded.append({"path": name, "why": "binary"})
            continue
        language = canon(label, NAMES)
        if language is None:
            continue
        if known(language):
            languages.append({"path": name, "language": language})
        else:
            unmapped[label] = unmapped.get(label, 0) + 1
    return {"languages": languages, "excluded": excluded,
            "_raw": {"labels_not_in_linguist": {k: v for k, v in sorted(unmapped.items())}}}
