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
is the makefile its recipe comes from. A folder with a `Makefile.in` and a `configure` of the project's own, no
Autotools' (zlib's), runs that configure first, with its defaults (`CONFIGURE`): the dry run reads the Makefile it
writes, the units' manifest is the Makefile.in and their `configure` the script. A makefile of another dialect
(nmake, Watcom, Borland, MMS) or one that only a configure script turns into a makefile (`Makefile.in`,
`Makefile.am`) is never read: a `not_executed` gap per file, but for a `Makefile.am` or `Makefile.in` of an
Autotools build, which `premap/autotools.py` states, or of a folder whose configure runs here.
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
# The project's own configure, by its own interpreter when Git marks it executable, else by sh (as
# `indexers/clang_run.py` runs it).
CONFIGURE = "if [ -x ./configure ]; then ./configure; else sh ./configure; fi"
DRY_RUN = ["make", "-pnk", "--no-print-directory"]


def _folder(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def configured(context) -> set[str]:
    """The folders with a `Makefile.in` and a `configure` of the project's own: no Autotools build's
    (`autotools.configures`), whose configure `indexers/clang_run.py` writes and runs apart."""
    from premap import autotools
    from premap.origins import disk_text
    folders = {_folder(rel) for rel in context.inventory.files if PurePosixPath(rel).name == "Makefile.in"}
    if not folders:
        return set()
    own = set(autotools.configures(context))
    return {folder for folder in folders if folder not in own
            and disk_text(context, "configure" if folder == "." else f"{folder}/configure") is not None}


def commands(context):
    own = configured(context)
    folders = sorted({_folder(rel) for rel in context.inventory.files if PurePosixPath(rel).name in MAKEFILES} | own,
                     key=lambda f: (f.count("/"), f))
    configure = (f"{{ {CONFIGURE} ; }} > /tmp/daodan-configure.log 2>&1"
                 " || { tail -n 20 /tmp/daodan-configure.log >&2; exit 3; }; exec " + " ".join(DRY_RUN))
    return [{"tool": "make", "argv": ["sh", "-c", configure] if folder in own else list(DRY_RUN), "cwd": folder,
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
    files, own = set(context.inventory.files), configured(context)
    units, gaps, places = [], [], {}
    for command, result in zip(commands, results):
        folder, stdout = command["cwd"], result["stdout"] or ""
        ran = "./configure, then make -pn" if folder in own else "make -pn"
        if START not in stdout:
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"{ran}: {(result['stderr'] or '').strip()[-300:]}"})
            continue
        if result["returncode"] != 0:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": f"{ran}: {(result['stderr'] or '').strip()[-300:]}"})
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
            if folder in own and manifest == path("Makefile"):  # the Makefile the configure wrote from it
                manifest = path("Makefile.in")
            places[path(name)] = name
            units.append({"name": name, "kind": "make-target", "root": folder, "manifest": manifest,
                          "source_roots": sorted({_folder(s) for s in sources}), "depends_on": sorted(edges),
                          "config": {"sources": sorted(sources),
                                     **({"configure": path("configure")} if folder in own else {})}})
    from premap import autotools
    built = autotools.configures(context)  # an Autotools build reads its folders' Makefile.am
    for rel in sorted(context.inventory.files):
        if PurePosixPath(rel).name in ("Makefile.am", "Makefile.in") and any(
                autotools._inside(_folder(rel), folder) for folder in built):
            continue
        if PurePosixPath(rel).name == "Makefile.in" and _folder(rel) in own:
            continue
        if OTHERS.match(PurePosixPath(rel).name):
            gaps.append({"kind": "not_executed", "path": rel,
                         "detail": "a makefile GNU Make does not read (another make's dialect, or a template a "
                                   "configure script fills): its targets are unknown"})
    return {"facts": {"units": units} if units else {}, "gaps": gaps}
