// The Codebase Map. Served by the MCP server the page lists the runs and follows the chosen run's events; served from an
// export it draws that file.
import { useEffect, useRef, useState } from 'react';
import { AppWindow, startApp, useNotify, useWindow } from '@acaprino/imago';
import type { AppView } from '@acaprino/imago';
import { Badge, Button, Column, Icon, Select, Spacer, Text } from '@acaprino/sigrid/primitives';
import type { BadgeTone } from '@acaprino/sigrid/primitives';
import { Empty } from '@acaprino/sigrid/components';
import { ToolbarButton } from '@acaprino/sigrid/layout';
import { useCommand } from '@acaprino/sigrid/assemblies';
import '@acaprino/sigrid/styles.css';
import '@acaprino/sigrid/graph.css';
import { Details } from './details.tsx';
import { parseEnvelope, readEnvelope } from './envelope.ts';
import type { Envelope, View } from './envelope.ts';
import { Explorer } from './explorer.tsx';
import { causeOf, whenFree } from './http.ts';
import { useExplorer } from './model.ts';
import type { Phase, Shown } from './model.ts';
import { projectName } from './names.ts';
import { Navigation } from './navigation.tsx';
import { OpenExport } from './openExport.tsx';
import { DAODAN } from './page.ts';
import { get } from './server.ts';
import { POLL_MS, Session, SessionDisclosure } from './session.tsx';
import { canEnter, shownDetails } from './state.ts';
import { Failed, Loading } from './states.tsx';
import { TOKEN } from './token.ts';
import { EVENT_LABEL, FAILURE, plural } from './words.ts';

// The views of the map: their word in the bar, their command, and the name of the content.
const VIEWS: (AppView<View> & { title: string })[] = [
  { id: 'logical', label: 'Logica', icon: 'structure', command: 'Vista logica', title: 'Mappa logica' },
  { id: 'physical', label: 'Fisica', icon: 'folder', command: 'Vista fisica', title: 'Mappa fisica' },
];
// The status row while there is no map.
const STATUS: Record<Exclude<Phase, 'ready'>, { badge?: string; tone?: BadgeTone; text: string }> = {
  none: { text: 'Nessun run' }, failed: { badge: 'Errore', tone: 'danger', text: 'Export non leggibile' }, loading: { badge: 'Lettura', tone: 'info', text: "Carico l'export…" },
};

// A finding names a project-relative file; the envelope's refs are relative to the run's target.
function fileRef(envelope: Envelope, file: string): string | null {
  const target = String(envelope.meta.target ?? '.').replace(/\/+$/, '');
  if (target === '.' || target === '') return `file:${file}`;
  return file.startsWith(`${target}/`) ? `file:${file.slice(target.length + 1)}` : null;
}

type LiveEvent = { cursor: number; timestamp: string; event: string; message: string; phase?: number };
type EventsPage = { events: LiveEvent[]; next_cursor: number; has_more: boolean };
type Run = { run_id: string; readable?: boolean };
const BUSY = 'server.busy';  // its notice
// In a window of its own the map took the App's place, and this is the way back to the screen the person left; in a browser the map is
// another tab.
function WayBack() {
  const label = "Torna all'analisi", run = () => window.location.assign(`/app/?${new URLSearchParams({ token: TOKEN })}`);
  useCommand({ id: 'daodan.analysis', label, group: 'Viste', icon: <Icon name="back" />, run });
  return <ToolbarButton label={label} icon={<Icon name="back" />} onClick={run}>{label}</ToolbarButton>;
}


function App() {
  const [envelope, setEnvelope] = useState<Envelope | null>(null);
  const [failure, setFailure] = useState('');
  const [runs, setRuns] = useState<string[] | null>(null);
  const [run, setRun] = useState(() => new URLSearchParams(window.location.search).get('run') ?? '');
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [opened, setOpened] = useState('');  // the file whose map is shown in place of the run's
  const [toShow, setToShow] = useState<Shown | null>(null);
  const [opening, setOpening] = useState(false);  // the dialog of another export
  const search = useRef<HTMLInputElement>(null);
  const model = useExplorer(envelope);
  const notify = useNotify(), window_ = useWindow();
  const { state, dispatch } = model;
  const phase: Phase = runs && !runs.length ? 'none' : failure ? 'failed' : model.ready ? 'ready' : 'loading';
  const ready = phase === 'ready';
  const detailsOpen = ready && shownDetails(state) !== null;
  const close = () => dispatch({ type: 'close' });
  // What is asked for outside the canvas is brought into its view; what is chosen on it is in view already.
  const show = (asked: Shown) => setToShow(asked);

  useCommand({ id: 'daodan.place.enter', label: "Entra nell'elemento scelto", group: 'Viste', icon: <Icon name="folderOpen" />, when: ready && canEnter(state, state.selected),
    run: () => { if (state.selected !== null) dispatch({ type: 'open', ref: state.selected }); } });
  useCommand({ id: 'daodan.place.root', label: 'Torna al sistema', group: 'Viste', icon: <Icon name="back" />, when: ready && state.scope !== null,
    run: () => dispatch({ type: 'root' }) });
  useCommand({ id: 'daodan.project.info', label: 'Informazioni sul progetto', group: 'Viste', icon: <Icon name="info" />, when: ready, run: () => dispatch({ type: 'info' }) });
  useCommand({ id: 'daodan.details.close', label: 'Chiudi dettaglio', group: 'Viste', keys: 'Escape', icon: <Icon name="close" />, when: detailsOpen, run: close });
  useEffect(() => window_.setTitle(document.title), [window_]);  // the window's title is the page's

  // That the server is busy is said once, whoever found it so: an attempt takes the place of its notice.
  const sayBusy = () => notify(FAILURE.retried, { id: BUSY });
  const read = <T,>(url: string, wanted?: () => boolean) => whenFree(() => get<T>(url), sayBusy, wanted);
  const addressOf = (id: string) => `./data/visual.json?run=${encodeURIComponent(id)}`;
  const asked = useRef(0);  // what was asked for last is what is shown: an export that comes late takes the place of nothing
  const load = (url: string) => {
    asked.current += 1;
    const mine = asked.current;
    const wanted = () => mine === asked.current;
    return read(url, wanted).then(json => {
      if (wanted()) { setEnvelope(parseEnvelope(json)); setFailure(''); }
    }).catch(reason => { if (wanted()) setFailure(causeOf(reason)); });
  };
  const listRuns = (wanted?: string) => read<{ runs: Run[] }>('./api/runs').then(json => {
    const ids = json!.runs.filter(item => item.readable).map(item => item.run_id);
    setRuns(ids);
    setRun(current => [wanted, current].find(id => id && ids.includes(id)) ?? ids[ids.length - 1] ?? '');
    if (wanted && ids.includes(wanted)) setOpened('');  // the run just made takes the place of a file too
  });
  useEffect(() => { listRuns().catch(() => load('./data/visual.json')); }, []);
  useEffect(() => {
    if (!runs || !run || opened) return;  // nothing of the run takes away a file the person opened: they go back to it by choosing it
    const address = addressOf(run);
    let cursor = 0, first = true, stopped = false, busy = false;
    setEnvelope(null); setEvents([]); load(address);
    // Reads every page the journal has, so the status line shows the latest event, not the 100th.
    const poll = async () => {
      if (busy) return;
      busy = true;
      try {
        const fresh: LiveEvent[] = [];
        for (let more = true; more && !stopped;) {
          const json = await read<EventsPage>(`./api/events?run=${encodeURIComponent(run)}&after=${cursor}`, () => !stopped);
          if (!json) return;
          fresh.push(...json.events);
          cursor = json.next_cursor;
          more = json.has_more;
        }
        if (stopped) return;
        if (fresh.length) setEvents(current => [...current, ...fresh].slice(-20));
        if (!first && fresh.some(item => item.event === 'phase_completed')) load(address);
        first = false;
      } catch { /* the next poll retries */ } finally { busy = false; }
    };
    poll();
    const timer = window.setInterval(poll, POLL_MS);
    return () => { stopped = true; window.clearInterval(timer); };
  }, [runs, run, opened]);
  const last = events[events.length - 1];
  const meta = state.envelope.meta;
  // Another export takes the place of the map shown; of a file that holds none the dialog says why.
  const openFile = async (file: File) => {
    const read = readEnvelope(await file.text());
    asked.current += 1;
    setOpened(file.name); setEnvelope(read); setFailure(''); setOpening(false);
  };
  // A finding's file: one this map does not hold changes nothing.
  const pick = (file: string) => {
    const ref = fileRef(state.envelope, file);
    if (ref) { dispatch({ type: 'select', ref }); show({ ref }); }
  };
  const session = { onPick: pick, onRun: (id: string) => { listRuns(id).catch(() => undefined); }, onBusy: sayBusy };
  const title = VIEWS.find(view => view.id === state.view)!.title;

  // The live event line is the run's, so it shows while its export is loading or unreadable too, and not beside the map of a file.
  const status = <>
    {phase === 'ready'
      ? <Text variant="soft" data-selectable="">{projectName(state.envelope)}{meta.target && meta.target !== '.' ? ` / ${String(meta.target)}` : ''} · run {String(meta.run_id ?? '')}{opened && ` · dal file ${opened}`}</Text>
      : <>{STATUS[phase].badge && <Badge tone={STATUS[phase].tone}>{STATUS[phase].badge}</Badge>}<Text variant="soft">{STATUS[phase].text}</Text></>}
    {!opened && (ready || !!runs?.length) && <><Spacer />
      <Text data-selectable="">{last ? `${last.timestamp} · ${EVENT_LABEL[last.event] ?? last.event}${last.phase == null ? '' : ` · fase ${last.phase}`}${last.message ? ` · ${last.message}` : ''}` : 'Nessun evento'}</Text></>}
  </>;
  // Which map is shown, where there are runs: the run's or, until one is chosen, that of the file opened (the status says its name).
  const runPicker = !!runs?.length && <Select size="sm" aria-label="Run" value={opened ? '' : run} placeholder="File aperto"
    onValueChange={id => { setOpened(''); setRun(id); }} options={runs.map(id => ({ value: id, label: `Run ${id}` }))} />;
  const openOther = <Button variant="ghost" size="sm" disabled={!ready} onClick={() => setOpening(true)}>Apri altro export</Button>;
  // The foot: what the whole export holds. What is in view the panel says.
  return <AppWindow views={VIEWS} view={state.view} onView={view => dispatch({ type: 'view', view })} contentLabel={title}
    search={ready ? () => search.current?.focus() : null} status={status}
    tools={window_.own && <WayBack />}
    footer={<Text>{ready ? `${plural(state.envelope.entities.length, 'entità', 'entità')} · ${plural(state.envelope.relations.length, 'relazione', 'relazioni')}` : 'Nessuna mappa'}</Text>}
    sidebar={sidebar => <Navigation model={model} phase={phase} show={show} sidebar={sidebar} />}
    inspector={<Details model={model} show={show} open={detailsOpen} close={close} />}>
    <Explorer model={model} title={title} search={search} toShow={toShow} show={show} ready={ready} runs={runPicker} openOther={openOther}>
      {!!runs?.length && <Column pad="lg"><SessionDisclosure {...session} /></Column>}
      {phase === 'none' && <Column pad="lg" gap="xl">
        <Empty title="Nessun run" description="Creane uno qui sotto, o avvia una mappa nella sessione." />
        <Session {...session} />
      </Column>}
      {phase === 'failed' && <Column pad="lg"><Failed title="Export non leggibile" cause={failure}
        retry={() => { setFailure(''); load(runs && run ? addressOf(run) : './data/visual.json'); }} /></Column>}
      {phase === 'loading' && <Column pad="lg"><Loading label="Carico l'export…" /></Column>}
    </Explorer>
    <OpenExport open={opening} onOpenChange={setOpening} onFile={openFile} />
  </AppWindow>;
}

startApp(DAODAN, document.getElementById('app')!, <App />);
