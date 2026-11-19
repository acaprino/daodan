"""The identity of the parsers a snapshot was read with: the fingerprint of the
structural helpers and parser packages, and the effective backend of each file."""
from __future__ import annotations

import hashlib
from importlib import metadata
import json
import sys
from pathlib import Path

from languages import SUPPORTED_EXTENSIONS

SCRIPT_DIR = Path(__file__).resolve().parent


# Parser packages whose installed versions enter the parser fingerprint; the
# call-resolution pass runs with exactly these versions (`resolve_edges.py`).
PARSER_PACKAGES = ("tree-sitter", "tree-sitter-language-pack", "tree-sitter-java",
                   "tree-sitter-javascript", "tree-sitter-typescript", "tree-sitter-rust",
                   "tree-sitter-go", "sqlglot")


def parser_fingerprint() -> str:
    """Identity of the structural helpers and installed parser versions.

    Compute once per snapshot or read batch. Start a fresh process after updating
    helper code; this fingerprint does not reload already imported Python modules.
    Grammar availability is checked separately by parser_profile.
    """
    digest = hashlib.sha256()
    helpers = [SCRIPT_DIR / name for name in
               ("snapshot.py", "source_files.py", "parser_identity.py", "symbol_records.py", "symbols_at.py",
                "import_resolution.py", "change_set.py", "run_store.py", "ast_parser.py", "tree_scope.py",
                "source_reader.py",
                "semantic_index.py", "dependency_graph.py", "snapshot_store.py", "json_snapshot.py",
                "semantic_store.py", "resolution.py", "store_graph.py", "store_graph_metrics.py",
                "store_consumers.py")]
    helpers += sorted((SCRIPT_DIR / "languages").rglob("*.py"))
    for helper in helpers:
        if helper.is_file():
            digest.update(helper.relative_to(SCRIPT_DIR).as_posix().encode("utf-8") + b"\0")
            digest.update(helper.read_bytes())
            digest.update(b"\0")
    versions = {}
    for package in PARSER_PACKAGES:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = None
    # Only the stdlib `ast` grammar varies with Python, and only by minor
    # version. A patch release or a separate runtime environment of the same
    # minor (the MCP server's) parses identically.
    digest.update(json.dumps({"python": list(sys.version_info[:2]), "packages": versions},
                             sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


def grammar_gaps(profiles) -> dict[str, str]:
    """The grammars that were not available for these parser profiles, with the reason: a snapshot's
    declared parsing gaps."""
    return dict(sorted((profile["grammar"], profile["reason"]) for profile in profiles
                       if isinstance(profile, dict) and profile.get("backend") == "unavailable"))


def _versions(language) -> dict:
    """A grammar's ABI and semantic version, as the pack states them."""
    found = {}
    for attribute in ("abi_version", "semantic_version"):
        value = getattr(language, attribute, None)
        if value is not None:
            found[attribute] = list(value) if isinstance(value, tuple) else value
    return found


def parser_profile(path: Path, language: str | None = None) -> dict:
    """Effective backend for this file, without reading its source bytes."""
    language = language or SUPPORTED_EXTENSIONS.get(path.suffix.lower())
    if language in {"java", "javascript", "typescript", "rust", "go", "kotlin", "csharp", "vue", "svelte", "astro", "c", "cpp"}:
        from languages._treesitter import get_parser
        grammar = "tsx" if path.suffix.lower() == ".tsx" else ("typescript" if language in {"vue", "svelte", "astro"} else language)
        loaded = get_parser(grammar)
        if not loaded:
            # A declared gap, never a weaker reading: the reason is part of the profile, so the file is read
            # again once its grammar is there.
            from languages._treesitter import load_failure
            return {"language": language, "backend": "unavailable", "grammar": grammar,
                    "reason": load_failure(grammar) or "no tree-sitter grammar installed"}
        profile = {"language": language, "backend": "tree-sitter", "grammar": grammar, **_versions(loaded[1])}
        if language in {"vue", "svelte"}:  # the template's own grammar (`languages/sfc.py`)
            from languages._treesitter import load_failure
            template = get_parser(language)
            profile["template"] = {"grammar": language, **(_versions(template[1]) if template else {
                "reason": load_failure(language) or "no tree-sitter grammar installed"})}
        return profile
    return {"language": language, "backend": {
        "python": "stdlib-ast", "css": "stylesheet", "markup": "stylesheet", "sql": "regex", "plsql": "regex",
    }.get(language, "file-level")}
