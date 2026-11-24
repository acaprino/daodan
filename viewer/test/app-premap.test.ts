import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  choiceDetails, choiceOf, countFound, dependencyFacts, directoryTree, finds, inventory, keptBranches, openBranches, provenanceFacts, rowOf,
  technologyFacts, unitTree,
} from '../app/premap.ts';

const context = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: 'a'.repeat(40), run_id: 'r1' };
const unit = (id: string, more = {}): any => ({ id, name: id, kind: 'npm', root: id, status: 'confirmed', dependencies: [], ...more });
const premap = (more = {}): any => ({ files: [], languages: [], technologies: [], units: [], dependencies: [], ...more });
// The tree as it is read: the name of each row, and of what it holds.
const names = (nodes: readonly any[]): unknown[] => nodes.map(node => (node.children ? [node.name, ...names(node.children)] : node.name));

test('the files are in their directories, the directories first and each by name', () => {
  const tree = directoryTree(['b.ts', 'src/z.ts', 'src/lib/util.ts', 'a/à.ts', 'a/z.ts', 'README.md']);
  assert.deepEqual(names(tree.nodes), [['a', 'à.ts', 'z.ts'], ['src', ['lib', 'util.ts'], 'z.ts'], 'b.ts', 'README.md']);
  const src = tree.nodes[1], lib = src.children![0];
  assert.deepEqual([src.id, src.icon, src.openIcon], ['directory:src', 'folder', 'folderOpen']);
  assert.deepEqual([lib.id, lib.children![0].id, lib.children![0].icon], ['directory:src/lib', 'src/lib/util.ts', 'file']);
  assert.deepEqual(directoryTree([]).nodes, []);
});

test('a unit is in the one that holds it, with its manifest and its kind and state in words', () => {
  const tree = unitTree([unit('web', { root: '.', manifest: 'package.json' }), unit('api', { parent: 'web', status: 'inferred', manifest: null }),
    unit('lost', { parent: 'gone', kind: null, status: null })]);
  assert.deepEqual(names(tree.nodes), [['web', 'package.json', 'api'], 'lost']);
  const [web, lost] = tree.nodes;
  assert.deepEqual([web.id, web.icon, web.meta, web.children![1].meta, lost.meta], ['unit:web', 'package', 'npm · Confermata', 'npm · Inferita', '']);
});

test('a search finds a file by its whole path and a unit by its name, kind, root and manifest, whatever the case and the spaces', () => {
  const files = directoryTree(['src/main.ts', 'src/lib/util.ts', 'README.md']);
  assert.deepEqual([' SRC/main ', 'src', 'lib/', 'niente', '', '  '].map(query => countFound(files, query)), [1, 2, 1, 0, 3, 3]);
  assert.ok(finds(files, 'src/main.ts', 'SRC/'));
  assert.ok(!finds(files, 'directory:src', 'src'));  // a directory shows for what it holds, and its id is not a path
  assert.equal(countFound(files, 'directory'), 0);
  const units = unitTree([unit('web', { root: 'client', manifest: 'client/package.json' }), unit('api', { kind: 'maven', root: 'server', manifest: null })]);
  assert.deepEqual(['WEB', 'maven', 'server', 'package.json', 'null'].map(query => countFound(units, query)), [1, 1, 1, 1, 0]);
});

test('the first level is open, and what the person opens and closes is kept', () => {
  const { nodes } = directoryTree(['src/lib/util.ts', 'docs/a.md', 'b.ts']);
  assert.deepEqual(openBranches(nodes, {}), ['directory:docs', 'directory:src']);
  const kept = keptBranches(nodes, { 'unit:web': false }, ['directory:src', 'directory:src/lib']);
  assert.deepEqual(kept, { 'unit:web': false, 'directory:docs': false, 'directory:src/lib': true });
  assert.deepEqual(openBranches(nodes, kept), ['directory:src', 'directory:src/lib']);
  assert.deepEqual(keptBranches(nodes, kept, ['directory:docs', 'directory:src', 'directory:src/lib']), { ...kept, 'directory:docs': true });
});

test('what is kept as chosen is a file or a unit of this pre-map, and the row that stands for it', () => {
  const web = unit('web', { manifest: 'package.json' }), found = premap({ files: ['src/main.ts'], units: [web] });
  assert.deepEqual(choiceOf(found, 'src/main.ts'), { kind: 'file', path: 'src/main.ts' });
  assert.deepEqual(choiceOf(found, 'package.json'), { kind: 'file', path: 'package.json' });
  assert.deepEqual(choiceOf(found, 'unit:web'), { kind: 'unit', unit: web });
  assert.deepEqual([choiceOf(found, ''), choiceOf(found, 'gone.ts'), choiceOf(found, 'unit:gone'), choiceOf(null, 'src/main.ts')], [null, null, null, null]);
  const files = directoryTree(found.files), units = unitTree(found.units);
  assert.deepEqual([rowOf(files, 'src/main.ts'), rowOf(files, 'unit:web'), rowOf(units, 'unit:web'), rowOf(units, '')], ['src/main.ts', null, 'unit:web', null]);
  assert.equal(units.choices.get(rowOf(units, 'package.json')!), 'package.json');
  assert.ok(!files.choices.has('directory:src'));  // a directory only opens and closes
});

test('the details of a file say its path, type and source, those of a unit its boundary', () => {
  const value = (choice: any, name: string) => choiceDetails(choice, context).facts.find(fact => fact.name === name)?.value;
  const file = { kind: 'file', path: 'src/main.test.ts' };
  assert.deepEqual([value(file, 'Percorso'), value(file, 'Tipo'), value(file, 'Fonte')], ['src/main.test.ts', 'ts', `snapshot del commit ${'a'.repeat(12)}`]);
  assert.equal(value({ kind: 'file', path: 'a.b/Makefile' }, 'Tipo'), 'senza estensione');
  const web = { kind: 'unit', unit: unit('web', { root: '', status: 'incomplete', manifest: 'package.json', dependencies: [{}, {}] }) };
  assert.deepEqual(choiceDetails(web as any, context).facts.map(fact => fact.value), ['npm', 'Incompleta', '.', 'package.json', '2']);
  assert.deepEqual(choiceDetails({ kind: 'unit', unit: unit('x', { kind: null, status: null, manifest: null }) }, context).facts.map(fact => fact.value),
    ['dichiarata', 'x', '0']);
});

test('a dependency says the constraint declared, the version resolved and the relation, each with its source', () => {
  const declared = { name: 'a', scope: 'npm', state: 'declared', source: 'package.json:3' };
  assert.deepEqual(dependencyFacts(declared), { declared: { version: 'Non specificato', source: 'package.json:3' }, resolved: null, relation: '—' });
  assert.deepEqual(dependencyFacts({ ...declared, state: 'declared_resolved', version: '^1', resolved_version: '1.2', resolution_source: 'package-lock.json', direct: true }),
    { declared: { version: '^1', source: 'package.json:3' }, resolved: { version: '1.2', source: 'package-lock.json' }, relation: 'Diretta' });
  assert.deepEqual(dependencyFacts({ ...declared, state: 'resolved', source: 'package-lock.json', resolved_version: '2.0', direct: false }),
    { declared: null, resolved: { version: '2.0', source: 'package-lock.json' }, relation: 'Transitiva' });
});

test('a technology says its category and its version, or why it has none', () => {
  const technology = { name: 'React', category: 'framework', source: 'package.json' };
  assert.equal(technologyFacts({ ...technology, version: '19' }), 'framework · 19');
  assert.equal(technologyFacts({ ...technology, state: 'declared', version: '' }), 'framework · Versione non dichiarata');
  assert.equal(technologyFacts({ ...technology, state: 'recognized' }), 'framework · Versione non registrata');
});

test('the four counts, and where they come from', () => {
  const found = premap({ files: ['a', 'b'], languages: [{ name: 'C', files: 2 }], units: [unit('web')], dependencies: [{}, {}, {}] });
  assert.deepEqual(inventory(found).map(count => count.value), ['2', '1', '1', '3']);
  assert.deepEqual(provenanceFacts(context, found).map(fact => fact.value), ['demo/shop', 'main', 'a'.repeat(40), 'r1', '2', '1', '3']);
  assert.deepEqual(provenanceFacts(context, null).map(fact => fact.value).slice(4), ['—', '—', '—']);
});
