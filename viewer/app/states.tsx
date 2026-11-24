// What the run and the synthesis both say: how the map of the system is, and that the graph could not be read or is empty.
import { Text } from '@acaprino/sigrid/primitives';
import { Empty, Note } from '@acaprino/sigrid/components';
import { Failed } from '../src/states.tsx';
import { mapNotice } from './run.ts';
import { model, useModel } from './use-model.ts';

export function MapNote() {
  const notice = mapNotice(useModel());
  return notice && <Note tone={notice.tone} title={notice.title}>{notice.message && <Text pre data-selectable="">{notice.message}</Text>}</Note>;
}

export function GraphFailed() {
  const { graphError } = useModel();
  return <Failed title="Grafo non disponibile." cause={graphError} retry={model.retryGraph} />;
}

// A graph the run has not written yet.
export function NoGroups({ fill }: { fill?: boolean }) {
  return <Empty fill={fill} title="Prima l’inventario, poi le relazioni."
    description="Il grafo del run non ha ancora gruppi di file. I nodi compaiono quando la pipeline scrive un artefatto." />;
}
