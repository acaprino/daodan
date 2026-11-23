"""The helpers the framework sources share live in one module (spec of the pipeline, 8.13, point 4).

Before, `_folders` was copied in six sources, and React Router's `_excerpt` and `_starts` and Angular's `_folder` and `_bytes` were
borrowed by the others. The module gives what they shared, as they did it: the folders whose `package.json` declares a package
(`dependencies` or `devDependencies`, a file that is no JSON skipped), the nearest of them that holds a file, and both
ends of what a tool said.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))
import premap  # noqa: E402
from premap import frameworks  # noqa: E402


class _Inventory:
    def __init__(self, files: dict):
        self._files, self.files = files, list(files)

    def text(self, rel: str) -> str:
        return self._files[rel]


class _Context:
    def __init__(self, files: dict):
        self.inventory = _Inventory(files)


def test_the_folders_are_those_whose_package_json_declares_the_package():
    context = _Context({
        "package.json": json.dumps({"devDependencies": {"next": "15"}}),
        "web/package.json": json.dumps({"dependencies": {"next": "15", "nuxt": "3"}}),
        "lib/package.json": json.dumps({"peerDependencies": {"next": "15"}}),  # a library's peer is no app of it
        "bad/package.json": "{",  # `npm-files` reports it
        "web/other.json": json.dumps({"dependencies": {"next": "1"}}),
        "list/package.json": "[]",
    })
    assert frameworks.folders(context, ("next",)) == [".", "web"]  # in the inventory's order
    assert frameworks.folders(context, ("nuxt", "@nuxt/kit")) == ["web"]
    assert frameworks.folders(context, ("astro",)) == []


def test_the_nearest_folder_holding_a_file_is_the_deepest():
    ordered = frameworks.nearest_first([".", "web", "web/app", "api"])
    assert ordered == ["web/app", "api", "web", "."]
    assert frameworks.folder_of(ordered, "web/app/page.ts") == "web/app"
    assert frameworks.folder_of(ordered, "web/x.ts") == "web"
    assert frameworks.folder_of(ordered, "docs/a.md") == "."
    assert frameworks.folder_of(["web"], "docs/a.md") is None


def test_both_ends_of_what_a_tool_said():
    assert frameworks.excerpt({"stderr": " short \n", "stdout": "ignored"}) == "short"
    assert frameworks.excerpt({"stderr": "", "stdout": "out"}) == "out"
    long = "a" * 400 + "b" * 400
    assert frameworks.excerpt({"stderr": long, "stdout": ""}) == f"{'a' * 300} [...] {'b' * 300}"


def test_no_framework_source_keeps_a_copy_of_a_shared_helper_or_borrows_another_sources():
    sources = (*premap.FRAMEWORK_SOURCES, *premap.TEMPLATE_SOURCES)
    names = {source.__name__.rsplit(".", 1)[-1] for source in sources}
    for source in sources:
        tree = ast.parse(Path(source.__file__).read_text(encoding="utf-8"))
        own = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        assert not own & {"_folders", "_folder", "_excerpt"}, (source.NAME, own)
        mine = source.__name__.rsplit(".", 1)[-1]
        others = names - {mine}
        borrowed = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name) and node.value.id in others]
        borrowed += [alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
                     and ((node.module or "").rsplit(".", 1)[-1] in others
                          or node.module == "premap" and any(alias.name in others for alias in node.names))
                     for alias in node.names]
        assert not borrowed, (source.NAME, borrowed)  # what two sources share is in `frameworks`, whatever its name
