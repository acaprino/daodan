"""Dependency-graph linter for the plugin marketplace.

Stdlib only, no dependencies, runs from the repository root:

    python scripts/lint_dependency_graph.py

Cross-plugin references inside plugin bodies are contracts. Until now they were
enforced only by prose in CLAUDE.md; this linter makes them mechanical. Eight
passes, each independently reported. Exits non-zero if any fails.

  1. declarations   every dependencies/optionalDependencies entry resolves:
                    bare names must exist in this marketplace (a bare external
                    name fails the whole plugin load at install time, the bug
                    that silently broke ai-tooling until marketplace 12.0.2);
                    qualified names must be name@marketplace with both halves
                    non-empty, and must not shadow a local plugin
  2. runtime refs   every runtime cross-plugin reference (role dispatch, skill
                    load or shared schema) is declared by its kernel, and an
                    explicit role or shared schema resolves to its provider
  3. forbidden edge nothing in codebase-xray references a senior-review
                    component at runtime. Prose next-steps suggestions are
                    fine; a spawn or skill load is the edge the old dependency
                    cycle was made of (see CLAUDE.md, marketplace 16.0.0)
  4. degrade notes  every spawn of an agent from an optionalDependencies
                    plugin carries a nearby skip note ("not installed" /
                    "skip"), so a missing optional plugin degrades a dimension
                    instead of failing the pipeline. Since pass 6 forbids
                    optional LOCAL dependencies, this pass now only ever fires
                    on cross-marketplace ones
  5. self edges     no plugin declares itself as a dependency
  6. internal deps  a dependency on a plugin inside this marketplace is always
     mandatory      hard. Bare names in optionalDependencies are rejected: they
                    buy silent degradation ("Skipped: not installed" on a whole
                    review dimension) and protect against nothing, since local
                    plugins install together. See CLAUDE.md, "Dependency
                    policy: every internal dependency is mandatory"
  7. no local       the other half of pass 6, over prose instead of
     degrade prose  declarations. A hard local dependency is always present, so
                    text making something conditional on its install, or naming
                    a stand-in for it, can only produce a silently reduced
                    result. Added after the 21.x policy pass deleted every such
                    branch by hand and still left one behind, with all six other
                    checks green
  8. deps are used  the reverse of pass 2: every hard local dependency is
                    backed by a runtime reference, or by an entry in
                    ARTIFACT_DEPENDENCIES naming the artifact that carries the
                    contract. A declaration nothing uses is a prose pointer with
                    an install cost. This is also the only check that notices a
                    dependency silently reintroduced by a concurrent writer

What counts as a runtime reference:

  - a `subagent_type:` line naming plugin:agent (an Agent spawn)
  - a neutral `role: plugin:agent` worker brief
  - a spawn/dispatch instruction naming plugin:component on the same line
  - a skill-load instruction (load/invoke/use + "skill") naming plugin:skill
  - a workflow sidecar's phase.role or role-valued phase.fanout binding
  - a workflow sidecar's dispatch.roles and explicit inline worker binding
  - a workflow sidecar's contract.shared_schemas provider/path binding

Plugin manifests are authoritative. Catalogs are generated output and may be
stale while kernels are being changed. Sidecars are parsed as TOML; their
fanout_from selections and local schemas do not create dependency edges.

Slash-command mentions (/plugin:command) are user-facing suggestions, not
runtime edges, and are deliberately not extracted. TRIGGER WHEN / DO NOT
TRIGGER WHEN lines are routing descriptions, never runtime. Tokens whose
prefix is not a known namespace (local plugin or the base name of a qualified
external dependency) are ignored in heuristic prose, but an unknown provider
in an explicit neutral role or schema binding is an error.

    python scripts/lint_dependency_graph.py --refs

prints the extracted runtime edges instead of linting, for maintenance.
"""
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

PLUGINS = Path("plugins")

# Runtime edges that must never exist, regardless of declarations.
# (source plugin, target namespace, reason)
FORBIDDEN_EDGES = [
    ("codebase-xray", "senior-review",
     "reintroduces the dependency cycle removed in marketplace 16.0.0"),
]

# Suppressions for pass 2, keyed (relative posix path, namespace). Add an
# entry only for a reference the linter misreads, with a reason.
ALLOWLIST = {
}

# Suppressions for pass 7, keyed (relative posix path, line number). Add an
# entry only for a line the linter misreads, with a reason. A line that really
# does make a dimension conditional on a hard local dependency gets fixed, never
# suppressed: that is the defect the pass exists to catch.
DEGRADE_PROSE_ALLOWLIST = {
}

# Real dependencies pass 8 cannot see, because the edge is an artifact contract
# rather than a spawn or a skill load. (owner, dependency): the artifact.
ARTIFACT_DEPENDENCIES = {
    ("abstraction-architect", "codebase-xray"):
        "reads the .codebase-xray/ run output; xray_path is required in global mode",
}

failures = []


def report(name, problems):
    if problems:
        failures.append(name)
        print(f"FAIL  {name}: {len(problems)}")
        for p in problems[:15]:
            print("        ", p)
        if len(problems) > 15:
            print(f"         ... and {len(problems) - 15} more")
    else:
        print(f"ok    {name}")


def load_plugins():
    """Read the hand-authored declarations, independently of generated catalogs."""
    plugins = {}
    for path in sorted(PLUGINS.glob("*/plugin.toml")):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        name = data.get("name")
        if name != path.parent.name:
            raise ValueError(f"{path.as_posix()}: name must match its kernel directory")
        dependencies = data.get("dependencies", {})
        components = data.get("components", {})
        plugins[name] = {
            "dependencies": dependencies.get("required", []),
            "optionalDependencies": dependencies.get("optional", []),
            "roles": set(components.get("roles", [])),
            "contract_exports": set(data.get("contracts", {}).get("exports", [])),
        }
    return plugins


def dep_base(entry):
    """codebase-xray -> codebase-xray, agent-teams@claude-code-workflows -> agent-teams."""
    return entry.split("@", 1)[0]


TOKEN = re.compile(r"(?<![\w@/.$-])([a-z0-9]+(?:-[a-z0-9]+)*):([a-z0-9]+(?:-[a-z0-9]+)*)")
SPAWN_LINE = re.compile(r"subagent_type|\bspawn|\bdispatch", re.IGNORECASE)
SKILL_LINE = re.compile(r"\bskill", re.IGNORECASE)
SKILL_VERB = re.compile(r"\b(load|invoke|use|run)\b", re.IGNORECASE)
ROUTING_LINE = re.compile(r"TRIGGER WHEN", re.IGNORECASE)
DEGRADE_NOTE = re.compile(r"not installed|\bskip|\boptional", re.IGNORECASE)
NEUTRAL_ROLE = re.compile(
    r"^\s*(?:-\s*)?role\s*:\s*[\"'`]?"
    r"([a-z0-9]+(?:-[a-z0-9]+)*):([a-z0-9]+(?:-[a-z0-9]+)*)"
    r"(?=[\"'`\s,}]|$)")
ROLE_BINDING = re.compile(
    r"^([a-z0-9]+(?:-[a-z0-9]+)*)/([a-z0-9]+(?:-[a-z0-9]+)*)$")


@dataclass(frozen=True)
class Reference:
    owner: str
    path: Path
    line_no: int
    namespace: str
    kind: str
    lines: list[str]
    target: str | None = None


def _field_lines(lines, key):
    return [i for i, line in enumerate(lines, start=1)
            if re.match(rf"^\s*{re.escape(key)}\s*=", line)]


def _role_reference(owner, path, line_no, value, lines, *, fanout=False):
    """Resolve only the role binding grammar used by neutral workflow phases."""
    if not isinstance(value, str):
        raise ValueError(f"{path.as_posix()}:{line_no}: role binding must be a string")
    if fanout:
        kind, separator, name = value.partition(":")
        if separator:
            if kind != "role":
                return None
            value = name
    if "/" not in value:
        return None  # local role, checked by the compiler
    match = ROLE_BINDING.fullmatch(value)
    if not match:
        raise ValueError(f"{path.as_posix()}:{line_no}: invalid role binding '{value}'")
    namespace, target = match.groups()
    if namespace == owner:
        return None
    return Reference(owner, path, line_no, namespace, "phase-role", lines, target)


def _sidecar_references(path):
    """Use parsed fields, never arbitrary TOML strings or artifact selections."""
    owner = path.relative_to(PLUGINS).parts[0]
    lines = path.read_text(encoding="utf-8").splitlines()
    data = tomllib.loads("\n".join(lines))
    role_lines = iter(_field_lines(lines, "role"))
    fanout_lines = iter(_field_lines(lines, "fanout"))
    refs = []
    dispatch = data.get("dispatch", {})
    line_no = next(iter(_field_lines(lines, "roles")), 1)
    for value in dispatch.get("roles", []):
        reference = _role_reference(owner, path, line_no, value, lines)
        if reference:
            refs.append(reference)
    if dispatch.get("inline_workers") is True:
        line_no = next(iter(_field_lines(lines, "inline_workers")), 1)
        reference = _role_reference(owner, path, line_no, "project-protocol/isolated-worker", lines)
        if reference:
            refs.append(reference)
    for phase in data.get("phases", []):
        if "role" in phase:
            reference = _role_reference(
                owner, path, next(role_lines, 1), phase["role"], lines)
            if reference:
                refs.append(reference)
        if "fanout" in phase:
            line_no = next(fanout_lines, 1)
            for value in phase["fanout"]:
                reference = _role_reference(owner, path, line_no, value, lines, fanout=True)
                if reference:
                    refs.append(reference)
    line_no = next(iter(_field_lines(lines, "shared_schemas")), 1)
    for value in data.get("contract", {}).get("shared_schemas", []):
        if not isinstance(value, str):
            raise ValueError(f"{path.as_posix()}:{line_no}: shared schema must be a string")
        namespace, separator, target = value.partition("/")
        candidate = Path(target)
        if (not separator or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", namespace)
                or candidate.is_absolute() or ".." in candidate.parts
                or len(candidate.parts) < 2 or candidate.parts[0] != "contracts"
                or candidate.suffix != ".toml" or "\\" in value):
            raise ValueError(f"{path.as_posix()}:{line_no}: invalid shared schema '{value}'")
        refs.append(Reference(owner, path, line_no, namespace, "shared-schema", lines, target))
    return refs


def extract_references(plugins):
    """Extract executable bindings and narrowly recognized prose instructions."""
    namespaces = set(plugins)
    for meta in plugins.values():
        for entry in meta["dependencies"] + meta["optionalDependencies"]:
            if "@" in entry:
                namespaces.add(dep_base(entry))

    refs = []
    for md in sorted(PLUGINS.glob("*/**/*.md")):
        owner = md.relative_to(PLUGINS).parts[0]
        lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines, start=1):
            if ROUTING_LINE.search(line):
                continue  # TRIGGER WHEN routing labels are prose
            neutral_role = NEUTRAL_ROLE.match(line)
            if neutral_role:
                ns, target = neutral_role.groups()
                if ns != owner:
                    refs.append(Reference(owner, md, i, ns, "neutral-role", lines, target))
                continue
            for m in TOKEN.finditer(line):
                ns = m.group(1)
                if ns not in namespaces or ns == owner:
                    continue
                if SPAWN_LINE.search(line):
                    kind = "spawn"
                elif SKILL_LINE.search(line) and SKILL_VERB.search(line):
                    kind = "skill-load"
                else:
                    continue  # prose mention, not enforced
                refs.append(Reference(owner, md, i, ns, kind, lines))
    for sidecar in sorted(PLUGINS.glob("*/workflows/*.toml")):
        refs.extend(_sidecar_references(sidecar))
    return refs


def check_declarations(plugins):
    problems = []
    for name, meta in plugins.items():
        for field in ("dependencies", "optionalDependencies"):
            for entry in meta[field]:
                if "@" in entry:
                    base, _, marketplace = entry.partition("@")
                    if not base or not marketplace:
                        problems.append(f"{name}: malformed qualified entry '{entry}'")
                    elif base in plugins:
                        problems.append(
                            f"{name}: '{entry}' qualifies a plugin that exists locally; "
                            f"local dependencies use the bare name")
                elif entry not in plugins:
                    problems.append(
                        f"{name}: bare dependency '{entry}' is not in this marketplace; "
                        f"cross-marketplace dependencies must use name@marketplace "
                        f"(a bare external name fails the whole plugin load)")
    return problems


def check_runtime_refs(plugins, refs):
    problems = []
    unregistered = set()
    for reference in refs:
        owner, path, line_no, ns, kind = (
            reference.owner, reference.path, reference.line_no,
            reference.namespace, reference.kind)
        rel = path.as_posix()
        if (rel, ns) in ALLOWLIST:
            continue
        if owner not in plugins:
            # A body without a kernel manifest has no declarations to check.
            # Keep scanning so it cannot hide later dependency violations.
            unregistered.add(owner)
            continue
        required = {dep_base(e) for e in plugins[owner]["dependencies"]}
        declared = required | {dep_base(e) for e in plugins[owner]["optionalDependencies"]}
        if ns not in declared:
            problems.append(
                f"{rel}:{line_no} {kind} of '{ns}:*' but '{ns}' is not in "
                f"{owner}'s dependencies or optionalDependencies")
        if kind == "phase-role" and ns not in required:
            problems.append(
                f"{rel}:{line_no} phase role provider '{ns}' must be a "
                f"required dependency of {owner}")
        if reference.target is not None:
            provider = plugins.get(ns)
            if provider is None and not any(
                    "@" in entry and dep_base(entry) == ns
                    for entry in plugins[owner]["dependencies"]
                    + plugins[owner]["optionalDependencies"]):
                problems.append(f"{rel}:{line_no} {kind} names unknown provider '{ns}'")
            elif provider is not None:
                if kind == "shared-schema":
                    if reference.target not in provider["contract_exports"]:
                        problems.append(
                            f"{rel}:{line_no} shared schema '{ns}/{reference.target}' "
                            "is not exported by its provider")
                elif reference.target not in provider["roles"]:
                    problems.append(
                        f"{rel}:{line_no} role '{ns}/{reference.target}' "
                        "is not declared by its provider")
            if kind == "shared-schema" and ns not in plugins[owner]["dependencies"]:
                problems.append(
                    f"{rel}:{line_no} shared schema provider '{ns}' must be a "
                    f"required dependency of {owner}")
    for owner in sorted(unregistered):
        problems.append(
            f"plugins/{owner}: has runtime references but no plugin.toml; "
            f"its dependency declarations cannot be checked")
    return problems


def check_forbidden_edges(refs):
    problems = []
    for reference in refs:
        owner, path, line_no, ns, kind = (
            reference.owner, reference.path, reference.line_no,
            reference.namespace, reference.kind)
        for src, dst, reason in FORBIDDEN_EDGES:
            if owner == src and ns == dst:
                problems.append(
                    f"{path.as_posix()}:{line_no} {kind} of '{ns}:*' from "
                    f"'{src}': {reason}")
    return problems


def check_degrade_notes(plugins, refs):
    problems = []
    for reference in refs:
        owner, path, line_no, ns, kind, lines = (
            reference.owner, reference.path, reference.line_no,
            reference.namespace, reference.kind, reference.lines)
        # Static phase bindings must be required dependencies. A skip prompt in
        # TOML would be the wrong remedy; optional external spawns live in bodies.
        if kind not in {"spawn", "neutral-role"} or owner not in plugins:
            continue
        optional = {dep_base(e) for e in plugins[owner]["optionalDependencies"]}
        if ns not in optional:
            continue
        window = lines[max(0, line_no - 13):line_no + 12]
        if not any(DEGRADE_NOTE.search(l) for l in window):
            problems.append(
                f"{path.as_posix()}:{line_no} spawns optional '{ns}:*' without a "
                f"nearby skip note; optional dependencies must degrade, never fail")
    return problems


def check_internal_deps_mandatory(plugins):
    """Standing rule since marketplace 21.3.0: a dependency on a plugin inside
    this marketplace is always hard.

    An optional local dependency protects against nothing (local plugins install
    together from the same marketplace) and buys silent degradation: a review
    prints "Skipped: not installed" for a whole dimension and hands back a report
    that reads as complete. Cross-marketplace entries are unaffected; they stay
    optional-capable because the user installs them by hand.
    """
    problems = []
    for name, meta in plugins.items():
        for entry in meta["optionalDependencies"]:
            # Membership, not just the absence of "@": a bare name that is NOT a local
            # plugin is pass 1's business (a typo, or an external name missing its
            # marketplace). Claiming it belongs in dependencies would send a maintainer
            # to break the whole plugin load.
            if "@" not in entry and entry in plugins:
                problems.append(
                    f"{name}: '{entry}' is a plugin in this marketplace and must be "
                    f"declared in dependencies, not optionalDependencies "
                    f"(see CLAUDE.md, 'Dependency policy: every internal "
                    f"dependency is mandatory')")
    return problems


INSTALL_CONDITIONAL = re.compile(
    r"not installed|\bis installed\b|\bfalls? back\b|\bfallback\b", re.IGNORECASE)

# A line asserting the plugin is always there, or that no fallback exists, states
# the policy rather than breaching it. Without this the pass fires on its own
# remedy: "There is no generic fallback variant" trips a bare /fallback/.
POLICY_AFFIRMATION = re.compile(
    r"always available|always present|is a hard dependency|are hard dependencies|"
    r"\bno (generic )?fallback\b|broken install", re.IGNORECASE)


def check_no_local_degrade_prose(plugins):
    """The inverse of pass 4, and the half of the policy pass 6 cannot reach.

    Pass 6 governs declarations. This governs the prose those declarations are
    supposed to bind. A hard local dependency is always present, so text that
    makes a dimension conditional on its install, or that names a stand-in for
    it, can only produce a silently reduced result: the review reports the
    dimension as run while a generic agent did the work, or drops it with a note
    nobody reads.

    This pass exists because prose drifts where declarations do not. The 21.x
    policy pass deleted every such branch by hand and still left one behind
    (`team-review.md`, the testing-dimension addendum), with all six other
    checks green. Two independent reviewers found it; no linter did.

    Deliberately narrow. The bare word "skip" is legitimate everywhere in this
    repo ("Skip the dimension only when its signal did not match"), so a match
    needs an install-conditional phrase AND a hard local dependency named on the
    same line.
    """
    problems = []
    for md in sorted(PLUGINS.glob("*/**/*.md")):
        owner = md.relative_to(PLUGINS).parts[0]
        if owner not in plugins:
            continue  # unregistered; pass 2 and lint_plugin_registration.py own it
        hard_local = {e for e in plugins[owner]["dependencies"]
                      if "@" not in e and e in plugins}
        if not hard_local:
            continue
        lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines, start=1):
            if (md.as_posix(), i) in DEGRADE_PROSE_ALLOWLIST:
                continue
            if not INSTALL_CONDITIONAL.search(line):
                continue
            if POLICY_AFFIRMATION.search(line):
                continue  # states the rule, does not breach it
            for ns in sorted(hard_local):
                # A dot before the name makes it a path, not a plugin reference:
                # codebase-xray publishes its artifacts to `.codebase-xray/`, so
                # every line naming that directory near the words "fall back"
                # would otherwise read as a degrade branch for the plugin.
                if re.search(rf"(?<![\w.-]){re.escape(ns)}(?![\w-])", line):
                    problems.append(
                        f"{md.as_posix()}:{i} makes something conditional on "
                        f"'{ns}' being installed (or names a fallback for it), "
                        f"but '{ns}' is a hard dependency of {owner} and is "
                        f"always present; a dimension is skipped only when its "
                        f"signal did not match")
    return problems


def check_deps_are_used(plugins, refs):
    """The reverse direction of pass 2, and the one nothing checked before.

    Pass 2 asks whether every runtime reference is declared. Nobody asked the
    opposite: whether every declaration is used. A hard local dependency that
    nothing spawns, loads or reads is not a dependency, it is a prose pointer
    with an install cost. CLAUDE.md already draws that line for runtime edges
    ("prose next-steps suggestions are fine; a spawn or Skill invocation is
    not"); this pass applies it to declarations.

    Two defects found on 2026-08-11 both live here. `senior-review` required
    `python-development`, the heaviest plugin in the set at 501 KB, to back one
    "see also" line in one agent. And a concurrent session silently restored
    `research -> codebase-mapper` after it was removed, with every other check
    green, because a declared-but-unused dependency was an error for nobody.

    ARTIFACT_DEPENDENCIES is for the real dependencies this cannot see: an edge
    expressed by reading files another plugin produces, rather than by spawning
    it. Those are legitimate and must be declared, so name them here with the
    artifact that carries the contract.
    """
    used = {(reference.owner, reference.namespace) for reference in refs}
    problems = []
    for name, meta in plugins.items():
        for dep in meta["dependencies"]:
            if "@" in dep or dep not in plugins:
                continue  # cross-marketplace; pass 1 owns those
            if (name, dep) in used or (name, dep) in ARTIFACT_DEPENDENCIES:
                continue
            problems.append(
                f"{name}: declares '{dep}' but never dispatches a role, loads a skill "
                f"or imports a shared schema from it, or declares an artifact contract. A prose "
                f"pointer is not a dependency: drop the declaration, or add it "
                f"to ARTIFACT_DEPENDENCIES with the artifact that carries the "
                f"contract")
    return problems


def check_self_edges(plugins):
    problems = []
    for name, meta in plugins.items():
        for field in ("dependencies", "optionalDependencies"):
            for entry in meta[field]:
                if dep_base(entry) == name:
                    problems.append(f"{name}: declares itself in {field}")
    return problems


def main():
    if not PLUGINS.is_dir():
        sys.exit("run from the repository root: plugins directory not found")

    try:
        plugins = load_plugins()
        refs = extract_references(plugins)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        sys.exit(f"cannot read kernel dependency bindings: {error}")

    if "--refs" in sys.argv[1:]:
        for reference in refs:
            print(f"{reference.owner} -> {reference.namespace}  ({reference.kind})  "
                  f"{reference.path.as_posix()}:{reference.line_no}")
        return

    spawns = sum(1 for reference in refs
                 if reference.kind in {"spawn", "neutral-role", "phase-role"})
    schemas = sum(1 for reference in refs if reference.kind == "shared-schema")
    print(f"{len(plugins)} plugins, {len(refs)} runtime cross-plugin references "
          f"({spawns} role dispatches, {schemas} shared schemas, "
          f"{len(refs) - spawns - schemas} skill loads)\n")

    report("declarations", check_declarations(plugins))
    report("runtime refs", check_runtime_refs(plugins, refs))
    report("forbidden edge", check_forbidden_edges(refs))
    report("degrade notes", check_degrade_notes(plugins, refs))
    report("self edges", check_self_edges(plugins))
    report("internal deps mandatory", check_internal_deps_mandatory(plugins))
    report("no local degrade prose", check_no_local_degrade_prose(plugins))
    report("deps are used", check_deps_are_used(plugins, refs))

    if failures:
        sys.exit(f"\n{len(failures)} check(s) failed: {', '.join(failures)}")
    print("\nall checks passed")


if __name__ == "__main__":
    main()
