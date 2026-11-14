#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Resolve a snapshot's call references with a probed engine.

The lexical resolver in `resolution.py` is the floor: it resolves a unique lexical
binding and nothing it cannot prove. Measured on two real projects it resolved 9.7%
and 13.0% of call references, and an engine recovered 31.6% of the sampled positions
it was asked about (evals/codebase-map/resolver-spike, spec §3.2.2). This command
attaches that engine, and it is optional in the strict sense: it is probed, never
assumed, and its absence is a declared degradation that writes nothing.

Three rules keep an engine's output from being mistaken for the lexical graph's:

1. **Every edge names its resolver.** `payload.resolver` is `builtin-lexical` for a
   lexically resolved reference and `<engine>@<version>` for one this command wrote,
   with `payload.confidence` `confirmed`, `candidate` or `external`. Edges of two
   resolvers are not comparable and are never merged into one count.
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

The calls the lexical resolver bound are asked about too, after the unresolved ones:
where the engine names another declaration or a definition outside the project, its
answer is stored and replaces the lexical target in the edge view. Their counts stay
apart, in `checked`, so `population`, `asked` and `confirmed` keep describing the
calls the lexical resolver left unresolved.

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
import asyncio
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import tokenize
import unicodedata
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import NamedTuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from embedding_worker import shared_cache_dir  # noqa: E402
from languages.python import require_minimum_interpreter  # noqa: E402
import resolution  # noqa: E402
import semantic_store  # noqa: E402
from source_reader import _binding, _no_links, _source_path  # noqa: E402
from snapshot_store import _pack, _unpack, logical_digest, open_snapshot  # noqa: E402

# The population an engine is asked about: the snapshot's own unresolved call
# references, minus the builtins the lexical resolver declines to model and minus
# the callees no project declaration is named after (`classify_reference`).
EXCLUDED_REASONS = frozenset({"unbound-name"})
# Files the derived pass leaves beside the edge store.
REPORT_NAME = "engine-report.json"
RUNNING_NAME = "engine-pass.running"
LOG_NAME = "engine-pass.log"
ENGINE_INSTALL = ("install uv, which gives the pass jedi and the snapshot's parser packages, "
                  "or install jedi in the interpreter that writes the snapshot")
ENGINE_RESOLVER_PREFIX = "engine"
CANDIDATE_REASONS = {
    "project-not-a-symbol": "engine-project-not-a-symbol",
    "ambiguous-target": "engine-ambiguous-target",
}
# The end class a per-position verdict is stored as; a candidate verdict is stored `uncertain`.
POSITION_ENDS = {"external-definition": "external", "project-not-a-symbol": "project-value",
                 "ambiguous-target": "project-callable"}


class Location(NamedTuple):
    """Where an engine says a callee is declared.

    `column` is the UTF-8 byte offset of the declaration's name on its 1-based
    `line`, the snapshot's own unit. A location without `module_path` is a
    definition the engine found outside any file, which is external.
    """

    module_path: Path | None
    line: int | None
    column: int | None


def byte_to_char(line: str, column: int) -> int | None:
    """A UTF-8 byte column as a code-point column, or None inside a character."""
    try:
        return len(line.encode("utf-8")[:column].decode("utf-8"))
    except UnicodeError:
        return None


def char_to_byte(line: str, column: int) -> int:
    return len(line[:column].encode("utf-8"))


def byte_to_utf16(line: str, column: int) -> int | None:
    """A UTF-8 byte column as UTF-16 code units, LSP's default position encoding."""
    chars = byte_to_char(line, column)
    return None if chars is None else len(line[:chars].encode("utf-16-le")) // 2


def utf16_to_byte(line: str, units: int) -> int | None:
    count = 0
    for index, character in enumerate(line):
        if count == units:
            return char_to_byte(line, index)
        if count > units:
            return None
        count += 2 if ord(character) > 0xFFFF else 1
    return len(line.encode("utf-8")) if count == units else None


class SourceLines:
    """Lines of the files an engine reads, decoded once."""

    def __init__(self):
        self._lines: dict[Path, list[str]] = {}

    def get(self, path: Path, line: int) -> str | None:
        path = Path(path)
        if path not in self._lines:
            try:
                self._lines[path] = path.read_text(encoding="utf-8").split("\n")
            except (OSError, UnicodeError):
                self._lines[path] = []
        lines = self._lines[path]
        return lines[line - 1] if type(line) is int and 1 <= line <= len(lines) else None


def shared_engine_dir(name: str) -> Path:
    """Where Daodan installs a language server on first use, shared across projects."""
    return shared_cache_dir() / "engines" / name


def free_memory() -> int | None:
    """Bytes of memory available to a new process, or None when the system does not say."""
    if os.name == "nt":
        import ctypes

        class Status(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                        ("total", ctypes.c_ulonglong), ("available", ctypes.c_ulonglong),
                        ("page_total", ctypes.c_ulonglong), ("page_free", ctypes.c_ulonglong),
                        ("virtual_total", ctypes.c_ulonglong), ("virtual_free", ctypes.c_ulonglong),
                        ("extended", ctypes.c_ulonglong)]

        status = Status()
        status.length = ctypes.sizeof(Status)
        return status.available if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)) else None
    try:
        with open("/proc/meminfo", encoding="ascii") as meminfo:
            for row in meminfo:
                if row.startswith("MemAvailable:"):
                    return int(row.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    return None


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
    languages = ("python",)

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
        # Directories the project puts on sys.path at runtime (`runtime_import_roots`).
        self.import_roots: list[Path] = []
        self.lines = SourceLines()
        self.install = None

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
            self.install = ENGINE_INSTALL
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
            roots = [str(self.project_root), *map(str, self.import_roots)]
            # Jedi appends added paths after the environment's, so a standard or
            # installed module still wins over a project script of the same name.
            self.plain_project = jedi.Project(path=str(self.project_root), added_sys_path=roots)
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
                                               added_sys_path=[*roots, str(packages)])
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

    def definitions(self, path: Path, line: int, column: int) -> list[Location]:
        """Infer at a UTF-8 byte column. Jedi counts code points, in both directions."""
        import jedi
        path = Path(path).resolve()
        text = self.lines.get(path, line)
        character = None if text is None else byte_to_char(text, column)
        if character is None:
            raise ValueError(f"no character starts at byte {column} of {path}:{line}")
        project, environment, _mode = self.environment_for(path)
        script = jedi.Script(path=str(path), project=project, environment=environment)
        found = []
        inferred = script.infer(line=line, column=character)
        if inferred and all(definition.type not in ("function", "class") for definition in inferred):
            # The value is an object, as a decorator returns one: the callee is declared where its name is.
            named = [definition for definition in script.goto(line=line, column=character, follow_imports=True)
                     if definition.type in ("function", "class")]
            inferred = named or inferred
        for definition in inferred:
            if definition.module_path is None:
                found.append(Location(None, None, None))
                continue
            target, row, start = Path(definition.module_path), definition.line, definition.column
            # An instance, statement or module names no declaration: it gets no column.
            # Only a project file can hold an edge's target; others need no conversion.
            declared = definition.type in ("function", "class")
            name_line = self.lines.get(target, row)                 if declared and target.is_relative_to(self.project_root) else None
            found.append(Location(target, row, char_to_byte(name_line, start)
                                  if name_line is not None and type(start) is int else None))
        return found

    def identity(self) -> str:
        return f"{self.name}@{self.version}"

    def context(self) -> str | None:
        """What a Jedi answer depends on besides the sources: its version, environments and import roots."""
        try:
            version = metadata.version("jedi")
        except metadata.PackageNotFoundError:
            return None
        offered = []
        for request in self.requests:
            packages = site_packages_of(request)
            try:
                # Distribution folders carry versions, so an upgrade is a new context.
                installed = sorted(child.name for child in packages.iterdir()) if packages else None
            except OSError:
                installed = None
            offered.append([request.as_posix(), installed])
        roots = sorted(path.as_posix() for path in self.import_roots)
        return f"jedi@{version}|" + hashlib.sha256(json.dumps([offered, roots]).encode("utf-8")).hexdigest()

    def report(self) -> dict:
        return {"environments": self.built, "unusable_environments": self.unusable,
                "import_roots": [path.relative_to(self.project_root).as_posix() for path in self.import_roots],
                "inference_modes": dict(sorted(self.modes.items())),
                "file_environments": dict(sorted(self.file_environments.items()))}


class EngineFailure(RuntimeError):
    """The engine can no longer answer; the pass stops asking and reports why."""


# Bounds that keep one server from taking a shared machine.
SERVER_MEMORY_MB = 2048
# A JVM server keeps its whole heap once grown; this one measured 1.8 GB with 2 GB allowed.
JVM_MEMORY_MB = 1024
ENGINE_THREADS = 2
LSP_START_TIMEOUT = 300
LSP_REQUEST_TIMEOUT = 60
LSP_OPEN_DOCUMENTS = 64


class LspEngine:
    """A language server asked `textDocument/definition` at the callee name, as Jedi is asked `infer`.

    multilspy supplies the pinned server releases and the JSON-RPC transport; each
    subclass says how its server is installed, launched, configured and known to be
    ready. The server is installed on first use into the shared engine directory,
    one directory per version, and writes nothing into the project. Positions cross
    the boundary in UTF-8 bytes and are converted to the encoding the server
    negotiated (UTF-16 unless it says otherwise), using the text the server was given.
    """

    name = "lsp"
    server_name = "language-server"
    languages: tuple[str, ...] = ()
    language_ids: dict[str, str] = {}

    def __init__(self, project_root: Path, install_dir: Path | None = None):
        self.project_root = Path(project_root).resolve()
        self.install_root = Path(install_dir) if install_dir else shared_engine_dir(self.server_name)
        self.install = None
        self.installed_now = False
        self.handler = None
        self.loop = None
        self.encoding = "utf-16"
        self.served: dict[Path, tuple[str, list[str]]] = {}
        self.virtual: dict[Path, Path] = {}
        self.open: dict[str, None] = {}
        self.timeouts = 0
        self.lines = SourceLines()

    # What a subclass supplies.
    def pinned(self) -> dict:
        """The release multilspy pins for this server, with at least `version`."""
        raise NotImplementedError

    def prepare(self, home: Path) -> tuple[bool, str]:
        """Install the pinned release into `home` when absent; (False, reason) with `self.install` set if it cannot."""
        raise NotImplementedError

    def command(self, home: Path) -> tuple[list[str], dict]:
        raise NotImplementedError

    def initialization_options(self) -> dict | None:
        return None

    def settings(self) -> dict:
        return {}

    def readiness_probe(self) -> tuple[str, str, int, int] | None:
        """A virtual document and a position whose definition must be on its first line, or None."""
        return None

    async def wait_ready(self) -> None:
        return None

    def notifications(self) -> dict:
        return {}

    def cleanup(self) -> None:
        return None

    # Shared machinery.
    @property
    def version(self) -> str | None:
        try:
            return self.pinned()["version"]
        except Exception:
            return None

    def home(self) -> Path:
        return self.install_root / str(self.version)

    def _run(self, coroutine, timeout):
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result(timeout=timeout)

    def _install(self, home: Path, fill) -> None:
        """Fill a sibling directory, then publish it whole, so an interrupted install leaves nothing usable."""
        if (home / ".installed").is_file():
            return
        self.installed_now = True
        print(f"installing {self.server_name} {self.version} into {home} (first use)", flush=True)
        partial = home.with_name(f".{home.name}.partial")
        shutil.rmtree(partial, ignore_errors=True)
        partial.mkdir(parents=True)
        fill(partial)
        (partial / ".installed").write_text(self.version or "", encoding="utf-8")
        shutil.rmtree(home, ignore_errors=True)
        os.replace(partial, home)

    def workspace_root(self) -> Path:
        """The folder the server opens as its workspace: the project, unless the engine describes one elsewhere."""
        return self.project_root

    def initialize_params(self) -> dict:
        folder = self.workspace_root()
        uri = folder.as_uri()
        return {
            "processId": os.getpid(), "rootPath": str(folder), "rootUri": uri,
            "workspaceFolders": [{"uri": uri, "name": folder.name}],
            "capabilities": {
                "general": {"positionEncodings": ["utf-16"]},
                "workspace": {"configuration": True, "workspaceFolders": True,
                              "didChangeConfiguration": {"dynamicRegistration": True}},
                "textDocument": {"synchronization": {"dynamicRegistration": True, "didSave": False},
                                 "definition": {"dynamicRegistration": True, "linkSupport": True}},
                "window": {"workDoneProgress": True},
            },
            "initializationOptions": self.initialization_options(),
        }

    def probe(self) -> tuple[bool, str]:
        try:
            from multilspy.lsp_protocol_handler.server import LanguageServerHandler, ProcessLaunchInfo
        except ImportError as error:
            self.install = "install uv, which gives the pass multilspy"
            return False, f"multilspy is not installed: {error}"
        if self.version is None:
            return False, f"multilspy pins no {self.server_name} release"
        home = self.home()
        try:
            ready, reason = self.prepare(home)
        except Exception as error:
            shutil.rmtree(home.with_name(f".{home.name}.partial"), ignore_errors=True)
            return False, f"could not install {self.server_name}: {type(error).__name__}: {error}"
        if not ready:
            return False, reason
        command, environment = self.command(home)
        self.handler = LanguageServerHandler(ProcessLaunchInfo(cmd=command, env=environment,
                                                               cwd=str(self.project_root)),
                                             start_independent_lsp_process=False)

        async def answer_none(_params):
            return None

        def section(path):
            value = self.settings()
            for key in filter(None, (path or "").split(".")):
                value = value.get(key) if isinstance(value, dict) else None
            return value

        async def configuration(params):
            return [section(item.get("section")) for item in params.get("items", ())]

        async def ignore(_params):
            return None

        for method in ("client/registerCapability", "client/unregisterCapability", "window/workDoneProgress/create",
                       "workspace/executeClientCommand", "window/showMessageRequest"):
            self.handler.on_request(method, answer_none)
        self.handler.on_request("workspace/configuration", configuration)
        for method in ("$/progress", "textDocument/publishDiagnostics", "window/logMessage", "window/showMessage",
                       "telemetry/event", "language/status", "language/progressReport",
                       "language/eventNotification", "language/actionableNotification"):
            self.handler.on_notification(method, ignore)
        for method, callback in self.notifications().items():
            self.handler.on_notification(method, callback)
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

        async def start():
            await self.handler.start()
            response = await self.handler.send.initialize(self.initialize_params())
            self.encoding = ((response or {}).get("capabilities") or {}).get("positionEncoding") or "utf-16"
            self.handler.notify.initialized({})
            if self.settings():
                self.handler.notify.workspace_did_change_configuration({"settings": self.settings()})
            await self.wait_ready()

        try:
            self._run(start(), LSP_START_TIMEOUT)
            probe = self.readiness_probe()
            if probe is not None:
                name, text, line, character = probe
                uri = (self.workspace_root() / name).as_uri()
                self._open(uri, self.language_ids.get(Path(name).suffix, self.name), text)
                # A server that indexes after starting answers once its index is usable.
                deadline = time.monotonic() + LSP_START_TIMEOUT
                answer = self._ask(uri, line, character)
                while not any(row == 0 for _uri, row, _units in answer) and time.monotonic() < deadline:
                    time.sleep(2)
                    answer = self._ask(uri, line, character)
                self._close(uri)
                if not any(row == 0 for _uri, row, _units in answer):
                    return False, f"{self.server_name} answered no definition for its readiness probe"
        except Exception as error:
            return False, f"{self.server_name} did not start: {type(error).__name__}: {error}"
        return True, ""

    def _open(self, uri: str, language: str, text: str) -> None:
        async def notify():
            self.handler.notify.did_open_text_document(
                {"textDocument": {"uri": uri, "languageId": language, "version": 0, "text": text}})
        self._run(notify(), LSP_REQUEST_TIMEOUT)
        self.open[uri] = None
        while len(self.open) > LSP_OPEN_DOCUMENTS:
            self._close(next(iter(self.open)))

    def _close(self, uri: str) -> None:
        async def notify():
            self.handler.notify.did_close_text_document({"textDocument": {"uri": uri}})
        self._run(notify(), LSP_REQUEST_TIMEOUT)
        self.open.pop(uri, None)

    def _ask(self, uri: str, line: int, character: int, method: str = "definition") -> list[tuple[str, int, int]]:
        process = getattr(self.handler, "process", None)
        if process is not None and process.returncode is not None:
            raise EngineFailure(f"{self.server_name} exited with code {process.returncode}")
        try:
            response = self._run(getattr(self.handler.send, method)(
                {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}}),
                LSP_REQUEST_TIMEOUT)
        except TimeoutError:
            if method != "definition":
                raise  # a slow follow-up question costs its answer, never the pass
            self.timeouts += 1
            if self.timeouts >= 3:
                raise EngineFailure(f"{self.server_name} timed out three times in a row") from None
            raise
        self.timeouts = 0
        if isinstance(response, dict):
            response = [response]
        found = []
        for item in response or ():
            target = item.get("targetUri") or item.get("uri")
            area = item.get("targetSelectionRange") or item.get("targetRange") or item.get("range")
            if target and area:
                found.append((target, area["start"]["line"], area["start"]["character"]))
        return found

    def served_text(self, path: Path) -> tuple[Path, str]:
        """The document the server is given for a source file: the file itself, line endings included.

        A server that reads a closed file from disk and an open one from this text must
        see the same characters, or every CRLF line shifts its answers by one more.
        """
        with path.open(encoding="utf-8", newline="") as handle:
            return path, handle.read()

    def _document(self, path: Path) -> tuple[str, list[str]]:
        if path not in self.served:
            served, text = self.served_text(path)
            if served.resolve() != path:
                # Answers come back resolved: a link inside the served path leads to the real file.
                self.virtual[served.resolve()] = path
            self.served[path] = (served.as_uri(), text.split("\n"))
        uri, lines = self.served[path]
        if uri not in self.open:
            language = self.language_ids.get(PurePosixPath(uri).suffix.lower(), self.name)
            self._open(uri, language, "\n".join(lines))
        return uri, lines

    def _to_server(self, line: str, column: int) -> int | None:
        if self.encoding == "utf-8":
            return column if byte_to_char(line, column) is not None else None
        if self.encoding == "utf-32":
            return byte_to_char(line, column)
        return byte_to_utf16(line, column)

    def _from_server(self, line: str, units: int) -> int | None:
        if self.encoding == "utf-8":
            return units if byte_to_char(line, units) is not None else None
        if self.encoding == "utf-32":
            return char_to_byte(line, units) if 0 <= units <= len(line) else None
        return utf16_to_byte(line, units)

    def definitions(self, path: Path, line: int, column: int) -> list[Location]:
        """Where the callee at a UTF-8 byte column is declared."""
        return self._locations(path, line, column, "definition")

    def implementations(self, path: Path, line: int, column: int) -> list[Location]:
        """Where it is implemented: asked when its declaration is a contract or a value."""
        return self._locations(path, line, column, "implementation")

    def _locations(self, path: Path, line: int, column: int, method: str) -> list[Location]:
        """Ask at a UTF-8 byte column, converted to the negotiated units of the served text."""
        from urllib.parse import unquote, urlparse
        from urllib.request import url2pathname
        path = Path(path).resolve()
        uri, lines = self._document(path)
        units = self._to_server(lines[line - 1], column) if 1 <= line <= len(lines) else None
        if units is None:
            raise ValueError(f"no character starts at byte {column} of {path}:{line}")
        found = []
        for target_uri, row, start in self._ask(uri, line - 1, units, method):
            if not target_uri.startswith("file:"):
                # A class file or a library the server reads from an archive: external.
                found.append(Location(None, None, None))
                continue
            target = Path(url2pathname(unquote(urlparse(target_uri).path))).resolve()
            target = self.virtual.get(target, target)
            if self.workspace_root() != self.project_root and target.is_relative_to(self.workspace_root()):
                target = self.project_root / target.relative_to(self.workspace_root())
            if target in self.served:
                served_lines = self.served[target][1]
                name_line = served_lines[row] if 0 <= row < len(served_lines) else None
            else:
                name_line = self.lines.get(target, row + 1) if target.is_relative_to(self.project_root) else None
            found.append(Location(target, row + 1, self._from_server(name_line, start) if name_line is not None else None))
        return found

    def close(self) -> None:
        if self.handler is not None and self.loop is not None:
            async def stop():
                await self.handler.shutdown()
                await self.handler.stop()
            try:
                self._run(stop(), LSP_REQUEST_TIMEOUT)
            except Exception:
                pass
            self.handler = None
        if self.loop is not None:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop = None
        self.cleanup()

    def identity(self) -> str:
        return f"{self.server_name}@{self.version}"

    def context(self) -> str | None:
        return None if self.version is None else self.identity()

    def report(self) -> dict:
        return {"server": self.identity(), "install_dir": self.home().as_posix() if self.version else None,
                "installed_now": self.installed_now, "documents": len(self.served),
                "position_encoding": self.encoding}


def _multilspy_pins(server: str) -> dict:
    """multilspy's runtime dependency file for one of its servers."""
    spec = importlib.util.find_spec("multilspy")
    if spec is None or not spec.origin:
        raise ImportError("multilspy")
    path = Path(spec.origin).parent / "language_servers" / server / "runtime_dependencies.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _platform() -> str:
    """The platform key multilspy uses in its pins: `win-x64`, `linux-arm64`, `osx-x64` and so on."""
    import platform
    system = {"Windows": "win", "Linux": "linux", "Darwin": "osx"}.get(platform.system(), platform.system().lower())
    machine = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x64"
    return f"{system}-{machine}"


def npm_manifests(root: Path) -> list[Path]:
    """The files that decide a JavaScript project's packages: root manifest, lockfile, workspace manifests."""
    root = Path(root)
    package = root / "package.json"
    if not package.is_file():
        return []
    found = [package, *[root / name for name in ("package-lock.json", "npm-shrinkwrap.json") if (root / name).is_file()]]
    try:
        workspaces = json.loads(package.read_text(encoding="utf-8")).get("workspaces") or []
    except (OSError, ValueError):
        workspaces = []
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages") or []
    for pattern in workspaces if isinstance(workspaces, list) else []:
        for directory in root.glob(str(pattern)):
            manifest = directory / "package.json"
            if manifest.is_file() and "node_modules" not in manifest.relative_to(root).parts:
                found.append(manifest)
    return sorted(set(found))


def npm_key(root: Path) -> str | None:
    manifests = npm_manifests(root)
    if not manifests:
        return None
    # The second field changes when the installation itself changes (type packages added).
    digest = hashlib.sha256(b"npm-install\0types-1\0")
    for manifest in manifests:
        digest.update(manifest.relative_to(root).as_posix().encode("utf-8") + b"\0" + manifest.read_bytes() + b"\0")
    return digest.hexdigest()[:16]


def _declares_types(package: Path) -> bool:
    """Whether an installed package carries its own type declarations."""
    try:
        data = json.loads((package / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if data.get("types") or data.get("typings") or "types" in json.dumps(data.get("exports") or {}):
        return True
    return (package / "index.d.ts").is_file()


def missing_type_packages(directory: Path) -> list[str]:
    """`@types/...` names for the declared packages installed without their own types.

    A JavaScript project rarely declares them, and without them the engine cannot
    tell what `res.send` or `request(app).get` is: the call stays unanswered
    instead of external.
    """
    try:
        data = json.loads((directory / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    declared = set()
    for table in ("dependencies", "devDependencies", "optionalDependencies"):
        if isinstance(data.get(table), dict):
            declared |= set(data[table])
    wanted = []
    for name in sorted(declared):
        if name.startswith("@types/"):
            continue
        typed = "@types/" + name.lstrip("@").replace("/", "__")
        installed = directory / "node_modules" / name
        if typed in declared or not installed.is_dir() or _declares_types(installed):
            continue
        if not (directory / "node_modules" / typed).is_dir():
            wanted.append(typed)
    return wanted


def _install_type_packages(npm: str, directory: Path) -> int:
    """Install the missing type packages beside the others, without scripts; one that does
    not exist must not cost the rest. Returns how many were installed."""
    wanted = missing_type_packages(directory)
    if not wanted:
        return 0
    base = [npm, "install", "--no-save", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error",
            "--package-lock=false"]

    def run(names, timeout):
        return subprocess.run([*base, *names], cwd=directory, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, timeout=timeout, shell=os.name == "nt").returncode == 0

    if run(wanted, 900):
        return len(wanted)
    return sum(1 for name in wanted if run([name], 300))


def _without_local_packages(manifest: Path) -> str | None:
    """A package.json without the packages it takes from a local path, or None when it has none.

    `file:`, `link:`, `workspace:` and bare paths point at the project's own code, which
    the manifest-only copy does not hold: npm would fail on every other package too.
    """
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    dropped = False
    for table in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        packages = data.get(table)
        if not isinstance(packages, dict):
            continue
        for name, spec in list(packages.items()):
            if isinstance(spec, str) and spec.startswith(("file:", "link:", "workspace:", ".", "/", "~/")):
                del packages[name]
                dropped = True
    return json.dumps(data, indent=2) + "\n" if dropped else None


def package_directories(root: Path, limit: int = 8) -> list[Path]:
    """Directories of the project with their own package.json and no installed packages, nearest first.

    The members of a workspace are served by its root, and a directory under an
    installed `node_modules` by that installation.
    """
    root = Path(root).resolve()
    served = {manifest.parent.resolve() for manifest in npm_manifests(root)} - {root}
    found = []
    for current, directories, files in os.walk(root):
        here = Path(current)
        directories[:] = sorted(name for name in directories if name != "node_modules" and not name.startswith("."))
        if "package.json" in files and here.resolve() not in served and not (here / "node_modules").is_dir():
            found.append(here)
            served |= {manifest.parent.resolve() for manifest in npm_manifests(here)}
    return sorted(found, key=lambda path: (len(path.relative_to(root).parts), path.as_posix()))[:limit]


def npm_modules(root: Path) -> Path | None:
    """The project's packages installed once into the shared directory, without running any package script.

    Only the manifests are copied there, so npm never sees the project's code; the
    lockfile is honoured when there is one. Every project with the same manifests
    shares the installation, and npm's own cache spares repeated downloads. None
    when the project has no package.json, npm is missing or the install fails.
    """
    root = Path(root).resolve()
    key, npm = npm_key(root), shutil.which("npm")
    if key is None or npm is None:
        return None
    destination = shared_cache_dir() / "npm" / key
    if (destination / "daodan-modules.json").is_file():
        return destination / "node_modules"
    print(f"installing the project's JavaScript packages into {destination} (first use)", flush=True)
    partial = destination.with_name(f".{key}.partial")
    shutil.rmtree(partial, ignore_errors=True)
    manifests = npm_manifests(root)
    local = False
    for manifest in manifests:
        target = partial / manifest.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        text = _without_local_packages(manifest) if manifest.name == "package.json" else None
        if text is None:
            shutil.copyfile(manifest, target)
        else:
            target.write_text(text, encoding="utf-8")
            local = True
    # A lockfile that still names the local packages cannot be honoured to the letter.
    locked = not local and any(manifest.name in ("package-lock.json", "npm-shrinkwrap.json") for manifest in manifests)
    command = [npm, "ci" if locked else "install", "--ignore-scripts", "--no-audit", "--no-fund",
               "--loglevel=error", *([] if locked else ["--package-lock=false"])]
    completed = subprocess.run(command, cwd=partial, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                               timeout=1800, shell=os.name == "nt")
    if completed.returncode != 0 and locked:
        # A lockfile out of step with its manifest still leaves the manifest to install from.
        command = [npm, "install", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error"]
        completed = subprocess.run(command, cwd=partial, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                   timeout=1800, shell=os.name == "nt")
    if completed.returncode != 0 or not (partial / "node_modules").is_dir():
        print(f"the project's JavaScript packages were not installed: {(completed.stderr or '')[-300:]}", flush=True)
        shutil.rmtree(partial, ignore_errors=True)
        return None
    try:
        typed = _install_type_packages(npm, partial)
    except (OSError, subprocess.SubprocessError):
        typed = 0
    if typed:
        print(f"installed {typed} type packages for declared JavaScript packages without their own", flush=True)
    (partial / "daodan-modules.json").write_text(json.dumps({"manifests": [m.relative_to(root).as_posix()
                                                                           for m in manifests],
                                                             "type_packages": typed}), encoding="utf-8")
    shutil.rmtree(destination, ignore_errors=True)
    os.replace(partial, destination)
    return destination / "node_modules"


def link_directory(link: Path, target: Path) -> None:
    """A directory link: a junction on Windows, which needs no privilege, a symbolic link elsewhere."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(target, link, target_is_directory=True)


def remove_mirror(root: Path) -> None:
    """Remove a mirror's links and copies without ever entering a link, so no target file is touched."""
    root = Path(root)
    if not root.is_dir() or root.is_symlink() or os.path.isjunction(root):
        return
    for entry in root.iterdir():
        if os.path.isjunction(entry):
            os.rmdir(entry)
        elif entry.is_symlink() or entry.is_file():
            entry.unlink()
        elif entry.is_dir():
            remove_mirror(entry)
    root.rmdir()


RUST_ANALYZER_RELEASE = "2026-11-09"
# The release's own checksums, per platform key of `_platform()`: (asset, sha256).
RUST_ANALYZER_ASSETS = {
    "win-x64": ("x86_64-pc-windows-msvc.zip", "973ab11e84955a7f8e3cf01ccd98a33f3ecbd6d4a14bf59bb164aa9e831c6fef"),
    "win-arm64": ("aarch64-pc-windows-msvc.zip", "ca0770b76d3881642221d0437f7535e324f22a9499bcd00bbebeb0228617249e"),
    "linux-x64": ("x86_64-unknown-linux-gnu.gz", "8c039b25cb338b3970c731646677a4c9d4e9dd7a92c9ab9ae459c71467fbf4a9"),
    "linux-arm64": ("aarch64-unknown-linux-gnu.gz", "813ca3cec78ac6dab99c7bc9d51e63578f6d401b994ecf29cc0dcad86f9b2cd4"),
    "osx-x64": ("x86_64-apple-darwin.gz", "abf410a54e33e9f8b2d37f76dde8884db86a030d6a9cc70c0e3f87a77c084c5c"),
    "osx-arm64": ("aarch64-apple-darwin.gz", "e43a65008f8f4291320f33c0545dd577ad7623a7407b584a27155833d3722dfb"),
}
GO_VERSION = "1.27.3"
GO_ASSETS = {
    "win-x64": ("go1.27.3.windows-amd64.zip", "f26081f438319757f8a1b46d7d0b2c5ec7583d4038e485e0aa725cfde7885fff"),
    "win-arm64": ("go1.27.3.windows-arm64.zip", "c507872ff21f8a7cd3c1c217b059c6f7271a4a9d8e692810ef9dd3e1f601197c"),
    "linux-x64": ("go1.27.3.linux-amd64.tar.gz", "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40"),
    "linux-arm64": ("go1.27.3.linux-arm64.tar.gz", "a06e99309dbcbdca1a8ccd2282c3ee146e55930886e26b4f1193269587165f49"),
    "osx-x64": ("go1.27.3.darwin-amd64.tar.gz", "b6f8e931e4ab497fcde6da8ae4499a58f9d258e55c8a80824a516eae5950a750"),
    "osx-arm64": ("go1.27.3.darwin-arm64.tar.gz", "dd3908cf20959d798c1e06ebe5b72213f0505ce01373b40ce3110975a6cd99c2"),
}
GOPLS_VERSION = "v0.24.0"


def unpack(archive: Path, destination: Path) -> None:
    """Extract a zip or a gzip tarball into `destination`."""
    if archive.name.endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(destination)
    else:
        import tarfile
        with tarfile.open(archive) as bundle:
            bundle.extractall(destination, filter="data")


def executable_name(name: str) -> str:
    return name + (".exe" if os.name == "nt" else "")


def go_toolchain() -> Path:
    """The Go release Daodan pins, unpacked once into the shared directory: its GOROOT."""
    home = shared_engine_dir("go") / GO_VERSION
    root = home / "go"
    if (root / "bin" / executable_name("go")).is_file():
        return root
    asset, digest = GO_ASSETS[_platform()]
    print(f"installing Go {GO_VERSION} into {home} (first use)", flush=True)
    partial = home.with_name(f".{GO_VERSION}.partial")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    archive = download(f"https://go.dev/dl/{asset}", partial / asset, sha256=digest)
    unpack(archive, partial)
    archive.unlink()
    shutil.rmtree(home, ignore_errors=True)
    os.replace(partial, home)
    return root


RUST_VERSION = "1.99.1"
RUST_TARGETS = {"win-x64": "x86_64-pc-windows-msvc", "win-arm64": "aarch64-pc-windows-msvc",
                "linux-x64": "x86_64-unknown-linux-gnu", "linux-arm64": "aarch64-unknown-linux-gnu",
                "osx-x64": "x86_64-apple-darwin", "osx-arm64": "aarch64-apple-darwin"}


def rust_toolchain() -> Path | None:
    """The directory whose `bin` holds cargo and rustc and whose sysroot holds the standard library's sources.

    The toolchain on PATH when it is complete; otherwise cargo, rustc and rust-src
    at the pinned release, downloaded from static.rust-lang.org into the shared
    directory and checked against the sha256 of the release manifest. Without the
    standard library's sources every call into `std` stays unresolved (semver:
    88.8% instead of 97.7%). None when the download fails.
    """
    cargo, rustc = shutil.which("cargo"), shutil.which("rustc")
    if cargo and rustc:
        try:
            sysroot = subprocess.run([rustc, "--print", "sysroot"], capture_output=True, text=True, timeout=60,
                                     stdin=subprocess.DEVNULL).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            sysroot = ""
        if sysroot and (Path(sysroot) / "lib" / "rustlib" / "src" / "rust" / "library").is_dir():
            return Path(cargo).parent.parent
    home = shared_engine_dir("rust") / RUST_VERSION
    if (home / ".installed").is_file():
        return home
    import tomllib
    import lzma
    import tarfile
    print(f"installing Rust {RUST_VERSION} (cargo, rustc, rust-src) into {home} (first use)", flush=True)
    partial = home.with_name(f".{RUST_VERSION}.partial")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    try:
        with open_url(f"https://static.rust-lang.org/dist/channel-rust-{RUST_VERSION}.toml",
                      timeout=120) as response:
            packages = tomllib.loads(response.read().decode("utf-8"))["pkg"]
        target = RUST_TARGETS[_platform()]
        for component in ("rustc", "cargo", "rust-src"):
            entry = packages[component]["target"]
            entry = entry.get(target) or entry["*"]
            archive = download(entry["xz_url"], partial / f"{component}.tar.xz", sha256=entry["xz_hash"])
            unpacked = partial / f"unpack-{component}"
            with tarfile.open(archive, "r:xz") as bundle:
                bundle.extractall(unpacked, filter="data")
            archive.unlink()
            top = next(child for child in unpacked.iterdir() if child.is_dir())
            shutil.copytree(top / component, partial, dirs_exist_ok=True)
            shutil.rmtree(unpacked, ignore_errors=True)
        (partial / ".installed").write_text(RUST_VERSION, encoding="utf-8")
        shutil.rmtree(home, ignore_errors=True)
        os.replace(partial, home)
    except Exception as error:
        print(f"the Rust toolchain was not installed: {type(error).__name__}: {error}", flush=True)
        shutil.rmtree(partial, ignore_errors=True)
        return None
    return home


class MirroredEngine(LspEngine):
    """An engine whose server works in a mirror of the project, so what its tools write never lands in the project.

    A package manager asked to read the project's crates or modules may write a
    lock file or a checksum file beside the manifest. The mirror holds a link per
    top-level directory and a copy of each top-level file, so such a write lands in
    the copy; answers are mapped back to the project's files. Removing the mirror
    never enters a link.
    """

    mirror: Path | None = None
    mirror_skip = (".git",)

    def build_mirror(self, links: dict | None = None) -> Path:
        mirror = Path(tempfile.mkdtemp(prefix=f"daodan-{self.name}-")) / self.project_root.name
        mirror.mkdir()
        # A directory that receives a link is a real directory of the mirror, one link per child.
        real = {parent.as_posix() for name in links or {} for parent in PurePosixPath(name).parents} - {"."}

        def fill(source: Path, target: Path, relative: PurePosixPath) -> None:
            for entry in source.iterdir():
                if entry.name in self.mirror_skip:
                    continue
                if entry.is_dir():
                    if (relative / entry.name).as_posix() in real:
                        (target / entry.name).mkdir()
                        fill(entry, target / entry.name, relative / entry.name)
                    else:
                        link_directory(target / entry.name, entry)
                elif entry.is_file():
                    shutil.copyfile(entry, target / entry.name)

        fill(self.project_root, mirror, PurePosixPath(""))
        for name, target in (links or {}).items():
            link_directory(mirror / name, target)
        return mirror

    def workspace_root(self) -> Path:
        return self.mirror or self.project_root

    def served_text(self, path: Path) -> tuple[Path, str]:
        with path.open(encoding="utf-8", newline="") as handle:
            text = handle.read()
        return self.workspace_root() / path.relative_to(self.project_root), text

    def cleanup(self) -> None:
        if self.mirror is not None:
            remove_mirror(self.mirror)
            self.mirror.parent.rmdir()
            self.mirror = None


class RustEngine(MirroredEngine):
    """Rust through rust-analyzer, from the release Daodan pins.

    The project is read by `cargo metadata`, which needs cargo (and the Rust sources
    of the standard library for calls into `std`). Build scripts and procedural macros
    stay off, so no project code runs; what a macro generates is not seen. The server
    works in a mirror of the project (`MirroredEngine`) with its target directory in
    a temporary folder, so a missing `Cargo.lock` is written in the mirror and never
    in the project.
    """

    name = "rust"
    server_name = "rust-analyzer"
    languages = ("rust",)
    language_ids = {".rs": "rust"}
    source_languages = ("rust",)
    quiescent_seconds = LSP_START_TIMEOUT - 10

    def __init__(self, project_root: Path, install_dir: Path | None = None):
        super().__init__(project_root, install_dir)
        self.target_dir: Path | None = None
        self.toolchain: Path | None = None
        self.status: dict = {}
        self.quiet = threading.Event()

    def pinned(self) -> dict:
        return {"version": RUST_ANALYZER_RELEASE}

    def prepare(self, home: Path) -> tuple[bool, str]:
        self.toolchain = rust_toolchain()
        if self.toolchain is None:
            self.install = "check the network: Daodan downloads cargo, rustc and rust-src from static.rust-lang.org"
            return False, "no Rust toolchain could be installed"

        def fill(partial):
            asset, digest = RUST_ANALYZER_ASSETS[_platform()]
            archive = download("https://github.com/rust-lang/rust-analyzer/releases/download/"
                               f"{RUST_ANALYZER_RELEASE}/rust-analyzer-{asset}", partial / asset, sha256=digest)
            binary = partial / executable_name("rust-analyzer")
            if archive.suffix == ".zip":
                unpack(archive, partial)
            else:
                import gzip
                with gzip.open(archive) as source, binary.open("wb") as target:
                    shutil.copyfileobj(source, target)
                binary.chmod(0o755)
            archive.unlink()

        self._install(home, fill)
        return True, ""

    def command(self, home: Path) -> tuple[list[str], dict]:
        # Crates the project depends on land in the shared directory, not in the user's cargo home.
        return [str(home / executable_name("rust-analyzer"))], {
            "PATH": str(self.toolchain / "bin") + os.pathsep + os.environ.get("PATH", ""),
            "CARGO_HOME": str(shared_cache_dir() / "cargo"), "CARGO_TARGET_DIR": str(self.target_dir)}

    def initialization_options(self) -> dict:
        return {"cargo": {"buildScripts": {"enable": False}, "features": "all", "targetDir": str(self.target_dir)},
                "procMacro": {"enable": False}, "checkOnSave": False, "cachePriming": {"enable": False},
                "numThreads": ENGINE_THREADS, "diagnostics": {"enable": False}}

    def initialize_params(self) -> dict:
        params = super().initialize_params()
        params["capabilities"]["experimental"] = {"serverStatusNotification": True}
        return params

    def notifications(self) -> dict:
        async def server_status(params):
            self.status = params or {}
            if self.status.get("quiescent"):
                self.quiet.set()
            else:
                self.quiet.clear()
        return {"experimental/serverStatus": server_status}

    async def wait_ready(self) -> None:
        deadline = time.monotonic() + self.quiescent_seconds
        while time.monotonic() < deadline:
            if self.quiet.is_set():
                await asyncio.sleep(2)
                if self.quiet.is_set():
                    return
            await asyncio.sleep(1)

    def readiness_probe(self):
        # A virtual file belongs to no crate; the quiescent status is the readiness signal.
        return None

    def probe(self) -> tuple[bool, str]:
        self.target_dir = Path(tempfile.mkdtemp(prefix="daodan-rust-target-"))
        self.mirror = self.build_mirror()
        return super().probe()

    def cleanup(self) -> None:
        super().cleanup()
        if self.target_dir is not None:
            shutil.rmtree(self.target_dir, ignore_errors=True)
            self.target_dir = None

    def context(self) -> str | None:
        """The server release, the compiler and the manifests, which decide what is external."""
        if self.version is None:
            return None
        manifests = hashlib.sha256()
        for path in sorted(self.project_root.rglob("Cargo.*")):
            if path.is_file() and "target" not in path.relative_to(self.project_root).parts:
                manifests.update(path.relative_to(self.project_root).as_posix().encode() + b"\0" + path.read_bytes())
        return f"{self.identity()}|cargo={manifests.hexdigest()[:16]}"

    def report(self) -> dict:
        return {**super().report(), "status": self.status.get("health"), "message": self.status.get("message")}


class GoEngine(MirroredEngine):
    """Go through gopls, built once from the release Daodan pins with the Go toolchain Daodan pins.

    gopls reads the project through the `go` command, so the toolchain is part of the
    engine. Modules are fetched into the shared directory by `go mod download` in the
    mirror, so a missing checksum is written in the mirror and never in the project;
    no project code runs, since `go list` and the type checker only read it.
    """

    name = "go"
    server_name = "gopls"
    languages = ("go",)
    language_ids = {".go": "go"}
    source_languages = ("go",)

    def pinned(self) -> dict:
        return {"version": GOPLS_VERSION}

    def go_environment(self) -> dict:
        root = go_toolchain()
        cache = shared_cache_dir() / "go"
        return {"GOROOT": str(root), "GOPATH": str(cache / "path"), "GOCACHE": str(cache / "build"),
                "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=readonly", "GOTELEMETRY": "off",
                "PATH": str(root / "bin") + os.pathsep + os.environ.get("PATH", "")}

    def prepare(self, home: Path) -> tuple[bool, str]:
        environment = self.go_environment()

        def fill(partial):
            scratch = Path(tempfile.mkdtemp(prefix="daodan-gopls-"))
            try:
                build = {**os.environ, **environment, "GOBIN": str(partial), "GOPATH": str(scratch / "path"),
                         "GOCACHE": str(scratch / "cache"), "GOFLAGS": ""}
                subprocess.run([str(go_toolchain() / "bin" / executable_name("go")), "install",
                                f"golang.org/x/tools/gopls@{GOPLS_VERSION}"], check=True, env=build,
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=1800)
            finally:
                # The module and build caches of gopls's own sources are not needed again; Go makes them read-only.
                shutil.rmtree(scratch, onexc=lambda function, path, _error: (os.chmod(path, 0o700), function(path)))

        self._install(home, fill)
        return True, ""

    def command(self, home: Path) -> tuple[list[str], dict]:
        return [str(home / executable_name("gopls")), "serve"], self.go_environment()

    def settings(self) -> dict:
        return {"gopls": {"usePlaceholders": False, "staticcheck": False, "analyses": {}, "diagnosticsDelay": "1h",
                          "build": {"directoryFilters": ["-node_modules", "-vendor"]}}}

    def readiness_probe(self):
        # A virtual file belongs to no package; gopls loads the workspace on its first request.
        return None

    def probe(self) -> tuple[bool, str]:
        self.mirror = self.build_mirror()
        environment = {**os.environ, **self.go_environment()}
        if (self.mirror / "go.mod").is_file():
            subprocess.run([str(go_toolchain() / "bin" / executable_name("go")), "mod", "download"], cwd=self.mirror,
                           env=environment, stdin=subprocess.DEVNULL, capture_output=True, timeout=1800)
        return super().probe()

    def context(self) -> str | None:
        if self.version is None:
            return None
        modules = hashlib.sha256()
        for path in sorted(self.project_root.rglob("go.*")):
            if path.is_file() and path.name in ("go.mod", "go.sum", "go.work"):
                modules.update(path.relative_to(self.project_root).as_posix().encode() + b"\0" + path.read_bytes())
        return f"{self.identity()}|go={GO_VERSION}|{modules.hexdigest()[:16]}"


class TypeScriptEngine(MirroredEngine):
    """TypeScript and JavaScript through typescript-language-server.

    The server needs no build and no installed dependencies: a file outside every
    tsconfig gets an inferred project, which is how tests and scripts are covered
    at all. Measured against scip-typescript, which indexes only the files a
    tsconfig includes and stops at a tsconfig extending an uninstalled package,
    this engine confirmed more edges on both a TypeScript and a JavaScript project.
    Vue and Svelte files are served as a virtual `.ts` or `.js` document holding
    only their script blocks at the snapshot's byte offsets, so a position means the
    same in both. Automatic type acquisition is off, so the server never downloads.

    Without the project's packages a library call is unresolved instead of external
    (ky: 59.1% instead of 90.9%). A project without `node_modules` gets its packages
    installed once into the shared directory (`npm_modules`), and the server opens a
    mirror of the project in a temporary directory: a link per top-level directory,
    a copy of each top-level file and `node_modules` linked to the shared install,
    since TypeScript looks for packages only in the folders above a file.
    """

    name = "typescript"
    server_name = "typescript-language-server"
    languages = ("typescript", "javascript", "vue", "svelte")
    language_ids = {".ts": "typescript", ".mts": "typescript", ".cts": "typescript", ".tsx": "typescriptreact",
                    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".jsx": "javascriptreact"}

    def pinned(self) -> dict:
        packages = [dependency["command"].split()[-1]
                    for dependency in _multilspy_pins("typescript_language_server")["runtimeDependencies"]]
        server = next(item for item in packages if item.startswith("typescript-language-server@"))
        return {"version": server.rsplit("@", 1)[1], "packages": packages}

    def prepare(self, home: Path) -> tuple[bool, str]:
        node, npm = shutil.which("node"), shutil.which("npm")
        if not node or not npm:
            self.install = "install Node.js 18 or later with npm (https://nodejs.org)"
            return False, "node and npm are needed to run typescript-language-server"

        def fill(partial):
            subprocess.run([npm, "install", "--prefix", str(partial), "--no-audit", "--no-fund", "--no-save",
                            *self.pinned()["packages"]], check=True, stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        self._install(home, fill)
        return True, ""

    def command(self, home: Path) -> tuple[list[str], dict]:
        # The npm shim is a shell script on Windows; node runs the entry point itself.
        cli = home / "node_modules" / "typescript-language-server" / "lib" / "cli.mjs"
        return [shutil.which("node"), str(cli), "--stdio"], {"UV_THREADPOOL_SIZE": str(ENGINE_THREADS)}

    def initialization_options(self) -> dict:
        return {"disableAutomaticTypingAcquisition": True, "maxTsServerMemory": SERVER_MEMORY_MB,
                "tsserver": {"useSyntaxServer": "never"}}

    def readiness_probe(self):
        return "__daodan_engine_probe__.ts", "function probe() {}\nprobe();\n", 1, 0

    mirror_skip = (".git", "node_modules")

    def probe(self) -> tuple[bool, str]:
        self.mirror = None
        links = {}
        for directory in package_directories(self.project_root):
            try:
                modules = npm_modules(directory)
            except (OSError, subprocess.SubprocessError) as error:
                print(f"the project's JavaScript packages were not installed: {error}", flush=True)
                modules = None
            if modules is not None:
                links[(PurePosixPath(directory.relative_to(self.project_root).as_posix()) / "node_modules").as_posix()] = modules
        if links:
            self.mirror = self.build_mirror(links)
        return super().probe()

    def served_text(self, path: Path) -> tuple[Path, str]:
        served, text = super().served_text(path)
        if path.suffix.lower() not in (".vue", ".svelte"):
            return served, text
        from languages.sfc import mask_non_script
        text, typed, _has_script = mask_non_script(text)
        return served.with_name(served.name + (".ts" if typed else ".js")), text

    def context(self) -> str | None:
        """The server version and the project's packages, which decide what is external."""
        if self.version is None:
            return None
        modules = self.project_root / "node_modules"
        packages = f"node_modules={modules.stat().st_mtime_ns}" if modules.is_dir() else \
            "npm=" + ",".join(str(npm_key(directory)) for directory in package_directories(self.project_root))
        return f"{self.identity()}|{packages}"

    def report(self) -> dict:
        return {**super().report(), "max_server_memory_mb": SERVER_MEMORY_MB,
                "packages": "project" if (self.project_root / "node_modules").is_dir() else
                "shared" if self.mirror else None}


class JavaEngine(LspEngine):
    """Java through Eclipse JDT LS, with the Java runtime its release bundles.

    The server never sees the build: its workspace is an Eclipse project that Daodan
    writes in a temporary directory, with the project's package roots as linked
    source folders and its libraries, resolved into the shared store by
    `jvm_classpath`, as jars. JDT LS refuses an invisible project beside a pom.xml
    or a Gradle build, and an offline Maven import was measured to answer no
    position, so neither is used; automatic building and both imports stay off.
    Nothing is compiled and nothing is written into the project. Memory and
    processors are capped for the JVM; the runtime library's index is shared.
    """

    name = "java"
    server_name = "eclipse-jdtls"
    languages = ("java",)
    source_languages = ("java",)
    language_ids = {".java": "java"}

    def __init__(self, project_root: Path, install_dir: Path | None = None):
        super().__init__(project_root, install_dir)
        self.workspace = None
        self.ready_event = None
        self.service_ready = False
        self.jre_home = None
        self.sources: list[Path] = []
        self.libraries: list[Path] = []
        self.source_roots: list[Path] = []

    def workspace_root(self) -> Path:
        return self.workspace / "project" if self.workspace is not None else self.project_root

    def describe_project(self) -> None:
        """Write the Eclipse project the server opens: linked package roots and library jars."""
        from xml.sax.saxutils import quoteattr
        sources = self.sources or sorted(self.project_root.rglob("*.java"))
        self.source_roots = java_source_roots(sources)
        try:
            self.libraries = jvm_classpath(self.project_root)
        except Exception as error:
            # Without its libraries the engine still answers for the project's own code.
            print(f"the project's libraries were not resolved: {type(error).__name__}: {error}", flush=True)
            self.libraries = []
        project = self.workspace / "project"
        project.mkdir()
        links = "".join(f"<link><name>source{index}</name><type>2</type><location>{path.as_posix()}</location></link>"
                        for index, path in enumerate(self.source_roots))
        (project / ".project").write_text(
            "<?xml version='1.0' encoding='UTF-8'?><projectDescription><name>daodan-sources</name><comment/>"
            "<projects/><buildSpec/><natures><nature>org.eclipse.jdt.core.javanature</nature></natures>"
            f"<linkedResources>{links}</linkedResources></projectDescription>", encoding="utf-8")
        entries = "".join(f"<classpathentry kind='src' path='source{index}'/>"
                          for index in range(len(self.source_roots)))
        entries += "".join(f"<classpathentry kind='lib' path={quoteattr(path.as_posix())}/>" for path in self.libraries)
        (project / ".classpath").write_text(
            "<?xml version='1.0' encoding='UTF-8'?><classpath>" + entries
            + "<classpathentry kind='con' path='org.eclipse.jdt.launching.JRE_CONTAINER'/>"
            "<classpathentry kind='output' path='bin'/></classpath>", encoding="utf-8")


    def pinned(self) -> dict:
        entry = _multilspy_pins("eclipse_jdtls")["vscode-java"][_platform()]
        version = entry["url"].rsplit("/", 2)[-2].lstrip("v")
        return {"version": version, **entry}

    def prepare(self, home: Path) -> tuple[bool, str]:
        pins = self.pinned()

        def fill(partial):
            from multilspy.multilspy_logger import MultilspyLogger
            from multilspy.multilspy_utils import FileUtils
            FileUtils.download_and_extract_archive(MultilspyLogger(), pins["url"], str(partial), pins["archiveType"])

        self._install(home, fill)
        self.jre_home = home / pins["jre_home_path"]
        # The archive is a zip and its extraction drops the execute bit: without it the bundled runtime cannot
        # start. Restored at every use, so an install made before this line is repaired too.
        if os.name != "nt":
            for binary in (*(self.jre_home / "bin").glob("*"), self.jre_home / "lib" / "jspawnhelper"):
                if binary.is_file() and not os.access(binary, os.X_OK):
                    binary.chmod(0o755)
        return True, ""

    def command(self, home: Path) -> tuple[list[str], dict]:
        pins = self.pinned()
        server = home / "extension" / "server"
        launcher = next(iter(sorted(server.glob("plugins/org.eclipse.equinox.launcher_*.jar"))))
        platform = _platform()
        family = "win" if platform.startswith("win") else "mac" if platform.startswith("osx") else "linux"
        arm = "_arm" if platform.endswith("arm64") else ""
        config = server / f"config_{family}{arm}"
        if not config.is_dir():
            config = server / f"config_{family}"
        self.workspace = Path(tempfile.mkdtemp(prefix="daodan-jdtls-"))
        shutil.copytree(config, self.workspace / "config")
        # Buildship, which the server starts even with the Gradle import off, downloads the list of
        # Gradle releases unless a cache younger than a day exists. A fresh empty list keeps it local.
        versions = self.workspace / "xdg" / "tooling" / "gradle" / "versions.json"
        versions.parent.mkdir(parents=True)
        versions.write_text("[]", encoding="utf-8")
        self.describe_project()
        lombok = sorted((home / "extension" / "lombok").glob("lombok-*.jar"))
        shared_index = self.install_root / "shared-index"
        command = [str(home / pins["jre_path"]), "--add-modules=ALL-SYSTEM",
                   "--add-opens", "java.base/java.util=ALL-UNNAMED", "--add-opens", "java.base/java.lang=ALL-UNNAMED",
                   "--add-opens", "java.base/sun.nio.fs=ALL-UNNAMED",
                   "-Declipse.application=org.eclipse.jdt.ls.core.id1", "-Dosgi.bundles.defaultStartLevel=4",
                   "-Declipse.product=org.eclipse.jdt.ls.core.product",
                   "-Djava.import.generatesMetadataFilesAtProjectRoot=false", "-Dfile.encoding=utf8",
                   "-XX:+UseParallelGC", "-XX:GCTimeRatio=4", "-XX:AdaptiveSizePolicyWeight=90",
                   "-Dsun.zip.disableMemoryMapping=true", f"-Xmx{JVM_MEMORY_MB}m", "-Xms100m",
                   f"-XX:ActiveProcessorCount={ENGINE_THREADS}", "-Xlog:disable",
                   *([f"-javaagent:{lombok[-1]}"] if lombok else []),
                   f"-Djdt.core.sharedIndexLocation={shared_index}",
                   "-jar", str(launcher), "-configuration", str(self.workspace / "config"),
                   "-data", str(self.workspace / "data")]
        return command, {"syntaxserver": "false", "JAVA_HOME": str(self.jre_home),
                         "XDG_CACHE_HOME": str(self.workspace / "xdg")}

    def settings(self) -> dict:
        return {"java": {
            "autobuild": {"enabled": False}, "maxConcurrentBuilds": 1,
            # The Gradle wrapper check fetches services.gradle.org even with the import off.
            "import": {"gradle": {"enabled": False, "wrapper": {"enabled": False}}, "maven": {"enabled": False},
                       "exclusions": ["**/node_modules/**", "**/.metadata/**", "**/archetype-resources/**",
                                      "**/META-INF/maven/**"]},
            "configuration": {"updateBuildConfiguration": "disabled",
                              "runtimes": [{"name": "JavaSE-21", "path": str(self.jre_home), "default": True}]},
            "references": {"includeDecompiledSources": False},
            "signatureHelp": {"enabled": False}, "format": {"enabled": False},
        }}

    def initialization_options(self) -> dict:
        return {"bundles": [], "workspaceFolders": [self.workspace_root().as_uri()], "settings": self.settings(),
                "extendedClientCapabilities": {"classFileContentsSupport": True}}

    def notifications(self) -> dict:
        async def status(params):
            if params.get("type") == "ServiceReady":
                self.service_ready = True
                if self.ready_event is not None:
                    self.ready_event.set()
        return {"language/status": status}

    async def wait_ready(self) -> None:
        # Both callbacks run on the transport's loop, so the flag and the event cannot race.
        if not self.service_ready:
            self.ready_event = asyncio.Event()
            await self.ready_event.wait()

    def probe(self) -> tuple[bool, str]:
        self.ready_event, self.service_ready = None, False
        return super().probe()

    def cleanup(self) -> None:
        if self.workspace is not None:
            shutil.rmtree(self.workspace, ignore_errors=True)
            self.workspace = None

    def context(self) -> str | None:
        if self.version is None:
            return None
        return f"{self.identity()}|libraries={coordinates_digest(self.project_root)}"

    def report(self) -> dict:
        return {**super().report(), "max_heap_mb": JVM_MEMORY_MB, "processors": ENGINE_THREADS,
                "source_roots": [path.as_posix() for path in self.source_roots], "libraries": len(self.libraries)}


# The Kotlin Analysis API in standalone mode with the platform it runs on, as KSP publishes it on
# Maven Central, and the compiler that builds the resolver against it once.
KOTLIN_ANALYSIS = "com.google.devtools.ksp:symbol-processing-aa:2.3.13"
KOTLIN_RUNTIME = ("com.google.devtools.ksp:symbol-processing-common-deps:2.3.13",
                  "org.jetbrains.kotlin:kotlin-stdlib:2.4.21",
                  "org.jetbrains.kotlinx:kotlinx-coroutines-core-jvm:1.10.2")
KOTLIN_COMPILER = ("org.jetbrains.kotlin:kotlin-compiler-embeddable:2.4.21",
                   "org.jetbrains.kotlin:kotlin-build-tools-api:2.4.21",
                   "org.jetbrains.kotlin:kotlin-stdlib:2.4.21",
                   "org.jetbrains.kotlin:kotlin-script-runtime:2.4.21",
                   "org.jetbrains.kotlin:kotlin-reflect:1.6.10",
                   "org.jetbrains.kotlin:kotlin-daemon-embeddable:2.4.21",
                   "org.jetbrains.kotlinx:kotlinx-coroutines-core-jvm:1.8.0",
                   "org.jetbrains:annotations:13.0")
KOTLIN_OPT_INS = ("KaExperimentalApi", "KaPlatformInterface", "KaImplementationDetail", "KaIdeApi")
KOTLIN_MEMORY_MB = 1536
JAVA_MINIMUM = 17
TEMURIN_JRE = "https://api.adoptium.net/v3/binary/latest/21/ga/{os}/{arch}/jre/hotspot/normal/eclipse"


MAVEN_CENTRAL = "https://repo1.maven.org/maven2"
# Coursier resolves Maven coordinates with their transitive dependencies, without running a build.
COURSIER = {"version": "2.1.24", "sha256": "8c724dc204534353ea8263ba0af624979658f7ab62395f35b04f03ce5714f330",
            "url": "https://github.com/coursier/coursier/releases/download/v2.1.24/coursier.jar"}
BUILD_SKIP = frozenset({"node_modules", "target", "build", "out", "bin", "dist"})
GRADLE_COORDINATE = re.compile(r"""["']([A-Za-z0-9_.\-]+):([A-Za-z0-9_.\-]+):([A-Za-z0-9_.\-+\[\],()]+)["']""")
GRADLE_KOTLIN_MODULE = re.compile(r"""\bkotlin\(\s*["']([A-Za-z0-9_.\-]+)["']\s*(?:,\s*["']([^"']+)["'])?\s*\)""")
GRADLE_KOTLIN_PLUGIN = re.compile(r"""kotlin\(\s*["'](?:jvm|multiplatform|android)["']\s*\)\s*version\s*["']([^"']+)["']"""
                                  r"""|org\.jetbrains\.kotlin\.(?:jvm|multiplatform|android)["']\)?\s*version\s*["']([^"']+)["']""")


def maven_central_dir() -> Path:
    """The shared Maven-layout store: Coursier's cache of Maven Central, also where Daodan puts its own jars."""
    return shared_cache_dir() / "coursier" / "https" / "repo1.maven.org" / "maven2"


USER_AGENT = "daodan"  # Python's default agent is refused by some hosts: the Temurin API answers 403


def open_url(url: str, timeout: float):
    """A URL opened with Daodan's own agent name."""
    import urllib.request
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout)


def download(url: str, target: Path, *, sha256: str | None = None, sha1_url: str | None = None) -> Path:
    """Fetch a file into the shared directory through a partial file, verified, with three attempts."""
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".partial")
    last = None
    for attempt in range(3):
        try:
            expected = sha256
            if sha1_url:
                with open_url(sha1_url, timeout=60) as response:
                    expected = response.read().decode("ascii", "replace").split()[0].lower()
            digest = hashlib.sha1() if sha1_url else hashlib.sha256()
            with open_url(url, timeout=600) as response, partial.open("wb") as handle:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    digest.update(chunk)
                    handle.write(chunk)
            if expected and digest.hexdigest() != expected:
                raise ValueError(f"checksum mismatch for {url}")
            os.replace(partial, target)
            return target
        except (OSError, ValueError) as error:
            last = error
            partial.unlink(missing_ok=True)
            time.sleep(2 * (attempt + 1))
    raise last


def maven_artifact(coordinate: str) -> Path:
    """A Maven artifact's jar: the local Maven repository first, then the shared store, else Maven Central."""
    group, artifact, version = coordinate.split(":")
    relative = Path(*group.split("."), artifact, version, f"{artifact}-{version}.jar")
    for repository in (Path.home() / ".m2" / "repository", maven_central_dir()):
        if (repository / relative).is_file():
            return repository / relative
    target = maven_central_dir() / relative
    print(f"downloading {coordinate} into {target.parent}", flush=True)
    url = f"{MAVEN_CENTRAL}/{relative.as_posix()}"
    return download(url, target, sha1_url=url + ".sha1")


def build_files(root: Path, names: tuple[str, ...]) -> list[Path]:
    """Build files under the project, outside dot directories and build outputs."""
    found, stack = [], [Path(root)]
    while stack:
        directory = stack.pop()
        try:
            entries = sorted(directory.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if not entry.name.startswith(".") and entry.name not in BUILD_SKIP and not entry.is_symlink():
                    stack.append(entry)
            elif entry.name in names:
                found.append(entry)
    return found


def _pom(path: Path, local: dict, depth: int = 0) -> dict:
    """A pom's properties, managed versions, dependencies, BOMs and remote parent, local parents merged in."""
    import xml.etree.ElementTree as ElementTree
    empty = {"properties": {}, "managed": {}, "dependencies": [], "boms": []}
    try:
        project = ElementTree.parse(path).getroot()
    except (OSError, ElementTree.ParseError):
        return empty
    parent = project.find("{*}parent")
    inherited = empty
    boms = []
    if parent is not None and depth < 5:
        coordinate = tuple(parent.findtext(f"{{*}}{key}") or "" for key in ("groupId", "artifactId", "version"))
        relative = parent.findtext("{*}relativePath")
        candidate = (path.parent / (relative if relative is not None else "../pom.xml")).resolve()
        if candidate.is_dir():
            candidate = candidate / "pom.xml"
        if candidate.is_file() and candidate.resolve() in local:
            inherited = _pom(candidate, local, depth + 1)
        elif all(coordinate):
            # A parent outside the project manages versions the way a BOM does.
            boms.append(":".join(coordinate))
    properties = dict(inherited["properties"])
    for key in ("groupId", "version"):
        value = project.findtext(f"{{*}}{key}") or (parent.findtext(f"{{*}}{key}") if parent is not None else None)
        if value:
            properties[f"project.{key}"] = properties[f"pom.{key}"] = value
    for item in project.findall("{*}properties/*"):
        properties[item.tag.split("}")[-1]] = (item.text or "").strip()

    def resolve(value):
        for _ in range(5):
            if not value or "${" not in value:
                break
            value = re.sub(r"\$\{([^}]+)\}", lambda match: properties.get(match.group(1), match.group(0)), value)
        return None if not value or "${" in value else value.strip()

    def entries(xpath):
        for dependency in project.findall(xpath):
            group = resolve(dependency.findtext("{*}groupId"))
            artifact = resolve(dependency.findtext("{*}artifactId"))
            if group and artifact:
                yield (group, artifact, resolve(dependency.findtext("{*}version")),
                       (dependency.findtext("{*}scope") or "").strip(), (dependency.findtext("{*}type") or "").strip())

    managed = dict(inherited["managed"])
    boms.extend(inherited["boms"])
    for group, artifact, version, scope, kind in entries("{*}dependencyManagement/{*}dependencies/{*}dependency"):
        if scope == "import" and kind == "pom" and version:
            boms.append(f"{group}:{artifact}:{version}")
        elif version:
            managed[(group, artifact)] = version
    dependencies = list(inherited["dependencies"])
    for xpath in ("{*}dependencies/{*}dependency", "{*}profiles/{*}profile/{*}dependencies/{*}dependency"):
        for group, artifact, version, scope, _kind in entries(xpath):
            if scope != "system":
                dependencies.append((group, artifact, version or managed.get((group, artifact))))
    return {"properties": properties, "managed": managed, "dependencies": dependencies, "boms": boms}


def jvm_coordinates(root: Path) -> tuple[list[str], list[str]]:
    """The project's library coordinates and BOMs, read from its build files without running any of them.

    Maven poms with their properties, managed versions, BOM imports and parents
    inside the project; a parent outside it is used as a BOM. Gradle build files
    and version catalogs give the coordinates they spell out, and `kotlin("x")`
    the Kotlin module at the Kotlin plugin's version. Dependencies a build script
    computes are invisible here, which is the price of not running it.
    """
    import tomllib
    poms = build_files(root, ("pom.xml",))
    local = {path.resolve() for path in poms}
    dependencies: set[str] = set()
    boms: set[str] = set()
    for pom in poms:
        description = _pom(pom, local)
        boms.update(description["boms"])
        for group, artifact, version in description["dependencies"]:
            dependencies.add(f"{group}:{artifact}:{version}" if version else f"{group}:{artifact}")
    import xml.etree.ElementTree as ElementTree
    project_modules = set()
    for pom in poms:
        try:
            project = ElementTree.parse(pom).getroot()
        except (OSError, ElementTree.ParseError):
            continue
        group = project.findtext("{*}groupId") or project.findtext("{*}parent/{*}groupId")
        artifact = project.findtext("{*}artifactId")
        if group and artifact:
            project_modules.add(f"{group}:{artifact}")
    gradle = build_files(root, ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"))
    kotlin_version = None
    for build in gradle:
        try:
            text = build.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in GRADLE_KOTLIN_PLUGIN.finditer(text):
            kotlin_version = kotlin_version or match.group(1) or match.group(2)
        dependencies.update(":".join(parts) for parts in GRADLE_COORDINATE.findall(text))
    for catalog in build_files(root, ("libs.versions.toml",)):
        try:
            data = tomllib.loads(catalog.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        versions = data.get("versions") or {}
        kotlin_version = kotlin_version or (versions.get("kotlin") if isinstance(versions.get("kotlin"), str) else None)
        for entry in (data.get("libraries") or {}).values():
            if isinstance(entry, str):
                parts = entry.split(":")
                if len(parts) >= 2:
                    dependencies.add(":".join(parts[:3]))
                continue
            if not isinstance(entry, dict):
                continue
            module = entry.get("module") or f"{entry.get('group', '')}:{entry.get('name', '')}"
            version = entry.get("version")
            if isinstance(version, dict):
                version = versions.get(version["ref"]) if "ref" in version else (
                    version.get("strictly") or version.get("require") or version.get("prefer"))
            version = version or versions.get(entry.get("version.ref") or "")
            if module.count(":") == 1 and not module.startswith(":"):
                dependencies.add(f"{module}:{version}" if isinstance(version, str) else module)
    for build in gradle:
        try:
            text = build.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, version in GRADLE_KOTLIN_MODULE.findall(text):
            if name not in ("jvm", "multiplatform", "android", "kapt", "plugin.serialization", "plugin.spring"):
                version = version or kotlin_version
                dependencies.add(f"org.jetbrains.kotlin:kotlin-{name}" + (f":{version}" if version else ""))
    # The project's own modules are sources, not libraries.
    dependencies = {item for item in dependencies if ":".join(item.split(":")[:2]) not in project_modules}
    return sorted(dependencies), sorted(boms)


def coursier_jar() -> Path:
    target = shared_engine_dir("coursier") / COURSIER["version"] / "coursier.jar"
    if not target.is_file():
        print(f"installing coursier {COURSIER['version']} into {target.parent} (first use)", flush=True)
        download(COURSIER["url"], target, sha256=COURSIER["sha256"])
    return target


def jvm_classpath(root: Path) -> list[Path]:
    """The jars of the project's libraries with their dependencies, resolved once into the shared store.

    Coursier fetches from Maven Central into the shared store, so each library is fetched
    once for every project on the machine. The resolved list is recorded per set
    of coordinates, so a later pass reads it without starting Coursier. A version
    the build leaves to a BOM or a parent comes from it; a version it does not
    spell out at all is the latest stable one, since a library call needs only to
    be recognized as a library's. A coordinate that does not resolve is left out;
    the rest still counts.
    """
    coordinates, boms = jvm_coordinates(root)
    if not coordinates:
        return []
    key = hashlib.sha256(json.dumps([coordinates, boms]).encode("utf-8")).hexdigest()[:16]
    record = shared_cache_dir() / "classpaths" / f"{key}.json"
    try:
        recorded = json.loads(record.read_text(encoding="utf-8"))
        known = [Path(item) for item in recorded["jars"]]
        # A coordinate that did not resolve is tried again a day later, not at every pass.
        settled = not recorded["unresolved"] or time.time() - record.stat().st_mtime < 86400
        if settled and all(path.is_file() for path in known):
            return known
    except (OSError, ValueError, KeyError, TypeError):
        pass
    print(f"resolving {len(coordinates)} libraries of the project into {maven_central_dir().parents[2]} "
          "(first use)", flush=True)
    base = [str(java_runtime()), "-Xmx512m", "-jar", str(coursier_jar()), "fetch", "--quiet",
            # Not the user's own repository: one there with a pom and no jar fails the whole resolution.
            "--cache", str(maven_central_dir().parents[2]), "--no-default", "-r", "central",
            *[item for bom in boms for item in ("--bom", bom)]]

    def fetch(items):
        completed = subprocess.run([*base, *items], stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                   timeout=1200)
        paths = [Path(row.strip()) for row in completed.stdout.splitlines() if row.strip().endswith(".jar")]
        return completed.returncode == 0, [path for path in paths if path.is_file()]

    def spelled(coordinate, fallback=False):
        if coordinate.count(":") >= 2:
            return coordinate
        # Coursier takes an empty version from the BOMs.
        return f"{coordinate}:" if boms and not fallback else f"{coordinate}:latest.stable"

    ok, jars = fetch([spelled(item) for item in coordinates])
    unresolved = []
    if not ok:
        found: dict[Path, None] = {}
        for coordinate in coordinates:
            single_ok, single = fetch([spelled(coordinate)])
            if not single_ok and coordinate.count(":") == 1 and boms:
                single_ok, single = fetch([spelled(coordinate, fallback=True)])
            found.update(dict.fromkeys(single))
            if not single_ok:
                unresolved.append(coordinate)
        jars = list(found)
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps({"coordinates": coordinates, "boms": boms, "unresolved": unresolved,
                                  "jars": [str(path) for path in jars]}, indent=1), encoding="utf-8")
    return jars


def coordinates_digest(root: Path) -> str:
    return hashlib.sha256(json.dumps(jvm_coordinates(root)).encode("utf-8")).hexdigest()[:16]


def java_source_roots(sources: list[Path]) -> list[Path]:
    """Where the package hierarchy of each Java file begins: its directory minus its package path."""
    roots: dict[Path, None] = {}
    for source in sources:
        try:
            with source.open(encoding="utf-8", errors="replace") as handle:
                head = handle.read(8192)
        except OSError:
            continue
        match = re.search(r"^\s*package\s+([\w.]+)\s*;", head, re.MULTILINE)
        directory = source.parent
        for _ in range(len(match.group(1).split(".")) if match else 0):
            directory = directory.parent
        roots[directory] = None
    return sorted(roots)


def java_runtime() -> Path:
    """A Java runtime of at least version 17: the one on PATH, else Temurin 21 in the shared directory."""
    import platform
    java = shutil.which("java")
    if java:
        try:
            probe = subprocess.run([java, "-XshowSettings:properties", "-version"], capture_output=True,
                                   text=True, timeout=60)
            match = re.search(r"java\.specification\.version = (\d+)", probe.stderr)
            if match and int(match.group(1)) >= JAVA_MINIMUM:
                return Path(java)
        except (OSError, subprocess.TimeoutExpired):
            pass
    home = shared_engine_dir("jre") / "21"
    executable = home / "bin" / ("java.exe" if os.name == "nt" else "java")
    if executable.is_file():
        return executable
    system = {"Windows": "windows", "Linux": "linux", "Darwin": "mac"}[platform.system()]
    arch = "aarch64" if platform.machine().lower() in ("arm64", "aarch64") else "x64"
    print(f"installing a Java 21 runtime into {home} (first use)", flush=True)
    partial = home.with_name(".21.partial")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    archive = partial / ("jre.zip" if system == "windows" else "jre.tar.gz")
    with open_url(TEMURIN_JRE.format(os=system, arch=arch), timeout=600) as response, \
            archive.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    if archive.suffix == ".zip":
        import zipfile
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(partial)
    else:
        import tarfile
        with tarfile.open(archive) as bundle:
            bundle.extractall(partial, filter="data")
    archive.unlink()
    top = next(child for child in partial.iterdir() if child.is_dir())
    bin_parent = top / "Contents" / "Home" if (top / "Contents" / "Home").is_dir() else top
    shutil.rmtree(home, ignore_errors=True)
    os.replace(bin_parent, home)
    shutil.rmtree(partial, ignore_errors=True)
    return executable


class KotlinEngine:
    """Kotlin through the Kotlin Analysis API in standalone mode: a local library, no server, no license.

    On first use Daodan downloads the Analysis API as KSP publishes it on Maven Central,
    a Java runtime when none of version 17 or later is installed, and the Kotlin
    compiler, and compiles `engines/KotlinResolver.kt` against it once, all into the
    shared directory. The resolver runs as one JVM process with a capped heap: it
    builds a standalone session over the snapshot's Kotlin and Java files, with the
    runtime's JDK and the Kotlin standard library as dependencies, and answers one
    position per line. Nothing is built, imported or downloaded for the project, and
    nothing is written into it. The Analysis API's standalone mode is not stable, so
    its version is pinned.
    """

    name = "kotlin"
    languages = ("kotlin",)
    # Java files are loaded too, so a Kotlin call into Java code arrives at its declaration.
    source_languages = ("kotlin", "java")

    def __init__(self, project_root: Path, install_dir: Path | None = None):
        self.project_root = Path(project_root).resolve()
        self.install_root = Path(install_dir) if install_dir else shared_engine_dir("kotlin-analysis-api")
        self.sources: list[Path] = []
        self.install = None
        self.installed_now = False
        self.process = None
        self.answers = None
        self.config = None
        self.lines = SourceLines()
        self.files = 0
        self.timeouts = 0
        self.libraries: list[Path] = []

    @property
    def version(self) -> str:
        return KOTLIN_ANALYSIS.rsplit(":", 1)[1]

    def source(self) -> Path:
        return SCRIPT_DIR / "engines" / "KotlinResolver.kt"

    def resolver(self) -> Path:
        digest = hashlib.sha256(self.source().read_bytes()).hexdigest()[:12]
        return self.install_root / f"{self.version}-{digest}" / "resolver.jar"

    def build(self, java: Path) -> Path:
        jar = self.resolver()
        if jar.is_file():
            return jar
        self.installed_now = True
        print(f"compiling the Kotlin resolver into {jar.parent} (first use)", flush=True)
        compiler = os.pathsep.join(str(maven_artifact(item)) for item in KOTLIN_COMPILER)
        classpath = os.pathsep.join(str(path) for path in self.runtime_classpath()[1:])
        jar.parent.mkdir(parents=True, exist_ok=True)
        partial = jar.with_name("resolver.partial.jar")
        command = [str(java), "-Xmx768m", f"-XX:ActiveProcessorCount={ENGINE_THREADS}", "-cp", compiler,
                   "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler", str(self.source()), "-classpath", classpath,
                   "-d", str(partial), "-jvm-target", "17", "-no-stdlib", "-no-reflect", "-Xskip-prerelease-check",
                   *[f"-opt-in=org.jetbrains.kotlin.analysis.api.{name}" for name in KOTLIN_OPT_INS]]
        completed = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)
        if completed.returncode != 0 or not partial.is_file():
            partial.unlink(missing_ok=True)
            raise RuntimeError("the Kotlin resolver did not compile: " + (completed.stderr or completed.stdout)[-600:])
        os.replace(partial, jar)
        return jar

    def runtime_classpath(self) -> list[Path]:
        return [self.resolver(), maven_artifact(KOTLIN_ANALYSIS), *(maven_artifact(item) for item in KOTLIN_RUNTIME)]

    def probe(self) -> tuple[bool, str]:
        import queue
        try:
            java = java_runtime()
            self.build(java)
            classpath = self.runtime_classpath()
        except Exception as error:
            return False, f"could not install the Kotlin Analysis API: {type(error).__name__}: {error}"
        try:
            project_libraries = jvm_classpath(self.project_root)
        except Exception as error:
            print(f"the project's libraries were not resolved: {type(error).__name__}: {error}", flush=True)
            project_libraries = []
        self.libraries = [maven_artifact("org.jetbrains.kotlin:kotlin-stdlib:2.4.21"), *project_libraries]
        descriptor, name = tempfile.mkstemp(prefix="daodan-kotlin-", suffix=".txt")
        os.close(descriptor)
        self.config = Path(name)
        self.config.write_text("".join(f"root={path}\n" for path in self.sources)
                               + "".join(f"library={path}\n" for path in self.libraries), encoding="utf-8")
        command = [str(java), f"-Xmx{KOTLIN_MEMORY_MB}m", f"-XX:ActiveProcessorCount={ENGINE_THREADS}",
                   "-Djava.awt.headless=true", "-cp", os.pathsep.join(map(str, classpath)),
                   "daodan.KotlinResolverKt", str(self.config)]
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1)
        self.answers = queue.Queue()

        def read():
            for row in self.process.stdout:
                self.answers.put(row.rstrip("\n"))
            self.answers.put(None)

        threading.Thread(target=read, daemon=True).start()
        try:
            ready = self.answers.get(timeout=LSP_START_TIMEOUT)
        except queue.Empty:
            return False, "the Kotlin Analysis API did not start in time"
        if not ready or not ready.startswith("READY"):
            return False, f"the Kotlin Analysis API did not start: {ready or 'the process exited'}"
        self.files = int(ready.split("\t")[1])
        return True, ""

    def definitions(self, path: Path, line: int, column: int) -> list[Location]:
        """Ask at a UTF-8 byte column; the resolver counts UTF-16 units, as PSI does."""
        import queue
        path = Path(path).resolve()
        text = self.lines.get(path, line)
        units = byte_to_utf16(text, column) if text is not None else None
        if units is None:
            raise ValueError(f"no character starts at byte {column} of {path}:{line}")
        if self.process.poll() is not None:
            raise EngineFailure(f"the Kotlin resolver exited with code {self.process.returncode}")
        self.process.stdin.write(f"{path}\t{line}\t{units}\n")
        self.process.stdin.flush()
        try:
            answer = self.answers.get(timeout=LSP_REQUEST_TIMEOUT)
        except queue.Empty:
            self.timeouts += 1
            if self.timeouts >= 3:
                raise EngineFailure("the Kotlin resolver timed out three times in a row") from None
            raise TimeoutError("the Kotlin resolver did not answer in time") from None
        self.timeouts = 0
        if answer is None:
            raise EngineFailure("the Kotlin resolver exited")
        fields = answer.split("\t")
        if fields[0] != "OK":
            raise RuntimeError(" ".join(fields[1:]) or "the Kotlin resolver failed")
        found = []
        for index in range(1, len(fields) - 2, 3):
            target, row, units = fields[index], int(fields[index + 1]), int(fields[index + 2])
            if target == "-":
                found.append(Location(None, None, None))
                continue
            target_path = Path(target).resolve()
            name_line = self.lines.get(target_path, row) if target_path.is_relative_to(self.project_root) else None
            found.append(Location(target_path, row, utf16_to_byte(name_line, units) if name_line is not None else None))
        return found

    def close(self) -> None:
        if self.process is not None:
            try:
                self.process.stdin.close()
                self.process.wait(timeout=30)
            except (OSError, subprocess.TimeoutExpired):
                self.process.kill()
            self.process = None
        if self.config is not None:
            self.config.unlink(missing_ok=True)
            self.config = None

    def identity(self) -> str:
        return f"kotlin-analysis-api@{self.version}"

    def context(self) -> str:
        source = hashlib.sha256(self.source().read_bytes()).hexdigest()[:12]
        return f"{self.identity()}|resolver={source}|libraries={coordinates_digest(self.project_root)}"

    def report(self) -> dict:
        return {"engine": self.identity(), "install_dir": self.install_root.as_posix(),
                "installed_now": self.installed_now, "files": self.files, "max_heap_mb": KOTLIN_MEMORY_MB,
                "processors": ENGINE_THREADS, "libraries": len(self.libraries),
                "position_encoding": "utf-16"}


def _pb_read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    size = len(buf)
    while pos < size:
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift > 63:
            raise ValueError("malformed protobuf varint")
    raise ValueError("truncated protobuf varint")


def _pb_iter_fields(buf: bytes):
    pos = 0
    size = len(buf)
    while pos < size:
        tag, pos = _pb_read_varint(buf, pos)
        field_no = tag >> 3
        wire_type = tag & 0x7
        if wire_type == 0:
            val, pos = _pb_read_varint(buf, pos)
            yield field_no, wire_type, val
        elif wire_type == 1:
            if pos + 8 > size:
                raise ValueError("truncated fixed64")
            yield field_no, wire_type, buf[pos:pos + 8]
            pos += 8
        elif wire_type == 2:
            length, pos = _pb_read_varint(buf, pos)
            if pos + length > size:
                raise ValueError("truncated length-delimited field")
            yield field_no, wire_type, buf[pos:pos + length]
            pos += length
        elif wire_type == 5:
            if pos + 4 > size:
                raise ValueError("truncated fixed32")
            yield field_no, wire_type, buf[pos:pos + 4]
            pos += 4
        else:
            raise ValueError(f"unsupported protobuf wire type: {wire_type}")


class ScipEngine:
    """Resolve call references from a precomputed SCIP index (Protobuf or JSON).

    Nothing in the pass produces an index: this reads one a project already has.
    A `local N` symbol is scoped to its document, so it is keyed by the document. A
    reference whose symbol the index defines nowhere is a definition outside the
    indexed sources, which is external. Positions are converted from the document's
    declared encoding (UTF-16 when unspecified, as scip-typescript writes them).
    """

    name = "scip"
    languages = None  # Query all AST languages in the snapshot, not only Python.
    UNITS = {1: "utf-8", 2: "utf-16", 3: "utf-32"}

    def __init__(self, project_root: Path, index_paths: list[Path] | None = None):
        self.project_root = Path(project_root).resolve()
        self.requested_paths = [Path(p).resolve() for p in (index_paths or ())]
        self.tool_name = "scip"
        self.tool_version = "1.0"
        self.install = None
        self.loaded_indexes: list[str] = []
        self._defs_by_symbol: dict[str, list[tuple[Path, int, int]]] = {}
        self._refs_by_pos: dict[tuple[Path, int, int], list[str]] = {}
        self._units: dict[Path, str] = {}
        self.lines = SourceLines()

    def _document(self, rel: str, occurrences, encoding: int) -> None:
        if not rel:
            return
        path = (self.project_root / rel).resolve()
        self._units[path] = self.UNITS.get(encoding, "utf-16")
        for rng, symbol, roles in occurrences:
            if len(rng) < 3 or not symbol:
                continue
            if symbol.startswith("local "):
                symbol = f"{path.as_posix()}#{symbol}"
            line, column = int(rng[0]) + 1, int(rng[1])
            if roles & 0x1:
                self._defs_by_symbol.setdefault(symbol, []).append((path, line, column))
            else:
                self._refs_by_pos.setdefault((path, line, column), []).append(symbol)

    def _parse_scip_bytes(self, data: bytes) -> None:
        stripped = data.lstrip()
        if stripped.startswith(b"{"):
            doc = json.loads(stripped.decode("utf-8"))
            meta = doc.get("metadata") or {}
            tinfo = meta.get("tool_info") or meta.get("toolInfo") or {}
            self.tool_name = str(tinfo.get("name") or self.tool_name)
            self.tool_version = str(tinfo.get("version") or self.tool_version)
            for d in doc.get("documents") or ():
                occurrences = [(list(o.get("range") or ()), o.get("symbol") or "",
                                int(o.get("symbol_roles") or o.get("symbolRoles") or 0))
                               for o in d.get("occurrences") or ()]
                encoding = d.get("position_encoding") or d.get("positionEncoding") or 0
                self._document(d.get("relative_path") or d.get("relativePath") or "", occurrences,
                               encoding if isinstance(encoding, int) else 0)
            return
        for field_no, wire_type, val in _pb_iter_fields(data):
            if field_no == 1 and wire_type == 2:
                for mf_no, m_wt, m_val in _pb_iter_fields(val):
                    if mf_no == 2 and m_wt == 2:
                        for tf_no, t_wt, t_val in _pb_iter_fields(m_val):
                            if tf_no == 1 and t_wt == 2:
                                self.tool_name = t_val.decode("utf-8", errors="replace") or self.tool_name
                            elif tf_no == 2 and t_wt == 2:
                                self.tool_version = t_val.decode("utf-8", errors="replace") or self.tool_version
            elif field_no == 2 and wire_type == 2:
                rel_path, encoding, occurrences = "", 0, []
                for df_no, d_wt, d_val in _pb_iter_fields(val):
                    if df_no == 1 and d_wt == 2:
                        rel_path = d_val.decode("utf-8", errors="replace")
                    elif df_no == 6 and d_wt == 0:
                        encoding = int(d_val)
                    elif df_no == 2 and d_wt == 2:
                        rng, sym, roles = [], "", 0
                        for of_no, o_wt, o_val in _pb_iter_fields(d_val):
                            if of_no == 1 and o_wt == 2:
                                p = 0
                                while p < len(o_val):
                                    v, p = _pb_read_varint(o_val, p)
                                    rng.append(v)
                            elif of_no == 1 and o_wt == 0:
                                rng.append(int(o_val))
                            elif of_no == 2 and o_wt == 2:
                                sym = o_val.decode("utf-8", errors="replace")
                            elif of_no == 3 and o_wt == 0:
                                roles = int(o_val)
                            elif of_no in (8, 9) and o_wt == 2:
                                # The typed range of the current schema; a zero field is not written.
                                fields = {number: int(value) for number, wire, value in _pb_iter_fields(o_val)
                                          if wire == 0}
                                if of_no == 8:
                                    line = fields.get(1, 0)
                                    rng = [line, fields.get(2, 0), line, fields.get(3, 0)]
                                else:
                                    rng = [fields.get(1, 0), fields.get(2, 0), fields.get(3, 0), fields.get(4, 0)]
                        occurrences.append((rng, sym, roles))
                self._document(rel_path, occurrences, encoding)

    def probe(self) -> tuple[bool, str]:
        self._defs_by_symbol.clear()
        self._refs_by_pos.clear()
        self._units.clear()
        self.loaded_indexes.clear()
        candidates = list(self.requested_paths)
        if not candidates and (self.project_root / "index.scip").is_file():
            candidates.append((self.project_root / "index.scip").resolve())
        if not candidates:
            self.install = "generate index.scip with the language's SCIP indexer and pass --scip-index"
            return False, "no SCIP index found; pass --scip-index <index.scip> or place index.scip in the project root"
        for idx_path in candidates:
            if not idx_path.is_file():
                return False, f"SCIP index does not exist: {idx_path}"
            try:
                self._parse_scip_bytes(idx_path.read_bytes())
                self.loaded_indexes.append(idx_path.as_posix())
            except Exception as exc:
                return False, f"invalid SCIP index {idx_path}: {type(exc).__name__}: {exc}"
        return True, ""

    def _convert(self, path: Path, line: int, column: int, *, to_bytes: bool) -> int | None:
        unit = self._units.get(path, "utf-16")
        text = self.lines.get(path, line)
        if text is None or unit == "utf-8":
            return column if text is not None else None
        if unit == "utf-16":
            return utf16_to_byte(text, column) if to_bytes else byte_to_utf16(text, column)
        return char_to_byte(text, column) if to_bytes else byte_to_char(text, column)

    def definitions(self, path: Path, line: int, column: int) -> list[Location]:
        path = Path(path).resolve()
        native = self._convert(path, line, column, to_bytes=False)
        found = []
        for symbol in self._refs_by_pos.get((path, line, native), ()):
            targets = self._defs_by_symbol.get(symbol)
            if not targets:
                found.append(Location(None, None, None))
                continue
            for target, row, start in targets:
                found.append(Location(target, row, self._convert(target, row, start, to_bytes=True)))
        return found

    def identity(self) -> str:
        return f"scip:{self.tool_name}@{self.tool_version}"

    def report(self) -> dict:
        return {"indexes": list(self.loaded_indexes)}


def callee_column(source_line: str, span: list[int], last_part: str) -> int | None:
    """The UTF-8 byte column of the callee's name, the snapshot's unit.

    For a multiline expression, the supplied line is the span's final line. A
    callee ends at its span's end; a matching substring elsewhere in its receiver
    is insufficient evidence of its position.
    """
    start, end = (span[1] if span[0] == span[2] else 0), span[3]
    encoded = source_line.encode("utf-8")
    if not last_part or not 0 <= start < end <= len(encoded):
        return None
    try:
        window = encoded[start:end].decode("utf-8")
    except UnicodeError:
        return None
    if not window.endswith(last_part):
        return None
    return end - len(last_part.encode("utf-8"))


def _python_name_positions(source: str) -> dict:
    """`(kind, line, byte column of def/async/class)` to `(name, line, byte column of the name)`."""
    names = {}
    previous = None
    declaration = None
    lines = source.split("\n")
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if declaration is not None and token.type == tokenize.NAME:
                row, column = token.start
                names[declaration] = (unicodedata.normalize("NFKC", token.string), row,
                                      char_to_byte(lines[row - 1], column))
                declaration = None
            if token.type == tokenize.NAME and token.string in ("def", "class"):
                line, column = token.start
                if token.string == "def" and previous is not None \
                        and previous.type == tokenize.NAME and previous.string == "async":
                    line, column = previous.start
                declaration = ("function" if token.string == "def" else "class", line,
                               char_to_byte(lines[line - 1], column))
            previous = token
    except (tokenize.TokenError, IndentationError):
        # Declarations recorded before a damaged suffix stay usable only where the
        # snapshot independently holds their exact spans.
        pass
    return names


def symbol_table(connection, rel: str, source: str) -> tuple[dict, set]:
    """Where each function, method and class of a file is named: `(line, byte column)` to `(id, kind)`.

    An engine answers with the position of a declaration's name, and only that
    position binds it to this snapshot: a matching bare name elsewhere proves no
    edge. Tree-sitter adapters record the name as `name_span`, and the names of a
    body's overload signatures as `signature_spans`; Python's AST gives
    only the statement start, so its names come from tokenizing the verified
    source. Two declarations named at one position are ambiguous, never a first match.
    """
    python = rel.lower().endswith((".py", ".pyi"))
    python_names = _python_name_positions(source) if python else {}
    table: dict = {}
    ambiguous: set = set()
    # A value binding is where a callable is held, not what is called: it never
    # becomes a target, and a callable named at the same position wins.
    bindings = {(line, column): (identity, "binding") for identity, line, column in connection.execute(
        "SELECT id, l0, c0 FROM sem_declarations WHERE file=? AND kind IN ('binding','parameter','property')",
        (rel,))}
    for identity, name, kind, line, column, blob in connection.execute(
            "SELECT id, name, kind, l0, c0, payload FROM sem_declarations "
            "WHERE file=? AND kind IN ('function','method','class') ORDER BY l0,c0", (rel,)):
        kind = "function" if kind == "method" else kind
        if python:
            found = python_names.get((kind, line, column))
            if found is None or found[0] != name:
                continue
            keys = [found[1:]]
        else:
            payload = _unpack(blob) or {}
            if not payload.get("name_span"):
                continue
            if payload.get("constructs"):
                identity, kind = f"{rel}::{payload['constructs']}", "class"
            # Overload signatures name the same body as the implementation's own name.
            keys = [(span[0], span[1]) for span in (payload["name_span"], *payload.get("signature_spans", ()))]
        for key in keys:
            if key in table and table[key][0] != identity:
                ambiguous.add(key)
            table.setdefault(key, (identity, kind))
    for key, value in bindings.items():
        table.setdefault(key, value)
    return table, ambiguous


def inventory_files(connection) -> set[str]:
    return {row[0] for row in connection.execute(
        "SELECT file FROM sem_coverage WHERE status='ast'")}


def grade(definition, inventory: set[str], tables: dict, root: Path,
          table_for) -> tuple[str, dict | None]:
    """One engine answer, graded by what this snapshot declares at that position.

    Returns `(verdict, target)` where verdict is `edge-call`, `edge-instantiation`,
    `external-definition`, `project-not-a-symbol`, `ambiguous-target`, `unresolved`
    or `binding` (a value binding, which `grade_all` never keeps as a target),
    and target carries the declaration identity an edge arrives at. The kind comes
    from the snapshot's declaration, never from the engine.
    """
    if definition is None:
        return "unresolved", None
    module_path = getattr(definition, "module_path", None)
    if not module_path:
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
    line = getattr(definition, "line", None)
    column = getattr(definition, "column", None)
    if type(line) is not int or type(column) is not int:
        return "project-not-a-symbol", None
    if (line, column) in ambiguous:
        return "ambiguous-target", None
    found = table.get((line, column))
    if found is None:
        return "project-not-a-symbol", None
    identity, kind = found
    if kind == "binding":
        return "binding", None
    verdict = "edge-instantiation" if kind == "class" else "edge-call"
    return verdict, {"id": identity, "file": relative, "kind": kind}


def grade_all(definitions, inventory: set[str], tables: dict, root: Path,
              table_for, *, follow=None) -> tuple[str, dict | None]:
    """Follow exact holders with engine evidence, bounded to 64 distinct queries.

    A holder beside a confirmed callable names its container (requirement 14).
    An external location alone does not identify a project holder's contents.
    Cycles, missing answers and exhausted budgets keep uncertainty explicit.
    """
    memo, active = {}, set()
    queries = 0

    def walk(items):
        nonlocal queries
        if not items:
            return "unresolved", None
        unique = {(str(item.module_path), item.line, item.column): item for item in items}
        graded = [(key, item, grade(item, inventory, tables, root, table_for))
                  for key, item in unique.items()]
        callable_found = any(answer[0].startswith("edge-") for _, _, answer in graded)
        answers = []
        for key, item, answer in graded:
            if answer[0] == "binding":
                if callable_found:
                    continue
                if follow is None or key in active or len(active) >= 32:
                    answer = ("project-not-a-symbol", None)
                elif key in memo:
                    answer = memo[key]
                elif queries >= 64:
                    answer = ("project-not-a-symbol", None)
                else:
                    queries += 1
                    active.add(key)
                    children = follow(item)
                    answer = walk(children) if children else ("project-not-a-symbol", None)
                    active.remove(key)
                    memo[key] = answer
            answers.append(answer)
        if all(answer == answers[0] for answer in answers):
            return answers[0]
        return "ambiguous-target", None

    return walk(definitions)


def runtime_imports(connection) -> dict[str, dict]:
    """Imports the snapshot could not place that reach a project module through `sys.path`.

    A bare `import snapshot` the snapshot could not place is how a test or a
    script reaches a tool after inserting the tool's directory into sys.path.
    When exactly one directory holds an inventoried Python module of that name,
    that directory is such a root. Standard-library names never make one. Returns,
    per module name, the directory relative to the snapshot root, the module's
    files and the files that import it.
    """
    placed = {(row[0], row[1]) for row in connection.execute("SELECT file, module FROM sem_modules")}
    importers: dict[str, set[str]] = {}
    for file, blob in connection.execute("SELECT file, payload FROM sem_bindings WHERE kind='import'"):
        module = (_unpack(blob) or {}).get("module") or ""
        head = module.split(".")[0]
        if head and not module.startswith(".") and (file, module) not in placed \
                and head not in sys.stdlib_module_names:
            importers.setdefault(head, set()).add(file)
    found: dict[str, dict[str, set[str]]] = {}
    for (rel,) in connection.execute("SELECT file FROM sem_coverage WHERE language='python'"):
        path = PurePosixPath(rel)
        package = path.name == "__init__.py"
        name = path.parent.name if package else path.stem
        if name in importers:
            directory = (path.parent.parent if package else path.parent).as_posix()
            found.setdefault(name, {}).setdefault(directory, set()).add(rel)
    return {name: {"directory": directory, "files": sorted(files), "importers": sorted(importers[name])}
            for name, places in sorted(found.items()) if len(places) == 1
            for directory, files in places.items()}


def runtime_import_roots(connection) -> list[str]:
    """Directories the project puts on sys.path at runtime (`runtime_imports`), relative and sorted."""
    return sorted({item["directory"] for item in runtime_imports(connection).values()})


def project_callee_names(connection) -> set[str]:
    """Names used to prioritize queries, never to prove a call external."""
    names = {unicodedata.normalize("NFKC", row[0]) for row in connection.execute(
        "SELECT DISTINCT name FROM sem_declarations WHERE kind IN ('function','method','class')")}
    # A Go method is declared as `Type.Method`; a call names it by the last segment.
    names |= {name.rsplit(".", 1)[-1] for name in names if "." in name}
    names |= {unicodedata.normalize("NFKC", row[0]) for row in connection.execute(
        "SELECT DISTINCT name FROM sem_bindings WHERE kind='import'")}
    return names


def classify_reference(payload: dict, names: set[str]) -> str:
    """An unresolved call is builtin, dynamic or askable, regardless of its name."""
    parts = payload.get("parts") or []
    if payload.get("reason") in EXCLUDED_REASONS:
        return "builtin"
    if not parts:
        return "dynamic"
    return "askable"


REFERENCE_CLASSES = ("builtin", "dynamic", "askable")


class ResolutionCounter:
    """Per-language counts of a snapshot's calls, fed one reference at a time."""

    def __init__(self, names: set[str]):
        self.names = names
        self.languages: dict[str, dict] = {}

    def add(self, language: str | None, res_state: str, payload: dict, *, engine_resolved: bool = False,
            engine_external: bool = False) -> None:
        counts = self.languages.setdefault(language or "unknown", {
            "calls": 0, "lexical_resolved": 0, "engine_confirmed": 0, "engine_refuted": 0,
            **dict.fromkeys(REFERENCE_CLASSES, 0)})
        counts["calls"] += 1
        if res_state == "resolved":
            # A bound call the engine places outside the project is external; one it rebinds is the engine's.
            counts["engine_refuted" if engine_external else
                   "engine_confirmed" if engine_resolved else "lexical_resolved"] += 1
            return
        counts["engine_confirmed"] += int(engine_resolved)
        counts[classify_reference(payload, self.names)] += 1

    def summary(self, binding: dict | None, *, stored_confirmed: bool = False) -> dict:
        """Resolved over resolvable, overall and per language.

        `external` counts the calls that cannot arrive at a project symbol under
        proven origin: builtins and the positions an engine inferred to a definition outside
        the inventory. `resolvable` is every other call, dynamic callees included;
        `unasked` is the askable remainder no engine pass has inferred. Each
        language reads its own entry of the edge store; its `engine` is None when
        no pass covers it. `stored_confirmed` counts the store's confirmed edges
        and its checks of the bound calls when the caller did not feed them
        reference by reference.
        """
        entries = (binding or {}).get("languages") or {}
        keys = ("calls", "lexical_resolved", "engine_confirmed", "engine_external", "asked", "engine_unresolved",
                *REFERENCE_CLASSES)
        total = dict.fromkeys(keys, 0)
        by_language = {}
        for language, counts in sorted(self.languages.items()):
            entry = entries.get(language) or {}
            verdicts = entry.get("verdicts") or {}
            row = {**counts,
                   "asked": int(entry.get("asked", 0)) + int(entry.get("reused", 0)),
                   "engine_unresolved": sum(int(verdicts.get(key, 0)) for key in
                                            ("unresolved", "ambiguous-target", "project-not-a-symbol"))}
            if stored_confirmed:
                checked = entry.get("checked") or {}
                corrected, refuted = int(checked.get("corrected", 0)), int(checked.get("external", 0))
                row["lexical_resolved"] -= corrected + refuted
                row["engine_confirmed"] += int(entry.get("confirmed", 0)) + corrected
                row["engine_refuted"] += refuted
            row["engine_external"] = int(verdicts.get("external-definition", 0)) + row["engine_refuted"]
            for key in keys:
                total[key] += row[key]
            resolvable = row["calls"] - row["builtin"] - row["engine_external"]
            resolved = row["lexical_resolved"] + row["engine_confirmed"]
            by_language[language] = {"calls": row["calls"], "resolved": resolved, "resolvable": resolvable,
                                     "resolved_ratio": round(resolved / resolvable, 3) if resolvable else None,
                                     "engine": entry.get("engine")}
        external = total["builtin"] + total["engine_external"]
        resolvable = total["calls"] - external
        resolved = total["lexical_resolved"] + total["engine_confirmed"]
        return {
            "calls": total["calls"],
            "resolved": resolved,
            "lexical_resolved": total["lexical_resolved"],
            "engine_confirmed": total["engine_confirmed"],
            "external": external,
            "external_by_class": {"builtin": total["builtin"],
                                  "engine-external-definition": total["engine_external"]},
            "resolvable": resolvable,
            "resolved_ratio": round(resolved / resolvable, 3) if resolvable else None,
            "dynamic": total["dynamic"],
            "askable": total["askable"],
            "unasked": max(total["askable"] - total["asked"], 0),
            "engine_unresolved": total["engine_unresolved"],
            "by_language": by_language,
            "note": "resolved_ratio is resolved over resolvable; external calls never arrive at a project symbol.",
        }


def resolution_summary(connection, binding: dict | None) -> dict:
    """Resolved over resolvable for a snapshot's call references and a bound edge store."""
    counter = ResolutionCounter(project_callee_names(connection))
    for res_state, blob, language in connection.execute(
            "SELECT r.resolution, r.payload, c.language FROM sem_references r "
            "LEFT JOIN sem_coverage c ON c.file=r.file WHERE r.kind='call'"):
        counter.add(language, res_state, _unpack(blob))
    return counter.summary(binding, stored_confirmed=True)


def verify_sources(store, languages=None) -> tuple[Path, dict[str, Path], int]:
    """Check the sources an engine can read, including dependencies inferred indirectly.

    Every inventoried file keeps its confined path, so no output can replace one.
    The bytes are hashed for the files of the engine's languages, or for every
    file when `languages` is None: a changed document cannot alter an inference,
    a changed source of the engine's language can, wherever it sits. Returns the
    root, the paths and how many files were hashed.
    """
    root, target, perimeter = _binding(store)
    paths = {}
    verified = 0
    for rel, entry in store.iter_file_headers_only():
        checked = languages is None or entry.get("language") in languages
        try:
            path = _source_path(rel, root, target, perimeter)
        except ValueError:
            if checked:
                raise
            continue
        paths[rel] = path
        if not checked:
            continue
        expected = entry.get("raw_hash")
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        if not isinstance(expected, str) or digest.hexdigest() != expected:
            raise ValueError(f"source differs from snapshot: {rel}; refresh the snapshot")
        verified += 1
    return root, paths, verified


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


EDGE_SCHEMA = 5
# One row per end of a reference: `verdict` is the end's class, `confidence` confirmed, uncertain or observed.
EDGE_COLUMNS = ("reference_id", "file", "language", "kind", "caller", "l0", "c0", "verdict", "target_id", "symbol",
                "resolver", "confidence", "payload")
HOLE_COLUMNS = ("reference_id", "file", "language", "kind", "l0", "c0", "class", "reason", "resolver")
EXTERNAL_COLUMNS = ("symbol", "manager", "package", "version")


def default_edge_store(manifest: Path) -> Path:
    """The derived store's place: beside the snapshot it is bound to."""
    return Path(manifest).with_name("engine-edges.sqlite")


def store_binding(store, manifest: Path, fingerprint: str, entries: dict, reports: dict) -> dict:
    """The store's meta: its snapshot, one entry per language an engine covered, and their totals.

    Each entry is what one engine pass established for one language. The totals
    exist for consumers that read one store as one population.
    """
    entries = dict(sorted(entries.items()))
    values = list(entries.values())
    verdicts: dict[str, int] = {}
    for entry in values:
        for key, count in (entry.get("verdicts") or {}).items():
            verdicts[key] = verdicts.get(key, 0) + count
    confirmed = sum(entry.get("confirmed", 0) for entry in values)
    candidates = sum(entry.get("candidates", 0) for entry in values)
    reasons = {entry.get("no_edges_reason") for entry in values} - {None}
    return {
        "schema": EDGE_SCHEMA,
        "manifest": Path(manifest).as_posix(),
        "manifest_digest": logical_digest(store),
        "parser_fingerprint": fingerprint,
        "resolver_version": semantic_store.RESOLVER_VERSION,
        "languages": entries,
        "engine_reports": dict(sorted(reports.items())),
        "engine": " + ".join(sorted({entry["engine"] for entry in values})) or None,
        "population": sum(entry.get("population", 0) for entry in values),
        "selected": sum(entry.get("selected", 0) for entry in values),
        "asked": sum(entry.get("asked", 0) for entry in values),
        "stride": max([entry.get("stride", 1) for entry in values] or [1]),
        "confirmed": confirmed,
        "candidates": candidates,
        "no_edges_reason": None if confirmed or candidates else (reasons.pop() if len(reasons) == 1 else
                                                                 "no-project-targets" if reasons else None),
        "verdicts": dict(sorted(verdicts.items())),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_edge_store(out: Path, edges: list[dict], binding: dict, holes: list[dict] = ()) -> Path:
    """Write the store atomically, so a partial pass leaves no store.

    An edge's `external` (`{manager, package, version}`) is kept once per symbol in `externals`.
    """
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{out.name}.", suffix=".partial", dir=out.parent)
    os.close(descriptor)
    temporary = Path(name)
    externals = {edge["symbol"]: edge["external"] for edge in edges if edge.get("external") and edge.get("symbol")}
    try:
        connection = sqlite3.connect(temporary)
        try:
            connection.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value BLOB NOT NULL)")
            connection.execute(
                "CREATE TABLE edges(reference_id TEXT,file TEXT NOT NULL,language TEXT,kind TEXT NOT NULL,caller TEXT,"
                "l0 INTEGER,c0 INTEGER,verdict TEXT NOT NULL,target_id TEXT,symbol TEXT,resolver TEXT NOT NULL,"
                "confidence TEXT NOT NULL,payload BLOB NOT NULL)")
            connection.execute(
                "CREATE TABLE holes(reference_id TEXT,file TEXT NOT NULL,language TEXT,kind TEXT NOT NULL,"
                "l0 INTEGER,c0 INTEGER,class TEXT NOT NULL,reason TEXT,resolver TEXT NOT NULL)")
            connection.execute("CREATE TABLE externals(symbol TEXT PRIMARY KEY,manager TEXT,package TEXT,version TEXT)")
            connection.execute("CREATE INDEX edges_reference ON edges(reference_id)")
            connection.execute("CREATE INDEX edges_file ON edges(file)")
            connection.execute("CREATE INDEX edges_target ON edges(target_id)")
            connection.execute("CREATE INDEX holes_reference ON holes(reference_id)")
            connection.executemany("INSERT INTO meta VALUES(?,?)",
                                   [(key, _pack(value)) for key, value in sorted(binding.items())])
            connection.executemany(
                f"INSERT INTO edges VALUES({','.join('?' for _ in EDGE_COLUMNS)})",
                [tuple(_pack(edge[key]) if key == "payload" else edge.get(key) for key in EDGE_COLUMNS)
                 for edge in edges])
            connection.executemany(f"INSERT INTO holes VALUES({','.join('?' for _ in HOLE_COLUMNS)})",
                                   [tuple(hole.get(key) for key in HOLE_COLUMNS) for hole in holes])
            connection.executemany("INSERT INTO externals VALUES(?,?,?,?)",
                                   [(symbol, *(package.get(key) for key in EXTERNAL_COLUMNS[1:]))
                                    for symbol, package in sorted(externals.items())])
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
        externals = {row[0]: dict(zip(EXTERNAL_COLUMNS[1:], row[1:]))
                     for row in connection.execute(f"SELECT {','.join(EXTERNAL_COLUMNS)} FROM externals")}
        edges = []
        for row in connection.execute(f"SELECT {','.join(EDGE_COLUMNS)} FROM edges ORDER BY file,l0,c0"):
            edge = {key: _unpack(value) if key == "payload" else value for key, value in zip(EDGE_COLUMNS, row)}
            if edge["verdict"] == "external":
                edge["external"] = externals.get(edge["symbol"])
            edges.append(edge)
        if getattr(store, "format", None) == "sqlite" and getattr(store, "connection", None) is not None:
            with semantic_store.semantic_reader(store) as sem_db:
                valid_targets = {
                    row[0]
                    for row in sem_db.execute(
                        "SELECT id FROM sem_declarations WHERE kind IN ('function','method','class')"
                    )
                }
                valid_refs = {
                    row[0]: (row[1], row[2])
                    for row in sem_db.execute(
                        "SELECT id,file,caller FROM sem_references WHERE kind IN ('call','read')"
                    )
                }
            for edge in edges:
                ref_id = edge.get("reference_id")
                if ref_id is None:
                    # A site the snapshot lists no reference for: kept, read by no consumer.
                    continue
                if ref_id not in valid_refs:
                    return None, binding, f"engine edge reference is not in snapshot: {ref_id}"
                ref_file, ref_caller = valid_refs[ref_id]
                if edge.get("file") != ref_file or edge.get("caller") != ref_caller:
                    return None, binding, f"engine edge callsite metadata mismatch for {ref_id}"
                if edge.get("verdict") == "project-callable" and edge.get("confidence") != "uncertain":
                    target_id = edge.get("target_id")
                    if not target_id or target_id not in valid_targets:
                        return None, binding, f"engine edge target is not in snapshot: {target_id}"
        return edges, binding, None
    except (sqlite3.Error, ValueError, TypeError) as error:
        return None, binding, f"invalid engine edge store: {error}"
    finally:
        if connection is not None:
            connection.close()


def read_edge_holes(path: Path) -> list[dict]:
    """The holes of a store `read_edge_store` accepted: references with no answer, by class."""
    connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return [dict(zip(HOLE_COLUMNS, row)) for row in connection.execute(
            f"SELECT {','.join(HOLE_COLUMNS)} FROM holes ORDER BY file,l0,c0")]
    finally:
        connection.close()


MEMORY_EXHAUSTED = re.compile(r"MemoryError|out of memory|OutOfMemoryError|bad_alloc|Cannot allocate memory",
                              re.IGNORECASE)


def snapshot_languages(connection) -> list[str]:
    return [row[0] for row in connection.execute(
        "SELECT DISTINCT language FROM sem_coverage WHERE status='ast' AND language IS NOT NULL ORDER BY language")]


def engine_languages(engine, connection) -> tuple[str, ...]:
    """The snapshot languages an engine answers for: its declared ones, or every parsed one."""
    declared = getattr(engine, "languages", ("python",))
    present = snapshot_languages(connection)
    if declared is None:
        return tuple(present)
    return tuple(language for language in declared if language in present) or tuple(declared[:1])


ANSWERS_NAME = "engine-answers.sqlite"
# A running pass publishes what it has proved at most this often.
PUBLISH_SECONDS = 30


def default_answers_path(manifest: Path) -> Path:
    """The answer cache of the analysis a snapshot belongs to, beside its card store."""
    import card_store
    return card_store.default_cards_path(manifest).with_name(ANSWERS_NAME)


def file_dependencies(connection) -> dict[str, set[str]]:
    """The inventoried files each file imports: placed imports and modules reached through `sys.path`."""
    dependencies: dict[str, set[str]] = {}
    for source, target in connection.execute("SELECT source, target FROM sem_edges"):
        dependencies.setdefault(source, set()).add(target)
    for item in runtime_imports(connection).values():
        for importer in item["importers"]:
            dependencies.setdefault(importer, set()).update(item["files"])
    return dependencies


def dependency_digests(hashes: dict[str, str], dependencies: dict[str, set[str]]) -> dict[str, str]:
    """A digest per file over its own bytes and every file it reaches through imports.

    Two snapshots give a file the same digest only when neither it nor anything it
    imports, directly or transitively, changed: the condition under which an engine
    answer at one of its positions can be reused. The files of an import cycle share
    one digest. Tarjan's algorithm, iterative, closes a component only after every
    component it reaches, so each digest is computed once.
    """
    def reach(node):
        return sorted(item for item in dependencies.get(node, ()) if item in hashes and item != node)

    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    digests: dict[str, str] = {}
    for root in sorted(hashes):
        if root in index:
            continue
        index[root] = low[root] = len(index)
        stack.append(root)
        on_stack.add(root)
        work = [(root, iter(reach(root)))]
        while work:
            node, children = work[-1]
            for child in children:
                if child not in index:
                    index[child] = low[child] = len(index)
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(reach(child))))
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[node])
                if low[node] == index[node]:
                    members = []
                    while True:
                        item = stack.pop()
                        on_stack.discard(item)
                        members.append(item)
                        if item == node:
                            break
                    members.sort()
                    inside = set(members)
                    beyond = sorted({digests[item] for member in members for item in reach(member)
                                     if item not in inside})
                    digest = hashlib.sha256(json.dumps(
                        [[[member, hashes[member]] for member in members], beyond]).encode("utf-8")).hexdigest()
                    digests.update(dict.fromkeys(members, digest))
    return digests


def file_ranks(connection) -> dict[str, float]:
    """The snapshot's PageRank of each file, or nothing when the graph metrics are absent."""
    try:
        return {row[0]: row[1] or 0.0 for row in connection.execute("SELECT node, score FROM sem_rank")}
    except sqlite3.Error:
        return {}


ANSWER_COLUMNS = ("context", "engine", "reference_id", "file", "file_hash", "file_digest", "verdict",
                  "target_id", "targets", "resolver", "line", "column")


def _answers_connection(path: Path):
    connection = sqlite3.connect(path, timeout=30)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS answers(context TEXT NOT NULL,engine TEXT NOT NULL,reference_id TEXT NOT NULL,"
        "file TEXT NOT NULL,file_hash TEXT NOT NULL,file_digest TEXT NOT NULL,verdict TEXT NOT NULL,"
        "target_id TEXT,targets TEXT NOT NULL,resolver TEXT NOT NULL,line INTEGER,column INTEGER,"
        "PRIMARY KEY(context,reference_id))")
    connection.execute("CREATE INDEX IF NOT EXISTS answers_file ON answers(engine,file)")
    return connection


def load_answers(path: Path, context: str, engine: str) -> tuple[dict[str, dict], dict[str, str]]:
    """The cached answers of this engine context by reference, and the file hashes the engine last answered for."""
    if not path.is_file():
        return {}, {}
    connection = _answers_connection(path)
    try:
        answers = {row[2]: dict(zip(ANSWER_COLUMNS, row)) for row in connection.execute(
            f"SELECT {','.join(ANSWER_COLUMNS)} FROM answers WHERE context=?", (context,))}
        known = dict(connection.execute("SELECT DISTINCT file, file_hash FROM answers WHERE engine=?", (engine,)))
    finally:
        connection.close()
    return answers, known


def save_answers(path: Path, context: str, engine: str, rows: list[dict]) -> None:
    """Add answers, keeping one engine context and one generation per file."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = _answers_connection(path)
    try:
        with connection:
            connection.execute("DELETE FROM answers WHERE engine=? AND context<>?", (engine, context))
            for file, digest in sorted({(row["file"], row["file_digest"]) for row in rows}):
                connection.execute("DELETE FROM answers WHERE context=? AND file=? AND file_digest<>?",
                                   (context, file, digest))
            connection.executemany(
                f"INSERT OR REPLACE INTO answers VALUES({','.join('?' for _ in ANSWER_COLUMNS)})",
                [tuple(row[key] for key in ANSWER_COLUMNS) for row in rows])
    finally:
        connection.close()


def answer_targets(definitions, root: Path, hashes: dict[str, str]) -> str:
    """The project files an answer points into, with their bytes: a reused answer needs them unchanged."""
    targets = {}
    for definition in definitions or ():
        module_path = getattr(definition, "module_path", None)
        if not module_path:
            continue
        try:
            relative = Path(module_path).resolve().relative_to(root).as_posix()
        except ValueError:
            continue
        targets[relative] = hashes.get(relative)
    return json.dumps(dict(sorted(targets.items())))


def resolve_edges(manifest: Path, *, engine, limit: int | None, stride: int,
                  dry_run: bool = False, out: Path | None = None) -> dict:
    """Ask the engine about the unresolved calls of its languages and record what it proves.

    The store keeps one entry per language. A pass replaces the entries and edges
    of its own languages and keeps those another engine wrote for this snapshot.
    Work goes where it is worth most: an answer whose file and imports are unchanged
    since the engine gave it comes from the answer cache; edited and new files are
    asked first, then files by rank; the engine starts only when a position needs
    it; and the pass publishes what it has proved every `PUBLISH_SECONDS`, so a
    stopped or failed pass resumes where it ended. A dry run neither reuses nor publishes.
    """
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
        languages = engine_languages(engine, connection)
        try:
            store_root, source_paths, verified_before = verify_sources(store, languages)
            destination = edge_destination(out or default_edge_store(manifest), manifest, source_paths)
        except (OSError, ValueError) as error:
            return {"engine": engine.name, "available": False,
                    "reason": str(error), "stage": "before-inference", "edges_store": None}
        if hasattr(engine, "import_roots"):
            engine.import_roots = [store_root / rel for rel in runtime_import_roots(connection)]
        if hasattr(engine, "sources"):
            # An engine that loads the sources itself gets the snapshot's perimeter, never the directory.
            wanted = set(engine.source_languages)
            engine.sources = sorted(source_paths[rel] for rel, language in connection.execute(
                "SELECT file, language FROM sem_coverage") if language in wanted and rel in source_paths)
        inventory = inventory_files(connection)
        hashes = {rel: entry.get("raw_hash") for rel, entry in store.iter_file_headers_only()}
        placeholders = ",".join("?" for _ in languages)
        rows = connection.execute(
            f"SELECT r.id, r.file, r.payload, r.l0, r.c0, r.l1, r.c1, c.language FROM sem_references r "
            f"JOIN sem_coverage c ON c.file=r.file "
            f"WHERE r.kind='call' AND r.resolution IN ('unresolved','resolved') AND c.language IN ({placeholders}) "
            f"ORDER BY r.id", tuple(languages)).fetchall()
        # The calls the lexical resolver bound, with the target the engine is checked against.
        lexical = dict(connection.execute(
            "SELECT id, target_id FROM sem_references WHERE kind='call' AND resolution='resolved'"))
        # Every call and read of these languages ends in an edge row or a hole (`holes_of`, by reference).
        sites = connection.execute(
            f"SELECT r.id, r.file, r.kind, r.l0, r.c0, c.language, r.resolution FROM sem_references r "
            f"JOIN sem_coverage c ON c.file=r.file WHERE r.kind IN ('call','read') AND c.language IN ({placeholders}) "
            f"ORDER BY r.id", tuple(languages)).fetchall()
        holes_of: dict[str, tuple[str, str]] = {}
        callee_names = project_callee_names(connection)
        counts = {language: {"population": 0, "selected": 0, "asked": 0, "reused": 0, "confirmed": 0,
                             "candidates": 0, "verdicts": {}, "excluded_classes": {},
                             "checked": {"population": 0, "asked": 0, "same": 0, "corrected": 0, "external": 0}}
                  for language in languages}
        population, bound = [], []
        for row in rows:
            if row[0] in lexical:
                bound.append(row)
                counts[row[7]]["checked"]["population"] += 1
                continue
            reference_class = classify_reference(_unpack(row[2]), callee_names)
            if reference_class in ("askable", "dynamic"):
                population.append(row)
                counts[row[7]]["population"] += 1
            else:
                excluded = counts[row[7]]["excluded_classes"]
                excluded[reference_class] = excluded.get(reference_class, 0) + 1
                holes_of[row[0]] = ("not-asked", reference_class)

        # Reuse: same engine context, same file and imports, same target bytes.
        context = None if dry_run else getattr(engine, "context", lambda: None)()
        cached, known, cache_path, cache_note, digests = {}, {}, None, None, {}
        if context is not None:
            context = f"{context}|{store['target']}|{fingerprint}|{semantic_store.RESOLVER_VERSION}|{EDGE_SCHEMA}"
            if hasattr(engine, "implementations"):
                context += "|implementation"
            digests = dependency_digests(hashes, file_dependencies(connection))
            try:
                cache_path = edge_destination(default_answers_path(manifest), manifest, source_paths)
                cached, known = load_answers(cache_path, context, engine.name)
            except (OSError, ValueError, sqlite3.Error) as error:
                cache_path, cache_note = None, f"answer cache unusable: {error}"
        ranks = file_ranks(connection)
        for group in (population, bound):
            group.sort(key=lambda row: (known.get(row[1]) == hashes.get(row[1]),
                                        ((_unpack(row[2]).get("parts") or [""])[-1] not in callee_names),
                                        -ranks.get(row[1], 0.0),
                                        row[1], row[3] or 0, row[4] or 0, row[0]))

        def reusable(row):
            answer = cached.get(row[0])
            if answer is None or answer["file"] != row[1] or answer["file_digest"] != digests.get(row[1]):
                return None
            if any(hashes.get(rel) != digest for rel, digest in json.loads(answer["targets"]).items()):
                return None
            return answer

        reused, pending, unchecked = [], [], []
        for row in population + bound:
            answer = reusable(row)
            if answer is None:
                (unchecked if row[0] in lexical else pending).append(row)
            else:
                reused.append((row, answer))
        # The unresolved calls come first: a limit spends its questions on them.
        selected = pending[::stride] + unchecked[::stride]
        if limit is not None:
            selected = selected[:limit]

        kept_entries, kept_edges, kept_holes, kept_reports = {}, [], [], {}
        if destination.is_file():
            previous, previous_binding, previous_reason = read_edge_store(destination, store)
            if previous_reason is None:
                kept_entries = {language: entry for language, entry in
                                (previous_binding.get("languages") or {}).items() if language not in counts}
                kept_edges = [edge for edge in previous if edge.get("language") in kept_entries]
                kept_holes = [hole for hole in read_edge_holes(destination) if hole["language"] in kept_entries]
                kept_reports = {key: value for key, value in (previous_binding.get("engine_reports") or {}).items()
                                if key in {entry["engine"] for entry in kept_entries.values()}}

        edges: list[dict] = []
        answers: list[dict] = []
        skipped_position = 0
        latencies: list[float] = []
        declarations: dict[str, dict] = {}
        source_lines: dict[str, list[str]] = {}
        progress = {"probed": False, "probe_elapsed": 0.0, "saved": 0, "published": time.perf_counter(),
                    "binding": None, "verified_after": None, "reused_identity": None, "written": None}

        def lines_for(rel):
            if rel not in source_lines:
                source_lines[rel] = source_paths[rel].read_text(encoding="utf-8").split("\n")
            return source_lines[rel]

        contracts: dict[str, bool] = {}

        def contract(identity):
            """Whether a declaration is a method an interface, a trait or a type declares."""
            if identity not in contracts:
                row = connection.execute("SELECT payload FROM sem_declarations WHERE id=?", (identity,)).fetchone()
                contracts[identity] = bool(row and (_unpack(row[0]) or {}).get("contract"))
            return contracts[identity]

        def count(language, verdict, reference_id=None, asked=False):
            """One verdict on an unresolved call; the bound calls are counted in `checked`.

            A call named by `reference_id` gets no edge: a hole, `engine-unresolved` once asked, else `not-asked`.
            """
            if reference_id is not None:
                holes_of[reference_id] = ("engine-unresolved" if asked else "not-asked", verdict)
            if reference_id in lexical:
                return
            verdicts = counts[language]["verdicts"]
            verdicts[verdict] = verdicts.get(verdict, 0) + 1

        def record(reference_id, rel, language, payload, verdict, target_id, resolver, line, column):
            """One answer as an edge row: the end class in `verdict`, the engine's own verdict in `payload.detail`."""
            if reference_id in lexical:
                # The engine agrees with the lexical target, names another declaration or a place outside.
                checked = counts[language]["checked"]
                if verdict.startswith("edge-") and target_id:
                    checked["same" if target_id == lexical[reference_id] else "corrected"] += 1
                elif verdict == "external-definition":
                    checked["external"] += 1
                else:
                    holes_of[reference_id] = ("engine-unresolved", verdict)
                    return
            else:
                count(language, verdict)
                if verdict.startswith("edge-") and target_id:
                    counts[language]["confirmed"] += 1
                elif verdict in CANDIDATE_REASONS:
                    counts[language]["candidates"] += 1
                else:
                    # Any other verdict, an outside place included, is a hole: the view reads the call as today.
                    holes_of[reference_id] = ("engine-unresolved", verdict)
                    return
            sure = verdict.startswith("edge-") or verdict == "external-definition"
            confidence = "confirmed" if sure else "uncertain"
            doubt = {} if sure else {"uncertain": {"reason": verdict, "candidates": []}}
            edges.append({
                "reference_id": reference_id, "file": rel, "language": language, "kind": "call",
                # The stored payload already qualifies its caller with its file.
                "caller": payload.get("caller"), "l0": line, "c0": column,
                "verdict": "project-callable" if verdict.startswith("edge-") else POSITION_ENDS[verdict],
                "target_id": target_id, "symbol": None, "resolver": resolver, "confidence": confidence,
                "payload": {**payload, "resolver": resolver, "confidence": confidence, "reason": f"engine-{verdict}",
                            "detail": verdict, "chain": [], **doubt},
            })

        def identity():
            return engine.identity() if progress["probed"] else (progress["reused_identity"] or engine.name)

        def holes():
            answered = {edge["reference_id"] for edge in edges}
            return [{"reference_id": reference_id, "file": rel, "language": language, "kind": kind, "l0": l0, "c0": c0,
                     "class": holes_of.get(reference_id, ("not-asked",))[0], "resolver": identity(),
                     "reason": holes_of[reference_id][1] if reference_id in holes_of else
                     "read" if kind == "read" else "not-selected" if resolution in ("unresolved", "resolved")
                     else resolution}
                    for reference_id, rel, kind, l0, c0, language, resolution in sites if reference_id not in answered]

        def publish(partial):
            """Verify the sources, then write the store and the new answers; a failure or None."""
            try:
                _root, _paths, verified_after = verify_sources(store, languages)
                edge_destination(destination, manifest, source_paths)
            except (OSError, ValueError) as error:
                return {"reason": str(error), "stage": "after-inference"}
            created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            entries = {}
            for language, numbers in counts.items():
                if numbers["confirmed"] + numbers["candidates"]:
                    no_edges_reason = None
                elif not numbers["population"]:
                    no_edges_reason = "no-unresolved-calls"
                elif not numbers["selected"] or not numbers["asked"] + numbers["reused"]:
                    no_edges_reason = "not-sampled"
                else:
                    no_edges_reason = "no-project-targets"
                complete = numbers["selected"] >= numbers["population"]
                entries[language] = {
                    "engine": identity(), "state": "partial" if partial else "fresh" if complete else "sampled",
                    **numbers, "stride": stride, "verdicts": dict(sorted(numbers["verdicts"].items())),
                    "excluded_classes": dict(sorted(numbers["excluded_classes"].items())),
                    "no_edges_reason": no_edges_reason, "created_at": created,
                    "source_verification": {"before_inference": verified_before, "after_inference": verified_after}}
            report = engine.report() if hasattr(engine, "report") else {}
            binding = store_binding(store, manifest, fingerprint, {**kept_entries, **entries},
                                    {**kept_reports, identity(): report})
            progress.update(binding=binding, verified_after=verified_after, published=time.perf_counter())
            if dry_run:
                return None
            try:
                progress["written"] = write_edge_store(destination, kept_edges + edges, binding, kept_holes + holes())
            except (OSError, sqlite3.Error, ValueError) as error:
                return {"reason": f"could not publish the engine edge store: {error}", "stage": "write"}
            if cache_path is not None:
                try:
                    save_answers(cache_path, context, engine.name, answers[progress["saved"]:])
                    progress["saved"] = len(answers)
                except (OSError, sqlite3.Error) as error:
                    progress["cache_error"] = f"answer cache not written: {error}"
            return None

        for (reference_id, rel, blob, _l0, _c0, _l1, _c1, language), answer in reused:
            if reference_id in lexical:
                counts[language]["checked"]["asked"] += 1
            else:
                counts[language]["selected"] += 1
                counts[language]["reused"] += 1
            progress["reused_identity"] = progress["reused_identity"] or answer["resolver"]
            record(reference_id, rel, language, _unpack(blob), answer["verdict"], answer["target_id"],
                   answer["resolver"], answer["line"], answer["column"])

        if reused and selected and not dry_run:
            # The reusable part of the graph is usable at once, before the engine starts.
            early = publish(partial=True)
            if early is not None:
                return {"engine": identity(), "available": False, "languages": list(languages),
                        "edges_store": None, **early}
        failure = None
        try:
            for reference_id, rel, blob, l0, c0, l1, c1, language in selected:
                counts[language]["selected"] += reference_id not in lexical
                payload = _unpack(blob)
                parts = payload.get("parts") or []
                if not parts:
                    # A reference with no parts is a dynamic callee, not a position this
                    # command failed to find: the verdict keeps the payload's own reason
                    # so the declared coverage says what was really asked about.
                    count(language, payload.get("reason") or "dynamic-reference", reference_id)
                    continue
                if not l0 or not l1:
                    count(language, "no-position", reference_id)
                    continue
                try:
                    lines = lines_for(rel)
                except (OSError, UnicodeError):
                    lines = []
                if not 1 <= l0 <= l1 <= len(lines):
                    count(language, "no-position", reference_id)
                    continue
                column = callee_column(lines[l1 - 1], [l0, c0, l1, c1], parts[-1])
                if column is None:
                    skipped_position += 1
                    count(language, "position-unverified", reference_id)
                    continue
                if not progress["probed"]:
                    # The engine starts only once a position needs it.
                    started = time.perf_counter()
                    try:
                        ready, reason = engine.probe()
                    except MemoryError:
                        ready, reason = False, "MemoryError while the engine started"
                    progress["probe_elapsed"] = time.perf_counter() - started
                    if not ready:
                        return {"engine": engine.name, "available": False, "reason": reason,
                                "install": getattr(engine, "install", None), "languages": list(languages),
                                "memory_exhausted": bool(MEMORY_EXHAUSTED.search(reason or ""))}
                    progress["probed"] = True
                started = time.perf_counter()
                (counts[language]["checked"] if reference_id in lexical else counts[language])["asked"] += 1
                try:
                    inferred = engine.definitions(source_paths[rel], l1, column)
                except (EngineFailure, MemoryError):
                    raise
                except Exception as error:
                    count(language, f"infer-error:{type(error).__name__}", reference_id, asked=True)
                    continue
                finally:
                    latencies.append(time.perf_counter() - started)
                try:
                    witnesses = list(inferred)

                    def follow(location):
                        try:
                            children = engine.definitions(Path(location.module_path), location.line, location.column)
                        except (EngineFailure, MemoryError):
                            raise
                        except Exception:
                            # An unsupported follow-up is missing evidence, never external.
                            return []
                        witnesses.extend(children)
                        return children

                    def table_for(name):
                        return symbol_table(connection, name, "\n".join(lines_for(name)))

                    verdict, target = grade_all(inferred, inventory, declarations, store_root, table_for, follow=follow)
                    if hasattr(engine, "implementations") and (
                            verdict in ("project-not-a-symbol", "ambiguous-target")
                            or (verdict.startswith("edge-") and target and contract(target["id"]))):
                        # The declaration is a contract or a value: the target is the one place that implements it,
                        # when no implementation falls outside the project's declarations.
                        try:
                            implemented = list(engine.implementations(source_paths[rel], l1, column))
                        except (EngineFailure, MemoryError):
                            raise
                        except Exception:
                            implemented = []
                        witnesses.extend(implemented)
                        concrete, elsewhere = {}, False
                        for item in implemented:
                            found_verdict, found = grade(item, inventory, declarations, store_root, table_for)
                            if not (found_verdict.startswith("edge-") and found):
                                elsewhere = True
                            elif not contract(found["id"]):
                                concrete[found["id"]] = (found_verdict, found)
                        if len(concrete) == 1 and not elsewhere:
                            verdict, target = next(iter(concrete.values()))
                except (OSError, UnicodeError) as error:
                    failure = {"reason": f"target source became unavailable during inference: {error}",
                               "stage": "after-inference"}
                    break
                target_id = (target or {}).get("id")
                record(reference_id, rel, language, payload, verdict, target_id, engine.identity(), l1, column)
                if context is not None:
                    answers.append({"context": context, "engine": engine.name, "reference_id": reference_id,
                                    "file": rel, "file_hash": hashes.get(rel) or "", "file_digest": digests.get(rel, ""),
                                    "verdict": verdict, "target_id": target_id,
                                    "targets": answer_targets(witnesses, store_root, hashes),
                                    "resolver": engine.identity(), "line": l1, "column": column})
                if not dry_run and time.perf_counter() - progress["published"] >= PUBLISH_SECONDS:
                    failure = publish(partial=True)
                    if failure is not None:
                        break
        except EngineFailure as error:
            failure = {"reason": str(error), "stage": "inference",
                       "memory_exhausted": bool(MEMORY_EXHAUSTED.search(str(error)))}
        except MemoryError:
            failure = {"reason": "MemoryError during inference", "stage": "inference", "memory_exhausted": True}
        finally:
            closer = getattr(engine, "close", None)
            if closer is not None:
                closer()
        if failure is not None and failure["stage"] == "inference":
            # What the engine proved before it failed stays, and the next pass resumes from it.
            publish(partial=True)
        if failure is None:
            failure = publish(partial=False)
        if failure is not None:
            return {"engine": identity(), "available": False, "languages": list(languages),
                    "edges_store": None, **failure}
        binding = progress["binding"]
        summary = resolution_summary(connection, binding)
    latencies.sort()
    entries = {language: binding["languages"][language] for language in counts}
    asked = sum(entry["asked"] for entry in entries.values())
    totals = {key: sum(entry[key] for entry in entries.values())
              for key in ("population", "selected", "reused", "confirmed", "candidates")}
    verdicts: dict[str, int] = {}
    excluded_classes: dict[str, int] = {}
    for entry in entries.values():
        for key, value in entry["verdicts"].items():
            verdicts[key] = verdicts.get(key, 0) + value
        for key, value in entry["excluded_classes"].items():
            excluded_classes[key] = excluded_classes.get(key, 0) + value
    reasons = {entry["no_edges_reason"] for entry in entries.values()} - {None}
    engine_report = engine.report() if hasattr(engine, "report") else {}
    return {
        "engine": identity(),
        "available": True,
        "project_root": project_root.as_posix(),
        **(engine_report if "environments" in engine_report else
           {"environments": [], "unusable_environments": [], "inference_modes": {}, **engine_report}),
        "languages": entries,
        "population": totals["population"],
        "population_language": languages[0] if len(languages) == 1 else "multi",
        "selected": totals["selected"],
        "asked": asked,
        "reused": totals["reused"],
        "answer_cache": cache_path.as_posix() if cache_path else None,
        **({"answer_cache_note": progress.get("cache_error") or cache_note}
           if progress.get("cache_error") or cache_note else {}),
        "stride": stride,
        "confirmed_edges": totals["confirmed"],
        "candidates": totals["candidates"],
        "no_edges_reason": None if totals["confirmed"] or totals["candidates"] else
        (reasons.pop() if len(reasons) == 1 else "no-project-targets"),
        "position_unverified": skipped_position,
        "excluded_classes": excluded_classes,
        "resolution": summary,
        "source_verification": {"before_inference": verified_before,
                                "after_inference": progress["verified_after"]},
        "verdicts": verdicts,
        "probe_init_elapsed_ms": round(1000 * progress["probe_elapsed"], 1),
        "inference_elapsed_ms": round(1000 * sum(latencies), 1),
        "total_elapsed_ms": round(1000 * (time.perf_counter() - run_started), 1),
        "latency_mean_ms": round(1000 * sum(latencies) / len(latencies), 1) if latencies else None,
        "latency_p95_ms": round(1000 * latencies[math.ceil(len(latencies) * 0.95) - 1], 1) if latencies else None,
        "inference_only_extrapolation": {
            "estimated_ms": round(1000 * sum(latencies) / asked * totals["population"], 1) if asked else None,
            "asked": asked, "selected": totals["selected"], "population": totals["population"], "stride": stride,
            "sampling_bias": "References are ordered deterministically by value: edited and new files first, then files by rank, "
                             "then by position; reused answers are taken first, the rest sampled by stride, "
                             "then truncated by limit. Dynamic or unverified selected references receive no "
                             "inference request.",
            "assumption": "Every population reference requires one request at the observed mean request cost.",
            "cost_scope": "Engine inference only; probe/init, source verification, grading and output writing excluded.",
        },
        "dry_run": dry_run,
        "edges_store": progress["written"].as_posix() if progress["written"] else None,
        "coverage": f"{asked + totals['reused']} of {totals['population']} unresolved call references"
                    + (f" ({totals['reused']} reused)" if totals["reused"] else ""),
        "note": "Engine edges live in a derived store bound to this snapshot; the "
                "snapshot itself is unchanged. Every edge names payload.resolver, so "
                "engine edges are never counted together with builtin-lexical ones.",
    }


ENVIRONMENT_MIN_FREE = 3 * 2**30
_REQUIREMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[^\]]*\])?\s*([<>=!~].*)?$")


def python_manifests(project_root: Path, names) -> list[str]:
    """The snapshot's files that declare Python packages: lockfiles, pyproject and requirements files."""
    found = []
    for name in names:
        base = PurePosixPath(name).name
        if base in ("pyproject.toml", "uv.lock") or (base.startswith("requirements") and base.endswith(".txt")):
            if (project_root / name).is_file():
                found.append(name)
    return sorted(found)


def _declared_requirements(project_root: Path, manifests: list[str], uv: str) -> list[str]:
    """Requirement lines the manifests declare, read without running anything of the project.

    A lockfile is exported from a copy of its two files; a pyproject without one gives
    its dependency tables; a requirements file gives its package lines. Editable
    installs, local paths, URLs and includes are left out: they are project code or
    need it.
    """
    import tomllib
    lines: list[str] = []
    for name in manifests:
        path, base = project_root / name, PurePosixPath(name).name
        if base == "uv.lock":
            continue
        if base == "pyproject.toml":
            exported = None
            if (path.parent / "uv.lock").is_file():
                with tempfile.TemporaryDirectory(prefix="daodan-lock-") as copy:
                    for item in ("pyproject.toml", "uv.lock"):
                        shutil.copyfile(path.parent / item, Path(copy) / item)
                    done = subprocess.run(
                        [uv, "export", "--frozen", "--no-emit-project", "--no-emit-workspace", "--all-groups",
                         "--all-extras", "--no-hashes", "--no-header", "--format", "requirements-txt"],
                        cwd=copy, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)
                    exported = done.stdout.splitlines() if done.returncode == 0 else None
            if exported is None:
                try:
                    data = tomllib.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    data = {}
                project = data.get("project") or {}
                exported = list(project.get("dependencies") or [])
                for table in (project.get("optional-dependencies") or {}, data.get("dependency-groups") or {}):
                    for values in table.values():
                        exported += [value for value in values if isinstance(value, str)]
                poetry = ((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}
                exported += [package for package in poetry if package.lower() != "python"]
            lines += exported
        else:
            try:
                lines += path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                pass
    kept = []
    for line in lines:
        line = line.split(" #")[0].strip()
        if line and not line.startswith(("#", "-", ".", "/")) and "://" not in line and " @ " not in line \
                and _REQUIREMENT.match(line.split(";")[0].strip()):
            kept.append(line)
    return sorted(set(kept))


def python_environment(project_root: Path, names) -> Path | None:
    """The project's declared Python packages in an environment of the shared directory.

    Built once per set of manifests and interpreter, from wheels only: no package
    build script and no project code runs, and nothing is written into the project.
    None when the project declares no package, uv is missing, the disk is short or
    no package could be installed.
    """
    project_root = Path(project_root).resolve()
    manifests = python_manifests(project_root, names)
    uv = shutil.which("uv")
    if not manifests or uv is None:
        return None
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    digest = hashlib.sha256(f"{version}\0{_platform()}\0".encode("utf-8"))
    for name in manifests:
        digest.update(name.encode("utf-8") + b"\0" + (project_root / name).read_bytes() + b"\0")
    destination = shared_cache_dir() / "python" / digest.hexdigest()[:16]
    marker = destination / "daodan-environment.json"
    if marker.is_file():
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(destination.parent).free
    if free < ENVIRONMENT_MIN_FREE:
        print(f"the project's Python packages were not installed: {free / 2**30:.1f} GB free in "
              f"{destination.parent}, at least {ENVIRONMENT_MIN_FREE / 2**30:.0f} GB are needed", flush=True)
        return None
    requirements = _declared_requirements(project_root, manifests, uv)
    if not requirements:
        return None
    print(f"installing the project's Python packages into {destination} (first use)", flush=True)
    shutil.rmtree(destination, ignore_errors=True)

    def run(*arguments, timeout=1800):
        return subprocess.run([uv, *arguments], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)

    if run("venv", str(destination), "--python", version).returncode != 0:
        return None
    install = ("pip", "install", "--python", str(destination), "--only-binary", ":all:")
    listed = destination / "daodan-requirements.txt"
    listed.write_text("\n".join(requirements) + "\n", encoding="utf-8")
    installed = len(requirements)
    if run(*install, "-r", str(listed)).returncode != 0:
        # One package without a wheel must not cost the others.
        installed = sum(1 for requirement in requirements if run(*install, requirement, timeout=600).returncode == 0)
    if installed == 0:
        shutil.rmtree(destination, ignore_errors=True)
        return None
    marker.write_text(json.dumps({"manifests": manifests, "requirements": len(requirements), "installed": installed,
                                  "python": version}) + "\n", encoding="utf-8")
    print(f"installed {installed} of {len(requirements)} declared Python packages", flush=True)
    return destination


def default_environments(project_root: Path) -> list[Path]:
    """The analyzed project's own environments, when it has one where projects keep it."""
    found = []
    for candidate in (project_root / ".venv", project_root / "venv"):
        if (candidate / "pyvenv.cfg").is_file():
            found.append(candidate)
    active = os.environ.get("VIRTUAL_ENV")
    if active and (Path(active) / "pyvenv.cfg").is_file() and Path(active) not in found:
        found.append(Path(active))
    return found


def _process_alive(pid: int) -> bool:
    if type(pid) is not int or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def pass_state(manifest: Path) -> dict | None:
    """The pass in flight or the last one finished beside the manifest, without opening it.

    `running` while the recorded process lives; `finished` after a pass that
    reported, with its per-language outcomes; `stopped` after `stop_pass`;
    `failed` when it ended without a report. None when no pass ever started.
    """
    manifest = Path(manifest)
    running = manifest.with_name(RUNNING_NAME)
    report = manifest.with_name(REPORT_NAME)
    if running.is_file():
        try:
            marker = json.loads(running.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            marker = {}
        if _process_alive(marker.get("pid")):
            return {"state": "running", "pid": marker.get("pid"), "started_at": marker.get("started_at")}
    if report.is_file():
        try:
            last = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            last = {}
        if last.get("stopped"):
            return {"state": "stopped", "reason": last.get("reason")}
        return {"state": "finished", "languages": last.get("languages") or {}}
    if running.is_file():
        return {"state": "failed", "reason": "the engine pass ended without a report; see " + LOG_NAME}
    return None


STATE_ORDER = ("missing", "failed", "sampled", "fresh", "unavailable")


def edge_state(manifest: Path) -> dict:
    """Report the derived edge store and its pass without touching either.

    `languages` holds one state per snapshot language an engine covers: `fresh`
    or `sampled` from the store, `unavailable` or `failed` from the last pass,
    `running` while a pass may still reach it, `missing` otherwise. The overall
    state is `running`, `stopped` or `stale` (store bound to another revision)
    when one applies, else the first of missing, failed, sampled, fresh and
    unavailable that a language holds. Every state carries `resolution`.
    """
    manifest = Path(manifest)
    store_path = default_edge_store(manifest)
    base = {"edges_store": store_path.as_posix()}
    with open_snapshot(manifest) as store:
        if store.format != "sqlite" or store.connection is None:
            return {**base, "state": "unavailable", "format": store.format,
                    "reason": "a JSON manifest holds no reference table"}
        binding, stale = None, None
        if store_path.is_file():
            _edges, loaded, reason = read_edge_store(store_path, store)
            binding, stale = (loaded, None) if reason is None else (None, reason)
        last = pass_state(manifest) or {}
        running = last.get("state") == "running"
        entries = (binding or {}).get("languages") or {}
        outcomes = last.get("languages") or {}
        languages = {}
        for language in snapshot_languages(store.connection):
            if language not in ENGINE_LANGUAGES:
                continue
            if language in entries:
                entry = entries[language]
                state, outcome = entry["state"], outcomes.get(language) or {}
                if state == "partial":
                    # A pass publishes as it goes: running, then what its stage ended as.
                    state = "running" if running else                         outcome["state"] if outcome.get("state") in ("failed", "unavailable") else "sampled"
                languages[language] = {"state": state, "engine": entry["engine"],
                                       "answered": entry.get("asked", 0) + entry.get("reused", 0),
                                       "population": entry.get("population", 0)}
                if state in ("failed", "unavailable") and outcome.get("reason"):
                    languages[language]["reason"] = outcome["reason"]
            elif language in outcomes and not running and outcomes[language]["state"] not in ("fresh", "sampled"):
                # Only the store proves edges; a report can only say why there are none.
                languages[language] = dict(outcomes[language])
            elif last.get("state") == "failed":
                languages[language] = {"state": "failed", "reason": last.get("reason")}
            else:
                languages[language] = {"state": "running" if running else "missing"}
        if running:
            result = {**base, "state": "running", "pid": last.get("pid"), "started_at": last.get("started_at")}
        elif last.get("state") == "stopped":
            result = {**base, "state": "stopped", "reason": last.get("reason")}
        elif stale is not None:
            result = {**base, "state": "stale", "reason": stale}
        else:
            states = {value["state"] for value in languages.values()}
            state = next((name for name in STATE_ORDER if name in states), "fresh")
            result = {**base, "state": state}
            first = next((value for value in languages.values() if value["state"] == state), {})
            for key in ("reason", "install"):
                if first.get(key):
                    result[key] = first[key]
            if state == "missing" and "reason" not in result:
                result["reason"] = "no engine pass has run for this snapshot"
        if binding is not None:
            result.update(engine=binding.get("engine"), created_at=binding.get("created_at"))
        result["languages"] = languages
        result["resolution"] = resolution_summary(store.connection, binding)
        return result


class EngineSpec(NamedTuple):
    """One engine of the derived pass: its languages and what its stage environment needs."""

    name: str
    languages: tuple[str, ...]
    requirements: tuple[str, ...]
    module: str
    install: str
    environment: dict


ENGINES = (
    EngineSpec("jedi", ("python",), ("jedi>=0.19",), "jedi", ENGINE_INSTALL, {}),
    # multilspy pins jedi-language-server, which would downgrade Jedi: each engine
    # runs in an environment of its own.
    EngineSpec("typescript", ("typescript", "javascript", "vue", "svelte"), ("multilspy==0.1.1",), "multilspy",
               "install uv, which gives the pass multilspy and its pinned typescript-language-server", {}),
    EngineSpec("java", ("java",), ("multilspy==0.1.1",), "multilspy",
               "install uv, which gives the pass multilspy and its pinned Eclipse JDT LS", {}),
    # Kotlin needs nothing in Python: its engine is a JVM process that installs itself.
    EngineSpec("kotlin", ("kotlin",), (), "json", "install uv, which runs the pass", {}),
    EngineSpec("rust", ("rust",), ("multilspy==0.1.1",), "multilspy",
               "install uv, which gives the pass multilspy; rust-analyzer installs itself", {}),
    EngineSpec("go", ("go",), ("multilspy==0.1.1",), "multilspy",
               "install uv, which gives the pass multilspy; Go and gopls install themselves", {}),
)
ENGINE_LANGUAGES = {language: spec for spec in ENGINES for language in spec.languages}
# One engine runs at a time, and only with this much memory free.
ENGINE_MIN_FREE = 2 * 2**30


def build_engine(name: str, project_root: Path, environments: list[Path], scip_index: list[Path] = ()):
    if name == "scip":
        return ScipEngine(project_root, list(scip_index))
    if name == "typescript":
        return TypeScriptEngine(project_root)
    if name == "java":
        return JavaEngine(project_root)
    if name == "kotlin":
        return KotlinEngine(project_root)
    if name == "rust":
        return RustEngine(project_root)
    if name == "go":
        return GoEngine(project_root)
    return JediEngine(project_root, environments)


def stage_command(spec: EngineSpec, manifest: Path, report_path: Path, environments: list[Path],
                  *, offline: bool = False) -> list[str] | None:
    """The command that runs one engine's stage with the snapshot's parser set.

    uv gives the stage an environment with the engine's requirements plus this
    interpreter's Python minor and exact parser packages, so the stage reproduces
    the parser fingerprint of the snapshot whichever environment wrote it, and the
    environment lives exactly as long as the stage. `offline` keeps uv from the
    network, for an environment already in its cache. Without uv, this interpreter
    runs the stage when it can import the engine. None when neither can.
    """
    import snapshot
    script = [str(Path(__file__).resolve()), str(manifest), "--engine", spec.name, "--compact",
              "--report-out", str(report_path)]
    if spec.name == "jedi":
        for path in environments:
            script.extend(["--environment", str(path)])
    uv = shutil.which("uv")
    if uv:
        pins = []
        for package in snapshot.PARSER_PACKAGES:
            try:
                pins.extend(["--with", f"{package}=={metadata.version(package)}"])
            except metadata.PackageNotFoundError:
                continue
        requirements = [item for requirement in spec.requirements for item in ("--with", requirement)]
        return [uv, "run", "--quiet", "--no-config", "--no-project", *(["--offline"] if offline else []),
                "--python", f"{sys.version_info[0]}.{sys.version_info[1]}",
                *requirements, *pins, "python", "-B", "-X", "faulthandler", *script]
    if importlib.util.find_spec(spec.module) is not None:
        # faulthandler puts a hard crash's traceback in the pass log.
        return [sys.executable, "-B", "-X", "faulthandler", *script]
    return None


def cached_offline(spec: EngineSpec, manifest: Path, report_path: Path, environments: list[Path]) -> bool:
    """Whether the stage's environment is already in uv's cache, so the stage runs with no network at all.

    Only the first stage of an engine on a machine reaches the package index.
    """
    command = stage_command(spec, manifest, report_path, environments, offline=True)
    if not command or "--offline" not in command:
        return False
    head = command[:command.index("python") + 1]
    try:
        return subprocess.run([*head, "-c", f"import {spec.module}"], stdin=subprocess.DEVNULL,
                              capture_output=True, timeout=120).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def engine_command(manifest: Path, report_path: Path, environments: list[Path]) -> list[str]:
    """The detached pass: this interpreter runs one stage per engine, one after another."""
    command = [sys.executable, "-B", "-X", "faulthandler", str(Path(__file__).resolve()), str(manifest),
               "--pass", "--report-out", str(report_path)]
    for path in environments:
        command.extend(["--environment", str(path)])
    return command


def pass_plan(manifest: Path) -> tuple[list[tuple[EngineSpec, list[str]]], dict, str]:
    """The engines whose languages the snapshot holds, with the entries already fresh."""
    manifest = Path(manifest)
    with open_snapshot(manifest) as store:
        present = snapshot_languages(store.connection)
        digest = logical_digest(store)
        fresh = {}
        if default_edge_store(manifest).is_file():
            _edges, binding, reason = read_edge_store(default_edge_store(manifest), store)
            if reason is None:
                fresh = {language: entry for language, entry in (binding.get("languages") or {}).items()
                         if entry.get("state") == "fresh"}
    plan = [(spec, [language for language in spec.languages if language in present]) for spec in ENGINES]
    return [(spec, wanted) for spec, wanted in plan if wanted], fresh, digest


def run_pass(manifest: Path, report_path: Path, environments: list[Path]) -> dict:
    """Run each engine's stage in turn and record per language what came of it.

    A language already fresh in the store is not asked again. Before a stage the
    free memory is checked; after a stage that ran out of memory no other starts.
    The report is rewritten after every stage, so the state shows progress.
    """
    manifest = Path(manifest).resolve()
    plan, fresh, digest = pass_plan(manifest)
    report = {"pass": True, "manifest_digest": digest, "languages": {}, "engines": {},
              "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    outcomes = report["languages"]
    exhausted = None
    for spec, wanted in plan:
        if all(language in fresh for language in wanted):
            outcomes.update({language: {"state": "fresh", "engine": fresh[language]["engine"]} for language in wanted})
            continue
        free = free_memory()
        if exhausted:
            reason, state, install = f"not started: {exhausted}", "failed", None
        elif free is not None and free < ENGINE_MIN_FREE:
            reason, state, install = (f"{free / 2**30:.1f} GB of memory free; an engine starts with at least "
                                      f"{ENGINE_MIN_FREE / 2**30:.0f} GB"), "failed", None
        else:
            stage_report = manifest.with_name(f".engine-stage-{spec.name}.json")
            stage_report.unlink(missing_ok=True)
            command = stage_command(spec, manifest, stage_report, environments,
                                    offline=cached_offline(spec, manifest, stage_report, environments))
            if command is None:
                reason, state, install = f"neither uv nor {spec.module} is available to {sys.executable}", \
                    "unavailable", spec.install
            else:
                print(f"engine pass: {spec.name} for {', '.join(wanted)}", flush=True)
                completed = subprocess.run(command, stdin=subprocess.DEVNULL, cwd=str(SCRIPT_DIR),
                                           env={**os.environ, **spec.environment})
                try:
                    stage = json.loads(stage_report.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    stage = None
                stage_report.unlink(missing_ok=True)
                if stage is None:
                    reason, state, install = (f"the {spec.name} stage exited with code {completed.returncode} "
                                              f"without a report; see {LOG_NAME}"), "failed", None
                    stage = {"memory_exhausted": bool(MEMORY_EXHAUSTED.search(_log_tail(manifest)))}
                elif stage.get("available"):
                    reason, state, install = None, None, None
                else:
                    reason = stage.get("reason")
                    install = stage.get("install")
                    state = "unavailable" if install else "failed"
                report["engines"][spec.name] = compact_report(stage)
                if stage.get("memory_exhausted"):
                    exhausted = f"the {spec.name} engine ran out of memory"
                if state is None:
                    for language in wanted:
                        entry = (stage.get("languages") or {}).get(language) or {}
                        outcomes[language] = {"state": entry.get("state", "fresh"), "engine": stage.get("engine")}
                    _write_report(report_path, report)
                    continue
        for language in wanted:
            outcomes[language] = {key: value for key, value in
                                  (("state", state), ("engine", spec.name), ("reason", reason), ("install", install))
                                  if value is not None}
        _write_report(report_path, report)
    report["available"] = any(outcome["state"] in ("fresh", "sampled") for outcome in outcomes.values())
    report["finished_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_report(report_path, report)
    return report


def _log_tail(manifest: Path, size: int = 65536) -> str:
    try:
        with manifest.with_name(LOG_NAME).open("rb") as log:
            log.seek(0, os.SEEK_END)
            log.seek(max(log.tell() - size, 0))
            return log.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def _spawn_detached(command: list[str], log) -> subprocess.Popen:
    options = {"stdin": subprocess.DEVNULL, "stdout": log, "stderr": log, "cwd": str(SCRIPT_DIR),
               "close_fds": True}
    if os.name != "nt":
        return subprocess.Popen(command, start_new_session=True, **options)
    detached = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    try:
        # Outlive a host that closes its job object when the calling command ends.
        return subprocess.Popen(command, creationflags=detached | 0x01000000, **options)
    except OSError:
        # The job forbids breaking away: the pass lives as long as the host.
        return subprocess.Popen(command, creationflags=detached, **options)


def _terminate_tree(pid: int) -> None:
    """End the pass and the interpreter it started, which a plain kill would orphan."""
    if os.name == "nt":
        result = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True)
        if result.returncode and _process_alive(pid):
            raise OSError(result.stderr.strip() or result.stdout.strip())
        return
    os.killpg(pid, signal.SIGTERM)


def _write_report(path: Path, report: dict) -> None:
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_edges(manifest: Path, *, check: bool = False, environments: list[Path] | None = None) -> dict:
    """Start the pass unless `check`, when some engine language is neither fresh nor settled.

    The pass is a detached child (`engine_command`) that runs one stage per engine
    and leaves the store, its report and a log beside the manifest, so a run is
    usable at once and its graph gains each language's edges as its stage lands.
    `fresh`, `running`, `stopped` and `unavailable` start nothing: only a new
    snapshot reopens them. When no stage could start, the report says so and no
    process is spawned. Returns the state plus `action`: `none`, `reported` or `started`.
    """
    manifest = Path(manifest).resolve()
    before = edge_state(manifest)
    if before["state"] in ("fresh", "running", "stopped", "unavailable") or before.get("format") == "json":
        return {**before, "action": "none"}
    if check:
        return {**before, "action": "reported"}
    with open_snapshot(manifest) as store:
        project_root = (Path(store["root"]) / store["target"]).resolve()
    if project_root.is_file():
        project_root = project_root.parent
    environments = list(environments) if environments is not None else default_environments(project_root)
    report_path = manifest.with_name(REPORT_NAME)
    running_path = manifest.with_name(RUNNING_NAME)
    for leftover in (report_path, running_path):
        leftover.unlink(missing_ok=True)
    plan, fresh, digest = pass_plan(manifest)
    pending = [(spec, wanted) for spec, wanted in plan if not all(language in fresh for language in wanted)]
    if pending and all(stage_command(spec, manifest, report_path, environments) is None for spec, _ in pending):
        outcomes = {language: {"state": "fresh", "engine": entry["engine"]} for language, entry in fresh.items()}
        for spec, wanted in pending:
            outcomes.update({language: {"state": "unavailable", "engine": spec.name, "install": spec.install,
                                        "reason": f"neither uv nor {spec.module} is available to {sys.executable}"}
                             for language in wanted})
        _write_report(report_path, {"pass": True, "manifest_digest": digest, "available": False,
                                    "languages": outcomes, "engines": {}})
        return {**edge_state(manifest), "action": "none"}
    with manifest.with_name(LOG_NAME).open("ab") as log:
        try:
            child = _spawn_detached(engine_command(manifest, report_path, environments), log)
        except OSError as error:
            _write_report(report_path, {"pass": True, "manifest_digest": digest, "available": False,
                                        "languages": {language: {"state": "failed", "reason":
                                                                 f"could not start the engine pass: {error}"}
                                                      for _spec, wanted in pending for language in wanted},
                                        "engines": {}})
            return {**edge_state(manifest), "action": "none"}
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    running_path.write_text(json.dumps({"pid": child.pid, "started_at": started}) + "\n", encoding="utf-8")
    return {**edge_state(manifest), "action": "started"}


def reset_pass(manifest: Path) -> dict | None:
    """Clear the previous revision's pass before a snapshot replaces its manifest.

    A running pass holds the manifest open, which on Windows refuses the
    replacement, and its result would describe the old revision anyway. Ends it,
    removes its marker, report, stage reports and partial store, and returns what it found.
    """
    manifest = Path(manifest)
    last = pass_state(manifest)
    if last is not None and last["state"] == "running":
        _terminate_tree(last["pid"])
    for name in (RUNNING_NAME, REPORT_NAME):
        manifest.with_name(name).unlink(missing_ok=True)
    for pattern in (f".{default_edge_store(manifest).name}.*.partial", ".engine-stage-*.json"):
        for leftover in manifest.parent.glob(pattern):
            leftover.unlink(missing_ok=True)
    return last


def stop_pass(manifest: Path, reason: str) -> dict:
    """End a running pass with its stages and servers, and record it as stopped, so no repair restarts it."""
    manifest = Path(manifest).resolve()
    last = pass_state(manifest)
    if last is None or last["state"] != "running":
        return {"stopped": False, "state": (last or {}).get("state", "missing")}
    try:
        _terminate_tree(last["pid"])
    except OSError as error:
        return {"stopped": False, "state": "running", "reason": f"could not stop pid {last['pid']}: {error}"}
    _write_report(manifest.with_name(REPORT_NAME),
                  {"pass": True, "available": False, "stopped": True, "reason": f"stopped: {reason}"})
    # The report is the record now; a dying process must not read as running.
    manifest.with_name(RUNNING_NAME).unlink(missing_ok=True)
    return {"stopped": True, "state": "stopped", "pid": last["pid"]}


def compact_report(report: dict, *, report_out: Path | None = None) -> dict:
    """Bounded summary for CLI/coordinator callers when the full report is on disk."""
    summary = {
        key: report[key]
        for key in (
            "engine", "available", "reason", "stage", "install", "project_root", "languages",
            "population", "population_language", "selected", "asked", "reused", "answer_cache", "stride",
            "confirmed_edges", "candidates", "no_edges_reason", "position_unverified",
            "excluded_classes", "resolution", "verdicts", "memory_exhausted",
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
    parser.add_argument("manifest", type=Path, nargs="?", help="a snapshot's manifest.sqlite")
    parser.add_argument("--pass", dest="whole_pass", action="store_true",
                        help="run every engine the snapshot's languages need, one after another, as the "
                             "detached pass does")
    parser.add_argument("--engine", choices=("jedi", "typescript", "java", "kotlin", "rust", "go", "scip"), default="jedi")
    parser.add_argument("--scip-index", action="append", default=[], type=Path,
                        help="path to a precomputed SCIP index file (index.scip Protobuf or JSON) when --engine scip is used")
    parser.add_argument("--environment", action="append", default=[], type=Path,
                        help="a virtual-environment root of the project under analysis, "
                             "turned into a real Jedi environment; a bare site-packages "
                             "directory also works, in added_sys_path mode. Repeatable; "
                             "populated environments beat empty stubs, then the "
                             "nearest serving scope wins per file. Default: the project's "
                             ".venv or venv, or VIRTUAL_ENV, else with --pass one built in the "
                             "shared directory from the declared packages; `none` uses no environment")
    parser.add_argument("--limit", type=int, default=None,
                        help="ask about at most this many positions")
    parser.add_argument("--stride", type=int, default=1,
                        help="ask about every Nth position, for a deterministic sample")
    parser.add_argument("--dry-run", action="store_true",
                        help="ask every position and grade it, without reusing cached answers or writing")
    parser.add_argument("--out", type=Path, default=None,
                        help="where to write the derived edge store; default "
                             "engine-edges.sqlite beside the manifest")
    parser.add_argument("--report-out", type=Path, default=None,
                        help="optional file path for the complete JSON report")
    parser.add_argument("--compact", action="store_true",
                        help="emit a compact summary on stdout instead of the full report")
    args = parser.parse_args(argv)
    if args.manifest is None:
        parser.error("a manifest is required")
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
    declined = any(str(path) == "none" for path in args.environment)
    environments = [] if declined else [path.resolve() for path in (args.environment or default_environments(project_root))]
    if args.whole_pass:
        if not environments and not declined:
            # The detached pass is where a first install may take minutes.
            # Snapshot paths are relative to the snapshot root, which a target below it does not change.
            with open_snapshot(manifest) as store:
                names = [row[0] for row in store.connection.execute("SELECT file FROM sem_coverage")]
                snapshot_root = Path(store["root"]).resolve()
            try:
                prepared = python_environment(snapshot_root, names)
            except (OSError, subprocess.SubprocessError) as error:
                print(f"the project's Python packages were not installed: {error}", flush=True)
                prepared = None
            environments = [prepared] if prepared is not None else []
        report = run_pass(manifest, (args.report_out or manifest.with_name(REPORT_NAME)).resolve(), environments)
        print(json.dumps({key: report[key] for key in ("available", "languages")}, indent=2, sort_keys=True))
        return 0 if report.get("available") else 1
    engine = build_engine(args.engine, project_root, environments, [path.resolve() for path in args.scip_index])
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
