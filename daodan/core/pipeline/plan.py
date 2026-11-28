"""The plan (spec 8.4): which adapter runs on which files, and what each needs first, as plain data.

`plan(rows)` takes `(path, {"language": ...})` pairs, `stored` reads them from a store (every executor takes its rows
from it); a row may carry the file's `status` and, when it stands for a group of files, their number (`files`).
It reads the adapters' own declarations (`engine_pass.ENGINES`, which the stages are built from, and
`dynamic.observers()`), and gives `{"nodes": [...], "gaps": [...]}`. It states no fact about
the project, only choices; the steps run the nodes it gives and nothing else (`snapshot.write_reading`,
`engine_pass.pass_plan`, `dynamic.run`).

A node is `{id, step, adapter, [version], on, container, needs}`: `step` is the id of the step that runs it and `id` is
`<step>:<adapter>` (`read_code:<language>`, `read_code:file-level` for the files with no language,
`link_calls:<analyzer name>`, `run_and_observe:<observer entry>`); `on` is
`{"languages", "files"}` (counts, never paths), and for a resolver also `unit_kinds`; `container` is whether it runs
in Daodan's container; `needs` are the ids of the nodes it waits for. A gap is `{kind, language, files, detail}`:
`no-analyzer` (a language no analyzer lists) or `no-observer` (a language with a resolver and no observer).

A node whose need failed does not start, and says which (`blocked`), per language: a resolver needs the parser of
each of its languages, an observer the resolver of each of its.
"""
from __future__ import annotations

import collections

FILE_LEVEL = "file-level"  # the adapter of the files with no language: their entry holds no reading
# The steps that run the nodes, by their ids: the reading (`snapshot.write_reading`), `engine_pass.STEP`, `dynamic.STEP`.
READ_CODE, LINK_CALLS, RUN_AND_OBSERVE = "read_code", "link_calls", "run_and_observe"


def node_of(row: dict) -> str:
    """The reading's node a file belongs to, from its inventory row."""
    return f"{READ_CODE}:{row.get('language') or FILE_LEVEL}"


def coverage(connection) -> list[tuple[str, dict]]:
    """The snapshot's files as grouped rows: per language and parse status, how many (`sem_coverage`)."""
    return [("", {"language": language, "status": status, "files": count}) for language, status, count in
            connection.execute("SELECT language, status, COUNT(*) FROM sem_coverage GROUP BY language, status")]


def stored(store) -> list[tuple[str, dict]]:
    """The rows of a snapshot, one source for every step: the parse status of each language once the snapshot is read
    (`coverage`), else its inventory, else, for a store that has none (JSON, a store written before it), its files'
    headers' languages."""
    connection = getattr(store, "connection", None)
    if connection is not None and connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sem_coverage'").fetchone():
        rows = coverage(connection)
        if rows:
            return rows
    return list(store.iter_listed())


def _analyzers() -> list:
    """The resolvers as the pass holds them (`engine_pass.ENGINES`), each with its adapter's declaration."""
    import importlib
    import types
    import engine_pass
    found = []
    for spec in engine_pass.ENGINES:
        module = importlib.import_module(f"indexers.{spec.indexer}")
        found.append(types.SimpleNamespace(
            NAME=spec.name, LANGUAGES=spec.languages, VERSION=getattr(module, "VERSION", None),
            UNIT_KINDS=module.UNIT_KINDS, NEEDS_CONTAINER=spec.needs_container,
            SNAPSHOT_LANGUAGES=getattr(module, "SNAPSHOT_LANGUAGES", ())))
    return found


def _owner(language: str):
    """The analyzer that resolves `language`: the first that lists it."""
    return next((analyzer for analyzer in _analyzers() if language in analyzer.LANGUAGES), None)


def need(node: dict, language: str) -> str | None:
    """The id of the node of `node`'s `needs` that `language` waits for: its parser (a resolver), its resolver (an
    observer); None where it waits for none."""
    if node["step"] == LINK_CALLS:
        needed = node_of({"language": language})
    else:
        owner = _owner(language)
        needed = f"{LINK_CALLS}:{owner.NAME}" if owner else None
    return needed if needed in node["needs"] else None


def blocked(node: dict, failed: dict) -> dict[str, tuple[str, str]]:
    """The languages of `node` whose need failed, each with the need and why: `failed` maps a node id to the reason
    it failed, or to `{language: reason}` where it failed for some of the languages that wait for it."""
    found = {}
    for language in node["on"]["languages"]:
        needed = need(node, language)
        reason = failed.get(needed) if needed else None
        if isinstance(reason, dict):
            reason = reason.get(language)
        if reason is not None:
            found[language] = (needed, reason)
    return found


def _node(step: str, adapter: str, version, on: dict, container: bool, needs: list[str]) -> dict:
    return {"id": f"{step}:{adapter}", "step": step, "adapter": adapter, **({"version": version} if version else {}),
            "on": on, "container": container, "needs": needs}


def _tally(rows) -> tuple[collections.Counter, dict, set]:
    """The files per language (None: no language), the statuses each language's files have, and the languages
    held at all, outside the perimeter or not."""
    files, statuses, held = collections.Counter(), collections.defaultdict(set), set()
    for _path, row in rows:
        language = row.get("language")
        if language:
            held.add(language)
        if row.get("status") == "excluded":  # outside the perimeter: in no node, and the inventory says why
            continue
        files[language] += row.get("files", 1)
        statuses[language].add(row.get("status"))
    return files, statuses, held


def _read(files: collections.Counter) -> list[dict]:
    nodes = [_node(READ_CODE, language, None, {"languages": [language], "files": files[language]}, False, [])
             for language in sorted(language for language in files if language)]
    if files[None]:
        nodes.append(_node(READ_CODE, FILE_LEVEL, None, {"languages": [], "files": files[None]}, False, []))
    return nodes


def parse_nodes(rows) -> list[dict]:
    """The reading's nodes alone, which need no adapter registry: what the reading takes its files from."""
    return _read(_tally(rows)[0])


def plan(rows) -> dict:
    """The nodes and gaps for `rows`."""
    import dynamic
    from semantic_store import READ
    files, statuses, held = _tally(rows)
    read = {language for language, found in statuses.items() if found & set(READ)}
    languages = sorted(language for language in files if language)
    nodes = _read(files)
    analyzers = _analyzers()
    owner: dict = {}
    for analyzer in analyzers:  # a language's resolver is the first analyzer that lists it
        for language in analyzer.LANGUAGES:
            owner.setdefault(language, analyzer)
    planned = set(languages)
    for analyzer in analyzers:  # a graph built from other languages' files is planned when the snapshot holds one
        if held & set(analyzer.SNAPSHOT_LANGUAGES):
            planned.update(analyzer.LANGUAGES)
    resolved = []
    for analyzer in analyzers:
        mine = [language for language in analyzer.LANGUAGES if language in planned and owner[language] is analyzer]
        if not mine:
            continue
        sources = sorted(language for language in analyzer.SNAPSHOT_LANGUAGES if files[language])
        # A graph of other languages' files reads them with its own parsers: no reading node of the snapshot is its need.
        needs = [] if analyzer.SNAPSHOT_LANGUAGES else [node_of({"language": language}) for language in mine
                                                        if files[language]]
        nodes.append(_node(LINK_CALLS, analyzer.NAME, analyzer.VERSION,
                           {"languages": mine, "files": sum(files[language] for language in {*mine, *sources}),
                            "unit_kinds": sorted(analyzer.UNIT_KINDS)}, bool(analyzer.NEEDS_CONTAINER), needs))
        resolved += mine
    watched = set()
    for observer in dynamic.observers():
        mine = sorted(language for language in observer.LANGUAGES if language in resolved)
        watched.update(observer.LANGUAGES)
        if mine:
            nodes.append(_node(RUN_AND_OBSERVE, observer.NAME, getattr(observer, "VERSION", None),
                               {"languages": mine, "files": sum(files[language] for language in mine)}, True,
                               sorted({f"{LINK_CALLS}:{owner[language].NAME}" for language in mine})))
    gaps = []
    served = {language for analyzer in analyzers for language in analyzer.SNAPSHOT_LANGUAGES}
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
