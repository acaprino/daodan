"""Flow starts that a tool or manifest declares, resolved only at their snapshot destinations."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import entries
import flows
import premap
import snapshot
from premap import python_build


def test_manifest_declarations_survive_reopening_without_a_source_read(tmp_path, monkeypatch):
    app = tmp_path / "project"
    source = app / "src"
    source.mkdir(parents=True)
    (app / "pyproject.toml").write_text(
        '[project.scripts]\ncheck="entry:check"\nverify="entry:check"\nwrong="entry:missing"\n[project.gui-scripts]\n'
        'viewer="entry:show"\n[tool.setuptools.package-dir]\n""="src"\n')
    (source / "entry.py").write_text("def check(): pass\ndef show(): pass\n")
    (source / "other.py").write_text("def missing(): pass\n")
    (source / "binary.rs").write_text("fn main() {}\n")
    (app / "Cargo.toml").write_text('[package]\nname="reader"\nversion="1.0.0"\n')
    manifest = tmp_path / "manifest.sqlite"
    snapshot.read_project(app, manifest)
    # The saved form of cargo metadata: tests and custom build scripts are not product commands.
    unit = {"kind": "cargo-crate", "root": ".", "manifest": "Cargo.toml", "name": "reader",
            "config": {"targets": [{"kind": kind, "name": kind, "path": "src/binary.rs"}
                                   for kind in ("bin", "test", "custom-build")]}}
    cargo = SimpleNamespace(NAME="cargo", VERSION="fixture", RANK="model", run=lambda _ctx: {"facts": {"units": [unit]}})
    premap.write(manifest, sources=(python_build, cargo))
    premap.modules.ensure_graph(manifest)
    monkeypatch.setattr(premap.modules._Inventory, "text", Mock(side_effect=AssertionError("source read")))
    from premap.flow_entries import evidence
    rows, gaps = evidence(manifest)
    rows = [r for r in rows if r["reader"] == "manifesto"]
    assert {(r["label"], r["symbol"], r["site"], r["kind"]) for r in rows if "gap" not in r} == {
        ("check", "src/entry.py::check", "src/entry.py:1", "comando"),
        ("verify", "src/entry.py::check", "src/entry.py:1", "comando"),
        ("viewer", "src/entry.py::show", "src/entry.py:2", "avvio di un processo"),
        ("bin", "src/binary.rs::main", "src/binary.rs:1", "avvio di un processo")}
    assert [r["label"] for r in rows if r.get("gap")] == ["wrong"]
    assert any(g["kind"] == "noir_unavailable" for g in gaps)
    links = flows.cached_links(manifest, [])
    assert {r["label"] for r in links["entries"] if r.get("reader") == "manifesto"} == {"check", "verify", "viewer", "bin"}
    assert any("entry:missing" in g["reason"] for g in links["gaps"])
    assert rows == [r for r in entries.candidates(links, manifest) if r["reader"] == "manifesto"]


def test_frozen_workflow_triggers_and_service_sites_do_not_guess_a_function_from_a_command(tmp_path, monkeypatch):
    from premap import module_graph, renovate
    from premap.flow_entries import evidence
    from test_codebase_map_container_runner import manifest_of

    workflow = ".github/workflows/sync.yml"
    triggers = {"push": None, "workflow_dispatch": None, "schedule": [{"cron": "0 4 * * *"}]}
    _, manifest = manifest_of(tmp_path, {
        workflow: "on:\n  push:\n  workflow_dispatch:\n  schedule:\n    - cron: '0 4 * * *'\n"
                  "jobs:\n  sync:\n    uses: org/tools/.github/workflows/sync.yaml@v1\n",
        "compose.yaml": "services:\n  jobs:\n    image: queue\n    command: sync\n",
        "sync.py": "def sync(): pass\n"})
    document = {"on": triggers, "jobs": {"sync": {"uses": "org/tools/.github/workflows/sync.yaml@v1"}}}
    run = Mock(return_value=[
        {"returncode": 0, "stdout": "{}", "stderr": "", "root": "/work"},
        {"returncode": 0, "stdout": f"{workflow}\n{json.dumps(document)}\n", "stderr": "", "root": "/work"}])
    premap.write(manifest, sources=(module_graph, renovate), runner=run)
    premap.modules.ensure_graph(manifest)
    monkeypatch.setattr(premap.modules._Inventory, "text", Mock(side_effect=AssertionError("manifest reread")))
    rows, _ = evidence(manifest)
    assert {(r["label"], r["kind"], r["declared_in"]) for r in rows} == {
        ("push", "evento del repository", f"{workflow}#on.push"),
        ("workflow_dispatch", "comando", f"{workflow}#on.workflow_dispatch"),
        ("0 4 * * *", "orario", f"{workflow}#on.schedule.0.cron"),
        ("jobs", "avvio di un processo", "compose.yaml#L2")}
    assert all(row.get("gap") for row in rows)
    assert next(row for row in rows if row["label"] == "jobs")["site"] == "compose.yaml:2"
    assert all(row["symbol"] != "sync.py::sync" for row in rows)
    assert not any(e["to"] == "sync.py::sync" for e in flows.cached_links(manifest, [])["edges"])
    assert evidence(manifest)[0] == rows
    assert run.call_count == 1


# ------------------------------------------------------------------ Next.js routes

def next_links(tmp_path, files, noir_report=None):
    """The links of a Next.js snapshot whose pre-map was made from the real `next typegen` output of the fixture and,
    when given, from a Noir report."""
    from premap import nextjs, noir
    from test_codebase_map_container_runner import manifest_of
    from test_codebase_map_premap_nextjs import VALIDATOR

    def run(commands):
        if commands[0]["tool"] == "noir":
            return [{"root": "/work", "returncode": 0, "stdout": json.dumps(noir_report), "stderr": ""}]
        return [{"root": "/work", "returncode": 0, "stderr": "", "stdout": "" if c["argv"][0] == "npx" else VALIDATOR}
                for c in commands]
    _, manifest = manifest_of(tmp_path, files)
    premap.write(manifest, sources=(noir, nextjs) if noir_report else (nextjs,), runner=run)
    return flows.cached_links(manifest, [])


def shop(**changed):
    from test_codebase_map_premap_nextjs import SHOP
    return {**SHOP, **changed}


def test_a_next_page_is_an_entry_on_its_default_export_with_the_line_of_that_function(tmp_path):
    links = next_links(tmp_path, shop())
    assert {e["path"]: (e["symbol"], e["site"], e["kind"], e["reader"], e["handler_source"])
            for e in links["entries"] if e["path"] != "/api/pay"} == {
        "/": ("app/page.tsx::Home", "app/page.tsx:1", "rotta", "next", "next"),
        "/checkout": ("app/checkout/page.tsx::Checkout", "app/checkout/page.tsx:3", "rotta", "next", "next"),
        "/orders/[id]": ("app/orders/[id]/page.tsx::Order", "app/orders/[id]/page.tsx:1", "rotta", "next", "next")}


def test_a_route_handler_with_two_exported_methods_is_two_entries(tmp_path):
    route = ("export async function GET() {\n  return Response.json({});\n}\n\n"
             "export async function POST() {\n  return Response.json({});\n}\n")
    links = next_links(tmp_path, shop(**{"app/api/pay/route.ts": route}))
    assert sorted((e["method"], e["symbol"], e["site"]) for e in links["entries"] if e["path"] == "/api/pay") == [
        ("GET", "app/api/pay/route.ts::GET", "app/api/pay/route.ts:1"),
        ("POST", "app/api/pay/route.ts::POST", "app/api/pay/route.ts:5")]


@pytest.mark.parametrize("get", [
    # a TypeScript overload: three records of the one export name
    "export async function GET(a: string): Promise<Response>;\nexport async function GET(a: number): Promise<Response>;\n"
    "export async function GET(a: any) {\n  return Response.json({});\n}\n",
    # a value and a type of one name
    "export const GET = () => Response.json({});\nexport type GET = { x: number };\n"])
def test_an_exported_method_the_file_makes_twice_is_a_gap_naming_the_cause_beside_the_entries_of_the_others(tmp_path, get):
    """`export-missing-or-ambiguous` was one reason, and an ambiguous export left without a word: the entry of the others stayed
    and the lost one was in no gap. Missing and ambiguous are two reasons, and only the missing one is silent."""
    route = get + "\nexport async function POST() {\n  return Response.json({});\n}\n"
    links = next_links(tmp_path, shop(**{"app/api/pay/route.ts": route}))
    assert [e["method"] for e in links["entries"] if e["path"] == "/api/pay"] == ["POST"]
    [gap] = [g for g in links["gaps"] if g["site"] == "app/api/pay/route.ts"]
    assert "GET: export-ambiguous" in gap["reason"] and "HEAD" not in gap["reason"] and "POST" not in gap["reason"]


@pytest.mark.parametrize("file, text, looked_for", [
    ("app/page.tsx", "export const title = 'Negozio';\n", "default"),
    ("app/api/pay/route.ts", "export const dynamic = 'force-static';\n", "GET, HEAD, OPTIONS, POST, PUT, DELETE, PATCH")])
def test_a_file_with_no_export_the_rule_names_has_no_entry_and_a_gap_naming_what_was_looked_for(
        tmp_path, file, text, looked_for):
    links = next_links(tmp_path, shop(**{file: text}))
    assert not [e for e in links["entries"] if e["site"].split(":")[0] == file]
    [gap] = [g for g in links["gaps"] if g["site"] == file]
    assert gap["symbol"] == f"{file}::<module>" and looked_for in gap["reason"]


def test_an_exported_method_the_snapshot_cannot_resolve_is_a_gap_beside_the_entries_of_the_others(tmp_path):
    route = "export async function GET() {\n  return Response.json({});\n}\n\nexport { POST } from './handlers';\n"
    links = next_links(tmp_path, shop(**{"app/api/pay/route.ts": route,
                                         "app/api/pay/handlers.ts": "export async function POST() {}\n"}))
    assert [(e["method"], e["symbol"]) for e in links["entries"] if e["path"] == "/api/pay"] == [
        ("GET", "app/api/pay/route.ts::GET")]
    [gap] = [g for g in links["gaps"] if g["site"] == "app/api/pay/route.ts"]
    assert "POST" in gap["reason"] and "reexport" in gap["reason"]


def test_a_route_handler_exported_under_two_methods_by_one_function_is_two_entries(tmp_path):
    route = "async function handler() {\n  return Response.json({});\n}\n\nexport { handler as GET, handler as POST };\n"
    links = next_links(tmp_path, shop(**{"app/api/pay/route.ts": route}))
    assert sorted((e["method"], e["symbol"], e["site"]) for e in links["entries"] if e["path"] == "/api/pay") == [
        ("GET", "app/api/pay/route.ts::handler", "app/api/pay/route.ts:1"),
        ("POST", "app/api/pay/route.ts::handler", "app/api/pay/route.ts:1")]


def test_a_layout_is_no_entry_and_no_gap(tmp_path):
    links = next_links(tmp_path, shop())
    assert not [e for e in links["entries"] if e["site"].startswith("app/layout.tsx")]
    assert not [g for g in links["gaps"] if g["site"].startswith("app/layout.tsx")]


def noir_route(url, method, file, name, line):
    return {"protocol": "http", "url": url, "method": method, "kind": "",
            "handler": {"path": f"/work/{file}", "line": line, "name": name}}


def test_a_noir_route_on_the_symbol_of_a_next_entry_is_dropped_and_one_in_another_file_stays(tmp_path):
    report = {"endpoints": [noir_route("/api/pay", "POST", "app/api/pay/route.ts", "POST", 1),
                            noir_route("/other", "GET", "server/other.ts", "other", 1)]}
    links = next_links(tmp_path, shop(**{"server/other.ts": "export function other() {}\n"}), report)
    assert [(e["reader"], e["symbol"], e["method"]) for e in links["entries"] if e["path"] == "/api/pay"] == [
        ("next", "app/api/pay/route.ts::POST", "POST")]
    assert [(e["reader"], e["symbol"]) for e in links["entries"] if e["path"] == "/other"] == [
        ("noir", "server/other.ts::other")]


def test_a_noir_route_with_no_handler_on_a_file_and_path_a_next_entry_covers_is_that_entry(tmp_path):
    """Noir names no handler for a page: its row has the file's own symbol, and no unique function at its site."""
    page = {"protocol": "http", "url": "/checkout", "method": "GET", "kind": "",
            "details": {"code_paths": [{"path": "/work/app/checkout/page.tsx", "line": 3}]}}
    links = next_links(tmp_path, shop(), {"endpoints": [page]})
    assert [(e["reader"], e["symbol"], e.get("method")) for e in links["entries"] if e["path"] == "/checkout"] == [
        ("next", "app/checkout/page.tsx::Checkout", None)]  # a page answers any method: Noir's is not copied onto it
    assert not [g for g in links["gaps"] if g["site"].startswith("app/checkout/page.tsx")]


def test_a_noir_route_on_the_function_a_next_entry_starts_under_another_path_is_its_own_entry(tmp_path):
    """Noir says the function answers `/other`, and Next starts it from `/checkout`: two routes, neither drops the
    other, and the method goes to no entry of another path."""
    report = {"endpoints": [noir_route("/other", "POST", "app/checkout/page.tsx", "Checkout", 3)]}
    links = next_links(tmp_path, shop(), report)
    found = [e for e in links["entries"] if e["symbol"] == "app/checkout/page.tsx::Checkout"]
    assert sorted((e["reader"], e["path"], e.get("method")) for e in found) == [
        ("next", "/checkout", None), ("noir", "/other", "POST")]


def test_a_noir_route_with_a_method_no_next_entry_of_its_file_and_path_carries_is_its_own_entry(tmp_path):
    """A route handler exports `GET` as a function and `POST` in a form the snapshot's exports do not name (Next gives
    no entry and no gap for it): Noir's `POST` on that file and path stays, and its `GET` is Next's."""
    route = "export async function GET() {\n  return Response.json({});\n}\n\nasync function POST() {\n  return 1;\n}\n"
    report = {"endpoints": [noir_route("/api/pay", "GET", "app/api/pay/route.ts", "GET", 1),
                            noir_route("/api/pay", "POST", "app/api/pay/route.ts", "POST", 5)]}
    links = next_links(tmp_path, shop(**{"app/api/pay/route.ts": route}), report)
    assert [(e["reader"], e["symbol"], e["method"]) for e in links["entries"] if e["path"] == "/api/pay"] == [
        ("next", "app/api/pay/route.ts::GET", "GET"), ("noir", "app/api/pay/route.ts::POST", "POST")]


def test_a_dropped_noir_route_does_not_give_its_method_to_the_next_page(tmp_path):
    report = {"endpoints": [noir_route("/checkout", "GET", "app/checkout/page.tsx", "Checkout", 3)]}
    links = next_links(tmp_path, shop(), report)
    assert [(e["reader"], e["symbol"], e.get("method")) for e in links["entries"] if e["path"] == "/checkout"] == [
        ("next", "app/checkout/page.tsx::Checkout", None)]

