"""
Usage Finder Module.

Finds where symbols are used across the codebase. Multi-language:
- Source file types: .py, .java, .js/.mjs/.cjs/.jsx, .ts/.tsx, .rs,
  .sql/.ddl/.dml, PL/SQL extensions (.pks, .pkb, .plsql, .pls, .pck, .prc,
  .fnc, .trg), and stylesheets (.css, .scss, .less).
- Import patterns are language-aware (Python `import`/`from`, Java `import`,
  JS/TS `import`/`require`; Rust, SQL/PL-SQL and stylesheets have no import
  pattern, so only raw usages are reported for them). Markup (.vue, .svelte,
  .html, .htm) is searched for raw usages too, because it applies CSS classes.
- Inheritance / call detection uses language-agnostic heuristics that work
  reasonably across the targeted set.

Uses ripgrep when available, then grep, then a pure-Python rglob fallback.
"""

from __future__ import annotations

import functools
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "UsageLocation",
    "UsageResult",
    "find_usages_with_grep",
    "find_importing_modules",
    "find_all_usages",
    "find_all_usages_batch",
    "is_excluded",
    "SOURCE_EXTENSIONS",
    "MARKUP_EXTENSIONS",
    "SEARCH_EXTENSIONS",
]

# Constants
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024
SUBPROCESS_TIMEOUT_SECONDS: int = 30

logger = logging.getLogger(__name__)


# Single source of truth for the languages package; no longer maintained
# separately here. Re-exported so callers that imported it from this module
# keep working.
from languages import SUPPORTED_EXTENSIONS as _SUPPORTED_EXTENSIONS_MAP
from tree_scope import Perimeter

SOURCE_EXTENSIONS: tuple[str, ...] = tuple(_SUPPORTED_EXTENSIONS_MAP.keys())

# Where a symbol is used without being imported: markup applies a CSS class
# (`class="dark-ambient-glow"`), so a usage search reads these too. They are not
# source files: nothing parses them, and analyze_file refuses them.
MARKUP_EXTENSIONS: tuple[str, ...] = (".vue", ".svelte", ".html", ".htm")
SEARCH_EXTENSIONS: tuple[str, ...] = SOURCE_EXTENSIONS + MARKUP_EXTENSIONS

DEFAULT_EXCLUDES = (
    "__pycache__",
    ".venv", "venv", ".tox",
    ".git",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    "target", "build", "dist", "out",
    "*.pyc", "*.class",
)

# `C:\...` / `c:/...`. Used to keep a Windows drive letter attached to its path
# when splitting `path:line:content` output from grep and ripgrep.
_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:[\\/]")


def is_excluded(path: Path, patterns: tuple[str, ...] | list[str]) -> bool:
    """
    Match exclude patterns against whole path segments, not substrings.

    A bare pattern ("out", "build") excludes a path only when it is one of the
    directory or file names, so `src/checkout.py`, `app/layout.ts`, and
    `docs/about/` survive. A leading-`*` pattern ("*.pyc") matches the file
    name's suffix.
    """
    parts = path.parts
    for pattern in patterns:
        if pattern.startswith("*"):
            if path.name.endswith(pattern[1:]):
                return True
        elif pattern in parts:
            return True
    return False


def validate_symbol(symbol: str) -> str:
    """
    Accept identifiers that are valid across the supported languages.

    Python/Java/JS/TS identifiers are `[A-Za-z_][A-Za-z0-9_]*` with optional
    dotted qualifiers; SQL allows dotted (schema.table) and quoted names but
    we restrict here to unquoted identifiers for safety. A hyphen is accepted
    after the first character, because a CSS class name (`dark-ambient-glow`)
    is the symbol a stylesheet exports; a leading hyphen stays refused, since
    grep would read it as an option.
    """
    if not re.match(r"^[A-Za-z_$][A-Za-z0-9_.$-]*$", symbol):
        raise ValueError(
            f"Invalid symbol name: {symbol!r}. Must be a valid identifier."
        )
    return symbol


@dataclass
class UsageLocation:
    file_path: str
    line_number: int
    line_content: str
    usage_type: str  # "import", "call", "inheritance", "reference"


@dataclass
class UsageResult:
    symbol: str
    source_file: str
    usages: list[UsageLocation]
    importing_modules: list[str]


def _classify_usage(line: str, symbol: str) -> str:
    stripped = line.strip()
    # Imports (Python, Java, JS/TS).
    if stripped.startswith(("from ", "import ", "@import ")) or " import " in stripped[:20]:
        return "import"
    if re.match(r"^\s*(?:const|let|var)\s+\w[\w{}\s,]*=\s*require\(", stripped):
        return "import"
    # Inheritance: class X extends Y, class X(Y), interface I extends J.
    if re.search(
        rf"\b(?:class|interface)\s+\w+(?:\s*<[^>]*>)?\s*"
        rf"(?:extends|implements|\()\s*[^{{(]*{re.escape(symbol)}",
        stripped,
    ):
        return "inheritance"
    # Function call: SYMBOL(.
    if re.search(rf"\b{re.escape(symbol)}\s*\(", stripped):
        return "call"
    return "reference"


def _searchable_files(search_path: Path, excludes: list[str]) -> list[Path]:
    """Select files before any backend reads source, including its fallbacks."""
    from snapshot import iter_files

    base = search_path.resolve() if search_path.is_dir() else search_path.resolve().parent
    return [path for path in iter_files(search_path)
            if path.suffix.lower() in SEARCH_EXTENSIONS
            and path.resolve().is_relative_to(base) and not is_excluded(path, excludes)]


def _search_output(tool: str, symbols: list[str], files: list[Path]) -> str | None:
    """Search bounded file arguments in batches below Windows' argv limit."""
    outputs = []
    batches: list[list[str]] = [[]]
    length = 0
    for path in files:
        value = str(path)
        if length + len(value) > 16000 and batches[-1]:
            batches.append([])
            length = 0
        batches[-1].append(value)
        length += len(value) + 3
    for batch in batches:
        if not batch:
            continue
        command = [tool, "-n", "--with-filename", "-F"] if tool == "rg" else [tool, "-nH", "-F"]
        for symbol in symbols:
            command += ["-e", symbol]
        command += ["--", *batch]
        try:
            result = subprocess.run(command, capture_output=True, text=True,
                                    timeout=SUBPROCESS_TIMEOUT_SECONDS)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        if result.returncode not in (0, 1):
            return None
        outputs.append(result.stdout)
    return "\n".join(outputs)


def find_usages_with_grep(
    symbol: str,
    search_paths: list[Path],
    exclude_patterns: list[str] | None = None,
) -> list[UsageLocation]:
    """
    Find usages of a symbol using ripgrep, falling back to grep, then to a
    pure-Python search.
    """
    symbol = validate_symbol(symbol)
    excludes = list(exclude_patterns or DEFAULT_EXCLUDES)
    usages: list[UsageLocation] = []

    for search_path in search_paths:
        if not search_path.exists():
            continue
        # Select the perimeter before a backend reads bytes. Filtering only
        # its output would still let it read ignored or hidden source files.
        perimeter = Perimeter(search_path)
        usages.extend(
            usage for usage in _search_one_path(symbol, search_path, excludes)
            if perimeter.covers(Path(usage.file_path))
        )

    return usages


def _search_one_path(symbol: str, search_path: Path, excludes: list[str]) -> list[UsageLocation]:
    """One search path, through the first backend that answers."""
    found: list[UsageLocation] = []

    files = _searchable_files(search_path, excludes)
    for tool in ("rg", "grep"):
        output = _search_output(tool, [symbol], files)
        if output is not None:
            _absorb_grep_lines(output, found, symbol)
            return found

    # 3. Pure-Python fallback.
    return _python_based_search(symbol, search_path, excludes, files=files)


def _split_grep_line(line: str) -> tuple[str, str, str] | None:
    """
    Split one `path:line:content` record from grep/ripgrep output.

    A Windows absolute path starts with its own colon (`C:\\src\\a.py`), so the
    drive prefix is held back before splitting; otherwise every absolute-path
    search parses the drive letter as the file name and the rest as a line
    number, and silently yields zero results.
    """
    drive = ""
    if _DRIVE_PREFIX_RE.match(line):
        drive, line = line[:2], line[2:]
    parts = line.split(":", 2)
    if len(parts) < 3:
        return None
    return drive + parts[0], parts[1], parts[2]


def _absorb_grep_lines(stdout: str, sink: list[UsageLocation], symbol: str) -> None:
    if not stdout:
        return
    for line in stdout.strip().split("\n"):
        if not line:
            continue
        parsed = _split_grep_line(line.rstrip("\r"))
        if parsed is None:
            continue
        file_path, line_no, raw_content = parsed
        try:
            line_num = int(line_no)
        except ValueError:
            continue
        content = raw_content.strip()
        sink.append(
            UsageLocation(
                file_path=file_path,
                line_number=line_num,
                line_content=content,
                usage_type=_classify_usage(content, symbol),
            )
        )


def _python_based_search(
    symbol: str,
    search_path: Path,
    exclude_patterns: list[str],
    *, files: list[Path] | None = None,
) -> list[UsageLocation]:
    selected = files if files is not None else _searchable_files(search_path, exclude_patterns)
    return _python_search_batch([symbol], selected)[symbol]


def _python_search_batch(symbols: list[str], files: list[Path]) -> dict[str, list[UsageLocation]]:
    """Read each allowed file once when neither external search tool answers."""
    found: dict[str, list[UsageLocation]] = {symbol: [] for symbol in symbols}
    for src in files:
        try:
            if src.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue
            content = src.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_num, line in enumerate(content.split("\n"), start=1):
            for symbol in symbols:
                if symbol in line:
                    found[symbol].append(UsageLocation(
                        file_path=str(src), line_number=line_num, line_content=line.strip(),
                        usage_type=_classify_usage(line, symbol),
                    ))
    return found


def _candidate_importer_files(
    symbol: str,
    source_module: str,
    search_path: Path,
    perimeter: Perimeter,
) -> list[Path]:
    """The same allowed inventory as the symbol search, restricted to source."""
    return [path for path in _searchable_files(search_path, list(DEFAULT_EXCLUDES))
            if path.suffix.lower() in SOURCE_EXTENSIONS and perimeter.covers(path)]


def find_importing_modules(
    symbol: str,
    source_module: str,
    search_paths: list[Path],
) -> list[str]:
    """
    Find files that import a specific symbol. Recognizes:

    - Python:     `from <mod> import ... <symbol> ...`, `import <mod>`
    - Java:       `import <mod>.<symbol>`, `import static <mod>.<symbol>`
    - JS / TS:    `import { <symbol> } from '<mod>'`, `import <symbol> from '<mod>'`,
                  `const { <symbol> } = require('<mod>')`
    """
    importing: list[str] = []
    seen: set[str] = set()

    py_patterns = [
        rf"from\s+{re.escape(source_module)}\s+import\s+.*\b{re.escape(symbol)}\b",
        rf"from\s+{re.escape(source_module)}\s+import\s+\*",
        rf"\bimport\s+{re.escape(source_module)}\b",
    ]
    java_patterns = [
        rf"\bimport\s+(?:static\s+)?{re.escape(source_module)}\.{re.escape(symbol)}\b",
        rf"\bimport\s+(?:static\s+)?{re.escape(source_module)}\.\*",
    ]
    js_patterns = [
        rf"\bimport\b[^;]*\b{re.escape(symbol)}\b[^;]*from\s+['\"]{re.escape(source_module)}['\"]",
        rf"\brequire\(['\"]{re.escape(source_module)}['\"]\)",
    ]
    all_patterns = [re.compile(p) for p in (py_patterns + java_patterns + js_patterns)]

    for search_path in search_paths:
        if not search_path.exists():
            continue
        perimeter = Perimeter(search_path)
        for src in _candidate_importer_files(symbol, source_module, search_path, perimeter):
            path_str = str(src)
            try:
                if src.stat().st_size > MAX_FILE_SIZE_BYTES:
                    continue
                content = src.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pattern in all_patterns:
                if pattern.search(content):
                    rel = str(src.relative_to(search_path.parent)) if search_path.parent else path_str
                    module = rel.replace("\\", "/")
                    if module not in seen:
                        seen.add(module)
                        importing.append(module)
                    break
    return importing


@functools.lru_cache(maxsize=4096)
def _resolved(path_str: str) -> str:
    """Resolved, case-normalized path string. Cached: called per usage hit."""
    try:
        resolved = Path(path_str).resolve()
    except OSError:
        resolved = Path(path_str).absolute()
    return os.path.normcase(str(resolved))


def _is_same_file(candidate: str, source_file: Path) -> bool:
    return _resolved(candidate) == _resolved(str(source_file))


def _resolve_project_root_and_paths(
    source_file: Path,
    project_root: Path | None = None,
) -> tuple[Path, list[Path]]:
    if project_root is None:
        current = source_file.parent
        while current != current.parent:
            if (
                (current / "pyproject.toml").exists()
                or (current / "package.json").exists()
                or (current / "pom.xml").exists()
                or (current / "build.gradle").exists()
                or (current / "build.gradle.kts").exists()
                or (current / ".git").exists()
            ):
                project_root = current
                break
            current = current.parent
        if project_root is None:
            project_root = source_file.parent

    search_paths: list[Path] = []
    for dir_name in ("src", "lib", "app", "packages", "modules", "core", "common"):
        candidate = project_root / dir_name
        if candidate.exists():
            search_paths.append(candidate)
    if not search_paths:
        search_paths = [project_root]
    return project_root, search_paths


def _source_module_for(source_file: Path, project_root: Path) -> str:
    try:
        rel_path = source_file.relative_to(project_root)
        source_module = str(rel_path).replace("\\", ".").replace("/", ".")
        if "." in source_file.name:
            source_module = source_module[: source_module.rfind(".")]
        return source_module
    except ValueError:
        return source_file.stem


def find_all_usages(
    symbol: str,
    source_file: Path,
    project_root: Path | None = None,
) -> UsageResult:
    """Find all usages of a symbol from a source file in the project."""
    symbol = validate_symbol(symbol)
    return find_all_usages_batch([symbol], source_file, project_root)[symbol]


def _graph_importing_modules(symbols: list[str], source_file: Path,
                             project_root: Path, manifest: dict | None) -> dict[str, list[str]]:
    """Match all requested bindings in one graph and one importer pass."""
    from snapshot import _python_module_candidates, build_manifest, resolved_imports

    manifest = build_manifest(project_root) if manifest is None else manifest
    root = Path(manifest["root"])
    target = (root / (manifest.get("target") or ".")).resolve()
    source = source_file.resolve()
    graph = resolved_imports(manifest)
    source_key = next((rel for rel in manifest["files"] if (root / rel).resolve() == source), None)
    importing = {symbol: [] for symbol in symbols}
    if source_key is None:
        return importing
    default_export = manifest["files"][source_key].get("default_export")
    for rel, modules in graph.items():
        if not any(source_key in targets for targets in modules.values()):
            continue
        entry = manifest["files"][rel]
        bindings = entry.get("import_bindings", [])
        for binding in bindings:
            if source_key not in modules.get(binding["module"], []):
                continue
            names = list(binding.get("names", []))
            default_import = binding.get("default_import")
            if default_import in names:
                # The default binding is a local alias, not an exported name.
                # Remove only its own occurrence: a combined import may also
                # name an unrelated export with the same spelling.
                names.remove(default_import)
            wildcard = any(name.startswith("*") for name in names)
            if not binding.get("from"):
                # Python import and a CommonJS module binding expose every
                # exported member; destructuring names only exposes its keys.
                wildcard = not names or not names[0].lstrip().startswith("{")
                if Path(rel).suffix.lower() == ".py":
                    wildcard = True
            elif Path(rel).suffix.lower() == ".py":
                # `from package import module` binds the module itself and
                # exposes its members, unlike `from module import Symbol`.
                candidates = _python_module_candidates(binding["module"], (root / rel).parent, target)
                wildcard = wildcard or any(
                    source == Path(candidate.rstrip("/") + "/" + name + ending).resolve()
                    for candidate in candidates for name in names if name != "*"
                    for ending in (".py", "/__init__.py")
                )
            declared = {part.strip().split(" as ")[0].split(":")[0].strip()
                        for name in names for part in name.strip("{} ").split(",")}
            for symbol in symbols:
                default_match = (default_import or "default" in declared) and symbol == default_export
                if (wildcard or symbol in declared or default_match) and rel not in importing[symbol]:
                    importing[symbol].append(rel)
    return importing


def find_all_usages_batch(
    symbols: list[str],
    source_file: Path,
    project_root: Path | None = None,
    *, manifest: dict | None = None,
) -> dict[str, UsageResult]:
    """
    Find usages for multiple symbols with one graph and one batched search.
    Every search backend receives only the current allowed source inventory.
    """
    valid_symbols: list[str] = []
    seen_sym: set[str] = set()
    for sym in symbols:
        try:
            validated = validate_symbol(sym)
        except ValueError:
            continue
        if validated not in seen_sym:
            seen_sym.add(validated)
            valid_symbols.append(validated)

    if not valid_symbols:
        return {}

    project_root, search_paths = _resolve_project_root_and_paths(source_file, project_root)
    source_module = _source_module_for(source_file, project_root)
    graph_language = source_file.suffix.lower() in {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
    if graph_language and manifest is None:
        from snapshot import build_manifest
        manifest = build_manifest(project_root)
    if manifest is not None:
        inventory_root = Path(manifest["root"])
        inventory_target = (inventory_root / (manifest.get("target") or ".")).resolve()
        base = inventory_target if inventory_target.is_dir() else inventory_target.parent
        perimeter = Perimeter(inventory_target)
        from snapshot import is_forbidden

        files = [inventory_root / rel for rel in manifest["files"]
                 if Path(rel).suffix.lower() in SEARCH_EXTENSIONS
                 and (inventory_root / rel).resolve().is_relative_to(base)
                 and (inventory_target.is_dir() or (inventory_root / rel).resolve() == inventory_target)
                 and perimeter.covers(inventory_root / rel)
                 and not is_forbidden(Path(rel).name)
                 and not is_excluded(inventory_root / rel, DEFAULT_EXCLUDES)]
    else:
        files = list(dict.fromkeys(path for search_path in search_paths
                                   for path in _searchable_files(search_path, list(DEFAULT_EXCLUDES))))
    files = [path for path in files if not _is_same_file(str(path), source_file)]

    # Attempt a single batched ripgrep pass across all symbols.
    by_symbol: dict[str, list[UsageLocation]] = {s: [] for s in valid_symbols}
    output = _search_output("rg", valid_symbols, files)
    if output is None:
        output = _search_output("grep", valid_symbols, files)
    if output is None:
        by_symbol = _python_search_batch(valid_symbols, files)
    else:
        for raw_line in output.splitlines():
            parsed = _split_grep_line(raw_line.rstrip("\r"))
            if parsed is None:
                continue
            fpath, line_no_str, raw_content = parsed
            try:
                line_num = int(line_no_str)
            except ValueError:
                continue
            if _is_same_file(fpath, source_file):
                continue
            content_stripped = raw_content.strip()
            for sym in valid_symbols:
                if sym in content_stripped:
                    by_symbol[sym].append(UsageLocation(
                        file_path=fpath, line_number=line_num, line_content=content_stripped,
                        usage_type=_classify_usage(content_stripped, sym),
                    ))

    if graph_language:
        importing = _graph_importing_modules(valid_symbols, source_file, project_root, manifest)
    else:
        importing = {sym: find_importing_modules(sym, source_module, search_paths) for sym in valid_symbols}

    return {
        sym: UsageResult(
            symbol=sym,
            source_file=str(source_file),
            usages=by_symbol[sym],
            importing_modules=importing[sym],
        )
        for sym in valid_symbols
    }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python usage_finder.py <symbol> [source_file]")
        sys.exit(1)

    symbol = sys.argv[1]
    source_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
    project_root = Path(".")
    result = find_all_usages(symbol, source_file, project_root)

    output = {
        "symbol": result.symbol,
        "source_file": result.source_file,
        "usage_count": len(result.usages),
        "usages": [
            {
                "file": u.file_path,
                "line": u.line_number,
                "type": u.usage_type,
                "content": u.line_content[:100],
            }
            for u in result.usages[:20]
        ],
        "importing_modules": result.importing_modules,
    }
    print(json.dumps(output, indent=2))
