# Refresh and supersession

Read `runtime.md` for selectors, revision checks and receipts. Explicit
update-research works even when Science Mode is OFF or its config is malformed;
it does not repair/change mode. Reuse caller scope and grants.

Resolve an exact ID or topic; disambiguate multiple matches before mutation.
With no selector, use research explicitly linked to the current task only when
exactly one identity is linked; otherwise ask for the scope before any mutation.
An empty inventory, including an empty all/tutte batch, returns `nessuna ricerca
da aggiornare` without network work or archive writes. A nonexistent selector
never implicitly creates research.
Apply `reuse.md` first, including existing unindexed Markdown. Keep the same
current file and identity: new evidence updates it, visibly strikes through
superseded claims, refreshes research timestamps and appends a descriptive
changelog. Historical snapshots are separate from that single current page.
For all/tutte, snapshot the list once, visit each canonical identity once and
report successes, unchanged, partial and failed records separately. A failed
record does not imply success for the batch or prevent independent updates.

For each record read its pinned revision and question, compare relevant
technology versions, search new findings/replications and check source versions
and editorial notices through primary publishers and available metadata services.
Record actual queries, access times, coverage and limits.

Keep these separate: source publication/editorial status; support for each claim;
local applicability; research supersession; experiment execution/result. Age alone
never makes a paper obsolete. A retraction triggers review of dependent claims,
not proof of their opposite. Suspend the retracted source as reliable positive
support until clarified; identify dependent claims and publish their changed
status and notice while preserving the historical revision. A newer technology may change applicability without
refuting the original result.

Use an immutable check receipt for every attempt. A completed no-change check
leaves the scientific revision unchanged; failed/partial/cancelled checks never
claim full freshness. Distinguish last_checked_at, latest complete check and
last_updated_at. Material changes publish a new immutable revision with expected
revision, cumulative changelog, reasons, replacement evidence, changed claim IDs
and residual uncertainty. Never erase old sources or revisions.

List known consuming specifications, ADR/FRD and tests, the pinned claims they
use and why they need review. State coverage of that consumer list. The owner
decides subsequent edits; accepted records are never silently rewritten.
