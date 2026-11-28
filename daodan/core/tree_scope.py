#!/usr/bin/env python3
"""
The perimeter of a Codebase Map: what no script descends into.

One rule, owned here, for every script that walks a tree:

- what Git ignores, when the target is inside a work tree that does not
  ignore it and git answers;
- every directory whose name starts with a dot, but those whose files the
  stack tool reads (`file_formats.READ_DOT_DIRECTORIES`: `.github`, `.maestro`);
- dependency and build directories, by name;
- every link, to a file or to a directory, whether or not its target exists.

All four apply below the target. The target itself is analyzed as given, so
naming a dot directory is how its content gets a Codebase Map of its own. A dot file
beside analyzed source is not a directory, and stays. A target that its work
tree ignores, itself or through a directory above it, is not that work tree's:
it is analyzed whole, as its own root.

The rule exists because tools write beside the code they work on. A lifecycle
campaign left its run records under `.daodan/` and its review under
`.team-review/`; the next snapshot counted them as project files, and an
incremental update of an untouched project asked for a full analysis.

A link is a name for a place that is not there. Git records it as a link,
never as what it points to. Read through, a link to a file of the project gave
one path twice, and a link out of the project put a file from outside in the
snapshot: a repository that tracks two tests as links into its documentation
could not have its snapshot written.

A script may read less than the perimeter. None reads more: a usage found in a
file the snapshot never recorded is a citation no phase file can carry.

Standard library only, and Daodan's register of file formats (`file_formats.py`).
"""

from __future__ import annotations

import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Iterator

import file_formats

__all__ = ["DEPENDENCY_DIRS", "GIT_OPTIONS", "Perimeter", "READ_DOT_DIRECTORIES", "git_executable", "work_tree", "workspace_glob"]

# First on every command line of Git on the host: a work tree's own configuration, and what it includes, can name
# programs Git runs, and the analyzed project's code runs only in Daodan's container: core.fsmonitor wherever Git
# reads the index (check-ignore, ls-files, status), and the hooks of core.hooksPath (post-index-change where a
# command writes the index). A setting given here wins over every configuration file, and Git passes it on to the
# commands it starts, a submodule's among them. A filter is a program the checkout names too: `source_files.git_info`
# asks Git which ones it declares before any command that reads a file's content.
GIT_OPTIONS = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")


def workspace_glob(pattern: str) -> re.Pattern:
    """Match a workspace path; **/ includes zero directories. Python 3.12 lacks glob.translate."""
    tokens = {"**/": "(?:[^/]+/)*", "**": ".*", "*": "[^/]*", "?": "[^/]"}
    return re.compile("".join(tokens.get(part, re.escape(part)) for part in re.split(r"(\*\*/|\*\*|\*|\?)", pattern)))


def git_executable() -> str | None:
    return program("git")


def program(name: str) -> str | None:
    """
    The absolute path of `name` from absolute PATH entries only. Windows process
    creation and `shutil.which` search the working directory before PATH, and a
    server's working directory is the analyzed project, so a bare `git`, `docker`
    or `uv` could run the project's own.
    """
    names = [name + suffix for suffix in (".exe", ".cmd", ".bat")] if os.name == "nt" and "." not in name else [name]
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        entry = entry.strip('"')
        if not entry or not os.path.isabs(entry):
            continue
        for name in names:
            candidate = os.path.join(entry, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
    return None

# Dependency and build output. Git usually ignores these too. They are named
# here because a project with no repository has no ignore rule to consult.
DEPENDENCY_DIRS = file_formats.DEPENDENCY_DIRECTORIES
# The dot directories that are the project's own configuration, read by the stack tool: a CI workflow once never
# reached the stack, and with it 31 of 88 technologies of the corpus.
READ_DOT_DIRECTORIES = file_formats.READ_DOT_DIRECTORIES

# Dot directories a reader does not need named back: the repository's own
# store, and the Codebase Map's own output.
_UNREPORTED = frozenset({".git", ".daodan"})

GIT_TIMEOUT_SECONDS = 30

# A Windows junction: a directory link that `lstat` does not report as a
# symbolic link (IO_REPARSE_TAG_MOUNT_POINT).
_JUNCTION = 0xA0000003


def _is_link(path: Path) -> bool:
    """True for a symbolic link or a junction, whether or not its target exists."""
    try:
        status = os.lstat(path)
    except OSError:
        return False
    return stat.S_ISLNK(status.st_mode) or getattr(status, "st_reparse_tag", 0) == _JUNCTION


def _key(relative: str) -> str:
    """One spelling per path: Git prints forward slashes, Windows does not."""
    return os.path.normcase(relative.replace("\\", "/").rstrip("/"))


def _held(git: str, base: Path) -> bool:
    """
    True when the base is inside a work tree that does not ignore it.
    `check-ignore` matches the directory and every directory above it up to
    the top level: it exits 0 when a rule applies, 1 when none does, and 128
    outside every work tree.
    """
    try:
        proc = subprocess.run(
            [git, *GIT_OPTIONS, "-C", str(base), "check-ignore", "-q", "."],
            capture_output=True, timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 1


def work_tree(base: Path) -> Path | None:
    """
    The top level of the work tree that holds a directory, or None: outside
    every work tree, when git does not answer, and when the work tree ignores
    the directory. A repository that ignores a directory neither tracks nor
    describes it: a project placed under a tool's ignored run directory once
    took that tool's paths, commit and dirty flag.
    """
    git = git_executable()
    if git is None or not _held(git, base):
        return None
    try:
        proc = subprocess.run(
            [git, *GIT_OPTIONS, "-C", str(base), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    top = proc.stdout.strip()
    return Path(top) if proc.returncode == 0 and top else None


class Perimeter:
    """
    The part of one target a script may read.

    `walk` yields it; `covers` answers for a path found some other way, by a
    glob or by a search tool. `dot_directories`, `dependency_directories`,
    `links` and `git_ignored` say what a walk left out, so that a run can declare it: an exclusion nobody
    reported is how a stylesheet once went missing from every inventory.
    """

    def __init__(self, target: Path) -> None:
        target = Path(target)
        # Walked as given, so a caller can still relate a yielded path to the
        # target it passed. Compared resolved, so a path that reached us
        # through a link or another spelling is still recognized.
        self.base = target if target.is_dir() else target.parent
        self._given_base = Path(os.path.abspath(self.base))
        self._resolved_base = self.base.resolve()
        self._ignored_files, self._ignored_dirs, self.git_ignore = self._ask_git()
        self._dot: set[Path] = set()
        self._dependency: set[Path] = set()
        self._links: set[Path] = set()
        self._ignored_seen: set[Path] = set()

    def _ask_git(self) -> tuple[frozenset[str], frozenset[str], str]:
        """
        The untracked paths Git ignores below the base, files and directories
        apart, and whether Git answered at all.

        Git is asked, never imitated: nested ignore files, negations and the
        user's own excludes are its to resolve. A tracked file is never in the
        answer, whatever pattern it matches, because Git does not ignore what
        it tracks. A work tree that ignores the base applies no rule below it.
        """
        git = git_executable()
        if git is None or not _held(git, self.base):
            return frozenset(), frozenset(), "unavailable"
        try:
            proc = subprocess.run(
                [git, *GIT_OPTIONS, "-C", str(self.base), "ls-files", "-z", "--others", "--ignored",
                 "--exclude-standard", "--directory"],
                capture_output=True, timeout=GIT_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.SubprocessError):
            return frozenset(), frozenset(), "unavailable"
        if proc.returncode != 0:
            return frozenset(), frozenset(), "unavailable"
        files: set[str] = set()
        dirs: set[str] = set()
        for raw in proc.stdout.split(b"\0"):
            entry = raw.decode("utf-8", errors="surrogateescape")
            if not entry:
                continue
            (dirs if entry.endswith("/") else files).add(_key(entry))
        return frozenset(files), frozenset(dirs), "applied"

    def _skips_directory(self, path: Path, relative: str, record: bool) -> bool:
        name = path.name
        if name.startswith(".") and name not in READ_DOT_DIRECTORIES:
            if record and name not in _UNREPORTED:
                self._dot.add(path)
            return True
        if name in DEPENDENCY_DIRS:
            if record and _key(relative) not in self._ignored_dirs:
                self._dependency.add(path)
            return True
        if _key(relative) in self._ignored_dirs:
            if record:
                self._ignored_seen.add(path)
            return True
        return False

    def _ignores_file(self, path: Path, relative: str, record: bool) -> bool:
        if _key(relative) not in self._ignored_files:
            return False
        if record:
            self._ignored_seen.add(path)
        return True

    def _leaves_link(self, path: Path) -> bool:
        """Asked last: a link another rule skips is reported by that rule."""
        if not _is_link(path):
            return False
        self._links.add(path)
        return True

    def _crosses_link(self, given: Path) -> bool:
        """True when a path below the base, as given, is a link or lies under one."""
        for base in (self._given_base, self._resolved_base):
            try:
                parts = given.relative_to(base).parts
            except ValueError:
                continue
            return any(_is_link(base.joinpath(*parts[:depth])) for depth in range(1, len(parts) + 1))
        return False

    def walk(self) -> Iterator[tuple[Path, list[str]]]:
        """Each directory inside the perimeter with its file names, in a stable order."""
        for dirpath, dirnames, filenames in os.walk(self.base):
            here = Path(dirpath)
            prefix = here.relative_to(self.base).as_posix()
            prefix = "" if prefix == "." else prefix + "/"
            dirnames[:] = [
                name for name in sorted(dirnames)
                if not self._skips_directory(here / name, prefix + name, record=True)
                and not self._leaves_link(here / name)
            ]
            yield here, [
                name for name in sorted(filenames)
                if not self._ignores_file(here / name, prefix + name, record=True)
                and not self._leaves_link(here / name)
            ]

    def covers(self, path: Path) -> bool:
        """
        True when a file is inside the perimeter. A path outside the target is
        not this perimeter's to judge, and passes. A path that names a link
        below the target, or passes through one, is outside whatever it leads to.
        """
        given = Path(os.path.abspath(path))
        resolved = given.resolve()
        if resolved != given and self._crosses_link(given):
            return False
        try:
            parts = resolved.relative_to(self._resolved_base).parts
        except ValueError:
            return True
        for depth in range(1, len(parts)):
            directory = self._resolved_base.joinpath(*parts[:depth])
            if self._skips_directory(directory, "/".join(parts[:depth]), record=False):
                return False
        return not self._ignores_file(resolved, "/".join(parts), record=False)

    @property
    def dot_directories(self) -> list[Path]:
        """The dot directories the walk pruned, outermost only, in a stable order."""
        return sorted(self._dot)

    @property
    def dependency_directories(self) -> list[Path]:
        """The dependency and build directories the walk pruned by name and Git does not ignore, in a stable order:
        what the project keeps of other people's code or of its builds (`vendor/`, a committed `dist/`)."""
        return sorted(self._dependency)

    @property
    def links(self) -> list[Path]:
        """The links the walk left out, as they stand in the tree, in a stable order."""
        return sorted(self._links)

    @property
    def git_ignored(self) -> int:
        """How many ignored paths the walk met: a pruned directory counts once."""
        return len(self._ignored_seen)
