// The run: how far it is, its phases as a path, what is missing and why; the graph as it takes shape and what happened are behind.
import { useEffect, useMemo, useState } from 'react';
import { Badge, Button, Cluster, Column, Icon, Progress, Split, Text } from '@acaprino/sigrid/primitives';
import { Note, Steps } from '@acaprino/sigrid/components';
import type { IconName } from '@acaprino/sigrid/primitives';
import { Fold, LongFold } from '../src/listed.tsx';
import { MORE, plural } from '../src/words.ts';
import { ExplorerLink } from './explorer-link.tsx';
import { useFrame } from './frame.tsx';
import { buildCounts } from './graph.ts';
import { Preview } from './preview.tsx';
import { short } from './repository.ts';
import { ContextFold } from './repository-screen.tsx';
import { linksNote, logItems, passAlert, phaseItems, runBar, runCount, runHelp, runPhaseLabel, statusLabel, steps } from './run.ts';
import type { LogItem } from './run.ts';
import { ctx, pass } from './snapshot.ts';
import { MapNote } from './states.tsx';
import { Step } from './step.tsx';
import { model, useModel } from './use-model.ts';

// The time, every second while a phase runs.
function useNow(running: boolean): number {
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    if (!running) return undefined;
    setNow(Date.now());
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [running]);
  return now;
}

// The phases, each with its time; the one that runs is the current one, wherever it is.
function Pipeline() {
  const s = useModel();
  const running = steps(s).findIndex(step => step.status === 'running');
  const now = useNow(running >= 0);
  return <Column data-selectable=""><Steps aria-label="Passi della pipeline" steps={phaseItems(s, now)} current={running} /></Column>;
}

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

export function RunScreen() {
  const s = useModel();
  const c = ctx(s), alert = passAlert(s);
  return <Step stage="analysis" line="La pipeline legge il codice in sei fasi."
    end={<Badge variant="secondary" tone={pass(s).state === 'failed' ? 'danger' : undefined}>{statusLabel(s)}</Badge>}>
    {c && <>
      <Column>
        <Split><Text variant="strong">{runPhaseLabel(s)}</Text><Text variant="note">{runCount(s)}</Text></Split>
        <Progress aria-label="Passi completati della pipeline" showValue {...runBar(s)} />
        <Text as="p" variant="note" data-selectable="">{runHelp(s)}</Text>
      </Column>
      {alert && <Note tone={alert.tone} title={alert.title}
        actions={alert.retry && <Button variant="outline" onClick={() => { model.retryPass(); }}><Icon name="refresh" />Riprova</Button>}>
        <Text pre data-selectable="">{alert.message}</Text></Note>}
      <Pipeline />
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
    </>}
  </Step>;
}
