"""Source: GNU Make's own database, `make -pn`, in each folder holding a makefile GNU Make reads.

`commands` describes, for Daodan's container, with the network closed, in each folder with a `GNUmakefile`,
`makefile` or `Makefile`: `make -pnk`, a dry run of the default goal (no recipe runs, except those GNU Make
always runs: `$(MAKE)` and `+` lines) that prints the database of rules it read and the implicit rules it
chose. `read` takes the last database of the output (a recursive make prints its own first) and turns each
target that GNU Make would write into a `make-target` unit: an explicit, non-phony target with a recipe that
names it (`$@`, or the target as a word) and at least one prerequisite; neither a goal the GNU Coding Standards
name (`all`, `install`, `clean`, `check`, ..., and `test`) nor an object file (`.o`, `.obj`, `.lo`), a step of
the unit that links it. A unit's sources are the project's files among its
prerequisites, followed through the steps that are not units; the units among them are its edges. Its manifest
is the makefile its recipe comes from. A makefile of another dialect (nmake, Watcom, Borland, MMS) or one that
only a configure script turns into a makefile (`Makefile.in`, `Makefile.am`) is never read: a `not_executed` gap
per file, but for a `Makefile.am` or `Makefile.in` of an Autotools build, which `premap/autotools.py` states.
"""
from __future__ import annotations

import posixpath
import re
from pathlib import PurePosixPath

NAME, VERSION, RANK = "make", "4.3", "model"  # GNU Make of the container's image (Ubuntu 24.04)
DOWNLOAD = ()  # the image's own
MAKEFILES = ("GNUmakefile", "makefile", "Makefile")  # what GNU Make reads in a folder, in that order
OTHERS = re.compile(r"(?i)^(makefile\..+|.+\.(mak|mms)|descrip\.mms)$")  # makefiles GNU Make does not read
OBJECTS = (".o", ".obj", ".lo")
STANDARD = frozenset({  # the goals the GNU Coding Standards name (7.2.6), and `test`: actions, never a unit
    "all", "install", "install-html", "install-dvi", "install-pdf", "install-ps", "install-strip", "uninstall",
    "clean", "distclean", "mostlyclean", "maintainer-clean", "TAGS", "info", "dvi", "html", "pdf", "ps", "dist",
    "check", "installcheck", "installdirs", "test"})
START, END = "# Make data base, printed on", "# Finished Make data base on"
RECIPE = re.compile(r"^#  recipe to execute \(from '(.+)', line \d+\):$")


def _folder(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def commands(context):
    folders = sorted({_folder(rel) for rel in context.inventory.files if PurePosixPath(rel).name in MAKEFILES},
                     key=lambda f: (f.count("/"), f))
    return [{"tool": "make", "argv": ["make", "-pnk", "--no-print-directory"], "cwd": folder,
             "env": {"LC_ALL": "C"}, "network": "none"} for folder in folders] or None


def database(stdout: str) -> dict[str, dict]:
    """The `# Files` section of the last database in `stdout`: target -> {prerequisites, phony, recipe, from}."""
    text = stdout[stdout.rfind(START):]
    text = text[:text.find(END)] if END in text else text
    files = text[text.find("\n# Files\n"):]
    out: dict[str, dict] = {}
    for block in files.split("\n\n"):
        lines = block.split("\n")
        if any(line.startswith("# Not a target:") for line in lines):
            continue
        head = next((line for line in lines if line and not line.startswith(("#", "\t"))), None)
        if head is None or ":" not in head:
            continue
        name, _, rest = head.partition(":")
        rest = rest.lstrip(":").split("|", 1)[0]
        source = next((m.group(1) for m in map(RECIPE.match, lines) if m), None)
        entry = out.setdefault(name.strip(), {"prerequisites": [], "phony": False, "recipe": [], "from": None})
        entry["prerequisites"] += rest.split()
        entry["phony"] |= any(line.startswith("#  Phony target") for line in lines)
        entry["recipe"] += [line[1:] for line in lines if line.startswith("\t")]
        entry["from"] = entry["from"] or source
    return out


def _writes(name: str, entry: dict) -> bool:
    recipe = "\n".join(entry["recipe"])
    named = re.compile(r"(?<![\w./-])" + re.escape(name) + r"(?![\w.-])")  # the name as a word, not in test.pk
    return bool(entry["recipe"]) and ("$@" in recipe or "$(@" in recipe or bool(named.search(recipe)))


def read(context, commands, results):
    files = set(context.inventory.files)
    units, gaps, places = [], [], {}
    for command, result in zip(commands, results):
        folder, stdout = command["cwd"], result["stdout"] or ""
        if START not in stdout:
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"make -pn: {(result['stderr'] or '').strip()[-300:]}"})
            continue
        if result["returncode"] != 0:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": f"make -pn: {(result['stderr'] or '').strip()[-300:]}"})
        rules = database(stdout)
        chosen = {name for name, entry in rules.items()
                  if not entry["phony"] and name not in STANDARD and not name.startswith(".") and "%" not in name
                  and not name.endswith(OBJECTS) and entry["prerequisites"] and _writes(name, entry)}

        def path(name: str) -> str:
            return posixpath.normpath(posixpath.join(folder, name)).removeprefix("./")

        for name in sorted(chosen):
            sources, edges, seen, todo = set(), set(), set(), list(rules[name]["prerequisites"])
            while todo:
                item = todo.pop()
                if item in seen:
                    continue
                seen.add(item)
                if item in chosen:
                    edges.add(item)
                    continue
                if path(item) in files:
                    sources.add(path(item))
                todo += rules.get(item, {}).get("prerequisites", [])
            manifest = path(rules[name]["from"] or "Makefile")
            places[path(name)] = name
            units.append({"name": name, "kind": "make-target", "root": folder, "manifest": manifest,
                          "source_roots": sorted({_folder(s) for s in sources}), "depends_on": sorted(edges),
                          "config": {"sources": sorted(sources)}})
    from premap import autotools
    configured = autotools.configures(context)  # an Autotools build reads its folders' Makefile.am
    for rel in sorted(context.inventory.files):
        if PurePosixPath(rel).name in ("Makefile.am", "Makefile.in") and any(
                autotools._inside(_folder(rel), folder) for folder in configured):
            continue
        if OTHERS.match(PurePosixPath(rel).name):
            gaps.append({"kind": "not_executed", "path": rel,
                         "detail": "a makefile GNU Make does not read (another make's dialect, or a template a "
                                   "configure script fills): its targets are unknown"})
    return {"facts": {"units": units} if units else {}, "gaps": gaps}
