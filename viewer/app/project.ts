// The repository's project file (`.daodan`) as the App reads it: its revisions, the choices made by hand and their conflicts,
// in the words the screens show. It draws nothing and asks nothing: the model asks the server (`/api/app/project/*`).

// A field's value as the file keeps it: absent is not the same as empty.
export type Value = { present: boolean; value?: unknown };
export type Edit = { object_id: string; key: string | null; field_path: string; action: 'set' | 'release'; base_rev: number; value: Value };
export type Revision = {
  rev: number; kind: string; author: string; created_at: string; summary: string; opened: number; closed: number; edits: Edit[];
};
// Where the value that disagrees with a choice comes from: the analysis that brought it, its producer, whether it is declared by the
// project (`origin`), or that the analysis took the object away.
export type Provenance = { analysis?: number; origin?: string; producer?: string | null; object?: string };
export type Conflict = {
  conflict_id: number; detected_rev: number; resolved_rev: number | null; open: boolean; incoming: Value; provenance: Provenance;
  edit_id: number; object_id: string; key: string | null; field_path: string; base: Value; value: Value;
};
export type Project = { head: number; revisions: Revision[]; conflicts: Conflict[] };
export type Field = 'name' | 'description';
export type Keep = 'manual' | 'incoming' | 'analysis';

export const FIELDS: Record<Field, { path: string; label: string }> = {
  name: { path: '/name', label: 'Nome' }, description: { path: '/attributes/description', label: 'Descrizione' },
};
const KIND: Record<string, string> = { analysis: 'Analisi', manual: 'Modifica a mano', resolution: 'Risoluzione', import: 'Importazione' };
const ORIGIN: Record<string, string> = { analysis: 'dall’analisi', declared: 'dichiarato dal progetto', resolution: 'da una conferma' };
// The three ways out of a conflict, in the order they are offered: the person's choice first.
export const KEEPS: readonly { keep: Keep; label: string }[] = [
  { keep: 'manual', label: 'Tieni la modifica' }, { keep: 'incoming', label: 'Usa il valore in arrivo' }, { keep: 'analysis', label: 'Segui l’analisi' },
];

export const fieldLabel = (path: string) => Object.values(FIELDS).find(field => field.path === path)?.label ?? path;
export const valueText = (value: Value) =>
  !value.present ? '(assente)' : typeof value.value === 'string' ? value.value || '(vuoto)' : JSON.stringify(value.value);

export function provenanceText(provenance: Provenance): string {
  if (provenance.object === 'removed') return 'l’analisi non trova più l’oggetto';
  return [provenance.analysis !== undefined && `analisi ${provenance.analysis}`, ORIGIN[provenance.origin ?? 'analysis'] ?? provenance.origin,
    provenance.producer].filter(Boolean).join(' · ');
}

// A revision as a row of the history: what it is, who made it, when, and the fields it changed from which revision.
export function revisionRow(revision: Revision): { name: string; about: string } {
  const changed = revision.edits.map(edit => `${fieldLabel(edit.field_path)}${edit.action === 'release' ? ' torna all’analisi' : ` → ${valueText(edit.value)}`}`
    + ` (da R${edit.base_rev})`);
  return {
    name: `R${revision.rev} · ${KIND[revision.kind] ?? revision.kind} · ${revision.author}`,
    about: [revision.created_at.replace('T', ' ').replace('+00:00', ' UTC'), revision.summary, ...changed].join(' · '),
  };
}

// The revisions that changed a node or a flow of the graph (its id is the file's key), the newest first; all of them without one.
export const historyOf = (project: Project | null, key?: string): Revision[] =>
  [...(project?.revisions ?? [])].reverse().filter(revision => key === undefined || revision.edits.some(edit => edit.key === key));

export const openConflicts = (project: Project | null, key?: string): Conflict[] =>
  (project?.conflicts ?? []).filter(conflict => conflict.open && (key === undefined || conflict.key === key));

// What the person typed for a field, as the server takes it: the head it was made on, so that a change made meanwhile is refused.
export const editBody = (project: Project | null, ref: string, field: Field, value: string) =>
  ({ ref, field, value: value.trim(), ...(project && { base_rev: project.head }) });

// A path typed for «Apri» or «Salva una copia»: the file is on this computer, where the local server runs.
export const pathError = (path: string) => (path.trim() ? '' : 'Scrivi il percorso del file .daodan.');

// What the file says of itself in the state: written, or why not.
export function recordedText(state: { state: string; rev?: number | null; cause?: string | null } | undefined): string {
  if (!state || state.state === 'idle') return 'Il file di progetto si scrive alla fine dell’analisi.';
  return state.state === 'done' ? `File di progetto alla revisione ${state.rev}.` : `File di progetto non scritto: ${state.cause}`;
}
