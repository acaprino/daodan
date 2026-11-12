// Runs inside the container. Exact recorder of the calls a test run executes: one
// file, loaded twice by the same process.
//
//   babel.config.js   plugins: ['<this file>']
//   NODE_OPTIONS="--require <this file>" DYN_ROOT=<project root> DYN_OUT=<out>-%p.json node jest --runInBand
//
// As a Babel plugin it passes the callee of every call of a project file through a
// recorder: f(a) becomes globalThis.__dynC(site, f)(a), o.m(a) becomes
// globalThis.__dynM(site, o, 'm')(a). As a preload it defines the two recorders in
// every realm and asks the inspector where each called function is defined; on exit
// it writes the sites in the shape of dynamic_map.js, with "exact": true.
// Not recorded: optional calls, private methods, super, import, require, eval,
// computed members and the calls on Jest's own object, which Jest hoists.
'use strict';
const path = require('path');

const ROOT = process.env.DYN_ROOT ? path.resolve(process.env.DYN_ROOT) + '/' : null;

function relative(url) {
  if (!url || !ROOT) return null;
  const file = url.startsWith('file://') ? decodeURIComponent(url.slice(7)) : url;
  return file.startsWith(ROOT) && !file.includes('/node_modules/') ? file.slice(ROOT.length) : null;
}

function calleeKind(url) {
  if (!url) return { kind: 'native' };
  if (url.startsWith('node:')) return { kind: 'runtime', module: url };
  const at = url.lastIndexOf('/node_modules/');
  if (at >= 0) {
    const parts = url.slice(at + 14).split('/');
    return { kind: 'package', module: parts[0].startsWith('@') ? parts.slice(0, 2).join('/') : parts[0] };
  }
  const file = relative(url);
  return file ? { kind: 'project', file } : { kind: 'other', module: url };
}

function install(outFile) {
  const fs = require('fs');
  const vm = require('vm');
  const inspector = require('inspector');
  const session = new inspector.Session();
  session.connect();
  // On the thread that owns the session the answer arrives before post returns.
  const post = (method, params) => { let out; session.post(method, params, (error, result) => { out = result; }); return out; };
  const urls = new Map();
  const interned = new Map();
  session.on('Debugger.scriptParsed', message => {
    const url = message.params.url;
    if (!interned.has(url)) interned.set(url, url);
    urls.set(message.params.scriptId, interned.get(url));
  });
  post('Debugger.enable');
  post('Debugger.setSkipAllPauses', { skip: true });
  const holder = { fn: null };
  globalThis[Symbol.for('daodan.dynamic')] = holder;
  const holderId = post('Runtime.evaluate', { expression: 'globalThis[Symbol.for("daodan.dynamic")]' }).result.objectId;

  // A bound function or a proxy is located at its target.
  function location(objectId, depth) {
    const answer = post('Runtime.getProperties', { objectId, ownProperties: true });
    let target = null;
    for (const property of (answer && answer.internalProperties) || []) {
      if (property.name === '[[FunctionLocation]]') return property.value.value;
      if (property.name === '[[TargetFunction]]' || property.name === '[[Target]]') target = property.value.objectId;
    }
    return target && depth < 4 ? location(target, depth + 1) : null;
  }

  const known = new WeakMap();   // function -> index in callees
  const callees = [];
  const calleeIndex = new Map();
  const sites = new Map();       // site id -> Set of callee indexes
  let lookups = 0;
  function locate(fn) {
    lookups += 1;
    holder.fn = fn;
    const own = post('Runtime.getProperties', { objectId: holderId, ownProperties: true });
    const id = own.result.find(property => property.name === 'fn').value.objectId;
    const at = location(id, 0);
    post('Runtime.releaseObject', { objectId: id });
    holder.fn = null;
    let name = '';
    try { if (typeof fn.name === 'string') name = fn.name; } catch (error) { /* a proxy may refuse */ }
    const callee = { ...calleeKind(at ? urls.get(at.scriptId) || '' : ''), name, line: at ? at.lineNumber : 0 };
    const key = `${callee.kind}|${callee.file || callee.module || ''}|${name}|${callee.line}`;
    if (!calleeIndex.has(key)) { calleeIndex.set(key, callees.length); callees.push(callee); }
    return calleeIndex.get(key);
  }
  function record(id, fn) {
    let index = known.get(fn);
    if (index === undefined) known.set(fn, index = locate(fn));
    const seen = sites.get(id);
    if (seen) seen.add(index); else sites.set(id, new Set([index]));
  }
  const bind = Function.prototype.bind;
  const dynC = (id, fn) => { if (typeof fn === 'function') record(id, fn); return fn; };
  const dynM = (id, object, key) => {
    const fn = object[key];
    if (typeof fn !== 'function') return fn;
    record(id, fn);
    return bind.call(fn, object);
  };
  const define = target => {
    Object.defineProperty(target, '__dynC', { value: dynC, configurable: true, writable: true });
    Object.defineProperty(target, '__dynM', { value: dynM, configurable: true, writable: true });
  };
  define(globalThis);
  // Jest runs each test file in a context of its own: the recorders go there too.
  const createContext = vm.createContext;
  vm.createContext = function (...args) {
    const context = createContext.apply(this, args);
    define(vm.runInContext('globalThis', context));
    return context;
  };

  // A Jest worker that does not exit in time gets SIGTERM: the sites are written then too.
  let written = false;
  const flush = () => {
    if (written || !sites.size) return;
    written = true;
    const out = [];
    for (const [id, seen] of sites) {
      const parts = id.split('|');
      out.push({ file: parts[0], line: Number(parts[1]), column: Number(parts[2]), name: parts.slice(3).join('|'),
        callees: [...seen].map(index => callees[index]) });
    }
    fs.writeFileSync(outFile.replace('%p', String(process.pid)),
      JSON.stringify({ exact: true, stats: { sites: out.length, callees: callees.length, lookups }, sites: out }));
  };
  process.on('exit', flush);
  process.on('SIGTERM', () => { flush(); process.exit(143); });
}

if (process.env.DYN_OUT && ROOT && !globalThis.__dynC) install(process.env.DYN_OUT);

module.exports = function plugin({ types: t }) {
  const helper = name => t.memberExpression(t.identifier('globalThis'), t.identifier(name));
  const lines = new WeakMap();
  const root = node => {
    while (node && (node.type === 'MemberExpression' || node.type === 'CallExpression')) node = node.object || node.callee;
    return node && node.type === 'Identifier' ? node.name : null;
  };
  return {
    name: 'daodan-dynamic-record',
    visitor: {
      'CallExpression|NewExpression': {
        exit(nodePath, state) {
          const file = relative(state.filename);
          if (!file) return;
          const node = nodePath.node;
          const callee = node.callee;
          const member = callee.type === 'MemberExpression';
          if (!member && callee.type !== 'Identifier') return;
          if (root(callee) === 'jest') return;
          const token = member ? callee.property : callee;
          let name;
          if (!member) name = callee.name === 'require' || callee.name === 'eval' ? null : callee.name;
          else if (callee.object.type === 'Super') name = null;
          else if (!callee.computed) name = token.type === 'Identifier' ? token.name : null;
          else name = token.type === 'StringLiteral' ? token.value : null;
          if (!name || !token.loc) return;
          if (!lines.has(state.file)) lines.set(state.file, state.file.code.split('\n'));
          const line = token.loc.start.line - 1;
          const column = Buffer.byteLength((lines.get(state.file)[line] || '').slice(0, token.loc.start.column), 'utf8');
          const id = t.stringLiteral(`${file}|${line}|${column}|${name}`);
          node.callee = member && node.type === 'CallExpression'
            ? t.callExpression(helper('__dynM'), [id, callee.object, callee.computed ? token : t.stringLiteral(name)])
            : t.callExpression(helper('__dynC'), [id, callee]);
        },
      },
    },
  };
};
