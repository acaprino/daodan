# abi3 packaging of the Oracle PL/SQL grammar: measured, and deliberately not adopted

This file records a packaging experiment that was run to completion and then
**rejected**. It is kept because the numbers are the reason it was rejected, and
because the question will come back the first time a real Oracle codebase has to
be mapped.

## The problem

`njank/tree-sitter-plsql` publishes no wheel. It has no PyPI release, no git tag
and no release automation, and its `setup.py` builds a version-specific C
extension, so consuming it requires a C compiler on the machine that installs
it. Every other grammar the Codebase Map uses arrives as a published wheel,
which is why no other language has this cost.

## The patch that collapses the wheel matrix

`bindings/python/tree_sitter_plsql/binding.c` uses only Limited-API calls
(`PyCapsule_New`, `PyMethodDef`, `PyModuleDef_HEAD_INIT`, `PyModule_Create`,
`PyMODINIT_FUNC`), and `src/parser.c` and `src/scanner.c` are pure tree-sitter
runtime C that never touch CPython. So an abi3 build is viable. Two additions to
`setup.py`, inside the `Extension(...)` and inside `setup(...)`:

```python
        Extension(
            name="tree_sitter_plsql._binding",
            sources=[...],
            include_dirs=["src"],
            extra_compile_args=extra_compile_args,
            define_macros=[("Py_LIMITED_API", "0x03090000")],   # added
            py_limited_api=True,                                # added
        )
    ],
    python_requires=">=3.9",
    options={"bdist_wheel": {"py_limited_api": "cp39"}},        # added
```

Build recipe, Windows (MSVC Build Tools 2022, `cl` 14.44.35207):

```bat
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
uv build --wheel --out-dir dist <grammar-checkout>
```

## Measured outcome

| | value |
|---|---|
| wheel produced | `tree_sitter_plsql-0.1.0-cp39-abi3-win_amd64.whl` |
| wheel size | 831,372 B = **0.79 MB** |
| installed `_binding.cp312-win_amd64.pyd` (non-abi3 build) | 11,656,704 B = **11.12 MB** |
| build wall time | ~21 s |
| built against | CPython 3.12.10 |
| **imports and parses correctly under CPython 3.11.15** | **yes** (`ABI3_OK has_error=False`) |
| imports and parses correctly under CPython 3.12.10 | yes |

The cross-version result is the point: one binary per platform covers Python
3.9 and later, so the matrix collapses from platforms x Python versions (4 x 5
= 20 binaries) to **4 binaries**.

Comparison points measured in the same environment: `tree-sitter-sql` 0.3.11
installs a 2.43 MB `_binding.pyd`; the `tree-sitter` runtime itself is 0.23 MB.

## Why it was still not adopted

Bundling the compiled extension into the plugin was costed and rejected:

| | size | consequence |
|---|---:|---|
| 4 platforms, installed `.pyd` | 44.5 MB | in the plugin kernel |
| x 5 host packages (the compiler replicates every skill file into `exports/<host>/`) | **222 MB** | against ~30 MB for all of `exports/` today, a 7x payload |
| `.git` today | 274 MB | binaries do not delta; every rebuild re-grows it |
| largest tracked file today | 1.87 MB | would become 11.12 MB |

Three further objections, none of them about size:

1. **No compiled binary is tracked in this repository today.** `git ls-files`
   over `.pyd/.so/.dylib/.dll/.whl` returns nothing, and
   `languages/_treesitter.py` obtains every grammar as a published package:
   `tree-sitter-language-pack` first, then per-grammar modules
   (`tree_sitter_python`, `tree_sitter_java`, `tree_sitter_sql`,
   `tree_sitter_rust`, `tree_sitter_go`). Bundling would make PL/SQL the only
   exception and the only grammar not arriving as a package.
2. **Bundling transfers the build obligation to us, it does not remove it.** The
   four binaries must be produced per platform, per upstream change, with
   MSVC/gcc/Xcode, in CI, indefinitely. Today that obligation belongs to nobody,
   because the grammar is unpublished.
3. **It is the wrong artifact to take provenance for.** The grammar publishes no
   tests, and its own README warns that exceeding its state budget "generates
   without errors but misparses at runtime in layout-dependent ways". Signing a
   binary built from that, for five hosts, means users run something they cannot
   audit and we own any silent misparse.

Bundling the wheels instead (3.2 MB) avoids the size problem but not the install
problem: a wheel is not importable, and the helper scripts run under
`uv run --no-config --no-project --script`, which resolves inline dependencies
from an index. A local wheel would need a path-based dependency, which is
host-specific wiring of exactly the kind the operational-compatibility rules
reject.

## The escalation path if this ever becomes a real requirement

Not bundling. Publishing an abi3 wheel under our own distribution name, built by
a cibuildwheel job over the four platforms, so that PL/SQL reaches users the same
way `tree-sitter-sql` already does. That costs no repository growth and no
compiler on the user's machine.

The precondition for taking that on is a real corpus. There is none today: see
`RESULTS.md`, "Evidence base".
