// The pre-map, read for its screen: its trees as Sigrid's `Tree` takes them, what a search finds, what is chosen, and its facts in
// words.
import type { IconName } from '@acaprino/sigrid/primitives';
import type { TreeNode } from '@acaprino/sigrid/assemblies';
import { short } from './repository.ts';
import type { Context } from './server.ts';
import { number, slug } from './snapshot.ts';
import type { Dependency, Premap, PremapFound, Unit } from './snapshot.ts';
import type { Kept } from './storage.ts';

// -- the trees ---------------------------------------------------------------------------------------------------------

export type PremapTree = {
  nodes: TreeNode[];
  choices: ReadonlyMap<string, string>;  // by row: what it chooses (`treeSelected`); a row that is not here only opens and closes
  texts: ReadonlyMap<string, string>;    // by row: what a search looks in, in lower case
};

const nameOf = (path: string) => path.slice(path.lastIndexOf('/') + 1);
const byName = (a: string, b: string) => nameOf(a).localeCompare(nameOf(b), 'it');

type Folder = { path: string; folders: Map<string, Folder>; files: string[] };
// The files in their directories: the directories first, each by name.
export function directoryTree(files: readonly string[]): PremapTree {
  const root: Folder = { path: '', folders: new Map(), files: [] };
  for (const path of files) {
    let at = root;
    for (const name of path.split('/').slice(0, -1)) {
      const inner: Folder = at.folders.get(name) ?? { path: at === root ? name : `${at.path}/${name}`, folders: new Map(), files: [] };
      at.folders.set(name, inner);
      at = inner;
    }
    at.files.push(path);
  }
  const rows = (folder: Folder): TreeNode[] => [
    ...[...folder.folders.values()].sort((a, b) => byName(a.path, b.path)).map(inner =>
      ({ id: `directory:${inner.path}`, name: nameOf(inner.path), icon: 'folder', openIcon: 'folderOpen', children: rows(inner) })),
    ...folder.files.sort(byName).map(path => ({ id: path, name: nameOf(path), icon: 'file' })),
  ];
  return { nodes: rows(root), choices: new Map(files.map(path => [path, path])), texts: new Map(files.map(path => [path, path.toLowerCase()])) };
}

const UNIT_STATUS: Record<string, string> = { confirmed: 'Confermata', inferred: 'Inferita', incomplete: 'Incompleta' };
const statusOf = (unit: Unit) => UNIT_STATUS[unit.status] || unit.status;
const unitRow = (unit: Unit) => `unit:${unit.id}`;
// The technical units in the unit that holds them, each with the manifest that declares it.
export function unitTree(units: readonly Unit[]): PremapTree {
  const choices = new Map<string, string>(), texts = new Map<string, string>(), ids = new Set(units.map(unit => unit.id));
  const rows = (holder: string | null): TreeNode[] => units.filter(unit => (unit.parent && ids.has(unit.parent) ? unit.parent : null) === holder).map(unit => {
    const id = unitRow(unit), children: TreeNode[] = [];
    choices.set(id, id);
    texts.set(id, [unit.name, unit.kind, unit.root, unit.manifest].join(' ').toLowerCase());
    if (unit.manifest) {
      const row = JSON.stringify([id, 'manifest']);
      choices.set(row, unit.manifest);
      children.push({ id: row, name: unit.manifest, icon: 'file' });
    }
    children.push(...rows(unit.id));
    return { id, name: unit.name, icon: 'package', meta: [unit.kind, statusOf(unit)].filter(Boolean).join(' · '), ...(children.length > 0 && { children }) };
  });
  return { nodes: rows(null), choices, texts };
}

// Whether a search finds a row: by the whole path of a file, by the name, kind, root and manifest of a unit.
export const finds = (tree: PremapTree, row: string, query: string) => tree.texts.get(row)?.includes(query.trim().toLowerCase()) ?? false;
export const countFound = (tree: PremapTree, query: string) => [...tree.texts.keys()].filter(row => finds(tree, row, query)).length;

// The first row that stands for what is chosen, or null.
export const rowOf = (tree: PremapTree, chosen: string) => [...tree.choices].find(([, choice]) => choice === chosen)?.[0] ?? null;

// The branches that are open: the ones of the first level, and what the person opened and closed.
export function openBranches(nodes: readonly TreeNode[], kept: Kept['treeOpen']): string[] {
  const open: string[] = [];
  const walk = (list: readonly TreeNode[], first: boolean) => {
    for (const node of list) {
      if (!node.children) continue;
      if (kept[node.id] ?? first) open.push(node.id);
      walk(node.children, false);
    }
  };
  walk(nodes, true);
  return open;
}
// What is kept once the person has opened or closed some: `open` is the whole list of the branches open now.
export function keptBranches(nodes: readonly TreeNode[], kept: Kept['treeOpen'], open: readonly string[]): Kept['treeOpen'] {
  const before = new Set(openBranches(nodes, kept)), now = new Set(open), next = { ...kept };
  for (const id of new Set([...before, ...now])) if (before.has(id) !== now.has(id)) next[id] = now.has(id);
  return next;
}

// -- what is chosen ----------------------------------------------------------------------------------------------------

export type Choice = { kind: 'unit'; unit: Unit } | { kind: 'file'; path: string };
// What `treeSelected` stands for in this pre-map, or null: another run may not have it.
export function choiceOf(premap: Premap | null, chosen: string): Choice | null {
  if (!premap || !chosen) return null;
  const unit = premap.units.find(item => unitRow(item) === chosen);
  if (unit) return { kind: 'unit', unit };
  return premap.files.includes(chosen) || premap.units.some(item => item.manifest === chosen) ? { kind: 'file', path: chosen } : null;
}

export type Fact = { name: string; value: string; code?: boolean };
export const CHOICE_TITLE: Record<Choice['kind'], string> = { unit: 'Unità tecnica', file: 'File dell’inventario' };
// What the details say of it.
export function choiceDetails(choice: Choice, c: Context): { icon: IconName; name: string; facts: Fact[]; text: string } {
  if (choice.kind === 'unit') {
    const { unit } = choice;
    return { icon: 'package', name: unit.name, text: unit.description ?? '', facts: [
      ...(unit.kind ? [{ name: 'Tipo', value: unit.kind }] : []),
      { name: 'Stato', value: statusOf(unit) || 'dichiarata' },
      { name: 'Radice', value: unit.root || '.', code: true },
      ...(unit.manifest ? [{ name: 'Manifest', value: unit.manifest, code: true }] : []),
      { name: 'Dipendenze registrate', value: number(unit.dependencies.length) },
    ] };
  }
  const name = nameOf(choice.path);
  return { icon: 'file', name, text: 'Il contenuto non viene eseguito.', facts: [
    { name: 'Percorso', value: choice.path, code: true },
    { name: 'Tipo', value: name.includes('.') ? name.slice(name.lastIndexOf('.') + 1) : 'senza estensione' },
    { name: 'Fonte', value: `snapshot del commit ${short(c.commit)}` },
  ] };
}

// -- its facts ---------------------------------------------------------------------------------------------------------

// How much the pre-map holds, and what each count counts.
export const inventory = (premap: Premap): { name: string; value: string; of: string }[] => [
  { name: 'File nello snapshot', value: number(premap.files.length), of: 'Inventario del checkout' },
  { name: 'Linguaggi rilevati', value: number(premap.languages.length), of: 'File sorgente riconosciuti' },
  { name: 'Unità tecniche', value: number(premap.units.length), of: 'Da manifest e strumenti di build' },
  { name: 'Dipendenze per unità', value: number(premap.dependencies.length), of: 'Da manifest e modelli di build' },
];

// A technology's category and version, in words.
export const technologyFacts = (technology: PremapFound['technologies'][number]) => [technology.category,
  technology.version || (technology.state === 'declared' ? 'Versione non dichiarata' : 'Versione non registrata')].filter(Boolean).join(' · ');

type Version = { version: string; source: string } | null;
// The versions of a dependency, each with where it is read, and how its unit needs it.
export function dependencyFacts(dependency: Dependency): { declared: Version; resolved: Version; relation: string } {
  const { state, source, version, resolved_version, resolution_source, direct } = dependency;
  return {
    declared: state === 'resolved' ? null : { version: version || 'Non specificato', source },
    resolved: resolved_version ? { version: resolved_version, source: resolution_source || source } : null,
    relation: direct === true ? 'Diretta' : direct === false ? 'Transitiva' : '—',
  };
}

const counted = (list?: readonly unknown[]) => (list ? number(list.length) : '—');
// Where the pre-map comes from, and what that proves.
export const provenanceFacts = (c: Context, premap: Premap | null): Fact[] => [
  { name: 'Repository', value: slug(c), code: true },
  { name: 'Branch', value: c.branch, code: true },
  { name: 'Commit', value: c.commit, code: true },
  { name: 'Run', value: c.run_id, code: true },
  { name: 'File nello snapshot', value: counted(premap?.files) },
  { name: 'Unità tecniche', value: counted(premap?.units) },
  { name: 'Dipendenze per unità', value: counted(premap?.dependencies) },
];
export const PROVENANCE_NOTES = [
  'I linguaggi provengono dai sorgenti dello snapshot. Le tecnologie e le dipendenze provengono dalla mappa dello stack.',
  'Il manifest fornisce il vincolo dichiarato. Il modello di build fornisce la versione risolta e la relazione diretta o transitiva, quando disponibili.',
  'Uno strumento usato dagli analyzer non prova che il progetto usi quel framework.',
];
