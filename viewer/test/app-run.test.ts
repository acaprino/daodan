import { test } from 'node:test';
import assert from 'node:assert/strict';
import { accessFeedback, preferredBranch, preparation, repositoryContext, repositoryReason, repositorySlug } from '../app/repository.ts';
import { askReason, buildStatus, gapLines, linksNote, logItems, mapNotice, passAlert, runHelp, runPercent, runPhaseLabel, serviceLine, statusLabel, statusOf, steps } from '../app/run.ts';
import type { RunEvent } from '../app/server.ts';
import type { Snapshot } from '../app/snapshot.ts';
import { STAGE_WORD, stages } from '../app/stages.ts';

const context = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'r1' };
// What these read of the snapshot: the server's state, the run's events, and what the page is doing.
const of = (server: object | null, more: object = {}) => ({
  server, serverError: '', events: [], premapError: '', checked: null, checking: false, graph: null, graphLoading: false, ...more,
}) as unknown as Snapshot;
const run = (state: string | undefined, events: Partial<RunEvent>[] = [], more: object = {}) => of({ context, job: { state: 'ready' }, run: { pass: { state, reason: null }, ...more } }, { events });
const rows = (s: Snapshot) => stages(s).map(row => [row.id, STAGE_WORD[row.state], row.reason]);

test('the stages say how they are, and why one cannot be opened', () => {
  const first = 'Scegli prima una repository e un branch.';
  assert.deepEqual(rows(of({ job: { state: 'idle' } })), [['repository', 'da fare', ''], ['premap', 'da fare', first], ['analysis', 'da fare', first], ['synthesis', 'da fare', first]]);
  assert.deepEqual(rows(of(null)).map(row => row[1]), ['da fare', 'da fare', 'da fare', 'da fare']);
  assert.equal(rows(of({ job: { state: 'preparing' } }))[0][1], 'in corso');
  assert.equal(rows(of({ job: { state: 'failed' } }))[0][1], 'non riuscita');
  assert.deepEqual(rows(run('running')), [['repository', 'fatta', ''], ['premap', 'fatta', ''], ['analysis', 'in corso', ''],
    ['synthesis', 'da fare', 'La sintesi è pronta quando la pipeline è conclusa.']]);
  assert.deepEqual(rows(run('fresh')).map(row => row.slice(1)), [['fatta', ''], ['fatta', ''], ['fatta', ''], ['fatta', '']]);
  assert.deepEqual(rows(run('failed')).slice(2).map(row => row.slice(1)), [['non riuscita', ''], ['fatta', '']]);
  assert.equal(rows(run('fresh', [{ kind: 'step.started', step: 'union' }]))[2][1], 'in corso');  // a step runs after the pass's end
  assert.equal(rows(of({ context, run: { pass: { state: 'fresh' } } }, { premapError: 'illeggibile' }))[1][1], 'non riuscita');
});

test('a GitHub address is read with or without its scheme, and nothing else is one', () => {
  for (const url of ['https://github.com/demo/shop', ' github.com/demo/shop/ ', 'https://github.com/demo/shop.git']) assert.equal(repositorySlug(url), 'demo/shop');
  for (const url of ['', 'demo/shop', 'https://gitlab.com/demo/shop', 'https://github.com/demo', 'https://github.com/demo/shop/tree/main', 'https://github.com/demo/..']) {
    assert.equal(repositorySlug(url), null, url);
  }
  assert.deepEqual([['dev', 'main'], ['dev', 'master'], ['dev']].map(names => preferredBranch(names.map(name => ({ name })), 'dev')), ['main', 'master', 'dev']);
});

test('the repository says why the branch waits, what the check found and how the preparation goes', () => {
  const found = { state: 'accessible' };
  assert.equal(repositoryReason(of(null)), 'Verifica prima l’accesso alla repository.');
  assert.equal(repositoryReason(of(null, { checking: true })), 'Verifica in corso.');
  assert.equal(repositoryReason(of({ job: { state: 'preparing' } }, { checked: found })), 'Preparazione in corso.');
  assert.equal(repositoryReason(of({ job: { state: 'idle' } }, { checked: found })), '');
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

test('the steps follow their own events, with the progress, the gaps and the causes', () => {
  const events = [
    { kind: 'step.started', step: 'parse' }, { kind: 'step.finished', step: 'parse' },
    { kind: 'step.started', step: 'analyze' }, { kind: 'analyzer.unavailable', step: 'analyze', analyzer: 'pyright', message: 'manca' }, { kind: 'step.finished', step: 'analyze' },
    { kind: 'step.started', step: 'stack' }, { kind: 'step.failed', step: 'stack', message: 'interrotto' },
    { kind: 'step.started', step: 'dynamic' },
  ];
  const s = run('running', events, { progress: { step: 'dynamic', done: 1, total: 4 } });
  assert.deepEqual(steps(s).map(step => [step.id, step.status, step.note]), [
    ['parse', 'done', 'Completata'], ['scan', 'pending', 'In attesa'], ['stack', 'failed', 'Non riuscita · interrotto'],
    ['analyze', 'done', 'Completata con lacune · pyright: manca'], ['dynamic', 'running', 'In corso · 1/4'], ['union', 'pending', 'In attesa'],
  ]);
  assert.equal(runPercent(s), 38);  // two of six and a quarter
  assert.equal(runPhaseLabel(s), 'Dynamic · osservazione dei test');
  assert.deepEqual(statusOf(s), { state: 'Analisi in corso', text: 'Dynamic · osservazione dei test', percent: 38 });
  const over = of({ context, run: { pass: { state: 'unavailable', reason: 'nessun container' } } });
  assert.deepEqual([steps(over)[0].status, steps(over)[0].note, runPercent(over)], ['skipped', 'Non eseguita · nessun container', 0]);
  assert.equal(runPercent(of(null)), 0);
});

test('the run says its phase, its state and what the last progress was', () => {
  assert.deepEqual([runPhaseLabel(run('fresh')), statusLabel(run('fresh')), runHelp(run('fresh'))],
    ['Pipeline completata', 'Completata', 'Pipeline conclusa: sintesi e grafo sono pronti da leggere.']);
  assert.deepEqual([runPhaseLabel(run(undefined)), statusLabel(run(undefined)), runHelp(run(undefined))],
    ['In attesa del passaggio del grafo', 'In esecuzione', 'In attesa del primo avanzamento del run.']);
  assert.match(runHelp(run('off')), /con le sue lacune/);
  assert.equal(runHelp(run('running', [], { progress: { step: 'scan', analyzer: 'ctags', done: 2, total: 3 } })), 'Ultimo avanzamento: Scan · ctags · 2/3');
  assert.equal(buildStatus(run('running')), 'Costruzione in corso');
  assert.equal(buildStatus(run('running', [{ kind: 'graph.ready' }])), 'Grafo del codice scritto');
});

test('the status row and the foot say the server that is read, lost, idle or at work', () => {
  assert.deepEqual(statusOf(of(null)), { state: 'Lettura', text: 'Lettura dello stato del server…', percent: null });
  assert.deepEqual(statusOf(of({ job: { state: 'idle' } }, { serverError: 'caduto' })), { state: 'Errore', text: 'Server non raggiungibile', percent: null });
  assert.deepEqual(statusOf(of({ job: { state: 'idle' } })), { state: 'Nessuna repository', text: '', percent: null });
  assert.deepEqual(statusOf(of({ job: { state: 'preparing', step: 'snapshot' } })), { state: 'Preparazione in corso', text: 'Snapshot e pre-mappa', percent: null });
  assert.equal(statusOf(of({ job: { state: 'failed', step: 'checkout' } })).text, 'Preparazione non riuscita (Checkout del branch)');
  assert.deepEqual(statusOf(run('fresh')), { state: 'Contesto pronto', text: 'Pipeline completata', percent: null });
  assert.equal(serviceLine(of({ engine: { engine: 'claude' } })), 'App locale: il codice resta sul tuo disco · Motore: claude');
  assert.equal(serviceLine(of({}, { serverError: 'caduto' })), 'Server non raggiungibile · Motore non scelto');
});

test('the pass, the map and the links say what is missing and why', () => {
  assert.equal(passAlert(run('fresh')), null);
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

test('the log says each event in words and leaves out progress and debug', () => {
  const items = logItems(of(null, { events: [
    { run: true, event: 'engine_failed', message: 'caduto', timestamp: '10:00' }, { run: true, event: 'altro', message: 'm' },
    { kind: 'progress', step: 'scan', message: '1/2' }, { kind: 'log', level: 'debug', message: 'interno' },
    { kind: 'step.finished', step: 'scan', message: '', data: { outputs: ['modules.json'] } }, { kind: 'step.started', step: 'union', message: '', data: { inputs: ['a', 'b'] } },
    { kind: 'gap', step: 'stack', message: 'x', data: { gap: { detail: 'manifest assente', remedy: 'aggiungilo' } } },
    { kind: 'analyzer.unavailable', step: 'analyze', analyzer: 'pyright', message: 'm', data: { cause: 'manca' } },
    { kind: 'log', level: 'error', message: 'rotto' },
  ] }));
  assert.deepEqual(items.map(item => [item.title, item.detail, item.type]), [
    ['Passaggio del grafo interrotto', 'caduto', 'error'], ['altro', 'm', ''], ['Scan · completato', 'Scritti: modules.json', ''], ['Union · avviato', 'Legge: a, b', ''],
    ['Stack · lacuna', 'manifest assente Rimedio: aggiungilo', 'gap'], ['Analyze · analyzer non disponibile · pyright', 'manca', ''], ['Pipeline · nota', 'rotto', 'error'],
  ]);
});

test('the gaps are the pass’s, the graph’s and the events’, each once', () => {
  const s = of({ context, run: { pass: { state: 'failed', reason: 'memoria' } } }, {
    graph: { unassigned: { count: 3 }, gaps: [{ reason: 'rotta non trovata' }] },
    events: [{ kind: 'gap', message: 'rotta non trovata' }, { kind: 'gap', message: 'x', data: { gap: { detail: 'lettore assente' } } }],
  });
  assert.deepEqual(gapLines(s), ['Grafo delle chiamate non rifinito: memoria', '3 file non assegnati a un modulo.', 'rotta non trovata', 'lettore assente']);
});
