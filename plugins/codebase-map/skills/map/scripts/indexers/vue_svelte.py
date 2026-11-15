"""Vue and Svelte: no SCIP indexer reads their templates, so their calls are asked of typescript-language-server
at each call position (`resolve_edges.resolve_edges`), one virtual `.ts` or `.js` document per component.

The adapter declares itself like the indexers (`indexers.analyzers`); `engine` in place of `index` makes its stage
the position stage. The stage runs under uv with multilspy, which pins the server release (`REQUIREMENTS`).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path, PurePosixPath

# Declared before the engine's own imports: the pass reads them while it is still being built (`ENGINES`).
ENTRY, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "typescript", ("vue", "svelte"), frozenset(), False
MIN_FREE = 2 * 2**30  # one language server at a time, with this much memory free
REQUIREMENTS, IMPORT = ("multilspy==0.1.1",), "multilspy"
INSTALL = "install uv, which gives the pass multilspy and its pinned typescript-language-server"

from resolve_edges import (ENGINE_THREADS, SERVER_MEMORY_MB, MirroredEngine, _multilspy_pins,  # noqa: E402
                           npm_key, npm_modules, package_directories)


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
