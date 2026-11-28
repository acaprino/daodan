import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createModel } from '../app/model.ts';
import { editBody, historyOf, KEEPS, openConflicts, pathError, provenanceText, recordedText, revisionRow, valueText } from '../app/project.ts';
import type { Conflict, Project, Revision } from '../app/project.ts';
import { STORAGE } from '../app/storage.ts';

const revision = (rev: number, more: Partial<Revision> = {}): Revision => ({
  rev, kind: 'analysis', author: 'daodan', created_at: '2026-11-28T09:00:00+00:00', summary: 'analisi', opened: 0, closed: 0, edits: [], ...more,
});
const renamed = revision(2, { kind: 'manual', author: 'ada', summary: 'modifica di /name',
  edits: [{ object_id: 'o1', key: 'component:server', field_path: '/name', action: 'set', base_rev: 1, value: { present: true, value: 'Il server' } }] });
const conflict = (more: Partial<Conflict> = {}): Conflict => ({
  conflict_id: 1, detected_rev: 3, resolved_rev: null, open: true, incoming: { present: true, value: 'kernel' },
  provenance: { analysis: 3, origin: 'declared', producer: 'daodan/visual@1' }, edit_id: 1, object_id: 'o1', key: 'component:server',
  field_path: '/name', base: { present: true, value: 'server' }, value: { present: true, value: 'Il server' }, ...more,
});
const project: Project = { head: 3, revisions: [revision(1), renamed, revision(3)], conflicts: [conflict(), conflict({ conflict_id: 2, open: false })] };

test('a revision says who made it, when, and which fields it changed from which revision', () => {
  assert.deepEqual(revisionRow(renamed), {
    name: 'R2 · Modifica a mano · ada', about: '2026-11-28 09:00:00 UTC · modifica di /name · Nome → Il server (da R1)',
  });
  assert.equal(revisionRow(revision(4, { kind: 'resolution', author: 'bob', edits: [{ ...renamed.edits[0], action: 'release' }] })).about,
    '2026-11-28 09:00:00 UTC · analisi · Nome torna all’analisi (da R1)');
});

test('the history of a node is the revisions that changed it, the newest first; the project has them all', () => {
  assert.deepEqual(historyOf(project, 'component:server').map(item => item.rev), [2]);
  assert.deepEqual(historyOf(project).map(item => item.rev), [3, 2, 1]);
  assert.deepEqual(historyOf(null, 'component:server'), []);
});

test('a conflict shows the two values with where the incoming one comes from, and three ways out', () => {
  assert.deepEqual(openConflicts(project, 'component:server').map(item => item.conflict_id), [1]);
  assert.deepEqual(openConflicts(project, 'component:web'), []);
  assert.deepEqual([valueText(conflict().value), valueText(conflict().incoming), valueText({ present: false }), valueText({ present: true, value: '' })],
    ['Il server', 'kernel', '(assente)', '(vuoto)']);
  assert.equal(provenanceText(conflict().provenance), 'analisi 3 · dichiarato dal progetto · daodan/visual@1');
  assert.equal(provenanceText({ analysis: 4, origin: 'analysis', producer: null, object: 'removed' }), 'l’analisi non trova più l’oggetto');
  assert.deepEqual(KEEPS.map(item => item.keep), ['manual', 'incoming', 'analysis']);
});

test('an edit carries the head it was made on; a path must be written; the state says the file', () => {
  assert.deepEqual(editBody(project, 'component:server', 'name', ' Il server '), { ref: 'component:server', field: 'name', value: 'Il server', base_rev: 3 });
  assert.deepEqual(editBody(null, 'x', 'description', 'd'), { ref: 'x', field: 'description', value: 'd' });
  assert.deepEqual([pathError(' '), pathError('/tmp/a.daodan')], ['Scrivi il percorso del file .daodan.', '']);
  assert.equal(recordedText({ state: 'done', rev: 3 }), 'File di progetto alla revisione 3.');
  assert.equal(recordedText({ state: 'failed', cause: 'disco pieno' }), 'File di progetto non scritto: disco pieno');
  assert.equal(recordedText(undefined), 'Il file di progetto si scrive alla fine dell’analisi.');
});

// The model: the project is read with the graph, an edit is sent with its head and the two are read again.
class Source {
  listeners: Record<string, ((message: { data: string }) => void)[]> = {};
  onerror: (() => void) | null = null;
  addEventListener(name: string, listener: (message: { data: string }) => void) { (this.listeners[name] ||= []).push(listener); }
  close() {}
  send(name: string, frame: unknown) { for (const listener of this.listeners[name] ?? []) listener({ data: JSON.stringify(frame) }); }
}
const turn = () => new Promise(resolve => setImmediate(resolve));

test('the project is read with the graph, and a change made by hand is sent with its head and read again', async () => {
  const calls: { path: string; body: unknown }[] = [], sources: Source[] = [], notices: string[] = [];
  const answers: Record<string, unknown> = {
    '/api/app/graph': { grouping: 'modules', nodes: [], open: [], edges: [], files: 0, unassigned: { count: 0 } },
    '/api/app/project/history': { head: 3, revisions: project.revisions },
    '/api/app/project/conflicts': { head: 3, conflicts: project.conflicts },
    '/api/app/project/edit': { rev: 4 },
  };
  const model = createModel({
    token: 't',
    fetch: async (address, init) => {
      const path = new URL(address, 'http://daodan.test').pathname;
      calls.push({ path, body: init?.body && JSON.parse(String(init.body)) });
      return { status: 200, ok: true, json: async () => answers[path] ?? {} } as Response;
    },
    stream: () => { const source = new Source(); sources.push(source); return source as never; },
    storage: () => ({ getItem: key => (key === STORAGE ? JSON.stringify({ screen: 'graph' }) : null), setItem() {} }),
  });
  model.start(text => { notices.push(text); });
  const context = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'r1' };
  sources[0].send('app', { context, job: { state: 'ready' }, run: { pass: { state: 'fresh' } }, engine: { engine: null, engines: [] },
    project: { state: 'done', rev: 3 } });
  for (let i = 0; i < 5; i++) await turn();
  assert.deepEqual(model.snapshot().project, project);
  const asked = (path: string) => calls.filter(call => call.path === path).length;
  const before = [asked('/api/app/graph'), asked('/api/app/project/history')];
  assert.equal(await model.changeNode('component:server', 'name', 'Il backend'), true);
  for (let i = 0; i < 5; i++) await turn();
  assert.deepEqual(calls.find(call => call.path === '/api/app/project/edit')?.body,
    { ref: 'component:server', field: 'name', value: 'Il backend', base_rev: 3 });
  assert.deepEqual([asked('/api/app/graph'), asked('/api/app/project/history')], [before[0] + 1, before[1] + 1]);
  assert.ok(notices.includes('Modifica salvata nel file di progetto.'));
  assert.equal(model.snapshot().projectBusy, '');
});
