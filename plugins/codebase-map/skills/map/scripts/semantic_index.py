"""Source-bound static bindings, deliberately narrower than compiler semantics.

Only unique lexical functions/classes and direct internal import bindings become
targets. Unknown scopes, receivers, rebindings and unsupported exports remain
explicit references with no target. No project source is imported or executed.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path

from tree_scope import Perimeter
import resolution

# One vocabulary with semantic_store: both owners of the source graph answer with
# the same target kinds and the same reasons, because resolution.py holds the policy.
_TARGET_KINDS = resolution.TARGET_KINDS

__all__ = ["build_semantic_index"]


def _manifest_signature(manifest: dict) -> str:
    """Bind operation-local caches to their source and semantic metadata."""
    identity = {key: manifest.get(key) for key in ("root", "target", "parser_fingerprint", "files")}
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _allowed(path: Path, rel: str, root: Path, target: Path, perimeter: Perimeter) -> bool:
    from snapshot import is_forbidden

    return (target.is_relative_to(root) and path.is_relative_to(target if target.is_dir() else target.parent)
            and (target.is_dir() or path == target) and perimeter.covers(path)
            and not is_forbidden(Path(rel).name))


def _index_reusable(index: dict | None, manifest: dict, observations: dict | None) -> bool:
    """Reuse only a complete observed-source operation in its current perimeter."""
    from snapshot import parser_fingerprint

    if (index is None or observations is None
            or index.get("parser_fingerprint") != parser_fingerprint()
            or index.get("_manifest_signature") != _manifest_signature(manifest)):
        return False
    root = Path(manifest.get("root") or ".").resolve()
    target = (root / (manifest.get("target") or ".")).resolve()
    perimeter = Perimeter(target)
    coverage = index.get("coverage", {})
    for rel in manifest.get("files", {}):
        allowed = _allowed((root / rel).resolve(), rel, root, target, perimeter)
        if allowed != (coverage.get(rel, {}).get("status") != "excluded"):
            return False
    for rel in index.get("_source_text", {}):
        data = observations.get(rel)
        if (not isinstance(data, bytes)
                or hashlib.sha256(data).hexdigest() != coverage.get(rel, {}).get("raw_hash")):
            return False
    return True


def _span_valid(span, lines: list[bytes]) -> bool:
    if not isinstance(span, list) or len(span) != 4 or any(type(n) is not int for n in span):
        return False
    start_line, start_column, end_line, end_column = span
    if not (1 <= start_line <= end_line <= len(lines)
            and 0 <= start_column <= len(lines[start_line - 1])
            and 0 <= end_column <= len(lines[end_line - 1])
            and (start_line < end_line or start_column <= end_column)):
        return False
    try:
        lines[start_line - 1][:start_column].decode("utf-8")
        lines[end_line - 1][:end_column].decode("utf-8")
    except UnicodeError:
        return False
    return True


def _validate(payload, data: bytes) -> str | None:
    """Reject malformed identity/scope/span data before any exact locations escape."""
    if (not isinstance(payload, dict) or type(payload.get("version")) is not int or payload["version"] != 1
            or payload.get("status") != "ast" or not isinstance(payload.get("backend"), str)):
        return "unsupported-semantic-payload"
    names = ("scopes", "declarations", "imports", "exports", "references")
    if any(not isinstance(payload.get(name), list) for name in names):
        return "invalid-semantic-collections"
    if not isinstance(payload.get("notes", []), list) or any(not isinstance(note, str) for note in payload.get("notes", [])):
        return "invalid-semantic-notes"
    lines = data.split(b"\n")
    scopes = {}
    for scope in payload["scopes"]:
        if (not isinstance(scope, dict) or not isinstance(scope.get("id"), str)
                or not isinstance(scope.get("kind"), str) or scope["id"] in scopes
                or (scope.get("parent") is not None and not isinstance(scope["parent"], str))
                or ("unresolved" in scope and type(scope["unresolved"]) is not bool)):
            return "invalid-scope"
        scopes[scope["id"]] = scope
    if not scopes or sum(scope.get("parent") is None for scope in scopes.values()) != 1:
        return "invalid-scope-root"
    for scope in scopes.values():
        seen = set()
        current = scope["id"]
        while current is not None:
            if current not in scopes or current in seen:
                return "invalid-scope-parent"
            seen.add(current)
            current = scopes[current].get("parent")
    ids = set()
    for declaration in payload["declarations"]:
        if (not isinstance(declaration, dict)
                or any(not isinstance(declaration.get(key), str) for key in ("id", "name", "kind", "scope"))
                or declaration["id"] in ids or declaration["scope"] not in scopes
                or ("lexical" in declaration and type(declaration["lexical"]) is not bool)
                or not _span_valid(declaration.get("span"), lines)):
            return "invalid-declaration"
        ids.add(declaration["id"])
    for binding in payload["imports"]:
        if (not isinstance(binding, dict)
                or any(not isinstance(binding.get(key), str) for key in ("scope", "local", "module", "imported", "mode"))
                or any(key in binding and type(binding[key]) is not bool for key in ("type_only", "unresolved"))
                or binding["scope"] not in scopes or not _span_valid(binding.get("span"), lines)):
            return "invalid-import-binding"
    for export in payload["exports"]:
        if (not isinstance(export, dict) or not isinstance(export.get("exported"), str)
                or (not isinstance(export.get("local"), str) and not isinstance(export.get("module"), str))):
            return "invalid-export"
    for reference in payload["references"]:
        if (not isinstance(reference, dict) or not isinstance(reference.get("scope"), str)
                or reference["scope"] not in scopes
                or not isinstance(reference.get("parts"), list)
                or any(not isinstance(part, str) for part in reference["parts"])
                or not isinstance(reference.get("kind"), str)
                or not _span_valid(reference.get("span"), lines)
                or (reference.get("caller") is not None
                    and (not isinstance(reference["caller"], str) or reference["caller"] not in ids))):
            return "invalid-reference"
    return None


def _source_entries(manifest: dict, observations: dict | None):
    from snapshot import MAX_FILE_BYTES, parser_fingerprint

    root = Path(manifest.get("root") or ".").resolve()
    target = (root / (manifest.get("target") or ".")).resolve()
    fingerprint = parser_fingerprint()
    fingerprint_matches = manifest.get("parser_fingerprint") == fingerprint
    perimeter = Perimeter(target)
    source_text, data_by_file, coverage, payloads = {}, {}, {}, {}
    for rel, entry in sorted(manifest.get("files", {}).items()):
        path = (root / rel).resolve()
        allowed = _allowed(path, rel, root, target, perimeter)
        record = {"status": "excluded", "reason": "outside-current-perimeter", "verified_source": False,
                  "reference_count": 0, "resolved_count": 0}
        coverage[rel] = record
        if not allowed:
            continue
        try:
            if observations is not None and rel in observations:
                data = observations[rel]
                if not isinstance(data, bytes):
                    record.update(status="unavailable", reason="invalid-source-observation")
                    continue
            else:
                if path.stat().st_size > MAX_FILE_BYTES:
                    record.update(status="oversized", reason="source-size-limit")
                    continue
                data = path.read_bytes()
            if len(data) > MAX_FILE_BYTES:
                record.update(status="oversized", reason="source-size-limit")
                continue
            text = data.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            record.update(status="unavailable", reason=type(exc).__name__)
            continue
        source_text[rel], data_by_file[rel] = text, data
        actual_hash = hashlib.sha256(data).hexdigest()
        record["raw_hash"] = actual_hash
        if not isinstance(entry, dict) or not isinstance(entry.get("raw_hash"), str):
            record.update(status="unbound-source", reason="manifest-source-hash-missing")
        elif entry["raw_hash"] != actual_hash:
            record.update(status="stale", reason="source-hash-mismatch")
        elif not fingerprint_matches:
            record.update(status="fingerprint-mismatch", reason="helper-fingerprint-mismatch")
        else:
            record["verified_source"] = True
            payload = entry.get("semantic")
            if payload is None:
                record.update(status="lexical", reason="semantic-backend-unavailable")
            else:
                problem = _validate(payload, data)
                if problem:
                    record.update(status="malformed", reason=problem)
                elif entry.get("status") != "parsed":
                    record.update(status="lexical", reason="source-not-successfully-parsed")
                else:
                    record.update(status="ast", reason=None, backend=payload["backend"],
                                  reference_count=len(payload["references"]), notes=list(payload.get("notes", [])))
                    payloads[rel] = payload
    return root, target, fingerprint, source_text, data_by_file, coverage, payloads


def build_semantic_index(manifest: dict, *, import_graph: dict | None = None,
                         source_observations: dict | None = None) -> dict:
    """Build a conservative index over every permitted semantic manifest entry.

    Observations are bytes captured by the calling snapshot operation, keyed by
    manifest-relative path. Without them, each permitted source is read once and
    retained for snippets and bounded lexical fallback. Private underscore fields
    are operation-local caches and must be omitted from persisted/public views.
    """
    from snapshot import resolved_imports

    root, target, fingerprint, source_text, data_by_file, coverage, payloads = _source_entries(manifest, source_observations)
    graph = resolved_imports(manifest) if import_graph is None else import_graph
    declarations, bindings, scopes, module_scopes, exports = {}, {}, {}, {}, {}
    for rel, payload in payloads.items():
        scopes[rel] = {scope["id"]: scope for scope in payload["scopes"]}
        module_scopes[rel] = next(scope["id"] for scope in payload["scopes"] if scope.get("parent") is None)
        table = defaultdict(list)
        for item in payload["declarations"]:
            identity = f"{rel}::{item['id']}"
            declarations[identity] = {**item, "id": identity, "source_id": item["id"], "file": rel}
            if item.get("lexical", True):
                table[(item["scope"], item["name"])].append(("declaration", identity))
        for item in payload["imports"]:
            table[(item["scope"], item["local"])].append(("import", item))
        bindings[rel] = table
        exported_names = defaultdict(list)
        for item in payload["exports"]:
            exported_names[item["exported"]].append(item)
        exports[rel] = exported_names

    def lexical(rel, scope_id, name):
        while scope_id is not None:
            scope = scopes[rel][scope_id]
            if scope.get("unresolved"):
                return None, "scope-unresolved"
            matches = bindings[rel].get((scope_id, name), [])
            if matches:
                return (matches[0], None) if len(matches) == 1 else (None, "ambiguous-binding")
            scope_id = scope.get("parent")
        return None, "unbound-name"

    def uncertain_imports(rel, scope_id, parts):
        """Keep import provenance when a rebind prevents a unique target.

        These are candidates, not a selected binding. Stop at the first binding
        scope so an outer import cannot bypass a known parameter/local shadow.
        """
        while scope_id is not None:
            scope = scopes[rel][scope_id]
            matches = bindings[rel].get((scope_id, parts[0]), [])
            if matches:
                return [{"files": list(graph.get(rel, {}).get(value["module"], [])),
                         "imported": parts[1] if value["mode"] == "namespace" and len(parts) == 2 else value["imported"]}
                        for kind, value in matches if kind == "import"]
            if scope.get("unresolved"):
                break
            scope_id = scope.get("parent")
        return []

    def exported_target(rel, exported, *, runtime=True):
        if rel not in payloads:
            return None, "import-target-" + coverage.get(rel, {}).get("status", "unavailable")
        if manifest["files"][rel].get("language") == "python":
            local = exported
        else:
            matches = exports[rel].get(exported, [])
            if len(matches) != 1:
                return None, "export-missing-or-ambiguous"
            export = matches[0]
            if export.get("type_only") and runtime:
                return None, "type-only-export"
            if export.get("module"):
                return None, "reexport-unsupported"
            local = export.get("local")
        binding, reason = lexical(rel, module_scopes[rel], local)
        if reason:
            return None, reason
        kind, value = binding
        if kind != "declaration":
            return None, "reexport-unsupported"
        if declarations[value]["kind"] not in _TARGET_KINDS:
            return None, "unsupported-target-kind"
        return value, None

    class Lookup:
        """The shared policy's view of this in-memory index.

        `semantic_store._Resolver` answers the same lookups over the snapshot's
        SQLite tables; resolution.py holds the rules so the two cannot drift.
        """

        def declaration(self, identity):
            return declarations.get(identity)

        def scope_record(self, rel, scope_id):
            return scopes.get(rel, {}).get(scope_id)

        def bindings_named(self, rel, scope_id, name):
            return list(bindings.get(rel, {}).get((scope_id, name), ()))

        def targets(self, rel, module):
            return list(graph.get(rel, {}).get(module, []))

        def language(self, rel):
            return manifest["files"].get(rel, {}).get("language")

        def lexical(self, rel, scope_id, name):
            return lexical(rel, scope_id, name)

        def exported_target(self, rel, exported):
            return exported_target(rel, exported)

    lookup = Lookup()
    references = []
    for rel, payload in sorted(payloads.items()):
        resolved_count = 0
        for number, item in enumerate(payload["references"]):
            record = {**item, "id": f"{rel}::reference#{number}", "file": rel,
                      "caller": f"{rel}::{item['caller']}" if item.get("caller") else None,
                      "target_id": None, "resolution": "unresolved", "reason": item.get("reason"),
                      "resolver": resolution.LEXICAL_RESOLVER,
                      "known_unrelated": False, "candidate_files": [], "imported_name": None,
                      "candidate_bindings": []}
            references.append(record)
            if item.get("reason") or not item["parts"]:
                record["reason"] = item.get("reason") or "dynamic-reference"
                continue
            parts = item["parts"]
            binding, reason = lexical(rel, item["scope"], parts[0])
            if reason:
                record["reason"] = reason
                record["candidate_bindings"] = uncertain_imports(rel, item["scope"], parts)
                continue
            binding_kind, value = binding
            if binding_kind == "declaration":
                if len(parts) != 1:
                    found = (resolution.instance_method(lookup, rel, item, parts)
                             if len(parts) == 2 else None)
                    if found is None:
                        record["reason"] = "unknown-receiver"
                    else:
                        record.update(target_id=found[0], resolution="resolved", reason=found[1])
                        resolved_count += 1
                elif declarations[value]["kind"] in _TARGET_KINDS:
                    record.update(target_id=value, resolution="resolved", reason="unique-lexical-binding")
                    resolved_count += 1
                else:
                    record.update(reason="non-callable-binding", known_unrelated=True, binding_id=value)
                continue
            imported = value
            targets = graph.get(rel, {}).get(imported["module"], [])
            record["candidate_files"] = list(targets)
            record["imported_name"] = imported["imported"]
            if imported.get("unresolved"):
                record["reason"] = imported.get("reason") or "import-binding-unresolved"
            elif imported.get("type_only"):
                record["reason"] = "type-only-import"
            elif imported["mode"] == "named" and len(parts) == 2 and lookup.language(rel) == "python":
                # Before the single-target rule: a Python relative import keys the
                # module as written, so one file's several `from . import x`
                # statements share the key and only the imported name picks the file.
                identity, reason = resolution.module_attribute(lookup, rel, imported, parts[1])
                record["imported_name"] = parts[1]
                record.update(target_id=identity, reason=reason)
            elif len(targets) != 1:
                record["reason"] = "import-target-missing-or-ambiguous"
            elif imported["mode"] == "namespace" and len(parts) == 2:
                record["imported_name"] = parts[1]
                identity, reason = exported_target(targets[0], parts[1])
                record.update(target_id=identity, reason=reason or "direct-internal-import")
            elif imported["mode"] in {"named", "default"} and len(parts) == 1 and imported["imported"] != "*":
                name = "default" if imported["mode"] == "default" else imported["imported"]
                identity, reason = exported_target(targets[0], name)
                record.update(target_id=identity, reason=reason or "direct-internal-import")
            else:
                record["reason"] = "unknown-receiver-or-import-form"
            if record["target_id"] is not None:
                record["resolution"] = "resolved"
                resolved_count += 1
        coverage[rel]["resolved_count"] = resolved_count

    return {"version": 1, "root": root.as_posix(), "target": manifest.get("target") or ".",
            "parser_fingerprint": fingerprint, "declarations": declarations,
            "references": references, "coverage": coverage,
            "notes": ["Static bindings only; no type inference or runtime execution coverage."]
                     + [f"{rel}: {item['status']} ({item.get('reason')})" for rel, item in coverage.items() if item["status"] != "ast"],
            "_source_text": source_text, "_source_observations": data_by_file, "_import_graph": graph,
            "_manifest_signature": _manifest_signature(manifest)}
