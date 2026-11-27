"""The corpus of the SQL grammar benchmark: which projects, at which tag, which of their SQL and PL/SQL files. Pure data
and rules, standard library only. The sources are never kept here: a Modal function with the network open downloads
each archive, reads the members in memory, and records the commit the tag resolved to (GitHub's archive carries it in
its header) and the sha256 of every file. Nothing of a project runs.

A project's `refs` are tried in order, the first that exists is taken; one that does not exist is a hole of the
run, with its cause, never a silent skip.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

SEED = "sql-grammar-1"  # the fixed seed of every cap: the same files are picked every time
SUFFIXES = (".sql", ".pks", ".pkb", ".pls", ".plsql", ".pck", ".prc", ".fnc", ".trg", ".tps", ".tpb")
MAX_BYTES = 2_000_000  # the product's own bound for a file it parses (`source_files.MAX_PARSE_BYTES`)
GLOT_BYTES = 200_000  # sqlglot is measured up to here: a larger file is skipped for it, and counted


@dataclass(frozen=True)
class Project:
    name: str
    repo: str  # owner/name on GitHub
    refs: tuple[str, ...]  # tags (or `heads/branch`), the first that exists
    license: str  # what the project declares; the run records the first line of its LICENSE file
    include: tuple[str, ...]  # path prefixes of what is read ("" is everything)
    dialect: str | None  # sqlglot's dialect for these files: oracle | postgres | None
    exclude: tuple[str, ...] = ()
    cap: int | None = None  # at most this many files, by the seeded order of their paths

    def url(self, ref: str) -> str:
        return f"https://codeload.github.com/{self.repo}/tar.gz/refs/{ref if ref.startswith('heads/') else 'tags/' + ref}"

    def accepts(self, path: str) -> bool:
        return (path.lower().endswith(SUFFIXES) and any(path.startswith(prefix) for prefix in self.include)
                and not any(path.startswith(prefix) for prefix in self.exclude))


PROJECTS = (
    Project("utplsql", "utPLSQL/utPLSQL", ("v3.1.14", "v3.1.13"), "Apache-2.0", ("source/",), "oracle", cap=600),
    Project("logger", "OraOpenSource/Logger", ("v3.1.1", "v3.1.0", "heads/master"), "MIT", ("source/",), "oracle"),
    Project("pljson", "pljson/pljson", ("v3.5.0", "v3.4.1", "heads/master"), "MIT", ("src/",), "oracle"),
    Project("oos-utils", "OraOpenSource/oos-utils", ("v1.0.0", "heads/master"), "MIT", ("source/",), "oracle"),
    Project("oracle-schemas", "oracle-samples/db-sample-schemas", ("v23.3", "v23.2", "v21.1"), "UPL-1.0", ("",), "oracle"),
    Project("postgres-regress", "postgres/postgres", ("REL_17_0",), "PostgreSQL", ("src/test/regress/sql/",), "postgres", cap=250),
    Project("pagila", "devrimgunduz/pagila", ("3.1.0", "3.0.0", "heads/master"), "PostgreSQL", ("",), "postgres"),
)


def strip_root(member: str) -> str:
    """A tar member's path without the archive's own folder (`utPLSQL-3.1.14/source/a.sql` is `source/a.sql`)."""
    return member.split("/", 1)[1] if "/" in member else ""


def select(project: Project, contents: dict[str, str], sizes: dict[str, int], seed: str = SEED) -> list[str]:
    """The project's files: those it accepts within the size bound, one path for each content (the first by path),
    capped by the seeded order. `contents` maps a path to its sha256."""
    seen: set[str] = set()
    kept = []
    for path in sorted(p for p in contents if project.accepts(p) and 0 < sizes[p] <= MAX_BYTES):
        if contents[path] not in seen:
            seen.add(contents[path])
            kept.append(path)
    if project.cap is not None and len(kept) > project.cap:
        kept = sorted(kept, key=lambda p: hashlib.sha256(f"{seed}:{p}".encode()).hexdigest())[:project.cap]
    return sorted(kept)


def fingerprint(hashes: dict[str, str]) -> str:
    """One digest for a selection: the same files give the same string."""
    return hashlib.sha256("\n".join(f"{p} {h}" for p, h in sorted(hashes.items())).encode()).hexdigest()[:16]
