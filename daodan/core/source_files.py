"""What enters a snapshot's inventory: the file kinds it records, the files it never
reads, the walk of the perimeter, and the identity of the tree that holds it."""
from __future__ import annotations

from collections import Counter
import fnmatch
import functools
import hashlib
import math
import os
import re
import subprocess
from pathlib import Path, PurePath, PurePosixPath
from typing import Iterator

import file_formats
from languages import SUPPORTED_EXTENSIONS
from tree_scope import GIT_OPTIONS, Perimeter, git_executable, work_tree


# Hashed but never parsed above this size; recorded with no symbols.
MAX_PARSE_BYTES = 2_000_000
# Not recorded at all above this size: a file this large is not what a claim cites.
MAX_FILE_BYTES = 20_000_000


# Non-source files a phase file legitimately cites. API contracts (protobuf,
# GraphQL, Prisma, XML schemas and WSDL), build files (Gradle, CMake, make,
# .NET project files) and infrastructure as code (Terraform) are inventoried
# as file-level entries: a claim can cite them and a diff notices their edits,
# with no symbols invented for them. `.properties`, `.config` and `.tfvars` stay
# out on purpose: they routinely hold passwords, and the forbidden list below
# filters by name, never by content.
DOC_EXTENSIONS = file_formats.DOCUMENTS

# Build manifests without an extension of their own. They declare the modules
# of a project (modules.py reads them), or how it runs (a Dockerfile), so they
# enter the manifest as file-level entries like any other configuration file.
MANIFEST_FILES = file_formats.MANIFESTS
# Makefiles: the ones GNU Make reads, and the other dialects and templates, which the pre-map names as gaps
MAKEFILES = file_formats.MAKEFILES


BUILD_FOLDERS = file_formats.BUILD_FOLDERS  # folders whose files without a suffix are build files: Conan's profiles


def is_build_file(name: str) -> bool:
    """A build file without a suffix the snapshot records by its name."""
    return name in MANIFEST_FILES or bool(MAKEFILES.match(name))

# Presentation files no adapter parses: Pug and Stylus. They carry no symbols,
# but they decide whether a screen renders, scrolls and can be completed, so
# they enter the manifest as file-level entries: a phase file can cite them and
# an incremental run notices when one changes. The set exists because a run
# once held not one `.css` path while a global dark-theme rule was overriding a
# consent modal's positioning and locking users out. Stylesheets and the style
# blocks of markup and components left it for their adapters, which record
# every rule as a symbol.
PRESENTATION_EXTENSIONS = file_formats.PRESENTATION  # `.jade`: Pug's name before 2016

# File-level sources whose explicit module references are read by the stack checker.
STACK_SOURCE_LANGUAGES = file_formats.STACK_SOURCES

# What the Codebase Map never reads; such a file never enters the manifest, not even as a hash: the snapshot's header
# names it in `excluded` by its path alone (`file_inventory.excluded`). The obvious credential files, by name alone.
FORBIDDEN_GLOBS = file_formats.FORBIDDEN
# Any other name that speaks of secrets is read unless its content holds a generated value: a
# run of at least 20 characters with an entropy of at least 4.5 bits per character, or 3 when
# hexadecimal. secretCipher.js holds the code that encrypts, not a key.
SECRET_NAME_GLOBS = file_formats.SECRET_NAMES
_RUN = re.compile(r"[A-Za-z0-9+/_.!@#$%^&*~?|-]{20,}")
_HEX = re.compile(r"[0-9a-fA-F]+")
_SCAN_BYTES = 2 * 1024 * 1024


def _generated(run: str) -> bool:
    entropy = -sum(n / len(run) * math.log2(n / len(run)) for n in Counter(run).values())
    return not run.isdigit() and entropy >= (3.0 if _HEX.fullmatch(run) else 4.5)


@functools.lru_cache(maxsize=4096)
def _holds_generated_value(path: str, mtime_ns: int, size: int) -> bool:
    try:
        with open(path, "rb") as stream:
            text = stream.read(_SCAN_BYTES).decode("utf-8", "ignore")
    except OSError:
        return True
    return any(_generated(run) for run in _RUN.findall(text))


def is_forbidden(name: str, path: Path | None = None) -> bool:
    """
    True for a file the Codebase Map must never read. Case-insensitive.

    A name that speaks of secrets without being an obvious credential file is judged by the
    content read through `path`; without a path such a file is not forbidden.
    """
    lowered = name.lower()
    if any(fnmatch.fnmatchcase(lowered, glob) for glob in FORBIDDEN_GLOBS):
        return True
    if path is None or not any(fnmatch.fnmatchcase(lowered, glob) for glob in SECRET_NAME_GLOBS):
        return False
    try:
        stat = path.stat()
    except OSError:
        return False
    return _holds_generated_value(str(path), stat.st_mtime_ns, stat.st_size)


def is_inventory_path(path: PurePath) -> bool:
    """Whether the snapshot records this kind of file, independent of its contents and perimeter."""
    suffix = path.suffix.lower()
    return (suffix in SUPPORTED_EXTENSIONS or suffix in DOC_EXTENSIONS or suffix in PRESENTATION_EXTENSIONS
            or suffix in STACK_SOURCE_LANGUAGES or is_build_file(path.name)
            or not suffix and path.parent.name in BUILD_FOLDERS)


def iter_walked(target: Path, perimeter: Perimeter | None = None,
                forbidden: list[Path] | None = None) -> Iterator[Path]:
    """Every file the walk of the perimeter allows, whether or not the snapshot records its kind, in a stable order. A
    file `is_forbidden` forbids is never yielded: its path alone goes to `forbidden`, when given."""
    perimeter = perimeter or Perimeter(target)
    for directory, filenames in perimeter.walk():
        for name in filenames:
            path = directory / name
            if target.is_file() and path != target:
                continue
            if is_forbidden(name, path):
                if forbidden is not None:
                    forbidden.append(path)
                continue
            yield path


def iter_files(target: Path, perimeter: Perimeter | None = None) -> Iterator[Path]:
    """
    Every file in the target the snapshot records, in a stable order.

    Which directories are descended into is the perimeter's rule, in
    tree_scope.py, and not this function's: nothing Git ignores, no directory
    whose name starts with a dot but those the stack tool reads, no dependency or build output. Pass a
    perimeter to read back afterwards what the walk left out.
    """
    for path in iter_walked(target, perimeter):
        if is_inventory_path(path):
            yield path


def read_text(path: Path) -> str:
    """File content with newlines normalized, so a line-ending change is not an edit."""
    data = path.read_bytes()
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def hash_text(text: str) -> str:
    """Short content hash. 16 hex characters: readable in a manifest, ample here."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def repo_root(target: Path) -> Path:
    """
    The base every manifest path is relative to: the top level of the work
    tree that holds the target, otherwise the target itself. A work tree that
    ignores the target does not hold it.
    """
    base = target.parent if target.is_file() else target
    return work_tree(base) or base


def _git(git: str, at: Path, *args: str, given: bytes | None = None, seconds: int = 10,
         answers: tuple[int, ...] = (0,)) -> bytes | None:
    """The output of Daodan's own `git` (no fsmonitor, no hooks: `GIT_OPTIONS`) in `at`; None when it does not answer
    (exits with a code outside `answers`, or not in `seconds`)."""
    try:
        proc = subprocess.run([git, *GIT_OPTIONS, "-C", str(at), *args], input=given, capture_output=True,
                              timeout=seconds)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode in answers else None


NO_ATTRIBUTES = "no Git work tree holds the project: its .gitattributes are not read"


def git_attributes(root: Path, paths: list[str], names) -> tuple[dict[str, dict[str, str]], str | None]:
    """
    The value of each attribute of `names` that `.gitattributes` gives each of
    `paths` (relative to `root`), as `git check-attr` reads them: it reads the
    attributes and runs nothing (`GIT_OPTIONS` keeps fsmonitor and hooks off).
    `unspecified` is left out. With why Git did not say, when a `.gitattributes`
    is among the paths and no work tree holds the root or Git did not answer.
    """
    git = git_executable()
    top = work_tree(root) if git is not None else None
    declared = any(PurePath(rel).name == ".gitattributes" for rel in paths)
    if top is None:
        return {}, NO_ATTRIBUTES if declared else None
    said = _git(git, root, "check-attr", "--stdin", "-z", *names, given=b"".join(p.encode() + b"\0" for p in paths))
    if said is None:
        return {}, "git check-attr did not answer" if declared else None
    found: dict[str, dict[str, str]] = {}
    fields = said.split(b"\0")
    for path, name, value in zip(fields[0::3], fields[1::3], fields[2::3]):
        if value != b"unspecified":
            found.setdefault(path.decode(), {})[name.decode()] = value.decode()
    return found, None


BINARY_SECONDS = 300  # `git grep` reads every file of the perimeter once
PATHSPECS_PER_CALL = 2000  # pathspecs on one command line, well under the system's limit on its length


def _pathspecs(root: Path, paths: list[str]) -> list[str]:
    """What `git grep` is asked for to read the files of `paths` and no other: a folder, for its own files only
    (`--max-depth=0`), when each regular file in it is one of `paths`, else each of its files of `paths`. A file the
    walk left out beside them (a forbidden name, a file Git ignores) is never opened."""
    asked: dict[str, set[str]] = {}
    for rel in paths:
        asked.setdefault(PurePath(rel).parent.as_posix(), set()).add(rel)
    specs = []
    for folder, files in sorted(asked.items()):
        try:
            with os.scandir(root / folder) as listing:
                whole = all(PurePosixPath(folder, entry.name).as_posix() in files for entry in listing
                            if entry.is_file(follow_symlinks=False))
        except OSError:
            whole = False
        specs += [folder] if whole else sorted(files)
    return specs


def git_binary(root: Path, paths: list[str]) -> tuple[set[str], str | None]:
    """
    The files of `paths` (relative to `root`) that Git calls binary, and why
    Git did not say, if it did not. `git grep -I` tells them apart as Git does
    everywhere (a `binary` or `-diff` attribute, else a NUL byte in the first
    8000 bytes): a non-empty file it does not list as text is binary. Linguist's
    own test is Ruby code (`blob_helper.rb`, a MIME table and an encoding
    detector), not data. `--no-index` reads the files where they stand, with or
    without a work tree, and reads no index; `--no-textconv` and `GIT_OPTIONS`
    leave every program of the checkout unrun. Git reads the files of `paths`
    and no other (`_pathspecs`), by their literal names.
    """
    git = git_executable()
    if git is None:
        return set(), "git is not available: binary files are not told apart"
    specs = _pathspecs(root, paths)
    text: set[str] = set()
    for start in range(0, len(specs), PATHSPECS_PER_CALL):
        said = _git(git, root, "--literal-pathspecs", "grep", "--no-index", "--no-exclude-standard", "--no-textconv",
                    "-I", "-l", "-z", "--max-depth=0", "-e", "", "--", *specs[start:start + PATHSPECS_PER_CALL],
                    seconds=BINARY_SECONDS, answers=(0, 1))  # 1: no file of these paths is text
        if said is None:
            return set(), "git grep did not answer: binary files are not told apart"
        text.update(name.decode("utf-8", errors="surrogateescape") for name in said.split(b"\0") if name)
    binary = set()
    for rel in paths:
        try:
            if rel not in text and (root / rel).stat().st_size:
                binary.add(rel)
        except OSError:
            continue
    return binary, None


FILTERED = "the checkout declares a Git filter, which Daodan does not run on the host"
UNASKED = "Git did not say which filters the checkout declares"


def git_info(root: Path) -> dict | None:
    """
    Commit, branch and dirtiness, as metadata, of the work tree that holds the
    root: none for a root no work tree holds. Nothing in the diff depends on it.

    `git status` reads the content of a changed file through the filter the
    checkout declares for it (.gitattributes, its configuration's program),
    which would run the project's code on the host: where a tracked file has
    one (`check-attr`, which reads attributes and runs nothing), or Git does
    not say, `dirty` is None and `dirty_unknown` says why. Status asks no
    submodule (each would run its own filters) and writes no index.
    """
    git = git_executable()
    top = work_tree(root) if git is not None else None
    if top is None:
        return None

    def run(*args: str, at: Path = root, given: bytes | None = None) -> bytes | None:
        return _git(git, at, *args, given=given)

    commit = (run("rev-parse", "HEAD") or b"").decode().strip()
    if not commit:
        return None
    info = {"commit": commit[:12], "branch": (run("rev-parse", "--abbrev-ref", "HEAD") or b"").decode().strip() or None}
    listed = run("ls-files", "-z", at=top)
    said = run("check-attr", "--stdin", "-z", "filter", at=top, given=listed) if listed is not None else None
    if said is None or any(value not in (b"unspecified", b"unset") for value in said.split(b"\0")[2::3]):
        return {**info, "dirty": None, "dirty_unknown": UNASKED if said is None else FILTERED}
    status = run("--no-optional-locks", "status", "--porcelain", "--ignore-submodules=all")
    return {**info, "dirty": bool(status.strip()) if status is not None else None,
            **({"dirty_unknown": "git status did not answer"} if status is None else {})}


def relative_to_root(path: Path, root: Path) -> str:
    """
    POSIX path relative to the manifest root, or absolute when outside it.

    A path is named by where it stands. Callers pass a root and a target they
    resolved, and paths walked from them: resolving again here named a link by
    what it points to.
    """
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def scope_record(perimeter: Perimeter, root: Path) -> dict:
    """
    What a perimeter left out, in the one shape the manifest and the scope
    command share. `git_ignore` is `unavailable` when no work tree holds the
    target or git did not answer: no ignore rule was applied then, and a reader
    must be able to tell.
    """
    return {
        "git_ignore": perimeter.git_ignore,
        "skipped": {
            "dot_directories": [relative_to_root(path, root) for path in perimeter.dot_directories],
            "links": [relative_to_root(path, root) for path in perimeter.links],
            "git_ignored": perimeter.git_ignored,
        },
    }
