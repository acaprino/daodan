// Measures the explorer at the address open in the page, for the Playwright MCP tool `browser_run_code_unsafe`
// (filename). It opens the address in a separate headless Chrome at 1440x900, because a window that is hidden
// or covered throttles frames to about one per second, then reports: every ELK layout in the worker from the
// request to the answer (the first includes loading ELK into the worker), the time from navigation to the
// painted graph (the layout drawn and the number of nodes in the DOM the same for two frames: the canvas draws only
// what is in its view, so `drawn` may be less than `nodes`), 20 selections spread over the drawn nodes
// (click in the DOM until the frame after the inspector shows the node), the same graph laid out again with the
// worker loaded, and the page's JS heap and DOM nodes after a collection. The worker's own heap is not counted.
// The page is read by its roles, its names and its words, as `viewer/test/browser.mjs` does.
async (mcpPage) => {
  const url = mcpPage.url();
  const type = mcpPage.context().browser().browserType();
  const browser = await type.launch({ channel: 'chrome', headless: true }).catch(() => type.launch({ headless: true }));
  try {
    const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
    await page.addInitScript(() => {
      if (window.__layouts) return;
      window.__layouts = [];
      const posted = new Map();
      const Native = window.Worker;
      window.Worker = class extends Native {
        constructor(...args) {
          super(...args);
          this.addEventListener('message', event => {
            const start = posted.get(event.data?.id);
            if (start !== undefined) window.__layouts.push(Math.round(performance.now() - start));
          });
        }
        postMessage(message, ...rest) {
          posted.set(message?.id, performance.now());
          return super.postMessage(message, ...rest);
        }
      };
    });
    const fps = await page.evaluate(() => new Promise(resolve => {
      let frames = 0;
      const start = performance.now();
      const tick = () => { frames += 1; if (performance.now() - start < 1000) requestAnimationFrame(tick); else resolve(frames); };
      requestAnimationFrame(tick);
    }));
    if (fps < 30) throw new Error(`frames throttled to ${fps} per second`);
    await page.goto(url, { waitUntil: 'load' });
    await page.evaluate(() => {
      window.explorer = {
        things: () => [...document.querySelectorAll('[role="group"][aria-label="Naviga il grafo"] [role="button"][aria-label]')],
        // What is in view, as the panel says it: while a layout is waited for it says that instead.
        inView: () => [...document.querySelectorAll('main [role="status"]')].map(item => item.textContent.match(/^(\d+) nod[oi] · (\d+) relazion/)).find(Boolean),
        failed: () => [...document.querySelectorAll('main [role="alert"]')].map(item => item.textContent).find(text => text.includes('Impossibile disporre il grafo')),
        // When a graph of the view named is painted: its counts, or the reason it is not.
        painted: view => new Promise((resolve, reject) => {
          const deadline = performance.now() + 60000;
          let last = 0;
          const check = () => {
            const { things, inView, failed } = window.explorer;
            if (failed()) return reject(new Error(failed()));
            const counts = document.querySelector('main')?.getAttribute('aria-label') === view && inView(), drawn = counts ? things().length : 0;
            if (drawn > 0 && drawn === last) {
              return requestAnimationFrame(() => resolve({ painted_ms: Math.round(performance.now()), nodes: Number(counts[1]), drawn, edges: Number(counts[2]) }));
            }
            if (performance.now() > deadline) return reject(new Error(`not painted in 60 s: ${drawn} nodes`));
            last = drawn;
            requestAnimationFrame(check);
          };
          requestAnimationFrame(check);
        }),
      };
    });
    const graph = await page.evaluate(() => window.explorer.painted('Mappa logica'));
    const selections = await page.evaluate(async () => {
      const times = [];
      for (let i = 0; i < 20; i += 1) {
        const things = window.explorer.things();
        const thing = things[Math.floor((i * things.length) / 20)];
        const name = thing.getAttribute('aria-label');
        const start = performance.now();
        thing.click();
        await new Promise(resolve => {
          const check = () => {
            const shown = document.querySelector('aside[aria-label="Dettaglio"] [aria-live="polite"]')?.textContent;
            return shown && (name === shown || name.startsWith(`${shown},`)) ? requestAnimationFrame(() => resolve()) : requestAnimationFrame(check);
          };
          requestAnimationFrame(check);
        });
        times.push(Math.round(performance.now() - start));
      }
      return times;
    });
    // The same graph laid out again with the worker already loaded: to Fisica, painted, and back to Logica.
    // React renders a click in a microtask, so each wait starts on the next frame and needs the view on and no
    // layout pending.
    const relayout_ms = await page.evaluate(async () => {
      const go = word => [...document.querySelectorAll('[role="toolbar"][aria-label="Daodan"] button')].find(button => button.textContent === word).click();
      go('Fisica');
      await window.explorer.painted('Mappa fisica');
      const start = performance.now();
      go('Logica');
      await window.explorer.painted('Mappa logica');
      return Math.round(performance.now() - start);
    });
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('HeapProfiler.collectGarbage');
    await cdp.send('Performance.enable');
    const { metrics } = await cdp.send('Performance.getMetrics');
    const metric = name => metrics.find(item => item.name === name)?.value;
    const sorted = [...selections].sort((a, b) => a - b);
    const environment = await page.evaluate(() => ({
      agent: navigator.userAgent, cores: navigator.hardwareConcurrency, viewport: [innerWidth, innerHeight],
      layouts: window.__layouts,
    }));
    return {
      url, browser: `${browser.version()} headless`, fps, ...environment, ...graph, relayout_ms,
      selection_ms: { p50: sorted[9], p95: sorted[18], max: sorted[19], all: selections },
      js_heap_mb: Math.round((metric('JSHeapUsedSize') / 2 ** 20) * 10) / 10, dom_nodes: metric('Nodes'),
    };
  } finally {
    await browser.close();
  }
}
