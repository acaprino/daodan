// Both pages at the widths where the frame changes and in both schemes: nothing sticks out sideways, the views are where the width
// puts them, and the bar is the same from one screen to the next. A photograph of each, for who looks at them.
// The widths are those of Segoe UI, the font of the suite on Windows: the workflow runs this there.
import assert from 'node:assert/strict';
import { mkdir, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { errors, graph, groups, mode, opened, quiet } from './serve.mjs';

const shots = new URL('./shots/', import.meta.url);
await rm(shots, { recursive: true, force: true });
await mkdir(shots, { recursive: true });
const still = async where => {
  await where.evaluate(() => Promise.race([
    Promise.all(document.getAnimations().map(({ finished }) => finished.catch(() => {}))), new Promise(done => setTimeout(done, 1000)),
  ]).then(() => {}));
  await where.waitForTimeout(300);  // the frame and the canvas take their width
};
const sticksOut = where => where.evaluate(() => {
  const out = [];
  if (document.documentElement.scrollWidth > innerWidth) out.push(`the page is ${document.documentElement.scrollWidth} wide in ${innerWidth}`);
  for (const slot of ['title-bar', 'app-shell-tabs', 'app-shell-status', 'sidebar', 'app-shell-content', 'app-shell-actions', 'app-shell-footer', 'app-shell-bottom', 'panel-header', 'panel-tools', 'panel-body', 'inspector-body', 'inspector-footer']) {
    for (const region of document.querySelectorAll(`[data-slot="${slot}"]`)) {
      if (region.clientWidth > 1 && region.scrollWidth > region.clientWidth) out.push(`${slot} is ${region.scrollWidth} wide in ${region.clientWidth}`);
    }
  }
  for (const slot of ['app-shell-status', 'app-shell-footer', 'title-bar']) {
    const tall = document.querySelector(`[data-slot="${slot}"]`)?.clientHeight ?? 0;
    if (tall > 48) out.push(`${slot} is ${tall} tall: more than a line`);
  }
  return out;
});
const barOf = async where => {
  const box = async locator => { const found = await locator.boundingBox(); return found && [found.x, found.width].map(Math.round); };
  return { brand: await box(where.locator('[data-slot="toolbar-brand"]')), commands: await box(where.locator('[data-slot="title-bar"]').getByRole('button', { name: /^Comandi/ })) };
};
const WIDTHS = [340, 390, 620, 860, 1440], SHOT = [390, 620, 1440];
const from = { screen: 'analysis', runId: 'demo', repositoryUrl: 'https://github.com/demo/shop' };
const SCREENS = [
  ['analisi-1-repository', { ...from, analysisStage: 'repository' }, 'Repository'],
  ['analisi-2-premappa', { ...from, analysisStage: 'premap', treeSelected: 'README.md' }, 'Pre-mappa'],
  ['analisi-3-run', { ...from, analysisStage: 'analysis' }, 'Analisi'],
  ['analisi-4-sintesi', { ...from, analysisStage: 'synthesis' }, 'Sintesi'],
  ['grafo', { ...from, screen: 'graph' }, 'Grafo del codice'],
  ['motore', { ...from, screen: 'engine' }, 'Motore e domande'],
];
const MAPS = [
  ['mappa-logica', 'Vista logica', null], ['mappa-fisica', 'Vista fisica', null],
  ['mappa-logica-progetto', 'Vista logica', 'Informazioni sul progetto'],
];
const wrong = [];
quiet();
mode.pathsClassified = true;
// A graph with more to see.
const more = ['Catalogo', 'Magazzino', 'Pagamenti', 'Notifiche'].map((name, n) => ({ ...groups[1], id: name, name, files: groups[1].files.slice(n) }));
const line = (source, target, counts, status = 'confirmed') => ({ source, target, counts, status, evidence: [] });
graph.nodes.push(...more);
graph.edges.push(line('Server', 'Catalogo', { calls: 12, imports: 3 }), line('Server', 'Pagamenti', { calls: 4 }, 'observed'), line('Catalogo', 'Magazzino', { imports: 2 }),
  line('Pagamenti', 'Notifiche', { calls: 1 }, 'sampled'), line('Client', 'Notifiche', { uses: 1 }));
const browser = await chromium.launch({ args: ['--disable-lcd-text'] });  // text in gray, as the window draws it
try {
  for (const own of [false, true]) {
    for (const scheme of ['dark', 'light']) {
      const bars = {};
      // Each width is loaded by itself, as a person opens it: a canvas keeps the view it had at another width.
      const look = async (where, name, open) => {
        for (const width of own ? [620, 1440] : WIDTHS) {
          await where.setViewportSize({ width, height: 850 });
          await open();
          await where.waitForFunction(() => !document.querySelector('main [aria-busy="true"]'));
          await still(where);
          const label = `${own ? 'finestra-' : ''}${name}-${scheme}-${width}`;
          if (SHOT.includes(width)) await where.screenshot({ path: fileURLToPath(new URL(`${label}.png`, shots)) });
          const out = await sticksOut(where);
          if (out.length) wrong.push(`${label}: ${out.join('; ')}`);
          const form = width >= 860 ? 'title-bar' : width < 620 && !own ? 'app-shell-bottom' : 'app-shell-tabs';
          if (await where.locator(`[data-slot="${form}"] [data-slot="toolbar-tabs"]`).count() !== 1) wrong.push(`${label}: the views are not in ${form}`);
          if (await where.evaluate(() => document.documentElement.dataset.scheme) !== scheme) wrong.push(`${label}: not ${scheme}`);
          // Under 620 the map has the button of its drawer before the brand.
          const now = await barOf(where);
          if (width < 620) delete now.brand;
          bars[width] ??= JSON.stringify(now);
          if (JSON.stringify(now) !== bars[width]) wrong.push(`${label}: the bar is ${JSON.stringify(now)}, and was ${bars[width]}`);
        }
      };
      const shown = await opened(browser, { width: 1440, scheme, own });
      for (const [name, state, title] of SCREENS) {
        await look(shown, name, async () => {
          await shown.goto('http://daodan.test/favicon.svg');  // where nothing writes what is kept
          await shown.evaluate(left => localStorage.setItem('daodan-app-v2', JSON.stringify(left)), state);
          await shown.goto('http://daodan.test/app/?token=test');
          await shown.getByRole('region', { name: title, exact: true }).waitFor();
        });
      }
      const drawing = shown.getByRole('group', { name: 'Naviga il grafo', exact: true });
      for (const [name, command, then] of MAPS) {
        await look(shown, name, async () => {
          await shown.goto('http://daodan.test/?token=test');
          await drawing.waitFor();
          for (const each of [command, then].filter(Boolean)) {
            const commands = shown.getByRole('dialog', { name: 'Cerca un comando' });
            await shown.keyboard.press('Control+k');
            await commands.getByRole('option', { name: each }).click();
            await commands.waitFor({ state: 'detached' });
          }
          await drawing.waitFor();
        });
      }
      await shown.keyboard.press('Control+k');
      await still(shown);
      if (!own) await shown.screenshot({ path: fileURLToPath(new URL(`palette-${scheme}-1440.png`, shots)) });
      await shown.context().close();
    }
  }
  assert.deepEqual([wrong, errors], [[], []]);
} finally { await browser.close(); }
