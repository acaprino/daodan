import { test } from 'node:test';
import assert from 'node:assert/strict';
import { accessFeedback, preferredBranch, preparation, repositoryContext, repositorySlug, sameChoice } from '../app/repository.ts';
import { askReason, buildStatus, gapLines, linksNote, logItems, mapNotice, passAlert, passWord, phaseItems, runBar, runCount, runHelp, runPercent, runPhaseLabel, serviceLine, statusLabel, statusOf, steps, stepTime } from '../app/run.ts';
import type { RunEvent } from '../app/server.ts';
import type { Snapshot } from '../app/snapshot.ts';
import { footOf, stages } from '../app/stages.ts';
import { DEFAULTS } from '../app/storage.ts';
import type { Kept } from '../app/storage.ts';

const context = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'r1' };
// What these read of the snapshot: the server's state, the run's events, and what the page is doing.
const of = (server: object | null, more: object = {}) => ({
  server, serverError: '', events: [], premapError: '', checked: null, checking: false, graph: null, graphLoading: false, ...more,
}) as unknown as Snapshot;
const run = (state: string | undefined, events: Partial<RunEvent>[] = [], more: object = {}) => of({ context, job: { state: 'ready' }, run: { pass: { state, reason: null }, ...more } }, { events });
const rows = (s: Snapshot) => stages(s).map(row => [row.id, row.state, row.reason]);

test('the stages say how they are, and why one cannot be opened', () => {
  const first = 'Scegli prima una repository e un branch.';
  assert.deepEqual(rows(of({ job: { state: 'idle' } })), [['repository', 'todo', ''], ['premap', 'todo', first], ['analysis', 'todo', first], ['synthesis', 'todo', first]]);
  assert.deepEqual(rows(of(null)).map(row => row[1]), ['todo', 'todo', 'todo', 'todo']);
  assert.equal(rows(of({ job: { state: 'preparing' } }))[0][1], 'running');
  assert.equal(rows(of({ job: { state: 'failed' } }))[0][1], 'error');
  assert.deepEqual(rows(run('running')), [['repository', 'done', ''], ['premap', 'done', ''], ['analysis', 'running', ''],
    ['synthesis', 'todo', 'La sintesi è pronta quando la pipeline è conclusa.']]);
  assert.deepEqual(rows(run('fresh')).map(row => row.slice(1)), [['done', ''], ['done', ''], ['done', ''], ['done', '']]);
  assert.deepEqual(rows(run('failed')).slice(2).map(row => row.slice(1)), [['error', ''], ['done', '']]);
  assert.equal(rows(run('fresh', [{ kind: 'step.started', step: 'assemble_graph' }]))[2][1], 'running');  // a step runs after the pass's end
  assert.equal(rows(of({ context, run: { pass: { state: 'fresh' } } }, { premapError: 'illeggibile' }))[1][1], 'error');
  const found = stages(of({ context, run: { pass: { state: 'running' }, progress: null } }, { premap: { files: ['a'], units: [] } }));
  assert.deepEqual(found.map(row => [row.detail, row.meta]),
    [['demo/shop · main', ''], ['1 file · 0 unità tecniche', ''], ['0 di 6 passi completati', '0%'], ['Risultati e lacune', '']]);
});

test('the foot has the way back, one action, and why it waits or what comes after it', () => {
  const at = (analysisStage: Kept['analysisStage'], server: object | null, more: object = {}, repositoryUrl = '') =>
    of(server, { kept: { ...DEFAULTS, analysisStage, repositoryUrl }, branch: '', ...more });
  const foot = (...given: Parameters<typeof at>) => {
    const { back, label, act, off, busy, note } = footOf(at(...given));
    return [back, label, act, off ? 'off' : busy, note];
  };
  const idle = { job: { state: 'idle' } }, done = { context, job: { state: 'ready' }, run: { pass: { state: 'fresh' } } };
  const url = 'https://github.com/demo/shop', commit = context.commit;
  const checked = { state: 'accessible', repository: context.repository, branches: [{ name: 'main', commit }, { name: 'dev', commit }] };
  assert.deepEqual(foot('repository', idle), [null, 'Verifica accesso', 'verify', 'off', 'Scrivi l’URL della repository.']);
  assert.deepEqual(foot('repository', idle, {}, url), [null, 'Verifica accesso', 'verify', '', 'Poi: il branch']);
  assert.deepEqual(foot('repository', idle, { checking: true }, url), [null, 'Verifica accesso', 'verify', 'Verifica…', 'Verifica in corso.']);
  assert.deepEqual(foot('repository', idle, { checked, branch: 'main' }, url), [null, 'Avvia l’analisi', 'select', '', 'Poi: Pre-mappa']);
  assert.deepEqual(foot('repository', { job: { state: 'preparing' } }, { checked }, url), [null, 'Avvia l’analisi', 'select', 'Preparazione…', 'Preparazione in corso.']);
  assert.deepEqual(foot('repository', done, { checked, branch: 'main', selecting: true }, url)[3], 'Preparazione…');
  // A step done is looked at, and goes on with its run; another branch, commit or address is another analysis.
  const more = [null, 'Continua', 'premap', '', 'Poi: Pre-mappa'];
  assert.deepEqual([foot('repository', done), foot('repository', done, {}, url), foot('repository', done, { checked, branch: 'main' }, url)], [more, more, more]);
  assert.equal(foot('repository', done, { checked, branch: 'dev' }, url)[2], 'select');
  assert.equal(foot('repository', done, { checked: { ...checked, branches: [{ name: 'main', commit: '2'.repeat(40) }] }, branch: 'main' }, url)[2], 'select');
  assert.equal(foot('repository', done, {}, 'https://github.com/demo/altro')[2], 'verify');
  assert.equal(sameChoice(at('repository', done, {}, 'https://github.com/Demo/Shop')), true);
  assert.deepEqual(foot('premap', done), ['repository', 'Continua', 'analysis', '', 'Poi: Analisi']);
  assert.deepEqual(foot('analysis', { ...done, run: { pass: { state: 'running' } } }), ['premap', 'Continua', 'synthesis', 'off', 'Attendi la fine della pipeline.']);
  assert.deepEqual(foot('analysis', done), ['premap', 'Continua', 'synthesis', '', 'Poi: Sintesi e grafo']);
  assert.deepEqual(foot('synthesis', done), ['analysis', 'Apri il grafo', 'graph', '', 'Ultimo passo']);
});

test('a phase says how long it has taken, as its events do', () => {
  const at = (second: number) => `2026-11-25T10:00:${String(second).padStart(2, '0')}Z`, now = Date.parse('2026-11-25T10:02:05Z');
  const events = [
    { kind: 'step.started', step: 'recognize_stack', at: at(0) }, { kind: 'step.finished', step: 'recognize_stack', at: at(9) },
    { kind: 'step.started', step: 'find_modules', at: at(9) }, { kind: 'step.failed', step: 'find_modules', at: at(12), message: 'disco pieno' },
    { kind: 'step.started', step: 'find_entry_points', at: at(0) }, { kind: 'step.started', step: 'link_calls' },
  ];
  const s = run('running', events);
  assert.deepEqual(steps(s).map(step => stepTime(s, step, now)), ['9 s', '3 s', '2 min 5 s', '', '', '']);
  assert.deepEqual(phaseItems(s, now).map(item => [item.status, item.description, item.meta]), [['done', undefined, '9 s'], ['error', 'Non riuscita · disco pieno', '3 s'],
    ['running', 'In corso', '2 min 5 s'], ['running', 'In corso', undefined], ['todo', undefined, undefined], ['todo', undefined, undefined]]);
});

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

test('the steps follow their own events, with the progress, the gaps and the causes', () => {
  const events = [
    { kind: 'step.started', step: 'recognize_stack' }, { kind: 'step.finished', step: 'recognize_stack' },
    { kind: 'step.started', step: 'link_calls' }, { kind: 'analyzer.unavailable', step: 'link_calls', analyzer: 'pyright', message: 'manca' }, { kind: 'step.finished', step: 'link_calls' },
    { kind: 'step.started', step: 'find_entry_points' }, { kind: 'step.failed', step: 'find_entry_points', message: 'interrotto' },
    { kind: 'step.started', step: 'run_and_observe' },
  ];
  const s = run('running', events, { progress: { step: 'run_and_observe', done: 1, total: 4 } });
  assert.deepEqual(steps(s).map(step => [step.id, step.status, step.note]), [
    ['recognize_stack', 'done', 'Completata'], ['find_modules', 'pending', 'In attesa'], ['find_entry_points', 'failed', 'Non riuscita · interrotto'],
    ['link_calls', 'done', 'Completata con lacune · pyright: manca'], ['run_and_observe', 'running', 'In corso · 1/4'], ['assemble_graph', 'pending', 'In attesa'],
  ]);
  assert.equal(runPercent(s), 38);  // two of six and a quarter
  assert.equal(runPhaseLabel(s), 'Esecuzione · osservazione dei test');
  assert.deepEqual(statusOf(s), { state: 'Analisi in corso', tone: 'info', text: 'Esecuzione', percent: 38 });  // the short name: one line
  const over = of({ context, run: { pass: { state: 'unavailable', reason: 'nessun container' } } });
  assert.deepEqual([steps(over)[0].status, steps(over)[0].note, runPercent(over)], ['skipped', 'Non eseguita · nessun container', 0]);
  assert.equal(runPercent(of(null)), 0);
});

test('the bar of the steps stops where a step failed once the run is over', () => {
  const events = [{ kind: 'step.started', step: 'recognize_stack' }, { kind: 'step.finished', step: 'recognize_stack' }, { kind: 'step.started', step: 'find_entry_points' }, { kind: 'step.failed', step: 'find_entry_points', message: 'interrotto' }];
  assert.deepEqual(runBar(run('running', events)), { value: 17 });
  assert.deepEqual(runBar(run('fresh', events)), { value: 17, status: 'error', valueText: 'Non riuscito · 17%' });
  assert.deepEqual(runBar(run('fresh', [...events, { kind: 'step.started', step: 'assemble_graph' }])), { value: 17 });  // one still runs
  assert.deepEqual(runBar(run('failed', events.slice(0, 2))), { value: 17 });  // the pass failed, no step did
});

test('the run says its phase, its state and what the last progress was', () => {
  assert.deepEqual([runPhaseLabel(run('fresh')), statusLabel(run('fresh')), runHelp(run('fresh'))],
    ['Pipeline completata', 'Completata', 'Pipeline conclusa: sintesi e grafo sono pronti da leggere.']);
  assert.deepEqual([runPhaseLabel(run(undefined)), statusLabel(run(undefined)), runHelp(run(undefined))],
    ['In attesa del passaggio del grafo', 'In esecuzione', 'In attesa del primo avanzamento del run.']);
  assert.match(runHelp(run('off')), /con le sue lacune/);
  assert.equal(runHelp(run('running', [], { progress: { step: 'find_modules', analyzer: 'ctags', done: 2, total: 3 } })), 'Ultimo avanzamento: Moduli · ctags · 2/3');
  assert.equal(buildStatus(run('running')), 'Costruzione in corso');
  assert.equal(buildStatus(run('running', [{ kind: 'graph.ready' }])), 'Grafo del codice scritto');
});

test('the count of the steps done is beside the title', () => {
  assert.equal(runCount(run('running')), '0 di 6 passi completati');
  assert.equal(runCount(run('running', [{ kind: 'step.started', step: 'recognize_stack' }, { kind: 'step.finished', step: 'recognize_stack' }])), '1 di 6 passi completati');
});

test('the status row and the foot say the server that is read, lost, idle or at work', () => {
  assert.deepEqual(statusOf(of(null)), { state: 'Lettura', tone: 'info', text: 'Lettura dello stato del server…', percent: null });
  assert.deepEqual(statusOf(of({ job: { state: 'idle' } }, { serverError: 'caduto' })), { state: 'Errore', tone: 'danger', text: 'Server non raggiungibile', percent: null });
  assert.deepEqual(statusOf(of({ job: { state: 'idle' } })), { state: 'Nessuna repository', text: '', percent: null });
  assert.deepEqual(statusOf(of({ job: { state: 'preparing', step: 'snapshot' } })), { state: 'Preparazione in corso', tone: 'info', text: 'Snapshot e pre-mappa', percent: null });
  assert.equal(statusOf(of({ job: { state: 'failed', step: 'checkout' } })).text, 'Preparazione non riuscita (Checkout del branch)');
  assert.deepEqual(statusOf(run('fresh')), { state: 'Contesto pronto', tone: 'success', text: 'Pipeline completata', percent: null });
  assert.equal(statusOf(run('running', [{ kind: 'step.started', step: 'link_calls' }])).text, 'Chiamate');  // as the 620 px shot runs it
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

test('the log says each event in words and leaves out progress and debug', () => {
  const items = logItems(of(null, { events: [
    { run: true, event: 'engine_failed', message: 'caduto', timestamp: '10:00' }, { run: true, event: 'phase_completed', message: 'm' }, { run: true, event: 'altro', message: 'm' },
    { kind: 'progress', step: 'find_modules', message: '1/2' }, { kind: 'log', level: 'debug', message: 'interno' },
    { kind: 'step.finished', step: 'find_modules', message: '', data: { outputs: ['modules.json'] } }, { kind: 'step.started', step: 'assemble_graph', message: '', data: { inputs: ['a', 'b'] } },
    { kind: 'gap', step: 'find_entry_points', message: 'x', data: { gap: { detail: 'manifest assente', remedy: 'aggiungilo' } } },
    { kind: 'analyzer.unavailable', step: 'link_calls', analyzer: 'pyright', message: 'm', data: { cause: 'manca' } },
    { kind: 'log', level: 'error', message: 'rotto' },
  ] }));
  assert.deepEqual(items.map(item => [item.title, item.detail, item.type]), [
    ['Passaggio del grafo interrotto', 'caduto', 'error'], ['Fase completata', 'm', ''], ['altro', 'm', ''], ['Moduli · completato', 'Scritti: modules.json', ''], ['Grafo · avviato', 'Legge: a, b', ''],
    ['Ingressi · lacuna', 'manifest assente Rimedio: aggiungilo', 'gap'], ['Chiamate · analyzer non disponibile · pyright', 'manca', ''], ['Pipeline · nota', 'rotto', 'error'],
  ]);
});

test('the gaps are the pass’s, the graph’s and the events’, each once', () => {
  const s = of({ context, run: { pass: { state: 'failed', reason: 'memoria' } } }, {
    graph: { unassigned: { count: 3 }, gaps: [{ reason: 'rotta non trovata' }] },
    events: [{ kind: 'gap', message: 'rotta non trovata' }, { kind: 'gap', message: 'x', data: { gap: { detail: 'lettore assente' } } }],
  });
  assert.deepEqual(gapLines(s), ['Grafo delle chiamate non rifinito: memoria', '3 file non assegnati a un modulo.', 'rotta non trovata', 'lettore assente']);
});
