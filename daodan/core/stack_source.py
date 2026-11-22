"""Catalog evidence from native Swift imports and fully qualified Elixir calls."""
from collections import defaultdict
from pathlib import PurePosixPath

from languages._treesitter import check_syntax_errors, get_parser, get_query, load_failure, node_text, query_captures
from source_files import MAX_PARSE_BYTES, STACK_SOURCE_LANGUAGES


QUERIES = {
    "swift.import": "(import_declaration (identifier . (simple_identifier) @sign))",
    "elixir.call": "(call target: (dot left: (alias) right: (identifier)) @sign)",
}


def check_sources(entries, project):
    """Return source evidence with its file and line, and why any source could not be read."""
    by_language = defaultdict(lambda: defaultdict(list))
    for entry in entries:
        for kind, values in ((entry.get("signs") or {}).get("source") or {}).items():
            language = kind.partition(".")[0]
            for value in values:
                by_language[language][kind, value].append(entry["id"])
    found, gaps = [], []
    for rel in project.files:
        language = STACK_SOURCE_LANGUAGES.get(PurePosixPath(rel).suffix.lower())
        if language not in by_language:
            continue
        signs = by_language[language]
        lines = project.lines(rel)
        source = "\n".join(lines).encode("utf-8")
        if not lines:
            reason = "source unavailable or changed since the snapshot"
        elif len(source) > MAX_PARSE_BYTES:
            reason = "source exceeds parsing size limit"
        elif (pair := get_parser(language)) is None:
            gaps.append({"kind": "source_grammar_unavailable", "path": rel, "language": language,
                         "detail": load_failure(language) or f"{language} grammar unavailable"})
            continue
        else:
            root = pair[0].parse(source).root_node
            reason = check_syntax_errors(root)
            for kind in sorted({kind for kind, _ in signs}):
                query = QUERIES[kind]
                if get_query(language, query) is None:
                    reason = f"grammar rejected the query for {kind}"
                    continue
                for node in query_captures(language, query, root).get("sign", ()):
                    if node.has_error or node.parent.has_error:
                        continue
                    if kind == "swift.import":
                        value = node_text(node, source).strip("`")
                    else:
                        module = node_text(node.child_by_field_name("left"), source).removeprefix("Elixir.")
                        function = node_text(node.child_by_field_name("right"), source)
                        value = f"{module}.{function}"
                    found.extend((ident, value, rel, node.start_point[0] + 1) for ident in signs.get((kind, value), ()))
        if reason:
            gaps.append({"kind": "unread_source", "path": rel, "detail": reason})
    return {"signs": sorted(found), "gaps": gaps}
