import { test } from 'node:test';
import assert from 'node:assert/strict';
import { handlerSource, listingOf, paging, stepWords } from '../app/paths.ts';
import { ORPHAN_WRITES } from '../app/snapshot.ts';
import type { PathCard, PathPage, PathResult } from '../app/snapshot.ts';

const card: PathCard = { card_id: 'save', handler: 'ui.ts::save', kind: 'azione', site: 'ui.ts:4', event: 'onClick' };
const page = (id: PathPage['id'], offset: number, result: Partial<PathResult> | undefined, previous: PathPage | null = null): PathPage =>
  ({ run: 'r1', id, offset, previous, result: result && { offset, count: 0, next_offset: null, ...result } });

test('a page says what it lists, which part of it, and where one can go', () => {
  assert.deepEqual([listingOf(null), listingOf(page(null, 0, undefined)), listingOf(page('save', 0, undefined)), listingOf(page(ORPHAN_WRITES, 0, undefined))],
    ['entries', 'entries', 'steps', 'writes']);
  const entries = page(null, 0, { count: 3, next_offset: 2, cards: [card, card] });
  assert.deepEqual(paging(entries), { range: 'Ingressi 1–2 di 3', previous: '', next: 'Ingressi successivi' });
  assert.deepEqual(paging(page(null, 2, { count: 3, cards: [card] }, entries)), { range: 'Ingressi 3–3 di 3', previous: 'Ingressi precedenti', next: '' });
  // The list left to read one entry is not a page before it.
  const step = { n: 1, from: 'a', site: 'a:1' };
  assert.deepEqual(paging(page('save', 0, { count: 2, next_offset: 1, steps: [step] }, entries)), { range: 'Passaggi 1–1 di 2', previous: '', next: 'Passaggi successivi' });
  const writes = page(ORPHAN_WRITES, 0, { count: 2, next_offset: 1, effects: [{ n: 1, writer: 'w', site: 's', effect: 'e', reason: 'r' }] }, entries);
  assert.deepEqual(paging(writes), { range: 'Scritture 1–1 di 2', previous: '', next: 'Scritture successive' });
  assert.equal(paging(page(ORPHAN_WRITES, 1, { count: 2, effects: [] }, writes)).previous, 'Scritture precedenti');
});

test('a step says where it comes from, what ends there and how it is proven', () => {
  assert.deepEqual(stepWords({ n: 2, parent: 1, from: 'a', site: 'a:1', end: 'lacuna', confidence: 'sampled', conflict: true, origin: 'dedotto', resolver: 'pyright' }),
    { title: 'Passaggio 2 · dal passo 1', end: 'Lacuna', proof: 'a:1 · campionata dal profiler · destinazioni in conflitto · dedotto · pyright' });
  assert.deepEqual(stepWords({ n: 1, from: 'a', site: 'a:1', end: 'effetto', confidence: 'altro' }), { title: 'Passaggio 1', end: 'Effetto', proof: 'a:1 · altro' });
  assert.equal(stepWords({ n: 1, from: 'a', site: 'a:1', end: 'continua' }).end, '');
  assert.deepEqual([handlerSource(card), handlerSource({ ...card, handler_source: 'decoratore', handler_confidence: 'observed' }), handlerSource({ ...card, handler_confidence: 'certa' })],
    ['', 'decoratore · osservata in esecuzione', 'certa']);
});
