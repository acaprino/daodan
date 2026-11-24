import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildCounts, endName, graphKey, levelsName, nodeById, nodeFacts, nodeName, openWithout, proofLabel, rootOf, runtimeSummary, shownOpen, visibleGraph } from '../app/graph.ts';
import type { Graph, GraphNode } from '../app/graph.ts';
import { DEFAULTS } from '../app/storage.ts';

const node = (id: string, more: Partial<GraphNode> = {}): GraphNode => ({ id, name: id, kind: 'directory', files: [`${id}/a.ts`], location: 'internal', status: 'confirmed', group: null, ...more });
const edge = (source: string, target: string, counts: Record<string, number> = { calls: 1 }) => ({ source, target, counts, evidence: [] });
// a → b → c, and d alone; b also imports d.
const graph: Graph = {
  grouping: 'directories', nodes: [node('a'), node('b'), node('c'), node('d', { location: 'external', files: [] })], open: [],
  edges: [edge('a', 'b'), edge('b', 'c'), edge('b', 'd', { imports: 2 })], files: 1234, levels: ['codice', 'infrastruttura'], unassigned: { count: 0 },
};
const seen = (filters: object) => { const g = visibleGraph(graph, { ...DEFAULTS, ...filters }); return [g.nodes.map(n => n.id).join(''), g.edges.length]; };

test('the graph in view follows the direction, the depth, the kind and the search', () => {
  assert.deepEqual(seen({}), ['abcd', 3]);
  assert.deepEqual(seen({ graphRoot: 'a', graphDepth: '1' }), ['ab', 1]);
  assert.deepEqual(seen({ graphRoot: 'a', graphDepth: '2' }), ['abcd', 3]);
  assert.deepEqual(seen({ graphRoot: 'b', graphDepth: '1', graphDirection: 'out' }), ['bcd', 2]);
  assert.deepEqual(seen({ graphRoot: 'b', graphDepth: '1', graphDirection: 'in' }), ['ab', 1]);
  assert.deepEqual(seen({ graphRoot: 'gone', graphDepth: '1' }), ['ab', 1]);  // the first node, when the one kept is gone
  assert.deepEqual(seen({ graphKind: 'imports' }), ['abcd', 1]);
  assert.deepEqual(seen({ graphKind: 'uses', graphRoot: 'a', graphDepth: '2' }), ['a', 0]);
  assert.deepEqual(seen({ graphSearch: ' B/A ' }), ['b', 0]);
});

test('a line that ends on an open group is in view with it', () => {
  const opened: Graph = { ...graph, nodes: [node('b/x', { group: 'b' }), node('a')], open: [{ id: 'b', name: 'b', parent: null }], edges: [edge('a', 'b'), edge('a', 'b/x')] };
  assert.equal(visibleGraph(opened, DEFAULTS).edges.length, 2);
  assert.deepEqual([endName(opened, 'b'), endName(opened, 'b/x'), endName(opened, 'altro')], ['b', 'b/x', 'altro']);
});

test('a group that closes closes what is open inside it, and the groups are asked on the graph screen alone', () => {
  const opened: Graph = { ...graph, open: [{ id: 'a', name: 'a', parent: null }, { id: 'a/x', name: 'x', parent: 'a' }, { id: 'a/x/y', name: 'y', parent: 'a/x' }, { id: 'b', name: 'b', parent: null }] };
  assert.deepEqual(openWithout(['a', 'a/x', 'a/x/y', 'b'], opened, 'a'), ['b']);
  assert.deepEqual(openWithout(['a', 'b'], null, 'a'), ['b']);
  const kept = { ...DEFAULTS, graphOpen: ['b', 'a'] };
  assert.deepEqual([shownOpen(kept), shownOpen({ ...kept, screen: 'graph' })], [[], ['a', 'b']]);
  assert.notEqual(graphKey('r1', kept), graphKey('r1', { ...kept, screen: 'graph' }));
  assert.notEqual(graphKey('r1', kept), graphKey('r2', kept));
});

test('the node the graph is read from is the one kept, else the one with most relations of the project', () => {
  assert.equal(rootOf(graph, 'c'), 'c');
  assert.equal(rootOf(graph, 'gone'), 'b');
  assert.equal(rootOf({ ...graph, nodes: [node('b/x', { group: 'b' }), node('a')] }, 'b'), 'b/x');
  assert.equal(rootOf({ ...graph, nodes: [] }, 'b'), '');
  assert.equal(nodeById(graph, 'gone')!.id, 'a');
});

test('nodes, lines and the whole graph are said in words', () => {
  assert.equal(nodeName({ kind: 'directory', name: '.' }), 'radice del repository');
  assert.deepEqual([nodeFacts(node('a')), nodeFacts(node('r', { location: 'external', node_type: 'database' })), nodeFacts(node('s', { kind: 'symbol', lines: [1, 5], members: ['x', 'y'] }))],
    ['1 file · confermato', 'database · esterno', 'righe 1–5 · 2 simboli']);
  assert.deepEqual([proofLabel('observed'), proofLabel('sampled', true), proofLabel('confirmed')], ['osservata in esecuzione', 'campionata dal profiler · destinazioni in conflitto', '']);
  assert.equal(runtimeSummary([{ status: 'observed' }, { status: 'observed' }, { status: 'sampled' }, { status: 'observed', conflict: true }]),
    '2 osservate in esecuzione · 1 campionata dal profiler · 1 in conflitto');
  assert.deepEqual([buildCounts(null), levelsName(graph)], ['—', 'Codice · Infrastruttura']);
  assert.match(buildCounts(graph), /^4 directory · 3 relazioni · 1\.?234 file$/);
});
