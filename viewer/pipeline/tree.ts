// The pipeline as a path for the page: the steps in their order and, for each, what it uses for the choice made. The data is written
// from the code's declarations (`data.ts`); nothing here draws.
import type { StepItem } from '@acaprino/sigrid/components';
import type { SelectGroup } from '@acaprino/sigrid/primitives';

export type Mode = 'today' | 'plan';
// One thing a step uses. `today` and `plan` are the step it is in, in each order; `langs`, `fam` and `fw` the languages, the build
// tools and the frameworks it is for; `all`: it is for every project.
export type Row = {
  today: string; plan: string; name: string; file: string; kind: string; where: string; tool: string; does: string;
  langs: string[]; fam: string[]; fw: string[]; all: boolean; status: string | null; declared: string | null;
  when: string; when_plan: string; ver: string;
};
export type Step = { key: string; title: string; code: string; what: string; writes: string };
// A language, a build tool or a framework, with what goes with it.
export type Choice = { id: string; name: string; group: string; langs: string[]; fam: string[]; fw: string[] };
export type Data = { rows: Row[]; steps: Record<Mode, Step[]>; choices: Choice[] };
export type Fact = { name: string; value: string; code?: boolean };
// A step with what it uses for the choice made.
export type Stage = Step & { rows: Row[] };
export type Path = {
  steps: Stage[];   // the steps of the path, in their order: the first is step 1
  beside: Stage[];  // what comes after the pipeline, and what every step shares
  shown: number; boxed: number;
};

export const ALL = 'all';
export const stepId = (key: string) => `step:${key}`;
export const rowId = (row: Row) => `row:${row.name}`;
// A step of the path: what comes after the pipeline, and what every step shares, are beside it. A key of the data, not source code.
const NUMBERED = /^[sp]\d+$/;
const when = (row: Row, mode: Mode) => (mode === 'plan' ? row.when_plan : row.when);

export function uses(row: Row, choice: Choice | null): boolean {
  if (row.all || !choice) return true;
  // A framework's own tool is for that framework, whatever language the two share.
  if (row.fw.length && choice.fw.length) return row.fw.some(item => choice.fw.includes(item));
  return row.langs.some(item => choice.langs.includes(item)) || row.fam.some(item => choice.fam.includes(item))
    || row.fw.some(item => choice.fw.includes(item));
}

export function pathOf(data: Data, mode: Mode, choice: Choice | null): Path {
  const path: Path = { steps: [], beside: [], shown: 0, boxed: 0 };
  for (const step of data.steps[mode]) {
    const rows = data.rows.filter(row => row[mode] === step.key && uses(row, choice));
    path.shown += rows.length;
    path.boxed += rows.filter(row => row.where === 'container').length;
    (NUMBERED.test(step.key) ? path.steps : path.beside).push({ ...step, rows });
  }
  return path;
}

export const countOf = (rows: Row[]) => (rows.length === 1 ? '1 voce' : `${rows.length} voci`);

// The path for `Steps`, which numbers them. Each has a status of its own, so that each can be gone to: without one, the steps before
// the one on the screen would read as done and the ones after could not be chosen.
export function itemsOf(path: Path): StepItem[] {
  return path.steps.map((step): StepItem => ({ label: step.title, meta: countOf(step.rows), status: 'todo' }));
}

// The line of a thing in the list of its step: with what, when and where.
export function lineOf(row: Row, mode: Mode): { title: string; tool: string; facts: { text: string; tone?: 'strong' }[]; contained: boolean } {
  const contained = row.where === 'container';
  return {
    title: row.ver ? `${row.name} ${row.ver}` : row.name, tool: row.tool, contained,
    facts: [{ text: when(row, mode) }, { text: contained ? 'solo nel container' : "sull'host" }, ...(row.status ? [{ text: row.status, tone: 'strong' as const }] : [])],
  };
}

// The facts of a step, said at the head of its list, or of something a step uses, said in the inspector.
export function detailOf(data: Data, mode: Mode, id: string): { title: string; name: string; facts: Fact[] } | null {
  const step = data.steps[mode].find(item => stepId(item.key) === id);
  if (step) {
    return { title: 'Step', name: step.title, facts: [
      { name: 'Che cosa fa', value: step.what },
      ...(step.writes ? [{ name: 'Scrive', value: step.writes }] : []),
      { name: 'Nome nel codice', value: step.code, code: true },
    ] };
  }
  const row = data.rows.find(item => rowId(item) === id && item[mode] !== '');
  if (!row) return null;
  return { title: 'Dettaglio', name: row.name, facts: [
    { name: 'Quando parte', value: when(row, mode) },
    { name: 'Con che cosa', value: row.tool },
    ...(row.ver ? [{ name: 'Versione', value: row.ver, code: true }] : []),
    { name: 'Dove gira', value: row.where === 'container' ? 'Solo nel container' : "Sull'host" },
    { name: 'Tipo', value: row.kind },
    { name: 'Che cosa dà', value: row.does },
    { name: 'File', value: row.file, code: true },
    ...(row.status ? [{ name: 'Da sistemare', value: row.status }] : []),
  ] };
}

// The choices of the select, in their groups.
export function groupsOf(data: Data): SelectGroup[] {
  const groups: SelectGroup[] = [];
  for (const choice of data.choices) {
    let group = groups.find(item => item.label === choice.group);
    if (!group) groups.push(group = { label: choice.group, options: [] });
    group.options.push({ value: choice.id, label: choice.name });
  }
  return groups;
}
