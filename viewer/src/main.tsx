// The Codebase Map. Served by the MCP server the page lists the runs and follows the chosen run's events; served from an
// export it draws that file.
import { StrictMode, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  applyKeptScheme, AppShell, Button, Cluster, Column, CommandPalette, CommandsProvider, DrawerButton, Empty, FormField, formatKeys, Icon,
  KeyHints, Note, PALETTE_COMMAND, Progress, Select, Spacer, Text, TitleBar, Toasts, Toolbar, ToolbarBrand, ToolbarButton, ToolbarSpacer,
  ToolbarTab, ToolbarTabs, useCommand, useCommandPalette, useMedia, useSchemeCommands, WordsProvider,
} from '@acaprino/sigrid';
import type { IconName, ToastItem } from '@acaprino/sigrid';
import '@acaprino/sigrid/styles.css';
import { Details } from './details.tsx';
import { parseEnvelope } from './envelope.ts';
import type { Envelope, View } from './envelope.ts';
import { Explorer } from './explorer.tsx';
import { useExplorer } from './model.ts';
import { projectName } from './names.ts';
import { Navigation } from './navigation.tsx';
import { LOOK } from './page.ts';
import { getJson, POLL_MS, Session } from './session.tsx';
import { WORDS } from './words.ts';

const VIEWS: { value: View; label: string; icon: IconName }[] = [
  { value: 'logical', label: 'Logica', icon: 'structure' },
  { value: 'physical', label: 'Fisica', icon: 'folder' },
];

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
  const [overview, setOverview] = useState(false);
  const [menu, setMenu] = useState(false);
  const [notices, setNotices] = useState<ToastItem[]>([]);
  const noticeId = useRef(0);  // not crypto.randomUUID, which a page served over plain http does not have
  const search = useRef<HTMLInputElement>(null);
  const model = useExplorer(envelope);
  const palette = useCommandPalette();
  // Under this width the frame is laid out as on a phone: the sidebar is a drawer and the views are at the foot.
  const narrow = useMedia('(width < 620px)');
  const { state, dispatch } = model;
  const ready = !(runs && !runs.length) && !failure && model.ready;
  const detailsOpen = ready && (state.selected !== null || overview);
  const say = (text: string) => { noticeId.current += 1; const id = String(noticeId.current); setNotices(list => [...list, { id, text }]); };
  const info = () => { dispatch({ type: 'select', ref: null }); setOverview(true); };
  const close = () => { dispatch({ type: 'select', ref: null }); setOverview(false); };

  // Ctrl+F: the search of the map in view; a page that shows no map has none.
  useCommand({ id: 'daodan.search', label: 'Cerca in questa vista', group: 'Vista', keys: 'Ctrl+F', icon: <Icon name="search" />,
    run: () => { if (search.current) search.current.focus(); else say('Questa vista non ha una ricerca.'); } });
  useCommand({ id: 'daodan.view.logical', label: 'Vista logica', group: 'Vista', icon: <Icon name="structure" />, checked: state.view === 'logical',
    run: () => dispatch({ type: 'view', view: 'logical' }) });
  useCommand({ id: 'daodan.view.physical', label: 'Vista fisica', group: 'Vista', icon: <Icon name="folder" />, checked: state.view === 'physical',
    run: () => dispatch({ type: 'view', view: 'physical' }) });
  useCommand({ id: 'daodan.project.info', label: 'Informazioni sul progetto', group: 'Vista', icon: <Icon name="info" />, when: ready, run: info });
  useCommand({ id: 'daodan.details.close', label: 'Chiudi dettaglio', group: 'Vista', keys: 'Escape', icon: <Icon name="close" />, when: detailsOpen, run: close });
  useSchemeCommands(LOOK);

  useEffect(() => {
    const ref = pick && envelope && fileRef(envelope, pick.file);
    if (ref) model.dispatch({ type: 'select', ref });
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
  // shortcut: nothing calls it, until ticket 18 of the port opens another export from a dialog
  const openFile = async (file: File | undefined) => {
    if (!file) return;
    try { dispatch({ type: 'replaceEnvelope', json: JSON.parse(await file.text()) }); }
    catch (reason) { dispatch({ type: 'replaceEnvelope', json: { error: String(reason) } }); }
  };
  const noRuns = runs && !runs.length;
  const loading = !noRuns && !failure && !envelope;
  const toView = (view: string) => dispatch({ type: 'view', view: view as View });
  const onRun = (id: string) => { listRuns(id).catch(() => undefined); };

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
    <Text data-selectable="">{ready ? `${projectName(state.envelope)}${meta.target && meta.target !== '.' ? ` / ${String(meta.target)}` : ''} · run ${String(meta.run_id ?? '')}`
      : noRuns ? 'Nessun run' : failure ? 'Export non leggibile' : "Carico l'export…"}</Text>
    {(ready || (runs && !noRuns)) && <><Spacer />
      <Text data-selectable="">{last ? `${last.timestamp} · ${last.event}${last.phase == null ? '' : ` · fase ${last.phase}`}${last.message ? ` · ${last.message}` : ''}` : 'Nessun evento'}</Text></>}
  </>;
  const footer = !narrow && <>
    <Text>{ready
      ? `${state.envelope.entities.length} entità · ${state.envelope.relations.length} relazioni · ${state.envelope.flows.length} flussi · ${state.envelope.gaps.length} lacune · ${model.projection.nodes.length} nodi · ${model.projection.edges.length} relazioni visibili · ${model.data.length} collegamenti di dati (tratteggiati) · ${model.projection.counts.aggregated} dentro i gruppi${model.focus ? ` · flusso su ${model.focus.nodes.length} nodi` : ''}`
      : 'Nessuna mappa'}</Text>
    <Spacer />
    <KeyHints ids={[PALETTE_COMMAND, 'daodan.search', { keys: 'F6', label: 'Area successiva' }]} />
  </>;
  const content = noRuns
    ? <><Empty title="Nessun run" description="Creane uno qui sotto, o avvia una mappa nella sessione." /><Session onPick={() => undefined} onRun={onRun} /></>
    : <>
      {(runs || ready) && <Cluster gap="md" align="end">
        {runs && <FormField label="Run"><Select aria-label="Run" value={run} onValueChange={setRun} options={runs.map(id => ({ value: id, label: id }))} /></FormField>}
        {ready && <Button variant="outline" onClick={info}><Icon name="info" />Informazioni sul progetto</Button>}
      </Cluster>}
      {runs && <Session onPick={file => setPick({ file })} onRun={onRun} />}
      {failure ? <Note tone="error" title="Export non leggibile" actions={<Button variant="outline"
          onClick={() => { setFailure(''); load(runs && run ? addressOf(run) : './data/visual.json'); }}><Icon name="refresh" />Riprova</Button>}>{failure}</Note>
        : !envelope ? <Progress aria-label="Carico l'export…" value={null} />
        : ready && <Explorer key={run} model={model} search={search} />}
    </>;
  return <>
    <AppShell titleBar={titleBar} status={status} footer={footer} bottomBar={bottomBar}
      contentLabel={state.view === 'logical' ? 'Mappa logica' : 'Mappa fisica'}
      sidebar={<Navigation model={model} ready={ready} open={menu} onOpenChange={setMenu} />}
      inspector={<Details model={model} open={detailsOpen} close={close} />}>
      <Column gap="lg" pad="lg" aria-busy={loading}>{content}</Column>
    </AppShell>
    <Toasts items={notices} durationMs={5000} onDismiss={id => setNotices(list => list.filter(notice => notice.id !== id))} />
  </>;
}

applyKeptScheme(LOOK);
createRoot(document.getElementById('app')!).render(
  <StrictMode><WordsProvider words={WORDS}><CommandsProvider><App /><CommandPalette /></CommandsProvider></WordsProvider></StrictMode>,
);
