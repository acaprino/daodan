import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  argvOf, commandFacts, confirmBody, confirmedWords, draftErrors, draftOf, gradeOf, isReady, KINDS, lineOf, removeBody, removedWords, setBody,
  setWords, titleOf, workOf,
} from '../app/commands.ts';
import type { Command } from '../app/server.ts';

// The commands as the state has them (`commands.listed`): the person's start, the assistant's tests, and a start it proposed and the
// person confirmed.
const start: Command = { kind: 'starts', root: 'web', argv: ['npm', 'run', 'dev'], by: 'user', grade: 'confermato', port: 5173 };
const tests: Command = { kind: 'tests', root: '.', argv: ['pytest', '-p', 'xdist', '-p', 'no:cacheprovider'], by: 'assistant', grade: 'proposto', runner: 'pytest' };
const confirmed: Command = { kind: 'builds', root: 'web', argv: ['npm', 'run', 'build'], by: 'user', grade: 'confermato', proposed_by: 'assistant', surface: 'webview' };

test('a command says what it does, where, its words and who stated it', () => {
  assert.deepEqual(KINDS.map(kind => kind.value), ['starts', 'tests', 'builds']);
  assert.deepEqual([titleOf(start), titleOf(tests), titleOf(confirmed)],
    ['Avvio dell’app in web', 'Esecuzione dei test nella radice del progetto', 'Build in web']);
  assert.equal(lineOf(tests), 'pytest -p xdist -p no:cacheprovider');
  assert.deepEqual([gradeOf(start), gradeOf(tests), gradeOf(confirmed)], [
    { badge: 'Confermato', tone: 'success', who: 'Impostato da te' },
    { badge: 'Proposto', tone: 'warning', who: 'Proposto dall’assistente: aspetta la tua conferma' },
    { badge: 'Confermato', tone: 'success', who: 'Proposto dall’assistente, confermato da te' },
  ]);
  assert.deepEqual(commandFacts(start).filter(Boolean).map(fact => fact!.name), ['Comando', 'Chi', 'Porta']);
  assert.deepEqual(commandFacts(tests).filter(Boolean).map(fact => [fact!.name, fact!.value]),
    [['Comando', 'pytest -p xdist -p no:cacheprovider'], ['Chi', 'Proposto dall’assistente: aspetta la tua conferma'], ['Runner', 'pytest']]);
  assert.deepEqual(commandFacts(confirmed).filter(Boolean).map(fact => fact!.name), ['Comando', 'Chi', 'Superficie']);
});

test('the form opens on the command kept for its kind and folder, one word a line, else empty', () => {
  const kept = [start, tests, confirmed];
  assert.deepEqual(draftOf('starts', 'web', kept), { kind: 'starts', root: 'web', words: 'npm\nrun\ndev', port: '5173' });
  assert.deepEqual(draftOf('tests', '.', kept), { kind: 'tests', root: '.', words: 'pytest\n-p\nxdist\n-p\nno:cacheprovider', port: '' });
  assert.deepEqual(draftOf('starts', 'api', kept), { kind: 'starts', root: 'api', words: '', port: '' });
  assert.deepEqual(draftOf('builds', '.'), { kind: 'builds', root: '.', words: '', port: '' });
});

test('the words are the lines as written: none is split, none dropped for being there twice', () => {
  assert.deepEqual(argvOf('npm\nrun\ndev'), ['npm', 'run', 'dev']);
  assert.deepEqual(argvOf('  go \r\n\ntest\n./...\n-run\nTest Login\n'), ['go', 'test', './...', '-run', 'Test Login']);
  assert.deepEqual(argvOf('-p\n-p\n-P'), ['-p', '-p', '-P']);
  assert.deepEqual(argvOf(' \n\n'), []);
});

test('the form is sent once it has a folder, a word, and a port from 1 to 65535 where it is given', () => {
  const draft = { kind: 'starts' as const, root: 'web', words: 'npm\nrun\ndev', port: '' };
  assert.deepEqual([draftErrors(draft), isReady(draft)], [{}, true]);
  assert.deepEqual(draftErrors({ ...draft, root: ' ', words: '\n', port: '0' }), {
    root: 'Scrivi la cartella: «.» è la radice del progetto.', words: 'Scrivi almeno una parola del comando.', port: 'La porta è un numero da 1 a 65535.' });
  for (const port of ['65536', '80.5', '1e3', '0x50', '-1', 'ottanta']) assert.equal(draftErrors({ ...draft, port }).port, 'La porta è un numero da 1 a 65535.', port);
  for (const port of ['1', ' 8080 ', '65535']) assert.equal(isReady({ ...draft, port }), true, port);
  assert.equal(isReady({ ...draft, kind: 'tests', port: '0' }), true);  // a port is a start's: the form shows it there alone
});

test('the person\'s command is sent as its words, its port as a number, with the surface of the one it replaces', () => {
  const draft = { kind: 'starts' as const, root: ' web ', words: 'npm\nrun\ndev', port: ' 3000 ' };
  assert.deepEqual(setBody(draft), { action: 'set', command: { kind: 'starts', root: 'web', argv: ['npm', 'run', 'dev'], port: 3000 } });
  assert.deepEqual(setBody({ ...draft, port: '' }).command, { kind: 'starts', root: 'web', argv: ['npm', 'run', 'dev'] });
  const build = { kind: 'builds' as const, root: 'web', words: 'pnpm\nbuild', port: '3000' };
  assert.deepEqual(setBody(build, [start, confirmed]).command, { kind: 'builds', root: 'web', argv: ['pnpm', 'build'], surface: 'webview' });
  const testing = { kind: 'tests' as const, root: '.', words: 'pytest', port: '' };
  assert.deepEqual(setBody(testing, [{ ...tests, surface: 'web' }]).command, { kind: 'tests', root: '.', argv: ['pytest'] });
  assert.equal(setWords(draft), 'Comando impostato: Avvio dell’app in web. Gira alla prossima analisi, nel container.');
});

test('a kept command is confirmed or removed by its kind, its folder and its runner where it has one', () => {
  assert.deepEqual(confirmBody(tests), { action: 'confirm', kind: 'tests', root: '.', runner: 'pytest' });
  assert.deepEqual(removeBody(start), { action: 'remove', kind: 'starts', root: 'web' });
  assert.notEqual(workOf('confirm', tests), workOf('remove', tests));
  assert.notEqual(workOf('remove', tests), workOf('remove', { ...tests, runner: 'jest' }));
  assert.equal(confirmedWords(tests), 'Comando confermato: Esecuzione dei test nella radice del progetto.');
  assert.equal(removedWords(start), 'Comando tolto: Avvio dell’app in web.');
});
