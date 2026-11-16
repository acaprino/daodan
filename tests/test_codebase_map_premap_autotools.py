"""The Autotools source of the pre-map: `configure.ac` and `Makefile.am`, read as files, never run.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_premap_autotools.py
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

import premap  # noqa: E402
from premap import autotools, make  # noqa: E402
import snapshot  # noqa: E402

# zlib's contrib/minizip at 51b7f2a, shortened: a GNU makefile of its own beside the Autotools build that also
# compiles mztools.c, and iowin32.c only for Windows hosts.
MINIZIP = {
    "contrib/minizip/configure.ac": "AC_INIT([minizip], [1.3.1], [bugzilla.redhat.com])\n"
                                    "AC_CONFIG_SRCDIR([minizip.c])\nAM_INIT_AUTOMAKE([foreign])\nLT_INIT\n"
                                    "AC_CONFIG_FILES([Makefile minizip.pc])\nAC_OUTPUT\n",
    "contrib/minizip/Makefile.am": "lib_LTLIBRARIES = libminizip.la\n\nif WIN32\niowin32_src = iowin32.c\nendif\n\n"
                                   "libminizip_la_SOURCES = \\\n\tioapi.c \\\n\tmztools.c \\\n\tunzip.c \\\n"
                                   "\tzip.c \\\n\t${iowin32_src}\n\nminizip_SOURCES = minizip.c\n",
    "contrib/minizip/Makefile": "all: minizip\nminizip: minizip.o\n\t$(CC) -o $@ minizip.o\n",
    **{f"contrib/minizip/{name}": "int f(void) { return 0; }\n"
       for name in ("ioapi.c", "mztools.c", "unzip.c", "zip.c", "iowin32.c", "minizip.c")},
    "contrib/minizip/sub/configure.ac": "AC_INIT([inner], [1])\n",  # configured by the outer one's configure
    "win32/Makefile.msc": "all:\n",
    "zlib.c": "int z(void) { return 0; }\n"}


def record(tmp_path, sources):
    project = tmp_path / "proj"
    for rel, text in MINIZIP.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8", newline="\n")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    failed = lambda commands: [{"returncode": 2, "stdout": "", "stderr": "no"} for _ in commands]  # noqa: E731
    return premap.write(manifest, sources=sources, runner=failed)


def test_a_configure_ac_is_a_unit_with_the_sources_its_makefile_am_names(tmp_path):
    """The outermost `configure.ac` of a folder is an `autotools-project` unit, named as `AC_INIT` names it, its
    manifest the `configure.ac`; its sources the files the `Makefile.am` beside it lists in a `_SOURCES` variable,
    a conditional one (`iowin32.c`) included: which of them a build compiles is the configure's to say. A
    `configure.ac` below another is configured by that one's configure, and makes no unit."""
    [unit] = [u for u in record(tmp_path, (autotools,))["units"] if u["kind"] == "autotools-project"]
    assert (unit["name"], unit["root"], unit["manifest"]) == ("minizip", "contrib/minizip",
                                                             "contrib/minizip/configure.ac")
    assert unit["config"]["sources"] == [f"contrib/minizip/{name}" for name in (
        "ioapi.c", "iowin32.c", "minizip.c", "mztools.c", "unzip.c", "zip.c")]
    assert unit["source_roots"] == ["contrib/minizip"] and unit["run"]["executes_project_code"]


def test_a_makefile_am_beside_a_configure_ac_is_no_gap_and_another_dialect_still_is(tmp_path):
    """Make does not read `Makefile.am`; the Autotools build does, so it is no `not_executed` gap of make's."""
    gaps = [g["path"] for g in record(tmp_path, (make,))["gaps"] if g["kind"] == "not_executed"]
    assert gaps == ["win32/Makefile.msc"]
