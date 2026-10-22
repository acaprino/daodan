# /// script
# requires-python = ">=3.11"
# dependencies = ["multilspy>=0.0.35"]
# ///
"""Spike stage 2 for language servers: count real call edges, not declarations.

`textDocument/definition` at the start of `receiver.method()` returns the
receiver's declaration, which is not a call edge. This stage asks for the
definition of the callee name itself and grades the target's symbol kind with
`textDocument/documentSymbol`, so a declaration is never merged into an edge.

Grades are reported separately and never merged:

* `edge-call`               - kind 6 Method, 9 Constructor, 12 Function
* `edge-instantiation`      - kind 5 Class
* `edge-variable-binding`   - kind 13 Variable, 8 Field, 7 Property, plus kind
  14 Constant, because tsserver reports `const f = vi.fn()` and
  `const useStore = create()(...)` as Constant and that is exactly the
  "a binding that may hold a callable" case this grade exists for. The
  prescribed {13, 8, 7} subset stays reproducible through
  `variable_binding_prescribed_kinds_only` and `binding_kind_split`. This is a
  *candidate* edge: hand-checked separately, never added to `edge-call`.
  A definition that lands inside a symbol without naming it (`kind_match =
  "containing-nested"`, in practice a parameter or a local binding) is graded
  here too, because reporting the enclosing function's kind for it is how a
  parameter of an arrow function gets counted as a project call edge.
* `definition-is-type-not-callable` - kind 10 Enum, 11 Interface, 2 Module,
  3 Namespace, 4 Package
* `definition-kind-unknown` - no document symbol matched the target position
* `definition-kind-not-graded(kind=N)` - a kind outside every category above;
  kept visible instead of being folded into a neighbour.

Fixes made in this revision (measurement campaign, 2026-10-22), each at its
cause rather than in the invocation:

1. `CALLABLE_KINDS` counted Enum(10), Interface(11) and Variable(13) as call
   edges. Replaced by the graded categories above.
2. `kind_at()` matched only on line span, so a method could be classified as
   its enclosing class. An exact `selectionRange.start == (line, character)`
   match is now preferred, innermost-containing (line *and* character) is the
   fallback, and the path that produced the kind is recorded as `kind_match`.
3. `request_document_symbols` returns a 2-tuple `(flat_symbols, tree)`; the
   previous code cached the tuple and then iterated it, so the first `symbol`
   was a list and `symbol.get(...)` raised `AttributeError`. The script could
   never have completed a run. The list is now unpacked.
4. Fix 4: when the workspace *is* the snapshot root, `relative_to(...).as_posix()
   + "/"` produced `"./"`, which matches no manifest key. The root case now
   yields `""`.
5. `dynamic-callee` records carry `parts: []`, so the old `if not parts: skip`
   silently dropped the whole category - 29% of the Rust population. The callee
   expression is now taken from the record's `span` and probed at its last
   identifier, falling back to the span start; `probe_kind` records which.
6. TS/JS, gopls and (partly) JDTLS are yielded by multilspy before they can
   answer cross-file queries, and `SyncLanguageServer` waits forever per
   request. An explicit, bounded, validated readiness wait now runs first, and
   every request is time-boxed. A run that never becomes ready exits non-zero
   and is never written up as a zero.
7. `--source-root` / `--workspace-rel` separate the three things the old
   `--project` conflated: the directory handed to the server, the on-disk root
   manifest keys resolve against, and the manifest prefix this workspace owns.

Found by running it, and fixed here rather than in the invocation:

8. The callee was located with `line.find(method, c0)`, which matches a *prefix*
   and takes the *first* occurrence. Probing `max` in
   `let max_attempts = max_attempts.max(1)` landed on `max_attempts`, and probing
   `retry_after` in `let retry_after = self.circuit_breaker.retry_after(...)`
   landed on the `let` binding. The name is now matched as a whole identifier and
   the **last** occurrence inside the recorded span is used, since the span is the
   callee expression. `probe_kind` names the strategy that produced the position.
9. JDTLS answers `textDocument/definition` with `jdt://contents/<container>/
   <package>/<Class>.class` for a JDK class and for anything inside a jar.
   Converting that to a path invents a file, which then fails the workspace test,
   so 711 of 1,000 Java positions were reported as `outside-workspace` instead of
   `external-definition`. The URI scheme now decides before any path logic runs.
10. `kind_at` read only top-level `range` / `selectionRange`. A client that does
    not advertise `hierarchicalDocumentSymbolSupport` is answered with the legacy
    flat `SymbolInformation`, whose range sits under `location`, so every gopls
    symbol looked rangeless: 932 of 1,000 Go positions came back
    `definition-kind-unknown` and the run reported **zero** edges while gopls had
    in fact resolved 93 % of them. Both response shapes are now normalised.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sqlite3
import sys
import time
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "plugins" / "codebase-map" / "skills" / "map-method" / "scripts"))
from snapshot_store import _unpack, open_snapshot  # noqa: E402

from multilspy import SyncLanguageServer  # noqa: E402
from multilspy.multilspy_config import MultilspyConfig  # noqa: E402
from multilspy.multilspy_logger import MultilspyLogger  # noqa: E402

SYMBOL_KIND_NAMES = {
    1: "File", 2: "Module", 3: "Namespace", 4: "Package", 5: "Class", 6: "Method",
    7: "Property", 8: "Field", 9: "Constructor", 10: "Enum", 11: "Interface",
    12: "Function", 13: "Variable", 14: "Constant", 15: "String", 16: "Number",
    17: "Boolean", 18: "Array", 19: "Object", 20: "Key", 21: "Null",
    22: "EnumMember", 23: "Struct", 24: "Event", 25: "Operator", 26: "TypeParameter",
}

EDGE_CALL_KINDS = {6, 9, 12}                 # Method, Constructor, Function
EDGE_INSTANTIATION_KINDS = {5}               # Class
# Variable, Field, Property, and Constant. Constant(14) belongs here rather than
# in an ungraded bucket: tsserver reports `const f = vi.fn()` and
# `const useStore = create()(...)` as kind 14, which is exactly the
# "a binding that may hold a callable" case this grade exists for. The split by
# kind is reported separately in `binding_kind_split` so the narrower
# {13, 8, 7} reading stays reproducible; nothing here is ever merged into
# `edge-call`.
EDGE_VARIABLE_BINDING_KINDS = {13, 8, 7, 14}
EDGE_VARIABLE_BINDING_PRESCRIBED = {13, 8, 7}
TYPE_NOT_CALLABLE_KINDS = {10, 11, 2, 3, 4}  # Enum, Interface, Module, Namespace, Package

EDGE_GRADES = ("edge-call", "edge-instantiation", "edge-variable-binding")

# Path fragments that mark a definition as belonging to a dependency rather than
# to the corpus. Matched case-insensitively on the posix form of the target. A
# toolchain installed somewhere unusual (a scratch Go root holding the standard
# library sources, for instance) is added per run with --external-marker.
DEFAULT_EXTERNAL_MARKERS = (
    "node_modules", "/go/pkg/mod/", "gomodcache", ".m2/repository", "/.cargo/",
    "cargo-home/registry", "/.rustup/", "/lib/rustlib/",
    "typescript/lib", ".gradle/", "site-packages", "/jdt.ls/", "vscode-java",
)


def go_root_marker() -> tuple[str, ...]:
    """The Go standard library lives under GOROOT, wherever the toolchain is."""
    import shutil
    import subprocess
    go = shutil.which("go")
    if go is None:
        return ()
    try:
        root = subprocess.run([go, "env", "GOROOT"], capture_output=True, text=True,
                              timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ()
    return (Path(root).resolve().as_posix().rstrip("/") + "/",) if root else ()

IDENT_RE = re.compile(r"[A-Za-z0-9_$]+")
IDENT_CHARS = "A-Za-z0-9_$"


def callee_pattern(method: str) -> re.Pattern:
    """The callee name as a whole identifier.

    `line.find(method)` matches a *prefix*, so probing `max` in
    `let max_attempts = max_attempts.max(1)` lands on `max_attempts` and asks the
    server about the wrong token. Requiring a non-identifier boundary on both
    sides removes that class of misprobe.
    """
    return re.compile(rf"(?<![{IDENT_CHARS}]){re.escape(method)}(?![{IDENT_CHARS}])")


def uri_to_path(uri: str) -> Path | None:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return None
    return Path(url2pathname(unquote(parsed.path)))


def grade_of(kind):
    if kind is None:
        return "definition-kind-unknown"
    if kind in EDGE_CALL_KINDS:
        return "edge-call"
    if kind in EDGE_INSTANTIATION_KINDS:
        return "edge-instantiation"
    if kind in EDGE_VARIABLE_BINDING_KINDS:
        return "edge-variable-binding"
    if kind in TYPE_NOT_CALLABLE_KINDS:
        return "definition-is-type-not-callable"
    return f"definition-kind-not-graded(kind={kind}:{SYMBOL_KIND_NAMES.get(kind, '?')})"


def prefix_of(workspace_rel: str | None) -> str:
    """Manifest-relative prefix, with the root case fixed to an empty string."""
    if workspace_rel is None:
        return ""
    normalised = workspace_rel.strip().replace("\\", "/").strip("/")
    return f"{normalised}/" if normalised else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True,
                        help="directory handed to the language server as its workspace root")
    parser.add_argument("--source-root", type=Path, default=None,
                        help="on-disk root that manifest-relative keys resolve against; "
                             "defaults to the manifest's own `root` metadata")
    parser.add_argument("--workspace-rel", default=None,
                        help="manifest-relative prefix selecting this workspace's files and "
                             "stripped to make server-relative paths; empty string = the whole "
                             "snapshot; defaults to --project relative to --source-root")
    parser.add_argument("--language", default="typescript",
                        choices=["typescript", "javascript", "java", "go", "rust"])
    parser.add_argument("--files", type=int, default=25)
    parser.add_argument("--per-file", type=int, default=40)
    parser.add_argument("--server-binary", default=None,
                        help="explicit server executable; required on Windows for the npm-shim "
                             "servers, where multilspy launches the extensionless file and fails "
                             "with WinError 193")
    parser.add_argument("--server-install-dir", default=None,
                        help="multilspy server_install_dir; keeps a downloaded server inside the "
                             "bench instead of ~/.multilspy/lsp")
    parser.add_argument("--request-timeout", type=int, default=180,
                        help="per-request wait in seconds; multilspy's own default is unbounded")
    parser.add_argument("--init-timeout", type=int, default=3600,
                        help="server start-up wait in seconds. multilspy applies its single "
                             "`timeout` to BOTH initialization and every request, and for "
                             "rust-analyzer initialization includes waiting for "
                             "`experimental/serverStatus` quiescent, i.e. the whole cold crate "
                             "fetch and index. The two are separated here: init gets this value, "
                             "then the per-request timeout is restored before measuring.")
    parser.add_argument("--ready-timeout", type=int, default=300,
                        help="bounded wait for the server to answer a known cross-file definition")
    parser.add_argument("--ready-interval", type=float, default=5.0)
    parser.add_argument("--ready-min-resolved", type=int, default=1)
    parser.add_argument("--ready-probe-count", type=int, default=4,
                        help="auto probes taken from call refs our own resolver already resolved "
                             "cross-file; 0 disables them")
    parser.add_argument("--ready-probe", type=Path, default=None,
                        help="JSON list of {file, line, character, label}; line is 1-based")
    parser.add_argument("--population-json", type=Path, default=None,
                        help="manifest_probe.py output used to weight the extrapolation by reason")
    parser.add_argument("--external-marker", action="append", default=[],
                        help="extra path fragment marking a dependency definition")
    parser.add_argument("--label", default=None)
    parser.add_argument("--log-file", type=Path, default=None,
                        help="capture the server's window/logMessage traffic; multilspy's own "
                             "logger has no handler, so without this the evidence is dropped")
    parser.add_argument("--max-edge-records", type=int, default=0,
                        help="0 = write a record for every probed position")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    workspace = args.project.resolve()
    if not workspace.is_dir():
        raise SystemExit(f"--project {workspace} is not a directory")
    with open_snapshot(args.manifest) as store:
        manifest_root_meta = store.metadata.get("root")
    source_root = (args.source_root or Path(manifest_root_meta)).resolve()
    if not source_root.is_dir():
        raise SystemExit(f"--source-root {source_root} is not a directory")

    if args.workspace_rel is not None:
        prefix = prefix_of(args.workspace_rel)
    else:
        try:
            relative = workspace.relative_to(source_root).as_posix()
        except ValueError:
            raise SystemExit(
                f"--project {workspace} is not under --source-root {source_root}; "
                f"pass --workspace-rel explicitly")
        prefix = prefix_of("" if relative == "." else relative)

    external_markers = tuple(m.lower() for m in DEFAULT_EXTERNAL_MARKERS) + \
        tuple(m.lower().replace("\\", "/") for m in args.external_marker) + \
        (tuple(m.lower() for m in go_root_marker()) if args.language == "go" else ())

    db = sqlite3.connect(f"file:{args.manifest}?mode=ro", uri=True)

    # --- our own lexical baseline over the same prefix, for the report --------
    base_params: list = [args.language]
    base_where = "c.language = ?"
    if prefix:
        base_where += " AND r.file LIKE ?"
        base_params.append(prefix + "%")
    lexical = {"resolved": 0, "unresolved": 0, "unbound_name": 0, "measurable": 0}
    for resolution, count in db.execute(
            f"SELECT r.resolution, COUNT(*) FROM sem_references r "
            f"JOIN sem_coverage c ON c.file = r.file "
            f"WHERE r.kind='call' AND ({base_where}) GROUP BY r.resolution", base_params):
        if resolution == "resolved":
            lexical["resolved"] += count
        else:
            lexical["unresolved"] += count
    lexical["total"] = lexical["resolved"] + lexical["unresolved"]
    lexical["lexical_resolved_share"] = (lexical["resolved"] / lexical["total"]) \
        if lexical["total"] else None

    by_file = collections.Counter()
    reason_population = collections.Counter()
    positions: dict[str, list[tuple[int, int, int, int, list[str], str]]] = collections.defaultdict(list)
    for file, line, column, l1, c1, blob in db.execute(
            f"SELECT r.file, r.l0, r.c0, r.l1, r.c1, r.payload FROM sem_references r "
            f"JOIN sem_coverage c ON c.file = r.file "
            f"WHERE r.kind='call' AND r.resolution!='resolved' AND ({base_where})", base_params):
        record = _unpack(blob)
        reason = record.get("reason") or "none"
        reason_population[reason] += 1
        if reason == "unbound-name":
            continue
        lexical["measurable"] += 1
        by_file[file] += 1
        positions[file].append((line, column, l1, c1, record.get("parts") or [], reason))
    sample = [file for file, _ in by_file.most_common(args.files)]
    selected = [(file, item) for file in sample for item in positions[file][:args.per_file]]
    if not selected:
        raise SystemExit(f"no unresolved {args.language} call references under prefix {prefix!r}")

    sample_reason_counts = collections.Counter(item[5] for _, item in selected)

    # --- readiness probes ----------------------------------------------------
    probes: list[dict] = []
    if args.ready_probe:
        for entry in json.loads(args.ready_probe.read_text(encoding="utf-8")):
            probes.append({"file": entry["file"], "line": int(entry["line"]),
                           "character": int(entry["character"]),
                           "label": entry.get("label", "explicit"), "origin": "explicit"})
    if args.ready_probe_count:
        probe_where = ("r.kind='call' AND r.resolution='resolved' AND r.target_id IS NOT NULL "
                       f"AND c.language=?")
        probe_params: list = [args.language]
        if prefix:
            probe_where += " AND r.file LIKE ?"
            probe_params.append(prefix + "%")
        rows = list(db.execute(
            f"SELECT r.file, r.l0, r.c0, r.target_id FROM sem_references r "
            f"JOIN sem_coverage c ON c.file = r.file WHERE {probe_where}", probe_params))

        # Prefer cross-file targets: they need the server's project model, not
        # just a parsed buffer, which is what makes them a real readiness signal.
        def is_cross_file(file: str, target_id: str) -> bool:
            owner = (target_id or "").split("::", 1)[0]
            return bool(owner) and owner != file

        rows.sort(key=lambda r: 0 if is_cross_file(r[0], r[3]) else 1)
        seen_files: set[str] = set()
        auto_added = 0
        for file, line, column, target_id in rows:
            if auto_added >= args.ready_probe_count:
                break
            if file in seen_files:
                continue
            seen_files.add(file)
            auto_added += 1
            probes.append({"file": file, "line": line, "character": column,
                           "label": f"lexical-resolved -> {target_id}",
                           "origin": "lexical-resolved",
                           "cross_file": is_cross_file(file, target_id)})

    log_messages: list[str] = []
    if args.log_file:
        import logging

        class _Capture(logging.Handler):
            def emit(self, record):
                try:
                    text = record.getMessage()
                except Exception:  # noqa: BLE001
                    return
                log_messages.append(text[:500])
                if len(log_messages) > 20000:
                    del log_messages[:5000]

        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = _Capture()
        handler.setLevel(logging.DEBUG)
        logger = logging.getLogger("multilspy")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.addHandler(logging.FileHandler(args.log_file, encoding="utf-8"))

    settings = {"code_language": args.language}
    if args.server_binary:
        settings["server_binary"] = args.server_binary
    if args.server_install_dir:
        settings["server_install_dir"] = args.server_install_dir
    server = SyncLanguageServer.create(MultilspyConfig.from_dict(settings),
                                       MultilspyLogger(), str(workspace),
                                       timeout=args.init_timeout)

    verdicts = collections.Counter()
    by_reason = collections.defaultdict(collections.Counter)
    by_grade_reason = collections.defaultdict(collections.Counter)
    edges = collections.Counter()
    examples = collections.defaultdict(list)
    latencies: list[float] = []
    kind_match_counts = collections.Counter()
    binding_split = collections.Counter()
    type_kinds = collections.Counter()
    probe_kind_counts = collections.Counter()
    external_packages = collections.Counter()
    external_schemes = collections.Counter()
    outside_targets = collections.Counter()
    records: list[dict] = []
    symbol_cache: dict[str, list] = {}
    symbol_errors: dict[str, str] = {}
    source_cache: dict[str, list[str]] = {}

    def server_relative(file: str) -> str:
        return file[len(prefix):] if prefix and file.startswith(prefix) else file

    def source_lines(file: str) -> list[str]:
        if file not in source_cache:
            path = source_root / PurePosixPath(file)
            try:
                source_cache[file] = path.read_text(encoding="utf-8",
                                                    errors="replace").splitlines()
            except OSError:
                source_cache[file] = []
        return source_cache[file]

    def normalise_symbol(symbol: dict) -> dict:
        """Accept both LSP documentSymbol response shapes.

        A client that advertises `hierarchicalDocumentSymbolSupport` gets
        `DocumentSymbol[]`, whose items carry `range` and `selectionRange` at the
        top level. A client that does not gets the legacy `SymbolInformation[]`,
        whose items carry neither: the range is nested under `location`.
        multilspy's gopls `initialize_params.json` declares no documentSymbol
        capability at all, so gopls answers in the legacy shape and every symbol
        looks rangeless. Without this hoist, `kind_at` matches nothing and a
        whole language measures as `definition-kind-unknown` with zero edges,
        which reads as "the engine found nothing" when it in fact found
        everything and the client could not see the kind.
        """
        if symbol.get("range") or symbol.get("selectionRange"):
            return symbol
        location = symbol.get("location") or {}
        span = location.get("range")
        if not span:
            return symbol
        normalised = dict(symbol)
        normalised["range"] = span
        normalised["selectionRange"] = span
        return normalised

    def symbol_kinds(relative: str) -> list:
        if relative not in symbol_cache:
            try:
                # request_document_symbols returns (flat_symbols, tree_or_None).
                symbols, _tree = server.request_document_symbols(relative)
                symbol_cache[relative] = [normalise_symbol(s) for s in (symbols or [])]
                if not symbol_cache[relative]:
                    symbol_errors[relative] = "empty-document-symbol-response"
            except Exception as error:  # noqa: BLE001
                symbol_cache[relative] = []
                symbol_errors[relative] = f"{type(error).__name__}: {error}"[:200]
        return symbol_cache[relative]

    target_source_cache: dict[str, list[str]] = {}

    def target_lines(relative: str) -> list[str]:
        """Source of a definition target, read from the server's own workspace."""
        if relative not in target_source_cache:
            try:
                target_source_cache[relative] = (workspace / PurePosixPath(relative)).read_text(
                    encoding="utf-8", errors="replace").splitlines()
            except OSError:
                target_source_cache[relative] = []
        return target_source_cache[relative]

    def identifier_at(relative: str, line: int, character: int) -> str | None:
        """The identifier starting at a position in the target file, if any."""
        lines = target_lines(relative)
        if not (0 <= line < len(lines)):
            return None
        text = lines[line]
        if not (0 <= character < len(text)):
            return None
        match = re.compile(rf"[{IDENT_CHARS}]+").match(text, character)
        return match.group(0) if match else None

    def name_matches(symbol_name, identifier: str) -> bool:
        """Whether a document symbol's name is the identifier at the target.

        gopls answers the legacy flat `SymbolInformation` shape and qualifies a
        method with its receiver, so the symbol for `func (l *Set) Len() int` is
        named `(*Set).Len` and the one for `func (k Key) String(...)` is
        `(Key).String`. Comparing that against the bare identifier written at the
        definition never matches, and every Go method definition then falls
        through to `containing-nested` and is demoted to a binding candidate even
        though the position is exactly the method's declaration. Other servers
        qualify with a container instead (`Foo.bar`, `pkg.Func`), so the last
        dotted segment is compared as well. The range test still has to hold,
        which is what keeps the looser comparison from matching a same-named
        symbol elsewhere in the file.
        """
        if not symbol_name:
            return False
        if symbol_name == identifier:
            return True
        return symbol_name.rsplit(".", 1)[-1] == identifier

    def kind_at(relative: str, line: int, character: int):
        """(kind, name, kind_match) for a definition position.

        Four rules, in order of how much they prove:

        1. `selection` - a document symbol's `selectionRange.start` *is* the
           position. The server pointed at a named symbol.
        2. `name-match` / `name-match-qualified` - a symbol whose range contains
           the position and whose `name` is the identifier actually written at
           that position, compared exactly or, when the server qualifies it, on
           its last dotted segment. This is what decides the legacy flat
           `SymbolInformation` shape, where the only range available covers the
           whole declaration, so a position inside a function body is
           geometrically indistinguishable from the function's own header.
           Reading the identifier settles it. The two values are reported
           separately because the qualified comparison is the looser of the two.
        3. `containing-header` - the position is at or before the innermost
           containing symbol's own name, so it is that symbol's declaration
           header. Normal for `public static int foo()`, `pub fn`, `func`, where
           the range starts at the modifiers and the selection range at the name.
        4. `containing-nested` - the position is inside the symbol, past its
           name, and nothing names it: a parameter or a local binding. Reporting
           the enclosing function's kind here is how a parameter of an arrow
           function gets counted as a project call edge, so the position is
           graded as a binding candidate instead.
        """
        symbols = symbol_kinds(relative)
        exact = None
        for symbol in symbols:
            selection = (symbol.get("selectionRange") or {}).get("start") or {}
            if selection.get("line") == line and selection.get("character") == character:
                span = symbol.get("range") or symbol.get("selectionRange") or {}
                area = ((span.get("end", {}).get("line", 0) - span.get("start", {}).get("line", 0)),
                        (span.get("end", {}).get("character", 0)
                         - span.get("start", {}).get("character", 0)))
                if exact is None or area < exact[0]:
                    exact = (area, symbol.get("kind"), symbol.get("name"))
        if exact is not None:
            return exact[1], exact[2], "selection"

        written = identifier_at(relative, line, character)
        best = None
        if written:
            named = None
            for symbol in symbols:
                symbol_name = symbol.get("name")
                if not name_matches(symbol_name, written):
                    continue
                span = symbol.get("range") or symbol.get("selectionRange") or {}
                start, end = span.get("start") or {}, span.get("end") or {}
                if not start or not end:
                    continue
                if (start.get("line", -1), start.get("character", -1)) <= (line, character) \
                        <= (end.get("line", -1), end.get("character", -1)):
                    area = (end.get("line", 0) - start.get("line", 0),
                            end.get("character", 0) - start.get("character", 0))
                    if named is None or area < named[0]:
                        named = (area, symbol.get("kind"), symbol_name,
                                 symbol_name == written)
            if named is not None:
                return named[1], named[2], ("name-match" if named[3] else "name-match-qualified")

        for symbol in symbols:
            span = symbol.get("range") or symbol.get("selectionRange") or {}
            start, end = span.get("start") or {}, span.get("end") or {}
            if not start or not end:
                continue
            start_key = (start.get("line", -1), start.get("character", -1))
            end_key = (end.get("line", -1), end.get("character", -1))
            if start_key <= (line, character) <= end_key:
                area = (end_key[0] - start_key[0], end_key[1] - start_key[1])
                if best is None or area < best[0]:
                    selection = (symbol.get("selectionRange") or {}).get("start") or start
                    best = (area, symbol.get("kind"), symbol.get("name"),
                            (selection.get("line", -1), selection.get("character", -1)))
        if best is not None:
            _area, kind, name, selection_start = best
            match = "containing-header" if (line, character) <= selection_start \
                else "containing-nested"
            return kind, name, match
        return None, None, None

    def probe_position(parts, span, lines, line, column):
        """(lsp_line, lsp_character, probe_kind, callee_text) for one record.

        `l0`/`c0` are 1-based line / 0-based character in our snapshot; LSP wants
        0-based for both, so the line is shifted by one and the character is not.
        """
        text = lines[line - 1] if 0 < line <= len(lines) else ""
        callee_text = ""
        l0, c0, l1, c1 = span
        start = c0 if isinstance(c0, int) else 0
        if l0 is not None and l1 is not None and l0 == l1 and 0 < l0 <= len(lines):
            line_text = lines[l0 - 1]
            end = c1 if isinstance(c1, int) and c1 <= len(line_text) else len(line_text)
            callee_text = line_text[start:end] if start <= len(line_text) else ""
        elif l0 is not None and l1 is not None and l0 < l1 and 0 < l0 <= len(lines) \
                and 0 < l1 <= len(lines):
            # A callee expression spread over several lines, common in Rust and in
            # chained TS calls. Rebuild it so the last identifier can still be probed
            # instead of degrading every multi-line dynamic callee to a span start.
            pieces = [lines[l0 - 1][start:]]
            pieces.extend(lines[i] for i in range(l0, l1 - 1))
            last = lines[l1 - 1]
            end = c1 if isinstance(c1, int) and c1 <= len(last) else len(last)
            pieces.append(last[:max(0, end)])
            callee_text = " ".join(p.strip() for p in pieces if p.strip())
        if parts:
            method = parts[-1]
            if not method:
                return None, None, "empty-callee-name", callee_text
            pattern = callee_pattern(method)
            # 1. The LAST whole-identifier occurrence inside the recorded span.
            #    The span *is* the callee expression, so its last occurrence of the
            #    name is the call. An earlier occurrence can be a same-named local
            #    declared on the same line, as in
            #    `let retry_after = self.circuit_breaker.retry_after(...)`, where a
            #    forward search from c0 asks the server about the `let` binding.
            if l0 is not None and l1 is not None and 0 < l0 <= len(lines) \
                    and 0 < l1 <= len(lines):
                for probe_line in range(l1, l0 - 1, -1):
                    line_text = lines[probe_line - 1]
                    base = 0
                    if probe_line == l1 and isinstance(c1, int) and c1 <= len(line_text):
                        line_text = line_text[:c1]
                    if probe_line == l0:
                        if start > len(line_text):
                            continue
                        line_text = line_text[start:]
                        base = start
                    matches = list(pattern.finditer(line_text))
                    if matches:
                        return (probe_line - 1, base + matches[-1].start(),
                                "named-part-span", callee_text)
            # 2. Last whole-identifier occurrence on the call's own line.
            origin = max(0, column)
            matches = list(pattern.finditer(text[origin:]))
            if matches:
                return line - 1, origin + matches[-1].start(), "named-part-line", callee_text
            matches = list(pattern.finditer(text))
            if matches:
                return line - 1, matches[-1].start(), "named-part-line-anywhere", callee_text
            # 3. The callee may sit on a following line of a multi-line call.
            for offset in range(1, 4):
                if line - 1 + offset < len(lines):
                    matches = list(pattern.finditer(lines[line - 1 + offset]))
                    if matches:
                        return (line - 1 + offset, matches[0].start(),
                                "named-part-next-line", callee_text)
            return None, None, "method-name-not-found", callee_text
        # dynamic-callee: parts is empty, the callee is an expression in `span`.
        if l0 is not None and l1 is not None and 0 < l0 <= len(lines) and 0 < l1 <= len(lines):
            # Walk the span backwards from its end and probe the last identifier in
            # it, computing the line as well as the character rather than assuming
            # the whole expression sits on the span's first line.
            for probe_line in range(l1, l0 - 1, -1):
                line_text = lines[probe_line - 1]
                if probe_line == l1 and isinstance(c1, int) and c1 <= len(line_text):
                    line_text = line_text[:c1]
                base = 0
                if probe_line == l0:
                    if start > len(line_text):
                        continue
                    line_text = line_text[start:]
                    base = start
                identifiers = list(IDENT_RE.finditer(line_text))
                if identifiers:
                    last = identifiers[-1]
                    return probe_line - 1, base + last.start(), "span-last-ident", callee_text
        return line - 1, column, "span-start", callee_text

    def definition_at(relative: str, lsp_line: int, lsp_character: int):
        started = time.perf_counter()
        try:
            found = server.request_definition(relative, lsp_line, lsp_character)
        except Exception as error:  # noqa: BLE001
            return None, f"error:{type(error).__name__}", time.perf_counter() - started
        return found, None, time.perf_counter() - started

    started_all = time.perf_counter()
    with server.start_server():
        startup = time.perf_counter() - started_all
        # Start-up is behind us; from here every request is time-boxed instead of
        # inheriting the (much larger) initialization budget.
        server.timeout = args.request_timeout

        # --- readiness: bounded, and validated by re-requesting a definition ---
        ready_started = time.perf_counter()
        attempts = 0
        readiness = {"strategy": "poll-known-cross-file-definition",
                     "probes": [{k: v for k, v in p.items()} for p in probes],
                     "ready": False, "attempts": 0, "seconds": None,
                     "resolved": [], "timeout_seconds": args.ready_timeout,
                     "interval_seconds": args.ready_interval,
                     "min_resolved_required": args.ready_min_resolved}
        if not probes:
            readiness["strategy"] = "none-available"
            readiness["ready"] = None
        else:
            deadline = time.perf_counter() + args.ready_timeout
            while True:
                attempts += 1
                resolved_now = []
                for probe in probes:
                    relative = server_relative(probe["file"])
                    if not (workspace / PurePosixPath(relative)).is_file():
                        continue
                    found, error, _ = definition_at(relative, probe["line"] - 1, probe["character"])
                    if error is None and found:
                        location = found[0]
                        resolved_now.append({"label": probe["label"], "file": probe["file"],
                                             "line": probe["line"], "character": probe["character"],
                                             "origin": probe["origin"],
                                             "target": location.get("absolutePath")
                                             or location.get("uri")})
                if len(resolved_now) >= args.ready_min_resolved:
                    readiness.update({"ready": True, "attempts": attempts,
                                      "seconds": time.perf_counter() - ready_started,
                                      "resolved": resolved_now})
                    break
                if time.perf_counter() >= deadline:
                    readiness.update({"ready": False, "attempts": attempts,
                                      "seconds": time.perf_counter() - ready_started,
                                      "resolved": resolved_now})
                    break
                time.sleep(args.ready_interval)

        if readiness["ready"] is False:
            payload = {"stage": 2, "label": args.label, "language": args.language,
                       "workspace": str(workspace), "source_root": str(source_root),
                       "workspace_rel_prefix": prefix, "readiness": readiness,
                       "fatal": "server never answered a known definition; no measurement taken"}
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 2

        for file, (line, column, l1, c1, parts, reason) in selected:
            relative = server_relative(file)
            lines = source_lines(file)
            if not lines:
                verdicts["skipped-source-unreadable"] += 1
                by_reason[reason]["skipped-source-unreadable"] += 1
                continue
            if not (workspace / PurePosixPath(relative)).is_file():
                verdicts["file-missing-in-project"] += 1
                by_reason[reason]["file-missing-in-project"] += 1
                continue
            lsp_line, lsp_character, probe_kind, callee_text = probe_position(
                parts, (line, column, l1, c1), lines, line, column)
            probe_kind_counts[probe_kind] += 1
            if lsp_line is None:
                verdicts[probe_kind] += 1
                by_reason[reason][probe_kind] += 1
                continue

            found, error, elapsed = definition_at(relative, lsp_line, lsp_character)
            if error is not None:
                verdicts[error] += 1
                by_reason[reason][error] += 1
                continue
            latencies.append(elapsed)

            call_line_text = lines[lsp_line][:240] if lsp_line < len(lines) else ""
            target_detail: dict = {}
            if not found:
                key = "unresolved"
            else:
                location = found[0] if isinstance(found, list) else found
                uri = location.get("uri", "") if isinstance(location, dict) else ""
                scheme = (urlparse(uri).scheme or "").lower()
                range_ = ((location.get("range") or {}).get("start") or {}) \
                    if isinstance(location, dict) else {}
                if scheme and scheme != "file":
                    # Not a filesystem location at all. JDTLS answers with
                    # `jdt://contents/<container>/<package>/<Class>.class` for a JDK
                    # class and for anything inside a jar, and turning that into a
                    # path invents a file that does not exist, which then fails the
                    # workspace test and is misreported as `outside-workspace`.
                    # A server cannot point into the corpus with a non-file URI, so
                    # the scheme alone decides it.
                    key = "external-definition"
                    parsed = urlparse(uri)
                    segments = [s for s in parsed.path.split("/") if s]
                    container = "/".join(segments[:2]) or parsed.netloc or scheme
                    external_schemes[scheme] += 1
                    external_packages[f"{scheme}::{container}"] += 1
                    target_detail = {"uri": uri, "scheme": scheme, "container": container,
                                     "line0": range_.get("line"),
                                     "character": range_.get("character")}
                else:
                    target = Path(location["absolutePath"]) if isinstance(location, dict) \
                        and location.get("absolutePath") else uri_to_path(uri)
                    if target is None:
                        key = "unreadable-location"
                    else:
                        resolved_path = target.resolve()
                        as_posix = resolved_path.as_posix()
                        lowered = as_posix.lower()
                        marker = next((m for m in external_markers if m in lowered), None)
                        rel_target = location.get("relativePath") if isinstance(location, dict) else None
                        if rel_target is not None and str(rel_target).startswith(".."):
                            rel_target = None
                        if marker:
                            key = "external-definition"
                            tail = as_posix.split(marker, 1)[-1].lstrip("/")
                            external_packages[f"{marker}::{tail.split('/')[0]}"] += 1
                            target_detail = {"path": as_posix, "marker": marker}
                        else:
                            try:
                                inside = resolved_path.relative_to(workspace)
                            except ValueError:
                                key = "outside-workspace"
                                try:
                                    resolved_path.relative_to(source_root)
                                except ValueError:
                                    outside_targets["<outside-source-root>"] += 1
                                else:
                                    outside_targets[resolved_path.parent.as_posix()] += 1
                                target_detail = {"path": as_posix,
                                                 "line": range_.get("line"),
                                                 "character": range_.get("character")}
                            else:
                                target_relative = inside.as_posix()
                                kind, name, kind_match = kind_at(
                                    target_relative, range_.get("line", -1),
                                    range_.get("character", -1))
                                if kind_match == "containing-nested":
                                    key = "edge-variable-binding"
                                    binding_split[f"nested-inside-{kind}:"
                                                  f"{SYMBOL_KIND_NAMES.get(kind, '?')}"] += 1
                                else:
                                    key = grade_of(kind)
                                    if key == "edge-variable-binding":
                                        binding_split[
                                            f"{kind}:{SYMBOL_KIND_NAMES.get(kind, '?')}"] += 1
                                kind_match_counts[kind_match or "none"] += 1
                                if key == "definition-is-type-not-callable":
                                    type_kinds[f"{kind}:{SYMBOL_KIND_NAMES.get(kind, '?')}"] += 1
                                if key in EDGE_GRADES:
                                    edges[f"{target_relative}::{name}"] += 1
                                    by_grade_reason[key][reason] += 1
                                target_detail = {"server_relative": target_relative,
                                                 "path": as_posix,
                                                 "line0": range_.get("line"),
                                                 "line1": (range_.get("line") or 0) + 1,
                                                 "character": range_.get("character"),
                                                 "kind": kind,
                                                 "kind_name": SYMBOL_KIND_NAMES.get(kind),
                                                 "kind_match": kind_match,
                                                 "symbol": name}
            verdicts[key] += 1
            by_reason[reason][key] += 1
            if len(examples[key]) < 8:
                examples[key].append(
                    f"{file}:{line}:{column} {'.'.join(parts)} -> "
                    f"{target_detail.get('path') or target_detail.get('uri') or ''}")
            if args.max_edge_records == 0 or len(records) < args.max_edge_records:
                records.append({
                    "verdict": key, "reason": reason, "probe_kind": probe_kind,
                    "callee": ".".join(parts) or None, "callee_text": callee_text or None,
                    "span": [line, column, l1, c1],
                    "call_site": {"file": file, "abs": (source_root / PurePosixPath(file)).as_posix(),
                                  "l0_1based": line, "c0_0based": column,
                                  "lsp_line0": lsp_line, "lsp_character0": lsp_character,
                                  "text": call_line_text},
                    "target": target_detail,
                    "latency_ms": round(elapsed * 1000, 3),
                })

    total = sum(verdicts.values())
    latencies.sort()
    edge_total = sum(value for key, value in verdicts.items() if key in EDGE_GRADES)
    grade_totals = {grade: verdicts.get(grade, 0) for grade in EDGE_GRADES}
    confirmed_edges = grade_totals["edge-call"] + grade_totals["edge-instantiation"]

    sample_n = sum(sample_reason_counts.values())
    unweighted_share = (confirmed_edges / sample_n) if sample_n else None
    weighted = None
    if args.population_json and args.population_json.is_file():
        population = json.loads(args.population_json.read_text(encoding="utf-8"))
        pop_reasons = {k: v for k, v in (population.get("reasons") or {}).items()
                       if k != "unbound-name"}
        terms = []
        for reason, pop_count in pop_reasons.items():
            sample_count = sum(by_reason.get(reason, {}).values())
            confirmed = sum(v for k, v in by_reason.get(reason, {}).items()
                            if k in ("edge-call", "edge-instantiation"))
            rate = (confirmed / sample_count) if sample_count else 0.0
            terms.append({"reason": reason, "population": pop_count,
                          "sample": sample_count,
                          "sample_confirmed_edges": confirmed,
                          "sample_edge_rate": rate,
                          "weighted_edges": pop_count * rate,
                          "sampled": sample_count > 0})
        pop_total = sum(t["population"] for t in terms)
        weighted_edges = sum(t["weighted_edges"] for t in terms)
        weighted = {"population_total": pop_total,
                    "population_source": str(args.population_json),
                    "weighted_edges": weighted_edges,
                    "weighted_share": (weighted_edges / pop_total) if pop_total else None,
                    "unsampled_population": sum(t["population"] for t in terms if not t["sampled"]),
                    "terms": sorted(terms, key=lambda t: -t["population"])}

    result = {
        "stage": 2,
        "label": args.label,
        "engine": {"name": f"{args.language} language server via multilspy",
                   "language": args.language,
                   "multilspy_server_binary": args.server_binary,
                   "multilspy_server_install_dir": args.server_install_dir,
                   "python": sys.version.split()[0]},
        "workspace": {"project": str(workspace), "source_root": str(source_root),
                      "manifest": str(args.manifest), "manifest_root": manifest_root_meta,
                      "workspace_rel_prefix": prefix,
                      "node_modules_in_project": (workspace / "node_modules").is_dir()},
        "sample": {"files": len(sample), "positions": len(selected),
                   "measurable_unresolved_call_refs_in_workspace": sum(by_file.values()),
                   "sample_reason_counts": dict(sample_reason_counts),
                   "selection": "files with the most measurable unresolved calls, "
                               "first --per-file positions of each; NOT a random sample"},
        "lexical_baseline_in_workspace": lexical,
        "population_reason_counts": dict(reason_population),
        "readiness": readiness,
        "verdicts": dict(verdicts),
        "grades": grade_totals,
        "real_edges": edge_total,
        "confirmed_edges_call_plus_instantiation": confirmed_edges,
        "real_edge_share": (edge_total / total) if total else None,
        "confirmed_edge_share": unweighted_share,
        "extrapolation": {"unweighted": {"sample_positions": sample_n,
                                         "confirmed_edges": confirmed_edges,
                                         "share": unweighted_share},
                          "weighted_by_reason": weighted},
        "verdicts_by_unresolved_reason": {k: dict(v) for k, v in sorted(by_reason.items())},
        "edge_reasons_by_grade": {k: dict(v) for k, v in sorted(by_grade_reason.items())},
        "kind_match_counts": dict(kind_match_counts),
        "binding_kind_split": dict(binding_split),
        "variable_binding_prescribed_kinds_only": sum(
            v for k, v in binding_split.items()
            if k.split(":", 1)[0].isdigit() and int(k.split(":", 1)[0])
            in EDGE_VARIABLE_BINDING_PRESCRIBED),
        "type_not_callable_kinds": dict(type_kinds),
        "probe_kind_counts": dict(probe_kind_counts),
        "external_packages": external_packages.most_common(30),
        "external_uri_schemes": dict(external_schemes),
        "outside_workspace_target_dirs": outside_targets.most_common(25),
        "document_symbol_errors": dict(list(symbol_errors.items())[:20]),
        "server_startup_seconds": startup,
        "timeouts": {"init_seconds": args.init_timeout,
                     "request_seconds": args.request_timeout},
        "elapsed_seconds": time.perf_counter() - started_all,
        "latency_ms": {"mean": (sum(latencies) / len(latencies) * 1000) if latencies else None,
                       "p95": (latencies[int(len(latencies) * 0.95) - 1] * 1000) if latencies else None,
                       "count": len(latencies)},
        "top_edges": edges.most_common(25),
        "server_log": {"captured": len(log_messages),
                       "log_file": str(args.log_file) if args.log_file else None,
                       "excerpt": log_messages[-300:]},
        "examples": {k: v for k, v in examples.items() if v},
        "records": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: result[k] for k in
                      ("label", "workspace", "sample", "lexical_baseline_in_workspace",
                       "readiness", "verdicts", "grades", "real_edges",
                       "confirmed_edges_call_plus_instantiation", "real_edge_share",
                       "confirmed_edge_share", "extrapolation", "kind_match_counts",
                       "probe_kind_counts", "server_startup_seconds", "elapsed_seconds",
                       "latency_ms")}, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
