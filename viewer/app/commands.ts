// The commands the person or the assistant stated for the folders of the project, as the state has them (`commands`): their words,
// the form that sets the person's own, and what each request to `/api/app/command` sends (`app.command`). It draws nothing.
import type { BadgeTone } from '@acaprino/sigrid/primitives';
import type { Command, CommandKind } from './server.ts';

// The three kinds (`commands.KINDS`), in the order the form offers them, with their words.
export const KINDS: readonly { value: CommandKind; label: string }[] = [
  { value: 'starts', label: 'Avvio dell’app' }, { value: 'tests', label: 'Esecuzione dei test' }, { value: 'builds', label: 'Build' },
];
const KIND = Object.fromEntries(KINDS.map(({ value, label }) => [value, label])) as Record<CommandKind, string>;

// What a command does, and where: its folder from the project's root, `.` the root.
export const titleOf = ({ kind, root }: Pick<Command, 'kind' | 'root'>) =>
  `${KIND[kind]} ${root === '.' ? 'nella radice del progetto' : `in ${root}`}`;

// The words of a command side by side, to be read: the form holds them one per line, as they are kept.
export const lineOf = (command: Pick<Command, 'argv'>) => command.argv.join(' ');

// Who stated it: the person's is confirmed, the assistant's is proposed until the person confirms it.
export function gradeOf(command: Pick<Command, 'by' | 'proposed_by'>): { badge: string; tone: BadgeTone; who: string } {
  if (command.by === 'assistant') return { badge: 'Proposto', tone: 'warning', who: 'Proposto dall’assistente: aspetta la tua conferma' };
  return { badge: 'Confermato', tone: 'success', who: command.proposed_by ? 'Proposto dall’assistente, confermato da te' : 'Impostato da te' };
}

// The facts of a kept command, in the window.
export const commandFacts = (command: Command) => [
  { name: 'Comando', value: lineOf(command), code: true },
  { name: 'Chi', value: gradeOf(command).who },
  command.runner ? { name: 'Runner', value: command.runner, code: true } : null,
  command.port !== undefined ? { name: 'Porta', value: String(command.port) } : null,
  command.surface ? { name: 'Superficie', value: command.surface, code: true } : null,
];

// What the form holds: the kind, the folder, the words one per line and the port, as written.
export type CommandDraft = { kind: CommandKind; root: string; words: string; port: string };

// The form for a kind and a folder: the words and the port of the command kept for them, where there is one (of `tests`, which
// keeps one for each runner, the first), else empty.
export function draftOf(kind: CommandKind, root: string, commands: readonly Command[] = []): CommandDraft {
  const kept = commands.find(command => command.kind === kind && command.root === root);
  return { kind, root, words: kept ? kept.argv.join('\n') : '', port: kept?.port !== undefined ? String(kept.port) : '' };
}

// The words of the form: one a line, without the spaces at their ends. A line is never split into words here: that would be a
// reader of shell written by hand (AGENTS.md, «Regola d'oro»), and the server takes the words. Sigrid's `ChipsInput` was weighed
// and does not fit: it drops a word written again in any case (`-p`, `-p`) and splits at a comma.
export const argvOf = (words: string) => words.split('\n').map(word => word.trim()).filter(Boolean);

// A port is figures alone: text with no grammar, read with a pattern. Only a start has one.
const FIGURES = /^\d+$/;
const portOf = (draft: CommandDraft) => (draft.kind === 'starts' ? draft.port.trim() : '');

export type DraftErrors = Partial<Record<'root' | 'words' | 'port', string>>;
// What is wrong in the form, by field; nothing when it can be sent. The server checks the rest: a folder outside the project.
export function draftErrors(draft: CommandDraft): DraftErrors {
  const errors: DraftErrors = {}, port = portOf(draft);
  if (!draft.root.trim()) errors.root = 'Scrivi la cartella: «.» è la radice del progetto.';
  if (!argvOf(draft.words).length) errors.words = 'Scrivi almeno una parola del comando.';
  if (port && !(FIGURES.test(port) && Number(port) >= 1 && Number(port) <= 65535)) errors.port = 'La porta è un numero da 1 a 65535.';
  return errors;
}
export const isReady = (draft: CommandDraft) => Object.keys(draftErrors(draft)).length === 0;

// The person's command takes the place of the one kept for its kind and folder (and, for the tests, its runner), with the
// surface of the start or build it replaces: the form does not show it.
export function setBody(draft: CommandDraft, commands: readonly Command[] = []) {
  const root = draft.root.trim(), port = portOf(draft);
  const surface = draft.kind === 'tests' ? undefined : commands.find(command => command.kind === draft.kind && command.root === root)?.surface;
  return {
    action: 'set' as const,
    command: { kind: draft.kind, root, argv: argvOf(draft.words), ...(port && { port: Number(port) }), ...(surface && { surface }) },
  };
}

// A kept command is found by its kind, its folder and, where it has one, its runner: the server matches the runner given.
const keyOf = ({ kind, root, runner }: Command) => ({ kind, root, ...(runner && { runner }) });
export const confirmBody = (command: Command) => ({ action: 'confirm' as const, ...keyOf(command) });
export const removeBody = (command: Command) => ({ action: 'remove' as const, ...keyOf(command) });
// What is being sent about a kept command, to mark its button.
export const workOf = (work: 'confirm' | 'remove', command: Command) => JSON.stringify([work, keyOf(command)]);

// What is said once the server has it.
export const setWords = (draft: CommandDraft) => `Comando impostato: ${titleOf({ kind: draft.kind, root: draft.root.trim() })}. Gira alla prossima analisi, nel container.`;
export const confirmedWords = (command: Command) => `Comando confermato: ${titleOf(command)}.`;
export const removedWords = (command: Command) => `Comando tolto: ${titleOf(command)}.`;
