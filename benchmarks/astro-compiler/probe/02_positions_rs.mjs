// `@astrojs/compiler-rs` (Astro 7): how many positions `parse` gives are right, against the text itself. The tree is ESTree with JSX nodes,
// each with `start` and `end` (offsets only: no line, no column). Every `.astro` file of the fixture is parsed with `\n` and with `\r\n`
// line ends. Ground truth: the text between `start` and `end` must begin and end as the node's own syntax does (`<name`..`>` for an opening
// element, `</name>` for a closing one, `{`..`}` for an expression container, the raw text for a JSXText or a literal, the name, or `{` and
// the name for a shorthand, for an attribute). The offset is tried as UTF-16 code units and as UTF-8 bytes; `unicode.astro` tells which.
// A parse that throws or reports an error is printed per file.
import fs from 'node:fs';
import { loadCompiler, sources } from './_lib.mjs';

const { name, compiler, version } = await loadCompiler();
if (name !== '@astrojs/compiler-rs') { console.log(`not applicable: the project's compiler is ${name} ${version}`); process.exit(0); }

const EXPECTED = {
  'src/pages/index.astro': [
    `onclick="save()"`, `onclick="this.disabled = true; confirmOrder(event)"`, `onclick='cancel("now")'`, `onclick=go()`, `onclick="multiLine()"`,
    `onsubmit="return validate(this)"`, `oninput="update(this.value)"`, "onclick={`pick('${item}')`}", `onclick="track('x')"`, `onclick="cardClick()"`,
    `{onclick}`, `onclick="widget()"`, `onclick="svgClick()"`,
  ],
  'src/pages/about.astro': [`onclick="goHome()"`], 'src/pages/blog/[slug].astro': [`onclick="share()"`], 'src/components/Card.astro': [`onclick="openCard(this)"`],
  'src/components/Counter.astro': [`onclick="increment()"`], 'src/pages/unicode.astro': [`onclick="afterText()"`, `onclick="afterUnicodeAttr()"`],
  'src/pages/tabs.astro': [`onclick="tabbed()"`, `onclick="deep()"`], 'src/pages/nofront.astro': [`onclick="noFrontmatter()"`],
  'src/pages/svg.astro': [`onclick="foreignClick()"`, `onend="smilEnd()"`, `onclick="pathClick()"`],
  'src/pages/calls.astro': [`onclick="cart.add(1)"`, `onclick="window.open('/x'); save()"`, `onclick="items[0]()"`, `onclick="factory()()"`, `onclick="(0, run)()"`, `onclick="new Thing()"`, `one="two()"`, `onfoo="bar()"`],
  'src/pages/edge.astro': [`onclick="afterScripts()"`, `onclick="afterString()"`, `onclick="afterMultiline()"`, `onclick="fromFrontmatter()"`, `onclick="fromProcessedScript()"`, `onclick="fromModuleScript()"`, `onclick="fromLayout()"`],
  'src/pages/broken.astro': [`onclick="beforeBreak()"`, `onclick="afterBreak()"`, `onclick="inBroken()"`],
};

const jsxName = (n) => (!n ? '' : n.type === 'JSXIdentifier' ? n.name : n.type === 'JSXNamespacedName' ? `${n.namespace.name}:${n.name.name}` : n.type === 'JSXMemberExpression' ? `${jsxName(n.object)}.${jsxName(n.property)}` : `<${n.type}>`);

function* nodes(value, parent = null) {
  if (Array.isArray(value)) { for (const v of value) yield* nodes(v, parent); return; }
  if (!value || typeof value !== 'object') return;
  if (typeof value.type === 'string') yield { node: value, parent };
  for (const [k, v] of Object.entries(value)) if (k !== 'type') yield* nodes(v, typeof value.type === 'string' ? value : parent);
}

// what the text between start and end should look like, by the type of node; null: not checked
function expectation(n, parent) {
  switch (n.type) {
    case 'JSXOpeningElement': return { prefix: ['<' + jsxName(n.name)], suffix: '>' };
    case 'JSXClosingElement': return { exact: `</${jsxName(n.name)}>` };
    case 'JSXElement': return { prefix: ['<' + jsxName(n.openingElement.name)], suffix: '>' };
    case 'JSXAttribute': return { prefix: [jsxName(n.name), '{' + jsxName(n.name)] };
    case 'JSXSpreadAttribute': return { prefix: ['{'], suffix: '}' };
    case 'JSXExpressionContainer': return { prefix: ['{'], suffix: '}' };
    case 'JSXText': return { exact: n.raw };
    case 'AstroFrontmatter': return n.start === n.end ? { empty: true } : { prefix: ['---'], suffix: '---' };
    case 'Literal': return parent?.type === 'JSXAttribute' ? { exact: n.raw } : null;
    default: return null;
  }
}

function lineColumn(text, offset) {
  let line = 1, col = 1;
  for (let i = 0; i < offset && i < text.length; i++) { if (text[i] === '\n') { line++; col = 1; } else col++; }
  return `${line}:${col}`;
}

const counts = new Map();
const bump = (group, key) => { const g = counts.get(group) ?? counts.set(group, {}).get(group); g[key] = (g[key] ?? 0) + 1; };
const odd = [];
const found = [];
const diagnostics = [];
const allOn = [];
for (const eol of ['\n', '\r\n']) {
  for (const file of sources()) {
    const text = fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n').replace(/\n/g, eol);
    const bytes = Buffer.from(text, 'utf8');
    const label = eol === '\n' ? 'LF  ' : 'CRLF';
    let result;
    try { result = compiler.parse(text); } catch (error) { diagnostics.push(`${label} ${file}: THREW ${String(error?.message ?? error).split('\n')[0].slice(0, 200)}`); continue; }
    diagnostics.push(`${label} ${file}: ${result.diagnostics.length} diagnostics${result.diagnostics.length ? ' ' + JSON.stringify(result.diagnostics.map((d) => ({ severity: d.severity, text: d.text, line: d.labels?.[0]?.line, column: d.labels?.[0]?.column }))).slice(0, 360) : ''}`);
    for (const { node: n, parent } of nodes(result.ast)) {
      const exp = expectation(n, parent);
      if (!exp) continue;
      const group = `${label} ${n.type}`;
      bump(group, 'n');
      if (exp.empty) { bump(group, 'empty (no frontmatter)'); continue; }
      if (typeof n.start !== 'number' || typeof n.end !== 'number') { bump(group, 'no start/end'); continue; }
      const check = (slice) => (exp.exact !== undefined ? slice === exp.exact : (exp.prefix === undefined || exp.prefix.some((p) => slice.startsWith(p))) && (exp.suffix === undefined || slice.endsWith(exp.suffix)));
      const asUnits = check(text.slice(n.start, n.end));
      const asBytes = check(bytes.subarray(n.start, n.end).toString('utf8'));
      bump(group, asUnits ? 'start..end right as UTF-16 units' : 'start..end NOT right as UTF-16 units');
      if (!asUnits && asBytes) bump(group, 'right only as BYTES');
      if (!asUnits && !asBytes) { bump(group, 'right in neither'); odd.push(`${group} ${jsxName(n.name ?? n.openingElement?.name)} ${n.start}..${n.end} in ${file}: ${JSON.stringify(text.slice(n.start, Math.min(n.end, n.start + 40)))}`); }
    }
    for (const needle of EXPECTED[file] ?? []) {
      const truth = text.indexOf(needle);
      if (truth < 0 || text.lastIndexOf(needle) !== truth) { console.log(`FIXTURE ERROR: ${file} ${needle}`); continue; }
      const attrName = needle.startsWith('{') ? needle.slice(1, -1) : needle.slice(0, needle.indexOf('='));
      const nameAt = truth + needle.indexOf(attrName);
      const matches = [...nodes(result.ast)].map((x) => x.node).filter((n) => n.type === 'JSXAttribute' && jsxName(n.name) === attrName && (n.start === truth || n.name.start === nameAt));
      found.push({ label, file, needle, nameAt, truth, attribute: matches[0] });
    }
    const onAttributes = [...nodes(result.ast)].map((x) => x.node).filter((n) => n.type === 'JSXAttribute' && jsxName(n.name).startsWith('on')).map((n) => `${jsxName(n.name)}@${n.start}`);
    allOn.push({ label, file, tree: onAttributes.length, listed: (EXPECTED[file] ?? []).length, onAttributes });
  }
}

console.log(`${name} ${version}`);
console.log('\n=== what parse says for each file (diagnostics, or a throw)');
for (const line of diagnostics) console.log(line);
console.log('\n=== per kind of node: is the text between start and end what the node should be');
for (const [group, g] of [...counts].sort()) console.log(`${group}: ` + Object.entries(g).map(([k, v]) => `${k}=${v}`).join('; '));
console.log(`\n=== nodes right in neither unit (${odd.length})`);
for (const line of odd.slice(0, 30)) console.log(line);
console.log('\n=== the events of the fixture, one by one: where the text writes the attribute and what the compiler says');
let ok = 0, present = 0;
for (const f of found) {
  const a = f.attribute;
  if (!a) { console.log(`MISSING ${f.label} ${f.file} ${f.needle}`); continue; }
  present++;
  const exact = a.name.start === f.nameAt;
  if (exact) ok++;
  console.log(`${exact ? 'exact ' : 'WRONG '} ${f.label} ${f.file} ${f.needle.slice(0, 44)}: attribute ${a.start}..${a.end}, name at ${a.name?.start}; text: attribute at ${f.truth} (${lineColumn(fs.readFileSync(f.file, 'utf8').replace(/\r\n/g, '\n').replace(/\n/g, f.label === 'LF  ' ? '\n' : '\r\n'), f.truth)}), name at ${f.nameAt}`);
}
console.log(`\nevents: ${found.length} listed (LF and CRLF) in the files that parse, found ${present}, name start exact ${ok}`);
console.log('\n=== attributes named on*: in the tree against listed in the fixture');
for (const a of allOn) console.log(`${a.tree === a.listed ? 'same ' : 'DIFF '} ${a.label} ${a.file}: tree ${a.tree}, listed ${a.listed}${a.tree === a.listed ? '' : ' -> ' + a.onAttributes.join(' | ')}`);
