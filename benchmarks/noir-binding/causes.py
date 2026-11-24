"""From the facts `measure.py` records for each endpoint of Noir's report to the causes of an unbound endpoint and the test of each candidate fix.

Everything here reads the recorded facts and nothing else. A cause is an ordered mechanical predicate over those facts (the first one that holds); there is
no rule for a framework, a library or a way of writing a handler. The endpoints no predicate names are counted as `unclassified` and listed.
"""
import pathlib
import re

SEGMENT = re.compile(r"[A-Za-z_$][\w$]*")  # an identifier inside a handler name: Noir's name is an identifier, not code with a grammar
NEAR = 3  # lines: a mapping annotation, a decorator or an attribute sits within this distance above the declaration it belongs to
CLOSURE = "closure"  # the word Noir writes for a handler that is a function written in place


def parts(name: str | None) -> list[str]:
    return SEGMENT.findall(name or "")


def tail(name: str | None) -> str | None:
    found = parts(name)
    return found[-1] if found else None


def last_of(d: dict) -> str | None:
    """The last identifier of a declaration's name: the snapshot writes a Go method `Type.Method`, a function with no name `(anonymous)` (no identifier)."""
    return None if d["name"].startswith("(") else tail(d["name"])


def cited_path(row: dict) -> str:
    return ((row.get("handler") or {}).get("path") or (row.get("code_path") or {}).get("path") or "")


def suffix(row: dict) -> str:
    return pathlib.PurePosixPath(row.get("file") or cited_path(row)).suffix or "(none)"


def stage(row: dict) -> str:
    """Where an endpoint of Noir's report stops: `http` (it reaches the binder), another protocol, or dropped before it."""
    if row.get("dropped"):
        return "no path" if row["dropped"].startswith("no path") else "dropped"
    return "http" if row.get("shape") == "http" else "other protocol"


def language(row: dict) -> str | None:
    return (row.get("file_header") or {}).get("language")


NOT_CODE = "no function of the project serves the endpoint"
NO_FUNCTION = "the snapshot holds no function where Noir cites"
NO_HANDLER = "Noir gives no handler"
MISMATCH = "Noir cites or names the handler and the snapshot holds it: a naming or position mismatch"
OTHER = "unclassified"


def cause(row: dict) -> tuple[str, str]:
    """Why an http endpoint that the binder leaves unbound is unbound: (the group, the cause), the first predicate that holds."""
    handler = row["row_handler"]
    json_name = (row.get("handler") or {}).get("name")
    covering = row["covering"]
    if not row["line"]:
        return NOT_CODE, "Noir cites a file and no line (a static file it serves)"
    if row["functions_in_file"] == 0:
        what = language(row)
        if row.get("file_header") is None or what is None:
            return NO_FUNCTION, "the cited file is not read by the snapshot (build file, configuration, specification, or a language it does not read)"
        if what == "markup":
            return NO_FUNCTION, "the cited file is markup (a template or a component with its code inside)"
        return NO_FUNCTION, "the snapshot holds no function in the cited code file"
    if not handler:
        if json_name:
            return MISMATCH, "the name is lost between Noir and the row (the handler has a name and no path)"
        if any(c["line"] == row["line"] for c in row["classes"]):
            return NO_HANDLER, "Noir names no handler and cites the header of a class (its actions are inherited: the class is the handler, not a function)"
        if candidates(row, "nested-below"):
            return NO_HANDLER, "Noir names no handler and a function nested in the covering function starts just below the cited line (a decorator or attribute line)"
        return NO_HANDLER, "Noir names no handler" + (", the line is inside a function (the registration)" if covering else ", no function covers the line")
    if handler == CLOSURE:
        if any(d["line"] == row["line"] for d in covering):
            return MISMATCH, "Noir names a closure and a function starts at the cited line"
        return NOT_CODE, "Noir names a closure and no function starts at the cited line (a mapping the framework answers, a health check)"
    if row["exact_matches"] > 1:
        return OTHER, "two functions of that name cover the line"
    if candidates(row, "qualified-suffix") or candidates(row, "last-part-covering"):
        if "(" in handler:
            return MISMATCH, "the name carries call parentheses (`f()`) and a covering function has that name"
        if candidates(row, "qualified-suffix"):
            return MISMATCH, "the name is the end of a covering function's qualified name (the class or function around it is not in Noir's name)"
        return MISMATCH, "the last part of the name is a covering function's name, with a receiver or object variable in front"
    if candidates(row, "class-of-covering"):
        return MISMATCH, "the name is the class that owns the covering function (a class-based view)"
    here = row["named_in_file"]
    if here:
        below = [d["line"] - row["line"] for d in here if d["line"] > row["line"]]
        if below and min(below) <= NEAR:
            return MISMATCH, "the line is above the function (decorator, annotation or attribute line)"
        return OTHER, "the file has the name at another line" + (", and another function covers the line" if covering else ", and no function covers the line")
    if row["named_elsewhere_count"] and not starts_at(row):
        return OTHER, "the name is a function of another file"
    where = ", and a function starts at the cited line" if starts_at(row) else (", and another function covers the line" if covering else ", and no function covers the line")
    return (MISMATCH if starts_at(row) else OTHER), ("no declaration ends with the last part of the name" if len(parts(handler)) > 1 else "no declaration has that name") + where


def starts_at(row: dict) -> list[dict]:
    return [d for d in row["covering"] if d["line"] == row["line"]]


def candidates(row: dict, fix: str) -> list[dict]:
    """The declarations a candidate fix would bind the endpoint to (more than one: ambiguous, none: the fix does not apply). A fix reads the endpoint's
    cited line and handler name against the snapshot's declarations: no application of it needs a name of a framework."""
    wanted, covering = row["row_handler"], row["covering"]
    last = tail(wanted)
    if fix == "innermost-covering":  # a control, with no name: the function with the fewest lines that covers the line (the registration function, for a route with no handler)
        return covering[:1] if len(covering) == 1 or (len(covering) > 1 and covering[0]["end"] - covering[0]["line"] < covering[1]["end"] - covering[1]["line"]) else covering
    if fix == "nested-below":  # no name: the functions that start at most BELOW lines under the line Noir cites for the route, inside the function that covers that line
        site = row.get("code_site") or {}
        inside = site.get("covering") or []
        return [d for d in site.get("below", []) if inside and d["end"] <= inside[0]["end"]]
    if wanted is None:  # Noir cites the line of the route's registration, not of a function: no fix has a handler to tie it to
        return []
    if fix == "qualified-suffix":  # the identifiers of the name are the last identifiers of the qualified name of a function that covers the line
        words = parts(wanted)
        return [d for d in covering if words and parts(d["qn"])[-len(words):] == words]
    if fix == "class-of-covering":  # the name is the qualified name of the class that owns a function that covers the line
        words = parts(wanted)
        return [d for d in covering if words and len(parts(d["qn"])) > len(words) and parts(d["qn"])[:-1][-len(words):] == words]
    if fix == "last-part-covering":  # the last identifier of the name is the `name` of a function that covers the line
        return [d for d in covering if last and last_of(d) == last]
    if fix == "starts-at-line":  # a function starts at the cited line (Noir cites the line of the handler's definition)
        return starts_at(row)
    if fix == "combined":  # every fix above that binds, and the functions they bind to: one function when they agree, more when they do not
        seen = {}
        for part in ("qualified-suffix", "last-part-covering", "class-of-covering", "starts-at-line"):
            for d in candidates(row, part):
                seen[(d["name"], d["line"])] = d
        return list(seen.values())
    if fix == "name-above":  # the function of that name starts at most NEAR lines below the cited line (decorator, annotation)
        return [d for d in row["named_in_file"] if last_of(d) == last and 0 < d["line"] - row["line"] <= NEAR] if last else []
    if fix == "name-in-file":  # the last identifier is the `name` of exactly one function of the file, wherever it is
        return [d for d in row["named_in_file"] if last_of(d) == last] if last else []
    if fix == "name-in-project":  # the last identifier names exactly one function of the project
        shown = [d for d in row["named_in_file"] if last_of(d) == last] + [d for d in row["named_elsewhere"] if last_of(d) == last]
        return shown if last and row["named_elsewhere_count"] <= len(row["named_elsewhere"]) else shown + [{"name": last, "line": -1}] * 2
    raise KeyError(fix)


FIXES = ("qualified-suffix", "last-part-covering", "class-of-covering", "starts-at-line", "combined", "nested-below", "name-above", "name-in-file", "name-in-project", "innermost-covering")
FOR_NO_HANDLER = ("nested-below", "innermost-covering")  # the fixes that are for an endpoint Noir gives no handler (measured on the bound ones too, as a control)


def same(a: dict, b: dict) -> bool:
    return (a["name"], a["line"], a.get("file")) == (b["name"], b["line"], b.get("file"))
