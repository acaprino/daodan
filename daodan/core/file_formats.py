"""Daodan's register of file formats, read from `data/file-formats.json`: the one place that says which files the
snapshot records, with which language, and which names it never descends into or opens.

The register is data, kept by hand: what Daodan accepts is Daodan's choice. What Linguist calls each accepted
extension and file name is beside it, in `data/linguist-catalog.json`, written by `format_catalog.py` from
Linguist's `languages.yml`; `languages[*].linguist` joins the two. The modules that own each rule bind these values
under the names their callers already use (`languages.SUPPORTED_EXTENSIONS`, `source_files.DOC_EXTENSIONS`,
`tree_scope.DEPENDENCY_DIRS`), with the reason of each list beside the name.

Standard library only: `tree_scope.py` imports it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "data" / "file-formats.json"
SCHEMA = "daodan/file-formats/v1"

_register = json.loads(PATH.read_text(encoding="utf-8"))
if _register.get("schema") != SCHEMA:
    raise ValueError(f"{PATH.name}: schema is not {SCHEMA}")

# Read with symbols: extension to Daodan's language, and that language's names in Linguist.
SOURCES: dict[str, str] = {extension: language for language, entry in _register["languages"].items()
                           for extension in entry["extensions"]}
LINGUIST_NAMES: dict[str, tuple[str, ...]] = {language: tuple(entry["linguist"])
                                              for language, entry in _register["languages"].items()}
# Recorded as file-level entries, with no symbols.
DOCUMENTS = frozenset(_register["documents"])
PRESENTATION = frozenset(_register["presentation"])
STACK_SOURCES: dict[str, str] = {extension: language for language, extensions in _register["stack_sources"].items()
                                 for extension in extensions}
MANIFESTS = frozenset(_register["manifests"])
MAKEFILES = re.compile(_register["makefiles"])  # a file name has no grammar: a pattern is what names a dialect
BUILD_FOLDERS = frozenset(_register["build_folders"])
# Never descended into, never opened.
DEPENDENCY_DIRECTORIES = frozenset(_register["dependency_directories"])
FORBIDDEN = tuple(_register["forbidden"])
SECRET_NAMES = tuple(_register["secret_names"])
