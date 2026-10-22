# python-parser results

Run date **2026-10-22**, one machine, Windows. The corpus figures are full
counts, not samples; the work-in-progress figures are over a seeded sample of
real files. Raw outputs are machine-local, under the bench directory of the run,
and every disagreement counted below was written there with file and line.

## Decision

**Python stays on the stdlib `ast` parser.** On valid code it is the reference
and the other strict parser agrees with it exactly; tree-sitter-python invents
definitions, cannot tell valid from invalid code, and does not cover Python 3.13.
Its only advantage, recovery from a broken file, is mostly in output that would
put wrong spans into the graph; the part that is safe can be had from the stdlib
itself, without a dependency.

Two changes follow, neither of them a parser change:

1. **Pin the interpreter.** The stdlib grammar follows the interpreter that runs
   the map. Under 3.11, four measured files are rejected that 3.12 accepts. The
   snapshot already records the Python minor in its parser fingerprint; it should
   also require a minimum (3.12 for every file measured here, 3.14 for the newest
   syntax) and declare the version in the report.
2. **Recover broken files with the stdlib.** Today a file with one syntax error
   yields no symbols at all. Parsing the longest prefix that ends on a logical
   line, and keeping only the definitions that prefix closes, recovers half of a
   broken file's definitions with **zero** wrong symbols and zero truncated spans
   on 1,892 broken files.

The Code Graph prerequisite recorded beside the resolver measurement, targets an
engine resolves but the symbol table does not recognise, has **no** parser cause:
see the last section.

## Versions under test

| Component | Identity |
|---|---|
| stdlib `ast` | CPython 3.11.15, 3.12.10, 3.13.14, 3.14.8 (reference 3.14) |
| tree-sitter-python | 0.25.0 (ABI 15) on tree-sitter 0.26.0, CPython 3.12.10 |
| LibCST | 1.9.0, CPython 3.12.10 |
| parso | 0.8.7, grammars 3.6 to 3.14 |

## Corpora

| Corpus | Files | Definitions (ast) | Imports (ast) |
|---|---:|---:|---:|
| user project 1 | 812 | 11,765 | 7,713 |
| user project 2 | 617 | 7,749 | 8,580 |
| this repository, without `exports/` | 264 | 4,408 | 2,931 |
| `site-packages` of project 1 | 8,954 | 163,973 | 106,024 |
| `site-packages` of project 2 | 11,889 | 207,101 | 136,843 |
| **total** | **22,536** | **394,996** | **262,091** |

## 1. Valid code

Every file was accepted by `ast` 3.14 and by tree-sitter without an ERROR node.

| | tree-sitter vs ast | LibCST vs ast |
|---|---|---|
| definitions matched (qualified name, kind, keyword line) | **394,996 of 394,996** | **394,996 of 394,996** |
| definitions emitted that ast does not declare | **13** | **0** |
| imports matched | 262,091 of 262,091 | 262,091 of 262,091 |
| column, decorator count, block flag on matched | identical | identical (column not exposed) |
| end line on matched | **614 differ** | 0 differ |

**The 13 extra definitions are wrong.** tree-sitter reads an assignment through a
call to the builtin `type` as a PEP 695 alias statement:

```python
type(enricher1).__name__ = "AdrasteaEnricher"     # tree-sitter: type_alias_statement
```

Isolated in `probe_divergences.py` (case 1): no ERROR node, a
`type_alias_statement` spanning the whole line. `type Pair = ...` and
`x = type(3)` are parsed correctly. Cases of this shape appear in real tests and
real libraries (aiohttp, cffi, pandas) and each becomes a symbol named
`<enclosing>.__name__` or similar that does not exist.

**The 614 end-line differences are a convention, not an error**: tree-sitter ends
a definition after trailing comments inside its indentation, ast at the last
statement (`probe_divergences.py` case 2). It matters only because a symbol's span
feeds its body hash: switching parser would change every such symbol's hash
without any code change.

## 2. The grammar and the interpreter

`features.py` (31 cases), one construct per parse:

| Construct | ast 3.11 | ast 3.12 | ast 3.13 | ast 3.14 | tree-sitter | LibCST |
|---|---|---|---|---|---|---|
| 3.8 to 3.11 syntax (walrus, match, except*, ...), 8 cases | ok | ok | ok | ok | ok | ok |
| PEP 695 generics and `type` aliases, PEP 701 f-strings, 5 cases | rejects | ok | ok | ok | ok | ok |
| PEP 696 type-parameter default (3.13) | rejects | rejects | ok | ok | **ERROR node** | ok |
| `except A, B:` and t-strings (3.14), 2 cases | rejects | rejects | rejects | ok | ok | ok |
| version-independent structure, 12 cases | ok | ok | ok | ok | ok, one NFKC name differs | ok |
| Python 2 `print 'x'`, mixed tabs and spaces, NUL byte | rejects | rejects | rejects | rejects | **accepts the first two silently** | rejects |

Every "rejects" in the ast columns is correct for that version. The stdlib parser
is exactly as current as the interpreter running it, and no more.

On the real corpora that dependence showed up four times, all under 3.11 and none
under 3.12 or later: three files of project 2 using `type CellKey = tuple[str, str]`
and similar, and one `pandas_ta` file with a nested-quote f-string
(`f"HMA{"" if mamode == "wma" else mamode[0]}_{length}"`). **No file was accepted by
an older interpreter with a different reading**: the acceptance profile is
monotonic, so a too-old interpreter fails loudly rather than silently.

tree-sitter is current to 3.14 except PEP 696, and it is **not a validator**: it
accepts invalid code with no ERROR node, so a broken file can look parsed.

## 3. Broken files

1,892 effective mutated files (a further 264 mutations left the file valid and are
excluded). Recovery is scored twice. By name: does the emitted (name, kind, line)
exist in the original. By span: does the emitted definition also carry the right
end line, because a wrong span is a wrong body hash. **`unsafe`** counts
emissions that would put a wrong identity or a wrong span into the graph.

| Policy | Name recall | Name precision | Exact spans | Unsafe |
|---|---:|---:|---:|---:|
| ast, whole file (today) | 0.00 % | n/a | 0.00 % | **0** |
| ast, top-level prefix | 38.10 % | 100.00 % | 40.71 % | 265 |
| ast, prefix on any logical line | 58.14 % | 100.00 % | 56.48 % | 2,218 |
| **ast, prefix on any logical line, closed definitions only** | **50.16 %** | **100.00 %** | **54.69 %** | **0** |
| tree-sitter, every definition | 86.98 % | 90.81 % | 86.64 % | 5,705 |
| tree-sitter, outside ERROR regions | 72.39 % | 94.81 % | 76.22 % | 2,256 |
| tree-sitter, before the first error | 50.95 % | 100.00 % | 52.84 % | 869 |

Unsafe emissions are partial spans (a container of the broken line, reported as
ending where the parse stopped) and wrong identities (a definition with no
counterpart, or a method attributed to the wrong class). The 3,076 wrong
identities of tree-sitter's full output are concentrated in merge-conflict and
missing-colon files, where error recovery re-parents the methods that follow the
error.

**The safe frontier is about 51 % recall, and both parsers reach it.** The best
safe tree-sitter policy, definitions before the first error, recalls 50.95 % and
still emits 869 partial spans. The stdlib closed-prefix policy recalls 50.16 %
with zero unsafe output, no dependency, and the same parser the map already uses.
Everything above that frontier is recall bought with wrong symbols.

Per mutation (name recall / unsafe):

| Mutation | ast closed prefix | tree-sitter before error | tree-sitter, all |
|---|---|---|---|
| bad indent | 53.82 % / 0 | 100.00 % / 436 | 100.00 % / 436 |
| merge conflict | 43.00 % / 0 | 45.57 % / 410 | 82.69 % / 1,483 |
| missing colon | 44.06 % / 0 | 24.07 % / 0 | 73.37 % / 1,616 |
| truncated mid-body | 81.64 % / 0 | 80.33 % / 23 | 97.27 % / 398 |
| unclosed parenthesis | 50.78 % / 0 | 36.00 % / 0 | 80.14 % / 1,274 |
| unterminated string | 48.14 % / 0 | 47.93 % / 0 | 97.73 % / 498 |

The stdlib recovery re-parses on average one or two prefixes per file: 1,297 of
1,892 files needed one attempt, 7 hit the cap of 60.

## 4. Speed

Sum of per-file parser time over the five corpora, the parser call alone:

| | Total | Median per file |
|---|---:|---:|
| ast 3.11 | 65.7 s | 0.84 to 2.71 ms |
| ast 3.14 | 80.8 s | 0.96 to 3.46 ms |
| tree-sitter | 56.0 s | 0.76 to 2.32 ms |
| LibCST | **4,594.5 s** | 49 to 264 ms |

All workers ran side by side under the same load. tree-sitter takes about 69 % of
ast 3.14's time, which is around 1 ms per file either way and invisible beside the
snapshot's other work. LibCST is about 57 times slower than ast for an identical
result, which disqualifies it.

## 5. Candidates excluded on the feature probe

**parso 0.8.7** reports error nodes on valid 3.10 to 3.14 syntax: `match`,
`except*`, PEP 695 `type` aliases, PEP 701 f-strings with nested quotes, `except
A, B:` and t-strings all produce `error_node` with its newest grammar
(`probe_parso.py`). It was not run on the corpora.

**LibCST 1.9.0** passed the feature probe (all valid cases accepted, all invalid
rejected) and was run on everything: identical to ast on all 22,536 files, at 57
times the cost. Its one real advantage, a grammar independent of the
interpreter, is matched by pinning the interpreter.

## 6. The Code Graph prerequisite has no parser cause

The resolver measurement recorded positions where Jedi resolves a call to a
target inside the project and the snapshot's symbol table does not recognise it:
374 of 1,600 on project 1, 181 of 1,600 on project 2. `gap_diagnosis.py` replayed
the same sample with the same environment per file; the replay reproduced the
published verdicts exactly on both projects.

**Most of the bucket is a defect of the measurement script.** `jedi_edges.py`
treats a target as "in the project" when its path is below the project root, and
a project's virtual environments live below its root. With the environments that
Fix 1 supplied, every third-party definition (`rich`, `pytest`, `pydantic`,
`opentelemetry`, `pymongo`) passed that test. Counting a target as project only
when its file is in the snapshot inventory:

| | Project 1 | Project 2 |
|---|---:|---:|
| gap as published | 374 | 181 |
| moved to external | 234 | 114 |
| **gap, corrected** | **140** | **67** |
| confirmed edges | 505, unchanged | 324, unchanged |

What remains, diagnosed position by position with Jedi `goto` on the method name:

| Cause | Project 1 | Project 2 | Layer |
|---|---:|---:|---|
| method inherited from a project base class | 125 | 0 | resolution rule |
| function called as a module attribute | 1 | 20 | resolution rule |
| callee external, through inheritance or module attribute | 7 | 9 | none, correctly not an edge |
| goto unresolved: methods of a third-party GUI base class | 3 | 33 | none |
| attribute of a function (`mock.assert_called`) | 3 | 0 | none |
| dynamic attribute | 1 | 5 | none |
| **parser** | **0** | **0** | |

A seeded sample of the 146 "resolution rule" positions, 20 per project, was read
at both ends: 40 of 40 are true edges. Two shapes cover them: `self.info(...)`
resolving to `def info(...)` on a project mixin the receiver's class inherits
from, and `worker.Pacer()` resolving to `class Pacer` in the module the receiver
names. The correction belongs in the resolution rule (follow the MRO to
project bases, resolve module-attribute calls), not in the parser.

**The extraction convention is the other real loss, and it is also not the
parser's.** The adapter records top-level definitions and class methods only.
Measured with ast on the same corpora, it drops 4.8 % to 7.2 % of the projects'
definitions and 8.8 % to 9.7 % of the libraries': functions nested in functions
(555 and 542 in the two projects), definitions inside `if`/`try`/`with` at module
or class level, nested classes, and `type` aliases. Every parser measured sees all
of them; the choice of what to record is the adapter's.

## Not measured

- **Other operating systems.** Windows only. The stdlib parser is the same code on
  every platform; tree-sitter's wheels were not tried elsewhere.
- **Python 3.10 and older interpreters.** 3.11 is the oldest measured.
- **Incremental parsing.** tree-sitter's edit-and-reparse was not exercised; the
  snapshot re-parses whole changed files, so it is not on the current path.
- **Semantic evidence.** The adapter also produces scopes, bindings and
  references with `python_semantics` over the ast tree. A tree-sitter switch would
  have required re-implementing them on another tree; that cost is real but was
  not needed to decide.
- **Hand-written broken files.** The six mutations are realistic but synthetic.
