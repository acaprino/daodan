import { test } from 'node:test';
import assert from 'node:assert/strict';
import { causeOf, createHttp, isBusy, whenFree } from '../src/http.ts';

const turn = () => new Promise(resolve => setImmediate(resolve));  // every promise already answered has gone on
const answers = (status: number, body?: unknown) => async () =>
  ({ status, ok: status < 400, json: async () => { if (body === undefined) throw new SyntaxError('no JSON'); return body; } }) as Response;

test('a request has the token where there is one, and a post its body', async () => {
  const asked: [string, RequestInit][] = [];
  const server = (token: string) => createHttp(async (path, init) => { asked.push([path, init!]); return answers(200, { ok: 1 })(); }, token);
  assert.deepEqual(await server('t').get('./a'), { ok: 1 });
  await server('').get('./a');
  await server('t').post('./b', { c: 2 });
  assert.deepEqual(asked.map(([path, { method, headers, body }]) => [path, method, headers, body]), [
    ['./a', undefined, { 'X-Daodan-Token': 't' }, undefined], ['./a', undefined, {}, undefined],
    ['./b', 'POST', { 'X-Daodan-Token': 't', 'Content-Type': 'application/json' }, '{"c":2}'],
  ]);
});

test('what fails says why, in Italian', async () => {
  const why = (fetch: () => Promise<Response>) => createHttp(fetch, '').get('./a').then(() => '', causeOf);
  assert.equal(await why(answers(400, { error: 'run sconosciuto' })), 'run sconosciuto');
  assert.equal(await why(answers(500)), 'il server ha risposto 500');
  assert.match(await why(answers(403, { error: 'refused' })), /^il server rifiuta la richiesta/);
  assert.equal(await why(answers(503, { error: 'project lock is held by another helper' })), 'Daodan è occupato');
  assert.equal(await why(async () => { throw new TypeError('Failed to fetch'); }), 'il server non risponde');
  assert.equal(await why(async () => { throw new Error('caduto'); }), 'caduto');
});

test('a busy server is asked again until it answers, and what fails otherwise is not', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const replies = [answers(503), answers(429), answers(200, { runs: [] })];
  let asked = 0, said = 0;
  const server = createHttp(() => replies[asked++](), '');
  const found = whenFree(() => server.get('./api/runs'), () => { said += 1; });
  await turn();
  assert.deepEqual([asked, said], [1, 1]);
  t.mock.timers.tick(1999);
  await turn();
  assert.equal(asked, 1);
  t.mock.timers.tick(1);
  await turn();
  assert.deepEqual([asked, said], [2, 1]);  // said once
  t.mock.timers.tick(2000);
  assert.deepEqual(await found, { runs: [] });
  await assert.rejects(whenFree(() => createHttp(answers(500), '').get('./a'), () => { said += 1; }), { message: 'il server ha risposto 500' });
  assert.equal(said, 1);
});

test('a busy server nobody waits for any more is left alone', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let asked = 0, wanted = true;
  const server = createHttp(() => { asked += 1; return answers(503)(); }, '');
  const found = whenFree(() => server.get('./a'), () => undefined, () => wanted);
  await turn();
  wanted = false;
  t.mock.timers.tick(2000);
  assert.deepEqual([await found, asked], [undefined, 1]);
  assert.deepEqual([isBusy(null), isBusy(new Error('altro'))], [false, false]);
});
