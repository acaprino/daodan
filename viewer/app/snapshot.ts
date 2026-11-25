// What the page draws from: one object, a new one at each change. `repository.ts`, `stages.ts`, `run.ts` and `graph.ts` read it.
import type { Graph } from './graph.ts';
import type { AppState, Checked, Context, Engine, Pass, RunEvent } from './server.ts';
import type { Kept } from './storage.ts';

export type Dependency = {
  name: string; scope: string; state: string; source: string; version?: string; resolved_version?: string; resolution_source?: string; direct?: boolean;
};
export type Unit = {
  id: string; name: string; kind: string; root: string; manifest?: string; status: string; parent?: string; description?: string; dependencies: Dependency[];
};
export type PremapFound = {
  files: string[]; languages: { name: string; files: number }[]; units: Unit[];
  technologies: { name: string; category: string; state?: string; version?: string; source: string; mark?: string }[];
};
export type Premap = PremapFound & { dependencies: (Dependency & { unit: string })[] };

export const ORPHAN_WRITES = Symbol('orphan writes');  // a view of its own, never sent to the server as a card's id
export type PathCard = {
  card_id: string; handler: string; kind: string; site: string; event: string; label?: string; handler_source?: string; handler_confidence?: string;
};
export type PathStep = {
  n: number; parent?: number; type?: string; from: string; to?: string; site: string; end?: string; origin?: string; resolver?: string;
  confidence?: string; conflict?: boolean; reason?: string;
};
export type PathEffect = { n: number; writer: string; site: string; effect: string; reason: string; stopped_at?: string };
export type PathResult = {
  run_id?: string; reason?: string; offset: number; count: number; next_offset: number | null;
  card?: PathCard; cards?: PathCard[]; steps?: PathStep[]; effects?: PathEffect[]; writes?: number; reached?: number; without_entry?: number;
};
// A page of evidence: the entries (`id` null), the steps of one, or the writes without an entry. The pages before it are of the
// same run and rules.
export type PathPage = {
  run: string; id: string | typeof ORPHAN_WRITES | null; offset: number; previous: PathPage | null; result?: PathResult; error?: string;
};

export type Call = { source: string; target: string; status?: string; conflict?: boolean; evidence: { path: string; line?: number }[] };
// The symbols and the calls of the file in the details, asked when it is chosen.
export type Symbols = {
  file: string; loading?: boolean; error?: string; symbols?: { id: string; name: string; lines?: number[]; freshness?: string }[]; calls?: Call[];
};

export type EngineDraft = Partial<Engine> & { api_key: string };
export type EngineWork = 'save' | 'probe' | 'forget';
export type Asked = { state: string; text: string; tools: string[]; cause: string | null };

export type Snapshot = Readonly<{
  kept: Kept;
  server: AppState | null; serverError: string;
  checked: Checked | null; checkedUrl: string; branch: string; checking: boolean; checkError: string;
  selecting: boolean; selectError: string;
  premap: Premap | null; premapError: string;
  graph: Graph | null; graphError: string; graphLoading: boolean;
  groupWanted: boolean;  // the graph screen is to show the details of the group it is read from: the person came there, or chose it
  pathPage: PathPage | null;
  symbols: Symbols | null;
  events: readonly RunEvent[];
  engineDraft: EngineDraft | null; engineSaid: string; engineTone: '' | 'good' | 'bad'; engineBusy: readonly EngineWork[];
  question: string; asked: Asked | null;
}>;

type Run = Pick<Snapshot, 'server'>;
const FINAL: readonly unknown[] = ['fresh', 'unavailable', 'failed', 'off'];
export const ctx = (s: Run): Context | null => s.server?.context ?? null;
export const slug = (c: Context | null) => (c ? `${c.repository.owner}/${c.repository.name}` : '');
export const pass = (s: Run): Pass => s.server?.run?.pass ?? {};
export const complete = (s: Run) => ctx(s) !== null && FINAL.includes(pass(s).state);  // the pipeline is over, well or not
export const viewingPaths = (s: Pick<Snapshot, 'kept' | 'server'>) =>
  s.kept.screen === 'analysis' && s.kept.analysisStage === 'synthesis' && complete(s);
