"""Within one tenant each external reference identifies one order. HTTP and import writers may run in separate processes against this SQLite schema. Replaying a reference must not add another row.
atomic_unit: A transfer must debit and credit together. transaction() creates the scoped tx handle; all tx.write operations roll back together on exception. db.write uses a separate autocommit connection and commits immediately even while that transaction context is active. credit may reject after debit.
write_skew: At least one on-call operator must remain. Unprotected transactions observe their own snapshots; two concurrent operators may request leave. lock_all acquires the predicate lock across all processes and establishes a fresh committed snapshot for the enclosed count and write before either executes; that lock serializes all on-call predicate updates.
retry_decision: A serialization conflict aborts the transaction. The price must be re-read for each successful transaction attempt; transaction() supplies a new current view and raises Conflict when aborted.
dedup_commit: The owner is serial; abrupt process failure is outside this scene. A successful debit and its receipt must be observable together on return. Debit may raise before mutation; a completed key binds amount and must reject a different amount on replay.
orm_orphans: Children require a present parent and must be deleted with it. The effective mapping is application-enforced in a single atomic owner; all relevant writers use delete_parent."""

import sqlite3
def setup():
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE orders(tenant TEXT, reference TEXT)')
    return db
def http_create(db, tenant, reference):
    if db.execute('SELECT 1 FROM orders WHERE tenant=? AND reference=?', (tenant, reference)).fetchone():
        return
    with db:
        db.execute('INSERT INTO orders VALUES (?, ?)', (tenant, reference))
def import_create(db, tenant, reference):
    with db:
        db.execute('INSERT INTO orders VALUES (?, ?)', (tenant, reference))


# Scenario atomic_unit
def transfer(db, debit, credit):
    with db.transaction() as tx:
        db.write(debit)
        tx.write(credit)


# Scenario write_skew
def leave(tx, operator):
    if tx.count_on_call() > 1:
        tx.set_off_call(operator)


# Scenario retry_decision
class Conflict(Exception):
    pass
def purchase(db):
    price = db.price()
    for attempt in range(2):
        try:
            with db.transaction() as tx:
                return tx.buy(price)
        except Conflict:
            if attempt:
                raise


# Scenario dedup_commit
def once(key, amount, done, debit):
    if key in done:
        return done[key]
    done[key] = amount
    debit(amount)
    return amount


# Scenario orm_orphans
def delete_parent(parents, children, parent_id):
    parents.pop(parent_id, None)
