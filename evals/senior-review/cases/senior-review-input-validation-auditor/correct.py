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
    return db.execute('SELECT name FROM products WHERE name=?', (name,)).fetchall()


# Scenario normalized_value
def normalized(request, validator, sink):
    from urllib.parse import unquote
    value = unquote(request)
    validator(value)
    return sink(value)


# Scenario query_object
def nosql(name):
    if not isinstance(name, str):
        raise ValueError('name')
    return {'name': name}


# Scenario interpreter_boundaries
def interpret(kind, value, adapters):
    import json
    if kind == 'shell':
        return adapters['argv'](['lookup', '--name', value])
    if kind == 'ldap':
        return adapters['ldap_value']('name', value)
    if kind == 'template':
        return adapters['template_data']('greeting', {'name': value})
    if kind == 'object':
        return json.loads(value)
    raise ValueError('kind')


# Scenario expanded_work
def match_input(value, risky_match):
    if len(value) > 256:
        raise ValueError('characters')
    return risky_match(value)
def expand_input(compressed, expand, expand_bounded):
    return expand_bounded(compressed, 4096)
