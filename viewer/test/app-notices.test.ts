import { test } from 'node:test';
import assert from 'node:assert/strict';
import { accessFeedback, preferredBranch, preparation, repositoryContext, repositorySlug } from '../app/repository.ts';
import { askReason } from '../app/engine.ts';
import { buildStatus, linksNote, logItems, mapNotice, passAlert, passWord, serviceLine } from '../app/notices.ts';
import { statusOf } from '../app/plan.ts';
import type { RunEvent } from '../app/server.ts';
import type { Snapshot } from '../app/snapshot.ts';

const context = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'r1' };
// What these read of the snapshot: the server's state, the run's events, and what the page is doing.
const of = (server: object | null, more: object = {}) => ({
  server, serverError: '', events: [], premapError: '', checked: null, checking: false, graph: null, graphLoading: false, ...more,
}) as unknown as Snapshot;
const run = (state: string | undefined, events: Partial<RunEvent>[] = [], more: object = {}) => of({ context, job: { state: 'ready' }, run: { pass: { state, reason: null }, ...more } }, { events });

test('a GitHub address is read with or without its scheme, and nothing else is one', () => {
  for (const url of ['https://github.com/demo/shop', ' github.com/demo/shop/ ', 'https://github.com/demo/shop.git']) assert.equal(repositorySlug(url), 'demo/shop');
  for (const url of ['', 'demo/shop', 'https://gitlab.com/demo/shop', 'https://github.com/demo', 'https://github.com/demo/shop/tree/main', 'https://github.com/demo/..']) {
    assert.equal(repositorySlug(url), null, url);
  }
  assert.deepEqual([['dev', 'main'], ['dev', 'master'], ['dev']].map(names => preferredBranch(names.map(name => ({ name })), 'dev')), ['main', 'master', 'dev']);
});

test('the repository says what the check found and how the preparation goes', () => {
  const found = { state: 'accessible' };
  assert.equal(accessFeedback(null), null);
  assert.equal(accessFeedback(found as never), null);
  assert.deepEqual(accessFeedback({ state: 'network', detail: 'timeout' } as never),
    { tone: 'error', title: 'Errore di rete.', message: 'Riprova la verifica. Il login non risolve un errore di connessione. (timeout)' });
  assert.equal(accessFeedback({ state: 'empty' } as never)!.tone, 'warning');
  assert.equal(preparation(undefined), null);
  assert.equal(preparation({ state: 'ready', step: null }), null);
  assert.deepEqual(preparation({ state: 'preparing', step: 'checkout', detail: 'main' }), { state: 'preparing', step: 'Checkout del branch', detail: 'main' });
  assert.deepEqual(preparation({ state: 'failed', step: 'altro', detail: 'disco pieno' }), { state: 'failed', step: 'altro', detail: 'disco pieno' });
  assert.deepEqual(repositoryContext(run('fresh')).map(fact => fact.value), ['demo/shop', 'main', '1'.repeat(12), 'r1']);
  assert.deepEqual(repositoryContext(of(null)), []);
});

test('how the graph is built is said by the run\'s state, and by the event that it is written', () => {
  assert.equal(buildStatus(run('running')), 'Costruzione in corso');
  assert.equal(buildStatus(run('fresh')), 'Costruzione conclusa');
  assert.equal(buildStatus(run('running', [{ kind: 'graph.ready' }])), 'Grafo del codice scritto');
  assert.equal(buildStatus(of(null, { graphLoading: true })), 'Lettura del grafo…');
});

test('the status row and the foot say the server that is read, lost, idle or at work', () => {
  assert.deepEqual(statusOf(of(null)), { state: 'Lettura', tone: 'info', text: 'Lettura dello stato del server…', percent: null });
  assert.deepEqual(statusOf(of({ job: { state: 'idle' } }, { serverError: 'caduto' })), { state: 'Errore', tone: 'danger', text: 'Server non raggiungibile', percent: null });
  assert.deepEqual(statusOf(of({ job: { state: 'idle' } })), { state: 'Nessuna repository', text: '', percent: null });
  assert.deepEqual(statusOf(of({ job: { state: 'preparing', step: 'snapshot' } })), { state: 'Preparazione in corso', tone: 'info', text: 'Snapshot del codice e modello di build', percent: null });
  assert.equal(statusOf(of({ job: { state: 'failed', step: 'checkout' } })).text, 'Preparazione non riuscita (Checkout del branch)');
  assert.deepEqual(statusOf(run('fresh')), { state: 'Contesto pronto', tone: 'success', text: 'Pipeline completata', percent: null });
  // A step under way is the plan's, not an event's: the events alone say none.
  assert.equal(statusOf(run('running', [{ kind: 'step.started', step: 'link_calls' }])).text, 'In attesa del passaggio del grafo');
  assert.equal(serviceLine(of({ engine: { engine: 'claude' } })), 'App locale: il codice resta sul tuo disco · Motore: claude');
  assert.equal(serviceLine(of({}, { serverError: 'caduto' })), 'Server non raggiungibile · Motore non scelto');
});

test('the pass, the map and the links say what is missing and why', () => {
  assert.equal(passAlert(run('fresh')), null);
  assert.deepEqual(['fresh', 'unavailable', 'failed', 'off', 'running', undefined].map(state => passWord(run(state))),
    ['completato', 'non disponibile', 'non riuscito', 'spento', 'in corso', '']);
  assert.deepEqual([passAlert(run('failed'))!.tone, passAlert(run('failed'))!.retry, passAlert(run('off'))!.tone, passAlert(run('off'))!.retry], ['error', true, 'warning', false]);
  assert.equal(passAlert(run('failed'))!.message, 'Nessuna causa registrata.');
  const mapped = (map: object | undefined) => mapNotice(of({ mapped: map }));
  assert.deepEqual([mapped(undefined), mapped({ state: 'idle' })], [null, null]);
  assert.deepEqual(mapped({ state: 'incomplete', cause: 'the recorded map still has stale or incomplete records',
    needs_review: { nodes: { count: 2 }, flows: { count: 1 }, refused_proposals: { count: 1 } } }), {
    tone: 'warning', title: 'Mappa del sistema parziale',
    message: 'Da verificare: 2 nodi, 1 flusso, 1 proposta rifiutata. Alcune prove sono incomplete o si riferiscono a una revisione precedente.',
  });
  assert.deepEqual([mapped({ state: 'done' }), mapped({ state: 'failed', cause: 'interrotto' })!.tone],
    [{ tone: 'info', title: 'Mappa del sistema registrata', message: '' }, 'error']);
  const links = (state: object | undefined, engine: string | null = 'claude') => linksNote(of({ links: state, engine: { engine } }));
  assert.match(links(undefined).message, /^Non ancora cercati/);
  assert.deepEqual([links({ state: 'idle' }, null).reason, links({ state: 'running' }).running], ['Scegli e salva prima un motore.', true]);
  assert.match(links({ state: 'done', routes: { called: 1, offered: 2, linked: 1 }, gaps: 0, stores: 1 }).message, /1 richiesta, 2 rotte, 1 legame, 0 lacune, 1 archivio\.$/);
  assert.deepEqual([links({ state: 'failed', cause: 'nessuna regola' }).tone, links({ state: 'failed', cause: 'nessuna regola' }).message], ['error', 'Non trovati. nessuna regola']);
  assert.deepEqual([askReason(of({})), askReason(of({ context })), askReason(of({ context, engine: { engine: 'claude' } }))],
    ['Seleziona prima una repository.', 'Scegli e salva prima un motore.', '']);
});

test('the log says each event in words, with the titles of the steps, and leaves out progress and debug', () => {
  const items = logItems(of(null, { events: [
    { run: true, event: 'engine_failed', message: 'caduto', timestamp: '10:00' }, { run: true, event: 'phase_completed', message: 'm' }, { run: true, event: 'altro', message: 'm' },
    { kind: 'progress', step: 'find_modules', message: '1/2' }, { kind: 'log', level: 'debug', message: 'interno' },
    { kind: 'step.finished', step: 'find_modules', message: '', data: { outputs: ['modules.json'] } }, { kind: 'step.started', step: 'assemble_graph', message: '', data: { inputs: ['a', 'b'] } },
    { kind: 'gap', step: 'find_entry_points', message: 'x', data: { gap: { detail: 'manifest assente', remedy: 'aggiungilo' } } },
    { kind: 'analyzer.unavailable', step: 'link_calls', analyzer: 'pyright', message: 'm', data: { cause: 'manca' } },
    { kind: 'log', level: 'error', message: 'rotto' },
  ] }));
  assert.deepEqual(items.map(item => [item.title, item.detail, item.type]), [
    ['Passaggio del grafo interrotto', 'caduto', 'error'], ['Fase completata', 'm', ''], ['altro', 'm', ''], ['Moduli · completato', 'Scritti: modules.json', ''],
    ['Grafo finale · avviato', 'Legge: a, b', ''], ['Punti di ingresso · lacuna', 'manifest assente Rimedio: aggiungilo', 'gap'],
    ['Chiamate · strumento non disponibile · pyright', 'manca', ''], ['Pipeline · nota', 'rotto', 'error'],
  ]);
});
