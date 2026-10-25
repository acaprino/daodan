# Integrity rules

`office_verify.py` applies these static rules. Each finding has a severity and a
fix class. Rules read the saved package only; nothing is rendered, recalculated or
validated against the OOXML schema.

| Severity | Meaning |
|---|---|
| `error` | The file is broken or shows a wrong result: blocks delivery |
| `warning` | A defect a reader or later editor will meet: fix or justify |
| `info` | Worth a look; often intentional |

| Fix class | What `fix` may do |
|---|---|
| `safe` | Apply mechanically through the engine; the content's meaning cannot change |
| `content` | Write new content that only describes what is already there (alternative text, a slide title taken from the slide's own heading) |
| `review` | Report with a proposed change; apply only when the user's request authorizes that specific change |
| `none` | Report only |

## All formats

| Rule | Severity | Fix | Detects |
|---|---|---|---|
| `package.invalid` | error | none | Unreadable, unsafe or structurally broken package (inspector errors) |
| `package.external-link` | warning | review | Content that depends on a target outside the file (hyperlinks excluded) |
| `package.macros` | info | none | Macros present; never run |

## Word

| Rule | Severity | Fix | Detects |
|---|---|---|---|
| `docx.broken-anchor` | error | review | Internal link to a bookmark that does not exist |
| `docx.alt-text-missing` | warning | content | Image without alternative text and not marked decorative |
| `docx.heading-skip` | warning | review | Heading level that skips a level (2 after none, 4 after 2) |
| `docx.tracked-changes` | warning | review | Unresolved tracked changes in a story |
| `docx.comments` | info | review | Comments left in the document |
| `docx.empty-paragraph-spacing` | info | review | Three or more consecutive empty body paragraphs used as spacing |

## PowerPoint

| Rule | Severity | Fix | Detects |
|---|---|---|---|
| `pptx.alt-text-missing` | warning | content | Picture without alternative text and not marked decorative |
| `pptx.empty-placeholder` | warning | safe | Placeholder with no content, which shows prompt text while editing |
| `pptx.off-slide` | warning | review | Top-level object extending beyond the slide canvas |
| `pptx.title-missing` | info | content | Slide without a titled title placeholder (outline and screen readers) |
| `pptx.hidden-slide` | info | review | Slide hidden in the show |

## Excel

| Rule | Severity | Fix | Detects |
|---|---|---|---|
| `xlsx.cached-error` | error | review | Formula whose stored result is an error (`#REF!`, `#DIV/0!` and the rest) |
| `xlsx.ref-error-in-formula` | error | review | Formula text that refers to a deleted range |
| `xlsx.broken-name` | error | review | Defined name that refers to a deleted range |
| `xlsx.inconsistent-formula` | warning | review | Formula that differs from identical formulas on both sides, compared in relative form |
| `xlsx.not-calculated` | warning | safe | Stored results the writer never calculated (`fullCalcOnLoad`, missing caches) |
| `xlsx.literal-error` | warning | review | Error value typed as a constant |
| `xlsx.hardcoded-constant` | info | review | Number other than 0 or 1 next to an arithmetic operator inside a formula |

## Outside these rules

Text overflow, overlapping objects, pagination, font substitution, formula
correctness, circular references and schema validity need an engine, a renderer
or a validator. The report names them under `not_checked`; the workflow covers them
with the engine and the format's reviewer, or reports them as unverified.

## Provenance

The Excel categories follow the checks listed by the `audit-xls` skill in
[anthropics/financial-services](https://github.com/anthropics/financial-services)
(Apache-2.0), and the overflow and alternative-text categories follow the issue
types of [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI)'s `view issues`
(Apache-2.0). Rules, wording and code here are original; nothing is copied.
