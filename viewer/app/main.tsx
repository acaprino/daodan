// The App page: a repository, its analysis, its graph and the questions to the engine, over the local server. Its frame is the
// map page's: the screens are the views of the title bar, and the app has one context at a time, so there is no sidebar.
import { StrictMode, useRef, useState } from 'react';
import type { ComponentType } from 'react';
import { createRoot } from 'react-dom/client';
import {
  applyKeptScheme, AppShell, Badge, Column, CommandPalette, CommandsProvider, Count, formatKeys, Icon, Inspector, KeyHints, Progress, Spacer, Text,
  TitleBar, Toasts, Toolbar, ToolbarBrand, ToolbarButton, ToolbarSpacer, ToolbarTab, ToolbarTabs, useCommand, useCommandPalette, useMedia,
  useSchemeCommands, WordsProvider,
} from '@acaprino/sigrid';
import type { IconName } from '@acaprino/sigrid';
import '@acaprino/sigrid/styles.css';
import '@acaprino/sigrid/graph.css';
import { LOOK } from '../src/page.ts';
import { WORDS } from '../src/words.ts';
import { analysisActions, AnalysisScreen } from './analysis.tsx';
import { engineActions, EngineScreen } from './engine-screen.tsx';
import { FrameContext } from './frame.tsx';
import type { Detail } from './frame.tsx';
import { GraphScreen } from './graph-screen.tsx';
import { short } from './repository.ts';
import { serviceLine, statusOf } from './run.ts';
import { ctx, slug } from './snapshot.ts';
import type { Place } from './storage.ts';
import { model, useModel } from './use-model.ts';

// The screens: their word in the bar, their command, and what they draw.
const PLACES: { value: Place; label: string; icon: IconName; command: string; Screen: ComponentType }[] = [
  { value: 'analysis', label: 'Analisi', icon: 'layers', command: 'Vai ad Analisi', Screen: AnalysisScreen },
  { value: 'graph', label: 'Grafo', icon: 'graph', command: 'Vai al Grafo', Screen: GraphScreen },
  { value: 'engine', label: 'Motore e domande', icon: 'ai', command: 'Vai a Motore e domande', Screen: EngineScreen },
];

function App() {
  const s = useModel();
  const [detail, show] = useState<Detail | null>(null);
  const search = useRef<HTMLInputElement>(null);
  const palette = useCommandPalette();
  // Under this width the frame is laid out as on a phone: the screens are at the foot.
  const narrow = useMedia('(width < 620px)');
  const place = PLACES.find(item => item.value === s.kept.screen)!;
  const close = () => show(null);
  const go = (value: string) => { close(); model.navigate(value as Place); };

  // Ctrl+F: the search of the screen in view; a screen without one says so.
  useCommand({ id: 'daodan.search', label: 'Cerca in questa vista', group: 'Vista', keys: 'Ctrl+F', icon: <Icon name="search" />,
    run: () => { if (search.current) search.current.focus(); else model.say('Questa schermata non ha una ricerca.'); } });
  for (const item of PLACES) {  // the list never changes, so neither does the order of the hooks
    useCommand({ id: `daodan.screen.${item.value}`, label: item.command, group: 'Schermate', icon: <Icon name={item.icon} />, checked: item === place,
      run: () => go(item.value) });
  }
  useCommand({ id: 'daodan.details.close', label: 'Chiudi dettaglio', group: 'Vista', keys: 'Escape', icon: <Icon name="close" />, when: detail !== null, run: close });
  useSchemeCommands(LOOK);

  const groups = s.graph?.nodes.length ?? 0;
  const word = (item: typeof place) => (item.value === 'graph' && groups > 0
    ? <>{item.label} <Count value={groups} label={groups === 1 ? 'gruppo' : 'gruppi'} /></> : item.label);
  const titleBar = <TitleBar><Toolbar aria-label="Daodan">
    <ToolbarBrand name="Daodan" />
    {!narrow && <ToolbarTabs aria-label="Schermate" value={place.value} onValueChange={go}>{PLACES.map(item =>
      <ToolbarTab key={item.value} value={item.value}>{word(item)}</ToolbarTab>)}</ToolbarTabs>}
    <ToolbarSpacer />
    <ToolbarButton label="Comandi" icon={<Icon name="search" />} shortcut={formatKeys('Ctrl+K')} variant="outline" onClick={() => palette.setOpen(true)}>Comandi</ToolbarButton>
  </Toolbar></TitleBar>;
  const bottomBar = narrow && <Toolbar aria-label="Schermate in basso">
    <ToolbarTabs aria-label="Schermate" value={place.value} onValueChange={go} edge="top" layout="stacked">{PLACES.map(item =>
      <ToolbarTab key={item.value} value={item.value} icon={<Icon name={item.icon} />}>{word(item)}</ToolbarTab>)}</ToolbarTabs>
  </Toolbar>;
  const state = statusOf(s), c = ctx(s);
  const status = <>
    <Badge variant="secondary">{state.state}</Badge>
    {state.text && <Text variant="soft">{state.text}</Text>}
    {state.percent !== null && <>
      {!narrow && <Progress aria-label="Passi completati della pipeline" value={state.percent} size="sm" inline />}
      <Text variant="strong">{state.percent}%</Text>
    </>}
    {c && <><Spacer /><Text data-selectable="">{narrow ? slug(c) : `${slug(c)} · ${c.branch} · ${short(c.commit)} · run ${c.run_id}`}</Text></>}
  </>;
  const footer = !narrow && <>
    <Text>{serviceLine(s)}</Text>
    <Spacer />
    <KeyHints ids={['daodan.search', { keys: 'F6', label: 'Area successiva' }]} />
  </>;
  return <FrameContext value={{ search, detail, show, close }}>
    <AppShell frame="sheet" titleBar={titleBar} status={status} actions={analysisActions(s) ?? engineActions(s)} footer={footer} bottomBar={bottomBar} contentLabel={place.label}
      inspector={<Inspector title={detail?.title ?? 'Dettaglio'} open={detail !== null} onOpenChange={open => { if (!open) close(); }} footer={detail?.footer}>
        {detail && <Column gap="lg" data-selectable="">{detail.content}</Column>}
      </Inspector>}>
      <place.Screen />
    </AppShell>
    <Toasts items={s.notices} durationMs={5000} onDismiss={model.dismiss} />
  </FrameContext>;
}

applyKeptScheme(LOOK);
model.start();
createRoot(document.getElementById('app')!).render(
  <StrictMode><WordsProvider words={WORDS}><CommandsProvider><App /><CommandPalette /></CommandsProvider></WordsProvider></StrictMode>,
);
