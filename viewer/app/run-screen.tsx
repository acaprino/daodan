// The run: how far its steps are, what is missing and why, the graph as it takes shape, and what happened.
import { useMemo, useState } from 'react';
import { Badge, Button, Cluster, Column, Icon, Progress, ScrollArea, Section, Text } from '@acaprino/sigrid/primitives';
import { Disclosure, Note } from '@acaprino/sigrid/components';
import type { IconName } from '@acaprino/sigrid/primitives';
import { plural } from '../src/words.ts';
import { ScreenPanel, useFrame } from './frame.tsx';
import { Preview } from './preview.tsx';
import { short } from './repository.ts';
import { linksNote, logItems, passAlert, runBar, runCount, runHelp, runPhaseLabel, statusLabel, steps } from './run.ts';
import type { LogItem, StepStatus } from './run.ts';
import { complete, ctx, pass, slug } from './snapshot.ts';
import { MapNote } from './states.tsx';
import { model, useModel } from './use-model.ts';

// The synthesis is what the run leads to: its button waits until the pipeline is over.
export function RunActions() {
  const s = useModel();
  return <>
    <Button variant="outline" asChild><a href={model.explorerUrl()} target="_blank" rel="noopener"><Icon name="external" />Apri l’esploratore</a></Button>
    <Button loading={!complete(s)} loadingText="Analisi in corso" onClick={() => model.selectStage('synthesis')}>Leggi sintesi</Button>
  </>;
}

const STEP_ICON: Record<StepStatus, IconName> = { done: 'check', running: 'play', failed: 'error', pending: 'clock', skipped: 'minus' };

// A list and not `Steps`, where what comes before the current one is done: here a step can fail, or wait, before one that runs.
function Pipeline() {
  const s = useModel();
  return <Column as="ol" gap="md" aria-label="Passi della pipeline" data-selectable="">{steps(s).map((step, index) =>
    <Cluster as="li" key={step.id} wrap={false} align="start" aria-current={step.status === 'running' ? 'step' : undefined}>
      <Icon name={STEP_ICON[step.status]} />
      <Column gap="xs">
        <Text variant="strong">{index + 1}. {step.label}</Text>
        <Text variant="note" pre>{step.note}</Text>
      </Column>
    </Cluster>)}</Column>;
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
      {reason && <Button variant="ghost" onClick={() => go(() => model.navigate('engine'))}><Icon name="ai" />Scegli il motore</Button>}
    </Cluster>
  </Column>;
}

function Execution() {
  const s = useModel();
  const c = ctx(s), alert = passAlert(s);
  return <Section title="Esecuzione" level={3} icon={<Icon name="tasks" />} gap="lg"
    end={<Badge variant={pass(s).state === 'failed' ? 'destructive' : 'secondary'}>{statusLabel(s)}</Badge>}>
    <Column>
      <Text as="p" variant="strong">{runPhaseLabel(s)}</Text>
      <Progress aria-label="Passi completati della pipeline" showValue {...runBar(s)} />
      <Text as="p" variant="note">{runHelp(s)}</Text>
    </Column>
    <Pipeline />
    {alert && <Note tone={alert.tone} title={alert.title}
      actions={alert.retry && <Button variant="outline" onClick={() => { model.retryPass(); }}><Icon name="play" />Riprova il passaggio</Button>}>
      <Text pre data-selectable="">{alert.message}</Text></Note>}
    <MapNote />
    <Links />
    {c && <Text as="p" variant="note" data-selectable="">Repository: {slug(c)} · {c.branch} · intero progetto</Text>}
  </Section>;
}

const LOG_ICON: Record<LogItem['type'], IconName> = { error: 'error', gap: 'alert', '': 'info' };
const FIRST = 8;  // how many events are in sight at first

function LogRow({ item }: { item: LogItem }) {
  return <Column as="li" gap="xs">
    <Cluster>
      <Icon name={LOG_ICON[item.type]} />
      <Text variant="strong">{item.title}</Text>
      {item.type && <Badge variant={item.type === 'error' ? 'destructive' : 'secondary'}>{item.type === 'error' ? 'Errore' : 'Attenzione'}</Badge>}
      {item.at && <Text variant="note"><time dateTime={item.at}>{new Date(item.at).toLocaleTimeString('it-IT')}</time></Text>}
    </Cluster>
    {item.detail && <Text variant="note" pre>{item.detail}</Text>}
  </Column>;
}

// The events, the newest first. Those in sight are announced as they come; the others are drawn only while their row is open.
function Activity() {
  const { events } = useModel();
  const [open, setOpen] = useState(false);
  const items = useMemo(() => logItems({ events }), [events]);
  const row = (item: LogItem, index: number) => <LogRow key={index} item={item} />;  // an event keeps its place in the run
  const rows = items.map(row).reverse();
  const rest = rows.slice(FIRST);
  const more = rest.length === 1 ? '1 altro evento' : `Altri ${rest.length} eventi`;
  return <Section title="Eventi e feedback" level={3} icon={<Icon name="history" />} gap="md"
    end={<Text variant="note">{plural(items.length, 'evento', 'eventi')}</Text>}>
    {!rows.length && <Text as="p" variant="muted">Nessun evento ancora.</Text>}
    <Column as="ul" gap="md" aria-label="Ultimi eventi" aria-live="polite" aria-relevant="additions" data-selectable="">{rows.slice(0, FIRST)}</Column>
    {rest.length > 0 && <Disclosure label={more} open={open} onOpenChange={setOpen}>
      {open && <ScrollArea bounded pad="xs" aria-label={more}><Column as="ul" gap="md" aria-label={more} data-selectable="">{rest}</Column></ScrollArea>}
    </Disclosure>}
  </Section>;
}

export function RunScreen() {
  const s = useModel();
  const c = ctx(s);
  return <ScreenPanel title="Analisi" subtitle={c && runCount(s)}>
    {c && <Column pad="lg" gap="xl" width="page">
      <Text as="p" variant="soft">Segui passi, analyzer, avanzamento ed eventi del run.</Text>
      <Note title={`Analisi del commit ${short(c.commit)}.`}>Avanzamento ed eventi sono quelli del run {c.run_id}. Il grafo cresce solo quando la pipeline scrive un artefatto.</Note>
      <Execution />
      <Preview />
      <Activity />
    </Column>}
  </ScreenPanel>;
}
