"""Link types: how an asking point and an offering point of the flows meet, with no tool or framework named.

A link type has a role pair (who asks, who offers), a key made of the raw values a rule or a source reads, and a meeting of
two keys. `REST` is the only one: a route reached and a route declared meet by service, method and path schema; whoever
declares the route (a rule, a source of `find_entry_points`) hands its path as text, and the type reads it with no knowledge
of who wrote it. Tables, queues and events have no type of their own: who writes and who reads one meet on the same node
`store:<store>/<key>` the flows give (`flows.link_facts`), so a `STORE` type would repeat that node.

Standard library only.
"""
from __future__ import annotations

import re
from typing import Callable, NamedTuple
from urllib.parse import urlsplit


class LinkType(NamedTuple):
    """A link type: its name, its role pair (who asks, who offers), how the raw values a rule reads become a
    key (None: a gap) and how an asking key meets an offering one (None: they do not; higher is closer)."""
    name: str
    pair: tuple[str, str]
    key: Callable[..., tuple | None]
    meet: Callable[[tuple, tuple], tuple | None]


def join(link_type: LinkType, asking: list[dict], offering: list[dict]) -> list[tuple[dict, list[dict]]]:
    """Each asking point (a dict with a `key`) with the offering points it meets best: one is a link,
    several an uncertain link, none a single side."""
    out = []
    for point in asking:
        met = [(m, o) for o in offering if (m := link_type.meet(point["key"], o["key"])) is not None]
        best = max((m for m, _ in met), default=None)
        out.append((point, [o for m, o in met if m == best]))
    return out


# A route's segment is text with no grammar: the parameter spellings of the frameworks (`<id>`, `{id}`).
_PATH_PARAMETER = re.compile(r"<[^<>/]*>|\{[^{}/]*\}")


def _holes(text: str) -> str | None:
    """The text with every `${...}` as `\\0`; None when one is not closed."""
    out, i = [], 0
    while i < len(text):
        if not text.startswith("${", i):
            out.append(text[i])
            i += 1
            continue
        depth, j = 0, i + 1
        while j < len(text):
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            if depth == 0:
                break
            j += 1
        if depth:
            return None
        out.append("\0")
        i = j + 1
    return "".join(out)


def _rest_key(service, method, path) -> tuple | None:
    """(service, METHOD, path schema). The query, the fragment and the base URL before the first segment,
    literal or not, are not part of the key; a parameter, interpolated (`${id}`) or declared (`:id`, `<id>`,
    `{id}`), is `{}`. A path whose first segment is interpolated is computed: a gap."""
    text = None if None in (service, method, path) else _holes(path)
    if text is None:
        return None
    head = text.lstrip("\0")
    try:
        split = urlsplit(head)  # the query and the fragment end the path; `//host` or `scheme://host` is the base URL
    except ValueError:  # a host in brackets that never closes
        return None
    # A scheme with no `//` after it (`items:batch`) is no base URL: it stays a segment.
    based = bool(split.netloc) or bool(split.scheme) and head[len(split.scheme) + 1:].startswith("//")
    rest = split.path if based else (head[:len(split.scheme) + 1] if split.scheme else "") + split.path
    if not rest or (based or head != text) and not rest.startswith("/"):
        return None  # an interpolation glued to what follows it, or nothing after the base
    segments = [s for s in rest.split("/") if s]
    if segments and "\0" in segments[0]:
        return None
    segments = ["{}" if s.startswith(":") else _PATH_PARAMETER.sub("{}", s.replace("\0", "{}")) for s in segments]
    return str(service), str(method).upper(), "/" + "/".join(segments)


def _segment_grade(asked: str, offered: str) -> int | None:
    """2 the same, 1 a literal filling a parameter, 0 a hole glued to a literal that must equal one, None no."""
    if asked == offered:
        return 2
    if offered == "{}":
        return 1
    if "{}" in asked and "{" not in offered:
        # Both texts are Daodan's own, made by `_rest_key`: segments with `{}` for a hole, no grammar.
        pattern = "".join("[^/]*" if part == "{}" else re.escape(part) for part in re.split(r"(\{\})", asked))
        return 0 if re.fullmatch(pattern, offered) else None
    return None


ANY_SERVICE = "*"  # the service of an offered route no rule names (the tool that declares it does not know it): it meets any


def _rest_meet(asked: tuple, offered: tuple) -> tuple | None:
    """Same method and number of segments, every segment meeting, and the same service or an offered `ANY_SERVICE`
    (the asking side names its service: it is never `*`). The service comes first: a route of the asked service
    before one of `*`, so a declared route only fills where no route of a rule meets. Then (True, total) when no
    hole has to equal a literal, the most literal route first; (False, 0) otherwise, so loose candidates tie; a route
    of `*` meets only the first kind: a hole that would have to equal one of its literals is no link to a route no
    rule vouches for."""
    if asked[1] != offered[1] or offered[0] not in (asked[0], ANY_SERVICE):
        return None
    calls, routes = asked[2].strip("/").split("/"), offered[2].strip("/").split("/")
    grades = [_segment_grade(call, route) for call, route in zip(calls, routes)] if len(calls) == len(routes) else [None]
    if None in grades:
        return None
    exact, strict = offered[0] == asked[0], min(grades) >= 1
    if not (exact or strict):
        return None
    # shortcut: the service ranks before the literal, so a rule's `/x/{}` beats a declared `/x/search`, when a measured project shows the declared route was the right one
    return (exact, strict, sum(grades) if strict else 0)


REST = LinkType("rest", ("rotta", "offre"), _rest_key, _rest_meet)  # the guide's "metodo e schema del percorso"
