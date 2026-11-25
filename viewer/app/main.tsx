// The App page: a repository, its analysis, its graph and the questions to the engine, over the local server. The window is
// Imago's, with the screens as its views; the app has one context at a time, so there is no sidebar.
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { ComponentType, ReactNode } from 'react';
import { flushSync } from 'react-dom';
import { AppWindow, focusContent, ScreenBoundary, startApp, useFocusKept, useNotify, useWindow } from '@acaprino/imago';
import type { AppView } from '@acaprino/imago';
import { useMedia } from '@acaprino/sigrid';
import { Badge, Cluster, Column, Heading, Icon, Progress, Spacer, Text } from '@acaprino/sigrid/primitives';
import { Inspector } from '@acaprino/sigrid/layout';
import { useCommand } from '@acaprino/sigrid/assemblies';
import '@acaprino/sigrid/styles.css';
import '@acaprino/sigrid/graph.css';
import { Mark } from '../src/mark.tsx';
import { DAODAN } from '../src/page.ts';
import { plural } from '../src/words.ts';
import { analysisActions, AnalysisScreen } from './analysis.tsx';
import { engineActions, EngineScreen } from './engine-screen.tsx';
import { FrameContext } from './frame.tsx';
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
type Screen = AppView<Place> & { Screen: ComponentType; actions: (s: Snapshot) => ReactNode };
const PLACES: Screen[] = [
  { id: 'analysis', label: 'Analisi', icon: 'layers', command: 'Vai ad Analisi', Screen: AnalysisScreen, actions: analysisActions },
  { id: 'graph', label: 'Grafo', icon: 'graph', command: 'Vai al Grafo', Screen: GraphScreen, actions: graphActions },
  { id: 'engine', label: 'Motore e domande', icon: 'ai', command: 'Vai a Motore e domande', Screen: EngineScreen, actions: engineActions },
];

// Whether the focus is in the details, beside the content or over it, or in the palette that closes them.
const inDetails = () => document.activeElement?.closest('aside, [role="dialog"]') != null;

// What the screens share. It changes with the details alone, so an event of the run draws again only what reads it.
// `leave`: the details of a screen go with it, and the focus stays where the person is.
function useShared(): { frame: Frame; leave: () => void } {
  const [detail, setDetail] = useState<Detail | null>(null);
  const [field, search] = useState<HTMLInputElement | null>(null);
  const reveal = useRef<(() => void) | null>(null);
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
  const leave = useCallback(() => setDetail(null), []);
  const go = useCallback((act: () => void) => {
    leave();
    act();
    focusContent();
  }, []);
  // The inspector gives the focus back to the last place outside it, or to the content; what opened the details comes first.
  useLayoutEffect(() => {
    if (detail === null) back.current?.focus({ preventScroll: true });
    back.current = null;
  }, [detail]);
  return { frame: useMemo(() => ({ search, field, reveal, detail, show, close, go }), [field, detail]), leave };
}

function App() {
  const s = useModel();
  const { frame, leave } = useShared();
  const { field, reveal, detail, close } = frame;
  const notify = useNotify(), window_ = useWindow();
  const narrow = useMedia('(width < 620px)');  // as on a phone, the status row is short
  const place = PLACES.find(item => item.id === s.kept.screen)!;
  useFocusKept(s.kept.analysisStage);
  const title = useRef('Dettaglio');
  if (detail) title.current = detail.title;  // one that closes keeps its title as it slides out
  useEffect(() => {
    window_.setTitle(document.title);  // the window's title is the page's
    model.start(notify);
  }, [notify, window_]);

  // Ctrl+F: the search of the screen in view, in sight first where its pane is hidden.
  const find = (at: HTMLInputElement) => {
    if (reveal.current) {
      focusContent();
      flushSync(reveal.current);
    }
    at.focus();
  };
  useCommand({ id: 'daodan.details.close', label: 'Chiudi dettaglio', group: 'Viste', keys: 'Escape', icon: <Icon name="close" />, when: detail !== null, run: close });

  const groups = s.graph?.nodes.length ?? 0;  // at the foot, and not on the tab: a number that changes would move the tab beside it (R14)
  const state = statusOf(s), c = ctx(s);
  // The row is announced when it changes: the percent, which changes all the time, is not heard from it but from the bars.
  const status = <>
    <Badge variant="secondary" tone={state.tone}>{state.state}</Badge>
    {state.text && <Text variant="soft">{state.text}</Text>}
    {state.percent !== null && <>
      {!narrow && <Progress aria-label="Passi completati della pipeline" value={state.percent} size="sm" inline />}
      <Text variant="strong" aria-hidden>{state.percent}%</Text>
    </>}
    {c && <><Spacer /><Text data-selectable="">{narrow ? slug(c) : `${slug(c)} · ${c.branch} · ${short(c.commit)} · run ${c.run_id}`}</Text></>}
  </>;
  return <FrameContext value={frame}>
    <AppWindow views={PLACES} view={place.id} onView={screen => { leave(); model.navigate(screen); }} search={field && (() => find(field))}
      status={status} actions={s.server && place.actions(s)}
      footer={<Text>{[serviceLine(s), groups > 0 && `${plural(groups, 'gruppo', 'gruppi')} nel grafo`].filter(Boolean).join(' · ')}</Text>}
      inspector={<Inspector title={title.current} open={detail !== null} onOpenChange={open => { if (!open) close(); }} footer={detail?.footer}>
        <Column gap="lg" data-selectable="">
          {/* The one live region: it stays while what the details are of changes, and reads the name alone. */}
          <Cluster wrap={false} align="start" aria-live="polite" aria-atomic="true">
            {detail && <><Mark image={detail.image} icon={detail.icon} /><Column><Heading size="small"><Text pre>{detail.name}</Text></Heading></Column></>}
          </Cluster>
          {detail && <ScreenBoundary key={`${detail.id} ${detail.key ?? ''}`}>{detail.content}</ScreenBoundary>}
        </Column>
      </Inspector>}>
      <place.Screen />
    </AppWindow>
  </FrameContext>;
}

startApp(DAODAN, document.getElementById('app')!, <App />);
