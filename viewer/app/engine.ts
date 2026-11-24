// The engine and the questions, in words: the engines to choose from, the key, how a question goes, the tools its answer took.
import { askReason, isAsking } from './run.ts';
import type { AppState, Engine } from './server.ts';
import type { Snapshot } from './snapshot.ts';

export const NO_ENGINE = 'none';  // the choice of no engine: a select takes an empty value as no choice at all
const ENGINE: Record<string, string> = {
  openai: 'Endpoint compatibile OpenAI', claude: 'Claude Code (riga di comando)', codex: 'Codex (riga di comando)',
};
export const engineOptions = (engines: readonly string[] = []) =>
  [{ value: NO_ENGINE, label: 'Nessuno' }, ...engines.map(value => ({ value, label: ENGINE[value] ?? value }))];
// Only an endpoint has an address, a model and a key: a command line has its own.
export const needsEndpoint = (engine: string | null | undefined) => engine === 'openai';
export const hasKey = (engine: Pick<Engine, 'api_key'> | undefined) => engine?.api_key === 'set';
export const keyHelp = (engine: Pick<Engine, 'api_key'> | undefined) =>
  (hasKey(engine) ? 'Chiave impostata: lasciare vuoto per tenerla.' : 'Va nel deposito delle credenziali del sistema.');

const ASKED: Record<string, string> = {
  running: 'in corso', done: 'conclusa', failed: 'non riuscita', cancelled: 'interrotta', no_engine: 'senza motore',
};
export const askedWord = (state: string) => ASKED[state] ?? state;
export const askFailed = (state: string | undefined) => state !== undefined && state !== 'running' && state !== 'done';

// What is said beside the button: that the engine is at work, or why it cannot be asked.
export const askNote = (s: Pick<Snapshot, 'server' | 'asked'>) => (isAsking(s) ? 'Il motore sta rispondendo.' : askReason(s));

// The question the server has, where this page asked none; empty without one.
export const lastQuestion = (asked: AppState['asked']) =>
  (asked?.question ? [`Ultima domanda: ${asked.question}`, askedWord(asked.state), asked.cause].filter(Boolean).join(' · ') : '');

// A tool of an answer: its name, and what it was given.
export function toolUse(tool: string) {
  const at = tool.indexOf(' ');
  return { name: at < 0 ? tool : tool.slice(0, at), value: at < 0 ? '' : tool.slice(at + 1), code: true };
}

const NOT_READY = 'not ready: ';  // and the cause
const readiness = (ready = '') => (ready === 'ready' ? 'pronti' : ready === 'not prepared' ? 'non preparati'
  : ready.startsWith(NOT_READY) ? `non pronti: ${ready.slice(NOT_READY.length)}` : ready);
// The server of the operations, for a session of the person's own.
export const mcpFacts = (server: Pick<AppState, 'mcp' | 'mcp_ready'>) => (server.mcp ? [
  { name: 'Comando', value: [server.mcp.command, ...server.mcp.args].join(' '), code: true },
  { name: 'Pacchetti del server', value: readiness(server.mcp_ready) },
] : null);
