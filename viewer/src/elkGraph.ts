// What ELK is asked for a drawing and what its answer means: pure, so its test asks the real ELK.
import type { ElkNode } from 'elkjs/lib/elk.bundled.js';
import type { Layout, LayoutGraph } from './layoutClient.ts';

// The room inside an open group, the title the canvas draws in its first 44px included.
const GROUP_PADDING = '[top=60,left=16,bottom=16,right=16]';

export function elkGraphOf(graph: LayoutGraph, direction: 'RIGHT' | 'DOWN'): ElkNode {
  // The same in an open group as around it: a group does not take the options of what holds it.
  const options = {
    'elk.direction': direction, 'elk.edgeRouting': 'ORTHOGONAL',
    'elk.spacing.nodeNode': '30', 'elk.spacing.edgeEdge': '12', 'elk.spacing.edgeNode': '18',
    'elk.layered.spacing.nodeNodeBetweenLayers': '80', 'elk.layered.nodePlacement.strategy': 'BRANDES_KOEPF',
  };
  const held = new Map<string | undefined, LayoutGraph['nodes']>();
  for (const node of graph.nodes) held.set(node.parent, [...(held.get(node.parent) ?? []), node]);
  const boxOf = ({ id, width, height }: LayoutGraph['nodes'][number]): ElkNode => {
    const inside = held.get(id);
    return inside ? { id, layoutOptions: { ...options, 'elk.padding': GROUP_PADDING }, children: inside.map(boxOf) } : { id, width, height };
  };
  return {
    id: 'root',
    layoutOptions: {
      ...options, 'elk.algorithm': 'layered',
      'elk.separateConnectedComponents': 'true', 'elk.spacing.componentComponent': '48',
      'elk.aspectRatio': direction === 'DOWN' ? '0.6' : '1.8', 'elk.padding': '[top=28,left=28,bottom=28,right=28]',
      // Every point of a line is from the corner of the drawing, whatever groups it goes through.
      'elk.json.edgeCoords': 'ROOT',
      // The groups are laid out with what is around them, so a line crosses their edge. Only where there is one: it costs the
      // separate components and the ratio.
      ...(graph.nodes.some(node => node.parent !== undefined) ? { 'elk.hierarchyHandling': 'INCLUDE_CHILDREN' } : {}),
    },
    children: (held.get(undefined) ?? []).map(boxOf),
    edges: graph.edges.map(edge => ({ id: edge.id, sources: [edge.source], targets: [edge.target] })),
  };
}

export function layoutOf(answer: ElkNode): Layout {
  const layout: Layout = { nodes: {}, edges: {} };
  const place = (holder: ElkNode) => {
    for (const node of holder.children ?? []) {
      layout.nodes[node.id] = { x: node.x ?? 0, y: node.y ?? 0, width: node.width ?? 0, height: node.height ?? 0 };
      place(node);
    }
  };
  place(answer);
  for (const edge of answer.edges ?? []) {
    const section = edge.sections?.[0];
    layout.edges[edge.id] = section ? [section.startPoint, ...(section.bendPoints ?? []), section.endPoint] : null;
  }
  return layout;
}
