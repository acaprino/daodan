BEGIN TRANSACTION;
CREATE TABLE account_notes (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    note TEXT NOT NULL
);
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    display_name TEXT NOT NULL,
    legacy_label TEXT
);
INSERT INTO "accounts" VALUES(1,'Ada','vendor-7');
CREATE TABLE inventory (id INTEGER PRIMARY KEY, shelf_code TEXT NOT NULL);
CREATE TABLE notification_routes (
    id INTEGER PRIMARY KEY,
    channel TEXT NOT NULL CHECK (channel IN ('sms', 'email'))
, destination TEXT NOT NULL DEFAULT '');
INSERT INTO "notification_routes" VALUES(1,'email','');
CREATE TABLE schema_migrations (name TEXT PRIMARY KEY);
INSERT INTO "schema_migrations" VALUES('001_core');
INSERT INTO "schema_migrations" VALUES('002_ticket_notes');
INSERT INTO "schema_migrations" VALUES('003_snapshot_key');
INSERT INTO "schema_migrations" VALUES('004_sms_route');
CREATE TABLE snapshots (id INTEGER PRIMARY KEY, resource_key TEXT NOT NULL);
INSERT INTO "snapshots" VALUES(1,'resource-A');
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE
);
CREATE VIEW vendor_accounts AS SELECT id, legacy_label FROM accounts;
CREATE VIEW stock_summary AS SELECT id, shelf_code AS location_code FROM inventory;
CREATE TRIGGER ticket_opened AFTER INSERT ON tickets BEGIN
    INSERT INTO account_notes(account_id, note) VALUES (NEW.account_id, 'opened');
END;
COMMIT;
