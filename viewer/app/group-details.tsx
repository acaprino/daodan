// The details of a group of the graph, in the inspector.
import type { ReactNode } from 'react';
import { Column, Text } from '@acaprino/sigrid';
import type { Detail } from './frame.tsx';
import { nodeFacts, nodeName, responsibilityOf } from './graph.ts';
import type { GraphNode } from './graph.ts';
import { short } from './repository.ts';
import { iconOf } from './scene.ts';
import { ctx } from './snapshot.ts';
import { useModel } from './use-model.ts';

function GroupFacts({ id }: { id: string }) {
  const s = useModel();
  const c = ctx(s), n = s.graph?.nodes.find(item => item.id === id);
  if (!c || !n) return <Text as="p" variant="muted">Non è più nel grafo di questo run.</Text>;
  return <Column>
    <Text as="p" variant="muted">{s.graph?.grouping === 'modules' ? 'Modulo' : 'Directory'} del grafo di questo run.</Text>
    <Text as="p">{responsibilityOf(n)}</Text>
    <Text as="p" variant="note">{nodeFacts(n)} · commit {short(c.commit)}</Text>
  </Column>;
}

const GROUP = 'graph.group';
export const groupDetail = (n: GraphNode, footer?: ReactNode): Detail =>
  ({ id: GROUP, key: n.id, title: 'Dettaglio del gruppo', icon: iconOf(n), name: nodeName(n), content: <GroupFacts id={n.id} />, footer });
// The group the details are of, which a canvas marks as long as they are shown.
export const groupOf = (detail: Detail | null): string | null => (detail?.id === GROUP ? detail.key ?? null : null);
