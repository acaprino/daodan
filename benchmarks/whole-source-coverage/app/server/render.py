"""HTML page listing a user's notes."""
from html import escape

PAGE = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Notes of {user}</title></head>
<body>
<h1>Notes of {user}</h1>
<ul>
{items}
</ul>
</body>
</html>
"""


def note_item(name: str) -> str:
    return f'<li><a href="/notes/{escape(name, quote=True)}">{escape(name)}</a></li>'


def note_list_page(user: str, names: list[str]) -> str:
    items = "\n".join(note_item(name) for name in names) or "<li>No notes yet.</li>"
    return PAGE.format(user=escape(user), items=items)
