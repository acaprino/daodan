// The run's links and pass, under the step of the calls; the graph as it takes shape and what happened are behind.
import { useMemo } from 'react';
import { Badge, Button, Cluster, Column, Icon, Text } from '@acaprino/sigrid/primitives';
import { Note } from '@acaprino/sigrid/components';
import type { IconName } from '@acaprino/sigrid/primitives';
import { Fold, LongFold } from '../src/listed.tsx';
import { MORE, plural } from '../src/words.ts';
import { ExplorerLink } from './explorer-link.tsx';
import { useFrame } from './frame.tsx';
import { buildCounts } from './graph.ts';
import { Preview } from './preview.tsx';
import { short } from './repository.ts';
import { ContextFold } from './repository-screen.tsx';
import { linksNote, logItems, passAlert } from './run.ts';
import type { LogItem } from './run.ts';
import { ctx } from './snapshot.ts';
import { MapNote } from './states.tsx';
import { model, useModel } from './use-model.ts';

// Why the links cannot be looked for now is in the note's text.
const WHY = 'links-why';
// The buttons are beside the note, not in it: a note whose tone changes is drawn anew, and would take the focus with it.
function Links() {
  const s = useModel();
  const { go } = useFrame();
  const { tone, title, message, running, reason } = linksNote(s);
  return <Column>
    <Note tone={tone} title={title}><Text pre id={WHY} data-selectable="">{message}</Text></Note>
    <Cluster>
      <Button variant="outline" loading={running} disabled={!running && reason !== ''} aria-describedby={WHY} onClick={() => { model.findLinks(); }}>
        <Icon name="play" />Trova i legami</Button>
      {reason && <Button variant="ghost" onClick={() => go(model.chooseEngine)}><Icon name="ai" />Scegli il motore</Button>}
    </Cluster>
  </Column>;
}

const LOG_ICON: Record<LogItem['type'], IconName> = { error: 'error', gap: 'alert', '': 'info' };
const FIRST = 8;  // how many events are in sight at first

function LogRow({ item }: { item: LogItem }) {
  return <Column as="li" gap="xs">
    <Cluster>
      <Icon name={LOG_ICON[item.type]} />
      <Text variant="strong">{item.title}</Text>
      {item.type && <Badge tone={item.type === 'error' ? 'danger' : 'warning'}>{item.type === 'error' ? 'Errore' : 'Attenzione'}</Badge>}
      {item.at && <Text variant="note"><time dateTime={item.at}>{new Date(item.at).toLocaleTimeString('it-IT')}</time></Text>}
    </Cluster>
    {item.detail && <Text variant="note" pre>{item.detail}</Text>}
  </Column>;
}

// The events, the newest first. Those in sight are announced as they come; the others are drawn only while their row is open.
function Activity() {
  const { events } = useModel();
  const items = useMemo(() => logItems({ events }), [events]);
  const row = (item: LogItem, index: number) => <LogRow key={index} item={item} />;  // an event keeps its place in the run
  const rows = items.map(row).reverse();
  const rest = rows.slice(FIRST);
  const more = MORE.events(rest.length);
  return <Fold label="Eventi e feedback" summary={plural(items.length, 'evento', 'eventi')}>
    <Column gap="md">
      {!rows.length && <Text as="p" variant="muted">Nessun evento ancora.</Text>}
      <Column as="ul" gap="md" aria-label="Ultimi eventi" aria-live="polite" aria-relevant="additions" data-selectable="">{rows.slice(0, FIRST)}</Column>
      {rest.length > 0 && <LongFold label={more}><Column as="ul" gap="md" aria-label={more} data-selectable="">{rest}</Column></LongFold>}
    </Column>
  </Fold>;
}

// The links between the modules and the pass that refines the graph of the calls, under the step of the calls: why the pass did not
// go, with «Riprova» where it failed; the graph as it takes shape and what happened are behind.
export function PassResult() {
  const s = useModel();
  const c = ctx(s), alert = passAlert(s);
  return c && <>
    {alert && <Note tone={alert.tone} title={alert.title}
      actions={alert.retry && <Button variant="outline" onClick={() => { model.retryPass(); }}><Icon name="refresh" />Riprova</Button>}>
      <Text pre data-selectable="">{alert.message}</Text></Note>}
    <MapNote />
    <Links />
    <Column gap="xs">
      <Fold label="Grafo in costruzione" summary={buildCounts(s.graph)}>
        <Column gap="md"><Preview /><Cluster><ExplorerLink /></Cluster></Column>
      </Fold>
      <Activity />
      <ContextFold />
      <Fold label="Come leggere l’avanzamento">
        <Text as="p" variant="soft" data-selectable="">Avanzamento ed eventi sono quelli del run {c.run_id} sul commit {short(c.commit)}, sull’intero progetto. Il grafo cresce solo quando la pipeline scrive un artefatto.</Text>
      </Fold>
    </Column>
  </>;
}
