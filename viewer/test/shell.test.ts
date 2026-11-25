import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';

const FOLDERS = ['src', 'app'];
const sources = FOLDERS.flatMap(folder => readdirSync(new URL(`../${folder}/`, import.meta.url)).filter(name => /\.tsx?$/.test(name))
  .map(name => ({ file: `${folder}/${name}`, text: readFileSync(new URL(`../${folder}/${name}`, import.meta.url), 'utf8') })));

test('the frame is the shell of Imago: no page draws a part of it', () => {
  const shell = ['AppShell', 'TitleBar', 'WindowControls', 'ToolbarBrand', 'ToolbarTabs', 'DrawerButton', 'CommandPalette', 'CommandsProvider', 'KeyHints', 'Toasts',
    'useSchemeCommands', 'applyKeptScheme', 'useCommandPalette', 'WordsProvider', 'createRoot', '__TAURI', '@tauri-apps', '@acaprino/sigrid/tauri'];
  for (const { file, text } of sources) for (const name of shell) assert.ok(!text.includes(name), `${file} has ${name}`);
});

test('both pages are started by the shell, as the one app Daodan, in its window', () => {
  const starts = sources.filter(({ text }) => text.includes('startApp(')).map(({ file }) => file);
  assert.deepEqual(starts, FOLDERS.map(folder => `${folder}/main.tsx`));
  for (const { file, text } of sources.filter(({ file }) => starts.includes(file))) {
    for (const part of ['startApp(DAODAN,', '<AppWindow ', 'useNotify()']) assert.ok(text.includes(part), `${file}: ${part}`);
  }
  assert.deepEqual(sources.filter(({ text }) => text.includes('defineApp(')).map(({ file }) => file), ['src/page.ts']);
});
