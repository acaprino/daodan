<!-- Recorded 2026-11-22 from the probe's three result files, classified by hand (one reason per row). Not re-run by modal_candidates.py: the other tables here are. Column 5 is the fork on the same input. -->

# Part A, per input (css-tree 3.2.1, positions: true). Counts: as expected 132, difference 38, failed 27; total 197

| batch | input | result | detail | @eslint/css-tree 4.1.3 on the same input |
|---|---|---|---|---|
| batch 1 | g1-import-supports-selector | difference | tree right (one String base.css; supports -> FeatureFunction selector holding the attribute string) but 1 onParseError "Unexpected input" on valid CSS | same input: no error, expectations met |
| batch 1 | g1-font-700-1rem-inter | as expected |  | same input: no error, expectations met |
| batch 1 | g1-font-bold-calc | as expected |  | same input: no error, expectations met |
| batch 1 | g1-attr-string-when | as expected |  | same input: no error, expectations met |
| batch 1 | g1-attr-string-custom-selector | as expected |  | same input: no error, expectations met |
| batch 1 | g1-var-uppercase | as expected |  | same input: no error, expectations met |
| batch 1 | g1-scope-limit | as expected |  | same input: no error, expectations met |
| batch 1 | g1-value-parens-from | as expected |  | same input: no error, expectations met |
| batch 1 | g1-source-not-inline | as expected |  | same input: no error, expectations met |
| batch 1 | g1-string-dollar | as expected |  | same input: no error, expectations met |
| batch 1 | g1-comment-then-rule | as expected |  | same input: no error, expectations met |
| batch 1 | g1-import-supports-layer-word | difference | tree right (`.layer` is a selector inside supports(), no Layer node) but 1 spurious onParseError | same input: no error, expectations met |
| batch 1 | g1-import-scheme-underscore | as expected |  | same input: no error, expectations met |
| batch 1 | g1-vue-vbind-comment | as expected |  | same input: no error, expectations met |
| batch 1 | g1-emoji-class | as expected |  | same input: no error, expectations met |
| batch 1 | g2-container-named | as expected |  | same input: no error, expectations met |
| batch 1 | g2-layer-dotted-statement | as expected |  | same input: no error, expectations met |
| batch 1 | g2-layer-list-statement | as expected |  | same input: no error, expectations met |
| batch 1 | g2-layer-block | as expected |  | same input: no error, expectations met |
| batch 1 | g2-layer-anonymous-block | as expected |  | same input: no error, expectations met |
| batch 1 | g2-import-url-layer-supports-media | as expected |  | same input: no error, expectations met |
| batch 1 | g2-import-layer-bare | as expected |  | same input: no error, expectations met |
| batch 1 | g2-import-url-unquoted | as expected |  | same input: no error, expectations met |
| batch 1 | g2-import-two-strings-comment | as expected |  | same input: no error, expectations met |
| batch 1 | g2-custom-media | difference | prelude is Raw ("--narrow (max-width: 30em)") + 1 onParseError; text exact | errors 1; PASS |
| batch 1 | g2-custom-selector | difference | prelude is Raw (":--heading h1, h2") + 1 onParseError; text exact | errors 1; PASS |
| batch 1 | g2-value-define | difference | prelude is Raw ("primary: #BF4040") + 1 onParseError; text exact | errors 1; PASS |
| batch 1 | g2-value-from | as expected |  | same input: no error, expectations met |
| batch 1 | g2-tw-source | as expected |  | same input: no error, expectations met |
| batch 1 | g2-tw-apply | as expected |  | same input: no error, expectations met |
| batch 1 | g2-tw-apply-variant-important | difference | @apply prelude with variant colons is Raw + 1 onParseError; text exact, `!important` inside it | errors 1; PASS |
| batch 1 | g2-tw-theme | as expected | custom property values are Raw by default (text exact); parsed Value only with parseCustomProperty: true | same input: no error, expectations met |
| batch 1 | g2-tw-utility | as expected |  | same input: no error, expectations met |
| batch 1 | g2-tw-import-tailwindcss | as expected |  | same input: no error, expectations met |
| batch 1 | g2-property | as expected |  | same input: no error, expectations met |
| batch 1 | g2-font-face | as expected |  | same input: no error, expectations met |
| batch 1 | g2-keyframes | as expected |  | same input: no error, expectations met |
| batch 1 | g2-keyframes-webkit | as expected |  | same input: no error, expectations met |
| batch 1 | g2-supports | difference | `(not (display: inline-grid))` valid but onParseError "Colon is expected"; AtrulePrelude.loc ends one char early (last `)` missing); the Atrule loc is right | same input: no error, expectations met |
| batch 1 | g2-media-range | as expected |  | same input: no error, expectations met |
| batch 1 | g2-media-custom | as expected |  | same input: no error, expectations met |
| batch 1 | g2-scope | as expected |  | same input: no error, expectations met |
| batch 1 | g2-starting-style | as expected |  | same input: no error, expectations met |
| batch 1 | g2-namespace | as expected |  | same input: no error, expectations met |
| batch 1 | g2-page | as expected |  | same input: no error, expectations met |
| batch 1 | g2-unknown | difference | unknown at-rule: prelude "1 2" (Number nodes), its block is read as declarations (`a: b`, expected none); next rule intact | errors 0; DIFF (decls: expected 1 [y], got 2 [a y]) |
| batch 1 | g2-charset-counter-style | as expected |  | same input: no error, expectations met |
| batch 1 | g2-media-nested-in-rule | as expected |  | same input: no error, expectations met |
| batch 1 | g2-layer-nested-in-media | as expected |  | same input: no error, expectations met |
| batch 1 | g3-nesting-amp | failed | `& .b` is a Rule, then `.c {..} &:hover {..} .d & {..} > .e {..}` is ONE Raw node to the end of the block + onParseError "Identifier is expected": 4 nested rules and 4 declarations lost | errors 0; DIFF |
| batch 1 | g3-nesting-amp-suffix | as expected |  | errors 1; DIFF (rules: expected 3 [.a \| &-b \| & + &], got 1 [.a]) |
| batch 1 | g3-pseudo-functions | as expected | :is/:where/:not/:has parsed as selector lists; Combinator nodes have loc null | errors 0; DIFF |
| batch 1 | g3-nth-of | as expected |  | same input: no error, expectations met |
| batch 1 | g3-shadow-dom | as expected |  | same input: no error, expectations met |
| batch 1 | g3-attr-strings | as expected |  | same input: no error, expectations met |
| batch 1 | g3-escaped-classes | as expected |  | same input: no error, expectations met |
| batch 1 | g3-namespaces | as expected |  | same input: no error, expectations met |
| batch 1 | g3-combinators-multiline | as expected |  | same input: no error, expectations met |
| batch 1 | g3-pseudo-elements | as expected |  | same input: no error, expectations met |
| batch 1 | g3-vue-svelte-modes | difference | :global()/:local()/:deep()/::v-deep() arguments are Raw text, not selectors; `>>>` is three `>` Combinators, `/deep/` a Combinator named "/deep/"; Combinator loc null | errors 0; DIFF |
| batch 1 | g3-keyframe-percent-selectors | as expected |  | same input: no error, expectations met |
| batch 1 | g4-url-forms | difference | unquoted url(data:..<svg xmlns='..'>..) -> declaration value Raw + 1 onParseError (invalid per spec: quotes in an unquoted url); text and loc exact; quoted/unquoted plain url() -> Url node, value decoded ("a b.png") | errors 1; PASS |
| batch 1 | g4-image-set | as expected |  | same input: no error, expectations met |
| batch 1 | g4-var-fallback | as expected |  | same input: no error, expectations met |
| batch 1 | g4-custom-property-json | as expected | values Raw by default, text exact (`{ "a": 1 }`, `{a:b}`, `[1, 2]`, empty); with parseCustomProperty: true `{..}` values stay Raw and add 2 onParseError | same input: no error, expectations met |
| batch 1 | g4-custom-property-semicolon-braces | as expected | values Raw by default, `;` inside string/url()/braces/parens does not end the declaration | same input: no error, expectations met |
| batch 1 | g4-composes | as expected |  | same input: no error, expectations met |
| batch 1 | g4-animation-container | as expected |  | same input: no error, expectations met |
| batch 1 | g4-unicode-range | as expected |  | same input: no error, expectations met |
| batch 1 | g4-important-forms | as expected | `important` is true only for lowercase `!important`; `!IMPORTANT` gives the string "IMPORTANT" and `!ie` the string "ie" (both truthy) | same input: no error, expectations met |
| batch 1 | g4-ie-hacks | difference | `filter: progid:...` value Raw + 1 onParseError (dropped by modern browsers too); `*zoom`, `_height`, `red\9`, `expression(...)` read | errors 1; PASS |
| batch 1 | g4-numbers-units | as expected |  | same input: no error, expectations met |
| batch 1 | g4-grid-areas-multiline | as expected |  | same input: no error, expectations met |
| batch 1 | g4-vendor-and-empty | as expected | stray `;` appear as Raw ";" nodes inside the block, no error | same input: no error, expectations met |
| batch 1 | g4-case-property | as expected | property as written (COLOR, Background-Color); the caller lowercases | same input: no error, expectations met |
| batch 1 | g5-comment-in-selector | as expected | AST and generate() skip the comment; the Rule prelude loc slice includes it | errors 0; DIFF |
| batch 1 | g5-comment-in-value | difference | value loc slice keeps comments ("red /* d */", "1px/* e */2px"); clean text only by generate() ("red", "1px 2px") or by cutting the onComment ranges | same input: no error, expectations met |
| batch 1 | g5-comment-before-colon | as expected |  | same input: no error, expectations met |
| batch 1 | g5-comment-multiline-lines | as expected |  | same input: no error, expectations met |
| batch 1 | g5-comment-star-in-string | as expected |  | same input: no error, expectations met |
| batch 1 | g5-comment-bang-and-empty | as expected |  | same input: no error, expectations met |
| batch 1 | g5-comment-unclosed | as expected |  | same input: no error, expectations met |
| batch 1 | g5-unclosed-block-eof | as expected |  | same input: no error, expectations met |
| batch 1 | g5-unclosed-nested-eof | as expected |  | same input: no error, expectations met |
| batch 1 | g5-unclosed-string | difference | as a browser: `content` kept as a declaration with Raw value "\"abc; color: red" + onParseError (swallows `color: red`); `.b` intact | errors 1; DIFF (decls: expected 1 [x], got 2 [content x]) |
| batch 1 | g5-unclosed-string-eof | as expected |  | same input: no error, expectations met |
| batch 1 | g5-stray-close-brace | difference | as spec: `} .b` is one rule with Raw prelude + onParseError; its declarations are still parsed | errors 1; DIFF (rules: expected 1 [a], got 2 [a \| }
.b]) |
| batch 1 | g5-stray-close-brace-end | as expected | Raw "}" node + 2 onParseError, no throw | errors 2; PASS |
| batch 1 | g5-extra-close-in-block | difference | second `}` joins the next prelude (Raw "} b") + onParseError | errors 1; NO-EXPECT |
| batch 1 | g5-semicolon-stray-top | difference | as spec: `;;; a` is a Raw prelude rule + onParseError; the block is parsed | errors 3; DIFF (rules: expected 0 [], got 1 [;;; a] \| decls: expected 0 [], got 1 [x]) |
| batch 1 | g5-bom | difference | offsets point into the string as given (BOM = offset 0) but columns on line 1 do not count it (17 positions); lines right | errors 0; DIFF |
| batch 1 | g5-crlf | as expected |  | same input: no error, expectations met |
| batch 1 | g5-lone-cr | as expected |  | same input: no error, expectations met |
| batch 1 | g5-formfeed | as expected |  | same input: no error, expectations met |
| batch 1 | g5-empty | as expected |  | same input: no error, expectations met |
| batch 1 | g5-only-whitespace-comment | as expected |  | same input: no error, expectations met |
| batch 1 | g5-cdo-cdc | as expected |  | same input: no error, expectations met |
| batch 1 | g5-slash-slash | as expected | `// not a comment color: red;` is a Raw statement + onParseError (a browser drops it too); `.b` intact | errors 1; PASS |
| batch 1 | g5-slash-slash-selector | difference | as spec: `// c .a` is a Raw prelude rule + onParseError | errors 1; DIFF (rules: expected 1 [.b], got 2 [// c
.a \| .b] \| decls: expected 1 [z], got 2 [x z]) |
| batch 1 | g5-nul-and-control | difference | NUL in a value: Raw value + onParseError (the spec replaces NUL by U+FFFD: valid ident); edge | errors 1; NO-EXPECT |
| batch 1 | g5-astral-offsets | as expected |  | same input: no error, expectations met |
| batch 1 | g5-tab-columns | as expected |  | same input: no error, expectations met |
| batch 1 | g5-no-final-newline-rule | as expected |  | same input: no error, expectations met |
| batch 1 | g5-missing-semicolon-then-prop | difference | `x: y z: w` one declaration with Raw value + onParseError; `q: r` kept (my expected end line was wrong: the rule ends on line 2) | errors 1; DIFF (rule 0 endLine: expected 3, got 2) |
| batch 1 | g5-decl-without-colon | as expected | `foo;` and `baz` are Raw statements + 2 onParseError; `bar: 1` kept | errors 2; PASS |
| batch 1 | g5-bad-selector-rule | difference | as spec: `a!b` is a rule with Raw prelude + onParseError; the block is parsed | errors 1; DIFF (rules: expected 1 [.c], got 2 [a!b \| .c] \| decls: expected 1 [z], got 2 [x z]) |
| batch 1 | g6-scss | failed | not CSS: 9 onParseError; `$x: 1; .a {..}` is one Raw-prelude rule that swallows `.a` and all its nested content; `// line comment @use .. @mixin ..` another; nested properties become a Raw value; `.#{$i}` Raw; only `.z` and `@mixin`'s `c: d` survive; no throw | errors 10; NO-EXPECT |
| batch 1 | g6-scss-line-comment-only | failed | not CSS: `// a comment with a { brace` opens a Raw-prelude rule and the real `.a { x: y }` is lost; 2 onParseError | errors 1; DIFF (rules: expected 1 [.a], got 2 [// a comment with a \| brace .a]) |
| batch 1 | g6-less | failed | not CSS: 10 onParseError; `.m(); .a when (@x)` one Raw prelude, mixin definitions Raw prelude, `@x: 1` at-rule x with Raw prelude ": 1", `&:extend(..); e: @@x` Raw; no throw | errors 9; NO-EXPECT |
| batch 1 | g6-postcss-mixins | difference | not CSS but mostly readable: @define-mixin/@each/@for preludes Raw + 7 onParseError, their blocks parsed; `.icon-$(name)` rules Raw prelude; `@mixin icon search` at-rule with identifiers | errors 7; NO-EXPECT |
| batch 1 | g6-postcss-nested-simple-vars | failed | not CSS: `$dir: top; $blue: ..; .menu_link` is one Raw-prelude rule; `border-$(dir): ..` Raw; 3 onParseError | errors 3; NO-EXPECT |
| batch 1 | g6-stylus | failed | not CSS: the whole file is one Raw node, 2 onParseError | errors 2; NO-EXPECT |
| batch 1 | g6-sass-indented | failed | not CSS: the whole file is one Raw node, 2 onParseError | errors 2; NO-EXPECT |
| batch 1 | g6-html-style-wrapper | difference | not CSS: `<style> .a` becomes a Raw prelude (block parsed), `</style>` a Raw node, 3 onParseError | errors 3; NO-EXPECT |
| batch 2 | n01-nested-class-first | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n02-nested-class-after-decl | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n03-decl-after-nested-class | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n04-nested-type | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n05-nested-child-combinator | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n06-nested-sibling-combinators | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n07-nested-pseudo-class | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n08-nested-id | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n09-nested-attr | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n10-nested-universal | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n11-amp-hover-then-dot-amp | failed | `&:hover {..}` is a Rule, `.b & {..}` is lost in a Raw node + onParseError | errors 0; DIFF |
| batch 2 | n12-amp-deep | as expected | `&`-led nested rules at every level; Combinator loc null | errors 0; DIFF |
| batch 2 | n13-media-in-rule-with-amp | as expected | @media inside a rule: block read as declarations and `& .b` rule; Combinator loc null | errors 0; DIFF |
| batch 2 | n14-nested-is | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n15-amp-compound-and-child | as expected |  | same input: no error, expectations met |
| batch 2 | n16-amp-alone | as expected |  | same input: no error, expectations met |
| batch 2 | n17-nested-list | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n18-typical-card | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n19-nested-in-layer | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n20-top-level-amp | as expected | `& .a` at top level read as a rule; Combinator loc null | errors 0; DIFF |
| batch 2 | n21-nested-class-multiline | failed | relaxed nesting (a nested rule not starting with `&`): the rule and everything after it in the block is ONE Raw node + 1 onParseError; its rules/declarations lost | same input: no error, expectations met |
| batch 2 | n22-nested-at-container-and-layer | failed | @container {color} inside a rule is read; `@layer x { color: blue }` inside a rule: its block is read as rules, `color: blue` is a Raw node + 2 onParseError (declaration lost) | same input: no error, expectations met |
| batch 2 | s01-supports-not | as expected |  | same input: no error, expectations met |
| batch 2 | s02-supports-not-nested | difference | valid `(not (display: inline-grid))`: onParseError "Colon is expected"; prelude loc drops the outer parenthesis | same input: no error, expectations met |
| batch 2 | s03-supports-paren-not | difference | valid `(not (display: grid))`: onParseError "Colon is expected"; prelude loc drops the outer parentheses | same input: no error, expectations met |
| batch 2 | s04-supports-or | as expected |  | same input: no error, expectations met |
| batch 2 | s05-supports-grouped | difference | valid `((a: b) and (c: d))`: onParseError "Identifier is expected"; prelude loc drops the outer parentheses | same input: no error, expectations met |
| batch 2 | s06-supports-not-selector | as expected |  | same input: no error, expectations met |
| batch 2 | s07-supports-selector-combinator | as expected |  | same input: no error, expectations met |
| batch 2 | s08-supports-font-tech | difference | valid `font-tech(color-COLRv1)`: onParseError "Unknown feature font-tech()", node GeneralEnclosed | same input: no error, expectations met |
| batch 2 | s09-import-supports-not | difference | tree right, 1 spurious onParseError on `supports(not (..))` | same input: no error, expectations met |
| batch 2 | s10-import-supports-selector-simple | difference | tree right, 1 spurious onParseError on `supports(selector(..))` | same input: no error, expectations met |
| batch 2 | s11-container-and | as expected |  | same input: no error, expectations met |
| batch 2 | s12-container-style | as expected |  | same input: no error, expectations met |
| batch 2 | s13-container-not | as expected |  | same input: no error, expectations met |
| batch 2 | s14-container-named-style | as expected |  | same input: no error, expectations met |
| batch 2 | s15-media-not | as expected |  | same input: no error, expectations met |
| batch 2 | s16-media-only-calc | as expected |  | same input: no error, expectations met |
| batch 2 | s17-layer-nested-and-list | as expected |  | same input: no error, expectations met |
| batch 2 | s18-escaped-at-keyword | difference | at-rule name is "\\69 mport" (escape not decoded); prelude right | errors 0; DIFF (atrule 0 name: expected "import", got "\\69 mport") |
| batch 2 | s19-uppercase-at-rule | as expected | names as written ("IMPORT", "MEDIA"); the caller lowercases | same input: no error, expectations met |
| batch 2 | s20-important-escaped | as expected |  | same input: no error, expectations met |
| batch 2 | s21-import-in-media | as expected |  | same input: no error, expectations met |
| batch 2 | t01-custom-variant-short | difference | @custom-variant with a parenthesised selector: Raw prelude + 1 onParseError; text exact | errors 1; PASS |
| batch 2 | t02-custom-variant-block | as expected | @custom-variant block with nested `&:where(..)` rule and `@slot;`; Combinator loc null | errors 0; DIFF |
| batch 2 | t03-variant | as expected |  | same input: no error, expectations met |
| batch 2 | t04-plugin-config-reference | as expected |  | same input: no error, expectations met |
| batch 2 | t05-theme-inline | difference | `--color-*: initial;` is a Raw statement + onParseError (declaration lost), the two other custom properties read (Raw values) | errors 1; DIFF (errors: expected 0, got 1 \| decls: expected 3 [--font-sans --color-* --animate-x], got 2 [) |
| batch 2 | t06-source-inline-and-not | as expected |  | same input: no error, expectations met |
| batch 2 | t07-utility-wildcard | difference | @utility tab-* prelude is Identifier "tab-" + Operator "*": the name needs the source text | same input: no error, expectations met |
| batch 2 | t08-layer-utilities-apply | as expected |  | same input: no error, expectations met |
| batch 2 | t09-apply-variants | difference | @apply with variants (`hover:bg-..`): Raw prelude + 1 onParseError; text exact | errors 1; DIFF (errors: expected 0, got 1) |
| batch 2 | t10-apply-arbitrary | difference | @apply with `w-[calc(100%-1rem)] [&>*]:p-2`: Raw prelude + 1 onParseError; text exact | errors 1; DIFF (errors: expected 0, got 1) |
| batch 2 | t11-theme-functions | as expected |  | same input: no error, expectations met |
| batch 2 | t12-import-layer-theme | difference | `@import .. layer(utilities) source(none)`: Raw prelude + 1 onParseError (the `layer(theme)` one is parsed) | errors 1; DIFF (errors: expected 0, got 1) |
| batch 2 | t13-property-fallback | as expected |  | same input: no error, expectations met |
| batch 2 | m01-export | as expected |  | same input: no error, expectations met |
| batch 2 | m02-import | as expected |  | same input: no error, expectations met |
| batch 2 | m03-value-as-from | difference | `@value small: (max-width: 599px)` Raw prelude + 1 onParseError; the `a as b from "x"` form parsed as identifiers | errors 1; PASS |
| batch 2 | m04-local-global-composes | as expected | :global(.g) / :local read; Combinator loc null; arguments of :global() are Raw | errors 0; DIFF |
| batch 2 | v01-data-url-unquoted-valid | as expected |  | same input: no error, expectations met |
| batch 2 | v02-url-fragment | as expected |  | same input: no error, expectations met |
| batch 2 | v03-slash-values | as expected |  | same input: no error, expectations met |
| batch 2 | v04-math-functions | as expected |  | same input: no error, expectations met |
| batch 2 | v05-modern-color | as expected |  | same input: no error, expectations met |
| batch 2 | v06-font-shorthands | as expected |  | same input: no error, expectations met |
| batch 2 | v07-font-family-list | as expected |  | same input: no error, expectations met |
| batch 2 | v08-animation-list | as expected |  | same input: no error, expectations met |
| batch 2 | v09-escaped-strings | as expected |  | same input: no error, expectations met |
| batch 2 | v10-minified | as expected |  | same input: no error, expectations met |
| batch 2 | v11-whitespace-before-colon-and-newline-value | as expected |  | same input: no error, expectations met |
| batch 3 | c01-custom-selector-use | as expected | `:--heading` is a PseudoClassSelector named "--heading" | errors 0; DIFF |
| batch 3 | c02-layer-in-rule-dotted | failed | daisyUI form `.a{@layer x.y{color:..;--a:1}}`: declarations inside the nested @layer are Raw statements + 4 onParseError (all lost) | same input: no error, expectations met |
| batch 3 | c03-layer-in-rule-spaced | failed | `@layer x { color: red }` inside a rule: declaration lost as Raw + 2 onParseError | same input: no error, expectations met |
| batch 3 | c04-supports-in-rule | as expected |  | same input: no error, expectations met |
| batch 3 | c05-scope-in-rule | as expected |  | same input: no error, expectations met |
| batch 3 | c06-container-in-rule-amp | as expected | @container inside a rule containing an `&` rule: read; Combinator loc null | errors 1; DIFF (errors: expected 0, got 1 \| rules: expected 2 [.a \| & .b], got 1 [.a] \| decls: expected 1 ) |
| batch 3 | c07-span-slash | as expected |  | same input: no error, expectations met |
| batch 3 | c08-custom-media-complex | difference | 3 x @custom-media: Raw prelude + onParseError each; text exact | errors 3; PASS |
| batch 3 | c09-amp-suffix-sass-leftover | as expected | `button& {..}` (invalid CSS) kept leniently as a Rule | errors 0; DIFF (rules: expected 1 [.a], got 2 [button& \| .a]) |
| batch 3 | c10-media-in-rule-decls-after-nested | as expected |  | same input: no error, expectations met |
| batch 3 | c11-declarations-after-amp-rule | as expected | declarations between and after `&` rules all read; Combinator loc null | errors 0; DIFF |
| batch 3 | c12-nested-two-levels-class | failed | `.a { .b { .c {..} } }`: `.b {..}` is a Raw node + onParseError: 2 rules and the declaration lost | same input: no error, expectations met |
