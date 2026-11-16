"""Vue and Svelte: no SCIP indexer reads their templates, so their calls are asked of typescript-language-server
at each call position (`position_stage.resolve_edges`), one virtual `.ts` or `.js` document per component. Only
the script blocks are read: a component with a template is a declared gap of its language (`unread`).

The adapter declares itself like the indexers (`indexers.analyzers`); `engine` in place of `index` makes its stage
the position stage. The stage runs under uv with multilspy, which pins the server release (`REQUIREMENTS`).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path, PurePosixPath

from engine_tools import executable_name, npm_key, npm_modules, package_directories
from language_servers import ENGINE_THREADS, SERVER_MEMORY_MB, MirroredEngine, _multilspy_pins

# The position stage's entry, which now serves no language: scip-typescript serves Vue and Svelte
# (`indexers/typescript.py`, `indexers/components.py`). Kept until a real run proves that path.
ENTRY, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "typescript", (), frozenset(), False
READ = ("vue", "svelte")  # what the engine reads when it is asked
MIN_FREE = 2 * 2**30  # one language server at a time, with this much memory free
REQUIREMENTS, IMPORT = ("multilspy==0.1.1",), "multilspy"
INSTALL = "install uv, which gives the pass multilspy and its pinned typescript-language-server"
NO_SCRIPT = "no script block: nothing of the component is read"
BLOCK_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>|<!--.*?-->", re.IGNORECASE | re.DOTALL)


def has_template(content: str, suffix: str) -> bool:
    """Whether a component holds markup outside its script and style blocks, comments aside: the `<template>`
    block of a `.vue` file, anything of a `.svelte` file. Its calls and bindings are in no script block."""
    rest = BLOCK_RE.sub("", content)
    return bool(re.search(r"<template\b", rest, re.IGNORECASE)) if suffix == ".vue" else bool(rest.strip())


def engine(project_dir: Path) -> "TypeScriptEngine":
    """The position engine of the stage."""
    return TypeScriptEngine(Path(project_dir))


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
    installed once into the shared directory (`npm_modules`, by Daodan's npm: the
    server and the install run on Daodan's Node, never the host's), and the server opens a
    mirror of the project in a temporary directory: a link per top-level directory,
    a copy of each top-level file and `node_modules` linked to the shared install,
    since TypeScript looks for packages only in the folders above a file.
    """

    name = "typescript"
    server_name = "typescript-language-server"
    # The stage answers for the entry's languages: the TypeScript and JavaScript sites are scip-typescript's.
    # A component imports files of those languages, so they are checked against the snapshot too (`reads`).
    languages, reads = READ, ("typescript", "javascript")
    language_ids = {".ts": "typescript", ".mts": "typescript", ".cts": "typescript", ".tsx": "typescriptreact",
                    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".jsx": "javascriptreact"}

    def pinned(self) -> dict:
        packages = [dependency["command"].split()[-1]
                    for dependency in _multilspy_pins("typescript_language_server")["runtimeDependencies"]]
        server = next(item for item in packages if item.startswith("typescript-language-server@"))
        return {"version": server.rsplit("@", 1)[1], "packages": packages}

    def prepare(self, home: Path) -> tuple[bool, str]:
        """The server installed on Daodan's Node (`runtime.node`), as scip-python is: the host's node and npm are
        never asked. What cannot be downloaded or installed is the reason, with what to do."""
        from indexers import runtime
        try:
            directory = runtime.node(self.project_root)
            if not (home / ".installed").is_file():
                runtime.room()
            with runtime.fetching(f"{self.server_name} {self.version}", "the npm registry"):
                self._install(home, lambda partial: runtime.npm_install(directory, partial, self.pinned()["packages"]))
        except runtime.Unavailable as error:
            self.install = error.install
            return False, error.reason
        return True, ""

    def command(self, home: Path) -> tuple[list[str], dict]:
        # The npm shim is a shell script on Windows; node runs the entry point itself.
        from indexers import runtime
        cli = home / "node_modules" / "typescript-language-server" / "lib" / "cli.mjs"
        node = runtime.node(self.project_root) / executable_name("node")
        return [str(node), str(cli), "--stdio"], {"UV_THREADPOOL_SIZE": str(ENGINE_THREADS)}

    def identity(self) -> str:
        """The stage's entry, then the server and its release: the pass reads a store entry as fresh only when it
        names the entry that serves the language (`engine_pass.from_source`)."""
        return f"{self.name}@{super().identity()}"

    def initialization_options(self) -> dict:
        return {"disableAutomaticTypingAcquisition": True, "maxTsServerMemory": SERVER_MEMORY_MB,
                "tsserver": {"useSyntaxServer": "never"}}

    def readiness_probe(self):
        return "__daodan_engine_probe__.ts", "function probe() {}\nprobe();\n", 1, 0

    mirror_skip = (".git", "node_modules")

    def probe(self) -> tuple[bool, str]:
        from indexers import runtime
        self.mirror = None
        try:  # the base's own first check: without multilspy no server starts, and nothing is downloaded for one
            import multilspy.lsp_protocol_handler.server  # noqa: F401
        except ImportError:
            return super().probe()
        try:
            npm = runtime.npm(runtime.node(self.project_root))  # Daodan's, for the packages and for the server
        except runtime.Unavailable as error:
            self.install = error.install
            return False, error.reason
        links = {}
        for directory in package_directories(self.project_root):
            try:
                modules = npm_modules(directory, npm=npm)
            except (OSError, subprocess.SubprocessError) as error:
                print(f"the project's JavaScript packages were not installed: {error}", flush=True)
                modules = None
            if modules is not None:
                folder = PurePosixPath(directory.relative_to(self.project_root).as_posix())
                links[(folder / "node_modules").as_posix()] = modules
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

    def unread(self, path: Path) -> str | None:
        """What of a file no adapter reads, None when it is read whole."""
        if has_template(path.read_text(encoding="utf-8", errors="replace"), path.suffix.lower()):
            return "template not read: calls and bindings in it are not sites"
        return None

    def nothing_read(self, path: Path) -> str | None:
        """Why nothing of a file is read, None when a script block of it is: a language none of whose files gives
        the engine anything is not fresh (`position_stage`)."""
        from languages.sfc import mask_non_script
        _text, _typed, has_script = mask_non_script(path.read_text(encoding="utf-8", errors="replace"))
        return None if has_script else NO_SCRIPT

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
