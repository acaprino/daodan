"""Source: the routes Next.js itself validates, `next typegen`, run in Daodan's container.

`commands` describes, in each folder whose `package.json` declares `next`, the project's own `next typegen`
(`npx --no-install`, offline: the runner's setup restores the project's packages first, `container_runner.TOOLS`, and
installs nothing else; without `next` installed `npx` would still ask the registry and fail after 70 seconds) and the print of `.next/types/validator.ts`, where each block ties a route and the kind of
config the tool checks a file against (a page, a route handler, a layout) to the import of that file. `read` reads
the blocks from the syntax tree (`typegen`) and binds each import to the one file of the snapshot with that
path and stem: a candidate with the route and no line, since the tool gives none. A route whose file is in another
language (`page.mdx`) is no candidate: what the tool writes for it is not guessed, and the gap names the file. A folder whose typegen fails or
writes no validator.ts is a gap, and the other folders are still read.
"""
from __future__ import annotations

import posixpath
from pathlib import PurePosixPath

from premap import frameworks

NAME, VERSION, RANK = "next", "daodan/premap/v4", "scanner"
SCRIPTS = ("typescript", "javascript")  # the snapshot's languages of the files a `.js` import names: `.ts`, `.tsx`, `.js`, `.jsx`
TYPES = ".next/types"
VALIDATOR = f"{TYPES}/validator.ts"


def commands(context):
    return [{"tool": NAME, "argv": argv, "cwd": folder, "env": env, "network": "none"}
            for folder in frameworks.folders(context, ("next",))
            for argv, env in ((["npx", "--no-install", "next", "typegen"], {"NEXT_TELEMETRY_DISABLED": "1", "npm_config_offline": "true"}),
                              (["cat", VALIDATOR], {}))] or None


def _next_path(path: str) -> str | None:
    """A Next.js route as `REST` reads a path: each dynamic segment (`[id]`) is a parameter, `{}`; None for a catch-all
    (`[...x]`, `[[...x]]`), which stands for several path schemas. Next.js's own table of a route's parameters is
    `ParamMap` in `.next/types/routes.d.ts` (the file `validator.ts` imports): the pre-map does not carry it (the
    Next.js source prints only `validator.ts`), so the segments of the route text are read, as the framework writes
    them: a whole segment between brackets. A text with no grammar, read with string operations."""
    # shortcut: the route text, not ParamMap of routes.d.ts (not read, not checked), and a segment like `a-[id]` stays literal, when the Next.js source also prints routes.d.ts
    segments = path.split("/")
    if any(segment.startswith(("[...", "[[...")) for segment in segments):
        return None
    return "/".join("{}" if segment.startswith("[") and segment.endswith("]") else segment for segment in segments)


def typegen(text: str) -> tuple[list[dict], int | None, list[dict]]:
    """The blocks of `.next/types/validator.ts` (`next typegen`, run in Daodan's container), read from its syntax tree
    (`QUERIES["typegen"]`), the line of the first error the tree holds (None when it parses whole), and the blocks it
    checks a file in that this reader does not read (`QUERIES["typegen_blocks"]`: a config type with no route). Each
    block is a checked file: the type of config the tool checks it against (`shape`), the route that type is written
    for (`path`) and the file it imports (`import`, relative to `.next/types`); an unread one gives its `import` and
    its `block`. The comment above a block is not read. A tree that holds an error gives no block: a file cut short
    must not pass as a short list."""
    import entries
    source = text.encode("utf-8")
    root = entries._parse(source, "typescript")
    if root is not None and root.has_error:
        return [], entries._error_line(root), []
    matches = entries._matches(source, "typescript", "typegen", root)
    read = {found["import"][0].start_byte for found in matches}
    unread = [{"import": entries._text(source, found["import"][0]), "block": " ".join(entries._text(source, found["block"][0]).split())}
              for found in entries._matches(source, "typescript", "typegen_blocks", root) if found["import"][0].start_byte not in read]
    return ([{"shape": entries._text(source, found["shape"][0]), "path": entries._text(source, found["route"][0]),
              "import": entries._text(source, found["import"][0])} for found in matches], None, unread)


def _tail(result: dict) -> str:
    return (result["stderr"] or result["stdout"]).strip()[-400:]


def read(context, commands, results):
    import entries
    import flows
    by_stem: dict[tuple[str, str], list[str]] = {}  # the import ends in `.js`: it names a script, not `page.css`
    elsewhere: dict[tuple[str, str], list[str]] = {}  # the files of that stem in another language (`page.mdx`)
    for rel, header in context.inventory.headers.items():
        path = PurePosixPath(rel)
        (by_stem if header.get("language") in SCRIPTS else elsewhere).setdefault(
            (path.parent.as_posix(), path.stem), []).append(rel)
    candidates, gaps = [], []
    for command, generated, printed in zip(commands[::2], results[::2], results[1::2]):
        folder = command["cwd"]
        if generated["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"next typegen exited with {generated['returncode']}: {_tail(generated)}"})
            continue
        if printed["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"next typegen exited with 0 and wrote no {VALIDATOR}: its distDir is not .next, "
                                   "or this Next.js has no typegen command"})
            continue
        blocks, error, unread = typegen(printed["stdout"])
        if error:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": f"{VALIDATOR} did not parse whole (an error at line {error}): it was printed cut "
                                   "short, or written as this reader does not know"})
        elif not blocks:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": f"no block of the known layout was found in {VALIDATOR}: this reader does not "
                                   "know this Next.js's layout, or the app has no page"})
        for block in unread:
            imported = posixpath.normpath(posixpath.join(folder, TYPES, block["import"]))
            path = PurePosixPath(imported)
            files = by_stem.get((path.parent.as_posix(), path.stem), [])
            gaps.append({"kind": "model_partial", "path": files[0] if len(files) == 1 else imported,
                         "detail": f"next typegen checks {imported} in a block with no route in its config type, which this "
                                   f"reader does not read: {block['block'][:300]}"})
        for block in blocks:
            imported = posixpath.normpath(posixpath.join(folder, TYPES, block["import"]))
            path = PurePosixPath(imported)
            files = by_stem.get((path.parent.as_posix(), path.stem), [])
            checks = f"next typegen checks {imported} for {block['path']}"
            if not files and elsewhere.get((path.parent.as_posix(), path.stem)):
                other = elsewhere[path.parent.as_posix(), path.stem]
                gaps.append({"kind": "model_partial", "path": other[0] if len(other) == 1 else imported,
                             "detail": f"{checks}, and the snapshot holds no TypeScript or JavaScript file with that "
                                       f"path and stem, only {', '.join(other)}: what the tool writes for it is not read"})
            elif not files:
                gaps.append({"kind": "outside_snapshot", "path": imported,
                             "detail": f"{checks}, and the snapshot holds no file with that path and stem"})
            elif len(files) > 1:
                gaps.append({"kind": "model_partial", "path": imported,
                             "detail": f"{checks}, and {len(files)} files of the snapshot have that path and stem: "
                                       f"{', '.join(files)}"})
            else:
                spec = entries.QUERIES["next"].get(block["shape"], {})
                route = _next_path(block["path"])
                candidates.append({"reader": entries.NEXT, "shape": block["shape"], "site": files[0],
                                   "symbol": f"{files[0]}::{flows.MODULE}", "path": block["path"],
                                   **({"kind": spec["kind"]} if spec.get("kind") else {}),
                                   "schema": flows.path_schema(route) if route is not None else None,
                                   **{key: spec[key] for key in ("exports", "methods") if spec.get(key)},
                                   **({"page": True} if spec.get("page") else {})})
    return {"facts": {"framework_entries": candidates} if candidates else {}, "gaps": gaps}


def from_record(report):
    """The candidates this source persisted in a pre-map and its gaps there; a pre-map made without the source, or
    where it was not needed, has none."""
    source = f"{NAME}@{VERSION}"
    return ([row for row in report.get("framework_entries", ()) if source in row["sources"]],
            [gap for gap in report["gaps"] if gap.get("source") == source])

