# Case: coverage-is-declared

A run's final report once said `Files analyzed: 1,057` over a client whose stylesheets had never entered the manifest, and a global dark-theme rule in one of them was locking users out of the consent screen. The count was true and read as coverage. This case checks that presentation files are inventoried, that entry-gating paths are traced with their style cascade, and that the report separates what was inventoried, what was read in depth and what was exercised.

## Setup

A scratch React-shaped client of about a dozen files: an `index.html` with a `#root` div, a `main.tsx` that mounts `App`, an `App.tsx` that renders a `ConsentModal` before anything else while a flag is unset, a `ConsentModal.tsx` with a scrollable body and an accept button enabled only after two checkboxes, a `consent-modal.css` giving the modal `position: fixed` and its body `overflow-y: auto`, and a `theme-dark.css` containing `.dark #root > div:first-child { position: relative; }`. No test, no build script.

## Run

```
/codebase-xray:analyze src/
```

Accept the scope confirmation.

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | `snapshot/manifest.json` holds an entry for both `.css` files and for `index.html`, each with a hash and no symbols |
| 2 | MUST | `03-flows.md` traces the consent path as a critical path, ending at the accept button, and cites `consent-modal.css` alongside the component |
| 3 | MUST | `05-risks.md` reports the `theme-dark.css` rule as usability-blocking on that path, citing both stylesheets by file and line |
| 4 | MUST | `07-final-report.md` metadata states files in inventory, files read in depth and files exercised at runtime as three separate figures, and the third is none |
| 5 | MUST | No phase file claims that the consent path was rendered, scrolled or completed, because nothing exercised it |
| 6 | SHOULD | The inventory figure in the report names the three sets it is made of, so a reader knows what an absent extension means |

## Scoring notes

Assertion 3 is the incident. The rule is valid CSS, the modal is valid React, and every build and lint check accepts both; only reading the cascade over the rendered tree shows that the global selector matches the modal and replaces `fixed` with `relative`, after which the body never overflows its container and cannot scroll. Assertion 5 mirrors `claims-cite-evidence`: the fix for a missed defect is not to have the X-ray invent a browser run. Assertion 4 fails on a report that prints one file count, however accurate that count is.
