import { test } from 'node:test';
import assert from 'node:assert/strict';
import type { GraphEdge, GraphNode, OpenGroup } from '../app/graph.ts';
import { iconOf, sceneOf as drawnOf } from '../app/scene.ts';

const sceneOf = (graph: Parameters<typeof drawnOf>[0]) => drawnOf(graph, mark => mark && `/mark/${mark}`);
const bare = { image: undefined, open: undefined, group: undefined };

const node = (id: string, more: Partial<GraphNode> = {}): GraphNode => ({ id, name: id, kind: 'directory', files: [`${id}/a.ts`], location: 'internal', status: 'confirmed', group: null, ...more });
const edge = (status: string, more: Partial<GraphEdge> = {}): GraphEdge => ({ source: 'a', target: 'b', counts: { calls: 1 }, status, evidence: [], ...more });

test('a thing has its name, its facts, its logo and the icon of its kind, and no place; the project comes before what is outside it', () => {
  const { nodes } = sceneOf({ nodes: [node('db', { location: 'external', node_type: 'database', mark: 'postgresql', files: [] }), node('.'), node('api', { location: 'external', files: [] })], edges: [] });
  assert.deepEqual(nodes, [
    { ...bare, id: '.', label: 'radice del repository', icon: 'folder', external: false, detail: '1 file · confermato', open: false },
    { ...bare, id: 'api', label: 'api', icon: 'globe', external: true, detail: undefined },
    { ...bare, id: 'db', label: 'db', icon: 'data', image: '/mark/postgresql', external: true, detail: 'database' },
  ]);
  assert.deepEqual(['file', 'symbol', 'component', 'altro'].map(kind => iconOf(node('x', { kind }))), ['file', 'code', 'structure', 'layers']);
});

test('a group open in place is a thing that holds what is in it, also an open group; what holds something opens', () => {
  const open: OpenGroup[] = [{ id: 'web', name: 'web', kind: 'directory', parent: null }, { id: 'web/ui', name: 'ui', kind: 'directory', parent: 'web' }];
  const { nodes, key } = sceneOf({
    nodes: [node('api'), node('web/ui/a.ts', { name: 'a.ts', kind: 'file', group: 'web/ui' }), node('web/main.ts', { name: 'main.ts', kind: 'file', group: 'web' }),
      node('s', { kind: 'symbol', files: [], lines: [1, 5] }), node('t', { kind: 'symbol', files: [], lines: [6, 9], members: ['u'] })],
    edges: [edge('confirmed', { source: 'api', target: 'web' })], open,
  });
  assert.deepEqual(nodes.map(thing => [thing.id, thing.open, thing.group]), [
    ['api', false, undefined], ['s', undefined, undefined], ['t', false, undefined],
    ['web', true, undefined], ['web/main.ts', false, 'web'], ['web/ui', true, 'web'], ['web/ui/a.ts', false, 'web/ui'],
  ]);
  assert.deepEqual(nodes.find(thing => thing.id === 'web/ui'), { id: 'web/ui', label: 'ui', icon: 'folder', image: undefined, open: true, group: 'web' });
  assert.match(key, /^api,s,t,[+]web,web\/main.ts,[+]web\/ui,web\/ui\/a.ts[|]api→web$/);  // an open group is another layout than a closed one
  // A group that is not open holds nothing: the thing is on the canvas as the others.
  assert.deepEqual(sceneOf({ nodes: [node('x', { group: 'gone' })], edges: [], open: [] }).nodes.map(thing => thing.id), ['x']);
});

test('a group has the logo of the one framework its files declare, closed and open, and a thing its own first', () => {
  const projects = [{ mark: 'react', name: 'React', category: 'framework', evidence: [] }, { mark: 'zod', name: 'Zod', category: 'library', evidence: [] }];
  const several = [...projects, { mark: 'nextjs', name: 'Next.js', category: 'framework', evidence: [] }];
  const { nodes } = sceneOf({ nodes: [node('a', { projects, mark: null }), node('b', { projects: several }), node('c', { projects, mark: 'stripe' })], edges: [],
    open: [{ id: 'd', name: 'd', parent: null, projects }] });
  assert.deepEqual(nodes.map(thing => [thing.id, thing.image]), [['a', '/mark/react'], ['b', undefined], ['c', '/mark/stripe'], ['d', '/mark/react']]);
});

test('a line says its kind by its dash and its words, and each is a line of its own', () => {
  const { edges, legend } = sceneOf({ nodes: [node('a'), node('b')], edges: [
    edge('confirmed', { counts: { calls: 2, imports: 1 } }), edge('observed'), edge('sampled'), edge('uncertain'), edge('observed', { conflict: true }),
  ] });
  assert.deepEqual(edges.map(line => [line.id, line.style, line.tone, line.label]), [
    ['0', 'solid', 'default', '2 chiamate, 1 import'],
    ['1', 'solid', 'accent', '1 chiamata · osservata in esecuzione'],
    ['2', 'dashed', 'accent', '1 chiamata · campionata dal profiler'],
    ['3', 'dashed', 'warning', '1 chiamata · incerta'],
    ['4', 'dashed', 'warning', '1 chiamata · osservata in esecuzione · destinazioni in conflitto'],
  ]);
  assert.ok(edges.every(line => line.from === 'a' && line.to === 'b' && line.directed && line.labelShown === 'chosen' && line.points === undefined));
  assert.deepEqual(legend.map(entry => [entry.label, entry.count]), [
    ['Relazioni', 1], ['Osservata in esecuzione', 1], ['Campionata dal profiler', 1], ['Prova insufficiente', 2],
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
