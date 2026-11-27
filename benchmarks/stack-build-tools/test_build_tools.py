"""The pure part of `modal_build_tools.py` on records written by hand: no fork, no pre-map, no network."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import modal_build_tools as bt  # noqa: E402


def entry(*sources, path="package.json"):
    return {"sources": list(sources), "signs": [["package", path, None, s] for s in sources]}


def record(units=(), workspace=(), unit_sources=(), with_=None, without=None):
    return {"units": list(units), "workspace": list(workspace), "unit_sources": list(unit_sources),
            "with": with_ or {}, "without": without or {}}


def test_a_host_mention_alone_is_not_the_fork_naming_an_entry():
    assert bt.fork_named({"npm": entry("stack-analyser"), "redis": entry("registry_hosts"),
                          "pnpm": entry("registry_hosts", "npm@11.19.1")}) == {"npm", "pnpm"}


def test_a_row_is_found_by_unit_kind_workspace_tool_or_stating_source_and_named_by_any_of_its_ids():
    made = bt.rows(record(units=["cmake-target", "npm-package"], workspace=["gradle"], unit_sources=["tsc"],
                          without={"pnpm": entry("stack-analyser")},
                          with_={"pnpm": entry("stack-analyser"), "maven": entry("maven@3.10.0", path="pom.xml")}))
    assert made["npm"] == {"fork": True, "fork_with": True, "sources": True}
    assert made["cmake"] == {"fork": False, "fork_with": False, "sources": True}
    assert made["gradle"]["sources"] and not made["gradle"]["fork"]
    assert made["tsc"]["sources"]
    assert made["maven"] == {"fork": False, "fork_with": True, "sources": False}
    assert not any(made["cargo"].values())


def test_lost_is_what_only_the_declarations_name_with_the_files_of_its_signs():
    made = record(without={"npm": entry("stack-analyser"), "redis": entry("registry_hosts")},
                  with_={"npm": entry("stack-analyser"), "redis": entry("registry_hosts", "compose@5.6.1", path="compose.yaml"),
                         "express": entry("npm@11.19.1", path="api/package.json")})
    assert bt.lost(made) == [{"id": "express", "files": ["api/package.json"]},
                             {"id": "redis", "files": ["compose.yaml"]}]


def test_summary_counts_both_only_the_sources_and_what_the_fork_names_beside():
    records = {
        "a": record(units=["cmake-target"], without={"c": entry("stack-analyser")}, with_={"c": entry("stack-analyser")}),
        "b": record(units=["cargo-crate"], without={"cargo": entry("stack-analyser")},
                    with_={"cargo": entry("stack-analyser"), "serde": entry("cargo@1.99.1", path="Cargo.toml")}),
        "c": record(without={"cargo": entry("stack-analyser")}, with_={"cargo": entry("stack-analyser")}),
    }
    made = bt.summary(records, {"c", "cargo"}, {"c": "tool", "cargo": "tool", "serde": "library"})
    assert made["fixtures"] == 3
    assert {k: made["tools"]["cmake"][k] for k in ("sources", "fork", "both", "uncovered", "fork_only")} == \
        {"sources": 1, "fork": 0, "both": 0, "uncovered": 1, "fork_only": 0}
    assert made["tools"]["cmake"]["uncovered_fixtures"] == ["a"] and made["tools"]["cmake"]["beside"] == {"c": 1}
    assert {k: made["tools"]["cargo"][k] for k in ("sources", "fork", "both", "uncovered", "fork_only")} == \
        {"sources": 1, "fork": 2, "both": 1, "uncovered": 0, "fork_only": 1}
    assert made["tool_ids"] == {"c": {"without": 1, "with": 1}, "cargo": {"without": 2, "with": 2}}
    assert made["lost"] == {"entries": 1, "fixtures": 1, "by_category": {"library": 1}}


def test_every_row_of_the_table_names_registry_ids_kinds_tools_and_sources_as_tuples_of_text():
    for tool, fields in bt.TOOLS.items():
        assert len(fields) == 4 and any(fields[1:]), tool
        assert all(isinstance(field, tuple) and all(isinstance(x, str) for x in field) for field in fields), tool


def test_the_ids_of_the_table_are_tools_of_the_registry():
    import json
    entries = json.loads((HERE.parents[1] / "daodan/data/service-registry.json").read_text(encoding="utf-8"))["entries"]
    tools = {e["id"] for e in entries if e.get("category") == "tool"}
    assert {ident for ids, *_ in bt.TOOLS.values() for ident in ids} <= tools
