"""Registration linter: every plugin content file on disk is declared in the marketplace.

Stdlib only, no dependencies, runs from the repository root:

    python scripts/lint_plugin_registration.py

`.claude-plugin/marketplace.json` is what makes an agent, skill or command
loadable. A file that exists under `plugins/<name>/agents/` but is absent from
that plugin's `agents` array does not exist at runtime: `subagent_type:
<plugin>:<agent>` resolves to nothing and the spawn fails with "Agent type not
found", taking its phase down with it. Nothing else in this repository checks
that array. The VS Code side has `gen_extension_manifest.py --check`; this is
the Claude Code equivalent, added after senior-review 9.0.0 shipped
`premise-auditor.md` on disk and undeclared, which silently disabled both
mechanisms that release existed to add.

Three passes, each independently reported. Exits non-zero if any fails.

  1. undeclared    a content file exists on disk but no manifest entry points at
                   it. This is the failure above: installed, invisible.
  2. dangling      a manifest entry points at a path that does not exist. This is
                   the same defect from the other side, and it is what a rename
                   that updates the file but not the manifest produces.
  3. pi globs      the Pi catalog registers nothing by name: `package.json` globs
                   the rendered tree instead. So the same invariant inverts
                   there, and the question becomes whether every generated
                   component of a registered kind falls inside a declared glob,
                   and whether every declared glob reaches anything at all. A
                   layout path moved out from under a glob would ship a package
                   whose commands do not exist, silently and on that host only.
                   Roles are deliberately not checked as a kind of their own:
                   they render as skills there.

All three content kinds are checked, because the invariant is not agent-specific:
an undeclared skill or command fails the same way for the same reason.

  agents      `./agents/<file>.md`      matched against plugins/<name>/agents/*.md
  skills      `./skills/<dir>`          matched against directories holding a SKILL.md
  commands    `./commands/<file>.md`    matched against plugins/<name>/commands/*.md

There is no grandfathering map on purpose: the invariant is mechanical, it holds
across every plugin today, and an exception would mean shipping something users
cannot load.
"""
import json
import sys
from pathlib import Path

MARKETPLACE = Path(".claude-plugin/marketplace.json")
PLUGINS = Path("plugins")
PI_MANIFEST = Path("package.json")
PI_PACKAGES = Path("exports/pi/plugins")

# Since the Claude bootstrap, `source` points at the generated package under
# `exports/claude/plugins/<name>` rather than at the authoring kernel. Both are
# scanned: the source is what a user installs, and the kernel is what an author
# edits, so a file added to one and not the other is still a registration bug.

failures: list[str] = []


def on_disk(source: Path, kind: str) -> set[str]:
    """Declared-path strings for what `plugins/<name>/<kind>/` actually holds."""
    directory = source / kind
    if not directory.is_dir():
        return set()
    if kind == "skills":
        return {f"./skills/{d.name}" for d in sorted(directory.iterdir())
                if (d / "SKILL.md").is_file()}
    return {f"./{kind}/{f.name}" for f in sorted(directory.glob("*.md"))}


def check():
    """Yield (pass_name, plugin, declared-path) for every violation."""
    data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    for plugin in data["plugins"]:
        name = plugin["name"]
        roots = [Path(plugin["source"])]
        kernel = PLUGINS / name
        # A neutral kernel is not a Claude package: its bodies live under
        # roles/ and workflows/ and the compiler decides their installed paths,
        # so only the generated package is checked for it.
        if (kernel / "plugin.toml").is_file():
            kernel = None
        if kernel is not None and kernel.is_dir() and kernel not in roots:
            roots.append(kernel)
        for kind in ("agents", "skills", "commands"):
            declared = set(plugin.get(kind, []))
            for root in roots:
                present = on_disk(root, kind)
                for path in sorted(present - declared):
                    yield "undeclared", name, path
                for path in sorted(declared):
                    target = root / path[2:]
                    exists = (target / "SKILL.md").is_file() if kind == "skills" else target.is_file()
                    if not exists:
                        yield "dangling", name, path


def report(name, problems, hint):
    if problems:
        failures.append(name)
        print(f"FAIL  {name} ({len(problems)}):")
        for plugin, path in problems:
            print(f"         {plugin}: {path}")
        print(f"         fix: {hint}")
    else:
        print(f"ok    {name}")


def check_pi() -> list[tuple[str, str, str]]:
    """Violations of the globbing catalog's half of the same invariant."""
    if not PI_MANIFEST.is_file() or not PI_PACKAGES.is_dir():
        return []
    declared = json.loads(PI_MANIFEST.read_text(encoding="utf-8")).get("pi", {})
    violations: list[tuple[str, str, str]] = []
    reached: dict[str, set[Path]] = {}
    for kind, patterns in declared.items():
        matched: set[Path] = set()
        for pattern in patterns:
            hits = {path for path in Path().glob(pattern.lstrip("./")) if path.is_dir()}
            if not hits:
                violations.append(("pi globs", "(manifest)", f"{kind}: {pattern} reaches nothing"))
            matched |= hits
        reached[kind] = matched

    for package in sorted(PI_PACKAGES.iterdir()):
        if not package.is_dir():
            continue
        for skill in sorted(package.glob("skills/*/SKILL.md")):
            if skill.parent.parent not in reached.get("skills", set()):
                violations.append(("pi globs", package.name, skill.as_posix()))
        for prompt in sorted(package.glob("prompts/*.md")):
            if prompt.parent not in reached.get("prompts", set()):
                violations.append(("pi globs", package.name, prompt.as_posix()))
    return violations


def main():
    if not MARKETPLACE.is_file() or not PLUGINS.is_dir():
        sys.exit("run from the repository root: .claude-plugin/marketplace.json not found")

    violations = sorted(set(check()) | set(check_pi()))
    data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    counted = sum(len(p.get(k, [])) for p in data["plugins"]
                  for k in ("agents", "skills", "commands"))
    print(f"{len(data['plugins'])} plugins scanned, {counted} declared content path(s)\n")

    report("undeclared", [(p, path) for kind, p, path in violations if kind == "undeclared"],
           "add the path to that plugin's agents/skills/commands array in "
           ".claude-plugin/marketplace.json, or delete the file")
    report("dangling", [(p, path) for kind, p, path in violations if kind == "dangling"],
           "the declared path does not exist: fix the entry to match the file on "
           "disk, or remove the entry")
    report("pi globs", [(p, path) for kind, p, path in violations if kind == "pi globs"],
           "widen the matching glob in the root package.json `pi` table, or move the "
           "component back under a path it already reaches")

    if failures:
        sys.exit(f"\n{len(failures)} check(s) failed: {', '.join(failures)}")
    print("\nall checks passed")


if __name__ == "__main__":
    main()
