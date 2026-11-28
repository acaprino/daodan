// Daodan's script for `astro.py`, run in Daodan's container, in the folder of an Astro project whose packages are restored. The last
// argument is the path of the JSON list of what to read, `{prefix, jsx, files}`: the `.astro` files of the folder, the start of the
// attribute names that are candidates for an event, and the file `astro` ships that declares them (data: `entry-queries.json`, `astro`).
//
// It calls `parse` of the compiler the project's own `astro` depends on, found from the folder of `astro` (so the one the project
// installed, whether the package manager hoists it or not): `@astrojs/compiler` (Astro 5 and 6: Go and WebAssembly, an async `parse`
// with its own tree; Astro 4 declares it too and was not run) or `@astrojs/compiler-rs` (Astro 7: Rust, a sync `parse` with an ESTree of
// JSX nodes). For each file it prints, as JSON, the errors the compiler reports and each attribute whose name starts with the prefix on
// an element of the page (a component's attribute is a prop, not an event): the line from 1 and the column from 0 in UTF-16 code units,
// the name, whether its value is a string written in place (`quoted`) or not, that string, and the tag. It prints too the text of the
// declarations file (`jsx`, null when the package has none), which `astro.py` reads for the names Astro declares as events, and the
// versions it ran with, `node` included. Each position is checked against the text before it is printed: the name must be written at
// the offset the compiler gives, and the line and the column are worked out from that offset, never taken from the compiler's own fields;
// else the attribute is in `unread` with why (the Go compiler's README warns its positions are incomplete and in some cases incorrect;
// measured in `benchmarks/astro-compiler/`: the start of an attribute is exact, that of an expression is one character off).
// Exit 3: the project has no `astro` or its compiler. Exit 4: its `astro` depends on no compiler this script knows.
// Packages are found with `createRequire`, as `angular_templates.mjs` does: `findPackageJSON` of `node:module` is from Node 22.14, and
// Astro 5 runs on Node 20 (measured on Node 20.20.2 with the script before this change: it failed at its import).
// shortcut: an element is a tag that does not start with a capital letter, as JSX tells it from a component; the Go compiler says so
// itself (`component`), compiler-rs gives only JSX. A namespaced tag (`<svg:rect>`) or a member (`<a.b>`) is no element here. A file
// the Rust compiler reports an error for is given no events: its tree holds nodes made up to recover (measured: an element named `this`
// at 0..0). Only a diagnostic of error severity is an error (Go: 1, Rust: 'error'); the fixture has produced no other, so the filter is
// not covered by a recorded answer.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

function stop(message, code) {
  process.stderr.write(`daodan-astro: ${message}\n`);
  process.exit(code);
}
const first = (error) => String(error?.message ?? error).split('\n')[0].slice(0, 300);

const args = process.argv.slice(2);
const job = JSON.parse(args.length ? fs.readFileSync(args.at(-1), 'utf8') : stop('no list of files was given', 2));
if (typeof job.prefix !== 'string' || !job.prefix) stop('the list names no prefix of the attributes that are events', 2);
const folder = process.cwd();

const COMPILERS = ['@astrojs/compiler', '@astrojs/compiler-rs'];
let astroManifest, fromAstro, astro;
try {
  astroManifest = createRequire(`${folder}/`).resolve('astro/package.json');
  astro = JSON.parse(fs.readFileSync(astroManifest, 'utf8'));
  fromAstro = createRequire(astroManifest);
} catch (error) {
  stop(`astro is not installed for ${folder}: ${first(error)}`, 3);
}
const name = COMPILERS.find((candidate) => astro.dependencies?.[candidate]);
if (!name) stop(`astro ${astro.version} depends on none of ${COMPILERS.join(', ')}`, 4);
let compiler, version;
try {
  version = fromAstro(`${name}/package.json`).version;
  const loaded = await import(pathToFileURL(fromAstro.resolve(name)).href); // the CommonJS build of the Go compiler has `parse` on `default`
  compiler = typeof loaded.parse === 'function' ? loaded : loaded.default;
} catch (error) {
  stop(`${name} is not installed for ${folder}: ${first(error)}`, 3);
}
if (typeof compiler?.parse !== 'function') stop(`${name} ${version} exports no parse`, 4);

const jsxName = (n) => (n?.type === 'JSXIdentifier' ? n.name : n?.type === 'JSXNamespacedName' ? `${n.namespace.name}:${n.name.name}` : null);
const isComponent = (tag) => tag[0] !== tag[0].toLowerCase();

// The index of the line an offset is in, from the offsets the lines start at.
function lineOf(starts, offset) {
  let low = 0, high = starts.length - 1;
  while (low < high) { const mid = (low + high + 1) >> 1; if (starts[mid] <= offset) low = mid; else high = mid - 1; }
  return low;
}

// The Go compiler: nodes with `attributes` and `children`; an attribute's `offset` counts UTF-8 bytes.
function goEvents(text, ast, events, unread) {
  const bytes = Buffer.from(text, 'utf8');
  const starts = [0];
  bytes.forEach((byte, index) => { if (byte === 0x0a) starts.push(index + 1); });
  const visit = (node) => {
    if (node.type === 'element' || node.type === 'custom-element') {
      for (const attribute of node.attributes ?? []) {
        if (!attribute.name.startsWith(job.prefix)) continue;
        const offset = attribute.position?.start?.offset;
        if (typeof offset !== 'number' || bytes.subarray(offset, offset + Buffer.byteLength(attribute.name)).toString('utf8') !== attribute.name) {
          unread.push(`the position the compiler gives for ${attribute.name} on <${node.name}> is not where it is written`);
          continue;
        }
        const line = lineOf(starts, offset);
        events.push({ line: line + 1, col: bytes.subarray(starts[line], offset).toString('utf8').length, name: attribute.name, kind: attribute.kind,
                      value: attribute.kind === 'quoted' ? attribute.value : null, tag: node.name });
      }
    }
    for (const child of node.children ?? []) visit(child);
  };
  visit(ast);
}

// compiler-rs: an ESTree, JSX elements anywhere in it (an expression's too); an offset counts UTF-16 code units, and there is no line.
function rsEvents(text, ast, events, unread) {
  const starts = [0];
  for (let i = 0; i < text.length; i++) if (text[i] === '\n') starts.push(i + 1);
  const visit = (value) => {
    if (Array.isArray(value)) { for (const item of value) visit(item); return; }
    if (!value || typeof value !== 'object') return;
    const tag = value.type === 'JSXElement' && value.openingElement.name.type === 'JSXIdentifier' ? value.openingElement.name.name : null;
    if (tag !== null && !isComponent(tag)) {
      for (const attribute of value.openingElement.attributes) {
        const attributeName = attribute.type === 'JSXAttribute' ? jsxName(attribute.name) : null;
        if (!attributeName?.startsWith(job.prefix)) continue;
        const offset = attribute.name.start;
        if (!text.startsWith(attributeName, offset)) {
          unread.push(`the position the compiler gives for ${attributeName} on <${tag}> is not where it is written`);
          continue;
        }
        const line = lineOf(starts, offset);
        const literal = attribute.value?.type === 'Literal' && typeof attribute.value.value === 'string';
        events.push({ line: line + 1, col: offset - starts[line], name: attributeName, kind: literal ? 'quoted' : attribute.value ? 'expression' : 'empty',
                      value: literal ? attribute.value.value : null, tag });
      }
    }
    for (const [key, child] of Object.entries(value)) if (key !== 'type') visit(child);
  };
  visit(ast);
}

const isError = (d) => d.severity === 1 || d.severity === 'error';
const diagnosticText = (d) => {
  const label = d.labels?.[0] ?? d.location ?? {};
  return `${String(d.text ?? d).slice(0, 200)}${label.line ? ` (line ${label.line})` : ''}`;
};

const files = [];
for (const file of job.files) {
  try {
    const text = fs.readFileSync(file, 'utf8');
    const result = await compiler.parse(text, { position: true });
    const events = [], unread = [];
    const errors = (result.diagnostics ?? []).filter(isError);
    if (!(name === '@astrojs/compiler-rs' && errors.length)) (name === '@astrojs/compiler' ? goEvents : rsEvents)(text, result.ast, events, unread);
    files.push({ f: file, events, ...(errors.length ? { errors: errors.map(diagnosticText) } : {}), ...(unread.length ? { unread } : {}) });
  } catch (error) {
    files.push({ f: file, error: first(error) });
  }
}
let jsx = null;
if (typeof job.jsx === 'string') {
  try { jsx = fs.readFileSync(path.join(path.dirname(astroManifest), job.jsx), 'utf8'); } catch { /* the package has none: `astro.py` says so */ }
}
process.stdout.write(JSON.stringify({ compiler: name, version, astro: astro.version, node: process.version, jsx, files }));
