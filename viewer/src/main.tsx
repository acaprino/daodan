// The Codebase Map. Served by the MCP server the page lists the runs and follows the chosen run's events; served from an
// export it draws that file.
import { StrictMode, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  applyKeptScheme, AppShell, Badge, Button, Column, CommandPalette, CommandsProvider, DrawerButton, Empty, formatKeys, Icon, KeyHints, Note,
  Progress, Select, Spacer, Text, TitleBar, Toasts, Toolbar, ToolbarBrand, ToolbarButton, ToolbarSpacer, ToolbarTab, ToolbarTabs, useCommand,
  useCommandPalette, useMedia, useSchemeCommands, WordsProvider,
} from '@acaprino/sigrid';
import type { IconName, ToastItem } from '@acaprino/sigrid';
import type { GraphCanvasHandle } from '@acaprino/sigrid/graph';
import '@acaprino/sigrid/styles.css';
import '@acaprino/sigrid/graph.css';
import { Details } from './details.tsx';
import { parseEnvelope } from './envelope.ts';
import type { Envelope, View } from './envelope.ts';
import { Explorer } from './explorer.tsx';
import { useExplorer } from './model.ts';
import type { Phase } from './model.ts';
import { counted, projectName } from './names.ts';
import { Navigation } from './navigation.tsx';
import { OpenExport } from './openExport.tsx';
import { LOOK } from './page.ts';
import { getJson, POLL_MS, Session, SessionDisclosure } from './session.tsx';
import { shownDetails } from './state.ts';
import { WORDS } from './words.ts';

// The views of the map: their word in the bar, their command, and the name of the content.
const VIEWS: { value: View; label: string; icon: IconName; command: string; title: string }[] = [
  { value: 'logical', label: 'Logica', icon: 'structure', command: 'Vista logica', title: 'Mappa logica' },
  { value: 'physical', label: 'Fisica', icon: 'folder', command: 'Vista fisica', title: 'Mappa fisica' },
];
// The status row while there is no map.
const STATUS: Record<Exclude<Phase, 'ready'>, { badge?: string; text: string }> = {
  none: { text: 'Nessun run' }, failed: { badge: 'Errore', text: 'Export non leggibile' }, loading: { badge: 'Lettura', text: "Carico l'export…" },
};

// A finding names a project-relative file; the envelope's refs are relative to the run's target.
function fileRef(envelope: Envelope, file: string): string | null {
  const target = String(envelope.meta.target ?? '.').replace(/\/+$/, '');
  if (target === '.' || target === '') return `file:${file}`;
  return file.startsWith(`${target}/`) ? `file:${file.slice(target.length + 1)}` : null;
}

type LiveEvent = { cursor: number; timestamp: string; event: string; message: string; phase?: number };
function App() {
  const [envelope, setEnvelope] = useState<Envelope | null>(null);
  const [failure, setFailure] = useState('');
  const [runs, setRuns] = useState<string[] | null>(null);
  const [run, setRun] = useState(() => new URLSearchParams(window.location.search).get('run') ?? '');
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [pick, setPick] = useState<{ file: string } | null>(null);
  const [menu, setMenu] = useState(false);
  const [opening, setOpening] = useState(false);  // the dialog of another export
  const [notices, setNotices] = useState<ToastItem[]>([]);
  const noticeId = useRef(0);  // not crypto.randomUUID, which a page served over plain http does not have
  const search = useRef<HTMLInputElement>(null);
  const canvas = useRef<GraphCanvasHandle>(null);
  const model = useExplorer(envelope);
  const palette = useCommandPalette();
  // Under this width the frame is laid out as on a phone: the sidebar is a drawer and the views are at the foot.
  const narrow = useMedia('(width < 620px)');
  const { state, dispatch } = model;
  const phase: Phase = runs && !runs.length ? 'none' : failure ? 'failed' : model.ready ? 'ready' : 'loading';
  const ready = phase === 'ready';
  const detailsOpen = ready && shownDetails(state) !== null;
  const say = (text: string) => { noticeId.current += 1; const id = String(noticeId.current); setNotices(list => [...list, { id, text }]); };
  const close = () => dispatch({ type: 'close' });
  // What is chosen outside the canvas is brought into its view; what is chosen on it is in view already.
  const show = (ref: string) => canvas.current?.focus(model.projection.owners[ref] ?? []);

  // Ctrl+F: the search of the map in view; a page that shows no map has none.
  useCommand({ id: 'daodan.search', label: 'Cerca in questa vista', group: 'Vista', keys: 'Ctrl+F', icon: <Icon name="search" />,
    run: () => { if (ready) search.current?.focus(); else say('Questa vista non ha una ricerca.'); } });
  for (const view of VIEWS) {  // the list never changes, so neither does the order of the hooks
    useCommand({ id: `daodan.view.${view.value}`, label: view.command, group: 'Vista', icon: <Icon name={view.icon} />, checked: state.view === view.value,
      run: () => dispatch({ type: 'view', view: view.value }) });
  }
  useCommand({ id: 'daodan.place.root', label: 'Torna al sistema', group: 'Vista', icon: <Icon name="back" />, when: ready && state.scope !== null,
    run: () => dispatch({ type: 'root' }) });
  useCommand({ id: 'daodan.project.info', label: 'Informazioni sul progetto', group: 'Vista', icon: <Icon name="info" />, when: ready, run: () => dispatch({ type: 'info' }) });
  useCommand({ id: 'daodan.details.close', label: 'Chiudi dettaglio', group: 'Vista', keys: 'Escape', icon: <Icon name="close" />, when: detailsOpen, run: close });
  useSchemeCommands(LOOK);

  useEffect(() => {
    const ref = pick && envelope && fileRef(envelope, pick.file);
    if (ref) { model.dispatch({ type: 'select', ref }); show(ref); }
  }, [pick]);
  const addressOf = (id: string) => `./data/visual.json?run=${encodeURIComponent(id)}`;
  const load = (url: string, stale = () => false) => getJson(url).then(json => {
    if (!stale()) { setEnvelope(parseEnvelope(json)); setFailure(''); }
  }).catch(reason => { if (!stale()) setFailure(String(reason?.message ?? reason)); });
  const listRuns = (wanted?: string) => getJson('./api/runs').then(json => {
    const ids = (json.runs as { run_id: string; readable?: boolean }[]).filter(item => item.readable).map(item => item.run_id);
    setRuns(ids);
    setRun(current => [wanted, current].find(id => id && ids.includes(id)) ?? ids[ids.length - 1] ?? '');
  });
  useEffect(() => { listRuns().catch(() => load('./data/visual.json')); }, []);
  useEffect(() => {
    if (!runs || !run) return;
    const address = addressOf(run);
    let cursor = 0, first = true, stopped = false, busy = false;
    const stale = () => stopped;
    setEnvelope(null); setEvents([]); load(address, stale);
    // Reads every page the journal has, so the status line shows the latest event, not the 100th.
    const poll = async () => {
      if (busy) return;
      busy = true;
      try {
        const fresh: LiveEvent[] = [];
        for (let more = true; more && !stopped;) {
          const json = await getJson(`./api/events?run=${encodeURIComponent(run)}&after=${cursor}`);
          fresh.push(...(json.events as LiveEvent[]));
          cursor = json.next_cursor;
          more = json.has_more;
        }
        if (stopped) return;
        if (fresh.length) setEvents(current => [...current, ...fresh].slice(-20));
        if (!first && fresh.some(item => item.event === 'phase_completed')) load(address, stale);
        first = false;
      } catch { /* the next poll retries */ } finally { busy = false; }
    };
    poll();
    const timer = window.setInterval(poll, POLL_MS);
    return () => { stopped = true; window.clearInterval(timer); };
  }, [runs, run]);
  const last = events[events.length - 1];
  const meta = state.envelope.meta;
  // Another export takes the place of the map shown; of a file that holds none the dialog says why.
  const openFile = async (file: File) => {
    dispatch({ type: 'replaceEnvelope', json: parseEnvelope(JSON.parse(await file.text())) });
    setOpening(false);
  };
  const toView = (view: string) => dispatch({ type: 'view', view: view as View });
  const session = { onPick: (file: string) => setPick({ file }), onRun: (id: string) => { listRuns(id).catch(() => undefined); } };
  const title = VIEWS.find(view => view.value === state.view)!.title;

  const titleBar = <TitleBar><Toolbar aria-label="Daodan">
    <DrawerButton onOpen={() => setMenu(true)} />
    <ToolbarBrand name="Daodan" />
    {!narrow && <ToolbarTabs aria-label="Viste" value={state.view} onValueChange={toView}>{VIEWS.map(view =>
      <ToolbarTab key={view.value} value={view.value}>{view.label}</ToolbarTab>)}</ToolbarTabs>}
    <ToolbarSpacer />
    <ToolbarButton label="Comandi" icon={<Icon name="search" />} shortcut={formatKeys('Ctrl+K')} variant="outline" onClick={() => palette.setOpen(true)}>Comandi</ToolbarButton>
  </Toolbar></TitleBar>;
  const bottomBar = narrow && <Toolbar aria-label="Viste in basso">
    <ToolbarTabs aria-label="Viste" value={state.view} onValueChange={toView} edge="top" layout="stacked">{VIEWS.map(view =>
      <ToolbarTab key={view.value} value={view.value} icon={<Icon name={view.icon} />}>{view.label}</ToolbarTab>)}</ToolbarTabs>
  </Toolbar>;
  // The live event line is the run's, so it shows while its export is loading or unreadable too.
  const status = <>
    {phase === 'ready'
      ? <Text variant="soft" data-selectable="">{projectName(state.envelope)}{meta.target && meta.target !== '.' ? ` / ${String(meta.target)}` : ''} · run {String(meta.run_id ?? '')}</Text>
      : <>{STATUS[phase].badge && <Badge variant="secondary">{STATUS[phase].badge}</Badge>}<Text variant="soft">{STATUS[phase].text}</Text></>}
    {(ready || !!runs?.length) && <><Spacer />
      <Text data-selectable="">{last ? `${last.timestamp} · ${last.event}${last.phase == null ? '' : ` · fase ${last.phase}`}${last.message ? ` · ${last.message}` : ''}` : 'Nessun evento'}</Text></>}
  </>;
  // The foot: what the whole export holds (what is in view the panel says), and the keys no control in sight shows.
  const footer = !narrow && <>
    <Text>{ready ? `${counted(state.envelope.entities.length, 'entità', 'entità')} · ${counted(state.envelope.relations.length, 'relazione', 'relazioni')}` : 'Nessuna mappa'}</Text>
    <Spacer />
    <KeyHints ids={['daodan.search', { keys: 'F6', label: 'Area successiva' }]} />
  </>;
  // Which map is shown: the run, where there are runs, or the export of a file.
  const source = <>
    {!!runs?.length && <Select size="sm" aria-label="Run" value={run} onValueChange={setRun} options={runs.map(id => ({ value: id, label: `Run ${id}` }))} />}
    <Button variant="ghost" size="sm" disabled={!ready} onClick={() => setOpening(true)}>Apri altro export</Button>
  </>;
  return <>
    <AppShell frame="sheet" titleBar={titleBar} status={status} footer={footer} bottomBar={bottomBar} contentLabel={title}
      sidebar={<Navigation model={model} phase={phase} show={show} open={menu} onOpenChange={setMenu} />}
      inspector={<Details model={model} open={detailsOpen} close={close} />}>
      <Explorer model={model} title={title} search={search} canvas={canvas} ready={ready} runs={source}>
        {!!runs?.length && <Column pad="lg"><SessionDisclosure {...session} /></Column>}
        {phase === 'none' && <Column pad="lg" gap="xl">
          <Empty title="Nessun run" description="Creane uno qui sotto, o avvia una mappa nella sessione." />
          <Session {...session} />
        </Column>}
        {phase === 'failed' && <Column pad="lg"><Note tone="error" title="Export non leggibile" actions={<Button variant="outline"
          onClick={() => { setFailure(''); load(runs && run ? addressOf(run) : './data/visual.json'); }}><Icon name="refresh" />Riprova</Button>}><Text data-selectable="">{failure}</Text></Note></Column>}
        {phase === 'loading' && <Column pad="lg" aria-busy><Progress aria-label="Carico l'export…" value={null} /></Column>}
      </Explorer>
    </AppShell>
    <OpenExport open={opening} onOpenChange={setOpening} onFile={openFile} />
    <Toasts items={notices} durationMs={5000} onDismiss={id => setNotices(list => list.filter(notice => notice.id !== id))} />
  </>;
}

applyKeptScheme(LOOK);
createRoot(document.getElementById('app')!).render(
  <StrictMode><WordsProvider words={WORDS}><CommandsProvider><App /><CommandPalette /></CommandsProvider></WordsProvider></StrictMode>,
);
