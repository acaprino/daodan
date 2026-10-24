# Local account service persistence contract

This packet is a complete small SQLite application snapshot for a content audit.
`applied.sql` is the native `Connection.iterdump()` snapshot of the identified
owned disposable environment `local-account-service`. It was created with Python
3.13.14 / SQLite 3.50.4, with `PRAGMA foreign_keys=ON`, by applying the migration
names recorded in its `schema_migrations` table. The dump and that table are the
evidence of applied state. A migration's source-file presence alone does not
establish that it ran. No production database, network or external service exists.

`migrations.py` is the complete ordered migration source. `application.py` contains
the complete persistence declarations, DTOs and handwritten application SQL for
these objects. Its `Entity` metadata is a small local persistence mapper; logical
attribute names resolve through `Column.physical_name`. All IDs are integer primary
keys. The database owns constraints and the trigger; callers keep foreign-key
enforcement enabled. No procedures, user-defined database functions or additional
triggers, views, ORMs, SQL writers or migration runners are omitted. The only
generation pipeline is documented below. The supplied dump includes all seed rows.

The service supports these independent operations:

1. Account creation persists `Account.name` into the physical `accounts.display_name`
   column. `name` is an intentional Python attribute name. `legacy_label` is a
   nullable vendor integration column, intentionally absent from the application
   entity and DTO; `vendor_accounts` keeps it readable. Keeping that legacy column
   is a supported requirement.
2. Opening a ticket writes a note through `ticket_opened`. Account deletion by
   admin, reset and retention callers uses the single `purge_account` function.
   It must succeed even after a ticket has been opened, removing its tickets and
   notes. The `ACCOUNT_NOTE` relation declares the chosen cascade policy; either
   database cascades or explicit child deletion can implement the purge contract.
   Ticket and note payloads have no independent retention requirement.
3. `005_inventory_v2` is the pending inventory migration in this packet. Inventory is
   empty before it runs; replacing the old location column is approved. The
   `stock_summary` reader must survive the migration and return the `bin_code`
   value as `location_code`. `INVENTORY_V2`, `place_inventory` and `list_inventory`
   activate only after successful completion of this migration. Review the engine's
   handling of the existing view, not the meaning of location values or rollout
   across concurrently running application versions.
4. Route configuration is enabled in the supplied environment. `004_sms_route`
   must already have been applied before enabling it. The route entity and both
   handwritten route operations use physical column `destination`. An empty
   destination is valid until configured. `005_inventory_v2` need not have run for
   route configuration; inventory has a separate explicit upgrade entry point.
5. `generate_projection.py` authors `generated_projection.py` from its current
   `INPUT_SCHEMA`. The input describes physical columns after `003_snapshot_key`.
   The application imports the checked-in reader; it does not regenerate on load.
   The reader must select the current `snapshots.resource_key`. `generation.txt`
   contains authentic read-only records from a separate owned fixture Git history:
   current source commit, last artifact-changing generation commit, exact generated
   bytes and input/output hashes. Those commits are fixture provenance, not claims
   about the enclosing project's history. Regenerating is the supported way to
   update the artifact; generated code is not hand maintained.

Each operation has its own fresh database in setup validation, so a failure in one
does not prevent examining the others. Runtime setup observations, the counterpart
packet and the independent scoring oracle are not admitted reviewer inputs.
Reviewer execution authority comes from the assignment, not from these setup
instructions. No transaction, concurrency, value-conversion, performance or
mixed-version guarantee is being introduced by this packet.
