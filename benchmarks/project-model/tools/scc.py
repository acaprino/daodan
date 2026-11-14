"""scc (Sloc, Cloc and Code): a language per file, from the extension, the file name and a shebang.

`scc --by-file -f json --gen .` prints per language the files it counted, each with the flag `Generated`
(a header marker, only checked with --gen). It follows .gitignore and skips `.git`, nothing else:
vendor and documentation folders are counted as code. A generated file is the only reason it gives for leaving a
file out, so the other three reasons are missing from its answer, not empty. Names are mapped to Linguist's spelling.
"""
from __future__ import annotations

import json

from _lang import canon, known, sh

VERSION = "v4.1.0"
NAMES = {
    "C Header": "C", "C++ Header": "C++", "Jupyter": "Jupyter Notebook", "Plain Text": "Text",
    "TypeScript Typings": "TypeScript", "JSX": "JavaScript", "Protocol Buffers": "Protocol Buffer",
    "Objective C": "Objective-C", "Objective C++": "Objective-C++", "BASH": "Shell", "Zsh": "Shell",
    "Korn Shell": "Shell", "Batch": "Batchfile", "Bazel": "Starlark", "PL/SQL": "PLSQL", "LaTeX": "TeX",
    "JavaServer Pages": "Java Server Pages", "Visual Basic": "Visual Basic .NET", "Twig Template": "Twig",
    "Freemarker Template": "FreeMarker", "Smarty Template": "Smarty", "Blade template": "Blade",
    "Ruby HTML": "HTML+ERB", "Gemfile": "Ruby", "Rakefile": "Ruby", "Scons": "Python", "Docker ignore": "Ignore List",
    "gitignore": "Ignore List", "ignore": "Ignore List", "Extensible Stylesheet Language Transformations": "XSLT",
    "Properties File": "Java Properties", "Patch": "Diff", "MSBuild": "XML", "nuspec": "XML",
    "Standard ML (SML)": "Standard ML", "Lisp": "Common Lisp", "LLVM IR": "LLVM", "Wolfram": "Mathematica",
    "DOT": "Graphviz (DOT)", "Visual Basic for Applications": "VBA", "JSONC": "JSON with Comments", "JSONL": "JSON",
}


def run(fixture_dir, work_dir) -> dict:
    done = sh(["scc", "--by-file", "-f", "json", "--gen", "."], cwd=fixture_dir)
    if done.returncode != 0:
        raise RuntimeError(f"scc -> {done.returncode}: {done.stderr[-500:]}")
    groups = json.loads(done.stdout) if done.stdout.strip() else []
    languages, excluded, unmapped = [], [], set()
    for group in groups:
        for item in group["Files"]:
            path = item["Location"]
            if item.get("Generated"):
                excluded.append({"path": path, "why": "generated"})
                continue
            name = canon(item["Language"], NAMES)
            if not known(name):
                unmapped.add(item["Language"])
            languages.append({"path": path, "language": name})
    return {"languages": languages, "excluded": excluded,
            "_raw": {"names_not_in_linguist": sorted(unmapped)}}
