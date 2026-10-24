"""Complete migration source for the supplied SQLite environment."""

CORE = """
CREATE TABLE schema_migrations (name TEXT PRIMARY KEY);
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    display_name TEXT NOT NULL,
    legacy_label TEXT
);
CREATE VIEW vendor_accounts AS SELECT id, legacy_label FROM accounts;
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE
);
CREATE TABLE inventory (id INTEGER PRIMARY KEY, shelf_code TEXT NOT NULL);
CREATE VIEW stock_summary AS SELECT id, shelf_code AS location_code FROM inventory;
CREATE TABLE notification_routes (
    id INTEGER PRIMARY KEY,
    channel TEXT NOT NULL CHECK (channel IN ('sms', 'email'))
);
CREATE TABLE snapshots (id INTEGER PRIMARY KEY, legacy_key TEXT NOT NULL);
"""

NOTES = """
CREATE TABLE account_notes (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    note TEXT NOT NULL
);
CREATE TRIGGER ticket_opened AFTER INSERT ON tickets BEGIN
    INSERT INTO account_notes(account_id, note) VALUES (NEW.account_id, 'opened');
END;
"""

SNAPSHOT_KEY = "ALTER TABLE snapshots RENAME COLUMN legacy_key TO resource_key;"
SMS_ROUTE = "ALTER TABLE notification_routes ADD COLUMN destination TEXT NOT NULL DEFAULT '';"

INVENTORY_V2 = """
ALTER TABLE inventory DROP COLUMN shelf_code;
ALTER TABLE inventory ADD COLUMN bin_code TEXT NOT NULL DEFAULT 'unassigned';
DROP VIEW stock_summary;
CREATE VIEW stock_summary AS SELECT id, bin_code AS location_code FROM inventory;
"""

MIGRATIONS = {
    '001_core': CORE,
    '002_ticket_notes': NOTES,
    '003_snapshot_key': SNAPSHOT_KEY,
    '004_sms_route': SMS_ROUTE,
    '005_inventory_v2': INVENTORY_V2,
}


def apply(connection, name):
    """Apply one known script, then record success. Callers own sequencing."""
    connection.executescript(MIGRATIONS[name])
    connection.execute('INSERT INTO schema_migrations(name) VALUES (?)', (name,))
    connection.commit()
