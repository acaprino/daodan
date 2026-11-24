import { test } from 'node:test';
import assert from 'node:assert/strict';
import type { GraphEdge, GraphNode } from '../app/graph.ts';
import { iconOf, sceneOf } from '../app/scene.ts';

const node = (id: string, more: Partial<GraphNode> = {}): GraphNode => ({ id, name: id, kind: 'directory', files: [`${id}/a.ts`], location: 'internal', status: 'confirmed', group: null, ...more });
const edge = (status: string, more: Partial<GraphEdge> = {}): GraphEdge => ({ source: 'a', target: 'b', counts: { calls: 1 }, status, evidence: [], ...more });

test('a thing has its name, its facts and the icon of its kind, and no place', () => {
  const { nodes } = sceneOf({ nodes: [node('.'), node('db', { location: 'external', node_type: 'database', files: [] }), node('api', { location: 'external', files: [] })], edges: [] });
  assert.deepEqual(nodes, [
    { id: '.', label: 'radice del repository', icon: 'folder', external: false, detail: '1 file · confermato' },
    { id: 'db', label: 'db', icon: 'data', external: true, detail: 'database' },
    { id: 'api', label: 'api', icon: 'globe', external: true, detail: undefined },
  ]);
  assert.deepEqual(['file', 'symbol', 'component', 'altro'].map(kind => iconOf(node('x', { kind }))), ['file', 'code', 'structure', 'layers']);
});

test('a line says its kind by its dash and its words, and each is a line of its own', () => {
  const { edges, legend } = sceneOf({ nodes: [node('a'), node('b')], edges: [
    edge('confirmed', { counts: { calls: 2, imports: 1 } }), edge('observed'), edge('sampled'), edge('uncertain'), edge('observed', { conflict: true }),
  ] });
  assert.deepEqual(edges.map(line => [line.id, line.style, line.tone, line.label]), [
    ['0', 'solid', 'default', 'calls: 2, imports: 1'],
    ['1', 'solid', 'accent', 'calls: 1 · osservata in esecuzione'],
    ['2', 'dashed', 'accent', 'calls: 1 · campionata dal profiler'],
    ['3', 'dashed', 'warning', 'calls: 1 · incerta'],
    ['4', 'dashed', 'warning', 'calls: 1 · osservata in esecuzione · destinazioni in conflitto'],
  ]);
  assert.ok(edges.every(line => line.from === 'a' && line.to === 'b' && line.directed && line.labelShown === 'chosen' && line.points === undefined));
  assert.deepEqual(legend.map(entry => [entry.label, entry.count]), [
    ['Relazioni', 1], ['Osservata in esecuzione', 1], ['Campionata dal profiler', 1], ['Incerta o in conflitto', 2],
  ]);
  assert.deepEqual(sceneOf({ nodes: [], edges: [] }).legend, []);
});

test('the name of a layout changes with its things and its lines alone', () => {
  const key = (nodes: GraphNode[], edges: GraphEdge[]) => sceneOf({ nodes, edges }).key;
  const two = [node('a'), node('b')];
  assert.equal(key(two, [edge('confirmed')]), key([node('a', { files: [] }), node('b')], [edge('observed')]));
  assert.notEqual(key(two, []), key(two, [edge('confirmed')]));
  assert.notEqual(key(two, []), key([...two, node('c')], []));
});
