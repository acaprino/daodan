// Runs inside the container, offline. Reads the V8 CPU profiles of a test run and
// writes, for every call site of a project function seen on the stack, the callees
// observed under that function whose name matches the site.
//
//   node dynamic_map.js <project root> <profile dir> <out.json>
//   node dynamic_map.js --sites <project root> <files.json> <out.json>
//
// A profile records caller and callee functions, not the calling line: a site is
// matched to a callee by the name it calls. Sampling misses short calls. With
// --sites no profile is read: each call site of the listed files gets the number
// of sites with the same name in its function, where matching by name is ambiguous.
'use strict';
const fs = require('fs');
const path = require('path');

const sitesMode = process.argv[2] === '--sites';
const [root, profileDir, outFile] = process.argv.slice(sitesMode ? 3 : 2);
const ROOT = path.resolve(root) + '/';
const parser = require(path.join(ROOT, 'node_modules/@babel/parser'));

const FUNCTIONS = new Set(['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression',
  'ObjectMethod', 'ClassMethod', 'ClassPrivateMethod']);
const CALLS = new Set(['CallExpression', 'OptionalCallExpression', 'NewExpression']);

function relative(url) {
  if (!url) return null;
  const file = url.startsWith('file://') ? decodeURIComponent(url.slice(7)) : url;
  return file.startsWith(ROOT) && !file.includes('/node_modules/') ? file.slice(ROOT.length) : null;
}

function calleeKind(frame) {
  const url = frame.url || '';
  if (!url) return { kind: 'builtin' };
  if (url.startsWith('node:')) return { kind: 'runtime', module: url };
  const at = url.lastIndexOf('/node_modules/');
  if (at >= 0) {
    const parts = url.slice(at + 14).split('/');
    return { kind: 'package', module: parts[0].startsWith('@') ? parts.slice(0, 2).join('/') : parts[0] };
  }
  const file = relative(url);
  return file ? { kind: 'project', file } : { kind: 'other', module: url };
}

const lastSegment = name => (name || '').split('.').pop().replace(/^(get|set|async|bound) /, '');

// caller "file|line|name" -> Map(callee key -> callee)
const observed = new Map();
let samples = 0;
const profiles = sitesMode ? [] : fs.readdirSync(profileDir).filter(entry => entry.endsWith('.cpuprofile')).sort();
for (const name of profiles) {
  const profile = JSON.parse(fs.readFileSync(path.join(profileDir, name), 'utf8'));
  samples += (profile.samples || []).length;
  const nodes = new Map(profile.nodes.map(node => [node.id, node]));
  for (const node of profile.nodes) {
    const file = relative(node.callFrame.url);
    if (!file || !node.children) continue;
    const key = `${file}|${node.callFrame.lineNumber}|${node.callFrame.functionName}`;
    let callees = observed.get(key);
    if (!callees) observed.set(key, callees = new Map());
    for (const id of node.children) {
      const frame = nodes.get(id).callFrame;
      if (frame.functionName.startsWith('(')) continue;
      const kind = calleeKind(frame);
      const calleeKey = `${frame.url}|${frame.lineNumber}|${frame.functionName}`;
      if (!callees.has(calleeKey)) {
        callees.set(calleeKey, { ...kind, name: frame.functionName, line: frame.lineNumber });
      }
    }
  }
}

function nameOf(node) {
  if (!node) return null;
  if (node.type === 'Identifier' || node.type === 'PrivateName') return node.name || (node.id && node.id.name);
  if (node.type === 'StringLiteral') return node.value;
  return null;
}

// One file: its functions (header lines, name, own call sites) and the module body as function 0.
function readFile(file) {
  const source = fs.readFileSync(path.join(ROOT, file), 'utf8');
  const lines = source.split('\n');
  const ast = parser.parse(source, { sourceType: 'unambiguous', errorRecovery: true,
    allowReturnOutsideFunction: true, plugins: ['jsx'] });
  const functions = [{ module: true, name: null, from: 0, to: 0, sites: [] }];
  const bytes = (line, column) => Buffer.byteLength((lines[line] || '').slice(0, column), 'utf8');
  (function walk(node, current, hint) {
    if (!node || typeof node.type !== 'string') return;
    if (FUNCTIONS.has(node.type)) {
      const own = { module: false, name: nameOf(node.id) || nameOf(node.key) || hint || null,
        from: node.loc.start.line - 1, to: node.body.loc.start.line - 1, sites: [] };
      functions.push(own);
      current = own;
    }
    if (CALLS.has(node.type)) {
      const callee = node.callee;
      const member = callee.type === 'MemberExpression' || callee.type === 'OptionalMemberExpression';
      const token = member ? callee.property : callee;
      const name = member && callee.computed && token.type !== 'StringLiteral' ? null : nameOf(token);
      if (name) {
        current.sites.push({ name, line: token.loc.start.line - 1, column: bytes(token.loc.start.line - 1, token.loc.start.column),
          startLine: node.loc.start.line - 1, startColumn: bytes(node.loc.start.line - 1, node.loc.start.column) });
      }
    }
    for (const key of Object.keys(node)) {
      if (key === 'loc' || key === 'leadingComments' || key === 'trailingComments' || key === 'innerComments') continue;
      const value = node[key];
      let inferred = null;
      if (node.type === 'VariableDeclarator' && key === 'init') inferred = nameOf(node.id);
      else if (node.type === 'AssignmentExpression' && key === 'right') {
        inferred = node.left.type === 'MemberExpression' ? nameOf(node.left.property) : nameOf(node.left);
      } else if ((node.type === 'ObjectProperty' || node.type === 'ClassProperty') && key === 'value') inferred = nameOf(node.key);
      if (Array.isArray(value)) value.forEach(item => walk(item, current, null));
      else if (value && typeof value === 'object') walk(value, current, inferred);
    }
  })(ast.program, functions[0], null);
  return functions;
}

if (sitesMode) {
  const out = {};
  for (const file of JSON.parse(fs.readFileSync(profileDir, 'utf8'))) {
    let functions;
    try { functions = readFile(file); } catch (error) { continue; }
    for (const fn of functions) {
      const counts = {};
      for (const site of fn.sites) counts[site.name] = (counts[site.name] || 0) + 1;
      for (const site of fn.sites) {
        out[`${file}|${site.line + 1}|${site.column + Buffer.byteLength(site.name, 'utf8')}|${site.name}`] = counts[site.name];
      }
    }
  }
  fs.writeFileSync(outFile, JSON.stringify(out));
  console.log(JSON.stringify({ sites: Object.keys(out).length }));
  process.exit(0);
}

const files = new Map();
const sites = [];
const stats = { profile_samples: samples, callers_observed: observed.size, callers_matched: 0, callers_ambiguous: 0,
  callers_unmatched: 0, files_unreadable: 0 };
for (const [key, callees] of observed) {
  const [file, lineText, functionName] = key.split('|');
  const line = Number(lineText);
  if (!files.has(file)) {
    try { files.set(file, readFile(file)); } catch (error) { files.set(file, null); stats.files_unreadable += 1; }
  }
  const functions = files.get(file);
  if (!functions) continue;
  let candidates = functions.filter(fn => !fn.module && fn.from <= line && line <= fn.to);
  const named = candidates.filter(fn => fn.name && fn.name === lastSegment(functionName));
  if (named.length) candidates = named;
  if (!candidates.length && line === 0) candidates = [functions[0]];
  if (!candidates.length) { stats.callers_unmatched += 1; continue; }
  stats[candidates.length > 1 ? 'callers_ambiguous' : 'callers_matched'] += 1;
  for (const fn of candidates) {
    for (const site of fn.sites) {
      const hits = [...callees.values()].filter(callee => lastSegment(callee.name) === site.name);
      sites.push({ file, ...site, caller: fn.module ? null : fn.name, callees: hits });
    }
  }
}

// A site reached through several profile nodes keeps the union of its callees.
const merged = new Map();
for (const site of sites) {
  const key = `${site.file}|${site.line}|${site.column}|${site.name}`;
  const known = merged.get(key);
  if (!known) { merged.set(key, site); continue; }
  for (const callee of site.callees) {
    if (!known.callees.some(other => other.kind === callee.kind && other.name === callee.name
      && other.line === callee.line && (other.file || other.module) === (callee.file || callee.module))) {
      known.callees.push(callee);
    }
  }
}
stats.sites_in_observed_callers = merged.size;
stats.sites_with_callee = [...merged.values()].filter(site => site.callees.length).length;
fs.writeFileSync(outFile, JSON.stringify({ stats, sites: [...merged.values()] }));
console.log(JSON.stringify(stats));
