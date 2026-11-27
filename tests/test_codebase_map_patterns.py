"""The regular expressions of the core do not grow (AGENTS.md: source code and markup are read from the syntax tree).

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_patterns.py

ALLOWED is what each file of `daodan/core/` had on 20 November 2026, counted with Python's own parser: every call of
`re.compile`, `re.search` and the like. A file may go down, never up; a new file starts at zero. When a file goes
down, lower its number here, so that the count cannot come back. Which of them read code or markup, and must become
a query on the tree, is the plan's Task H2: this test only keeps the number from growing meanwhile.
"""
from __future__ import annotations

import ast
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "daodan" / "core"
USES = {"compile", "search", "match", "fullmatch", "finditer", "findall", "sub", "subn", "split"}
ALLOWED = {
    "build_units.py": 48, "cascade_scan.py": 8, "change_set.py": 4, "classifier.py": 1, "code_graph.py": 1,
    "comment_rewriter.py": 39, "container.py": 11, "doc_review.py": 23, "docker_build.py": 12,
    "dynamic/__init__.py": 2, "dynamic/callgrind.py": 4, "dynamic/clang.py": 3, "dynamic/dotnet.py": 6,
    "dynamic/go.py": 1, "dynamic/javascript.py": 5, "dynamic/jvm.py": 4, "dynamic/python.py": 9, "dynamic/rust.py": 2,
    "engine_tools.py": 1, "file_formats.py": 1, "file_inventory.py": 2, "format_catalog.py": 1, "flows.py": 7, "import_resolution.py": 1, "indexers/clang.py": 12,
    "indexers/clang_run.py": 7, "indexers/csharp.py": 8, "indexers/css.py": 59, "indexers/go.py": 7,
    "indexers/java.py": 6, "indexers/jvm.py": 10, "indexers/kotlin.py": 1, "indexers/python.py": 12,
    "indexers/python_unbound.py": 1, "indexers/rust.py": 8, "indexers/typescript.py": 6,
    "languages/cfamily.py": 18, "languages/csharp.py": 5, "languages/detect/rules/header.py": 2, "languages/detect/rules/sql_rowtype.py": 1,
    "languages/go.py": 5, "languages/java.py": 5,
    "languages/javascript.py": 5, "languages/kotlin.py": 8, "languages/markup.py": 2, "languages/plsql.py": 9,
     "languages/rust.py": 8, "languages/sfc.py": 3, "languages/sql.py": 19,
    "languages/stylesheet.py": 34,  "mark_svg.py": 11, "mcp_service.py": 1,
    "module_inventory.py": 1, "module_records.py": 2, "modules.py": 1,
    "premap/autotools.py": 3, "premap/cmake.py": 6, "premap/compose.py": 10,
    "premap/dockerfile.py": 2, "premap/gitmodules.py": 3, "premap/gradle.py": 1, "premap/jvm_files.py": 13,
    "premap/make.py": 3, "premap/meson.py": 1, "premap/module_graph.py": 3, "premap/npm_lock.py": 2,
    "premap/npm_tests.py": 11, "premap/origins.py": 3, "premap/project_files.py": 1, "premap/python_build.py": 1,
    "premap/python_tests.py": 10, "premap/renovate.py": 14, "premap/requirements.py": 1, "premap/sbt.py": 2,
    "premap/tsc.py": 1, "premap/uv.py": 1, "preparation.py": 11, "registry_build.py": 6, "repository.py": 3,
    "retrieval.py": 4, "review_experience.py": 3, "review_roster.py": 31, "run_store.py": 1, "semantic_map.py": 3,
    "semantic_store.py": 1, "service_registry.py": 4, "snapshot.py": 2, "source_files.py": 2, "support_table.py": 4,
    "symbols_at.py": 1, "system_map.py": 2, "tree_scope.py": 2, "usage_finder.py": 6,
}


def uses(path: Path) -> int:
    """The calls of the `re` module in a file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sum(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and isinstance(node.func.value, ast.Name) and node.func.value.id == "re" and node.func.attr in USES
               for node in ast.walk(tree))


def test_no_file_of_the_core_has_more_regular_expressions_than_it_had():
    found = {path.relative_to(CORE).as_posix(): uses(path) for path in sorted(CORE.rglob("*.py"))}
    grown = {name: (count, ALLOWED.get(name, 0)) for name, count in found.items() if count > ALLOWED.get(name, 0)}
    assert grown == {}, f"more regular expressions than allowed (found, allowed): {grown}"


def test_the_count_only_goes_down():
    assert sum(ALLOWED.values()) <= 651  # 27 November 2026: -1, the position stage gone (T2.B.7); -11, requirements files and VCS requirements read by pip's parser, tomllib, configparser and ast (T3.A.8a); +1, Linguist's expressions tried on the dot directories the perimeter reads; +1, Composer's PLATFORM_PACKAGE_REGEX on a package name (T1.B.9b); +2, Linguist's `vendor`/`documentation` expressions on paths (T1.B.5); texts with no grammar; 659 on the 26th
