'use strict';
// Starts the app the project declares, waits for its port, stops it (plan task 11.2). Runs INSIDE the container,
// under Daodan's Node, over the project's copy:
//   node app.cjs <out dir> <name> <cwd> <port|-> <limit seconds> <command>
// writes <out dir>/app-<name>.json and app-<name>.log; the command is the declared one, run by `sh -c`, never changed.
// `startApp`, `waitReady` and `stopApp` are the exploration's too (it opens the browser between the two).
const fs = require('node:fs');
const net = require('node:net');
const { spawn } = require('node:child_process');

const GRACE = 10000; // ms between SIGTERM and SIGKILL of the app's process group
// What a dev server prints is a log line, which has no grammar: a regular expression reads the local address it says
// (the only address Daodan uses without a declared port: never a scan).
const PRINTED = /https?:\/\/(?:localhost|127\.0\.0\.1|\[::1\]):\d+\/?/;
const COLOR = /\x1b\[[0-9;]*m/g; // the log line's colour codes, a log's too
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

function startApp(cwd, command) {
  const env = { ...process.env, FORCE_COLOR: '0', NO_COLOR: '1', CI: '1', BROWSER: 'none' };
  const child = spawn('sh', ['-c', command], { cwd, env, detached: true, stdio: ['ignore', 'pipe', 'pipe'] });
  const app = { child, text: '', ended: null };
  for (const stream of [child.stdout, child.stderr]) stream.on('data', chunk => { app.text += chunk; });
  child.on('exit', (code, signal) => { app.ended = { code, signal }; });
  child.on('error', error => { app.text += `${error.message}\n`; app.ended = { code: null, signal: null }; });
  return app;
}

function canConnect(port) { // `localhost` may be IPv4 or IPv6: either answers
  const one = host => new Promise(resolve => {
    const socket = net.connect({ host, port, timeout: 500 });
    socket.on('connect', () => { socket.destroy(); resolve(true); });
    socket.on('error', () => resolve(false));
    socket.on('timeout', () => { socket.destroy(); resolve(false); });
  });
  return Promise.all([one('127.0.0.1'), one('::1')]).then(found => found.some(Boolean));
}

// `{state, address, port}`: ready; exited (before the port answered); not_ready (the port or the printed address
// never answered); no_address (alive, no declared port, nothing printed).
async function waitReady(app, declared, limit) {
  const deadline = Date.now() + limit * 1000;
  let printed = null;
  while (Date.now() < deadline) {
    if (app.ended) return { state: 'exited' };
    if (declared) {
      if (await canConnect(declared)) return { state: 'ready', address: `http://localhost:${declared}/`, port: declared };
    } else {
      printed = printed || PRINTED.exec(app.text.replace(COLOR, ''));
      if (printed) {
        const port = Number(new URL(printed[0]).port);
        if (await canConnect(port)) return { state: 'ready', address: printed[0], port };
      }
    }
    await sleep(200);
  }
  return app.ended ? { state: 'exited' } : { state: declared || printed ? 'not_ready' : 'no_address' };
}

// The live members of the app's process group, from /proc (Linux, the container's; no `ps` to depend on): a zombie is
// gone, not alive. `pid (name) state ppid pgrp ...`: the name may hold spaces and parentheses, so read after its last `)`.
function members(pid) {
  const found = [];
  for (const entry of fs.readdirSync('/proc')) {
    if (!/^\d+$/.test(entry)) continue; // a process folder's name: not a source text
    try {
      const stat = fs.readFileSync(`/proc/${entry}/stat`, 'utf8');
      const [state, , group] = stat.slice(stat.lastIndexOf(')') + 2).split(' ');
      if (group !== String(pid) || state === 'Z') continue;
      found.push(`${entry} ${fs.readFileSync(`/proc/${entry}/cmdline`, 'utf8').split('\0').join(' ').trim()}`);
    } catch (error) { /* it ended while we looked */ }
  }
  return found;
}

// `{stopped, left}`: stopped 'exited' (it ended on its own), 'term' (SIGTERM was enough), 'kill' (SIGKILL after GRACE);
// left the processes of its group and the port still answering.
async function stopApp(app, port) {
  const pid = app.child.pid;
  let stopped = 'exited';
  if (members(pid).length) {
    stopped = 'term';
    try { process.kill(-pid, 'SIGTERM'); } catch (error) { /* the group is gone */ }
    const until = Date.now() + GRACE;
    while (members(pid).length && Date.now() < until) await sleep(100);
    if (members(pid).length) {
      stopped = 'kill';
      try { process.kill(-pid, 'SIGKILL'); } catch (error) { /* the group is gone */ }
      await sleep(1000);
    }
  }
  const left = members(pid);
  // the kernel (or the sandbox) closes a dead process's listener a moment later: wait for it before saying it is left
  let open = port && await canConnect(port);
  for (let waited = 0; open && waited < 3000; waited += 200) { await sleep(200); open = await canConnect(port); }
  if (open) left.push(`port ${port} still accepts connections`);
  return { stopped, left };
}

const tail = text => text.replace(COLOR, '').trim().split('\n').slice(-8).map(line => line.trim()).join(' | ').slice(-600);

// The whole run: start, wait, `between(ready, out, name)` (the exploration, which writes its own files) while the app
// is up, stop; writes app-<name>.json and app-<name>.log. A throw of `between` is the record's `between_error`: the
// app is stopped all the same.
async function run([out, name, cwd, port, limit, command], between) {
  fs.mkdirSync(out, { recursive: true });
  const started = Date.now();
  const app = startApp(cwd, command);
  const ready = await waitReady(app, port === '-' ? null : Number(port), Number(limit));
  const record = { ...ready, address: ready.address || null, port: ready.port || null };
  if (ready.state === 'exited') Object.assign(record, { exit: app.ended.code, signal: app.ended.signal });
  if (ready.state === 'ready' && between) {
    try { await between(ready, out, name); } catch (error) { record.between_error = String(error && error.stack || error).slice(0, 800); }
  }
  record.seconds = Math.round((Date.now() - started) / 1000);
  Object.assign(record, await stopApp(app, record.port), { tail: tail(app.text) });
  fs.writeFileSync(`${out}/app-${name}.log`, app.text);
  fs.writeFileSync(`${out}/app-${name}.json`, JSON.stringify(record));
}

// The app's pipes may outlive its group: the driver ends by itself once it has written its record.
if (require.main === module) run(process.argv.slice(2)).then(() => process.exit(0), error => { console.error('DRIVER FAILED', error); process.exit(1); });
module.exports = { startApp, waitReady, stopApp, canConnect, tail, run, PRINTED };
