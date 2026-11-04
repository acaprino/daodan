"""Shared read-only view over lexical references and verified engine edges.

Consumers read this module instead of opening `engine-edges.sqlite` directly or
running an engine at query time. Lexical bindings remain authoritative when an
engine disagrees; divergent answers are surfaced in `conflicts` and candidate
answers stay outside confirmed call edges.

Standard library only.
"""
from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import resolution  # noqa: E402
import resolve_edges  # noqa: E402
import semantic_store  # noqa: E402
from snapshot_store import SnapshotStore, _unpack, logical_digest, open_snapshot  # noqa: E402

__all__ = [
    "EDGE_VIEW_SCHEMA",
    "EDGE_VIEW_VERSION",
    "classify_target_kind",
    "load_edge_view",
]

EDGE_VIEW_SCHEMA = "daodan/edge-view/v1"
EDGE_VIEW_VERSION = 1

_PROTOCOL_BASES = frozenset({"Protocol", "typing.Protocol", "typing_extensions.Protocol"})
_ABC_BASES = frozenset({"ABC", "abc.ABC", "ABCMeta", "abc.ABCMeta"})
_ABSTRACT_DECORATORS = frozenset({
    "abstractmethod", "abc.abstractmethod",
    "abstractclassmethod", "abc.abstractclassmethod",
    "abstractstaticmethod", "abc.abstractstaticmethod",
    "abstractproperty", "abc.abstractproperty",
})


def _is_protocol_base(base: str) -> bool:
    cleaned = base.split("[", 1)[0].strip()
    return cleaned in _PROTOCOL_BASES or cleaned.endswith(".Protocol")


def _is_abc_base(base: str) -> bool:
    cleaned = base.split("[", 1)[0].strip()
    if cleaned in _ABC_BASES or cleaned.endswith(".ABC"):
        return True
    if "metaclass=" in cleaned:
        _, _, meta = cleaned.partition("metaclass=")
        meta = meta.strip()
        return meta in _ABC_BASES or meta.endswith(".ABCMeta")
    return False


def _is_abstract_decorator(decorator: str) -> bool:
    cleaned = decorator.split("(", 1)[0].strip().lstrip("@")
    return cleaned in _ABSTRACT_DECORATORS or cleaned.endswith(".abstractmethod")


def _build_target_kinds(store: SnapshotStore, sem_db) -> dict[str, str]:
    """Classify each callable/class declaration as protocol, interface or concrete."""
    scopes: dict[tuple[str, str], dict] = {}
    for file_rel, scope_id, blob in sem_db.execute("SELECT file, id, payload FROM sem_scopes"):
        scopes[(file_rel, scope_id)] = _unpack(blob)

    declarations: dict[str, dict] = {}
    for decl_id, file_rel, blob in sem_db.execute(
        "SELECT id, file, payload FROM sem_declarations WHERE kind IN ('function','class')"
    ):
        payload = _unpack(blob)
        payload["file"] = file_rel
        declarations[decl_id] = payload

    file_symbols: dict[str, dict] = {}

    def symbols_for(file_rel: str) -> dict:
        if file_rel not in file_symbols:
            entry = store.get_file(file_rel, semantic=False) or {}
            file_symbols[file_rel] = entry.get("symbols") or {}
        return file_symbols[file_rel]

    def class_kind(decl_id: str) -> str:
        decl = declarations.get(decl_id)
        if not decl:
            return "concrete"
        bases = list(decl.get("bases") or ())
        sym = symbols_for(decl["file"]).get(decl.get("qualified_name") or decl.get("name")) or {}
        for sig in sym.get("signatures") or ():
            if isinstance(sig, dict):
                for base in sig.get("bases") or ():
                    if base not in bases:
                        bases.append(base)
        if any(_is_protocol_base(base) for base in bases):
            return "protocol"
        if any(_is_abc_base(base) for base in bases):
            return "interface"
        return "concrete"

    kinds: dict[str, str] = {}
    for decl_id, decl in declarations.items():
        if decl.get("kind") == "class":
            kinds[decl_id] = class_kind(decl_id)
            continue
        file_rel = decl["file"]
        scope_info = scopes.get((file_rel, decl.get("scope")))
        owner_class_id = None
        if scope_info and scope_info.get("kind") == "class" and scope_info.get("declaration"):
            owner_class_id = f"{file_rel}::{scope_info['declaration']}"
        owner_kind = class_kind(owner_class_id) if owner_class_id else "concrete"
        if owner_kind == "protocol":
            kinds[decl_id] = "protocol"
            continue
        qname = decl.get("qualified_name") or decl.get("name")
        sym = symbols_for(file_rel).get(qname) or symbols_for(file_rel).get(decl.get("name")) or {}
        decorators = [
            dec
            for sig in sym.get("signatures") or ()
            if isinstance(sig, dict)
            for dec in (sig.get("decorators") or ())
        ]
        if any(_is_abstract_decorator(dec) for dec in decorators):
            kinds[decl_id] = "interface"
        elif owner_kind == "interface" and decl.get("decorated"):
            kinds[decl_id] = "interface"
        else:
            kinds[decl_id] = "concrete"
    return kinds


def classify_target_kind(store: SnapshotStore, target_id: str | None) -> str | None:
    """Return `protocol`, `interface` or `concrete` for one declaration ID."""
    if not target_id:
        return None
    with semantic_store.semantic_reader(store) as sem_db:
        return _build_target_kinds(store, sem_db).get(target_id, "concrete")


def load_edge_view(
    store: SnapshotStore | Path | str,
    *,
    engine_store: Path | str | None = None,
    lexical_overrides: dict[str, str] | None = None,
) -> dict:
    """Merge lexical call references with verified engine edges for one snapshot."""
    with ExitStack() as stack:
        if not isinstance(store, SnapshotStore):
            store = stack.enter_context(open_snapshot(Path(store)))
        if store.format != "sqlite" or store.connection is None:
            return {
                "schema": EDGE_VIEW_SCHEMA,
                "version": EDGE_VIEW_VERSION,
                "manifest_digest": logical_digest(store),
                "parser_fingerprint": store.metadata.get("parser_fingerprint"),
                "resolver_version": semantic_store.RESOLVER_VERSION,
                "profile": {
                    "lexical_resolver": resolution.LEXICAL_RESOLVER,
                    "engine": None,
                    "engine_available": False,
                },
                "coverage": {
                    "status": "unsupported_format",
                    "sampled": False,
                    "population": 0,
                    "selected": 0,
                    "asked": 0,
                    "stride": 1,
                    "confirmed": 0,
                    "candidates": 0,
                    "no_edges_reason": "json-manifest",
                },
                "references": [],
                "candidates": [],
                "conflicts": [],
                "gaps": ["JSON snapshot holds no semantic reference table"],
            }

        sem_db = stack.enter_context(semantic_store.semantic_reader(store))
        target_kinds = _build_target_kinds(store, sem_db)
        edge_path = Path(engine_store) if engine_store is not None else resolve_edges.default_edge_store(store.path)
        gaps: list[str] = []
        engine_edges: list[dict] = []
        binding: dict | None = None

        if not edge_path.is_file():
            coverage_status = "missing_store"
        else:
            loaded_edges, binding, reason = resolve_edges.read_edge_store(edge_path, store)
            if reason is not None or loaded_edges is None:
                coverage_status = "rejected_store"
                gaps.append(reason or "engine edge store rejected")
            else:
                engine_edges = loaded_edges
                population = int(binding.get("population", 0))
                selected = int(binding.get("selected", 0))
                asked = int(binding.get("asked", 0))
                stride = int(binding.get("stride", 1))
                sampled = (selected < population) or (stride > 1)
                if sampled:
                    coverage_status = "sampled"
                    gaps.append(
                        f"engine pass sampled {selected} of {population} unresolved Python call references (stride={stride})"
                    )
                elif not engine_edges:
                    coverage_status = "completed_empty"
                else:
                    coverage_status = "complete"

        engine_by_ref: dict[str, dict] = {edge["reference_id"]: edge for edge in engine_edges}
        overrides = dict(lexical_overrides or {})
        references: list[dict] = []
        candidates: list[dict] = []
        conflicts: list[dict] = []

        rows = sem_db.execute(
            "SELECT id, file, caller, target_id, resolution, payload FROM sem_references "
            "WHERE kind='call' ORDER BY file, l0, c0, id"
        ).fetchall()

        for ref_id, file_rel, caller, target_id, res_state, blob in rows:
            payload = _unpack(blob)
            if ref_id in overrides:
                target_id = overrides[ref_id]
                res_state = "resolved" if target_id else "unresolved"
                payload = {**payload, "target_id": target_id, "resolution": res_state}
            lex_resolver = payload.get("resolver") or resolution.LEXICAL_RESOLVER
            eng = engine_by_ref.get(ref_id)

            record = {
                **payload,
                "id": ref_id,
                "file": file_rel,
                "caller": caller,
                "target_id": target_id,
                "resolution": res_state,
                "resolver": lex_resolver,
                "confidence": "confirmed" if res_state == "resolved" else None,
                "provenance": [lex_resolver] if res_state == "resolved" else [],
                "lexical_resolution": res_state,
                "lexical_target_id": target_id,
                "lexical_reason": payload.get("reason"),
                "target_kind": target_kinds.get(target_id) if target_id else None,
            }

            if eng is not None:
                eng_conf = eng.get("confidence")
                eng_target = eng.get("target_id")
                eng_resolver = eng.get("resolver")
                if res_state == "resolved":
                    if eng_conf == "confirmed" and eng_target and eng_target != target_id:
                        conflicts.append({
                            "reference_id": ref_id,
                            "file": file_rel,
                            "caller": caller,
                            "span": payload.get("span"),
                            "lexical_target_id": target_id,
                            "lexical_resolver": lex_resolver,
                            "engine_target_id": eng_target,
                            "engine_resolver": eng_resolver,
                            "reason": "divergent-lexical-and-engine-targets",
                        })
                    elif eng_conf == "confirmed" and eng_target == target_id and eng_resolver not in record["provenance"]:
                        record["provenance"].append(eng_resolver)
                else:
                    if eng_conf == "confirmed" and eng_target and eng_target in target_kinds:
                        record.update(
                            target_id=eng_target,
                            resolution="resolved",
                            resolver=eng_resolver,
                            confidence="confirmed",
                            provenance=[eng_resolver],
                            reason=eng.get("payload", {}).get("reason") or f"engine-{eng.get('verdict')}",
                            target_kind=target_kinds.get(eng_target, "concrete"),
                        )
                    elif eng_conf == "candidate":
                        candidate_entry = {
                            "reference_id": ref_id,
                            "file": file_rel,
                            "caller": caller,
                            "span": payload.get("span"),
                            "verdict": eng.get("verdict"),
                            "resolver": eng_resolver,
                            "target_id": eng_target,
                        }
                        record["engine_candidate"] = candidate_entry
                        candidates.append(candidate_entry)

            references.append(record)

        population = int(binding.get("population", 0)) if binding else 0
        selected = int(binding.get("selected", 0)) if binding else 0
        asked = int(binding.get("asked", 0)) if binding else 0
        stride = int(binding.get("stride", 1)) if binding else 1
        confirmed = int(binding.get("confirmed", 0)) if binding else 0
        cand_count = int(binding.get("candidates", 0)) if binding else 0
        no_edges_reason = binding.get("no_edges_reason") if binding else None

        return {
            "schema": EDGE_VIEW_SCHEMA,
            "version": EDGE_VIEW_VERSION,
            "manifest_digest": logical_digest(store),
            "parser_fingerprint": store.metadata.get("parser_fingerprint"),
            "resolver_version": semantic_store.RESOLVER_VERSION,
            "profile": {
                "lexical_resolver": resolution.LEXICAL_RESOLVER,
                "engine": binding.get("engine") if binding else None,
                "engine_available": coverage_status in {"complete", "sampled", "completed_empty"},
                "engine_store": edge_path.as_posix() if edge_path.is_file() else None,
                "engine_report": binding.get("engine_report", {}) if binding else {},
            },
            "coverage": {
                "status": coverage_status,
                "sampled": coverage_status == "sampled",
                "population": population,
                "selected": selected,
                "asked": asked,
                "stride": stride,
                "confirmed": confirmed,
                "candidates": cand_count,
                "no_edges_reason": no_edges_reason,
            },
            "references": references,
            "candidates": candidates,
            "conflicts": conflicts,
            "gaps": gaps,
        }
