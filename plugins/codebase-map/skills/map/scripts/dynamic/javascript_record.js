// Runs inside the container. Exact recorder of the calls a test run executes: one
// file, loaded twice by the same process. It is the recorder of the dynamic step's
// JavaScript observer (dynamic/javascript.py), which carries it into the container.
//
//   NODE_OPTIONS="--require <this file>" DYN_ROOT=<project root> DYN_OUT=<out>-%p.json \
//     DYN_BABEL=<a @babel/core outside the project> npm test
//
// As a Babel plugin it passes the callee of every call of a project file through a
// recorder: f(a) becomes globalThis.__dynC(site, f)(a), o.m(a) becomes
// globalThis.__dynM(site, o, 'm')(a), (0, o.m)(a) becomes (0, globalThis.__dynC(site, o.m))(a).
// As a preload it defines the recorders in every realm and asks the inspector where
// each called function is defined; on exit it writes the sites, with "exact": true.
//
// With DYN_BABEL the preload also puts the plugin where the code is compiled, and
// the project is not changed:
// - a source Node runs as written (CommonJS through Module._compile, ES modules
//   through module.registerHooks, where Node has it) is printed by that Babel;
// - a @babel/core the run loads itself (babel-jest, @babel/register) gets the plugin
//   in every transform;
// - code another tool printed (ts-jest, Vitest's Vite, a TypeScript loader), on its
//   way to Node's loaders or to the vm module the runners evaluate with, is printed
//   again by that Babel through the source map inline in it: a call is a site only
//   where that map leads to the same name in the file as written.
// A callee is placed through the source map inline in the script that defines it, at
// the function of the file as written whose head holds that place.
// Without DYN_BABEL the plugin comes from the project's Babel configuration:
//   babel.config.js   plugins: ['<this file>']
// A project file V8 ran unrecorded (printed with no inline map, or loaded where the
// recorder has no hook) is named in "unobserved".
// Not recorded: optional calls, private methods, super, import, require, eval,
// computed members and the calls on Jest's own object, which Jest hoists.
'use strict';
const path = require('path');
const { fileURLToPath } = require('url');

const slash = file => (path.sep === '/' ? file : file.split(path.sep).join('/'));
const ROOT = process.env.DYN_ROOT ? slash(path.resolve(process.env.DYN_ROOT)) + '/' : null;

function relative(url) {
  if (!url || !ROOT) return null;
  const file = slash(url.startsWith('file://') ? fileURLToPath(url) : url.split('?')[0]);
  return file.startsWith(ROOT) && !file.includes('/node_modules/') ? file.slice(ROOT.length) : null;
}

const versions = new Map();   // package folder -> the version its package.json states
function version(folder) {
  if (!versions.has(folder)) {
    let stated = null;
    try { stated = JSON.parse(require('fs').readFileSync(`${folder}/package.json`, 'utf8')).version || null; } catch (error) { /* none */ }
    versions.set(folder, stated);
  }
  return versions.get(folder);
}

function calleeKind(url) {
  if (!url) return { kind: 'native' };
  if (url.startsWith('node:')) return { kind: 'runtime', module: url };
  url = slash(url.startsWith('file://') ? fileURLToPath(url) : url);
  const at = url.lastIndexOf('/node_modules/');
  if (at >= 0) {
    const parts = url.slice(at + 14).split('/');
    const module = parts[0].startsWith('@') ? parts.slice(0, 2).join('/') : parts[0];
    return { kind: 'package', module, version: version(`${url.slice(0, at + 14)}${module}`) };
  }
  const file = relative(url);
  return file ? { kind: 'project', file } : { kind: 'other', module: url };
}

// The byte column of a place of `text`'s line, whose columns Babel and source maps count in UTF-16 units.
const bytes = (lines, line, column) => Buffer.byteLength((lines[line] || '').slice(0, column), 'utf8');
const texts = new Map();      // project file -> its text as written
function written(file) {
  if (!texts.has(file)) {
    let text = null;
    try { text = require('fs').readFileSync(ROOT + file, 'utf8').replace(/^﻿/, ''); } catch (error) { /* gone */ }
    texts.set(file, text);
  }
  return texts.get(file);
}

// The source map a data: URL holds.
function decoded(url) {
  const comma = url.indexOf(',');
  const data = url.slice(comma + 1);
  return JSON.parse(/;base64$/.test(url.slice(0, comma)) ? Buffer.from(data, 'base64').toString('utf8') : decodeURIComponent(data));
}

// The project file an `originalSource` of the source map of `file`'s code names (relative to `file`).
function source(file, original, root) {
  if (!original) return null;
  if (original.startsWith('file://')) return relative(original);
  return relative(slash(path.resolve(path.dirname(ROOT + file), (root || '') + original)));
}

// A source map with the generated columns of its first line moved right by `by`: the
// first segment of a line is the only absolute one, so only its first field changes.
const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
function shifted(map, by) {
  const mappings = map.mappings || '';
  if (!by || !mappings || mappings[0] === ';') return map;
  let value = 0, shift = 0, at = 0, digit;
  do { digit = B64.indexOf(mappings[at++]); value += (digit & 31) << shift; shift += 5; } while (digit & 32);
  value = (value & 1 ? -(value >>> 1) : value >>> 1) + by;
  let vlq = value < 0 ? (-value << 1) | 1 : value << 1, out = '';
  do { digit = vlq & 31; vlq >>>= 5; out += B64[vlq ? digit | 32 : digit]; } while (vlq);
  return { ...map, mappings: out + mappings.slice(at) };
}

// The plugin where the code is compiled: see the head of the file. A project file whose
// code runs as it is goes to `unobserved`; `starts` is the cache of the function it returns.
function hook(babelPath, unobserved, starts) {
  const fs = require('fs');
  const Module = require('module');
  const vm = require('vm');
  const own = require(babelPath);
  const MAP = /^[ \t]*\/\/[#@] sourceMappingURL=(data:application\/json[^\s,]*,\S+)[ \t]*$/gm;
  const print = (code, filename, sourceType, origin) => own.transformSync(code, {
    filename, sourceType, babelrc: false, configFile: false, retainLines: true, compact: false,
    plugins: [[plugin, origin ? { origin } : {}]], sourceMaps: 'inline', inputSourceMap: origin ? origin.input : false,
    parserOpts: { allowReturnOutsideFunction: sourceType === 'script', allowAwaitOutsideFunction: true, plugins: ['importAttributes'] },
  }).code;
  // `code` of `filename` as it runs here: printed with the plugin when it is the file as written, or when another
  // tool printed it with an inline map; else as it is, and named. `prefix`: the columns a wrapper added to line 0.
  const recorded = (code, filename, sourceType, prefix) => {
    const file = typeof code === 'string' && typeof filename === 'string' && relative(filename);
    if (!file || code.includes('globalThis.__dyn')) return code;   // not the project's, or printed with the plugin
    try {
      if (code === written(file)) return print(code, filename, sourceType, null);
      const found = [...code.matchAll(MAP)].pop();
      if (found && written(file) !== null) {
        const input = shifted(decoded(found[1]), prefix);
        const map = new Module.SourceMap(input);
        return print(code.slice(0, found.index) + code.slice(found.index + found[0].length), filename, sourceType,
          { input, map, lines: written(file).split('\n'), same: original => source(file, original, input.sourceRoot) === file });
      }
    } catch (error) { /* a syntax this Babel does not read: the file runs as it is */ }
    unobserved.add(file);
    return code;
  };
  const compile = Module.prototype._compile;
  Module.prototype._compile = function (content, filename, ...rest) {
    return compile.call(this, recorded(content, filename, 'script', 0), filename, ...rest);
  };
  if (typeof Module.registerHooks === 'function') {
    Module.registerHooks({
      load(url, context, nextLoad) {
        const loaded = nextLoad(url, context);
        if (loaded.format !== 'module' || loaded.source == null || !url.startsWith('file://')) return loaded;
        return { ...loaded, source: recorded(String(loaded.source), fileURLToPath(url), 'module', 0) };
      },
    });
  }
  // The vm functions the runners evaluate a module with (Jest's compileFunction, Vitest's runInThisContext and
  // Script): a negative columnOffset is a wrapper's prefix on line 0, which the printed code no longer has.
  const evaluate = (code, options) => {
    options = typeof options === 'string' ? { filename: options } : options || {};
    const prefix = options.columnOffset < 0 && !options.lineOffset ? -options.columnOffset : 0;
    const printed = recorded(code, options.filename, 'script', prefix);
    return [printed, printed !== code && prefix ? { ...options, columnOffset: 0 } : options];
  };
  for (const [name, at] of [['compileFunction', 2], ['runInThisContext', 1], ['runInContext', 2], ['runInNewContext', 2]]) {
    const original = vm[name];
    vm[name] = function (code, ...rest) {
      const [printed, options] = evaluate(code, rest[at - 1]);
      rest[at - 1] = options;
      return original.call(this, printed, ...rest);
    };
  }
  vm.Script = new Proxy(vm.Script, {   // a proxy, so Node's own scripts are still instances of it
    construct: (Script, [code, options], target) => Reflect.construct(Script, evaluate(code, options), target),
  });
  Module.syncBuiltinESMExports();   // the ES module views of vm see the hooks too
  const withPlugin = options => ({
    ...options, retainLines: true, sourceMaps: options && options.sourceMaps === 'inline' ? 'inline' : 'both',
    plugins: [...((options && options.plugins) || []), plugin],
  });
  const wrapped = new WeakMap();
  const load = Module._load;
  Module._load = function (request, ...rest) {
    const core = load.call(this, request, ...rest);
    if (request !== '@babel/core' || !core || typeof core.transformSync !== 'function') return core;
    if (!wrapped.has(core)) {
      const patched = {};
      for (const name of ['transform', 'transformSync', 'transformAsync']) {
        patched[name] = (code, options, callback) => {
          if (typeof options === 'function') [options, callback] = [{}, options];
          return callback ? core[name](code, withPlugin(options), callback) : core[name](code, withPlugin(options));
        };
      }
      wrapped.set(core, new Proxy(core, { get: (target, key) => (key in patched ? patched[key] : target[key]) }));
    }
    return wrapped.get(core);
  };
  // Where each function and class of a project file as written starts and where its body starts: [line, column,
  // byte column, type, body line, body column]; nothing for a file this Babel does not read (a .vue file).
  return file => {
    if (!starts.has(file)) {
      const found = [];
      const text = written(file);
      try {
        const syntax = /\.[cm]?tsx?$/.test(file) ? ['typescript', ...(/x$/.test(file) ? ['jsx'] : [])] : ['jsx'];
        const ast = own.parseSync(text, { filename: ROOT + file, babelrc: false, configFile: false, sourceType: 'unambiguous',
          parserOpts: { plugins: [...syntax, 'decorators-legacy', 'importAttributes'], allowReturnOutsideFunction: true } });
        const rows = text.split('\n');
        own.traverse(ast, {
          'Function|Class'(nodePath) {
            const { start } = nodePath.node.loc, body = nodePath.node.body.loc.start;
            found.push([start.line - 1, start.column, bytes(rows, start.line - 1, start.column),
              nodePath.isClass() ? 'class' : 'function', body.line - 1, body.column]);
          },
        });
      } catch (error) { /* its functions are not placed */ }
      starts.set(file, found);
    }
    return starts.get(file);
  };
}

function install(outFile) {
  const fs = require('fs');
  const vm = require('vm');
  const Module = require('module');
  const inspector = require('inspector');
  const { threadId } = require('worker_threads');
  const session = new inspector.Session();
  // A process without an inspector (the parent of `node --test`) runs as it is, unrecorded.
  try { session.connect(); } catch (error) { return; }
  // On the thread that owns the session the answer arrives before post returns.
  const post = (method, params) => { let out; session.post(method, params, (error, result) => { out = result; }); return out; };
  const urls = new Map();
  const interned = new Map();
  const ran = new Set();         // project files V8 parsed
  const maps = new Map();        // project script id -> the inline source map V8 read in it, by url and hash
  const loaded = new Map();      // that url and hash -> the map's data: URL, then the map
  session.on('Debugger.scriptParsed', message => {
    const { url, scriptId, sourceMapURL, hash, scriptLanguage } = message.params;
    if (!interned.has(url)) interned.set(url, url);
    urls.set(scriptId, interned.get(url));
    const file = scriptLanguage !== 'WebAssembly' && relative(url);
    if (!file) return;
    ran.add(file);
    if (!sourceMapURL || !sourceMapURL.startsWith('data:')) return;
    const key = `${url}|${hash}`;
    if (!loaded.has(key)) loaded.set(key, sourceMapURL);
    maps.set(scriptId, key);
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
  function mapOf(scriptId) {
    const key = maps.get(scriptId);
    let map = key && loaded.get(key);
    if (typeof map === 'string') {
      try { map = new Module.SourceMap(decoded(map)); } catch (error) { map = null; }
      loaded.set(key, map);
    }
    return map || null;
  }

  const known = new WeakMap();   // function -> index in callees
  const callees = [];
  const calleeIndex = new Map();
  const sites = new Map();       // site id -> Set of callee indexes
  const unobserved = new Set();  // project files that ran unrecorded
  const marked = new Set();      // project files whose recorded code ran
  let startsOf = () => [];
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
    // V8 places a function at its parameters, in the code it runs: the script's inline map leads back to the file
    // as written, and the function declared there is the innermost one whose head (start to body) holds the place.
    const map = callee.kind === 'project' && mapOf(at.scriptId);
    const origin = map ? map.findEntry(at.lineNumber, at.columnNumber) : {};
    let start = null;
    if (map && origin.generatedLine === at.lineNumber && origin.originalLine !== undefined
        && source(callee.file, origin.originalSource, map.payload.sourceRoot) === callee.file) {
      const place = [origin.originalLine, origin.originalColumn];
      const before = (a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] <= b[1]);
      for (const item of startsOf(callee.file)) {
        if (before(item, place) && before(place, [item[4], item[5]]) && (!start || before(start, item))) start = item;
      }
    }
    if (start) Object.assign(callee, { line: start[0], column: start[2], type: start[3] });
    const key = `${callee.kind}|${callee.file || callee.module || ''}|${name}|${callee.line}|${callee.column}`;
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
  const { isProxy } = require('util').types;
  const dynC = (id, fn) => { if (typeof fn === 'function') record(id, fn); return fn; };
  // A bound function adds no frame to the stack, which code that finds its caller there counts on; binding reads
  // the function's length and name, which a proxy (Chai's matchers) may refuse.
  const dynM = (id, object, key) => {
    const fn = object[key];
    if (typeof fn !== 'function') return fn;
    record(id, fn);
    return isProxy(fn) ? (...args) => Reflect.apply(fn, object, args) : bind.call(fn, object);
  };
  const dynF = file => { marked.add(file); };
  const define = target => {
    for (const [name, value] of [['__dynC', dynC], ['__dynM', dynM], ['__dynF', dynF]]) {
      Object.defineProperty(target, name, { value, configurable: true, writable: true });
    }
  };
  define(globalThis);
  // Jest runs each test file in a context of its own: the recorders go there too.
  const createContext = vm.createContext;
  vm.createContext = function (...args) {
    const context = createContext.apply(this, args);
    define(vm.runInContext('globalThis', context));
    return context;
  };
  known.set(vm.createContext, locate(createContext));   // a call of it is a call of Node's
  if (process.env.DYN_BABEL) startsOf = hook(process.env.DYN_BABEL, unobserved, new Map());

  // A Jest worker that does not exit in time gets SIGTERM: the sites are written then too.
  let written = false;
  const flush = () => {
    for (const file of ran) if (!marked.has(file)) unobserved.add(file);
    if (written || !(sites.size || unobserved.size)) return;
    written = true;
    const out = [];
    for (const [id, seen] of sites) {
      const parts = id.split('|');
      out.push({ file: parts[0], line: Number(parts[1]), column: Number(parts[2]), name: parts.slice(3).join('|'),
        callees: [...seen].map(index => callees[index]) });
    }
    fs.writeFileSync(outFile.replace('%p', `${process.pid}-${threadId}`),
      JSON.stringify({ exact: true, node: process.versions.node, stats: { sites: out.length, callees: callees.length, lookups },
        unobserved: [...unobserved].sort(), sites: out }));
  };
  process.on('exit', flush);
  process.on('SIGTERM', () => { flush(); process.exit(143); });
  // A worker thread a pool terminates (Vitest's threads) runs no exit handler: it writes when the thread that
  // terminates it asks, over a channel that keeps no thread alive.
  const { Worker, BroadcastChannel, isMainThread } = require('worker_threads');
  if (!isMainThread) {
    const channel = new BroadcastChannel('daodan.dynamic');
    channel.unref();
    channel.onmessage = ({ data }) => {
      if (data === `flush ${threadId}`) { flush(); channel.postMessage(`flushed ${threadId}`); }
    };
  }
  const terminate = Worker.prototype.terminate;
  Worker.prototype.terminate = function (...args) {
    const id = this.threadId;
    if (id < 0) return terminate.apply(this, args);   // it has ended
    return new Promise(resolve => {
      const channel = new BroadcastChannel('daodan.dynamic');
      const done = () => { clearTimeout(timer); channel.close(); resolve(); };
      const timer = setTimeout(done, 3000);
      channel.onmessage = ({ data }) => { if (data === `flushed ${id}`) done(); };
      channel.postMessage(`flush ${id}`);
    }).then(() => terminate.apply(this, args));
  };
}

function plugin({ types: t }) {
  const helper = name => t.memberExpression(t.identifier('globalThis'), t.identifier(name));
  const rows = new WeakMap();   // Babel's file -> the lines of the code it reads
  const root = node => {
    while (node && (node.type === 'MemberExpression' || node.type === 'CallExpression')) node = node.object || node.callee;
    return node && node.type === 'Identifier' ? node.name : null;
  };
  // Where a name of the code Babel reads is in the file as written, [line, byte column]: the same place, or the
  // place the code's inline map leads to when the same name is written there; null elsewhere.
  const place = (state, loc, name) => {
    const origin = state.opts.origin;
    if (!origin) {
      if (!rows.has(state.file)) rows.set(state.file, state.file.code.split('\n'));
      return [loc.line - 1, bytes(rows.get(state.file), loc.line - 1, loc.column)];
    }
    const entry = origin.map.findEntry(loc.line - 1, loc.column);
    if (entry.originalLine === undefined || entry.generatedLine !== loc.line - 1 || !origin.same(entry.originalSource)) return null;
    const text = origin.lines[entry.originalLine] || '';
    const column = entry.originalColumn + (/['"]/.test(text[entry.originalColumn] || '') ? 1 : 0);
    if (!text.startsWith(name, column) || /[\w$]/.test(text[column + name.length] || '')) return null;
    return [entry.originalLine, bytes(origin.lines, entry.originalLine, column)];
  };
  return {
    name: 'daodan-dynamic-record',
    visitor: {
      Program: {
        exit(nodePath, state) {   // the file's recorded code ran: see `marked`
          const file = relative(state.filename);
          if (file) nodePath.unshiftContainer('body', t.expressionStatement(t.logicalExpression('&&', helper('__dynF'),
            t.callExpression(helper('__dynF'), [t.stringLiteral(file)]))));
        },
      },
      'CallExpression|NewExpression': {
        exit(nodePath, state) {
          const file = relative(state.filename);
          if (!file) return;
          const node = nodePath.node;
          // (0, o.m)(a): the unbound call printed code makes of an imported function
          const unbound = node.type === 'CallExpression' && node.callee.type === 'SequenceExpression'
            && node.callee.expressions.length === 2 && node.callee.expressions[0].type === 'NumericLiteral';
          const callee = unbound ? node.callee.expressions[1] : node.callee;
          const member = callee.type === 'MemberExpression';
          if (!member && callee.type !== 'Identifier') return;
          if (root(callee) === 'jest') return;
          const token = member ? callee.property : callee;
          let name;
          if (!member) name = callee.name === 'require' || callee.name === 'eval' ? null : callee.name;
          else if (callee.object.type === 'Super') name = null;
          else if (!callee.computed) name = token.type === 'Identifier' ? token.name : null;
          else name = token.type === 'StringLiteral' ? token.value : null;
          const at = name && token.loc && place(state, token.loc.start, name);
          if (!at) return;
          const id = t.stringLiteral(`${file}|${at[0]}|${at[1]}|${name}`);
          if (unbound) node.callee.expressions[1] = t.callExpression(helper('__dynC'), [id, callee]);
          else node.callee = member && node.type === 'CallExpression'
            ? t.callExpression(helper('__dynM'), [id, callee.object, callee.computed ? token : t.stringLiteral(name)])
            : t.callExpression(helper('__dynC'), [id, callee]);
        },
      },
    },
  };
}

if (process.env.DYN_OUT && ROOT && !globalThis.__dynC) install(process.env.DYN_OUT);

module.exports = plugin;
