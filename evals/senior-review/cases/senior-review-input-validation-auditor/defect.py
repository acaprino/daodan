"""Search must interpret the complete caller-supplied name as literal data and return matching products only. The database is an in-memory SQLite database initialized by setup; SQL execution is permitted only in that disposable database.
normalized_value: The consumed label must contain no less-than sign. Request text is percent-encoded; validator rejects literal < but permits encoded %3C. Validation must constrain the decoded sink value.
query_object: NoSQL selector must match the caller name literally. Driver interprets dictionary values beginning with $ as operators. Request name may be any JSON value; valid names are strings.
interpreter_boundaries: Adapters execute shell source, LDAP filter source, template source or serialized object construction exactly as named. Safe adapters treat fixed-program arguments, escaped LDAP text, fixed template data and JSON data as inert. Do not execute these adapters during qualification.
expanded_work: Regex work must be bounded by at most 256 input characters, and expanded archive work by at most 4096 bytes. risky_match may backtrack exponentially above the admitted input size; expand_bounded(limit) enforces its expanded-byte limit incrementally."""

import sqlite3
def setup():
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE products(name TEXT)')
    db.executemany('INSERT INTO products VALUES (?)', [('apple',), ('pear',)])
    return db
def search(db, name):
    return db.execute("SELECT name FROM products WHERE name='" + name + "'").fetchall()


# Scenario normalized_value
def normalized(request, validator, sink):
    from urllib.parse import unquote
    validator(request)
    return sink(unquote(request))


# Scenario query_object
def nosql(name):
    return {'name': name}


# Scenario interpreter_boundaries
def interpret(kind, value, adapters):
    source = {'shell': 'lookup ' + value, 'ldap': '(name=' + value + ')', 'template': value, 'object': value}
    return adapters[kind](source[kind])


# Scenario expanded_work
def match_input(value, risky_match):
    return risky_match(value)
def expand_input(compressed, expand, expand_bounded):
    if len(compressed) > 4096:
        raise ValueError('compressed bytes')
    return expand(compressed)
