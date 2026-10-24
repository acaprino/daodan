# Release requirements

Two independent release proposals target the same starting system. v1 reads the
non-null customers.name column, which the old schema contains. v2 reads the new
customers.display_name column. Both versions must serve requests during a rolling
update. v1 remains active until all v2 instances are healthy. The schema migrations
below run before any v2 instance starts. No ORM alias, view or query rewrite exists.
Static review only; no deployment, database command or application run authorized.

Proposal A runs only migration-a.sql, then starts v2 and drains v1.
Proposal B runs only migration-b.sql, then starts v2 and drains v1. It keeps the
old name column for the whole supported rollback window. Writes are disabled
during this migration and both versions only read this table during rollout.
