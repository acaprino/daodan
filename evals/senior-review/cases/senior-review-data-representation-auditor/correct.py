"""Rows have unique integer IDs and nonunique integer created timestamps. Stable cursor pagination must enumerate every row once in ascending (created,id) order for an unchanged dataset. Cursor is the last returned row.
money_and_time: Amounts are exact decimal currency values; persistence must preserve their decimal sum. This currency domain admits at most 1000 finite decimal strings, each from 0 through 1000000000 with at most two fractional digits; arithmetic uses a 28-significant-digit decimal context, unchanged during the operation. Instants supplied with UTC offset must retain that offset on round trip. No live clock involved.
stored_versions: Stored v1 rows use name, v2 rows use display; v1 must remain readable. display may legitimately be NULL and must not silently become an empty value. No other version exists.
backfill_race: Backfill uses a captured row revision and computed value. It may restart and race with writers; applying a conversion may not overwrite newer edits. compare_and_set is atomic."""

ROWS = [{'created': 1, 'id': 1}, {'created': 1, 'id': 2}, {'created': 2, 'id': 3}]
def page(cursor=None, limit=1):
    rows = sorted(ROWS, key=lambda row: (row['created'], row['id']))
    return [row.copy() for row in rows if cursor is None or (row['created'], row['id']) > (cursor['created'], cursor['id'])][:limit]


# Scenario money_and_time
def save_amount(values):
    from decimal import Decimal
    return str(sum((Decimal(v) for v in values), Decimal(0)))
def save_instant(value):
    return value.isoformat()


# Scenario stored_versions
def read_row(row):
    return row['display'] if row['version'] == 2 else row['name']


# Scenario backfill_race
def apply_backfill(store, key, captured_revision, converted):
    return store.compare_and_set(key, captured_revision, converted)
