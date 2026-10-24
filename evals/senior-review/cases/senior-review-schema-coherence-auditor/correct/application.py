"""Persistence declarations and all application readers/writers in review scope."""

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from generated_projection import SNAPSHOT_SELECT
from migrations import apply


@dataclass(frozen=True)
class Column:
    physical_name: str
    sql_type: str
    nullable: bool = False


@dataclass(frozen=True)
class ForeignKey:
    column: str
    target: str
    on_delete: str


@dataclass(frozen=True)
class Entity:
    table: str
    columns: dict[str, Column]
    foreign_keys: tuple[ForeignKey, ...] = ()


# These declarations are the application's small persistence mapper. Dictionary
# keys are Python attribute names; Column.physical_name is the SQL identifier.
# Integer id columns are primary keys. SQLite allocates account_notes.id.
ACCOUNT = Entity('accounts', {
    'id': Column('id', 'INTEGER'),
    'name': Column('display_name', 'TEXT'),
})
TICKET = Entity('tickets', {
    'id': Column('id', 'INTEGER'),
    'account_id': Column('account_id', 'INTEGER'),
}, (ForeignKey('account_id', 'accounts.id', 'CASCADE'),))
ACCOUNT_NOTE = Entity('account_notes', {
    'id': Column('id', 'INTEGER'),
    'account_id': Column('account_id', 'INTEGER'),
    'note': Column('note', 'TEXT'),
}, (ForeignKey('account_id', 'accounts.id', 'CASCADE'),))
ROUTE = Entity('notification_routes', {
    'id': Column('id', 'INTEGER'),
    'channel': Column('channel', 'TEXT'),
    'destination': Column('destination', 'TEXT'),
})
SNAPSHOT = Entity('snapshots', {
    'id': Column('id', 'INTEGER'),
    'resource_key': Column('resource_key', 'TEXT'),
})
# This entity is activated only after upgrade_inventory succeeds.
INVENTORY_V2 = Entity('inventory', {
    'id': Column('id', 'INTEGER'),
    'bin': Column('bin_code', 'TEXT'),
})


@dataclass(frozen=True)
class Account:
    id: int
    name: str


@dataclass(frozen=True)
class Route:
    id: int
    channel: str
    destination: str


@dataclass(frozen=True)
class Snapshot:
    id: int
    resource_key: str


def open_supplied_environment():
    """Create an owned disposable connection from the supplied applied dump."""
    connection = sqlite3.connect(':memory:')
    connection.execute('PRAGMA foreign_keys = ON')
    connection.executescript(Path(__file__).with_name('applied.sql').read_text())
    return connection


def applied_chain(connection):
    return [row[0] for row in connection.execute(
        'SELECT name FROM schema_migrations ORDER BY name')]


def create_account(connection, account):
    attributes = ('id', 'name')
    columns = ', '.join(ACCOUNT.columns[name].physical_name for name in attributes)
    values = tuple(getattr(account, name) for name in attributes)
    connection.execute(f'INSERT INTO accounts ({columns}) VALUES (?, ?)', values)


def list_accounts(connection):
    return [Account(*row) for row in connection.execute(
        'SELECT id, display_name FROM accounts ORDER BY id')]


def open_ticket(connection, ticket_id, account_id):
    connection.execute('INSERT INTO tickets(id, account_id) VALUES (?, ?)',
                       (ticket_id, account_id))


def list_account_notes(connection, account_id):
    return list(connection.execute(
        'SELECT id, note FROM account_notes WHERE account_id = ?', (account_id,)))


def purge_account(connection, account_id):
    # The existing admin/reset/retention path; all three call this function.
    connection.execute('DELETE FROM accounts WHERE id = ?', (account_id,))


def read_vendor_labels(connection):
    return list(connection.execute('SELECT id, legacy_label FROM vendor_accounts'))


def configure_route(connection, route):
    connection.execute(
        'UPDATE notification_routes SET channel = ?, destination = ? WHERE id = ?',
        (route.channel, route.destination, route.id))


def list_routes(connection):
    return [Route(*row) for row in connection.execute(
        'SELECT id, channel, destination FROM notification_routes ORDER BY id')]


def list_snapshots(connection):
    return [Snapshot(*row) for row in connection.execute(SNAPSHOT_SELECT)]


def upgrade_inventory(connection):
    apply(connection, '005_inventory_v2')


def place_inventory(connection, item_id, bin_code):
    connection.execute('INSERT INTO inventory(id, bin_code) VALUES (?, ?)',
                       (item_id, bin_code))


def list_inventory(connection):
    return list(connection.execute(
        'SELECT id, location_code FROM stock_summary ORDER BY id'))
