#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Resolve a snapshot's unresolved call references with an optional, probed engine.

The lexical resolver in `resolution.py` is the floor: it resolves a unique lexical
binding and nothing it cannot prove. Measured on two real projects it resolved 9.7%
and 13.0% of call references, and an engine recovered 31.6% of the sampled positions
it was asked about (evals/codebase-map/resolver-spike, spec §3.2.2). This command
attaches that engine, and it is optional in the strict sense: it is probed, never
assumed, and its absence is a declared degradation that writes nothing.

Three rules keep an engine's output from being mistaken for the lexical graph's:

1. **Every edge names its resolver.** `payload.resolver` is `builtin-lexical` for a
   lexically resolved reference and `<engine>@<version>` for one this command wrote,
   with `payload.confidence` `confirmed` or `candidate`. Edges of two resolvers are
   not comparable and are never merged into one count.
2. **An edge must arrive at a symbol the snapshot already holds.** The engine's
   answer is graded by membership in this snapshot's own declaration table, which is
   the measured grading and also the prerequisite's point: an engine attached before
   the extraction convention widened produced edges with no arrival node. A target
   file outside the inventory is `external-definition`; a name inside the inventory
   that is no declaration is `project-not-a-symbol`, recorded as a candidate.
3. **Coverage is declared, never implied.** One inference costs about 99 ms (p95
   307 ms), so a whole project's unresolved population is hours, not seconds. The
   run reports how many positions it asked about out of how many, and `--limit`
   bounds it. A partial pass is a partial pass.

One property of an engine's answer needs stating before a consumer trusts an edge:
it can land on a *contract* rather than an implementation. Verified on this
repository's own scripts, `adapter.parse(...)` in `ast_parser.py` infers to the
`LanguageAdapter.parse` declaration in `languages/base.py`, which is the protocol the
call goes through, not the adapter that runs. Such an edge is true and is not
comparable to one landing on a concrete body: a consumer that propagates through it
(`stale-callers`, `edit_impact`) must decide that separately, which is one reason
these edges stay in their own store instead of being merged into the lexical graph.

Run it through uv, which supplies the engine without making it a dependency of the
snapshot:

    uv run --with jedi --no-config --no-project --script resolve_edges.py \
        <manifest.sqlite> --engine jedi --environment <venv-or-site-packages> [...]

Without `--environment` the engine sees the project only, and the measured residual
unresolved rises from 2.7% to 24.1%; the report says which of the two it ran.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import sqlite3
import sys
import tempfile
import time
import tokenize
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from languages.python import require_minimum_interpreter  # noqa: E402
import resolution  # noqa: E402
import semantic_store  # noqa: E402
from source_reader import _binding, _no_links, _source_path  # noqa: E402
from snapshot_store import _pack, _unpack, logical_digest, open_snapshot  # noqa: E402

# The population an engine is asked about: the snapshot's own unresolved call
# references, minus the builtins the lexical resolver declines to model.
EXCLUDED_REASONS = frozenset({"unbound-name"})
ENGINE_RESOLVER_PREFIX = "engine"
CANDIDATE_REASONS = {
    "project-not-a-symbol": "engine-project-not-a-symbol",
    "ambiguous-target": "engine-ambiguous-target",
}


def site_packages_of(environment: Path) -> Path | None:
    """The importable directory of a venv root, a site-packages dir, or neither."""
    if (environment / "pyvenv.cfg").is_file():
        for candidate in (environment / "Lib" / "site-packages",):
            if candidate.is_dir():
                return candidate
        matches = sorted(environment.glob("lib/python*/site-packages"))
        return matches[-1] if matches else None
    if environment.is_dir() and environment.name == "site-packages":
        return environment
    return None


def package_names(site_packages: Path | None) -> list[str]:
    """Directly importable top-level names, excluding installers and metadata.

    This is a static count of the supplied directory. It does not execute `.pth`
    files or claim to enumerate editable dependencies exposed by those files.
    """
    if site_packages is None:
        return []
    excluded = {"pip", "setuptools", "wheel", "pkg_resources", "_distutils_hack",
                "_virtualenv", "__pycache__"}
    names = set()
    for child in site_packages.iterdir():
        name = child.name
        if child.is_file():
            if name.endswith((".py", ".pyc", ".pyd", ".so")):
                name = name.split(".")[0]
            else:
                continue
        if name.isidentifier() and name not in excluded:
            names.add(name)
    return sorted(names)


def requested_interpreter(environment: Path) -> str | None:
    for candidate in (environment / "Scripts/python.exe", environment / "bin/python",
                      environment / "bin/python3"):
        if candidate.is_file():
            return candidate.as_posix()
    if (environment / "pyvenv.cfg").is_file():
        relative = "Scripts/python.exe" if (environment / "Lib/site-packages").is_dir() else "bin/python"
        return (environment / relative).as_posix()
    return None


class JediEngine:
    """The measured Python engine: Jedi, inferring at the callee name.

    The environment model is the one the recording campaign measured, not a
    simpler one: an inference run against the project's real environments confirmed
    505 of 1,600 positions with 2.7% residual, and the same run without them 403
    with 24.1% residual (evals/codebase-map/resolver-spike/RESULTS.md). So each
    `--environment` is turned into a real Jedi environment through
    `create_environment(path, safe=False)`, and only an environment that fails to
    build degrades to `added_sys_path` over only its own site-packages. Populated
    environments beat installer-only stubs; serving scope breaks ties between
    populated offers. A run with no usable environment uses `project-only` mode.
    The report records the choice, interpreter and package count for each file.

    Deliberately not touched: `jedi.settings.fast_parser`. Setting it to False raises
    a KeyError inside jedi 0.20.1 (`jedi/inference/syntax_tree.py`), which the
    campaign recorded as a known pitfall rather than working around.
    """

    name = "jedi"

    def __init__(self, project_root: Path, environments: list[Path]):
        self.project_root = project_root
        self.requests = environments
        self.modes: dict[str, int] = {}
        self.unusable: list[str] = []
        self.built: list[dict] = []
        self._per_root: dict[Path, tuple] = {}
        self.file_environments: dict[str, dict] = {}
        self.version: str | None = None
        self.plain_project = None
        self.default_environment = None

    def scope_of(self, root: Path) -> Path:
        """The source subtree an environment serves.

        A conventional venv (`.venv`, `venv`, `env`) lives inside the package
        directory it serves and no source file is ever inside the venv itself, so
        nearest-enclosing has to match the parent. Anything else scopes to its own
        directory.
        """
        if root.name == "site-packages":
            for ancestor in list(root.parents)[:3]:
                if (ancestor / "pyvenv.cfg").is_file():
                    return self.scope_of(ancestor)
            # A bare directory was explicitly offered for this project; its
            # dependencies cannot serve source files inside site-packages itself.
            return self.project_root
        parent = root.parent
        if root.name in (".venv", "venv", "env") and parent != root:
            try:
                parent.relative_to(self.project_root)
            except ValueError:
                return root
            return parent
        return root

    def probe(self) -> tuple[bool, str]:
        """Import the engine, build its environments, and answer one real inference.

        A version string is not readiness: the measured campaign found ten defects in
        its own harness before it could measure, two of them producing plausibly
        false numbers. Readiness is an inference that answers.
        """
        self.modes.clear()
        self.unusable.clear()
        self.built.clear()
        self._per_root.clear()
        self.file_environments.clear()
        try:
            import jedi
        except ImportError as error:
            return False, (f"jedi is not installed: {error}. Run this command through "
                           f"`uv run --with jedi --no-config --no-project --script "
                           f"resolve_edges.py` or install jedi into this interpreter.")
        self.version = getattr(jedi, "__version__", "unknown")
        try:
            from jedi.api.environment import create_environment, get_default_environment
        except ImportError as error:
            return False, f"jedi has no environment API: {error}"
        try:
            self.default_environment = get_default_environment()
            self.plain_project = jedi.Project(path=str(self.project_root),
                                              added_sys_path=[str(self.project_root)])
            for request in self.requests:
                entry = {"path": request.as_posix(), "scope": self.scope_of(request).as_posix(),
                         "environment": None, "mode": None, "site_packages": None,
                         "requested_interpreter": requested_interpreter(request),
                         "interpreter": getattr(self.default_environment, "executable", sys.executable),
                         "package_count": 0, "package_names": [],
                         "package_count_source": "direct site-packages names; .pth not executed"}
                packages = site_packages_of(request)
                entry["site_packages"] = packages.as_posix() if packages else None
                environment = None
                project = self.plain_project
                if packages is None:
                    entry["mode"] = "unusable"
                    self.unusable.append(str(request))
                else:
                    try:
                        entry["package_names"] = package_names(packages)
                    except OSError as error:
                        entry["package_inventory_error"] = f"{type(error).__name__}: {error}"[:300]
                        entry["mode"] = "unusable"
                        self.unusable.append(str(request))
                        self.built.append(entry)
                        continue
                    entry["package_count"] = len(entry["package_names"])
                    try:
                        environment = create_environment(str(request), safe=False)
                        # The report carries a description, never the live object:
                        # the binding is JSON and an Environment is not serializable.
                        entry["environment"] = getattr(environment, "path", None) or str(request)
                        entry["interpreter"] = getattr(environment, "executable", None) \
                            or entry["requested_interpreter"] or str(request)
                        version = getattr(environment, "version_info", None)
                        entry["python_version"] = ".".join(map(str, version[:3])) if version else None
                        entry["mode"] = "create_environment"
                    except Exception as error:
                        environment = None
                        entry["mode"] = "added_sys_path"
                        entry["create_environment_error"] = \
                            f"{type(error).__name__}: {error}"[:300]
                        # Only this environment's dependency directory is added.
                        # Pooling all candidates silently gives a file packages
                        # from unrelated projects and misstates its provenance.
                        project = jedi.Project(path=str(self.project_root),
                                               added_sys_path=[str(self.project_root), str(packages)])
                self.built.append(entry)
                self._per_root[request] = (environment, project, entry)
            # Positional, because jedi 0.20 renamed the keyword `source` to `code`.
            # Verified against jedi 0.20.1; the identity that answered is recorded in
            # the edge store's binding, so another version is another resolver.
            probe = jedi.Script("import os\nos.getcwd()\n", project=self.plain_project,
                                environment=self.default_environment)
            if not probe.infer(line=2, column=6):
                return False, "jedi answered no definition for its own readiness probe"
        except Exception as error:  # an engine that cannot infer is not ready
            return False, f"{type(error).__name__}: {error}"
        return True, ""

    def environment_for(self, absolute: Path) -> tuple:
        """Prefer populated environments, then the nearest eligible serving scope."""
        candidates = [item for item in self._per_root.values() if item[2]["mode"] != "unusable"]
        populated = [item for item in candidates if item[2]["package_count"] > 0]
        candidates = populated or candidates
        scoped = [item for item in candidates if absolute.is_relative_to(Path(item[2]["scope"]))]

        def rank(item):
            entry = item[2]
            scope = Path(entry["scope"])
            shared = len(Path(os.path.commonpath([absolute.parent, scope])).parts) \
                if absolute.drive == scope.drive else 0
            distance = len(absolute.parent.parts) + len(scope.parts) - 2 * shared
            return (-len(scope.parts) if scoped else distance,
                    entry["mode"] != "create_environment", entry["path"])

        if candidates:
            environment, project, entry = min(scoped or candidates, key=rank)
            mode = entry["mode"]
            record = {key: entry[key] for key in ("path", "scope", "mode", "interpreter",
                                                  "requested_interpreter", "package_count")}
            record["selection"] = ("populated" if populated else "empty") + \
                ("-serving-scope" if scoped else "-nearest-offered-environment")
        else:
            environment, project, mode = self.default_environment, self.plain_project, "project-only"
            record = {"path": None, "mode": mode, "scope": self.project_root.as_posix(),
                      "interpreter": getattr(self.default_environment, "executable", sys.executable),
                      "requested_interpreter": None, "package_count": 0,
                      "selection": "no-usable-environment"}
        try:
            file = absolute.relative_to(self.project_root).as_posix()
        except ValueError:
            file = absolute.as_posix()
        self.file_environments[file] = record
        self.modes[mode] = self.modes.get(mode, 0) + 1
        return project, environment or self.default_environment, mode

    def definitions(self, path: Path, line: int, column: int) -> list:
        import jedi
        project, environment, _mode = self.environment_for(Path(path).resolve())
        script = jedi.Script(path=str(path), project=project, environment=environment)
        return script.infer(line=line, column=column)

    def identity(self) -> str:
        return f"{self.name}@{self.version}"

    def report(self) -> dict:
        return {"environments": self.built, "unusable_environments": self.unusable,
                "inference_modes": dict(sorted(self.modes.items())),
                "file_environments": dict(sorted(self.file_environments.items()))}


def callee_column(source_line: str, span: list[int], last_part: str) -> int | None:
    """Convert the callee's UTF-8 byte span to Jedi's character column.

    For a multiline expression, the supplied line is the span's final line. A
    Python callee ends at the span's end; a matching substring elsewhere in its
    receiver is insufficient evidence of its position.
    """
    start, end = (span[1] if span[0] == span[2] else 0), span[3]
    encoded = source_line.encode("utf-8")
    if not last_part or not 0 <= start < end <= len(encoded):
        return None
    try:
        window = encoded[start:end].decode("utf-8")
        if not window.endswith(last_part):
            return None
        byte_column = end - len(last_part.encode("utf-8"))
        return len(encoded[:byte_column].decode("utf-8"))
    except UnicodeError:
        return None


def symbol_table(connection, rel: str, source: str) -> tuple[dict, set]:
    """Bind exact engine name positions to this snapshot's declarations.

    Snapshot spans begin at `def`, `async` or `class`; Jedi positions begin at the
    declaration's name. Tokenize the verified source to bridge those conventions.
    A matching bare name at a different position proves no edge.
    """
    names = {}
    previous = None
    declaration = None
    lines = source.split("\n")
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if declaration is not None and token.type == tokenize.NAME:
                kind, line, column = declaration
                names[(kind, line, column)] = (
                    unicodedata.normalize("NFKC", token.string), *token.start)
                declaration = None
            if token.type == tokenize.NAME and token.string in ("def", "class"):
                line, column = token.start
                if token.string == "def" and previous is not None \
                        and previous.type == tokenize.NAME and previous.string == "async":
                    line, column = previous.start
                byte_column = len(lines[line - 1][:column].encode("utf-8"))
                declaration = ("function" if token.string == "def" else "class",
                               line, byte_column)
            previous = token
    except (tokenize.TokenError, IndentationError):
        # Successfully recorded declarations before a damaged suffix remain
        # usable only when this snapshot independently holds their exact spans.
        pass
    rows = connection.execute(
        "SELECT id, name, kind, l0, c0 FROM sem_declarations "
        "WHERE file=? AND kind IN ('function','class') ORDER BY l0,c0", (rel,))
    table: dict = {}
    ambiguous: set = set()
    for identity, name, kind, line, column in rows:
        position = names.get((kind, line, column))
        if position is None or position[0] != name:
            continue
        key = (name, kind, position[1], position[2])
        if key in table and table[key] != identity:
            ambiguous.add(key)
        table.setdefault(key, identity)
    return table, ambiguous


def inventory_files(connection) -> set[str]:
    return {row[0] for row in connection.execute(
        "SELECT file FROM sem_coverage WHERE status='ast'")}


def grade(definition, inventory: set[str], tables: dict, root: Path,
          table_for) -> tuple[str, dict | None]:
    """One engine answer, graded by what this snapshot holds.

    Returns `(verdict, target)` where verdict is `edge-call`, `edge-instantiation`,
    `external-definition`, `project-not-a-symbol`, `ambiguous-target` or `unresolved`,
    and target carries the declaration identity an edge arrives at.
    """
    if definition is None:
        return "unresolved", None
    module_path = getattr(definition, "module_path", None)
    name = getattr(definition, "name", None) or ""
    if not module_path or not name:
        return "external-definition", None
    try:
        relative = Path(module_path).resolve().relative_to(root).as_posix()
    except ValueError:
        return "external-definition", None
    if relative not in inventory:
        # Inside the project directory but not in the snapshot: a virtual
        # environment, a build output, a file the perimeter leaves out. Counting
        # exactly these as project code was the measured harness defect that made
        # the published gap three times its real size.
        return "external-definition", None
    if relative not in tables:
        tables[relative] = table_for(relative)
    table, ambiguous = tables[relative]
    kind = getattr(definition, "type", None)
    line = getattr(definition, "line", None)
    column = getattr(definition, "column", None)
    if kind not in ("function", "class") or type(line) is not int \
            or type(column) is not int:
        return "project-not-a-symbol", None
    key = (unicodedata.normalize("NFKC", name), kind, line, column)
    if key in ambiguous:
        return "ambiguous-target", None
    identity = table.get(key)
    if identity is not None:
        verdict = "edge-instantiation" if kind == "class" else "edge-call"
        return verdict, {"id": identity, "file": relative, "kind": kind}
    return "project-not-a-symbol", None


def grade_all(definitions, inventory: set[str], tables: dict, root: Path,
              table_for) -> tuple[str, dict | None]:
    """Confirm only if every engine answer identifies the same declaration."""
    if not definitions:
        return "unresolved", None
    answers = [grade(item, inventory, tables, root, table_for) for item in definitions]
    first_verdict, first_target = answers[0]
    if all(answer == answers[0] for answer in answers):
        return first_verdict, first_target
    return "ambiguous-target", None


def verify_sources(store) -> tuple[Path, dict[str, Path]]:
    """Check the complete inventory, including dependencies inferred indirectly."""
    root, target, perimeter = _binding(store)
    paths = {}
    for rel, entry in store.iter_file_headers_only():
        path = _source_path(rel, root, target, perimeter)
        expected = entry.get("raw_hash")
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        if not isinstance(expected, str) or digest.hexdigest() != expected:
            raise ValueError(f"source differs from snapshot: {rel}; refresh the snapshot")
        paths[rel] = path
    return root, paths


def edge_destination(out: Path, manifest: Path, sources: dict[str, Path]) -> Path:
    """Refuse evidence collisions and linked destinations before any write."""
    out = Path(os.path.abspath(out))
    existing = out
    while not existing.exists() and not existing.is_symlink():
        existing = existing.parent
    _no_links(existing)
    protected = [Path(manifest).resolve(), *sources.values()]
    for path in protected:
        if out == path or (out.exists() and path.exists() and out.samefile(path)):
            raise ValueError(f"engine edge output would overwrite snapshot evidence: {out}")
    return out


EDGE_SCHEMA = 1


def default_edge_store(manifest: Path) -> Path:
    """The derived store's place: beside the snapshot it is bound to."""
    return Path(manifest).with_name("engine-edges.sqlite")


def write_edge_store(out: Path, edges: list[dict], binding: dict) -> Path:
    """Write the engine's edges atomically, so a partial pass leaves no store."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{out.name}.", suffix=".partial", dir=out.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        connection = sqlite3.connect(temporary)
        try:
            connection.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value BLOB NOT NULL)")
            connection.execute(
                "CREATE TABLE edges(reference_id TEXT PRIMARY KEY,file TEXT NOT NULL,caller TEXT,"
                "target_id TEXT,verdict TEXT NOT NULL,resolver TEXT NOT NULL,"
                "confidence TEXT NOT NULL,l0 INTEGER,c0 INTEGER,payload BLOB NOT NULL)")
            connection.execute("CREATE INDEX edges_file ON edges(file)")
            connection.execute("CREATE INDEX edges_target ON edges(target_id)")
            connection.executemany("INSERT INTO meta VALUES(?,?)",
                                   [(key, _pack(value)) for key, value in sorted(binding.items())])
            connection.executemany(
                "INSERT INTO edges VALUES(?,?,?,?,?,?,?,?,?,?)",
                [(edge["reference_id"], edge["file"], edge["caller"], edge["target_id"],
                  edge["verdict"], edge["resolver"], edge["confidence"], edge["l0"], edge["c0"],
                  _pack(edge["payload"])) for edge in edges])
            connection.commit()
        finally:
            connection.close()
        os.replace(temporary, out)
    finally:
        temporary.unlink(missing_ok=True)
    return out


def read_edge_store(path: Path, store) -> tuple[list[dict] | None, dict | None, str | None]:
    """The edges bound to this exact snapshot, their binding, or the reason they are not.

    A store whose manifest digest, parser fingerprint or resolver version differs
    describes another snapshot or policy, and its edges are not this graph's: the
    caller gets the reason rather than a plausible-looking join.
    """
    path = Path(path)
    if not path.is_file():
        return None, None, f"no engine edge store at {path}"
    connection = None
    binding = None
    try:
        connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        binding = {key: _unpack(value) for key, value in connection.execute("SELECT key,value FROM meta")}
        if binding.get("schema") != EDGE_SCHEMA:
            return None, binding, f"engine edge store schema {binding.get('schema')} is not {EDGE_SCHEMA}"
        if binding.get("manifest_digest") != logical_digest(store):
            return None, binding, "the edge store is bound to a different snapshot revision"
        if binding.get("parser_fingerprint") != store.metadata.get("parser_fingerprint"):
            return None, binding, "the edge store was written under another parser fingerprint"
        if binding.get("resolver_version") != semantic_store.RESOLVER_VERSION:
            return (
                None,
                binding,
                f"the edge store was written under resolver version {binding.get('resolver_version')}, "
                f"expected {semantic_store.RESOLVER_VERSION}",
            )
        edges = [dict(reference_id=row[0], file=row[1], caller=row[2], target_id=row[3],
                      verdict=row[4], resolver=row[5], confidence=row[6], l0=row[7], c0=row[8],
                      payload=_unpack(row[9]))
                 for row in connection.execute(
                     "SELECT reference_id,file,caller,target_id,verdict,resolver,confidence,"
                     "l0,c0,payload FROM edges ORDER BY file,l0,c0")]
        if getattr(store, "format", None) == "sqlite" and getattr(store, "connection", None) is not None:
            with semantic_store.semantic_reader(store) as sem_db:
                valid_targets = {
                    row[0]
                    for row in sem_db.execute(
                        "SELECT id FROM sem_declarations WHERE kind IN ('function','class')"
                    )
                }
                valid_refs = {
                    row[0]: (row[1], row[2])
                    for row in sem_db.execute(
                        "SELECT id,file,caller FROM sem_references WHERE kind='call'"
                    )
                }
            for edge in edges:
                ref_id = edge.get("reference_id")
                if ref_id not in valid_refs:
                    return None, binding, f"engine edge reference is not in snapshot: {ref_id}"
                ref_file, ref_caller = valid_refs[ref_id]
                if edge.get("file") != ref_file or edge.get("caller") != ref_caller:
                    return None, binding, f"engine edge callsite metadata mismatch for {ref_id}"
                if edge.get("confidence") == "confirmed" or str(edge.get("verdict", "")).startswith("edge-"):
                    target_id = edge.get("target_id")
                    if not target_id or target_id not in valid_targets:
                        return None, binding, f"engine edge target is not in snapshot: {target_id}"
        return edges, binding, None
    except (sqlite3.Error, ValueError, TypeError) as error:
        return None, binding, f"invalid engine edge store: {error}"
    finally:
        if connection is not None:
            connection.close()


def resolve_edges(manifest: Path, *, engine, limit: int | None, stride: int,
                  dry_run: bool = False, out: Path | None = None) -> dict:
    """Ask the engine about the unresolved call references and record what it proves."""
    run_started = time.perf_counter()
    if limit is not None and (type(limit) is not int or limit < 0):
        raise ValueError("limit must be a nonnegative integer")
    if type(stride) is not int or stride < 1:
        raise ValueError("stride must be a positive integer")
    with open_snapshot(manifest) as store:
        if store.format != "sqlite" or store.connection is None:
            return {"engine": engine.name, "available": False,
                    "reason": "a JSON manifest holds no reference table; write the snapshot "
                              "in its default sqlite format to attach an engine"}
        connection = store.connection
        project_root = (Path(store["root"]) / store["target"]).resolve()
        if project_root.is_file():
            project_root = project_root.parent
        fingerprint = store.metadata.get("parser_fingerprint")
        import snapshot
        if fingerprint != snapshot.parser_fingerprint():
            return {"engine": engine.name, "available": False,
                    "reason": "the snapshot's parser fingerprint is not the current one; "
                              "write a current snapshot before attaching an engine"}
        try:
            store_root, source_paths = verify_sources(store)
            destination = edge_destination(out or default_edge_store(manifest), manifest, source_paths)
        except (OSError, ValueError) as error:
            return {"engine": engine.name, "available": False,
                    "reason": str(error), "stage": "before-inference", "edges_store": None}
        probe_started = time.perf_counter()
        ready, reason = engine.probe()
        probe_elapsed = time.perf_counter() - probe_started
        if not ready:
            return {"engine": engine.name, "available": False, "reason": reason,
                    "install": "uv run --with jedi --no-config --no-project --script resolve_edges.py"}
        inventory = inventory_files(connection)
        rows = connection.execute(
            "SELECT r.id, r.file, r.payload, r.l0, r.c0, r.l1, r.c1 FROM sem_references r "
            "JOIN sem_coverage c ON c.file=r.file "
            "WHERE r.kind='call' AND r.resolution='unresolved' AND c.language='python' "
            "ORDER BY r.id").fetchall()
        population = [row for row in rows
                      if _unpack(row[2]).get("reason") not in EXCLUDED_REASONS]
        selected = population[::stride] if stride > 1 else population
        if limit is not None:
            selected = selected[:limit]

        verdicts: dict[str, int] = {}
        written = 0
        candidates = 0
        edges: list[dict] = []
        skipped_position = 0
        asked = 0
        latencies: list[float] = []
        declarations: dict[str, dict] = {}
        source_lines: dict[str, list[str]] = {}

        def lines_for(rel):
            if rel not in source_lines:
                source_lines[rel] = source_paths[rel].read_text(encoding="utf-8").split("\n")
            return source_lines[rel]

        for reference_id, rel, blob, l0, c0, l1, c1 in selected:
            payload = _unpack(blob)
            parts = payload.get("parts") or []
            if not parts:
                # A reference with no parts is a dynamic callee, not a position this
                # command failed to find: the verdict keeps the payload's own reason
                # so the declared coverage says what was really asked about.
                key = payload.get("reason") or "dynamic-reference"
                verdicts[key] = verdicts.get(key, 0) + 1
                continue
            if not l0 or not l1:
                verdicts["no-position"] = verdicts.get("no-position", 0) + 1
                continue
            try:
                lines = lines_for(rel)
            except (OSError, UnicodeError):
                lines = []
            if not 1 <= l0 <= l1 <= len(lines):
                verdicts["no-position"] = verdicts.get("no-position", 0) + 1
                continue
            column = callee_column(lines[l1 - 1], [l0, c0, l1, c1], parts[-1])
            if column is None:
                skipped_position += 1
                verdicts["position-unverified"] = verdicts.get("position-unverified", 0) + 1
                continue
            started = time.perf_counter()
            asked += 1
            try:
                inferred = engine.definitions(source_paths[rel], l1, column)
            except Exception as error:
                verdicts[f"infer-error:{type(error).__name__}"] = \
                    verdicts.get(f"infer-error:{type(error).__name__}", 0) + 1
                continue
            finally:
                latencies.append(time.perf_counter() - started)
            try:
                verdict, target = grade_all(inferred, inventory, declarations, store_root,
                                           lambda name: symbol_table(connection, name,
                                                                     "\n".join(lines_for(name))))
            except (OSError, UnicodeError) as error:
                return {"engine": engine.identity(), "available": False,
                        "reason": f"target source became unavailable during inference: {error}",
                        "stage": "after-inference", "edges_store": None}
            verdicts[verdict] = verdicts.get(verdict, 0) + 1
            if verdict.startswith("edge-") and target is not None:
                written += 1
                confidence = "confirmed"
            elif verdict in CANDIDATE_REASONS:
                candidates += 1
                confidence = "candidate"
            else:
                continue
            edges.append({
                "reference_id": reference_id, "file": rel,
                # The stored payload already qualifies its caller with its file.
                "caller": payload.get("caller"),
                "target_id": (target or {}).get("id"), "verdict": verdict,
                "resolver": engine.identity(), "confidence": confidence,
                "l0": l1, "c0": column,
                "payload": {**payload, "resolver": engine.identity(),
                            "confidence": confidence, "reason": f"engine-{verdict}"},
            })
        try:
            verify_sources(store)
            destination = edge_destination(destination, manifest, source_paths)
        except (OSError, ValueError) as error:
            return {"engine": engine.identity(), "available": False,
                    "reason": str(error), "stage": "after-inference", "edges_store": None}
        if edges:
            no_edges_reason = None
        elif not population:
            no_edges_reason = "no-unresolved-calls"
        elif not selected or not asked:
            no_edges_reason = "not-sampled"
        else:
            no_edges_reason = "no-project-targets"
        binding = {
            "schema": EDGE_SCHEMA,
            "manifest": manifest.as_posix(),
            "manifest_digest": logical_digest(store),
            "parser_fingerprint": fingerprint,
            "resolver_version": semantic_store.RESOLVER_VERSION,
            "engine": engine.identity(),
            "engine_report": engine.report() if hasattr(engine, "report") else {},
            "population": len(population),
            "population_language": "python",
            "selected": len(selected),
            "asked": asked,
            "stride": stride,
            "confirmed": written,
            "candidates": candidates,
            "no_edges_reason": no_edges_reason,
            "source_verification": {"before_inference": len(source_paths),
                                    "after_inference": len(source_paths)},
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    latencies.sort()
    written_path = None
    if not dry_run:
        # The snapshot is evidence and stays read-only: an engine's edges are a
        # derived store bound to it, the way cards are, never a mutation of it.
        # Persist valid empty passes too so consumers tell a completed empty
        # pass apart from a missing store.
        try:
            written_path = write_edge_store(destination, edges, binding)
        except (OSError, sqlite3.Error, ValueError) as error:
            return {"engine": engine.identity(), "available": False,
                    "reason": f"could not publish the engine edge store: {error}",
                    "stage": "write", "edges_store": None}
    return {
        "engine": engine.identity(),
        "available": True,
        "project_root": project_root.as_posix(),
        **(engine.report() if hasattr(engine, "report") else
           {"environments": [], "unusable_environments": [], "inference_modes": {}}),
        "population": len(population),
        "population_language": "python",
        "selected": len(selected),
        "asked": asked,
        "stride": stride,
        "confirmed_edges": written,
        "candidates": candidates,
        "no_edges_reason": no_edges_reason,
        "position_unverified": skipped_position,
        "source_verification": binding["source_verification"],
        "verdicts": verdicts,
        "probe_init_elapsed_ms": round(1000 * probe_elapsed, 1),
        "inference_elapsed_ms": round(1000 * sum(latencies), 1),
        "total_elapsed_ms": round(1000 * (time.perf_counter() - run_started), 1),
        "latency_mean_ms": round(1000 * sum(latencies) / len(latencies), 1) if latencies else None,
        "latency_p95_ms": round(1000 * latencies[math.ceil(len(latencies) * 0.95) - 1], 1) if latencies else None,
        "inference_only_extrapolation": {
            "estimated_ms": round(1000 * sum(latencies) / asked * len(population), 1) if asked else None,
            "asked": asked, "selected": len(selected), "population": len(population), "stride": stride,
            "sampling_bias": "References are ordered by id, sampled by stride, then truncated by limit. "
                             "This deterministic sample may favor particular files and call shapes. "
                             "Dynamic or unverified selected references receive no inference request.",
            "assumption": "Every population reference requires one request at the observed mean request cost.",
            "cost_scope": "Engine inference only; probe/init, source verification, grading and output writing excluded.",
        },
        "dry_run": dry_run,
        "edges_store": written_path.as_posix() if written_path else None,
        "coverage": f"{asked} of {len(population)} unresolved call references",
        "note": "Engine edges live in a derived store bound to this snapshot; the "
                "snapshot itself is unchanged. Every edge names payload.resolver, so "
                "engine edges are never counted together with builtin-lexical ones.",
    }


def compact_report(report: dict, *, report_out: Path | None = None) -> dict:
    """Bounded summary for CLI/coordinator callers when the full report is on disk."""
    summary = {
        key: report[key]
        for key in (
            "engine", "available", "reason", "stage", "install", "project_root",
            "population", "population_language", "selected", "asked", "stride",
            "confirmed_edges", "candidates", "no_edges_reason", "position_unverified",
            "source_verification", "probe_init_elapsed_ms", "inference_elapsed_ms",
            "total_elapsed_ms", "latency_mean_ms", "latency_p95_ms", "dry_run",
            "edges_store", "coverage",
        )
        if key in report
    }
    if report_out is not None:
        summary["report_out"] = report_out.as_posix()
    return summary


def main(argv: list[str] | None = None) -> int:
    require_minimum_interpreter("resolve_edges.py")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("manifest", type=Path, help="a snapshot's manifest.sqlite")
    parser.add_argument("--engine", choices=("jedi",), default="jedi")
    parser.add_argument("--environment", action="append", default=[], type=Path,
                        help="a virtual-environment root of the project under analysis, "
                             "turned into a real Jedi environment; a bare site-packages "
                             "directory also works, in added_sys_path mode. Repeatable; "
                             "populated environments beat empty stubs, then the "
                             "nearest serving scope wins per file")
    parser.add_argument("--limit", type=int, default=None,
                        help="ask about at most this many positions")
    parser.add_argument("--stride", type=int, default=1,
                        help="ask about every Nth position, for a deterministic sample")
    parser.add_argument("--dry-run", action="store_true",
                        help="grade and report without writing the edge store")
    parser.add_argument("--out", type=Path, default=None,
                        help="where to write the derived edge store; default "
                             "engine-edges.sqlite beside the manifest")
    parser.add_argument("--report-out", type=Path, default=None,
                        help="optional file path for the complete JSON report")
    parser.add_argument("--compact", action="store_true",
                        help="emit a compact summary on stdout instead of the full report")
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be nonnegative")
    if args.stride < 1:
        parser.error("--stride must be positive")

    manifest = args.manifest.resolve()
    if not manifest.is_file():
        print(json.dumps({"error": f"no such manifest: {manifest}"}), file=sys.stderr)
        return 2
    with open_snapshot(manifest) as store:
        project_root = (Path(store["root"]) / store["target"]).resolve()
        if project_root.is_file():
            project_root = project_root.parent
    engine = JediEngine(project_root, [path.resolve() for path in args.environment])
    report = resolve_edges(manifest, engine=engine, limit=args.limit,
                           stride=args.stride, dry_run=args.dry_run, out=args.out)
    report_out = None
    if args.report_out is not None:
        report_out = args.report_out.resolve()
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    emitted = compact_report(report, report_out=report_out) if args.compact else (
        {**report, "report_out": report_out.as_posix()} if report_out is not None else report
    )
    print(json.dumps(emitted, indent=2, sort_keys=True))
    return 0 if report.get("available") else 1


if __name__ == "__main__":
    raise SystemExit(main())
