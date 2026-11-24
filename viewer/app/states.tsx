// What the run and the synthesis both say: how the map of the system is, and that something is being read or could not be.
import { Button, Column, Empty, Icon, Note, Progress, Text } from '@acaprino/sigrid';
import { focusContent } from './frame.tsx';
import { mapNotice } from './run.ts';
import { model, useModel } from './use-model.ts';

export function MapNote() {
  const notice = mapNotice(useModel());
  return notice && <Note tone={notice.tone} title={notice.title}>{notice.message && <Text pre data-selectable="">{notice.message}</Text>}</Note>;
}

export function Loading({ label }: { label: string }) {
  return <Column aria-busy><Progress aria-label={label} value={null} /></Column>;
}

// What could not be read, and why. The note goes when it is asked again, and its button with it: the focus goes to the content, unless
// `retry` takes it nearer.
export function Failed({ title, cause, retry }: { title: string; cause: string; retry: () => void }) {
  const again = () => { focusContent(); retry(); };
  return <Note tone="error" title={title} actions={<Button variant="outline" onClick={again}><Icon name="refresh" />Riprova</Button>}>
    <Text pre data-selectable="">{cause}</Text>
  </Note>;
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
