# schema-coherence-auditor independent qualification case

Authoring pack, not a behavioral qualification result. Reviewer identity:
`senior-review:schema-coherence-auditor`. Materialize exactly one entire directory
(`defect/` or `correct/`) into a neutral target. Only that target, the canonical role
and its required references belong in the isolated reviewer's read scope. Never
provide this file, the counterpart or private setup observations to the reviewer.

## Independent causal controls (scorer only)

| Control | Requirement and causal mechanism in defect | Healthy counterevidence / must_not_report |
|---|---|---|
| SC001 | `create_account(Account(2, 'Lin'))` resolves logical `name` to nonexistent SQL column `name`, while native applied DDL owns `display_name`. The actual INSERT fails. Compare the used mapper declaration with applied DDL and handwritten account reader. | Correct maps logical `name` explicitly to `display_name`; the same DTO persists and reads back. Do not report different naming conventions, a missing `name` SQL column when mapped, or intentionally retained nullable `legacy_label` / `vendor_accounts`. |
| SC002 | Applied `account_notes.account_id` is `ON DELETE RESTRICT`, whereas `ACCOUNT_NOTE` declares CASCADE and the purge contract permits deletion after opening a ticket. `ticket_opened` is a hidden writer that inserts a referencing note. The unchanged admin/reset/retention writer executes `DELETE accounts`, which now fails with an FK violation. Name the trigger-created row and every supplied purge caller. | Correct applied FK is CASCADE. The same unmodified purge deletes account, ticket and note through database enforcement. Do not demand manual child deletes, claim the trigger is absent from the writer inventory, or create a transaction-integrity finding. |
| SC003 | `005_inventory_v2` drops `inventory.shelf_code` before removing dependent `stock_summary`. SQLite rejects the DROP COLUMN while the view still names the column; later view recreation is unreachable. The empty-table approved replacement and post-success-only entity contract remove unrelated value-loss and old-binary premises. | Correct drops the view first, then replaces the column and recreates the view inside the migration. An inserted `bin_code` is returned via stable alias `location_code`. Do not report pre-upgrade entity drift or demand cross-version rollout machinery. This is dependent-object DDL ordering, not application-startup ordering. |
| SC004 | Native applied dump and `schema_migrations` show only 001, 002, 003; `004_sms_route` is present in source but unapplied in the identified environment. Route configuration is enabled and both model and SQL require `destination`, so configuration fails. Attribute mismatch to environment state, not an incorrect model. | Correct dump records 004 and physical `destination`; same route DTO/configuration/read succeeds. No live production connection is required because supplied native state is admitted. Do not equate migration-file existence with execution or flag deliberately pending 005. |
| SC005 | Current generator input and applied 003 describe `resource_key`, but the checked-in imported reader selects `legacy_key`. Authentic owned Git records show output last generated before the current input revision. The snapshot read fails; regenerating from current input yields different output. | Correct current generator output equals the checked-in reader and its latest generation record. Exact regeneration in an owned copy yields identical bytes and the snapshot round trip succeeds. Do not demand a second schema authority, manual edits or treat generated status alone as freshness. |

Each control has an independently fresh connection, so one failure does not hide
another. All five are persistent-representation disagreements. Field meaning,
atomicity, concurrent writers, cost, startup dependency ordering and mixed-version
coexistence remain outside this reviewer's mandate. No artificial finding quota:
separate or consolidated findings are acceptable if each distinct causal mechanism
is correctly evidenced, without multiplying one mechanism into duplicate findings.

## Evidence, coverage and remaining limits

Target files contain native applied SQL, applied ledger, complete migration source,
all model/DTO/SQL code, trigger and views, current generator input and output, and
authentic exported generation history. No procedures or additional generation
pipeline exist. Private setup uses only Python stdlib SQLite in fresh in-memory
databases and an owned local Git repository. It records Python/engine/Git versions,
commands, exits, exact target hashes, PRAGMA/catalog state, observed operations and
generated-byte comparisons in `.daodan/runs/specialists-composition-20261023/schema-inputs/`.
That private material is the author's setup/oracle evidence, never reviewer input.

Source-only review must classify its conclusions as derived; author setup does
not grant the reviewer runtime coverage. Setup cannot establish behavior on other
SQLite versions, other engines, production environments, external ORMs, concurrent
transactions, unknown deployment runners, FK enforcement disabled by other callers,
or end-to-end product execution. Native dump generation is not evidence that a
different deployment applied the same chain. Migration 005 is exercised separately
from enabled route configuration; no startup orchestration is being tested.

The healthy target must return a complete clean report when all admitted inputs
are inspected. Missing required inputs, partial coverage or missing delivery is a
review gap, not a product defect. A successful SQLite setup or artifact hash audit
does not qualify the reviewer; the coordinator independently audits the oracle and
then runs fresh isolated qualification with the existing result envelope.
