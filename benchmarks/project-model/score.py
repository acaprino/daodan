"""Score a tool's project pre-map against a fixture's hand-written expected.json.

score(expected, got) -> {facet: result}. A facet absent from `got` is not given by the tool:
{"given": False, "expected": n}. A given facet:
{"given": True, "expected", "found", "found_normalised", "missed", "extra", "wrong"},
with expected == found + len(wrong) + len(missed). The rules are in SCHEMA.md.

CLI:
  python score.py <tools> <fixtures> [--json OUT]   tables per tool and facet
  python score.py --check [<fixtures>]              validate expected.json files
<tools>: all or a comma list of results/<tool>.json names.
<fixtures>: all, a family (js, py, jvm, sys, mix) or a comma list of fixture names.
Standard library only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
RESULTS = HERE / "results"
FAMILIES = ("js", "py", "jvm", "sys", "mix", "real")

FACETS = (
    "languages", "languages.files", "excluded",
    "units", "units.depends_on", "units.source_roots", "units.config",
    "workspace", "workspace.members", "toolchains", "dependencies",
    "frameworks", "services", "needs",
)
FACT_KEYS = ("languages", "excluded", "units", "workspace", "toolchains", "dependencies",
             "frameworks", "services", "needs")
TOP_KEYS = FACT_KEYS + ("traps", "unknown", "connections")
PER_UNIT = ("dependencies", "frameworks")  # facets whose items name a unit: "unknown" may keep some units
WHY = ("vendored", "generated", "documentation", "binary", "submodule")
SCOPES = ("runtime", "dev", "build", "test", "optional", "peer", "provided")
VERSION_FIELDS = ("version", "declared", "resolved")
KINDS = ("npm-package", "deno-project", "angular-project", "nx-project", "python-project", "cargo-crate",
         "go-module", "maven-module", "gradle-project", "sbt-project", "dotnet-project", "cmake-target",
         "make-target", "meson-target", "bazel-target", "composer-package", "gem", "pub-package", "swift-package",
         "mix-project", "cabal-package", "stack-project", "dune-project", "zig-package", "julia-package",
         "terraform-module", "helm-chart", "bundler-project", "buf-module", "bazel-module", "source-tree", "xcode-target", "msbuild-project", "kobalt-project")
CHECKERS = ("pyright", "mypy", "ruff", "pylint", "flake8", "black", "basedpyright")
CONFIG_KEYS = ("tsconfig", "paths", "entry_files", "packages", "build_tags", "include_dirs", "source_sets",
               "compile_tasks", "nested_modules")

# Ecosystem of a dependency, from the base name of the file that declares it.
FILE_ECOSYSTEM = {
    "pyproject.toml": "pypi", "setup.py": "pypi", "setup.cfg": "pypi", "pipfile": "pypi",
    "pipfile.lock": "pypi", "poetry.lock": "pypi", "uv.lock": "pypi", "pdm.lock": "pypi",
    "pylock.toml": "pypi", "environment.yml": "pypi",
    "package.json": "npm", "package-lock.json": "npm", "npm-shrinkwrap.json": "npm",
    "pnpm-lock.yaml": "npm", "pnpm-workspace.yaml": "npm", "yarn.lock": "npm", "bun.lock": "npm", "deno.json": "npm",
    "cargo.toml": "cargo", "cargo.lock": "cargo",
    "pom.xml": "maven", "build.gradle": "maven", "build.gradle.kts": "maven",
    "gradle.lockfile": "maven", "gradle.properties": "maven", "libs.versions.toml": "maven", "build.sbt": "maven",
    "packages.config": "nuget", "directory.packages.props": "nuget", "packages.lock.json": "nuget",
    "composer.json": "composer", "composer.lock": "composer",
    "pubspec.yaml": "pub", "pubspec.lock": "pub",
}
KIND_ECOSYSTEM = {
    "python-project": "pypi", "npm-package": "npm", "cargo-crate": "cargo",
    "maven-module": "maven", "gradle-project": "maven", "sbt-project": "maven",
    "dotnet-project": "nuget", "composer-package": "composer", "pub-package": "pub",
}

# Framework spellings that differ by more than case and punctuation. Ask the core owner to extend.
FRAMEWORK_ALIASES = {"next": "nextjs", "nuxtjs": "nuxt", "vue": "vuejs", "nest": "nestjs", "spring": "springframework",
                     "postgres": "postgresql", "awss3": "amazons3", "telegram": "telegrambotapi"}


# ---------------------------------------------------------------- normalisation

def _declared(value, root=None):
    """A declared_in value: a file path, optionally with a #field fragment naming the setting."""
    if value is None:
        return None
    file, sep, field = str(value).partition("#")
    return _path(file, root) + (sep + field.strip() if field.strip() else "")


def _file(value):
    return None if value is None else str(value).partition("#")[0]


def _path(value, root=None, keep_dir=False):
    if value is None:
        return None
    s = str(value).strip().replace("\\", "/")
    if root:
        r = str(root).replace("\\", "/").rstrip("/") + "/"
        if s.lower().startswith(r.lower()):
            s = s[len(r):]
        elif s.lower() + "/" == r.lower():
            s = ""
    is_dir = s.endswith("/")
    s = re.sub(r"/+", "/", s)
    while s.startswith("./"):
        s = s[2:]
    s = s.strip("/")
    if s in ("", "."):
        return "."
    return s + "/" if keep_dir and is_dir else s


def _ecosystem(declared_in=None, kind=None):
    if declared_in:
        base = PurePosixPath(_file(declared_in).replace("\\", "/")).name.lower()
        if base in FILE_ECOSYSTEM:
            return FILE_ECOSYSTEM[base]
        if base.startswith("requirements") and base.endswith((".txt", ".in")):
            return "pypi"
        if base.endswith((".csproj", ".fsproj", ".vbproj")):
            return "nuget"
        if base == "go.mod":
            return "go"
        if base == "gemfile" or base.endswith(".gemspec"):
            return "gem"
    return KIND_ECOSYSTEM.get(kind or "")


def _name(value, eco):
    if value is None:
        return None
    s = str(value).strip()
    if eco == "pypi":
        return re.sub(r"[-_.]+", "-", s).lower()
    if eco in ("npm", "nuget", "composer", "pub"):
        return s.lower()
    if eco == "cargo":
        return s.lower().replace("_", "-")
    if eco == "maven":
        return s.replace("/", ":")
    return s


def _loose(value):
    return None if value is None else re.sub(r"[-_.]+", "-", str(value).strip()).lower()


def _version(value):
    """Spelling-only normalisation: spaces, case, a leading v/go/=/==, trailing .0 segments."""
    if value is None:
        return None
    s = re.sub(r"\s+", "", str(value)).lower()
    s = re.sub(r"^(?:==|=)(?=\d)", "", s)
    s = re.sub(r"^(?:v|go)(?=\d)", "", s)
    return re.sub(r"\d+(?:\.\d+)+", lambda m: re.sub(r"(?:\.0)+$", "", m.group()), s)


def _framework(value):
    s = re.sub(r"[^a-z0-9]", "", str(value).lower())
    return FRAMEWORK_ALIASES.get(s, s)


def _put(out, item, key, value):
    if key in item:
        out[key] = value


def _norm_units(units, root):
    out = []
    for u in units or []:
        kind = str(u.get("kind", "")).strip().lower()
        eco = _ecosystem(u.get("manifest"), kind)
        n = {}
        _put(n, u, "kind", kind)
        _put(n, u, "root", _path(u.get("root"), root))
        _put(n, u, "name", _name(u.get("name"), eco))
        _put(n, u, "manifest", _path(u.get("manifest"), root))
        _put(n, u, "source_roots", sorted({_path(p, root) for p in u.get("source_roots") or []}))
        _put(n, u, "depends_on", sorted({_name(d, eco) for d in u.get("depends_on") or []}))
        _put(n, u, "config", dict(u.get("config") or {}))
        out.append(n)
    return out


def _norm_workspaces(ws, root):
    if ws is None:
        return []
    out = []
    for w in ws if isinstance(ws, list) else [ws]:
        n = {}
        _put(n, w, "tool", str(w.get("tool", "")).strip().lower())
        _put(n, w, "root", _path(w.get("root"), root))
        _put(n, w, "members", sorted({_path(m, root) for m in w.get("members") or []}))
        out.append(n)
    return out


def _norm_toolchains(items, root):
    out = []
    for t in items or []:
        n = {}
        _put(n, t, "tool", str(t.get("tool", "")).strip().lower())
        _put(n, t, "version", None if t.get("version") is None else str(t["version"]).strip())
        _put(n, t, "declared_in", _declared(t.get("declared_in"), root))
        if "declared_in" in t:
            n["declared_file"] = _file(n["declared_in"])
        out.append(n)
    return out


def _norm_dependencies(items, root):
    out = []
    for d in items or []:
        eco = _ecosystem(d.get("declared_in"))
        n = {}
        _put(n, d, "unit", _name(d.get("unit"), eco) if eco else _loose(d.get("unit")))
        _put(n, d, "name", _name(d.get("name"), eco))
        n["loose"] = _loose(d.get("name"))
        for key in ("declared", "resolved"):
            _put(n, d, key, None if d.get(key) is None else str(d[key]).strip())
        _put(n, d, "scope", None if d.get("scope") is None else str(d["scope"]).strip().lower())
        _put(n, d, "declared_in", _declared(d.get("declared_in"), root))
        out.append(n)
    return out


def _norm_named(items, field, root):
    out = []
    for f in items or []:
        n = {"name": _framework(f.get("name", ""))}
        _put(n, f, field, _loose(f.get(field)))
        out.append(n)
    return out


# ---------------------------------------------------------------- matching

def _key(item, fields):
    if any(f not in item or item[f] is None for f in fields):
        return None
    return tuple(item[f] for f in fields)


def _match(exp, got, levels):
    """Pair items level by level (finest key first); returns pairs, unmatched exp, unmatched got."""
    pairs, left_e, left_g = [], list(range(len(exp))), list(range(len(got)))
    for fields in levels:
        index = {}
        for j in left_g:
            k = _key(got[j], fields)
            if k is not None:
                index.setdefault(k, []).append(j)
        rest = []
        for i in left_e:
            k = _key(exp[i], fields)
            bucket = index.get(k) if k is not None else None
            if bucket:
                j = bucket.pop(0)
                pairs.append((i, j))
                left_g.remove(j)
            else:
                rest.append(i)
        left_e = rest
    return pairs, left_e, left_g


def _diff(e, g, fields):
    """Fields that differ; only fields the tool gives are compared. Returns (diff, spelling_only)."""
    diff, spelling_only = {}, True
    for f in fields:
        if f not in g or e.get(f) == g[f] or (f in ("name", "unit") and e.get(f) is None):
            continue
        if (f == "declared_in" and e.get(f) and g[f] and ("#" not in e[f] or "#" not in g[f])
                and _file(e[f]) == _file(g[f])):
            continue  # the fragment is compared only when both sides name one
        diff[f] = {"expected": e.get(f), "got": g[f]}
        if not (f in VERSION_FIELDS and e.get(f) is not None and g[f] is not None
                and _version(e[f]) == _version(g[f])):
            spelling_only = False
    return diff, spelling_only


def _result(expected, found=0, missed=(), extra=(), wrong=()):
    wrong = list(wrong)
    return {"given": True, "expected": expected, "found": found,
            "found_normalised": found + sum(1 for w in wrong if w["same_after_normalisation"]),
            "missed": list(missed), "extra": list(extra), "wrong": wrong}


def _facet(exp, got, levels, fields, label):
    pairs, missed, extra = _match(exp, got, levels)
    found, wrong = 0, []
    for i, j in pairs:
        diff, spelling_only = _diff(exp[i], got[j], fields)
        if diff:
            wrong.append({"item": label(exp[i]), "fields": diff, "same_after_normalisation": spelling_only})
        else:
            found += 1
    return _result(len(exp), found, [label(exp[i]) for i in missed], [label(got[j]) for j in extra], wrong)


def _pairs_facet(exp_units, got_units, pairs, field, label):
    """Set-valued sub-facet (depends_on, source_roots, members) over every expected unit."""
    by_exp = {i: j for i, j in pairs}
    expected, found, missed, extra = 0, 0, [], []
    for i, e in enumerate(exp_units):
        want = set(e.get(field) or [])
        expected += len(want)
        j = by_exp.get(i)
        have = set(got_units[j][field]) if j is not None and field in got_units[j] else set()
        found += len(want & have)
        missed += [f"{label(e)} > {v}" for v in sorted(want - have)]
        extra += [f"{label(e)} > {v}" for v in sorted(have - want)]
    return _result(expected, found, missed, extra)


def _config_facet(exp_units, got_units, pairs, label):
    by_exp = {i: j for i, j in pairs}
    expected, found, missed, wrong = 0, 0, [], []
    for i, e in enumerate(exp_units):
        want = e.get("config") or {}
        expected += len(want)
        j = by_exp.get(i)
        have = got_units[j].get("config") if j is not None else None
        for key in sorted(want):
            item = f"{label(e)} > {key}"
            if have is None or key not in have:
                missed.append(item)
            elif _canon(have[key]) == _canon(want[key]):
                found += 1
            else:
                wrong.append({"item": item, "fields": {key: {"expected": want[key], "got": have[key]}},
                              "same_after_normalisation": False})
    return _result(expected, found, missed, [], wrong)


def _canon(value):
    """Order-free form of a config value: lists sorted, paths normalised."""
    def walk(v):
        if isinstance(v, dict):
            return {str(k): walk(x) for k, x in v.items()}
        if isinstance(v, list):
            return sorted((walk(x) for x in v), key=lambda x: json.dumps(x, sort_keys=True))
        return _path(v) if isinstance(v, str) and "/" in v.replace("\\", "/") else v
    return json.dumps(walk(value), sort_keys=True)


def _not_given(expected):
    return {"given": False, "expected": expected}


def _unit_label(u):
    label = f"{u.get('kind', '')}@{u.get('root', '')}"
    return label + f":{u['name']}" if str(u.get("kind", "")).endswith("-target") and u.get("name") else label


def _ws_label(w):
    return f"{w.get('tool', '')}@{w.get('root', '')}"


# ---------------------------------------------------------------- score

def _known_units_only(expected, got):
    """Apply {"facet": f, "known": [units]} entries of "unknown": score f only for those units."""
    expected, got = dict(expected), dict(got)
    for entry in expected.get("unknown") or []:
        if not isinstance(entry, dict) or entry.get("facet") not in PER_UNIT:
            continue
        facet, known = entry["facet"], {_loose(u) for u in entry.get("known") or []}
        kept = [x for x in expected.get(facet) or [] if _loose(x.get("unit")) in known]
        names = {_loose(x.get("name")) for x in kept}
        expected[facet] = kept
        if isinstance(got.get(facet), list):
            got[facet] = [x for x in got[facet] if (_loose(x.get("unit")) in known if "unit" in x
                                                     else _loose(x.get("name")) in names)]
    return expected, got


def score(expected, got, root=None):
    """Score one fixture. `root`, if given, is stripped from absolute paths in `got`."""
    expected, got = _known_units_only(expected, got)
    out = {}

    # languages: the set of names, and the language of each listed file
    e_lang = expected.get("languages") or []
    e_names = {}
    for x in e_lang:
        e_names.setdefault(str(x["language"]).lower(), x["language"])
    e_files = {_path(x["path"]): str(x["language"]).lower() for x in e_lang if x.get("path")}
    if "languages" in got:
        g_lang = got["languages"] or []
        g_names = {}
        for x in g_lang:
            g_names.setdefault(str(x.get("language", "")).lower(), x.get("language", ""))
        out["languages"] = _result(len(e_names), len(set(e_names) & set(g_names)),
                                   [e_names[k] for k in sorted(set(e_names) - set(g_names))],
                                   [g_names[k] for k in sorted(set(g_names) - set(e_names))])
        g_files = {_path(x["path"], root): str(x.get("language", "")).lower() for x in g_lang if x.get("path")}
        if g_files:
            found, missed, wrong = 0, [], []
            for p, lang in sorted(e_files.items()):
                if p not in g_files:
                    missed.append(p)
                elif g_files[p] == lang:
                    found += 1
                else:
                    wrong.append({"item": p, "fields": {"language": {"expected": lang, "got": g_files[p]}},
                                  "same_after_normalisation": False})
            out["languages.files"] = _result(len(e_files), found, missed, [], wrong)
        else:
            out["languages.files"] = _not_given(len(e_files))
    else:
        out["languages"] = _not_given(len(e_names))
        out["languages.files"] = _not_given(len(e_files))

    # excluded: a directory entry (trailing /) covers the files under it, both ways
    e_ex = [(_path(x["path"], keep_dir=True), x.get("why")) for x in expected.get("excluded") or []]
    if "excluded" in got:
        g_ex = [(_path(x["path"], root, keep_dir=True), x.get("why"), "why" in x) for x in got["excluded"] or []]
        used, found, missed, wrong = set(), 0, [], []
        for p, why in e_ex:
            cover = [j for j, (q, _, _) in enumerate(g_ex) if _covers(p, q)]
            used.update(cover)
            if not cover:
                missed.append(p)
                continue
            whys = {g_ex[j][1] for j in cover if g_ex[j][2]}
            if whys and why not in whys:
                wrong.append({"item": p, "fields": {"why": {"expected": why, "got": sorted(map(str, whys))}},
                              "same_after_normalisation": False})
            else:
                found += 1
        extra = [g_ex[j][0] for j in range(len(g_ex)) if j not in used]
        out["excluded"] = _result(len(e_ex), found, missed, extra, wrong)
    else:
        out["excluded"] = _not_given(len(e_ex))

    # units and their set-valued parts
    e_units = _norm_units(expected.get("units"), None)
    sub = {"units.depends_on": "depends_on", "units.source_roots": "source_roots"}
    if "units" in got:
        g_units = _norm_units(got["units"], root)
        levels = [("root", "kind", "name", "manifest"), ("root", "kind", "name"), ("root", "kind"), ("root",)]
        out["units"] = _facet(e_units, g_units, levels, ("kind", "name", "manifest"), _unit_label)
        pairs, _, _ = _match(e_units, g_units, levels)
        for facet, field in sub.items():
            if any(field in u for u in g_units):
                out[facet] = _pairs_facet(e_units, g_units, pairs, field, _unit_label)
            else:
                out[facet] = _not_given(sum(len(u.get(field) or []) for u in e_units))
        if any("config" in u for u in g_units):
            out["units.config"] = _config_facet(e_units, g_units, pairs, _unit_label)
        else:
            out["units.config"] = _not_given(sum(len(u.get("config") or {}) for u in e_units))
    else:
        out["units"] = _not_given(len(e_units))
        for facet, field in sub.items():
            out[facet] = _not_given(sum(len(u.get(field) or []) for u in e_units))
        out["units.config"] = _not_given(sum(len(u.get("config") or {}) for u in e_units))

    # workspace (an object or a list of objects) and its members
    e_ws = _norm_workspaces(expected.get("workspace"), None)
    if "workspace" in got:
        g_ws = _norm_workspaces(got["workspace"], root)
        levels = [("root", "tool"), ("root",)]
        out["workspace"] = _facet(e_ws, g_ws, levels, ("tool",), _ws_label)
        pairs, _, _ = _match(e_ws, g_ws, levels)
        if any("members" in w for w in g_ws):
            out["workspace.members"] = _pairs_facet(e_ws, g_ws, pairs, "members", _ws_label)
        else:
            out["workspace.members"] = _not_given(sum(len(w.get("members") or []) for w in e_ws))
    else:
        out["workspace"] = _not_given(len(e_ws))
        out["workspace.members"] = _not_given(sum(len(w.get("members") or []) for w in e_ws))

    simple = (
        ("toolchains", _norm_toolchains, [("tool", "declared_in", "version"), ("tool", "declared_in"), ("tool", "declared_file", "version"),
                                            ("tool", "declared_file"), ("tool",)],
         ("version", "declared_in"),
         lambda t: f"{t.get('tool', '')}@{t['declared_in']}" if t.get("declared_in") else t.get("tool", "")),
        ("dependencies", _norm_dependencies,
         [("unit", "name", "scope", "declared_in"), ("unit", "name", "scope"), ("unit", "name"), ("name",),
          ("loose",)],
         ("unit", "declared", "resolved", "scope", "declared_in"),
         lambda d: f"{d.get('name')} ({d['unit']})" if d.get("unit") else str(d.get("name"))),
        ("frameworks", lambda x, r: _norm_named(x, "unit", r), [("name", "unit"), ("name",)], ("unit",),
         lambda f: f["name"]),
        ("services", lambda x, r: _norm_named(x, "kind", r), [("name",)], (), lambda s: s["name"]),  # kind: free word, not compared
    )
    for facet, norm, levels, fields, label in simple:
        e = norm(expected.get(facet), None)
        out[facet] = _facet(e, norm(got[facet], root), levels, fields, label) if facet in got else _not_given(len(e))

    # needs: one item, the container flag
    if "needs" in got:
        want = bool((expected.get("needs") or {}).get("container", False))
        have = (got["needs"] or {}).get("container")
        if have is None or bool(have) == want:
            out["needs"] = _result(1, 1)
        else:
            out["needs"] = _result(1, 0, wrong=[{"item": "needs", "fields": {"container": {
                "expected": want, "got": bool(have)}}, "same_after_normalisation": False}])
    else:
        out["needs"] = _not_given(1)
    unknown = {k for k in expected.get("unknown") or [] if isinstance(k, str)}
    return {facet: r for facet, r in out.items() if facet.split(".")[0] not in unknown}


def _covers(e, g):
    if e == g:
        return True
    if e.endswith("/") and (g + "/").startswith(e):
        return True
    return g.endswith("/") and (e + "/").startswith(g)


# ---------------------------------------------------------------- check expected.json

def check_expected(doc, fixture_dir):
    """Shape problems of one expected.json; paths are checked when fixture_dir is given."""
    p = []
    if not isinstance(doc, dict):
        return ["top level is not an object"]
    for k in doc:
        if k not in TOP_KEYS:
            p.append(f"unknown key {k!r}")
    for k in ("needs", "traps"):
        if k not in doc:
            p.append(f"missing {k!r}")
    base = Path(fixture_dir) if fixture_dir else None

    def path_ok(where, value, want_dir=None):
        if not isinstance(value, str):
            p.append(f"{where}: path is not a string: {value!r}")
            return
        if "\\" in value or value.startswith("/") or PureWindowsPath(value).drive:
            p.append(f"{where}: path not POSIX relative: {value!r}")
            return
        if base is None:
            return
        target = base / value if value not in ("", ".") else base
        if not target.exists():
            p.append(f"{where}: path does not exist: {value!r}")
        elif want_dir is True and not target.is_dir():
            p.append(f"{where}: not a directory: {value!r}")
        elif want_dir is False and target.is_dir():
            p.append(f"{where}: is a directory: {value!r}")

    def items(key):
        value = doc.get(key)
        if value is None:
            return []
        if not isinstance(value, list):
            p.append(f"{key}: not a list")
            return []
        good = []
        for n, x in enumerate(value):
            if isinstance(x, dict):
                good.append((f"{key}[{n}]", x))
            else:
                p.append(f"{key}[{n}]: not an object")
        return good

    def need(where, x, *fields):
        for f in fields:
            if not isinstance(x.get(f), str):
                p.append(f"{where}: {f!r} missing or not a string")

    for w, x in items("languages"):
        need(w, x, "language")
        if "path" in x:
            path_ok(w, x["path"], want_dir=False)
    for w, x in items("excluded"):
        need(w, x, "path")
        if x.get("why") not in WHY:
            p.append(f"{w}: why {x.get('why')!r} not in {WHY}")
        if isinstance(x.get("path"), str) and x.get("why") != "submodule":  # a submodule may be absent
            path_ok(w, x["path"], want_dir=x["path"].endswith("/") or None)

    units = items("units")
    names = {u.get("name") for _, u in units}
    # a unit is referred to by its name, or by its root when it has no name or shares it with another unit
    counts = {}
    for _, u in units:
        counts[u.get("name")] = counts.get(u.get("name"), 0) + 1
    refs = ({n for n in names if n is not None} | {None}
            | {u.get("root") for _, u in units if u.get("name") is None or counts[u.get("name")] > 1})
    seen = set()
    for w, u in units:
        need(w, u, "kind", "root")
        if not (u.get("name") is None and "name" in u or isinstance(u.get("name"), str)):
            p.append(f"{w}: 'name' missing: give it as the manifest writes it, or null when nothing names the unit")
        if isinstance(u.get("kind"), str) and u["kind"] not in KINDS:
            p.append(f"{w}: kind {u['kind']!r} not in the SCHEMA.md list")
        for c in (u.get("config") or {}) if isinstance(u.get("config"), dict) else ():
            if c not in CONFIG_KEYS:
                p.append(f"warning: {w}: config key {c!r} is not in the documented vocabulary")
        key = (_path(u.get("root")), u.get("kind"), u.get("name"), _path(u.get("manifest")))
        if key in seen:
            p.append(f"{w}: duplicate unit {key}")
        seen.add(key)
        if isinstance(u.get("root"), str):
            path_ok(w + ".root", u["root"], want_dir=True)
        if "manifest" not in u or u["manifest"] == "":
            p.append(f"{w}: manifest missing or empty: give the file, or null for a unit without one")
        elif u["manifest"] is not None:
            path_ok(w + ".manifest", u["manifest"], want_dir=False)
        for s in u.get("source_roots") or []:
            path_ok(w + ".source_roots", s, want_dir=True)
        for d in u.get("depends_on") or []:
            if d not in refs:
                p.append(f"{w}: depends_on {d!r} is not a unit name")
        if "config" in u and not isinstance(u["config"], dict):
            p.append(f"{w}: config is not an object")

    ws = doc.get("workspace")
    for n, x in enumerate(ws if isinstance(ws, list) else [ws] if ws else []):
        w = f"workspace[{n}]"
        if not isinstance(x, dict):
            p.append(f"{w}: not an object")
            continue
        need(w, x, "tool", "root")
        if isinstance(x.get("root"), str):
            path_ok(w + ".root", x["root"], want_dir=True)
        roots = {_path(u.get("root")) for _, u in units}
        for m in x.get("members") or []:
            path_ok(w + ".members", m, want_dir=True)
            if units and _path(m) not in roots:
                p.append(f"{w}: member {m!r} is not a unit root")

    dep_names = {(str(d.get("name", "")).lower(), _file(d.get("declared_in"))) for _, d in items("dependencies")}
    for w, t in items("toolchains"):
        need(w, t, "tool", "version", "declared_in")
        if (str(t.get("tool", "")).lower(), _file(t.get("declared_in"))) in dep_names:
            p.append(f"{w}: {t.get('tool')!r} is also a dependency in the same file: the package manager installs it, "
                     "so it is not a toolchain")
        if str(t.get("tool", "")).lower() in CHECKERS:
            p.append(f"{w}: {t.get('tool')!r} only targets a language version: tool is the language, "
                     "declared_in names the setting after #")
        if isinstance(t.get("declared_in"), str):
            path_ok(w, _file(t["declared_in"]), want_dir=False)
    seen = set()
    for w, d in items("dependencies"):
        need(w, d, "name", "declared_in")
        if units and d.get("unit") not in refs:
            p.append(f"{w}: unit {d.get('unit')!r} is not a unit name")
        eco = _ecosystem(d.get("declared_in"))
        same_eco = {_loose(u.get("name")) for _, u in units
                    if u.get("name") and (eco is None or _ecosystem(u.get("manifest"), u.get("kind")) in (eco, None))}
        if d.get("name") and _loose(d.get("name")) in same_eco:
            p.append(f"warning: {w}: {d.get('name')!r} is also a unit of this project: fine if it is the published "
                     "package, otherwise it goes in depends_on")
        if d.get("scope") not in SCOPES:
            p.append(f"{w}: scope {d.get('scope')!r} not in {SCOPES}")
        for f in ("declared", "resolved"):
            if f not in d or not (d[f] is None or isinstance(d[f], str)):
                p.append(f"{w}: {f!r} missing or not a string or null")
        key = (d.get("unit"), d.get("name"), d.get("scope"), d.get("declared_in"))
        if key in seen:
            p.append(f"{w}: duplicate dependency {key}")
        seen.add(key)
        if isinstance(d.get("declared_in"), str):
            path_ok(w, _file(d["declared_in"]), want_dir=False)
    for key in ("frameworks", "services"):
        for w, f in items(key):
            need(w, f, "name", "evidence", *(("kind",) if key == "services" else ()))
            if key == "frameworks" and units and "unit" in f and f["unit"] not in refs:
                p.append(f"{w}: unit {f['unit']!r} is not a unit name")
            if isinstance(f.get("evidence"), str):
                path_ok(w, f["evidence"])
    needs = doc.get("needs")
    if "needs" in doc:
        if not isinstance(needs, dict) or not isinstance(needs.get("container"), bool):
            p.append("needs: container missing or not a boolean")
        elif needs["container"] and not str(needs.get("reason", "")).strip():
            p.append("needs: container is true without a reason")
    for k in doc.get("unknown") or []:
        if isinstance(k, dict):
            f, known = k.get("facet"), k.get("known")
            if f not in PER_UNIT or not isinstance(known, list):
                p.append(f"unknown: {k!r} must be {{'facet': one of {PER_UNIT}, 'known': [unit names]}}")
                continue
            for u in known:
                if u not in refs:
                    p.append(f"unknown: known unit {u!r} is not a unit name")
            for w, x in items(f):
                if x.get("unit") not in known:
                    p.append(f"{w}: unit {x.get('unit')!r} is not in the known units of {f}")
        elif k not in FACT_KEYS:
            p.append(f"unknown: {k!r} is not a facet")
        elif doc.get(k):
            p.append(f"unknown: {k!r} is listed as unknown but also filled")
    for w, c in items("connections"):
        need(w, c, "kind", "key")
        for side in ("provided_by", "used_by"):
            if not isinstance(c.get(side), list):
                p.append(f"{w}: {side!r} missing or not a list of unit names")
                continue
            for u in c[side]:
                if units and u not in refs:
                    p.append(f"{w}: {side} {u!r} is not a unit name")
        if not isinstance(c.get("evidence"), list) or not c["evidence"]:
            p.append(f"{w}: 'evidence' missing or not a non-empty list of files")
        else:
            for e in c["evidence"]:
                path_ok(w + ".evidence", _file(e))
    traps = doc.get("traps")
    if "traps" in doc and (not isinstance(traps, list) or not traps or not all(isinstance(t, str) for t in traps)):
        p.append("traps: must be a non-empty list of strings")
    return p


# ---------------------------------------------------------------- CLI

def _fixtures(spec):
    names = sorted(d.name for d in FIXTURES.iterdir()
                   if d.is_dir() and not d.name.startswith("_") and (d / "expected.json").exists())
    if spec in (None, "all"):
        return names
    if spec in FAMILIES:
        return [n for n in names if n.split("-", 1)[0] == spec]
    return [s.strip() for s in spec.split(",") if s.strip()]


def _tools(spec):
    if spec == "all":
        return sorted(f.stem for f in RESULTS.glob("*.json"))
    return [s.strip() for s in spec.split(",") if s.strip()]


def run_check(spec):
    bad = 0
    for name in _fixtures(spec):
        d = FIXTURES / name
        try:
            doc = json.loads((d / "expected.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"{name}: cannot read expected.json: {exc}")
            bad += 1
            continue
        descriptor = (d / "source.json").exists()
        problems = check_expected(doc, None if descriptor else d)
        if descriptor:
            try:
                src = json.loads((d / "source.json").read_text(encoding="utf-8"))
                if not isinstance(src.get("repo"), str) or not re.fullmatch(r"[0-9a-f]{40}", str(src.get("commit"))):
                    problems.append("source.json: needs repo (URL) and commit (40 hex characters)")
            except (OSError, ValueError, AttributeError) as exc:
                problems.append(f"source.json: cannot read: {exc}")
        errors = [x for x in problems if not x.startswith("warning:")]
        bad += bool(errors)
        status = f"{len(errors)} errors" if errors else "ok"
        if len(problems) > len(errors):
            status += f", {len(problems) - len(errors)} warnings"
        print(f"{name}: {status}{' (descriptor: paths not checked)' if descriptor else ''}")
        for line in problems:
            print(f"  - {line}")
    return 1 if bad else 0


def run_tables(tool_spec, fixture_spec, json_out=None):
    expected = {}
    for n in _fixtures(fixture_spec):
        try:
            expected[n] = json.loads((FIXTURES / n / "expected.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"skipped {n}: cannot read expected.json: {exc}", file=sys.stderr)
    fixtures = list(expected)
    everything = {}
    for tool in _tools(tool_spec):
        path = RESULTS / f"{tool}.json"
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        runs = data.get("fixtures", {})
        per_fixture = {}
        for n in fixtures:
            got = (runs.get(n) or {}).get("output")
            per_fixture[n] = score(expected[n], got if isinstance(got, dict) else {})
        everything[tool] = per_fixture
        ran = sum(1 for n in fixtures if isinstance((runs.get(n) or {}).get("output"), dict))
        print(f"\n## {tool} {data.get('version', '')}".rstrip() + f"\n\nfixtures with output: {ran}/{len(fixtures)}\n")
        print("| facet | given in | found / expected | identified | normalised | missed | extra |")
        print("| --- | --- | --- | --- | --- | --- | --- |")
        for facet in FACETS:
            rows = [per_fixture[n][facet] for n in fixtures if facet in per_fixture[n]]  # unknown facets drop out
            total = sum(r["expected"] for r in rows)
            given = [r for r in rows if r["given"]]
            if not given:
                print(f"| {facet} | 0/{len(rows)} | not given | | | | |")
                continue
            found = sum(r["found"] for r in given)
            ident = found + sum(len(r["wrong"]) for r in given)
            norm = sum(r["found_normalised"] for r in given)
            missed = sum(len(r["missed"]) for r in given)
            extra = sum(len(r["extra"]) for r in given)
            print(f"| {facet} | {len(given)}/{len(rows)} | {found}/{total} | {ident} | {norm} | {missed} | {extra} |")
    if json_out:
        Path(json_out).write_text(json.dumps(everything, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


def main(argv):
    if argv and argv[0] == "--check":
        return run_check(argv[1] if len(argv) > 1 else None)
    json_out = None
    if "--json" in argv:
        i = argv.index("--json")
        json_out = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if len(argv) != 2:
        print(__doc__)
        return 2
    return run_tables(argv[0], argv[1], json_out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
