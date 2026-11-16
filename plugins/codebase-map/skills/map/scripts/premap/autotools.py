"""Source: an Autotools build, `configure.ac` and `Makefile.am`, read as files, never run.

The outermost `configure.ac` (or `configure.in`) of a folder is an `autotools-project` unit, named as `AC_INIT`
names it, its manifest that file; one below it is configured by its configure (`AC_CONFIG_SUBDIRS`) and makes no
unit. Its sources are the files the `Makefile.am` of its folders list in a `_SOURCES` variable, conditional ones
included: which of them a build compiles is the configure's to say, and the C and C++ analyzer runs it
(`indexers/clang_run.py`, `autotools`). The snapshot keeps no `configure.ac`: it is read from disk, in the folders
the snapshot holds.
"""
from __future__ import annotations

import posixpath
import re
from pathlib import PurePosixPath

from premap.origins import disk_text

NAME, VERSION, RANK = "autotools", "daodan/premap/v1", "reader"
CONFIGURES = ("configure.ac", "configure.in")
INIT = re.compile(r"AC_INIT\(\s*\[?([^],)]+)")
SOURCES = re.compile(r"^\s*\w+_SOURCES\s*\+?=(.*)$", re.M)  # once its continuation lines are joined
ASSIGNED = re.compile(r"^\s*(\w+)\s*=(.*)$", re.M)


def _folder(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def configures(context) -> dict[str, str]:
    """Each folder of the snapshot holding a `configure.ac` (or `configure.in`): the file's path."""
    found = {}
    for folder in sorted(context.inventory.directories):
        for name in CONFIGURES:
            rel = name if folder == "." else f"{folder}/{name}"
            if folder not in found and disk_text(context, rel) is not None:
                found[folder] = rel
    return found


def run(context):
    found = configures(context)
    tops = [f for f in sorted(found) if not any(o != f and _inside(f, o) for o in found)]
    files = set(context.inventory.files)
    units = []
    for top in tops:
        text = disk_text(context, found[top]) or ""
        named = INIT.search(text)
        sources = set()
        for rel in sorted(files):
            if PurePosixPath(rel).name == "Makefile.am" and _inside(_folder(rel), top):
                text = context.inventory.text(rel).replace("\\\n", " ")
                variables = dict(ASSIGNED.findall(text))  # a variable a `_SOURCES` names (`${iowin32_src}`)
                for value in SOURCES.findall(text):
                    words = value.split()
                    for word in [w for word in words for w in (
                            variables.get(word.strip("${}()"), "").split() if word.startswith("$") else [word])]:
                        path = posixpath.normpath(posixpath.join(_folder(rel), word))
                        if path in files:
                            sources.add(path)
        units.append({"name": named.group(1).strip() if named else None, "kind": "autotools-project", "root": top,
                      "manifest": found[top], "source_roots": sorted({_folder(s) for s in sources}),
                      "config": {"sources": sorted(sources)}})
    return {"facts": {"units": units}} if units else None
