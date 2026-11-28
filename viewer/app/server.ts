// What the local server answers, and how the page asks it: as the map's page does, and by a stream, which takes no headers, so the
// token is in its address.
import { createHttp } from '../src/http.ts';
import type { Fetch } from '../src/http.ts';

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
// A host a tool of the project asked to reach outside the registries: its port, the address it resolves to (null where it does
// not), whether that address is in the user's own network, and the files of the project that declare it.
export type HostRequest = { host: string; port: number; address: string | null; network: boolean; declared_in: string[] };
// The requests of one tool, answered together.
export type HostGroup = { tool: string; project: string; requests: HostRequest[] };
// The one plan of the run (`codebase_map_status.plan`, `daodan snapshot plan`): the eight steps in order with their state, what a run
// may reach, the actions with theirs, and the gaps. The states and kinds are the server's closed lists (`plan.STATES`,
// `plan.ACTION_STATES`, `plan.ACTIONS`); `viewer/test/plan.json` is checked against them.
export type StepState = 'pending' | 'running' | 'done' | 'failed' | 'skipped';
export type PlanStep = {
  id: string; state: StepState; executes: 'no' | 'container'; stops: boolean; cause?: string | null; remedy?: string | null;
  started_at?: string; ended_at?: string;
};
export type ActionKind = 'read' | 'recognize' | 'model' | 'entries' | 'resolve' | 'observe' | 'explore' | 'assemble';
export type PlanAction = {
  id: string; step: string; kind: ActionKind; project_code: boolean; container: boolean;
  target: { languages?: string[]; files?: number; unit_kinds?: string[]; source?: string; technologies?: number; root?: string };
  state: StepState | 'not_possible' | 'awaiting_approval';
  tools?: string[]; network?: string[]; hosts?: string[]; gap?: string; cause?: string | null; remedy?: string | null;
};
export type Policy = {
  network: { canonical: string[]; approved: string[]; blocked: string[]; other: string; answered_in: string };
  container: { engine: string; cause?: string; remedy?: string };
};
export type PlanGap = { kind: string; detail: string; language?: string; files?: number };
export type Plan = { steps: PlanStep[]; policy: Policy; actions: PlanAction[]; gaps: PlanGap[] };
export type AppState = {
  context?: Context | null;
  job?: Job;
  run?: { pass?: Pass; progress?: RunProgress | null; plan?: Plan | null } | null;
  engine?: Engine;
  mcp?: { command: string; args: string[] } | null;
  mcp_ready?: string;
  asked?: { state: string; question?: string; cause?: string | null };
  links?: Links;
  mapped?: Mapped;
  egress?: HostGroup[];
  project?: { state: string; rev?: number | null; cause?: string | null };  // the repository's project file, written at each analysis
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
  fetch: Fetch;
  stream: (address: string) => EventSource;
  storage: () => Pick<Storage, 'getItem' | 'setItem'>;  // called inside a try: a browser may refuse it
};

export const createServer = ({ token, fetch, stream }: Host) => ({
  ...createHttp(fetch, token),
  stream: (run: string, cursors: Cursors) => stream(`/api/stream?${new URLSearchParams({
    token, max_seconds: '60', run, after: String(cursors.after), pipeline_after: String(cursors.pipeline_after), pulse_after: String(cursors.pulse_after),
  })}`),
});
