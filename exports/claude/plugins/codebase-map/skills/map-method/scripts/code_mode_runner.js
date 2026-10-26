// Trusted transport runner. Model code is data evaluated in a separate Worker.
// The bootstrap token stays in this realm; Worker messages never supply it.
const encoder = new TextEncoder();
const reader = Deno.stdin.readable.pipeThrough(new TextDecoderStream()).getReader();
let buffered = "";
async function readLine() {
  for (;;) {
    const newline = buffered.indexOf("\n");
    if (newline >= 0) {
      const line = buffered.slice(0, newline);
      buffered = buffered.slice(newline + 1);
      return line;
    }
    const { value, done } = await reader.read();
    if (done) return null;
    buffered += value;
  }
}

const bootstrap = JSON.parse(await readLine());
const token = bootstrap.token;
const pending = new Set();
let ended = false;
let writes = Promise.resolve();
function send(payload) {
  const bytes = encoder.encode(JSON.stringify({ ...payload, token }) + "\n");
  writes = writes.then(async () => {
    let offset = 0;
    while (offset < bytes.length) offset += await Deno.stdout.write(bytes.subarray(offset));
  });
  return writes;
}

const source = `
(() => {
  const pending = new Map();
  let sequence = 0;
  let initialized = false;
  const notify = self.postMessage.bind(self);
  const quiet = () => {};
  globalThis.console = Object.freeze({log: quiet, info: quiet, debug: quiet,
    warn: quiet, error: quiet, table: quiet, trace: quiet, dir: quiet,
    time: quiet, timeEnd: quiet, assert: quiet, clear: quiet});
  self.onmessage = async ({data}) => {
    if (initialized) {
      const waiter = pending.get(data.id);
      if (!waiter) return;
      pending.delete(data.id);
      if (data.error) waiter.reject(new Error(data.error));
      else waiter.resolve(data.value);
      return;
    }
    initialized = true;
    const tools = Object.create(null);
    for (const name of data.tools) {
      Object.defineProperty(tools, name, {value: (arguments_) => new Promise((resolve, reject) => {
        const id = ++sequence;
        pending.set(id, {resolve, reject});
        notify({type: 'call', id, name, arguments: arguments_});
      })});
    }
    Object.freeze(tools);
    try {
      const factory = new Function('tools', 'catalog', '"use strict"; return (' + data.code + '\\n);');
      const program = factory(tools, data.catalog);
      if (typeof program !== 'function') throw new Error('code must be a JavaScript function');
      const value = await program();
      if (pending.size) throw new Error('await every tool call before returning');
      if (value === undefined) throw new Error('return a JSON value from the program');
      notify({type: 'result', value});
    } catch (error) {
      notify({type: 'error', error: String(error?.message || error)});
    }
  };
})();`;
const url = URL.createObjectURL(new Blob([source], { type: "application/javascript" }));
const worker = new Worker(url, { type: "module" });
URL.revokeObjectURL(url);

async function finish(payload) {
  if (ended) return;
  ended = true;
  worker.terminate();
  try {
    await send(payload);
    Deno.exit(payload.type === "result" ? 0 : 1);
  } catch (_) {
    Deno.exit(1);
  }
}

worker.onmessage = async ({ data }) => {
  if (ended) return;
  try {
    if (!data || typeof data !== "object") throw new Error("invalid worker protocol message");
    if (data.type === "call") {
      if (!Number.isSafeInteger(data.id) || data.id < 1 || pending.has(data.id)) {
        throw new Error("invalid or duplicate protocol request id");
      }
      pending.add(data.id);
      await send({ type: "call", id: data.id, name: data.name, arguments: data.arguments });
    } else if (data.type === "result") {
      if (pending.size) throw new Error("await every tool call before returning");
      const text = JSON.stringify(data.value);
      if (text === undefined || encoder.encode(text).length > bootstrap.maxOutputBytes) {
        throw new Error("final output exceeds limit; return a smaller selection");
      }
      await finish({ type: "result", value: data.value });
    } else if (data.type === "error") {
      await finish({ type: "error", error: String(data.error).slice(0, 4000) });
    } else {
      throw new Error("unknown worker protocol message");
    }
  } catch (error) {
    await finish({ type: "error", error: String(error?.message || error).slice(0, 4000) });
  }
};
worker.onerror = (event) => {
  event.preventDefault();
  finish({ type: "error", error: String(event.message).slice(0, 4000) });
};
worker.postMessage({ code: bootstrap.code, catalog: bootstrap.catalog, tools: bootstrap.tools });

while (!ended) {
  const line = await readLine();
  if (line === null) {
    await finish({ type: "error", error: "host protocol closed" });
    break;
  }
  const reply = JSON.parse(line);
  if (!pending.delete(reply.id)) {
    await finish({ type: "error", error: "unknown host protocol response" });
    break;
  }
  worker.postMessage(reply);
}
