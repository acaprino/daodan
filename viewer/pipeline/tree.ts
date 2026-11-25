// The tree of the pipeline as a scene for the canvas: the steps in their order and, hanging from each, what it uses for the choice made.
// The data is written from the code's declarations (`data.ts`); nothing here draws.
import type { GraphEdge, GraphLegendEntry, GraphNode } from '@acaprino/sigrid/graph';
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
export type Scene = {
  nodes: GraphNode[]; edges: GraphEdge[];
  steps: Map<string, number[]>;  // the steps of the path, each with its number
  branches: string[];            // the steps something hangs from
  key: string; shown: number; boxed: number;
};

export const ALL = 'all';
export const stepId = (key: string) => `step:${key}`;
export const rowId = (row: Row) => `row:${row.name}`;
const NUMBERED = /^[sp]\d+$/;  // a step of the path: what comes after the pipeline, and what every step shares, are beside it
const when = (row: Row, mode: Mode) => (mode === 'plan' ? row.when_plan : row.when);

export function uses(row: Row, choice: Choice | null): boolean {
  if (row.all || !choice) return true;
  // A framework's own tool is for that framework, whatever language the two share.
  if (row.fw.length && choice.fw.length) return row.fw.some(item => choice.fw.includes(item));
  return row.langs.some(item => choice.langs.includes(item)) || row.fam.some(item => choice.fam.includes(item))
    || row.fw.some(item => choice.fw.includes(item));
}

export function sceneOf(data: Data, mode: Mode, choice: Choice | null): Scene {
  const nodes: GraphNode[] = [], edges: GraphEdge[] = [], steps = new Map<string, number[]>(), branches: string[] = [];
  let shown = 0, boxed = 0, number = 0, before: Step | null = null;
  for (const step of data.steps[mode]) {
    const id = stepId(step.key), onPath = NUMBERED.test(step.key);
    if (onPath) number += 1;
    nodes.push({ id, label: onPath ? `${number}. ${step.title}` : step.title, detail: step.code, icon: 'layers' });
    if (onPath) {
      steps.set(id, [number]);
      if (before) edges.push({ id: `then:${step.key}`, from: stepId(before.key), to: id, kind: 'link', label: `scrive ${before.writes}`, tone: 'accent' });
      before = step;
    }
    const rows = data.rows.filter(row => row[mode] === step.key && uses(row, choice));
    if (rows.length) branches.push(id);
    for (const row of rows) {
      const contained = row.where === 'container';
      shown += 1;
      if (contained) boxed += 1;
      nodes.push({ id: rowId(row), label: row.ver ? `${row.name} ${row.ver}` : row.name, detail: row.tool, icon: contained ? 'package' : 'device' });
      edges.push({ id: `uses:${row.name}`, from: id, to: rowId(row), label: when(row, mode), style: contained ? 'dashed' : 'solid' });
    }
  }
  return { nodes, edges, steps, branches, key: `${mode}|${choice?.id ?? ALL}`, shown, boxed };
}

export function legendOf(scene: Scene): GraphLegendEntry[] {
  return [
    { style: 'solid', label: "usa, sull'host", count: scene.shown - scene.boxed },
    { style: 'dashed', label: 'usa, solo nel container', count: scene.boxed },
    { style: 'solid', tone: 'accent', label: 'poi, con ciò che ha scritto' },
  ];
}

// What the inspector says of the thing chosen: a step, or something a step uses.
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
