"""The functions of the project that wrap an HTTP client, proved from the engine's own data, and the `rotta` rule each
one proposes.

A call made through a wrapper (`adminFetch(url, body)` around `fetch`) is hidden from the route join: a `rotta` rule
is written by hand, wrapper by wrapper. The proof needs no name, no depth and no expression, only what the engine and
the snapshot state. For a call the engine resolves, at every sure end, into a function of the table
(`daodan/data/http-clients.json`: `external_symbols` of the view), made inside a named function F of the project:

- the URL argument is a bare name, and the engine reads it as a parameter (`detail`) that F itself reads (`caller`): the
  engine, not the snapshot, says so, since the lexical scope of a generic function stays open in the snapshot;
- the snapshot declares that name once inside F's span, as F's parameter: its place among the formal parameters in the
  syntax tree of F's own declaration is the position of the URL in every call to F (overloads change nothing, for a
  method as for a function: the implementation's parameters decide); a destructured or rest parameter has no place of
  its own, and TypeScript's `this`, which no call passes, leaves the scope unresolved, so it is refused as below;
- the name is written nowhere else: the snapshot declares every target of an assignment it reads (`url = x`, `url += x`,
  `url++`, `[url] = x`, `({url} = x)`, `for (url of x)`), and every inner declaration of the name. What it cannot read
  (`(url as any) = x`, `[(url as any)] = xs`, `eval(...)` and `(eval)(...)`) it declares nothing for: the reader leaves that
  scope unresolved (`languages/semantic.py`, `block`), or the lines unread around a syntax error. F holding such a scope
  or such lines is refused. The one exemption is the reader's own reason for a generic function
  (`semantic.GENERIC_SCOPE_REASON`, set first on the scope the function opens: any later reason takes its place on that
  scope or sits on another scope of F, and refuses). `arguments`, which aliases the parameters in sloppy mode, is a read
  the snapshot records: F reading it is refused;
- the method is read as a rule reads it (`flows._value`): a literal, or the default when the options are absent; options
  with a spread, a computed key or a `__proto__` hold members the key reading cannot see, and the method is no literal;
- the callee form `file::name`, the one a rule names F by (`flows.Facts.named`), is no other declaration's of the file: the
  reader gives the same bare name to an object literal's method, a block's function and a namespace's member, and the rule
  would reach them too.

The proof holds as far as the reader marks unresolved, or unread, what it does not read: it cannot see a write the reader
walks without declaring and without a mark. The holes the reviews found (a callee wrapped in parentheses or an erased
type, an element or a fragment as an attribute's value, lines skipped around a syntax error) are closed in the reader, each
with its test in `tests/test_xray_semantic_syntax.py`, and the shapes of each in `tests/test_codebase_map_flows_http_wrapper.py`.

Each other case is a gap with its site and its cause, never a candidate: a URL built from a parameter (the gap names the
argument's node type: a template, a binary expression, a call), a parameter that is written again, shadowed, destructured
or rest, a method that is no literal, ends outside the table mixed with ends in it, calls of the client that read the route
differently, a name two declarations share. A function that is not named (a callback), one the URL is not a parameter of,
a call with no URL and a call whose ends are not the table's are no wrapper and no gap. A wrapper of a wrapper (a function
that passes its own parameter to a proved wrapper) is not proved here: it needs the proof of the wrapper it calls, and no
rule yet. A table entry for another language needs its reader to declare assignment targets and to leave unresolved what it
cannot read.

`flows.link_facts` applies the proposed rules with no model (`applied`), and reads a call of the table made outside a wrapper
as a rule would (`asked`): both ask for a route with `service(rules)`, and meet the routes `find_entry_points` declares.

    python flows.py wrappers MANIFEST [--rules RULES]
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import code_graph  # noqa: E402
import edge_view  # noqa: E402
import entries  # noqa: E402
import flows  # noqa: E402
import semantic_store  # noqa: E402
from languages import semantic  # noqa: E402
from snapshot_store import _unpack, open_snapshot  # noqa: E402

CLIENTS = json.loads((SCRIPT_DIR.parent / "data" / "http-clients.json").read_text(encoding="utf-8"))["clients"]
_TABLE = {(item["manager"], item["package"], item["descriptors"]): item for item in CLIENTS}
NAMEABLE = ("function", "method", "class", "binding")  # what a rule's `callee` can name: not an overload's `unknown`
# The service of a call no rule names (a call of the table, a wrapper's rule with no single service): no rule offers it, so
# it meets only the routes `find_entry_points` declares, of the service `flows.ANY_SERVICE`, and only with no loose hole.
UNNAMED = ""


def client(symbol: str) -> dict | None:
    """The table's entry for a symbol of the engine, whatever the version of its package; None for any other."""
    parts = code_graph.split_symbol(symbol)
    return _TABLE.get((parts[1], parts[2], parts[4])) if parts else None


def asked(ref: dict) -> dict | None:
    """The table's entry a call of the view is a call of: every sure end of it (`external_symbols`, which the view gives only
    when all the ends of the call are certain and external) a function of the table, all read alike; None for any other."""
    found = [client(symbol) for symbol in ref.get("external_symbols") or ()]
    return found[0] if found and all(found) and len({(item["url"], item["method"]) for item in found}) == 1 else None


def service(rules: list[dict]) -> str:
    """The service a call of the client asks with when no rule names its own: the one service the recorded `offre` rules
    name, else `UNNAMED`."""
    services = _services(rules)
    return services[0] if len(services) == 1 else UNNAMED


def _inside(owner: dict, line: int, column: int) -> bool:
    return tuple(owner["span"][:2]) <= (line, column) < tuple(owner["span"][2:])


class _Snapshot:
    """What the proof reads of the snapshot beyond the view, once per file or per name."""

    def __init__(self, facts: flows.Facts):
        self.facts = facts
        self._declared: dict | None = None
        self._named: dict | None = None
        self._scopes: dict[str, dict] = {}
        self._unread: dict[str, list] = {}

    def declared(self, owner: dict, name: str) -> list[dict]:
        """The declarations of that name inside the function's span: its parameter, and what gives the name a value or
        declares it again. The engine could not say it: the SCIP roles do not tell a write from a read
        (`code_graph.Occurrence` keeps only `definition`; scip-python gives a redefinition the read role), and the gate of
        `Traversal._binding` serves a module's or a class's bindings, never a parameter."""
        if self._declared is None:
            self._declared = defaultdict(list)
            for declaration in self.facts.declarations.values():
                self._declared[declaration["file"], declaration["name"]].append(declaration)
        return [d for d in self._declared[owner["file"], name] if _inside(owner, d["line"], d["column"])]

    def sharing(self, owner: dict) -> list[dict]:
        """The other declarations of the file that a rule naming the function reaches too: the same `file::name`."""
        if self._named is None:
            self._named = defaultdict(list)
            for declaration in self.facts.declarations.values():
                if declaration["kind"] in NAMEABLE:
                    self._named[self.facts.named(declaration["id"])].append(declaration)
        return [d for d in self._named[self.facts.named(owner["id"])] if d["id"] != owner["id"]]

    def unresolved(self, owner: dict) -> list:
        """The reasons of the scopes inside the function that the reader left unresolved, the generic function's apart."""
        file = owner["file"]
        if file not in self._scopes:
            self._scopes[file] = {identity: _unpack(blob) for identity, blob in self.facts.db.execute(
                "SELECT id, payload FROM sem_scopes WHERE file=?", (file,))}
        scopes = self._scopes[file]
        own = {identity for identity, scope in scopes.items()
               if scope.get("caller") is not None and f"{file}::{scope['caller']}" == owner["id"]}  # a scope's caller has no file

        def within(identity):
            while identity is not None:
                if identity in own:
                    return True
                identity = scopes[identity].get("parent")
            return False
        # shortcut: a generic function's scope is unresolved for its type parameters, which write nothing, so only that
        # reason is let through; upgrade when the reader declares the type parameters instead of blocking the scope
        return [scope.get("reason") for identity, scope in scopes.items()
                if scope.get("unresolved") and scope.get("reason") != semantic.GENERIC_SCOPE_REASON and within(identity)]

    def unread(self, owner: dict) -> list[list[int]]:
        """The line ranges inside the function that the reader skipped around a syntax error (`sem_coverage`, `partial`):
        what it declares and records of them is nothing, a write included."""
        file = owner["file"]
        if file not in self._unread:
            row = self.facts.db.execute("SELECT payload FROM sem_coverage WHERE file=?", (file,)).fetchone()
            self._unread[file] = (_unpack(row[0]).get("unread") or []) if row else []
        return [lines for lines in self._unread[file] if lines[0] <= owner["span"][2] and owner["span"][0] <= lines[1]]

    def reads_arguments(self, owner: dict) -> bool:
        """Whether the snapshot records a read or a call of `arguments` inside the function: it does (`arguments[0] = x`
        is a read of the name, whose subscript the reader declares no write for), so the tree is not read for it."""
        return any(ref["parts"][:1] == ["arguments"] and _inside(owner, *ref["span"][:2])
                   for ref in self.facts.uses[owner["file"]])


def _parameters_read(facts: flows.Facts, owner: dict, tree, node) -> list[str]:
    """The names written in a node that the engine reads as a parameter of the function itself."""
    found, stack = [], [node]
    while stack:
        item = stack.pop()
        if item.type in flows.NAMES and any(
                read["caller"] == owner["id"] and read.get("detail") == "parameter"
                for read in facts.reads.get((owner["file"], *entries._at(item)), ())):
            found.append(entries._text(tree.source, item))
        stack.extend(item.named_children)
    return found


def _place(owner: dict, tree, declaration: dict, name: str) -> tuple[int | None, str]:
    """The place of the parameter a declaration is among the arguments of a call to the function, read from the
    function's own node in the tree, else None and why. TypeScript's `this`, which no call passes, would take a place it
    does not have: the reader leaves such a function's scope unresolved (`binding` of a `this` pattern), so none gets here."""
    span = owner["span"]
    node = tree.root.descendant_for_point_range((span[0] - 1, span[1]), (span[2] - 1, span[3]))
    if node is None or tuple(node.start_point) != (span[0] - 1, span[1]):
        return None, "the function is not where the snapshot declares it in its syntax tree"
    listed = node.child_by_field_name("parameters")
    formal = list(listed.named_children) if listed is not None else [node.child_by_field_name("parameter")]
    patterns = []
    for parameter in formal:  # the pattern a formal parameter declares: a type and a default take nothing from it
        if parameter is None or parameter.is_extra:
            continue
        if parameter.type in ("required_parameter", "optional_parameter"):
            parameter = parameter.child_by_field_name("pattern")
        elif parameter.type == "assignment_pattern":
            parameter = parameter.child_by_field_name("left")
        if parameter is not None:
            patterns.append(parameter)
    at = (declaration["line"] - 1, declaration["column"])
    for index, pattern in enumerate(patterns):
        if tuple(pattern.start_point) <= at < tuple(pattern.end_point):
            if tuple(pattern.start_point) == at and pattern.type == "identifier":
                return index, ""
            return None, f"the parameter {name} " + (
                "is a rest parameter: it holds every argument from its place on" if pattern.type == "rest_pattern"
                else "is destructured: it has no place of its own among the arguments")
    return None, "no formal parameter of the function holds the declaration"


def prove(facts: flows.Facts, view: dict) -> tuple[list[dict], list[dict]]:
    """`(proofs, gaps)` of the view's calls of the table's clients from a named function of the project.

    A proof is `{symbol, callee, index, method, site}`: the wrapper's declaration, its id in a rule's form, the position
    of the URL among its parameters, the method and the call it was proved at. A gap is `{site, symbol, reason}`, `symbol`
    the callee form of the function."""
    snapshot, proofs, gaps = _Snapshot(facts), [], []

    def refuse(owner: dict, site: str, reason: str) -> None:
        gaps.append({"site": site, "symbol": facts.named(owner["id"]), "reason": reason})

    for ref in view["references"]:
        symbols = ref.get("external_symbols") or ()
        found = [client(symbol) for symbol in symbols]
        owner = facts.declarations.get(ref.get("caller") or "")
        if not any(found) or owner is None or owner["kind"] not in ("function", "method") \
                or owner["name"] == "(anonymous)":
            continue
        site = f"{ref['file']}:{ref['span'][0]}"
        # one spec for every end: a future entry may read the URL or the method elsewhere than another end of the same call
        if not all(found) or len({(item["url"], item["method"]) for item in found}) != 1:
            refuse(owner, site, f"several ends, not all of them one client's: {', '.join(symbols)}")
            continue
        spec = found[0]
        call = flows._read_call(facts, ref, [str(part) for part in ref.get("parts") or ()])
        if isinstance(call, str):
            refuse(owner, site, call)
            continue
        args = call["args"]
        argument = flows._unwrapped(args[spec["url"]]) if spec["url"] < len(args) and args[spec["url"]] is not None \
            else None
        if argument is None:
            continue
        tree, own = call["tree"], _parameters_read(facts, owner, call["tree"], argument)
        if argument.type not in flows.NAMES:
            if own:
                refuse(owner, site, f"the URL is built from the parameter {', '.join(own)} by {argument.type}")
            continue
        name = entries._text(tree.source, argument)
        declared = snapshot.declared(owner, name)
        if not own:
            for item in (item for item in declared if item["kind"] == "parameter"):  # the engine reads a property there
                index, why = _place(owner, tree, item, name)
                refuse(owner, site, f"{name} is a parameter of the function, but the engine reads another variable "
                                    "there: it is shadowed" if index is not None else why)
                break
            continue
        if not declared:
            refuse(owner, site, f"the snapshot declares no parameter {name} in the function: it is another function's")
            continue
        if reasons := snapshot.unresolved(owner):
            refuse(owner, site, f"the function holds a scope the reader cannot close ({'; '.join(map(str, reasons))}): "
                                f"it may write {name} with no declaration")
            continue
        if lines := snapshot.unread(owner):
            refuse(owner, site, "the function holds lines the reader could not read (a syntax error), "
                                f"at {', '.join(f'{first}-{last}' for first, last in lines)}: it may write {name} there")
            continue
        if snapshot.reads_arguments(owner):
            refuse(owner, site, f"the function reads `arguments`, which can write {name} by its place")
            continue
        if [item["kind"] for item in declared] != ["parameter"]:
            refuse(owner, site, f"the parameter {name} is declared or assigned again inside the function: "
                                + ", ".join(sorted(f"{item['kind']} at line {item['line']}" for item in declared)))
            continue
        index, why = _place(owner, tree, declared[0], name)
        if index is None:
            refuse(owner, site, why)
            continue
        method = flows._value(spec["method"], call, facts)
        if method is None:
            refuse(owner, site, f"method {spec['method']}: {flows._not_literal(call)}")
            continue
        if others := snapshot.sharing(owner):
            refuse(owner, site, f"the callee form {facts.named(owner['id'])} is also that of another declaration of the "
                                f"file, at line {', '.join(str(item['line']) for item in others)}: a rule would reach both")
            continue
        proofs.append({"symbol": owner["id"], "callee": facts.named(owner["id"]), "index": index,
                       "method": method.upper(), "site": site, "at": (ref["file"], *ref["span"][:2])})
    return proofs, gaps


def _calls(view: dict) -> dict[str, list[dict]]:
    """The calls that resolve to each declaration, by its id."""
    out = defaultdict(list)
    for ref in view["references"]:
        if ref["resolution"] == "resolved" and ref.get("target_id") and not edge_view.uncertainty(ref):
            out[ref["target_id"]].append(ref)
    return out


def _services(rules: list[dict]) -> list[str]:
    """The services the recorded `offre` rules name as a text: the services of the project's own routes. A `rotta` rule
    names the service of a call, which may be another system's (a payment provider); a rule that reads its service from
    the call (`arg0`) names none."""
    named = {rule["route"]["service"] for rule in rules if rule.get("link") == "offre" and isinstance(rule.get("route"), dict)}
    return sorted(service for service in named if isinstance(service, str)
                  and not flows._ARG.match(service) and not flows._NESTED.match(service))


def _ruled(facts: flows.Facts, calls: dict, rules: list[dict]) -> set[str]:
    """The wrappers a recorded rule already names, in a rule's form: by its `callee`, or by its `written` at a call that
    resolves to the wrapper."""
    written = [rule for rule in rules if "written" in rule]
    named = {rule["callee"] for rule in rules if "callee" in rule}
    for target, refs in calls.items():
        if any(flows._written(rule, [str(part) for part in ref.get("parts") or ()], ref["file"])
               for rule in written for ref in refs):
            named.add(facts.named(target))
    return named


def _readable(facts: flows.Facts, refs: list[dict], index: int) -> int:
    """How many of the calls to a wrapper have, as argument `index`, a text the rules read."""
    count = 0
    for ref in refs:
        call = flows._read_call(facts, ref, [str(part) for part in ref.get("parts") or ()])
        count += not isinstance(call, str) and flows._value(f"arg{index}", call, facts, template=True) is not None
    return count


def _proposed(proofs: list[dict], gaps: list[dict], ruled: set[str]) -> list[tuple]:
    """`(callee, index, method, first proof)` of each proved wrapper no recorded rule names (`ruled`) and no gap blocks, by
    callee; a wrapper whose calls of the client read the route differently is a gap, added to `gaps`."""
    blocked = {gap["symbol"] for gap in gaps}
    by_callee = defaultdict(list)
    for proof in proofs:
        by_callee[proof["callee"]].append(proof)
    out = []
    for callee, found in sorted(by_callee.items()):
        if callee in ruled or callee in blocked:
            continue
        first = min(found, key=lambda proof: (proof["site"].rpartition(":")[0], int(proof["site"].rpartition(":")[2])))
        reads = sorted({(proof["index"], proof["method"]) for proof in found})
        if len(reads) != 1:
            gaps.append({"site": first["site"], "symbol": callee, "reason": "its calls of the client read the route "
                         "differently: " + ", ".join(f"argument {index} with {method}" for index, method in reads)})
            continue
        out.append((callee, *reads[0], first))
    return out


def report(facts: flows.Facts, view: dict, rules: list[dict]) -> dict:
    """The candidates and the gaps of a snapshot under the recorded rules, and the engine's `coverage` (with `why`, the view's
    reasons, when it gave no answer).

    A candidate is `{callee, rule, proof, calls, literal}` and the `rotta` rule that names the wrapper, its route read from
    the argument the proof found: the service is the one the recorded `offre` rules name when they name one, else the rule
    has none and the candidate lists `services` (none: the routes the project declares meet any service), for the model to
    choose, since `validate_rules` refuses a rule with no service and `*`. `calls` resolve to the wrapper, `literal` of
    them have a URL the rules read. A wrapper a recorded rule names has none."""
    proofs, gaps = prove(facts, view)
    calls, services = _calls(view), _services(rules)
    ruled = _ruled(facts, calls, rules)
    candidates = []
    for callee, index, method, first in _proposed(proofs, gaps, ruled):
        refs = calls.get(first["symbol"], [])
        route = {"method": method, "path": f"arg{index}"}
        if len(services) == 1:
            route = {"service": services[0], **route}
        entry = {"callee": callee, "rule": {"callee": callee, "link": "rotta", "route": route}, "proof": first["site"],
                 "calls": len(refs), "literal": _readable(facts, refs, index)}
        if len(services) != 1:
            entry["services"] = services
            if not services:
                entry["note"] = "no recorded rule names a service: the routes the project declares meet any service"
        candidates.append(entry)
    status = view["coverage"]["status"]
    return {"candidates": candidates,
            "gaps": sorted((gap for gap in gaps if gap["symbol"] not in ruled), key=lambda gap: (gap["site"], gap["reason"])),
            "coverage": status,
            # no engine answer is no wrapper: a store the snapshot rejects shows nothing else, so its reason is here
            **({"why": view["gaps"]} if status not in ("complete", "lower-bound") else {})}


def applied(facts: flows.Facts, view: dict, rules: list[dict]) -> tuple[list[dict], set[tuple]]:
    """What `flows.link_facts` applies with no model: the `rotta` rule each proved wrapper proposes, with `service(rules)`
    where the candidate names none, and the calls of the client the proofs stand on, `(file, line, column)`: their URL is
    the wrapper's parameter, read at the wrapper's own calls, so they ask for no route of their own."""
    proofs, gaps = prove(facts, view)
    asking = service(rules)
    proposed = [{"callee": callee, "link": "rotta", "route": {"service": asking, "method": method, "path": f"arg{index}"}}
                for callee, index, method, _ in _proposed(proofs, gaps, _ruled(facts, _calls(view), rules))]
    return proposed, {proof["at"] for proof in proofs}


def wrappers(manifest: Path, rules: list[dict]) -> dict:
    """`report` of a snapshot, for the command line."""
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        view = edge_view.load_edge_view(store)
        return report(flows.Facts(store, db, view), view, rules)
