import { test } from 'node:test';
import assert from 'node:assert/strict';
import { appearanceOptions, applyStored, readAppearance } from '../app/imago-page.ts';

const store = (values: Record<string, string> = {}) => ({
  values, getItem: (key: string) => values[key] ?? null, setItem(key: string, value: string) { values[key] = value; },
}) as unknown as Storage & { values: Record<string, string> };
const root = () => {
  const attributes: Record<string, string> = {};
  return { attributes, style: {} as Record<string, string>, classList: { toggle() {} },
    setAttribute: (name: string, value: string) => { attributes[name] = value; }, ownerDocument: null } as unknown as HTMLElement & { attributes: Record<string, string> };
};

test('a stored look and theme are read back', () => {
  assert.deepEqual(readAppearance(store({ 'daodan.look': 'oni', 'daodan.theme': 'dark' })), { look: 'oni', theme: 'dark' });
});

test('a missing, corrupt or unreadable choice is Smooth and the system theme', () => {
  const smooth = { look: 'smooth', theme: 'system' };
  assert.deepEqual(readAppearance(null), smooth);
  assert.deepEqual(readAppearance(store()), smooth);
  assert.deepEqual(readAppearance(store({ 'daodan.look': 'neon', 'daodan.theme': '{' })), smooth);
  assert.deepEqual(readAppearance({ getItem() { throw new Error('blocked'); } }), smooth);
});

test('the look at the start of a page is the stored one', () => {
  const page = root();
  applyStored(page, store({ 'daodan.look': 'oni', 'daodan.theme': 'light' }));
  assert.deepEqual([page.attributes['data-im-app'], page.attributes['data-im-look'], page.attributes['data-im-theme']], ['daodan', 'oni', 'light']);
});

test('choosing a theme stores it and puts it on the root; the choice is what get gives back', () => {
  const page = root(), storage = store();
  const options = appearanceOptions(page, storage);
  options.set({ look: 'smooth', theme: 'dark' });
  assert.equal(page.attributes['data-im-theme'], 'dark');
  assert.deepEqual(storage.values, { 'daodan.look': 'smooth', 'daodan.theme': 'dark' });
  assert.deepEqual(options.get(), { look: 'smooth', theme: 'dark' });
});

test('a choice made while the storage refuses lasts, and a change made elsewhere is read when reloaded', () => {
  const page = root();
  const blocked = { getItem: () => null, setItem() { throw new Error('quota'); } } as unknown as Storage;
  const options = appearanceOptions(page, blocked);
  options.set({ look: 'oni', theme: 'dark' });
  assert.deepEqual(options.get(), { look: 'oni', theme: 'dark' });
  const storage = store();
  const watching = appearanceOptions(page, storage);
  storage.setItem('daodan.theme', 'light');
  watching.reload();
  assert.equal(page.attributes['data-im-theme'], 'light');
});
