"""The simple commands of a shell text, read from its syntax tree (tree-sitter bash), never run.

One reader for every shell text the pre-map reads: the scripts of a `package.json`, a GitHub step's `run`, a GitLab
job's lines, a Makefile's recipe and the shell scripts they run. No official tool gives a shell text's commands
without running it, and `shlex` splits words, not commands: it knows no `if`, `$(...)`, comment or redirection.

`commands(script)` gives each simple command, in the order it is written, as `(assigned, words)`: the variables it
sets for its program (`NAME=value` before it) and its words from the program on, each as the shell gives it once its
quotes are removed; an expansion (`$X`, `${X}`, `$(...)`, `` `...` ``) stays as written, never evaluated. A command
inside a substitution is a command too. `written(script)` gives the same with the line each command is written on
and whether the grammar read it whole (no open quote, no missing word). Both are None where the bash grammar is not
available.
"""
from __future__ import annotations

from languages import _treesitter

QUOTED = '$`"\\\n'  # what a backslash escapes in double quotes; in a bare word, any character


def _unescape(text: str, only: str | None = None) -> str:
    out, i = [], 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text) and (only is None or text[i + 1] in only):
            out.append("" if text[i + 1] == "\n" else text[i + 1])
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _word(node, source: bytes) -> str:
    """A word as the shell gives it to the program: its quotes removed, its expansions as written."""
    text = _treesitter.node_text(node, source)
    if node.type == "word":
        return _unescape(text)
    if node.type == "raw_string":
        return text[1:-1]
    if node.type == "string":
        return _unescape(text[1:-1], QUOTED)
    if node.type in ("concatenation", "command_name"):
        return "".join(_word(child, source) for child in node.children)
    return text  # an expansion, a substitution, a number, an ANSI-C string


def written(script: str) -> list[tuple[dict, list[str], str, bool]] | None:
    """Each simple command of `script` as `(assigned, words, line, whole)`: `line` the lines it is written on, its
    continuations joined (a `\\` and a newline are a space), as a gap names it; `whole` false where the tree has an
    error or a missing node in it."""
    loaded = _treesitter.get_parser("bash")
    if loaded is None:
        return None
    source = script.encode("utf-8")
    nodes = _treesitter.query_captures("bash", "(command) @command", loaded[0].parse(source).root_node).get(
        "command", [])
    rows = script.split("\n")
    found = []
    for node in sorted(nodes, key=lambda node: node.start_byte):
        name = node.child_by_field_name("name")
        if name is None:
            continue
        assigned = {}
        for child in node.children:
            if child.type == "variable_assignment":
                value = child.child_by_field_name("value")
                assigned[_treesitter.node_text(child.child_by_field_name("name"), source)] = (
                    "" if value is None else _word(value, source))
        words = [_word(name, source),
                 *(_word(argument, source) for argument in node.children_by_field_name("argument"))]
        line = "\n".join(rows[node.start_point[0]:node.end_point[0] + 1]).replace("\\\n", " ").strip()
        found.append((assigned, words, line, not node.has_error))
    return found


def commands(script: str) -> list[tuple[dict, list[str]]] | None:
    """Each simple command of `script` as `(assigned, words)` (the module's docstring)."""
    said = written(script)
    return None if said is None else [(assigned, words) for assigned, words, _, _ in said]
