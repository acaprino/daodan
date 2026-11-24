// What the person asks the host session and what the session answers, in the words the page says them: pure, so it is tested.
export type Asked = { id: number; kind: string; scope: string; text: string; state: string; message?: string };
export type Finding = { file?: string; line?: number; severity?: string; title?: string; premise?: string; example?: string; request: number };
export type Question = Pick<Asked, 'kind' | 'scope' | 'text'>;

export const KINDS = [{ value: 'review', label: 'Review' }, { value: 'map', label: 'Mappa' }];
export const SCOPES = [
  { value: 'global', label: 'Globale' }, { value: 'changeset', label: 'Changeset' }, { value: 'feature', label: 'Funzionalità' },
  { value: 'prompt', label: 'Prompt libero' },
];
const STATES: Record<string, string> = { pending: 'in attesa della sessione', taken: 'in corso', done: 'conclusa' };

// A run's name, as the server takes it (RUN_ID in mcp_service.py): an identifier, so a regular expression.
const RUN_NAME = /^[a-z0-9]+(-[a-z0-9]+)*$/;

export const needsText = (scope: string): boolean => scope === 'feature' || scope === 'prompt';

// What is wrong in a form before it is sent, or nothing.
export function questionProblem({ scope, text }: Question): string {
  if (!needsText(scope) || text.trim()) return '';
  return scope === 'feature' ? 'Scrivi il nome della funzionalità.' : 'Scrivi le indicazioni per la sessione.';
}
export function runProblem(name: string): string {
  if (!name) return 'Scrivi il nome del run.';
  return RUN_NAME.test(name) ? '' : 'Solo minuscole, cifre e trattini, come in nome-del-run.';
}

export const askedTitle = (item: Asked): string => `#${item.id} ${item.kind} · ${item.scope}`;
export const askedText = (item: Asked): string => [item.text, item.message].filter(Boolean).join('\n');
export const askedState = (item: Asked): string => STATES[item.state] ?? item.state;

// A finding is as the review wrote it: what it does not say is said to be unknown.
export const findingPlace = (item: Finding): string => `${item.file ?? 'unknown'}:${item.line ?? '?'}`;
export const findingText = (item: Finding): string => [item.title ?? item.premise ?? 'unknown', item.example].filter(Boolean).join(' · ');
export const findingSeverity = (item: Finding): string => item.severity ?? 'unknown';

export const gapText = (gap: unknown): string => (typeof gap === 'string' ? gap : JSON.stringify(gap));
