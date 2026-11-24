// What the local server answers, and how the page asks it: the token goes in a header, and in the address of the stream,
// which takes no headers.
export type Context = { repository: { owner: string; name: string }; branch: string; commit: string; run_id: string };
export type Job = { state: string; step?: string | null; detail?: string };
export type Pass = { state?: string | null; reason?: string | null };
export type RunProgress = { step?: string; analyzer?: string; message?: string; done: number; total: number };
export type Engine = { engine: string | null; engines: string[]; base_url?: string; model?: string; api_key?: string; unkept?: string | null };
export type Links = {
  state: string; cause?: string | null; routes?: { called: number; offered: number; linked: number }; gaps?: number; stores?: number;
};
type Review = { count?: number; ids?: string[] };
export type Mapped = {
  state: string; cause?: string | null; needs_review?: { nodes?: Review; flows?: Review; refused_proposals?: Review };
  discovery?: { count?: number; effect_coverage?: { without_entry?: number } };
};
export type AppState = {
  context?: Context | null;
  job?: Job;
  run?: { pass?: Pass; progress?: RunProgress | null } | null;
  engine?: Engine;
  mcp?: { command: string; args: string[] } | null;
  mcp_ready?: string;
  asked?: { state: string; question?: string; cause?: string | null };
  links?: Links;
  mapped?: Mapped;
};

// An event of the run's own journal (`run`), or of its pipeline.
export type RunEvent = {
  run?: boolean; event?: string; timestamp?: string; message: string;
  kind?: string; step?: string; analyzer?: string; level?: string; at?: string;
  data?: { cause?: string; gap?: { detail?: string; remedy?: string }; outputs?: string[]; inputs?: string[] };
};
export type Cursors = { after: number; pipeline_after: number; pulse_after: number };
export type EventsFrame = {
  run_events: { run_id: string; next_cursor: number; events: RunEvent[]; pipeline: { next_cursor: number; events: RunEvent[] } };
  pulse: { next_cursor: number };
};

export type Checked = {
  state: 'accessible' | 'not_accessible' | 'network' | 'empty'; detail?: string;
  repository: Context['repository']; default: string; branches: { name: string; commit: string }[];
};

// What the page takes from where it runs: the browser, or a test.
export type Host = {
  token: string;
  fetch: (path: string, init?: RequestInit) => Promise<Response>;
  stream: (address: string) => EventSource;
  storage: () => Pick<Storage, 'getItem' | 'setItem'>;  // called inside a try: a browser may refuse it
};

async function answer(response: Response) {
  const body = await response.json().catch(() => ({}));
  if (response.status === 503) throw Object.assign(new Error('Daodan è occupato'), { busy: true });  // another helper holds the project now
  if (!response.ok) throw new Error(body.error || `il server ha risposto ${response.status}`);
  return body;
}

export const isBusy = (error: unknown) => (error as { busy?: boolean } | null)?.busy === true;
export const causeOf = (error: unknown) => (error instanceof Error ? error.message : String(error));

export function createServer({ token, fetch, stream }: Host) {
  const auth = { 'X-Daodan-Token': token };
  return {
    get: <T>(path: string): Promise<T> => fetch(path, { headers: auth, cache: 'no-store' }).then(answer),
    post: <T>(path: string, body: unknown): Promise<T> =>
      fetch(path, { method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(answer),
    stream: (run: string, cursors: Cursors) => stream(`/api/stream?${new URLSearchParams({
      token, max_seconds: '60', run, after: String(cursors.after), pipeline_after: String(cursors.pipeline_after), pulse_after: String(cursors.pulse_after),
    })}`),
  };
}
