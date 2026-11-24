// The App page: a repository, its analysis, its graph and the questions to the engine, over the local server. Its frame is the
// map page's: the screens are the views of the title bar, and the app has one context at a time, so there is no sidebar.
import { Fragment, StrictMode, useCallback, useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { ComponentType, ReactNode } from 'react';
import { flushSync } from 'react-dom';
import { createRoot } from 'react-dom/client';
import { Badge, Cluster, Column, Count, Heading, Icon, Logo, Progress, Spacer, Text } from '@acaprino/sigrid/primitives';
import { Toasts } from '@acaprino/sigrid/components';
import { AppShell, Inspector, TitleBar, Toolbar, ToolbarBrand, ToolbarButton, ToolbarSpacer, ToolbarTab, ToolbarTabs } from '@acaprino/sigrid/layout';
import { applyKeptScheme, CommandPalette, CommandsProvider, formatKeys, KeyHints, useCommand, useCommandPalette, useSchemeCommands } from '@acaprino/sigrid/assemblies';
import { useMedia, WordsProvider } from '@acaprino/sigrid';
import type { IconName } from '@acaprino/sigrid/primitives';
import '@acaprino/sigrid/styles.css';
import '@acaprino/sigrid/graph.css';
import { LOOK } from '../src/page.ts';
import { WORDS } from '../src/words.ts';
import { analysisActions, AnalysisScreen } from './analysis.tsx';
import { engineActions, EngineScreen } from './engine-screen.tsx';
import { focusContent, FrameContext, useFocusKept } from './frame.tsx';
import type { Detail, Frame } from './frame.tsx';
import { graphActions, GraphScreen } from './graph-screen.tsx';
import { short } from './repository.ts';
import { serviceLine, statusOf } from './run.ts';
import { ctx, slug } from './snapshot.ts';
import type { Snapshot } from './snapshot.ts';
import type { Place } from './storage.ts';
import { model, useModel } from './use-model.ts';

// The screens: their word in the bar, their command, what they draw, and what is in the window's action bar once the server is read
// (null where there is nothing: an element that draws nothing would leave an empty bar).
type Screen = { value: Place; label: string; icon: IconName; command: string; Screen: ComponentType; actions: (s: Snapshot) => ReactNode };
const PLACES: Screen[] = [
  { value: 'analysis', label: 'Analisi', icon: 'layers', command: 'Vai ad Analisi', Screen: AnalysisScreen, actions: analysisActions },
  { value: 'graph', label: 'Grafo', icon: 'graph', command: 'Vai al Grafo', Screen: GraphScreen, actions: graphActions },
  { value: 'engine', label: 'Motore e domande', icon: 'ai', command: 'Vai a Motore e domande', Screen: EngineScreen, actions: engineActions },
];

// Whether the focus is in the details, beside the content or over it, or in the palette that closes them.
const inDetails = () => document.activeElement?.closest('aside, [role="dialog"]') != null;

// What the screens share. It changes with the details alone, so an event of the run draws again only what reads it.
function useShared(): Frame {
  const [detail, setDetail] = useState<Detail | null>(null);
  const search = useRef<HTMLInputElement>(null), reveal = useRef<(() => void) | null>(null);
  const opener = useRef<HTMLElement | null>(null), back = useRef<HTMLElement | null>(null);
  const show = useCallback((next: Detail) => {
    const at = document.activeElement;
    if (next.opener !== undefined) opener.current = next.opener;
    else if (!inDetails()) opener.current = at instanceof HTMLElement && at !== document.body ? at : null;
    setDetail(next);
  }, []);
  const close = useCallback(() => {
    back.current = inDetails() ? opener.current : null;
    setDetail(null);
  }, []);
  const go = useCallback((act: () => void) => {
    setDetail(null);
    act();
    focusContent();
  }, []);
  // The inspector gives the focus back to the last place outside it, or to the content; what opened the details comes first.
  useLayoutEffect(() => {
    if (detail === null) back.current?.focus({ preventScroll: true });
    back.current = null;
  }, [detail]);
  return useMemo(() => ({ search, reveal, detail, show, close, go }), [detail]);
}

function App() {
  const s = useModel();
  const frame = useShared();
  const { search, reveal, detail, close, go } = frame;
  const palette = useCommandPalette();
  // Under this width the frame is laid out as on a phone: the screens are at the foot.
  const narrow = useMedia('(width < 620px)');
  const place = PLACES.find(item => item.value === s.kept.screen)!;
  useFocusKept(s.kept.screen, s.kept.analysisStage, narrow);
  const toScreen = (value: string) => { close(); model.navigate(value as Place); };  // by its tab, which keeps the focus

  // Ctrl+F: the search of the screen in view, in sight first where its pane is hidden; a screen without one says so.
  const find = () => {
    if (!search.current || search.current.disabled) { model.say('Questa schermata non ha una ricerca.'); return; }
    if (reveal.current) {
      focusContent();
      flushSync(reveal.current);
    }
    search.current.focus();
  };
  useCommand({ id: 'daodan.search', label: 'Cerca in questa vista', group: 'Vista', keys: 'Ctrl+F', icon: <Icon name="search" />, run: find });
  for (const item of PLACES) {  // the list never changes, so neither does the order of the hooks
    useCommand({ id: `daodan.screen.${item.value}`, label: item.command, group: 'Schermate', icon: <Icon name={item.icon} />, checked: item === place,
      run: () => go(() => model.navigate(item.value)) });
  }
  useCommand({ id: 'daodan.details.close', label: 'Chiudi dettaglio', group: 'Vista', keys: 'Escape', icon: <Icon name="close" />, when: detail !== null, run: close });
  useSchemeCommands(LOOK);

  const groups = s.graph?.nodes.length ?? 0;
  const word = (item: typeof place) => (item.value === 'graph' && groups > 0
    ? <>{item.label} <Count value={groups} label={groups === 1 ? 'gruppo' : 'gruppi'} /></> : item.label);
  const titleBar = <TitleBar><Toolbar aria-label="Daodan">
    <ToolbarBrand name="Daodan" />
    {!narrow && <ToolbarTabs aria-label="Schermate" value={place.value} onValueChange={toScreen}>{PLACES.map(item =>
      <ToolbarTab key={item.value} value={item.value}>{word(item)}</ToolbarTab>)}</ToolbarTabs>}
    <ToolbarSpacer />
    <ToolbarButton label="Comandi" icon={<Icon name="search" />} shortcut={formatKeys('Ctrl+K')} variant="outline" onClick={() => palette.setOpen(true)}>Comandi</ToolbarButton>
  </Toolbar></TitleBar>;
  const bottomBar = narrow && <Toolbar aria-label="Schermate in basso">
    <ToolbarTabs aria-label="Schermate" value={place.value} onValueChange={toScreen} edge="top" layout="stacked">{PLACES.map(item =>
      <ToolbarTab key={item.value} value={item.value} icon={<Icon name={item.icon} />}>{word(item)}</ToolbarTab>)}</ToolbarTabs>
  </Toolbar>;
  const state = statusOf(s), c = ctx(s);
  // The row is announced when it changes: the percent, which changes all the time, is not heard from it but from the bars.
  const status = <>
    <Badge variant="secondary">{state.state}</Badge>
    {state.text && <Text variant="soft">{state.text}</Text>}
    {state.percent !== null && <>
      {!narrow && <Progress aria-label="Passi completati della pipeline" value={state.percent} size="sm" inline />}
      <Text variant="strong" aria-hidden>{state.percent}%</Text>
    </>}
    {c && <><Spacer /><Text data-selectable="">{narrow ? slug(c) : `${slug(c)} · ${c.branch} · ${short(c.commit)} · run ${c.run_id}`}</Text></>}
  </>;
  const footer = !narrow && <>
    <Text>{serviceLine(s)}</Text>
    <Spacer />
    <KeyHints ids={['daodan.search', { keys: 'F6', label: 'Area successiva' }]} />
  </>;
  return <FrameContext value={frame}>
    <AppShell frame="sheet" titleBar={titleBar} status={status} actions={s.server && place.actions(s)} footer={footer} bottomBar={bottomBar} contentLabel={place.label}
      inspector={<Inspector title={detail?.title ?? 'Dettaglio'} open={detail !== null} onOpenChange={open => { if (!open) close(); }} footer={detail?.footer}>
        <Column gap="lg" data-selectable="">
          {/* The one live region: it stays while what the details are of changes, and reads the name alone. */}
          <Cluster wrap={false} align="start" aria-live="polite" aria-atomic="true">
            {detail && <>{detail.image ? <Logo src={detail.image} decorative icon={detail.icon} /> : <Icon name={detail.icon} />}<Column><Heading size="small"><Text pre>{detail.name}</Text></Heading></Column></>}
          </Cluster>
          {detail && <Fragment key={`${detail.id} ${detail.key ?? ''}`}>{detail.content}</Fragment>}
        </Column>
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
