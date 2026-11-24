// The graph of the code: for now its frame, and the details of the group it is read from.
import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { Column, Empty, Text } from '@acaprino/sigrid';
import { ScreenPanel, useFrame } from './frame.tsx';
import { buildCounts } from './graph.ts';
import { groupDetail } from './group-details.tsx';
import { model, useModelSlice } from './use-model.ts';

// In the window's action bar.
export const graphActions = (): ReactNode => null;

// The details of the group the graph is read from, when the person has just come to the screen or chosen it: as soon as the graph has it.
function useWantedGroup() {
  const { show } = useFrame();
  const graph = useModelSlice(s => s.graph), root = useModelSlice(s => s.kept.graphRoot), wanted = useModelSlice(s => s.groupWanted);
  useEffect(() => {
    const n = wanted ? graph?.nodes.find(item => item.id === root) : undefined;
    if (!n) return;
    show(groupDetail(n));
    model.groupShown();
  }, [graph, root, wanted]);
}

// shortcut: nothing is drawn (it was on Imago, in `viewer/app/app.js` at 99665814e), until ticket 22 of the port draws it on Sigrid
export function GraphScreen() {
  const graph = useModelSlice(s => s.graph);
  useWantedGroup();
  return <ScreenPanel title="Grafo del codice" subtitle={graph && buildCounts(graph)}>
    <Column fill pad="lg" gap="lg">
      <Text as="p" variant="soft">Gruppi di file, dipendenze e percorsi del run. Ogni relazione conserva le sue evidenze.</Text>
      <Empty fill title="Grafo" description="Questa schermata è in preparazione." />
    </Column>
  </ScreenPanel>;
}
