import { test } from 'node:test';
import assert from 'node:assert/strict';
import { askedWord, askFailed, askNote, engineOptions, hasKey, keyHelp, lastQuestion, mcpFacts, needsEndpoint, NO_ENGINE, toolUse } from '../app/engine.ts';

const context = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'r1' };

test('the engines are in words, after the choice of none; only an endpoint has a key, whose help says if it is there', () => {
  assert.deepEqual(engineOptions(['claude', 'altro']), [
    { value: NO_ENGINE, label: 'Nessuno' }, { value: 'claude', label: 'Claude Code (riga di comando)' }, { value: 'altro', label: 'altro' },
  ]);
  assert.deepEqual(engineOptions(), [{ value: NO_ENGINE, label: 'Nessuno' }]);
  assert.deepEqual(['openai', 'claude', null, undefined].map(needsEndpoint), [true, false, false, false]);
  assert.deepEqual([hasKey({ api_key: 'set' }), hasKey({ api_key: 'missing' }), hasKey(undefined)], [true, false, false]);
  assert.equal(keyHelp({ api_key: 'set' }), 'Chiave impostata: lasciare vuoto per tenerla.');
  assert.equal(keyHelp(undefined), 'Va nel deposito delle credenziali del sistema.');
});

test('how a question goes is in words, and why another cannot be asked', () => {
  assert.deepEqual(['running', 'done', 'failed', 'cancelled', 'no_engine', 'altro'].map(askedWord),
    ['in corso', 'conclusa', 'non riuscita', 'interrotta', 'senza motore', 'altro']);
  assert.deepEqual([undefined, 'running', 'done', 'failed', 'cancelled'].map(askFailed), [false, false, false, true, true]);
  const ready = { context, engine: { engine: 'claude', engines: ['claude'] } };
  assert.equal(askNote({ server: ready, asked: null }), '');
  assert.equal(askNote({ server: { context }, asked: null }), 'Scegli e salva prima un motore.');
  assert.equal(askNote({ server: null, asked: null }), 'Seleziona prima una repository.');
  assert.equal(askNote({ server: { ...ready, asked: { state: 'running' } }, asked: null }), 'Il motore sta rispondendo.');
  assert.equal(askNote({ server: ready, asked: { state: 'running', text: '', tools: [], cause: null } }), 'Il motore sta rispondendo.');
});

test('the last question is said with its state and its cause, and not at all when there was none', () => {
  assert.deepEqual([lastQuestion(undefined), lastQuestion({ state: 'idle', question: '' })], ['', '']);
  assert.equal(lastQuestion({ state: 'running', question: 'Dove?' }), 'Ultima domanda: Dove? · in corso');
  assert.equal(lastQuestion({ state: 'failed', question: 'Dove?', cause: 'caduto' }), 'Ultima domanda: Dove? · non riuscita · caduto');
});

test('a tool is its name and what it was given; the server is its command and how its packages are', () => {
  assert.deepEqual(toolUse('leggi {"path": "a b.ts"}'), { name: 'leggi', value: '{"path": "a b.ts"}', code: true });
  assert.deepEqual(toolUse('mappa'), { name: 'mappa', value: '', code: true });
  assert.equal(mcpFacts({ mcp: null }), null);
  const mcp = { command: 'uv', args: ['run', 'mcp_server.py'] };
  assert.deepEqual(mcpFacts({ mcp, mcp_ready: 'ready' }), [
    { name: 'Comando', value: 'uv run mcp_server.py', code: true }, { name: 'Pacchetti del server', value: 'pronti' },
  ]);
  assert.equal(mcpFacts({ mcp, mcp_ready: 'not ready: timeout' })![1].value, 'not ready: timeout');
});
