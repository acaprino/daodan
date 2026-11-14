"""tokei: a language per file, from the extension and the file name.

`tokei -o json -f .` prints per language the files it counted, with their lines. It follows .gitignore, .ignore
and `.tokeignore`, skips hidden files and folders, and counts everything else, vendored folders included. It has
no notion of generated, vendored or documentation files, so `excluded` is missing from its answer. Files embedded
in another language (the script of a `.vue`) are `children` and not read here. Names are mapped to Linguist's
spelling.
"""
from __future__ import annotations

import json

from _lang import canon, known, sh

VERSION = "15.0.0"
NAMES = {
    "C Header": "C", "C++ Header": "C++", "C++ Module": "C++", "Arduino C++": "C++", "Jupyter Notebooks": "Jupyter Notebook",
    "Plain Text": "Text", "JSX": "JavaScript", "Protocol Buffers": "Protocol Buffer", "BASH": "Shell", "Zsh": "Shell",
    "Korn shell": "Shell", "Batch": "Batchfile", "Bazel": "Starlark", "Autoconf": "M4Sugar", "Jinja2": "Jinja",
    "Rakefile": "Ruby", "Scons": "Python", "Visual Basic": "Visual Basic .NET", "XSL": "XSLT", "Ruby HTML": "HTML+ERB",
    "Go HTML": "Go Template", "PO File": "Gettext Catalog", "RPM Specfile": "RPM Spec", "Ebuild": "Gentoo Ebuild",
    "Metal Shading Language": "Metal", "Standard ML (SML)": "Standard ML", "Wolfram": "Mathematica",
}


def run(fixture_dir, work_dir) -> dict:
    done = sh(["tokei", "-o", "json", "-f", "."], cwd=fixture_dir)
    if done.returncode != 0:
        raise RuntimeError(f"tokei -> {done.returncode}: {done.stderr[-500:]}")
    report = json.loads(done.stdout) if done.stdout.strip() else {}
    languages, unmapped = [], set()
    for language, entry in report.items():
        if language == "Total":
            continue
        name = canon(language, NAMES)
        if not known(name):
            unmapped.add(language)
        for item in entry["reports"]:
            path = item["name"]
            languages.append({"path": path[2:] if path.startswith("./") else path, "language": name})
    return {"languages": languages, "_raw": {"names_not_in_linguist": sorted(unmapped)}}
