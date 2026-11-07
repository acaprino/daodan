"""The resolution policy both owners of the source graph share.

`semantic_store._Resolver` answers over the snapshot's SQLite tables and
`semantic_index.build_semantic_index` answers over the same facts in memory. They
must not disagree: a usage claim from one and an edit-impact packet from the other
that contradict each other are the defect this module exists to prevent. Each owner
supplies the lookups of `ResolutionLookup` over its own storage; the rules live here
once, and a rule added to one owner only would be a contradiction the day it landed.

Every rule is lexical and conservative, and none infers a type. A receiver is an
instance only when it is the first parameter of the function the reference sits in
and that function is declared in a class body. A base is followed only when its name
resolves to a project class. An instance attribute is never resolved, because it is a
binding and not a symbol, so it has no arrival node.

What these rules recover was measured rather than assumed:
evals/codebase-map/python-parser/RESULTS.md section 6 records 146 positions an engine
resolved and the symbol table did not, 125 of them a method inherited from a project
base class and 21 a callable reached as an attribute of a module, with 40 of 40
sampled records reading true at both ends and zero of them caused by the parser.
"""
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Protocol

__all__ = ["LEXICAL_RESOLVER", "MRO_LIMIT", "TARGET_KINDS", "ResolutionLookup",
           "class_named", "instance_method", "module_attribute"]


# The resolver identity stamped on every reference the lexical rules answer, so an
# edge always names what produced it and an engine's edge is never counted together
# with one of these. The rules' own revision is `semantic_store.RESOLVER_VERSION`,
# recorded in the snapshot's semantic meta and in its parser fingerprint.
LEXICAL_RESOLVER = "builtin-lexical"


# Kinds a reference can arrive at. A binding, a parameter or a module is not a
# target: it has no symbol, so it has no body hash and no contract to go stale.
TARGET_KINDS = frozenset({"function", "class"})

# Cap on distinct project classes considered by C3. Cycles and hierarchies beyond
# this bound stay unresolved instead of yielding a partial method lookup.
MRO_LIMIT = 8


class ResolutionLookup(Protocol):
    """The seven facts a resolution rule may ask storage for.

    Identities are file-qualified (`"<rel>::<source id>"`); scope ids and source
    ids are file-local and always paired with their `rel`.
    """

    def declaration(self, identity: str) -> dict | None:
        """One declaration's payload, or None when this graph does not hold it."""

    def scope_record(self, rel: str, scope_id: str) -> dict | None:
        """One scope's payload: `kind`, `parent`, and a class body's `declaration`."""

    def bindings_named(self, rel: str, scope_id: str, name: str) -> list[tuple]:
        """All bindings a class body holds under `name`, including non-callables."""

    def targets(self, rel: str, module: str) -> list[str]:
        """The files an import's module specifier resolves to, empty when it resolves to none."""

    def language(self, rel: str) -> str | None:
        """The file's language, because a rule may be one language's semantics only."""

    def lexical(self, rel: str, scope_id: str, name: str):
        """`(binding, None)` on a unique binding, `(None, reason)` otherwise."""

    def exported_target(self, rel: str, exported: str):
        """`(identity, None)` for a file's exported name, `(None, reason)` otherwise."""


def class_named(lookup: ResolutionLookup, rel: str, scope_id: str, dotted: str) -> str | None:
    """Resolve a base name to a project class, in this file or an imported one.

    A dotted base (`mixins.LoggingMixin`) is followed only through a namespace
    import that resolves to exactly one file. A subscript, a call or any other
    expression is not a name and is left alone by the caller.
    """
    head, *rest = dotted.split(".")
    binding, reason = lookup.lexical(rel, scope_id, head)
    if reason or binding is None:
        return None
    kind, value = binding
    if kind == "declaration":
        if rest:
            return None
        payload = lookup.declaration(value)
        return value if payload is not None and payload.get("kind") == "class" else None
    imported = value
    if imported.get("unresolved") or imported.get("type_only"):
        return None
    if imported.get("mode") == "named" and len(rest) == 1:
        identity, reason = module_attribute(lookup, rel, imported, rest[0])
        payload = lookup.declaration(identity) if identity else None
        return identity if payload is not None and payload.get("kind") == "class" else None
    targets = lookup.targets(rel, imported["module"])
    if len(targets) != 1:
        return None
    if imported.get("mode") == "namespace":
        if len(rest) != 1:
            return None
        name = rest[0]
    else:
        if rest:
            return None
        name = imported.get("imported")
    if not name:
        return None
    identity, reason = lookup.exported_target(targets[0], name)
    if reason or identity is None:
        return None
    payload = lookup.declaration(identity)
    return identity if payload is not None and payload.get("kind") == "class" else None


def _project_mro(lookup: ResolutionLookup, origin: str) -> list[str] | None:
    """Python C3, only for a complete, unambiguous project hierarchy.

    An unknown base can supply an earlier member, and a decorated class or a
    custom metaclass can replace the namespace or its lookup. None is skipped.
    The implicit builtin object is the only non-project terminal accepted.
    """
    terminal = "<builtin-object>"
    memo = {terminal: [terminal]}
    active = set()
    visited = set()

    def linearize(identity):
        if identity in memo:
            return memo[identity]
        if identity in active or len(visited) >= MRO_LIMIT:
            return None
        visited.add(identity)
        payload = lookup.declaration(identity)
        if payload is None or payload.get("dynamic_class") or not payload.get("bases_complete"):
            return None
        owner = identity.split("::", 1)[0]
        # A recorded mutation or rebind of the class name prevents trusting the
        # declaration as the class object a receiver belongs to.
        binding, reason = lookup.lexical(owner, payload["scope"], payload["name"])
        if reason or binding != ("declaration", identity):
            return None
        body = lookup.scope_record(owner, payload.get("body"))
        if body is None or body.get("reason") != "class body namespace order is unresolved":
            return None
        active.add(identity)
        bases = []
        for name in payload.get("bases") or ():
            base = class_named(lookup, owner, payload["scope"], name)
            if base is None and name == "object":
                binding, reason = lookup.lexical(owner, payload["scope"], name)
                if binding is None and reason == "unbound-name":
                    base = terminal
            if base is None or base in bases:
                active.remove(identity)
                return None
            bases.append(base)
        if not bases:
            bases = [terminal]
        sequences = []
        for base in bases:
            inherited = linearize(base)
            if inherited is None:
                active.remove(identity)
                return None
            sequences.append(list(inherited))
        sequences.append(list(bases))
        result = [identity]
        while any(sequences):
            sequences = [sequence for sequence in sequences if sequence]
            candidate = next((sequence[0] for sequence in sequences
                              if not any(sequence[0] in other[1:] for other in sequences)), None)
            if candidate is None:
                active.remove(identity)
                return None
            result.append(candidate)
            for sequence in sequences:
                if sequence[0] == candidate:
                    sequence.pop(0)
        active.remove(identity)
        memo[identity] = result
        return result

    result = linearize(origin)
    return [identity for identity in result if identity != terminal] if result else None


def instance_method(lookup: ResolutionLookup, rel: str, item: dict,
                    parts: list[str]) -> tuple[str, str] | None:
    """Resolve a plain method's receiver using C3 and all member binding sites.

    The parser certifies the receiver only for an undecorated method's first
    positional parameter. Shadowing assignments, ambiguous members, decorators
    and instance writes stop resolution instead of falling through to a base.
    """
    caller = item.get("caller")
    if not caller:
        return None
    declaring = lookup.declaration(f"{rel}::{caller}")
    if declaring is None or declaring.get("receiver") != parts[0]:
        return None
    scope = lookup.scope_record(rel, declaring.get("scope"))
    if scope is None or scope.get("kind") != "class" or not scope.get("declaration"):
        return None
    origin = f"{rel}::{scope['declaration']}"
    mro = _project_mro(lookup, origin)
    if mro is None:
        return None
    for identity in mro:
        payload = lookup.declaration(identity)
        owner = identity.split("::", 1)[0]
        if (payload.get("instance_writes_unknown")
                or parts[1] in (payload.get("instance_writes") or ())
                or lookup.bindings_named(owner, payload["body"], "__getattribute__")):
            return None
    for identity in mro:
        payload = lookup.declaration(identity)
        owner = identity.split("::", 1)[0]
        body = payload.get("body")
        if body:
            found = lookup.bindings_named(owner, body, parts[1])
            if not found:
                continue
            if len(found) != 1 or found[0][0] != "declaration":
                return None
            target = lookup.declaration(found[0][1])
            if target is None or target.get("kind") not in TARGET_KINDS or target.get("decorated"):
                return None
            reason = "instance-method" if identity == origin else "inherited-project-method"
            return found[0][1], reason
    return None


def module_attribute(lookup: ResolutionLookup, rel: str, imported: dict,
                     name: str) -> tuple[str | None, str]:
    """Resolve `module.attribute` where the local name binds a module object.

    Python's `from . import worker` binds the module itself, so `worker.Pacer` is
    that module's attribute and `Pacer` a project symbol. The import map keys the
    module as written (`.`), a key several submodule imports of one file share, so
    the file is picked by the imported name: the one whose stem is that name, or
    that name's package `__init__.py`. Anything else stays unresolved rather than
    guessed, and says which.
    """
    local_module = imported.get("imported")
    if imported.get("mode") != "named" or local_module in (None, "*"):
        return None, "unknown-receiver-or-import-form"
    matches = []
    for target in lookup.targets(rel, imported["module"]):
        path = PurePosixPath(target)
        module_path = path.parent if path.name == "__init__.py" else path.with_suffix("")
        if module_path.name != local_module:
            continue
        namespace = module_path.parent
        written = imported["module"]
        if written.startswith("."):
            level = len(written) - len(written.lstrip("."))
            expected = PurePosixPath(rel).parent
            if level - 1 > len(expected.parts):
                continue
            for _ in range(level - 1):
                expected = expected.parent
            remainder = written[level:]
            if remainder:
                expected = expected.joinpath(*remainder.split("."))
            if namespace != expected:
                continue
        elif namespace.parts[-len(written.split(".")):] != tuple(written.split(".")):
            continue
        matches.append(target)
    if not matches:
        return None, "import-target-missing-or-ambiguous"
    if len(matches) > 1:
        return None, "module-attribute-target-ambiguous"
    path = PurePosixPath(matches[0])
    package = (path.parent.parent if path.name == "__init__.py" else path.parent) / "__init__.py"
    package_rel = package.as_posix()
    package_scope = lookup.scope_record(package_rel, "module")
    if package_scope is not None:
        binding, reason = lookup.lexical(package_rel, "module", local_module)
        dynamic, dynamic_reason = lookup.lexical(package_rel, "module", "__getattr__")
        if binding is not None or reason != "unbound-name" or dynamic is not None or dynamic_reason != "unbound-name":
            return None, "module-attribute-package-binding-ambiguous"
    elif lookup.language(package_rel) is not None:
        return None, "module-attribute-package-unavailable"
    identity, reason = lookup.exported_target(matches[0], name)
    return identity, reason or "module-attribute"
