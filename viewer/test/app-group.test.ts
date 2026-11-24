import { test } from 'node:test';
import assert from 'node:assert/strict';
import type { Graph, GraphEdge, GraphNode, OpenGroup } from '../app/graph.ts';
import { callRows, isProven, perimeter, proofRow, recordedIn, relationRow, relationsOf, shortPath, siteOf, stateOf, symbolRows, whatIs } from '../app/group.ts';

const node = (id: string, more: Partial<GraphNode> = {}): GraphNode => ({ id, name: id, kind: 'directory', files: [`${id}/a.ts`], location: 'internal', status: 'confirmed', group: null, ...more });
const edge = (source: string, target: string, more: Partial<GraphEdge> = {}): GraphEdge => ({ source, target, counts: { calls: 1 }, status: 'confirmed', evidence: [], ...more });
const web: OpenGroup = { id: 'web', name: 'web', kind: 'directory', parent: null };
// web, open, holds ui, open, and main.ts; api calls web, and main.ts calls db.
const graph: Graph = {
  grouping: 'directories', files: 3, unassigned: { count: 0 }, open: [web, { id: 'ui', name: 'ui', parent: 'web' }],
  nodes: [node('api'), node('main.ts', { kind: 'file', group: 'web' }), node('db', { location: 'external', node_type: 'database', files: [] })],
  edges: [
    edge('api', 'web', { counts: { calls: 2, imports: 1 } }),
    edge('main.ts', 'db', { status: 'observed', evidence: [{ path: 'web/main.ts', line: 3, target: 'store.ts', kind: 'calls', key: 'save' }] }),
    edge('main.ts', 'db', { status: 'uncertain', evidence: [{ path: 'web/main.ts' }, { path: 'web/other.ts' }] }),
    edge('api', 'db', { conflict: true }),
  ],
};

test('a thing says what it is and how it is', () => {
  const [api, main, db] = graph.nodes, symbol = node('s', { kind: 'symbol', status: 'inferred' });
  assert.deepEqual([api, main, db, symbol, node('m', { kind: 'component' }), web].map(whatIs),
    ['Directory selezionata', 'File selezionato', 'Nodo esterno selezionato', 'Simbolo selezionato', 'Modulo selezionato', 'Directory selezionata']);
  assert.deepEqual([api, db, symbol, node('x', { location: 'external' }), web].map(stateOf),
    ['confermato', 'Dipendenza esterna · database', 'inferito', 'Dipendenza esterna', 'aperto sul posto']);
});

test('its perimeter is its files, or its lines, or what it holds open', () => {
  const values = (thing: GraphNode | OpenGroup) => perimeter(graph, thing).map(fact => [fact.name, fact.value].join(': '));
  assert.deepEqual(values(graph.nodes[0]), ['File assegnati: 1', 'Relazioni nel grafo: 2', 'Provenienza: Directory del checkout']);
  assert.deepEqual(values(node('s', { kind: 'symbol', lines: [1, 5], members: ['t'] })),
    ['Righe: 1–5', 'Simboli dentro: 1', 'Relazioni nel grafo: 0', 'Provenienza: Outline del file']);
  assert.deepEqual(values(node('s', { kind: 'symbol', files: [], provenance: 'scip' })), ['Righe: —', 'Relazioni nel grafo: 0', 'Provenienza: scip']);
  assert.deepEqual(values(node('m', { kind: 'component' })).at(-1), 'Provenienza: Non registrata');
  assert.deepEqual(values(web), ['Elementi dentro: 2', 'Relazioni nel grafo: 1']);
});

test('its relations are read from where it is, and those proven at run time are apart', () => {
  assert.deepEqual(relationsOf(graph, 'web').map(item => relationRow(graph, 'web', item)), [{ name: '← api', about: 'calls: 2, imports: 1' }]);
  assert.deepEqual(relationsOf(graph, 'api').map(item => relationRow(graph, 'api', item)),
    [{ name: '→ web', about: 'calls: 2, imports: 1' }, { name: '→ db', about: 'calls: 1 · destinazioni in conflitto' }]);
  assert.deepEqual(graph.edges.map(isProven), [false, true, false, true]);
  assert.deepEqual(graph.edges.filter(isProven).map(item => proofRow(graph, item).name),
    ['main.ts → db · osservata in esecuzione', 'api → db · destinazioni in conflitto']);
});

test('a file says the relations recorded in it, or that name it', () => {
  assert.deepEqual(recordedIn(graph, 'web/main.ts'), [
    { name: 'main.ts → db', about: 'calls · save · osservata in esecuzione · riga 3 · store.ts' },
    { name: 'main.ts → db', about: 'incerta' },
  ]);
  assert.deepEqual(recordedIn(graph, 'store.ts'), [{ name: 'main.ts → db', about: 'calls · save · osservata in esecuzione · riga 3' }]);
  assert.deepEqual(recordedIn(graph, 'README.md'), []);
  assert.deepEqual([siteOf({ path: 'a.ts', line: 4 }), siteOf({ path: 'a.ts' }), shortPath('src/lib/util.ts'), shortPath('a.ts')], ['a.ts:4', 'a.ts', 'lib/util.ts', 'a.ts']);
});

test('the symbols of a file and the calls among them are said with their lines', () => {
  const symbols = { file: 'file:a.ts', symbols: [{ id: 'a.ts::save', name: 'save', lines: [1, 5], freshness: 'fresh' }, { id: 'a.ts::x', name: 'x' }],
    calls: [{ source: 'a.ts::save', target: 'file:src/b.ts', status: 'sampled', evidence: [{ path: 'src/a.ts', line: 2 }, { path: 'src/a.ts', line: 4 }] }] };
  assert.deepEqual(symbolRows(symbols), [{ name: 'save', about: 'righe 1–5 · scheda aggiornata' }, { name: 'x', about: '' }]);
  assert.deepEqual(callRows(symbols), [{ name: 'save → src/b.ts', about: 'a.ts:2, a.ts:4 · campionata dal profiler' }]);
  assert.deepEqual([symbolRows({ file: 'f', loading: true }), callRows({ file: 'f', error: 'x' })], [[], []]);
});
