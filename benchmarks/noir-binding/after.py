"""After the correction (`modal_binding.py --mode after` ships this file to `/daodan/measure/`): the tree's own binder, with nothing substituted.

The checkout is at `/work` (nothing of it runs here). Noir's answer is recorded in the pre-map (`premap.write`), and the links' own `flows.bind_declared`
(`binder.bind`) is run over every row of it on a `flows.Facts` built as `flows.link_facts` builds it; a second `Facts`, untouched, gives the node of a function
as it was before the binder named any function by its route. Then `flows.link_facts(manifest, [])` is run as it is: no substitution.

For each endpoint (all of Noir's rows, so that `_name_handlers` sees what it sees in the links): how the binder ties it (by the name at the row's line, or by
the function that starts there), the symbol, the cause it words when it does not, the declarations it ended on, and for a bound one what leaves its node in the
links, with the sites that lie outside the lines of the function bound. For a function bound by position that has no name (`NAMELESS`), what the syntax tree
says of the place it is written in: an argument of a call (which, among how many; whether an earlier or a later argument holds a function, as a guard or a handler
array does), an element of an array, the other functions that start on its line.
"""
import collections
import json
import os
import pathlib
import subprocess
import sys
import time
import types

ROOT = "/work"
FUNCTION_LIKE = {"arrow_function", "function_expression", "function", "generator_function", "lambda_expression", "anonymous_method_expression", "func_literal",
                 "lambda", "closure_expression", "function_declaration", "method_definition"}
WRAPPERS = {"argument", "parenthesized_expression", "await_expression", "as_expression", "satisfies_expression", "non_null_expression", "type_assertion"}
LISTS = {"arguments", "argument_list", "array", "array_expression", "collection_expression", "initializer_expression", "composite_literal"}


def brief(d: dict) -> dict:
    return {"name": d["name"], "qn": d.get("qualified_name"), "line": d["line"], "end": d["end"]}


def holds_function(node) -> bool:
    stack = [node]
    while stack:
        n = stack.pop()
        if n.type in FUNCTION_LIKE:
            return True
        stack.extend(n.children)
    return False


def text(tree, node) -> str:
    return tree.source[node.start_byte:node.end_byte].decode("utf-8", "replace")


def callee_of(tree, call) -> str | None:
    """The last name of what a call calls (`get` of `app.get(...)`), as the syntax tree has it."""
    function = call.child_by_field_name("function") or call.child_by_field_name("expression") or (call.named_children[0] if call.named_children else None)
    if function is None:
        return None
    return text(tree, function).rpartition(".")[2][:40]


def syntax(facts, d: dict) -> dict:
    """Where the function `d` is written, from the file's syntax tree."""
    tree = facts.tree(d["file"])
    if isinstance(tree, str):
        return {"tree": tree[:60]}
    span = d["span"]
    node = tree.root.descendant_for_point_range((span[0] - 1, span[1]), (span[2] - 1, span[3]))
    while node.type not in FUNCTION_LIKE and node.parent is not None and node.parent.start_point == node.start_point:
        node = node.parent  # the smallest node of that span may be a child of it
    chosen = node
    while chosen.parent is not None and chosen.parent.type in WRAPPERS:
        chosen = chosen.parent
    parent = chosen.parent
    info = {"type": node.type, "parent": parent.type if parent is not None else None}
    if parent is not None and parent.type in LISTS:
        elements = list(parent.named_children)
        index = next(i for i, e in enumerate(elements) if e.start_byte == chosen.start_byte and e.end_byte == chosen.end_byte)
        info.update({"list": parent.type, "index": index, "elements": len(elements),
                     "earlier_with_a_function": sum(holds_function(e) for e in elements[:index]), "later_with_a_function": sum(holds_function(e) for e in elements[index + 1:])})
        holder = parent.parent
        if parent.type not in ("arguments", "argument_list") and holder is not None and holder.type in LISTS:
            info["list_is_an_argument_of"] = holder.parent.type if holder.parent is not None else None
        call = holder if parent.type in ("arguments", "argument_list") else (holder.parent if holder is not None else None)
        if call is not None and call.type.endswith(("call_expression", "invocation_expression")):
            info.update({"callee": callee_of(tree, call), "call_line": call.start_point[0] + 1})
    return info


def run(name: str) -> dict:
    os.chdir("/")
    sys.path[:0] = ["/daodan/core"]
    import binder
    import edge_view
    import entries
    import flows
    import premap
    import semantic_store
    import snapshot
    from languages.semantic import NAMELESS
    from premap import noir
    from snapshot_store import open_snapshot

    out = {"name": name}
    manifest = pathlib.Path("/tmp/noir-binding/after/manifest.sqlite")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    snapshot.read_project(pathlib.Path(ROOT), manifest)
    out["snapshot_seconds"] = round(time.monotonic() - started, 1)
    [command] = noir.commands(types.SimpleNamespace(inventory=types.SimpleNamespace(files=True)))
    env = {"PATH": os.environ["PATH"], "HOME": "/tmp/noir-home", "LANG": "C.UTF-8"}
    os.makedirs(env["HOME"], exist_ok=True)
    result = subprocess.run(command["argv"], cwd=os.path.join(ROOT, command["cwd"]), env=env, capture_output=True, text=True, timeout=3000, stdin=subprocess.DEVNULL)
    if result.returncode != 0:
        return {**out, "failed": f"Noir exited with {result.returncode}"}
    report = json.loads(result.stdout)
    registration = {}  # where Noir says each route is declared (`details.code_paths[0]`), by the row's site, method and path
    for endpoint in report.get("endpoints") or ():
        handler = endpoint.get("handler") or {}
        paths = (endpoint.get("details") or {}).get("code_paths") or [{}]
        where = handler if handler.get("path") else paths[0]
        if where.get("path"):
            file = where["path"][len(ROOT) + 1:] if where["path"].startswith(ROOT + "/") else where["path"]
            site = f"{file}:{where['line']}" if where.get("line") else file
            first = paths[0]
            registration.setdefault((site, endpoint["method"], endpoint["url"]), f"{(first.get('path') or '')[len(ROOT) + 1:]}:{first.get('line')}")
    answer = {"returncode": 0, "stdout": result.stdout, "stderr": "", "root": ROOT}
    record = premap.write(manifest, sources=(noir,), runner=lambda commands: [answer])
    rows = record.get("noir_entries", [])
    out["rows"] = len(rows)

    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        view = edge_view.load_edge_view(store)
        facts = flows.Facts(store, db, view)
        plain = flows.Facts(store, db, view)  # no function named by its route: the nodes as the binder before found them
        bound = flows.bind_declared(rows, facts, view, [])  # as the links bind the declared rows
        assert len(bound) == len(rows)
        out["named_by_their_route"] = len(facts.route_named)
        facts_rows = []
        for i, (row, done) in enumerate(zip(rows, bound)):
            item = {"i": i, "shape": row["shape"], "handler": row["handler"], "site": row["site"], "method": row.get("method"), "path": row["path"],
                    "registration": registration.get((row["site"], row.get("method"), row["path"])), "ok": not done.get("gap"),
                    "symbol": done.get("symbol") if not done.get("gap") else None}
            matches, starts = binder._placed(row, facts) if "handler" in row else ([], None)
            item["by"] = ("name" if len(matches) == 1 else "position") if item["ok"] else None
            if item["ok"]:
                functions = matches if len(matches) == 1 else starts
                item["decls"] = [d["id"] for d in functions]
                item["decl_brief"] = [brief(d) for d in functions[:3]]
                item["file"] = functions[0]["file"]
                item["lines"] = [min(d["line"] for d in functions), max((d["end"] or d["line"]) for d in functions)]
                if len(matches) == 1:
                    item["same_node_as_before"] = plain.node(matches[0]["id"]) == item["symbol"]  # a row the binder tied before: its symbol must be the one it had
                else:
                    function = functions[0]
                    item["agrees"] = binder._agrees(row["handler"], function, facts)
                    item["nameless"] = function["name"] in NAMELESS
                    file, _, line = row["site"].rpartition(":")
                    every = [d for d in facts.functions.get(file, ()) if d["line"] == int(line)]
                    item["starting_at_the_line"] = [{**brief(d), "held_by_the_chosen": d is not function and function["span"][:2] <= d["span"][:2] and d["span"][2:] <= function["span"][2:]} for d in every]
                    if item["nameless"]:
                        item["syntax"] = syntax(facts, function)
                        item["holds_functions"] = [brief(d) for d in facts.functions.get(file, ()) if d is not function and function["span"][:2] <= d["span"][:2] and d["span"][2:] <= function["span"][2:]][:3]
                item["named_by_route"] = any(d["id"] in facts.route_named for d in functions)
            else:
                item["gap"] = done["gap"].partition(": ")[2] or None
                if "handler" in row and row["handler"] is not None and starts is not None and len(starts) == 1:
                    item["function_at_the_line"] = brief(starts[0])
                    item["written_directly_in_it"] = [{**brief(d), "folds": facts.folds(d)} for d in facts.functions.get(starts[0]["file"], ())
                                                      if (owner := facts.owner(d)) is not None and owner["id"] == starts[0]["id"]][:6]
            facts_rows.append(item)
        out["facts"] = facts_rows
        edges_from = collections.defaultdict(list)
        try:
            started = time.monotonic()
            links = flows.link_facts(manifest, [])
            out["links_seconds"] = round(time.monotonic() - started, 1)
        except Exception as error:  # the links of this snapshot did not build
            links = None
            out["links_failed"] = f"{type(error).__name__}: {str(error)[:400]}"
        if links is not None:
            noir_entries = [e for e in links["entries"] if e.get("reader") == entries.NOIR and e.get("shape") == "http"]
            mine = collections.Counter(item["symbol"] for item in facts_rows if item["ok"] and item["shape"] == "http")
            theirs = collections.Counter(e["symbol"] for e in noir_entries)
            out["links"] = {"noir_entries": len(noir_entries), "same_symbols_as_the_binder_rows": mine == theirs, "edges": len(links["edges"]), "gaps": len(links["gaps"])}
            for edge in links["edges"]:
                if edge["type"] in ("chiama", "attiva"):
                    edges_from[edge["from"]].append(edge)
            for item in facts_rows:
                if not item["ok"]:
                    continue
                edges = edges_from.get(item["symbol"], ())
                outside = []
                for edge in edges:
                    file, _, line = edge["site"].rpartition(":")
                    if not (file == item["file"] and line.isdecimal() and item["lines"][0] <= int(line) <= item["lines"][1]):
                        outside.append(edge["site"])
                item["edges_out"] = len(edges)
                item["edges_outside_its_lines"] = len(outside)
                item["edges_sample"] = [{"to": e["to"], "site": e["site"]} for e in edges[:3]]
                item["outside_sample"] = outside[:2]
    return out
