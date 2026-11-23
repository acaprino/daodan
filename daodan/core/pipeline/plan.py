"""The plan (spec 8.4): which adapter runs on which files, and what each needs first, as plain data.

`plan(rows)` takes the inventory's rows, `(path, {"language": ...})` pairs (`stored` reads them from a store; a row
may also carry the file's `status`, which the pass has from the snapshot), and the adapters' own declarations
(`indexers.analyzers()`, `dynamic.observers()`), and gives `{"nodes": [...], "gaps": [...]}`. It states no fact about
the project, only choices; the steps run the nodes it gives and nothing else (`snapshot.write_reading`,
`engine_pass.pass_plan`, `dynamic.run`).

A node is `{id, step, adapter, [version], on, container, needs}`: `id` is `<step>:<adapter>` (`parse:<language>`,
`parse:file-level` for the files with no language, `resolve:<analyzer entry>`, `observe:<observer entry>`); `on` is
`{"languages", "files"}` (counts, never paths), and for a resolver also `unit_kinds`; `container` is whether it runs
in Daodan's container; `needs` are the ids of the nodes it waits for. A gap is `{kind, language, files, detail}`:
`no-analyzer` (a language no analyzer lists) or `no-observer` (a language with a resolver and no observer).

A node whose need failed does not start, and says which (`blocked`), per language: a resolver needs the parser of
each of its languages, an observer the resolver of each of its.
"""
from __future__ import annotations

import collections

FILE_LEVEL = "file-level"  # the adapter of the files with no language: their entry holds no reading


def node_of(row: dict) -> str:
    """The parse node a file belongs to, from its inventory row."""
    return f"parse:{row.get('language') or FILE_LEVEL}"


def stored(store) -> list[tuple[str, dict]]:
    """The rows of a snapshot: its inventory, or, for a store that has none (JSON, a store written before it), its
    files' headers' languages."""
    rows = list(store.iter_inventory())
    return rows or [(path, {"language": header.get("language")}) for path, header in store.iter_file_headers_only()]


def _owner(language: str):
    """The analyzer that resolves `language`: the first that lists it."""
    import indexers
    return next((analyzer for analyzer in indexers.analyzers() if language in analyzer.LANGUAGES), None)


def need(node: dict, language: str) -> str:
    """The id of the node `node` waits for on `language`: its parser (a resolver), its resolver (an observer)."""
    if node["step"] == "resolve":
        return f"parse:{language}"
    owner = _owner(language)
    return f"resolve:{owner.ENTRY if owner else 'none'}"


def blocked(node: dict, failed: dict) -> dict[str, tuple[str, str]]:
    """The languages of `node` whose need failed, each with the need and why: `failed` maps a node id to the reason
    it failed, or to `{language: reason}` where it failed for some of the languages that wait for it."""
    found = {}
    for language in node["on"]["languages"]:
        needed = need(node, language)
        reason = failed.get(needed)
        if isinstance(reason, dict):
            reason = reason.get(language)
        if reason is not None:
            found[language] = (needed, reason)
    return found


def _node(step: str, adapter: str, version, on: dict, container: bool, needs: list[str]) -> dict:
    return {"id": f"{step}:{adapter}", "step": step, "adapter": adapter, **({"version": version} if version else {}),
            "on": on, "container": container, "needs": needs}


def plan(rows, record=None) -> dict:
    """The nodes and gaps for `rows`. `record`, the pre-map (None before `scan`), does not change a choice yet: the
    units of a node come from it when the plan is recomputed after the scan (8.4)."""
    import dynamic
    import indexers
    from semantic_store import READ
    files, held, read = collections.Counter(), set(), set()
    for _path, row in rows:
        language = row.get("language")
        if language:
            held.add(language)
        if row.get("status") == "excluded":  # outside the perimeter: in no node, and the inventory says why
            continue
        files[language] += 1
        if row.get("status") in READ:
            read.add(language)
    languages = sorted(language for language in files if language)
    nodes = [_node("parse", language, None, {"languages": [language], "files": files[language]}, False, [])
             for language in languages]
    if files[None]:
        nodes.append(_node("parse", FILE_LEVEL, None, {"languages": [], "files": files[None]}, False, []))
    analyzers = indexers.analyzers()
    owner: dict = {}
    for analyzer in analyzers:  # a language's resolver is the first analyzer that lists it
        for language in analyzer.LANGUAGES:
            owner.setdefault(language, analyzer)
    planned = set(languages)
    for analyzer in analyzers:  # a graph built from other languages' files is planned when the snapshot holds one
        if held & set(getattr(analyzer, "SNAPSHOT_LANGUAGES", ())):
            planned.update(analyzer.LANGUAGES)
    resolved = []
    for analyzer in analyzers:
        mine = [language for language in analyzer.LANGUAGES if language in planned and owner[language] is analyzer]
        if not mine:
            continue
        sources = sorted(language for language in getattr(analyzer, "SNAPSHOT_LANGUAGES", ()) if files[language])
        counted = sorted({*mine, *sources})
        nodes.append(_node("resolve", analyzer.ENTRY, getattr(analyzer, "VERSION", None),
                           {"languages": mine, "files": sum(files[language] for language in counted),
                            "unit_kinds": sorted(analyzer.UNIT_KINDS)},
                           bool(analyzer.NEEDS_CONTAINER), [f"parse:{language}" for language in counted
                                                            if files[language]]))
        resolved += mine
    watched = set()
    for observer in dynamic.observers():
        mine = sorted(language for language in observer.LANGUAGES if language in resolved)
        watched.update(observer.LANGUAGES)
        if mine:
            nodes.append(_node("observe", observer.ENTRY, getattr(observer, "VERSION", None),
                               {"languages": mine, "files": sum(files[language] for language in mine)}, True,
                               sorted({f"resolve:{owner[language].ENTRY}" for language in mine})))
    gaps = []
    served = {language for analyzer in analyzers for language in getattr(analyzer, "SNAPSHOT_LANGUAGES", ())}
    for language in languages:  # a graph of other languages' files serves one whose files it reads no code of
        if language not in owner and (language not in served or language in read):
            gaps.append({"kind": "no-analyzer", "language": language, "files": files[language], "detail":
                         f"{files[language]} {language} files are in the snapshot and no analyzer lists the language: "
                         "no graph"})
    for language in sorted(resolved):
        if language not in watched:
            gaps.append({"kind": "no-observer", "language": language, "files": files[language], "detail":
                         f"{language}: no observer runs its tests, so its graph holds no observed edge"})
    return {"nodes": nodes, "gaps": gaps}
