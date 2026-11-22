# The CSS parser of the stylesheet graph

The proof that the stylesheet graph reads plain CSS through `@eslint/css-tree` 4.1.3 (the ESLint fork of CSSTree, MIT) and
not through the hand-written reader it had (`languages/stylesheet.py`, `_sheet` in `indexers/css.py`). Run on Modal on
2026-11-22. Nothing runs on the host: exact pins go into the image with `--ignore-scripts` and the corpus is read as data and
never executed. The runs on the corpus (`ab_run`, `measure_run`, `probe_run`) have `block_network=True`; `lock_check`,
`record_fixtures`, `cssinjs_run` and `lang_css.py`'s cases keep the network open, to install packages (always with
`--ignore-scripts`) or to fetch a checkout.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/css-parser/modal_css_parser.py::<entry>

| Entry | What it does | Output |
|---|---|---|
| `lock_check` | the lockfile npm writes for the pinned package, against the one in the tree | printed |
| `record_fixtures` | the engine runs of the graph's test fixtures, added to `tests/fixtures/css-graph/recorded/` | the recordings |
| `ab_run --out DIR` | the A/B of the graph's records on the corpus (below) | `DIR/ab-groups.json` (a copy is `results/ab-groups.json`) |
| `measure_run` | the values of the Sass, Less and Stylus trees, read two ways (below) | `results/values-other-dialects.json` |
| `cssinjs_run` | the graph of a styled-components project, its scripts' CSS read two ways | `results/cssinjs-ab.json` |
| `probe_run --script FILE` | a Node script beside the pinned engines and the corpus: `probes/reread_raw.mjs`, `probes/generic_family.mjs`, `probes/semicolon_raw.mjs` | printed |

`candidates/` is the choice of the parser: the same 197 inputs, comparator and corpus through css-tree, its fork, PostCSS,
Lightning CSS, tinycss2 and the old reader, re-run on Modal (`candidates/README.md`, with pins, dates and licences).

## What was chosen

| | |
|---|---|
| Parser | `@eslint/css-tree` 4.1.3 (released 2026-11-17, MIT; `mdn-data` 2.37.2, `source-map-js`), no install script |
| Runs like | the Sass engine: Daodan's pinned Node through `node_runner`, pinned in `daodan/core/indexers/css_engines/package.json` and its lockfile; `css_csstree.js` writes facts in the pass's neutral tree, `css.tree_records` reads them, the parser's own tree never leaves the script |
| Reads | `.css`, `.pcss`, `.postcss` files; the sheets from outside the snapshot (a package, a CDN sheet); the `<style>` blocks of HTML and EJS, and of Vue, Svelte and Astro components whose language is css; style attributes (`context: 'declarationList'`); the CSS text of scripts (styled-components, emotion) |
| Does not read | the values of Sass, Less and Stylus trees (measured below: it does not hold); the Sass, Less and Stylus sheets of packages (the hand reader, as before) |

## The candidates

Run 2026-11-22, `candidates/`: 197 inputs (155 with rule or declaration expectations written before any candidate ran) and
the 1,860-file corpus through one comparator; `candidates/README.md` has every table.

| Candidate | Pin | Released | Licence | Expectations met (of 155) | Why not chosen |
|---|---|---|---|---|---|
| `@eslint/css-tree` (chosen) | 4.1.3 | 2026-11-17 | MIT | 144 | its faults: below and in `candidates/README.md` (an at-rule it does not know keeps a Raw prelude; `&` after an at-rule inside a rule; the stack on deep nesting) |
| css-tree | 3.2.1 | 2026-03-05 | MIT | 125 | no relaxed nesting: 17 of 22 nesting inputs fail, 7,840 errors in 107 corpus files, 18,938 declarations fewer than PostCSS; spurious errors on valid `@import ... supports()` |
| PostCSS + `postcss-safe-parser` | 8.5.33 + 7.1.0 | 2026-11-13, 2026-09-04 | MIT | 138 | strings only (inferred: no grammar, no lexer, so the names of `animation`, `font`, `container` and every prelude need hand rules); the core throws on 18 inputs; 8 of 10 comments right |
| Lightning CSS | 1.33.0 | 2026-07-20 | MPL-2.0 | 136 | no selector, value or prelude text, no lines, no end positions, no comments; throws on 21 inputs; a native binary per platform |
| tinycss2 | 1.5.1 | 2025-11-23 | BSD | 136 | no end positions; Python, a second runtime beside the Node the other engines use (inferred: token lists, no selector grammar, no lexer) |
| the old reader | `stylesheet.py` | | the project's | 142 | what the engine replaces; the A/B below measures what it gets wrong |

## Choices that depart from the brief's rules

Each is measured both ways; the owner decides whether to keep it. The "with it" side re-runs from this folder; the "without
it" figures are development runs (the first A/B and the first engine run of this work), which the folder does not re-run:
`probes/reread_raw.mjs` (196 read again, 0 still Raw), `probes/semicolon_raw.mjs` (0 `;`-only Raw on the corpus).

| Choice | Without it | With it |
|---|---|---|
| A statement or a rule prelude the parser keeps as Raw *inside a block* is read again, whole, as the contents of a block, by the same parser | the first A/B: 196 holes on the corpus and, behind them, 348 rules, 463 references and 86 `animation` references the old reader had (daisyUI, Tailwind's `theme.css` and `index.css`) | 0 holes, those records are back; at the top level the Raw stays a hole |
| A value the lexer cannot match (it has a `var()`) is a hole only where an identifier or a string outside the `--x` of a `var()` could be a name | the first run of the engine on this corpus: 1,640 holes (1,443 `font-family`, 183 `animation`, 10 `font`, 4 others) | 243 (183 `animation`, 60 fonts); `font-family: var(--f)` alone is no hole, `var(--f, Arial)` is |
| A `Raw` that holds only `;` is not a hole | one hole per stray `;` (`a{;}`, a `;` after a block): 0 on this corpus, the unit and engine tests have it | none |
| An at-rule's label is the text as the source spells it (`@media(min-width: 1px)`) | the node ids of 5,278 rules and 5,380 references change (`@media (`), as the first A/B showed in primer | the ids are the old reader's: 0 nodes differ |
| `tree_records` is told the flatten mode: a sheet's nested selector list is `:is(h1, h2) a`, a script's CSS keeps the expanded list it had | the three respelled nodes of `cssinjs-ab.json` | the node ids of script CSS are the old ones |

## The lockfile

`lock_check`: `npm install --package-lock-only --ignore-scripts` on `package.json` with the lockfile of `f9440f8e9` (npm
10.9.9, in the image) writes a file **identical** to the one in the tree: what npm adds for the pin is `@eslint/css-tree`
4.1.3 (integrity `sha512-3WQJPt+K...`) and `mdn-data` 2.37.2. From no lockfile npm resolves newer patch versions of
`@babel/*` that have nothing to do with the pin, so that file is not the one to keep. `npm ci --ignore-scripts` of the
tree's lockfile is the image build of every run here.

## The A/B of the graph's records

**Parameters.** Corpus: the 30 packages of `candidates/corpus-packages.txt` at exact versions, installed one at a time;
1,860 `.css` files read, 74,578,563 bytes (1,864 found, 8 MB limit and unreadable files). Old side: `indexers/css.py` of
commit `f9440f8e9` (`git show`, `parse()`: the hand reader `_sheet` for every stylesheet) with this checkout's
`languages/stylesheet.py`, which this step does not touch. New side: `css.engine_sheets` with the engine, in chunks of about
3 MB over 4 processes. The records are the graph's input before it resolves anything (`node`, `ref`, `classes`, `hole`,
`file`: declared names, references with their line and fallback, imports, holes), compared one by one as JSON with empty
fields left out. A record of one side pairs with one of the other by the same line and the same thing it is about (a
name, a label), then by the line, then by the name; what does not pair is "only old" or "only new"; a pair that differs is
named by the fields that differ. Ground truth for `var()`, independent of both readers: `var_tokens.mjs` lists every
`var(` function token followed by a `--name` in the tokenizer of the fork (no parser, no tree), with its line and its
fallback (the tokens up to the parenthesis that closes it).

**Totals.**

| | nodes | references | holes | files read | files missing |
|---|---|---|---|---|---|
| old reader | 968,198 | 459,946 | 0 | 1,860 | 0 |
| engine | 968,198 | 463,057 | 264 | 1,860 | 0 |

Every node is the same, id and names and line: 0 pairs of nodes differ. The engine takes 38 to 48 s for the corpus (the
sum of the chunks' own time).

**Against the tokenizer** (449,958 uses of a custom property in the corpus):

| | uses found | missing | at another line | with another fallback | files exactly right, fallbacks included (of 1,860) |
|---|---|---|---|---|---|
| old reader | 446,614 | 3,669 | 325 | 4,681 | 1,416 |
| engine | 449,958 | 0 | 0 | 0 | 1,860 |

**Every difference, by class** (`results/ab-groups.json` has each group with examples; the counts are references or holes):

| Class | Count | Files | What | Demonstrated by |
|---|---|---|---|---|
| fixed: fallback cut | 4,543 | 427 | the old `VAR_RE` ends a fallback at the first `)`: `cubic-bezier(.28,.84,.42,1` | the old text is a prefix of the new with an unbalanced parenthesis |
| fixed: another fallback | 138 | 120 | in the examples the old reader blanks the strings: `var(--bs-breadcrumb-divider, "/")` has no fallback, `BlinkMacSystemFont, , , Helvetica` | the tokenizer's fallback is the engine's (4,543 + 138 = the 4,681 uses with another fallback above) |
| fixed: nested `var()` missed | 3,344 | 416 | `var(--a, var(--b, x))`: the old regex consumed the inner use | the tokenizer holds them, the old reader lacks them (3,669 missing = these and the next) |
| fixed: wrong line | 325 | 16 | a use on the line after the property's: the old reader counts from the stripped value | the tokenizer's line; the old line does not hold the use, the new does |
| fixed: not a family | 155 | 36 | `-apple-system` 80 and `BlinkMacSystemFont` 75 as references to an `@font-face` | the lexer matches both as `<generic-family>` (with `system-ui`), measured by `probes/generic_family.mjs` |
| new hole: `value-not-matched`, keyframes | 183 | 114 | `animation:` with a `var()` and a word that could be a name: the lexer does not match it | 74 of them are references the old reader found (5 files, daisyUI) |
| new hole: `value-not-matched`, fonts | 60 | 22 | the same for `font` and `font-family`, and Tailwind's `--theme(...)` | 4 of them are references the old reader found (`--theme(...)` read as family names) |
| new hole: `unparsed`, declaration | 21 | 13 | `--bs-table-hover-color: $white`, an uncompiled Sass variable in a CSS file (bootswatch) | the parser keeps the value as Raw |
| regressions without a hole, in the `.css` files of this corpus | 0 | 0 | | |

The 78 references lost (74 keyframes, 4 fonts) each sit at a line with a hole that says why. The other differences are all
gains; the engine finds 3,111 references more than the old reader and is right on every use of the tokenizer.

**What the parser keeps as Raw.** Without a second read, 194 statements and 2 rule preludes of the corpus are Raw (the fork
loses a rule that starts with `&` inside an at-rule inside a rule: 192 in daisyUI; and, in Tailwind's own `theme.css` and
`index.css`, the declarations before a nested `@keyframes` in `@theme default {}` become the prelude of a rule). Inside a
block the engine reads the text of such a statement again, whole, with the same parser as the contents of a block
(`x{...}` with the positions of the source): all 196 read cleanly (`probes/reread_raw.mjs`: 196 read, 0 still Raw; packages
daisyui 192, tailwindcss 4). At the top level a prelude that is not a selector is an invalid rule (CSS Syntax) and stays a
hole with its block read. A `Raw` that holds only `;` is nothing. A `Raw` value is a hole and the declaration stays
(`--x: $white`, an empty `--x:;` is no hole).

**Fixtures and tests that keep this.** `tests/test_codebase_map_css_csstree.py` (the tree to records: pure; the engine
itself on Modal: newline forms and lines, UTF-16 offsets after astral characters, at-rule text by the `Atrule` slice,
parse errors on a right tree, a sheet that cannot be read costs only itself, depth, Raw forms, the second read,
lexer holes, exact-text at-rules, style attributes), `tests/test_codebase_map_css_graph.py` (the `css-plain` fixture and
the others, replayed from the runs recorded here; the host-marks test now holds `a.css` with `@config`, `@plugin` and
`@import` of files that would leave a mark and a `.pcss`).

## Other feeders

**Style blocks and style attributes** go through the same run (the markup's `<style>` texts and attributes are items of
the one call). `lang_css.py`'s cases, run here with the working tree's code and, for the same day, with the code of
`f9440f8e9` (see the table below), hand check included:

| Case | Files | Hand check | Nodes | Arcs | Holes |
|---|---|---|---|---|---|
| tududi | 1,708 | 20/20 -> 20/20 | 2,672 -> 2,669 | 39,629 -> 39,626 | 350 -> 351 |
| bulma | 602 | 7/11 -> 7/11 | 109,307 -> 109,307 | 8,860,896 -> 8,862,180 | 7,773 -> 7,800 |
| bootstrap3 | 282 | 15/15 -> 15/15 | 4,218 -> 4,218 | 147,232 -> 147,232 | 1,577 -> 1,643 |
| hn-svelte | 20 | 16/16 -> 16/16 | 81 -> 81 | 73 -> 73 | 17 -> 15 |
| v3-admin-vite | 131 | 15/15 -> 15/15 | 624 -> 624 | 952 -> 952 | 21 -> 36 |
| saas-starter | 43 | 15/15 -> 15/15 | 560 -> 560 | 1,310 -> 1,311 | 39 -> 42 |
| sc-website | 139 | 12/15 -> 12/15 | 582 -> 580 | 111 -> 115 | 200 -> 250 |

Old code on the left, the working tree's on the right, both run on 2026-11-22. The committed `benchmarks/inference-audit/results/`
are older runs of other code and are not a baseline. Every difference there is, by case:

- **tududi.** -3 rules and -3 class arcs, **regressions with a hole**: three rules of `styles.ejs` sit behind an EJS tag
  (`<%# ... %> .agent-row`, `<%# .nav-dd-menu needs no rule here ... %> [dir="rtl"] .setup-pre`): 3 `rule unparsed` holes and
  1 `statement unparsed`. Inferred, not checked node by node: the old nodes had the template's text in their selectors (and
  may have named `.nav-dd-menu` from inside the comment); nothing shows whether the old answer was right for the other two. Template tags in a style text are not
  CSS and the engine does not blank them. -4 `no-font-face` holes (system font keywords, inferred from the corpus A/B). +1
  `value-not-matched` (Font Awesome's `font-family` with `var()`).
- **bulma.** +1,290 `custom-property` arcs and -2 `undeclared` holes (inferred: the nested `var()` the old reader missed, as
  in the corpus A/B);
  -6 `keyframes` arcs, with the 4 `value-not-matched` holes at their lines; +24 `unparsed` declarations and +1 statement,
  Liquid tags in the docs' style attributes (`--height: {{ include.height }}`, `{% if page.doc-tab == ... %}`): the
  declaration stays declared, what it holds is a hole.
- **bootstrap3.** +66 `unparsed` declarations: `filter: progid:DXImageTransform...`, which the parser keeps as Raw.
- **hn-svelte.** -2 `no-font-face` (inferred: system font keywords).
- **v3-admin-vite.** +1 `unparsed` (`filter: alpha(opacity=0)`) and +14 `value-not-matched` for `animation` with `var()`
  in Element Plus's `index.css`.
- **saas-starter.** +1 `variant` arc (not examined); +1 `unparsed` statement (`tw-animate-css`, its text is keyframe
  percentages: `0%,70%,100% { opacity: 1; }20%,50% { opacity: 0; }`); +2 `value-not-matched` (Tailwind's `--theme(...)`).
- **sc-website** (CSS-in-JS, no committed baseline): -2 rules, +4 arcs, +50 `unparsed` statements, +2 `unparsed` rules, +2
  `value-not-matched`, -3 `no-keyframes`, -1 `interpolated-selector`: the same as the CSS-in-JS section below.

The hand checks do not change. Time: the same tree took 21.9 and 38.2 s of graph on tududi in two runs (the machine was not
quiet), so no difference in time is claimed; the engine's own time on the corpus is 38 to 48 s for 74.6 MB. Each sheet
from outside the snapshot is a Node run of its own (not batched); on tududi that is part of the engine's seconds.

**The values of Sass, Less and Stylus trees** (sub-step 3): 922 `.scss`, 147 `.less` and 19 `.styl` files of the corpus
through their engines (3 `.scss` not read), every declaration's value read by the code of `declaration` as it is and by
`parse(value, {context: 'value'})` with the lexer (`value_facts.cjs`, through the engine's own `declFacts`);
`results/values-other-dialects.json`.

| | declarations | same | same, and a hole (the parser throws: `$x`, `#{}`, `@x`) | the fork reads more | the fork loses, a hole says so |
|---|---|---|---|---|---|
| Sass | 22,827 | 15,771 (69.1%) | 6,599 (28.9%) | 359 (1.6%) | 98 (0.4%) |
| Less | 3,108 | 1,528 (49.2%) | 1,571 (50.5%) | 0 | 9 (0.3%) |
| Stylus | 798 | 696 (87.2%) | 101 (12.7%) | 0 | 1 |

It does not hold, and no value of those trees goes through the fork: the parser *throws* on a value with a variable or an
interpolation, 29%, 51% and 13% of the values, where the regular expressions read nothing and say nothing; switching
would make about 8,300 silent values into holes and lose the names of 108 values (`var(--#{$p}-family)`, `fpFadeInDown
300ms $bezier`) for 359 values gained (the nested `var()` again). The better source for Sass is the Sass parser itself,
which has the function calls as nodes: not measured here.

**The CSS text of scripts** (sub-step 4): styled-components' own website at commit `e70dc5c3f`, 139 files, 280 CSS texts
(`cssinjs_run`: the graph twice, the text read by the engine and by the hand reader as scss):

| | nodes | arcs | holes |
|---|---|---|---|
| hand reader | 581 | 110 | 200 |
| engine | 579 | 114 | 250 |

What differs, every site in a script file (`results/cssinjs-ab.json`; the node ids are the same: the mode of `tree_records`
for script CSS is scss):

- **2 rules lost, each with a hole** (regressions): `components/CodeBlock.tsx:44 __dd6__ &` and
  `components/UsersLogos/index.tsx:63 & svg`. Each follows a `${mixin}` on a line of its own with no `;`: the parser takes
  everything up to the next `{` for one prelude (a `rule unparsed` hole at `CodeBlock.tsx:30` and `UsersLogos/index.tsx:59`
  names it). The hand reader let such a line go.
- **4 arcs gained**: `CelebrationEffect.tsx:253-254`, the uses of `--angle`, `--progress` and `--speed`.
- **Holes**: +50 `statement unparsed` (a statement that is an interpolation, ``${mobile(css`...`)}``, `${rowDisplay}`: the hand
  reader let them go silently, the engine declares them), +2 `rule unparsed`, +2 `keyframes value-not-matched`; -3
  `keyframes no-keyframes` (`__dd0__`, a placeholder the hand reader took for a keyframes name) and -1
  `interpolated-selector`.
- One engine run reads the 280 texts (0.3 s); the sheets and markup of the project take another (0.24 s).

It is kept, because the fork reads 579 of the 581 rules and finds arcs the hand reader did not; the 2 rules and the 50
holes are the cost, and the block to take out is the `texts` and `read_texts` part of `graph()` and the `cssinjs-text`
branch that reads them.

## What is measured and what is inferred

Measured: every number above. Inferred: that the 3,344 missing nested uses are all inner `var()` of a fallback (the
tokenizer says they are missing and the examples are nested; not every one was read); that the engine's two missing rules
in the scripts' CSS come from the `${mixin}` statement without a `;` (the two holes say the rule's prelude begins with it);
that the 3 rules lost in `styles.ejs` are all behind an EJS tag (the holes' texts show it). Not measured: the cost of the
engine's one run per sheet from outside the snapshot (they are not batched).

The hand reader stays for the Sass, Less and Stylus sheets of packages and for the values of those trees; the 60 regular
expressions of `css.py` are 59: the one gone is `EJS_RE`, which was already unused, the change removed none of its own.
