// ELK in a worker: positions and orthogonal routes for one projection, answered with the request id.
import ELK from 'elkjs/lib/elk.bundled.js';
import type { Layout, LayoutGraph } from './layoutClient.ts';

const elk = new ELK();

self.onmessage = async (event: MessageEvent<{ id: number; graph: LayoutGraph; direction: 'RIGHT' | 'DOWN' }>) => {
  const { id, graph, direction } = event.data;
  try {
    const result = await elk.layout({
      id: 'root',
      layoutOptions: {
        'elk.algorithm': 'layered', 'elk.direction': direction, 'elk.edgeRouting': 'ORTHOGONAL',
        'elk.spacing.nodeNode': '30', 'elk.spacing.edgeEdge': '12', 'elk.spacing.edgeNode': '18',
        'elk.layered.spacing.nodeNodeBetweenLayers': '80', 'elk.layered.nodePlacement.strategy': 'BRANDES_KOEPF',
        'elk.separateConnectedComponents': 'true', 'elk.spacing.componentComponent': '48',
        'elk.aspectRatio': direction === 'DOWN' ? '0.6' : '1.8', 'elk.padding': '[top=28,left=28,bottom=28,right=28]',
      },
      children: graph.nodes.map(node => ({ id: node.id, width: node.width, height: node.height })),
      edges: graph.edges.map(edge => ({ id: edge.id, sources: [edge.source], targets: [edge.target] })),
    });
    const layout: Layout = { nodes: {}, edges: {} };
    for (const node of result.children ?? []) layout.nodes[node.id] = { x: node.x ?? 0, y: node.y ?? 0, width: node.width ?? 0, height: node.height ?? 0 };
    for (const edge of result.edges ?? []) {
      const section = edge.sections?.[0];
      layout.edges[edge.id] = section ? [section.startPoint, ...(section.bendPoints ?? []), section.endPoint] : null;
    }
    self.postMessage({ id, layout });
  } catch (error) {
    self.postMessage({ id, error: String((error as Error)?.message ?? error) });
  }
};
