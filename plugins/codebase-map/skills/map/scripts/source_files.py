"""What enters a snapshot's inventory: the file kinds it records, the files it never
reads, the walk of the perimeter, and the identity of the tree that holds it."""
from __future__ import annotations

from collections import Counter
import fnmatch
import functools
import hashlib
import math
import re
import subprocess
from pathlib import Path
from typing import Iterator

from languages import SUPPORTED_EXTENSIONS
from tree_scope import Perimeter, git_executable, work_tree


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
DOC_EXTENSIONS = frozenset({
    ".bat", ".cabal", ".cfg", ".cmake", ".cmd", ".csproj", ".fsproj", ".gemspec", ".gql", ".gradle",
    ".graphql", ".hcl", ".ini", ".json", ".json5", ".jsonc", ".md", ".mk",
    ".plist", ".props", ".proto", ".prisma", ".ps1", ".rst", ".sh", ".sln", ".slnx",
    ".targets", ".tf", ".toml", ".txt", ".vbproj", ".vcproj", ".vcxproj", ".wsdl", ".xml", ".xsd",
    ".xsl", ".xslt", ".yaml", ".yml",
})

# Build manifests without an extension of their own. They declare the modules
# of a project (modules.py reads them), or how it runs (a Dockerfile), so they
# enter the manifest as file-level entries like any other configuration file.
MANIFEST_FILES = frozenset({
    "go.mod", "go.work", "Gemfile", "Package.swift", "mix.exs", "build.sbt",
    "build.zig.zon", "dune-project", "Dockerfile",
})

# Presentation files no adapter parses: Pug and Stylus. They carry no symbols,
# but they decide whether a screen renders, scrolls and can be completed, so
# they enter the manifest as file-level entries: a phase file can cite them and
# an incremental run notices when one changes. The set exists because a run
# once held not one `.css` path while a global dark-theme rule was overriding a
# consent modal's positioning and locking users out. Stylesheets and the style
# blocks of markup and components left it for their adapters, which record
# every rule as a symbol.
PRESENTATION_EXTENSIONS = frozenset({".pug", ".styl", ".stylus"})


# What the Codebase Map never reads; such a file never enters the manifest, not even as a hash.
# The obvious credential files, by name alone.
FORBIDDEN_GLOBS = (
    ".env", ".env.*", "credentials.*", "secrets.*",
    "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*", "id_ed25519*",
    ".npmrc", ".pypirc", ".netrc",
    "*service-account*.json", "*kubeconfig*", "*.tfstate", "*.tfstate.*", "*.keystore", "*.jks",
)
# Any other name that speaks of secrets is read unless its content holds a generated value: a
# run of at least 20 characters with an entropy of at least 4.5 bits per character, or 3 when
# hexadecimal. secretCipher.js holds the code that encrypts, not a key.
SECRET_NAME_GLOBS = ("*secret*", "*credential*")
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


def iter_files(target: Path, perimeter: Perimeter | None = None) -> Iterator[Path]:
    """
    Every file in the target the snapshot records, in a stable order.

    Which directories are descended into is the perimeter's rule, in
    tree_scope.py, and not this function's: nothing Git ignores, no directory
    whose name starts with a dot, no dependency or build output. Pass a
    perimeter to read back afterwards what the walk left out.
    """
    perimeter = perimeter or Perimeter(target)
    for directory, filenames in perimeter.walk():
        for name in filenames:
            path = directory / name
            if is_forbidden(name, path):
                continue
            if target.is_file() and path != target:
                continue
            suffix = path.suffix.lower()
            if (
                suffix not in SUPPORTED_EXTENSIONS
                and suffix not in DOC_EXTENSIONS
                and suffix not in PRESENTATION_EXTENSIONS
                and name not in MANIFEST_FILES
            ):
                continue
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


def git_info(root: Path) -> dict | None:
    """
    Commit, branch and dirtiness, as metadata, of the work tree that holds the
    root: none for a root no work tree holds. Nothing in the diff depends on it.
    """
    git = git_executable()
    if git is None or work_tree(root) is None:
        return None

    def run(*args: str) -> str | None:
        try:
            proc = subprocess.run(
                [git, "-C", str(root), *args], capture_output=True, text=True, timeout=10
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return proc.stdout.strip() if proc.returncode == 0 else None

    commit = run("rev-parse", "HEAD")
    if not commit:
        return None
    return {
        "commit": commit[:12],
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(run("status", "--porcelain")),
    }


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
