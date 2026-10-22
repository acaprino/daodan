# python-parser

Measures which parser the Codebase Map should use for Python, on the axes that
matter for a Code Graph: whether the symbols it produces are right on valid code,
how far its accepted syntax depends on the interpreter running it, what it
recovers from a file that is mid-edit and whether what it recovers is safe to put
into the graph, how fast it is, and what it costs to install.

It is a measurement harness like `../retrieval-benchmark/` and
`../resolver-spike/`, not an agent-scored case. Results and the decision they
support are in `RESULTS.md`.

## Candidates

| Parser | What it is |
|---|---|
| stdlib `ast` | CPython's own parser; the current adapter, `languages/python.py` |
| tree-sitter-python 0.25.0 | the only Python grammar for the engine every other language here uses |
| LibCST 1.9.0 | the only other strict parser with its own grammar, so its accepted syntax does not follow the interpreter |
| parso 0.8.7 | the error-recovering parser under Jedi; excluded on the feature probe, see `RESULTS.md` |

## Corpora

Every corpus is copied once by `freeze.py` into a frozen directory with a SHA-256
manifest, and every parser reads the copy. Two corpora are live repositories, and
a comparison is only valid if every parser reads the same bytes.

- three projects, selected with the Codebase Map's own perimeter (Git-tracked and
  untracked-not-ignored, dot-directories excluded): two user projects and this
  repository without `exports/`
- two `site-packages` trees of those projects' environments, for breadth of real
  third-party code
- `features.py`: one construct per case from Python 3.8 to 3.14, plus invalid code
  that must be rejected
- a work-in-progress corpus built by `mutate.py`: six realistic ways a file is
  broken while someone types (unclosed parenthesis, missing colon, file cut
  mid-body, merge-conflict markers, bad indent, unterminated string) injected into
  valid real files, with the definitions the original declared as ground truth

## Files

| File | Role |
|---|---|
| `freeze.py` | copies every corpus into a frozen tree with a hash manifest |
| `ast_worker.py` | stdlib facts, run once per CPython version; also records the top-level prefix salvage of a broken file |
| `ts_worker.py` | the same facts from tree-sitter-python, plus which definitions touch an ERROR region |
| `libcst_worker.py` | the same facts from LibCST |
| `run_all.py` | runs every worker on every corpus in parallel and builds the work-in-progress corpus |
| `analyze.py` | sections A to J: parse status, interpreter dependence, structural agreement, feature matrix, recovery by name, timing, the adapter's own extraction losses |
| `analyze_cst.py` | section K: LibCST against stdlib |
| `salvage_eval.py` | recovery scored on spans as well as names, with every stdlib and tree-sitter policy |
| `gap_diagnosis.py` | replays the resolver measurement's Python gap with the snapshot inventory as the project test, and diagnoses each remaining position with Jedi `goto` |
| `probe_divergences.py`, `probe_libcst.py`, `probe_parso.py` | one construct per parse for every divergence the corpora showed |

Workers emit one JSON line per file with the same fields (`q` qualified name, `k`
kind, `l` keyword line, `e` end line, `c` byte column, `d` decorators, `b` inside a
compound statement, `a` enclosing kinds), so every comparison is between parsers,
never between extractors. All walkers are iterative.

## Running

```
python freeze.py --dest <frozen> --corpus "name=git|<repo>[|exclude-regex]" --corpus "name=dir|<folder>"
python run_all.py --out <dir> --interp 3.11=<python> ... --interp 3.14=<python> --reference 3.14 \
    --ts-python <venv with tree-sitter-python> --cst-python <venv with libcst> \
    --corpus "name=dir|<frozen>/name" ... --mutation-corpora a,b,c --mutations-per-corpus 120
python analyze.py --out <dir>
python analyze_cst.py --out <dir>
python salvage_eval.py --out <dir>        # with the reference interpreter
uv run --no-project --script gap_diagnosis.py --fix1 <jedi-edges-fix1.json> --manifest <manifest.sqlite> \
    --project <project root> --out <gap.json>
```

Every disagreement counted is written with file and line to `<dir>/examples/`.
Write outputs outside the repository.
