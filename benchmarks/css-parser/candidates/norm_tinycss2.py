"""tinycss2 behind the same shape as adapters.mjs (parse_stylesheet, then parse_blocks_contents on every block), plus the position checks."""
import json
import os
from pathlib import Path

import tinycss2

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get('OUT', HERE / 'out'))
inputs = json.load(open(HERE / 'inputs.json', encoding='utf-8'))
OUT.mkdir(parents=True, exist_ok=True)


def collapse(s):
    return ' '.join(s.split())


def ser(tokens, comments=False):
    return tinycss2.serialize([t for t in tokens if comments or t.type != 'comment'])


def line_starts(src, conv):
    starts = [0]
    i = 0
    while i < len(src):
        c = src[i]
        if c == '\r':
            if i + 1 < len(src) and src[i + 1] == '\n':
                i += 1
            starts.append(i + 1)
        elif c == '\n' or (conv == 'spec' and c == '\f'):
            starts.append(i + 1)
        i += 1
    return starts


def offset_of(starts, line, col):
    return starts[line - 1] + col - 1 if 1 <= line <= len(starts) else -1


def scan_comments(tokens, out):
    for t in tokens:
        if t.type == 'comment':
            out['comments'].append({'text': t.value.strip(), 'line': t.source_line, 'column': t.source_column})
        elif t.type == 'function':
            scan_comments(t.arguments, out)
        elif t.type in ('() block', '[] block'):
            scan_comments(t.content, out)


def blocks(content):
    return tinycss2.parse_blocks_contents(content, skip_comments=False, skip_whitespace=True)


def walk(nodes, out):
    for n in nodes:
        t = n.type
        if t == 'qualified-rule':
            full = ser(n.prelude, True)
            out['rules'].append({'sel': [collapse(ser(n.prelude)), collapse(full)], 'line': n.source_line, 'col': n.source_column, 'endLine': None})
            out['pos'].append({'kind': 'rule', 'line': n.source_line, 'col': n.source_column, 'text': full.lstrip()[:3]})
            scan_comments(n.prelude, out)
            walk(blocks(n.content), out)
        elif t == 'at-rule':
            full = ser(n.prelude, True)
            text = collapse(ser(n.prelude))
            out['atrules'].append({'name': n.at_keyword, 'prelude': [text, collapse(full)] if text else None, 'hasBlock': n.content is not None,
                                   'line': n.source_line, 'col': n.source_column, 'endLine': None})
            out['pos'].append({'kind': 'atrule', 'line': n.source_line, 'col': n.source_column, 'text': '@' + n.at_keyword[:3]})
            scan_comments(n.prelude, out)
            if n.content is not None:
                walk(blocks(n.content), out)
        elif t == 'declaration':
            out['decls'].append({'property': n.name, 'value': [collapse(ser(n.value)), collapse(ser(n.value, True))], 'important': bool(n.important), 'line': n.source_line})
            out['pos'].append({'kind': 'decl', 'line': n.source_line, 'col': n.source_column, 'text': n.name[:3]})
            scan_comments(n.value, out)
        elif t == 'comment':
            out['comments'].append({'text': n.value.strip(), 'line': n.source_line, 'column': n.source_column})
            out['pos'].append({'kind': 'comment', 'line': n.source_line, 'col': n.source_column, 'text': '/*'})
        elif t == 'error':
            out['errors'] += 1


items = []
P = {'nodes': 0, 'startSpec': 0, 'startEditor': 0, 'startNoText': 0, 'lcOffset': 0, 'lcOffsetOk': 0, 'blockEnds': 0, 'endExcl': 0, 'endIncl': 0,
     'endGiven': 0, 'endNone': 0, 'refMembership': 0, 'refMembershipOk': 0, 'startMismatch': []}
for inp in inputs:
    src = inp['src']
    out = {'threw': None, 'errors': 0, 'rules': [], 'decls': [], 'atrules': [], 'comments': [], 'pos': []}
    try:
        walk(tinycss2.parse_stylesheet(src, skip_comments=False, skip_whitespace=True), out)
    except Exception as e:  # noqa: BLE001
        out = {'threw': f'{type(e).__name__}: {str(e)[:100]}', 'errors': 0, 'rules': [], 'decls': [], 'atrules': [], 'comments': [], 'pos': []}
    spec, editor = line_starts(src, 'spec'), line_starts(src, 'editor')
    for p in out['pos']:
        P['nodes'] += 1
        text = p['text']
        ok_spec = text != '' and src.startswith(text, offset_of(spec, p['line'], p['col']))
        ok_ed = text != '' and src.startswith(text, offset_of(editor, p['line'], p['col']))
        P['startSpec'] += ok_spec
        P['startEditor'] += ok_ed
        if not ok_spec and len(P['startMismatch']) < 8:
            P['startMismatch'].append(f"{inp['id']} {p['kind']} {p['line']}:{p['col']} text {text!r}")
        P['endNone'] += 1
    del out['pos']
    items.append({'id': inp['id'], **out})
caps = {'ruleSel': True, 'ruleEnd': False, 'declLine': True, 'declValue': True, 'atrules': True, 'atrulePrelude': True, 'comments': True, 'declOrder': True, 'errors': True}
P['startMismatchCount'] = len(P['startMismatch'])
json.dump({'tool': 'tinycss2', 'caps': caps, 'position': P, 'items': items}, open(OUT / 'norm_tinycss2.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('tinycss2:', len(items), 'inputs, threw', sum(1 for i in items if i['threw']), 'positions', {k: v for k, v in P.items() if k != 'startMismatch'})
