# CSS parsers compared

The proof of the choice of `@eslint/css-tree` 4.1.3 for the stylesheet graph: the same inputs, the same comparator and the
same corpus through every candidate, re-run on Modal. Run 2026-11-22. `results/` holds the output of the last run.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/css-parser/candidates/modal_candidates.py

Nothing is installed on the host: exact pins go into the image with `--ignore-scripts` at build, the run has
`block_network=True`, the corpus is read as data and never executed. Node v22.23.5, Python 3.12.1.

## Parameters

| What | Value |
|---|---|
| Inputs | `inputs.json`: 197 texts. Expectations were written before each input was run, in three batches (114, 71, 12). 189 are CSS: 106 forms of the specifications and of real stylesheets (`g1`-`g5`: at-rules, selectors, values, robustness: comments, unclosed blocks, BOM, CRLF, form feed), 22 nesting forms (`n`), 21 modern at-rule syntaxes (`s`), 13 Tailwind 4 (`t`), 4 CSS Modules (`m`), 11 values (`v`), 12 nesting with `@layer`, `@scope` and `@container` (`c`). The other 8 (`g6`) are SCSS, Less, Stylus, indented Sass, PostCSS mixins and a `<style>` wrapper: no candidate may throw on them |
| Expectations | rules (selector, line, end line), declarations (name, value, `!important`, line), at-rules (name, prelude, block, lines), comments (text, line, column); 155 inputs carry rule or declaration expectations |
| Comparator | `compare.mjs`, one for all. `failed`: the tool threw or lost something expected (fewer rules, declarations or at-rules). `difference`: nothing lost, something extra or different (value, line, prelude, flag, comment) or a parse error on valid CSS. `as expected`: the rest. A capability a tool does not give is not compared ("not given", below) |
| Invalid by design | 23 inputs (listed in `compare.mjs`, among them the 15 `g5` ones that are invalid CSS): a parse error on them is not counted; "threw on invalid" counts the 15 |
| Adapters | `adapters.mjs` (css-tree, fork, PostCSS, safe-parser, Lightning CSS), `norm_tinycss2.py`, `norm_current.py`; each gives the same shape `{rules, decls, atrules, comments, positions}` |
| Positions | `norm.mjs`: for every node a tool locates, does its text start at the reported line and column (newlines LF, CR, CRLF and FF as CSS Syntax says: "spec"; FF no line end, as an editor and the snapshot: "editor"); does the offset agree with line and column; is a block's end offset exclusive or inclusive of `}` |
| Corpus | `corpus-packages.txt`: 30 npm packages at exact versions, installed one at a time; 1,864 `.css` files found, 1,860 read (an 8 MB limit and unreadable files), 74.6 MB. Counts rules, declarations, at-rules, errors, throws, time |
| Depth | `depth.mjs`: seven forms nested 100 to 50,000 deep; parse, walk, `generate` and `toPlainObject` each alone, css-tree and the fork |
| Current reader | `daodan/core/languages/stylesheet.py` with `base.py` and `comments.py` from this checkout, unchanged (`parse_sheet(text, "css")`, CRLF and CR turned into LF as the snapshot does); two stubs keep tree-sitter out |

Not here: `postcss-selector-parser` and `postcss-value-parser` (PostCSS companions), `@bramus/specificity` (it installs
upstream css-tree). They are in no number below.

## Candidates

| Candidate | Pin | Released | Licence | Install and weight (registry metadata) |
|---|---|---|---|---|
| css-tree | 3.2.1 | 2026-03-05 | MIT | no install script; `mdn-data` 2.27.1, `source-map-js` 1.2.4; 1.36 MB unpacked |
| `@eslint/css-tree` (the fork) | 4.1.3 | 2026-11-17 | MIT | no install script; `mdn-data` 2.37.2, `source-map-js` 1.2.4; 1.52 MB; Node `^20.19 \|\| ^22.13 \|\| >=24` |
| PostCSS | 8.5.33 | 2026-11-13 | MIT | no install script; `nanoid` 3.3.20, `picocolors` 1.1.1, `source-map-js`; 221 KB |
| `postcss-safe-parser` | 7.1.0 | 2026-09-04 | MIT | no install script; uses PostCSS 8.5.33; 5.7 KB |
| Lightning CSS | 1.33.0 | 2026-07-20 | MPL-2.0 | Rust: a native binary per platform (11 optional packages, one installed), `detect-libc`; 514 KB without the binary |
| tinycss2 | 1.5.1 | 2025-11-23 (PyPI) | BSD (PyPI classifier) | Python >= 3.10; `webencodings` 0.6.1; wheel 28 KB |
| current reader | `stylesheet.py` | this checkout | the project's own | Python, no dependency |

Repositories on 2026-11-22 (GitHub API): `csstree/csstree` 2,130 stars, last push 2026-09-16; `eslint/csstree` (the
fork, MIT) 24 stars, last push 2026-11-22.

## Results

### Inputs

Measured: `results/summary.json`, one row per input in `results/per-input.tsv`. "daisyUI forms": the three inputs `c02`,
`c03` and `c12` (a layer with declarations nested in a rule, two levels of nesting).

| Candidate | Rules and declarations met (of 155) | 189 CSS inputs: as expected / difference / failed | Nesting (22): as expected / failed | daisyUI forms (3) as expected | Unknown at-rules (15): as expected / difference / failed | Threw on `g6` (8) | Threw on invalid (15) | Comments right (10) |
|---|---|---|---|---|---|---|---|---|
| css-tree 3.2.1 | 125 | 139 / 28 / 22 | 5 / 17 | 0 | 4 / 10 / 1 | 0 | 0 | 10 |
| fork 4.1.3 | 144 | 167 / 19 / 3 | 22 / 0 | 3 | 4 / 10 / 1 | 0 | 0 | 10 |
| PostCSS | 133 | 164 / 13 / 12 | 22 / 0 | 3 | 14 / 1 / 0 | 6 | 11 | 7 |
| PostCSS + safe-parser | 138 | 170 / 19 / 0 | 22 / 0 | 3 | 14 / 1 / 0 | 0 | 0 | 8 |
| Lightning CSS | 136 | 157 / 11 / 21 | 22 / 0 | 3 | 11 / 0 / 4 | 7 | 9 | 0 |
| Lightning CSS, error recovery | 143 | 142 / 35 / 12 | 22 / 0 | 3 | 0 / 12 / 3 | 0 | 0 | 0 |
| tinycss2 | 136 | 170 / 17 / 2 | 22 / 0 | 3 | 13 / 1 / 1 | 0 | 0 | 10 |
| current reader | 142 | 176 / 12 / 1 | 22 / 0 | 3 | 13 / 1 / 1 | 0 | 0 | 10 |

Not given, so not compared: the current reader gives no selector text, no at-rules and no prelude; Lightning CSS no
selector, value, prelude or comment text, no declaration order or lines and no end position; PostCSS reports no parse
errors. The rows of the current reader and of Lightning CSS are therefore not like for like with the others: what the
hand reader gets wrong in selectors, preludes and value names is not in this table (the A/B of the graph's records in
`benchmarks/css-parser/README.md` measures it).

`results/part-a-table.md` is the earlier per-input table of css-tree 3.2.1 with the fork beside it, classified by hand
(132 as expected, 38 difference, 27 failed of 197, `g6` included). It was not re-run, and its counts are not comparable
with the table above: another classification.

### Positions

Nodes the tool locates (`results/console.txt`, first lines). "start" columns: how many nodes have their own text at the
reported line and column.

| Candidate | Nodes | Start, spec newlines | Start, editor newlines | Offset agrees with line and column | Blocks | End exclusive / inclusive | No end |
|---|---|---|---|---|---|---|---|
| css-tree 3.2.1 | 660 | 654 | 652 | 658 | 308 | 304 / 3 | 0 |
| fork 4.1.3 | 718 | 712 | 710 | 716 | 334 | 330 / 3 | 0 |
| PostCSS | 678 | 676 | 676 | 671 | 306 | 303 / 5 | 0 |
| PostCSS + safe-parser | 759 | 756 | 756 | 752 | 335 | 332 / 5 | 5 |
| tinycss2 | 741 | 739 | 737 | not given | not given | not given | 741 |
| Lightning CSS | 332 | no text | no text | not given | not given | not given | all |

Lightning CSS starts checked against css-tree's own list of starts: 306 of 332 (330 of 356 with recovery). A form feed is
a line end for css-tree and the fork, not for the snapshot: two nodes of the fork's table.

### Corpus

1,860 files, 74.6 MB, every candidate read all of them (`results/corpus*.txt`). Time is the adapter's own wall clock, or
CPU, on 4 Modal CPUs: css-tree took 8.2 to 14.4 s and the fork 6.0 to 12.6 s in the runs seen (the probe's and ours), so
it shows the order of magnitude only. The times below are the last run.

| Candidate | Rules | Declarations | At-rules | Comments | Files with an error | Errors | Files that threw | Time |
|---|---|---|---|---|---|---|---|---|
| css-tree 3.2.1 | 544,830 | 1,335,772 | 34,745 | not read | 107 | 7,840 | 0 | 10.7 s |
| fork 4.1.3 | 544,702 | 1,353,200 | 35,083 | not read | 30 | 320 | 0 | 7.7 s |
| PostCSS | 545,048 | 1,354,710 | 35,157 | 32,892 | not reported | not reported | 0 | 5.4 s |
| PostCSS + safe-parser | 545,048 | 1,354,710 | 35,157 | 32,892 | not reported | not reported | 0 | 5.4 s |
| Lightning CSS | 517,269 | 1,300,175 | 33,597 | 0 | 36 | 156 | 23 | 22.0 s |
| Lightning CSS, error recovery | 545,020 | 1,353,829 | 34,782 | 0 | 36 | 168 | 0 | 23.2 s |
| tinycss2 | 545,048 | 1,354,707 | 35,157 | 32,883 | 3 | 3 | 0 | 11.6 s wall, 40.7 s CPU |
| current reader | 545,048 | 1,354,710 | 34,282 (blocks) | 33,040 | not reported | not reported | 0 | 20.9 s wall, 74.0 s CPU |

What css-tree and its fork keep as `Raw` (a text their grammar does not read, kept exact): css-tree 2,824 statements,
2,461 rule or at-rule preludes and 9 values; the fork 194 statements, 115 preludes and 9 values. PostCSS and the
current reader agree to the unit (rules 545,048, declarations 1,354,710). The fork has 346 rules, 1,510 declarations and
74 at-rules fewer than that, css-tree 218, 18,938 and 412. PostCSS is a count to compare with, not the truth. That the
fork's shortfall is the `Raw` it reports is inferred from the sizes (194 + 115 + 9 nodes, 320 errors in 30 files), not
checked node by node.

### Depth

`results/depth.txt` (css-tree) and `results/depth_fork.txt`. `parse` never threw, from 100 to 50,000 levels of any of the
seven forms; at 3,000 levels and more six of the seven report one parse error (the custom-property blocks none). `walk`,
`generate` and `toPlainObject` threw `RangeError: Maximum call stack size exceeded` at some depth between 300 and 50,000
levels, depending on the form, the candidate and the run (nested rules: `generate` threw at 1,000 for css-tree in the
probe's run and for the fork in the last, and not for the other). A file that throws is `files.missing` with the reason:
the engine wraps parse and walk in `try/catch` per file.

## Why not the others, and what the fork still gets wrong

Measured unless marked *inferred*.

- **css-tree 3.2.1.** It does not read relaxed CSS nesting: after one nested rule, what follows up to the end of the
  block is one `Raw` node with an error (17 of 22 nesting inputs fail, 3 of 3 daisyUI forms; `g3-nesting-amp` loses
  four rules and four declarations). On the corpus that is 7,840 errors in 107 files and 18,938 declarations fewer than
  PostCSS; `daisyui` alone has 2,710 `Raw` statements and 2,346 `Raw` preludes. Valid `@import ... supports(selector(...))`
  and `@supports (not (...))` give a spurious parse error, and the `@supports` prelude's location ends one character
  early; the fork gives no error on them (`results/part-a-table.md`). The fork is the same parser with nesting, `@layer`,
  `@container` and `@scope` fixed.
- **PostCSS 8.5.33 with `postcss-safe-parser` 7.1.0.** The best of the others on these inputs (170 / 19 / 0, nesting 22 of
  22, no throw on the corpus). The core throws on 18 inputs (6 of 8 `g6`, 11 of 15 invalid), so only the safe parser
  would do. Against it: its end offset is missing on 5 nodes, 7 of 759 offsets disagree with line and column, and 8 of
  10 comments are right. *Inferred from its API as the adapter uses it:* a selector, an at-rule's parameters and a value
  are strings, there is no CSS grammar and no property lexer, so the names in `animation`, `font` and `container` and
  every at-rule prelude would need hand rules or two more packages (not measured here): what the repository's rule of
  gold (`AGENTS.md`) asks not to write.
- **Lightning CSS 1.33.0.** It gives no selector, value or prelude text, no declaration order or lines, no end
  positions and no comments (0 of 10); it throws on 21 inputs, 7 of 8 `g6` and 23 corpus files, and with error recovery
  it still has 35 differences and 12 failures. A native binary per platform, MPL-2.0. *Inferred:* its tree is a
  normalised model (declarations and `!important` ones in separate lists), not the source.
- **tinycss2 1.5.1.** Close on these inputs (170 / 17 / 2, 3 parse errors on the corpus) but it gives no end position
  (741 of 741) and no offset. *Inferred from the adapter, which serialises token lists back to text:* its prelude and
  its values are tokens, with no selector grammar and no property lexer; and it is Python, a second runtime beside the
  pinned Node that the Sass, Less and Stylus engines run on.
- **The current reader.** It is what the engine replaces, not a competitor on accuracy: 176 / 12 / 1 on what it gives,
  and the same corpus totals as PostCSS. The repository rule (`AGENTS.md`, "Regola d'oro") keeps a hand-written reader
  only where no official tool gives the datum.
- **The fork (chosen).** 144 of 155 expectations met, 167 / 19 / 3 on the CSS inputs; its 3 failures are
  `g3-nesting-amp-suffix` and `t05-theme-inline` (both invalid CSS) and `c06-container-in-rule-amp`. What it still gets
  wrong:
  - *An at-rule the grammar does not know keeps its prelude as `Raw` with one parse error, the text exact:*
    `@custom-media`, `@custom-selector`, `@value`, `@apply` with variants, `@custom-variant`, `@import ... source(none)`
    (9 of the 15 unknown at-rule inputs, and `c08-custom-media-complex`; 113 `@custom-media` preludes on the corpus). The
    block of an unknown at-rule is read as declarations (`g2-unknown`).
  - *A rule that starts with `&` inside an at-rule block is lost as one `Raw` statement:* `c06-container-in-rule-amp`
    (`.a { @container (...) { & .b { c: d } } }`) loses a rule and a declaration; css-tree 3.2.1 reads that one. On the corpus 192 `Raw` statements,
    all in `daisyui`, their text starting with a selector, inside `@supports` (120), `@starting-style` (36), `@media`
    (24) and `@scope` (12).
  - *Values:* 8 `aspect-ratio: attr(...)` (uikit) and 1 `filter: progid:...` (leaflet) are `Raw`; Tailwind's own `index.css`
    has 2 `Raw` statements in `@theme` and 2 `Raw` rule preludes (`t05-theme-inline`: `--color-*: initial;` is a `Raw`
    statement, the declaration is lost). An escaped at-keyword is not decoded (`@\69 mport` is
    returned with its escape: `s18`).
  - *Recovery on invalid CSS differs from the expectations:* 7 of its 19 differences (six `g5` inputs, `c09`).
  - *Positions:* 6 of 718 node starts do not sit at their text under CSS Syntax newlines (8 under the snapshot's), and 2
    offsets disagree with line and column.
  - *Stack:* `walk`, `generate` and `toPlainObject` throw on deep nesting (above); `parse` does not.

## Re-run against the recorded run

- `results/summary.json` is byte-identical to the probe's `candidates-summary.json`: every count and every position
  figure of every candidate.
- Corpus: counts, errors, throws and `Raw` tables are equal. Differences: times (above); css-tree's table was made by an
  earlier version of `corpus.mjs` (its header and its list of messages differ, the totals and the per-package rows are
  equal); tinycss2's per-package list orders its ties differently (the totals are equal).
- Depth: the thresholds of `walk` and `generate` move with the stack (above); the pattern is the same.
- The corpus resolved to the same tree as the probe's: same top-level versions, the same `extraneous` packages, 1,864
  `.css` files (`results/versions.txt`). The probe installed the corpus by package name; here every version is pinned.

Measured: everything in the tables. Inferred: the sentences marked so, and the causes of the counts of `Raw`.
