// Measures the explorer at the address open in the page, for the Playwright MCP tool `browser_run_code_unsafe`
// (filename). It opens the address in a separate headless Chrome at 1440x900, because a window that is hidden
// or covered throttles frames to about one per second, then reports: every ELK layout in the worker from the
// request to the answer (the first includes loading ELK into the worker), the time from navigation to the
// painted graph (every visible node in the DOM, then two frames), 20 selections spread over the visible nodes
// (click in the DOM until the frame after the inspector shows the node), the same graph laid out again with the
// worker loaded, and the page's JS heap and DOM nodes after a collection. The worker's own heap is not counted.
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
    const graph = await page.evaluate(() => new Promise((resolve, reject) => {
      const deadline = performance.now() + 60000;
      const check = () => {
        const foot = document.querySelector('.canvas-foot')?.textContent ?? '';
        const visible = Number(foot.match(/^(\d+) nodi/)?.[1] ?? NaN);
        const drawn = document.querySelectorAll('.react-flow__node').length;
        const failed = document.querySelector('.canvas-state.bad')?.textContent;
        if (failed) return reject(new Error(failed));
        if (visible > 0 && drawn === visible) {
          return requestAnimationFrame(() => requestAnimationFrame(() => resolve({
            painted_ms: Math.round(performance.now()), nodes: visible,
            edges: document.querySelectorAll('.react-flow__edge').length, footer: foot,
          })));
        }
        if (performance.now() > deadline) return reject(new Error(`not painted in 60 s: ${drawn}/${visible} nodes`));
        requestAnimationFrame(check);
      };
      check();
    }));
    const selections = await page.evaluate(async () => {
      const buttons = [...document.querySelectorAll('.react-flow__node .node-button')];
      const times = [];
      for (let i = 0; i < 20; i += 1) {
        const button = buttons[Math.floor((i * buttons.length) / 20)];
        const name = button.querySelector('.node-name').textContent;
        const start = performance.now();
        button.click();
        await new Promise(resolve => {
          const check = () => (document.querySelector('.inspector h2')?.textContent === name
            ? requestAnimationFrame(() => resolve()) : requestAnimationFrame(check));
          requestAnimationFrame(check);
        });
        times.push(Math.round(performance.now() - start));
      }
      return times;
    });
    // The same graph laid out again with the worker already loaded: to Fisica, painted, and back to Logica.
    // React renders a click in a microtask, so each wait starts on the next frame and needs the tab on and no
    // layout pending.
    const relayout_ms = await page.evaluate(async () => {
      const painted = label => new Promise(resolve => {
        const check = () => {
          const on = document.querySelector('.tab.on')?.textContent === label;
          const pending = [...document.querySelectorAll('.canvas-state')].some(item => item.textContent.startsWith('Dispongo'));
          const visible = Number(document.querySelector('.canvas-foot')?.textContent.match(/^(\d+) nodi/)?.[1] ?? NaN);
          const drawn = document.querySelectorAll('.react-flow__node').length;
          if (on && !pending && visible > 0 && drawn === visible) requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
          else requestAnimationFrame(check);
        };
        requestAnimationFrame(check);
      });
      const tab = label => [...document.querySelectorAll('.tab')].find(button => button.textContent === label);
      tab('Fisica').click();
      await painted('Fisica');
      const start = performance.now();
      tab('Logica').click();
      await painted('Logica');
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
