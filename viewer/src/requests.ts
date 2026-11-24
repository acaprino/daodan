// What the person asks the host session and what the session answers, in the words the page says them: pure, so it is tested.
export type Asked = { id: number; kind: string; scope: string; text: string; state: string; message?: string };
export type Finding = { file?: string; line?: number; severity?: string; title?: string; premise?: string; example?: string; request: number };
export type Question = Pick<Asked, 'kind' | 'scope' | 'text'>;

type Choice = { value: string; label: string };
export const KINDS: Choice[] = [{ value: 'review', label: 'Review' }, { value: 'map', label: 'Mappa' }];
export const SCOPES: Choice[] = [
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

const wordOf = (choices: Choice[], value: string): string => choices.find(choice => choice.value === value)?.label ?? value;
export const askedTitle = (item: Asked): string => `#${item.id} ${wordOf(KINDS, item.kind)} · ${wordOf(SCOPES, item.scope)}`;
export const askedText = (item: Asked): string => [item.text, item.message].filter(Boolean).join('\n');
export const askedState = (item: Asked): string => STATES[item.state] ?? item.state;

// The tone of a word, where Sigrid has one for what it says: the word says the same, so the tone is never alone.
export type Tone = 'danger' | 'warning' | 'success' | null;
export const askedTone = (item: Asked): Tone => (item.state === 'done' ? 'success' : null);

// A finding is as the review wrote it: what it does not say is said to be missing.
export const findingPlace = (item: Finding): string => (item.file ? `${item.file}:${item.line ?? '?'}` : 'file non indicato');
export const findingText = (item: Finding): string => [item.title ?? item.premise ?? 'senza titolo', item.example].filter(Boolean).join(' · ');
export const findingSeverity = (item: Finding): string => item.severity ?? 'gravità non indicata';
export const findingTone = (item: Finding): Tone => (['Critical', 'High'].includes(item.severity ?? '') ? 'danger' : 'warning');

export const gapText = (gap: unknown): string => (typeof gap === 'string' ? gap : JSON.stringify(gap));
