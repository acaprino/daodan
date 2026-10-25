# Routing from one entry

`office:start` takes any Office request and works out which workflows to run,
with which operation, before anything is built. The conversation itself (how a
question is shaped, how a decision is recorded, when a decision map is opened)
belongs to `work-controller:work-record` and its question rules; this reference
adds only what is specific to Office files: what an input can be, what the user
can want from it, and which workflow and operation serve it.

## 1. Inventory the inputs

Read every input before deciding what it is for. A URL is fetched only to read
it, never to submit anything.

| Input | What it can be | How to read it |
|---|---|---|
| `.pptx`, `.potx` | A deck to edit, expand, revise, restyle or review; the base of a derived deck; a template or theme source | `office:deckcraft`'s `pptx_inspect.py inspect` |
| `.docx`, `.dotx` | A document to work on; a content source for a deck; a template or theme source | `office:docx`'s `docx_inspect.py inspect` |
| `.xlsx`, `.xltx` | A workbook to work on; a data source for a deck or document | `office:xlsx`'s `xlsx_inspect.py inspect` |
| A website URL | A content source, a colour and brand source, or both | Fetch and read the pages; `office:design`'s `palette.py from-url` for colours |
| An image or logo | A colour source; an asset to insert | `palette.py from-image`; view it |
| Stylesheets or design tokens | A colour source | `palette.py from-css` |
| Notes, text, a PDF, a research report | A content source | Read it |
| Nothing | Create from the request itself | |

An input's role comes from the request ("use their website for the colours",
"turn this report into slides"). When the request does not say and the role
changes the result, that is a decision for the user.

## 2. Name the destination

The destination is what the user holds at the end: a deck, a document, a
workbook, a theme (`.potx` and `.dotx`), an integrity report, a repaired copy or
an export (PDF, preview). A request can have several. A document and a deck made
from the same brief share one design record. When the destination itself is
unclear ("do something with this website"), it is the first and only question
of the first round.

## 3. Route to workflows and operations

| Request | Workflow | Operation |
|---|---|---|
| A theme, template, slide master, house style or brand kit | `theme` | |
| A new deck, document or workbook, from a brief, sources, data or a website | the format's workflow | Create |
| A deck from an existing document or report, or a document from a deck | the target format's workflow | Derive; the existing file is a content source |
| A shorter version, another audience or language of an existing file | the file's workflow | Derive |
| Add slides, sections or content to an existing file | the file's workflow | Expand |
| Update figures or claims, rewrite, restructure, shorten | the file's workflow | Revise |
| The same content with a new look, or with the user's brand | the file's workflow | Restyle; `theme` first when the look comes from a new source and is wanted as a reusable template |
| Change one wording, figure, format or element | the file's workflow | Edit |
| Check, validate or audit a file | `verify` | |
| Repair the defects of a file | `fix` | |
| Read, summarize, review or export a file | the file's workflow | Review or export |
| A document and its deck from one brief | `document`, then `presentation` | Create, sharing one design record |

Operations combine (expand and restyle); the workflow runs the union of their
steps, as `office:intake`'s operation table describes.

## 4. Settle what the inputs settle, then ask once

The decisions each routed workflow leaves open are the operation's row in
`office:intake`, the format's planning decisions and, when the look is new, the
design decisions. Before asking anything, settle every decision the request
states or an input supplies: an existing file gives its argument mode, audience,
theme and styles; a website or logo gives the colours; a report gives the claims.
Propose a default with its reason where one is sound (a slide count from the
speaking time). What remains goes to the user through `work-controller`'s
question rules, in one round, one decision per question, with the recommended
option first; the agent never answers a user decision itself. A decision that
depends on another waits for it: the palette choice follows the colour source;
slide design follows the content plan; a deck built on a new theme follows the
theme.

## 5. Record and run

Record one brief per routed workflow under `office:intake`'s "Record the route",
with the operation and each decision's value and source (request, file,
discovery, proposal or answer). A recorded brief is that workflow's intake
round: its method asks nothing already in it. Run the workflows in order and
pass outputs forward: a generated theme becomes the base of the deck or
document; a document and deck from one brief share one design record. A change
of destination during the work re-enters this routing.
