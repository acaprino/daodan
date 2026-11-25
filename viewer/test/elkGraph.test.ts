import { test } from 'node:test';
import assert from 'node:assert/strict';
import Bundled from 'elkjs/lib/elk.bundled.js';
import { elkGraphOf, layoutOf } from '../src/elkGraph.ts';
import type { Layout, LayoutGraph, Point } from '../src/layoutClient.ts';

const ELK = (Bundled as unknown as { default?: typeof Bundled }).default ?? Bundled;
const TITLE = 44;  // the title of an open group, as the canvas draws it
const box = (id: string, parent?: string) => ({ id, width: 256, height: 64, parent });
// Two groups, one in the other, and what is around them; a line in a group, one out of it, one into the inner one, one to a group.
const NESTED: LayoutGraph = {
  nodes: [box('user'), box('web'), box('page', 'web'), box('api', 'web'), box('inner', 'web'), box('deep', 'inner'), box('store')],
  edges: [
    { id: 'in', source: 'page', target: 'api' }, { id: 'out', source: 'api', target: 'store' },
    { id: 'into', source: 'user', target: 'deep' }, { id: 'group', source: 'user', target: 'web' },
  ],
};
const PARENTS = new Map(NESTED.nodes.map(node => [node.id, node.parent]));
const FLAT: LayoutGraph = { nodes: ['a', 'b', 'c'].map(id => box(id)), edges: [{ id: 'ab', source: 'a', target: 'b' }] };
const laidOut = async (graph: LayoutGraph, direction: 'RIGHT' | 'DOWN') => layoutOf(await new ELK().layout(elkGraphOf(graph, direction)));

// The place of a node from the corner of the drawing: its groups' corners and its own.
function cornerOf(layout: Layout, id: string): Point {
  const own = layout.nodes[id], parent = PARENTS.get(id);
  if (parent === undefined) return { x: own.x, y: own.y };
  const base = cornerOf(layout, parent);
  return { x: base.x + own.x, y: base.y + own.y };
}
function onEdge(layout: Layout, id: string, at: Point): boolean {
  const { x, y } = cornerOf(layout, id), { width, height } = layout.nodes[id];
  const near = (a: number, b: number) => Math.abs(a - b) < 1.5;
  const within = (value: number, from: number, size: number) => value > from - 1.5 && value < from + size + 1.5;
  return ((near(at.x, x) || near(at.x, x + width)) && within(at.y, y, height)) || ((near(at.y, y) || near(at.y, y + height)) && within(at.x, x, width));
}

test('what an open group holds is asked for in it, with the options of the drawing and room for its title', () => {
  const asked = elkGraphOf(NESTED, 'DOWN');
  assert.deepEqual(asked.children!.map(node => node.id), ['user', 'web', 'store']);
  const web = asked.children![1], inner = web.children![2];
  assert.deepEqual([web.children!.map(node => node.id), inner.children!.map(node => node.id)], [['page', 'api', 'inner'], ['deep']]);
  for (const group of [web, inner]) {
    assert.deepEqual([group.width, group.height], [undefined, undefined]);  // as large as what it holds
    assert.equal(group.layoutOptions!['elk.direction'], 'DOWN');
    assert.ok(Number(/top=(\d+)/.exec(group.layoutOptions!['elk.padding'])![1]) >= TITLE);
  }
  assert.deepEqual(asked.edges!.map(edge => [edge.id, edge.sources, edge.targets]), NESTED.edges.map(edge => [edge.id, [edge.source], [edge.target]]));
  assert.equal(asked.layoutOptions!['elk.hierarchyHandling'], 'INCLUDE_CHILDREN');
  // With no open group nothing is nested, and the separate components are laid out by themselves.
  assert.equal(elkGraphOf(FLAT, 'RIGHT').layoutOptions!['elk.hierarchyHandling'], undefined);
});

for (const direction of ['RIGHT', 'DOWN'] as const) {
  test(`ELK puts each thing in its group, under the title and from its corner, and the routes from the corner of the drawing (${direction})`, async () => {
    const layout = await laidOut(NESTED, direction);
    assert.deepEqual(Object.keys(layout.nodes).sort(), NESTED.nodes.map(node => node.id).sort());
    for (const node of NESTED.nodes) {
      const { x, y, width, height } = layout.nodes[node.id];
      if (node.parent === undefined) continue;
      const group = layout.nodes[node.parent];
      assert.ok(x >= 0 && y >= TITLE && x + width <= group.width && y + height <= group.height, `${node.id} in ${node.parent}`);
    }
    for (const id of ['user', 'page', 'api', 'deep', 'store']) assert.deepEqual([layout.nodes[id].width, layout.nodes[id].height], [256, 64]);
    for (const edge of NESTED.edges) {
      const route = layout.edges[edge.id]!;
      assert.ok(route.length >= 2, edge.id);
      assert.ok(onEdge(layout, edge.source, route[0]), `${edge.id} leaves ${edge.source}`);
      assert.ok(onEdge(layout, edge.target, route[route.length - 1]), `${edge.id} reaches ${edge.target}`);
    }
    const along = direction === 'RIGHT' ? 'x' : 'y';
    assert.ok(cornerOf(layout, 'page')[along] < cornerOf(layout, 'api')[along]);
    assert.ok(cornerOf(layout, 'api')[along] < cornerOf(layout, 'store')[along]);
  });
}

test('a drawing with no open group is laid out as ever, and a line with no route has none', async () => {
  const layout = await laidOut(FLAT, 'RIGHT');
  assert.ok(layout.nodes.a.x + 256 < layout.nodes.b.x);
  assert.equal(layout.edges.ab!.length >= 2, true);
  assert.deepEqual(layoutOf({ id: 'root', edges: [{ id: 'lost', sources: ['a'], targets: ['b'] }] }), { nodes: {}, edges: { lost: null } });
});

test('a line between an open group and what it holds does not stop the layout', async () => {
  const graph: LayoutGraph = { ...NESTED, edges: [...NESTED.edges, { id: 'down', source: 'web', target: 'page' }, { id: 'up', source: 'deep', target: 'web' }] };
  const layout = await laidOut(graph, 'RIGHT');
  assert.deepEqual(Object.keys(layout.nodes).sort(), graph.nodes.map(node => node.id).sort());
});
