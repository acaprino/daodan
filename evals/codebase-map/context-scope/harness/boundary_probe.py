"""Post-hoc probe: does a narrowed read boundary let the packet deliver?

Exploratory, never part of the registered protocol. The read boundary is narrowed to the files of
the gold entities (what an interview that already knows the area would grant) with one anchor.
It tells whether `needs_split` comes from the size of the boundary or from the planner itself.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as ev

project = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
shard = tuple(map(int, sys.argv[3].split('/'))) if len(sys.argv) > 3 else (0, 1)
budget = int(sys.argv[4]) if len(sys.argv) > 4 else 24000
manifest = project / '.codebase-map/manifest.sqlite'
lexical = manifest.with_name('retrieval.sqlite')
queries = json.loads((project / '.evaluation/queries.json').read_bytes())['queries']
rows = []
with ev.open_snapshot(manifest) as store:
    table = ev.entities(store)
    corpus = ev.Corpus(project)
    for position, item in enumerate(queries):
        if position % shard[1] != shard[0]:
            continue
        gold = item['gold']
        files = sorted({table[g][0] for g in gold})
        request = ev.request_for(item['query'], manifest)
        request['read_boundary'] = files
        request['anchors'] = [{'entity_id': gold[0]}]
        authority = {'root': str(project), 'read_boundary': files, 'write_boundary': []}
        indexes = {'retrieval': str(lexical)}
        recipient = {'id': 'probe', 'available_tokens': budget, 'reserve_tokens': 0, 'max_chars': budget, 'max_evaluations': 2000}
        started = time.perf_counter()
        row = {'id': item['id'], 'files': files, 'gold': len(gold)}
        try:
            plan = ev.scope.prepare_scope(request, authority=authority, indexes=indexes)
            plan = ev.scope.advance_scope(plan, request, authority=authority, indexes=indexes, max_steps=100)
            packet = ev.packets.build_packet(plan, request, authority=authority, recipient=recipient, indexes=indexes)
            row.update(status=packet['status'], plan_status=plan['status'], localized=plan['localized'],
                       analysis=len({r['entity_id'] for r in plan['analysis']}), chars=len(packet['input'] or ''),
                       **ev.coverage(ev.packet_lines(packet), gold, table))
        except ValueError as error:
            row['error'] = str(error)[:200]
        row['seconds'] = round(time.perf_counter() - started, 1)
        rows.append(row)
output.write_text(json.dumps({'budget': budget, 'rows': rows}, indent=1) + '\n', encoding='utf8')
print(json.dumps([{k: r.get(k) for k in ('id', 'status', 'localized', 'analysis', 'chars', 'full', 'seconds')} for r in rows]))
