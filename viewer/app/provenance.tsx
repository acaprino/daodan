// Where the graph of the run comes from and what it does not know, in the inspector.
import { Column, Icon, Section, Text } from '@acaprino/sigrid/primitives';
import { DescriptionList, Note } from '@acaprino/sigrid/components';
import type { Detail } from './frame.tsx';
import { levelLabel } from './graph.ts';
import { short } from './repository.ts';
import { gapLines } from './run.ts';
import { ctx, number, pass, plural, slug } from './snapshot.ts';
import { useModel } from './use-model.ts';

// What the run says it does not know: facts of the run, so they are not announced. `first`: how many are in sight, the others
// being in the details.
export function Gaps({ first }: { first?: number }) {
  const gaps = gapLines(useModel());
  if (!gaps.length) return <Text as="p" variant="muted">Nessuna lacuna registrata dal run.</Text>;
  const rest = first === undefined ? 0 : Math.max(0, gaps.length - first);
  return <Column data-selectable="">
    <Note tone="warning" announce={false} title={plural(gaps.length, 'lacuna', 'lacune')} items={gaps.slice(0, first)} />
    {rest > 0 && <Text as="p" variant="note">{rest === 1 ? '1 altra lacuna' : `Altre ${number(rest)} lacune`} in «Provenienza e lacune».</Text>}
  </Column>;
}

function Provenance() {
  const s = useModel();
  const c = ctx(s), graph = s.graph, meta = graph?.meta;
  return <>
    <Text as="p" variant="muted">Dati registrati nel run selezionato.</Text>
    <DescriptionList aria-label="Dati del run" items={[
      { name: 'Repository', value: slug(c) || '—', code: true },
      { name: 'Branch e commit', value: c ? `${c.branch} · ${short(c.commit)}` : '—', code: true },
      { name: 'Run', value: c?.run_id ?? '—', code: true },
      { name: 'Grafo costruito', value: meta?.created_at || '—' },
      { name: 'File', value: number(graph?.files) },
      { name: `${levelLabel(graph)} / relazioni`, value: `${graph?.nodes.length ?? '—'} / ${graph?.edges.length ?? '—'}` },
      { name: 'Passaggio del grafo', value: pass(s).state || '—' },
      { name: 'Digest dello snapshot', value: meta?.snapshot_digest || '—', code: true },
    ]} />
    <Section title="Limiti dichiarati" level={3} icon={<Icon name="info" />} gap="md">
      <Text as="p" variant="soft">Le relazioni osservate provengono da chiamate registrate durante l’esecuzione. Le relazioni campionate provengono dal profiler. Possono esserci altre chiamate.</Text>
      <Gaps />
    </Section>
  </>;
}

// The name of the run in view, as the heading of the details that are of the whole run.
export function RunName() {
  return slug(ctx(useModel())) || '—';
}

export const PROVENANCE: Detail = { id: 'provenance', title: 'Provenienza e lacune del grafo', icon: 'info', name: <RunName />, content: <Provenance /> };
