// `@astrojs/compiler` (Astro 5, 6): how many positions `parse` gives are right, against the text itself. Every `.astro` file of the fixture is
// parsed twice, with `\n` and with `\r\n` line ends. Ground truth: where the text writes the node's own token (`<name` for a tag, `{` for an
// expression, the name for an attribute, the value for a text or a comment, `---` for the frontmatter), compared with the offset the compiler
// reports; the line and the column must be those of that offset. The compiler writes the offset in UTF-8 bytes (its `Point` type says so)
// and the column in UTF-16 code units (measured on `unicode.astro`): both readings of the offset are counted, and `delta` is how far the
// reported offset is from the token (0: exact; +1: the token starts one character after the reported offset).
import fs from 'node:fs';
import { loadCompiler, sources, walk, point } from './_lib.mjs';

const { name, compiler, version } = await loadCompiler();
if (name !== '@astrojs/compiler') { console.log(`not applicable: the project's compiler is ${name} ${version}`); process.exit(0); }

// the events the fixture lists: [attribute name, its exact source]; each is written once in its file
const EXPECTED = {
  'src/pages/index.astro': [
    ['onclick', `onclick="save()"`], ['onclick', `onclick="this.disabled = true; confirmOrder(event)"`], ['onclick', `onclick='cancel("now")'`],
    ['onclick', `onclick=go()`], ['onclick', `onclick="multiLine()"`], ['onsubmit', `onsubmit="return validate(this)"`],
    ['oninput', `oninput="update(this.value)"`], ['onclick', "onclick={`pick('${item}')`}"], ['onclick', `onclick="track('x')"`],
    ['onclick', `onclick="cardClick()"`], ['onclick', `{onclick}`], ['onclick', `onclick="widget()"`], ['onclick', `onclick="svgClick()"`],
  ],
  'src/pages/about.astro': [['onclick', `onclick="goHome()"`]],
  'src/pages/blog/[slug].astro': [['onclick', `onclick="share()"`]],
  'src/components/Card.astro': [['onclick', `onclick="openCard(this)"`]],
  'src/components/Counter.astro': [['onclick', `onclick="increment()"`]],
  'src/pages/unicode.astro': [['onclick', `onclick="afterText()"`], ['onclick', `onclick="afterUnicodeAttr()"`]],
  'src/pages/tabs.astro': [['onclick', `onclick="tabbed()"`], ['onclick', `onclick="deep()"`]],
  'src/pages/nofront.astro': [['onclick', `onclick="noFrontmatter()"`]],
  'src/pages/svg.astro': [['onclick', `onclick="foreignClick()"`], ['onend', `onend="smilEnd()"`], ['onclick', `onclick="pathClick()"`]],
  'src/pages/calls.astro': [['onclick', `onclick="cart.add(1)"`], ['onclick', `onclick="window.open('/x'); save()"`], ['onclick', `onclick="items[0]()"`], ['onclick', `onclick="factory()()"`], ['onclick', `onclick="(0, run)()"`], ['onclick', `onclick="new Thing()"`], ['one', `one="two()"`], ['onfoo', `onfoo="bar()"`]],
  'src/pages/edge.astro': [['onclick', `onclick="afterScripts()"`], ['onclick', `onclick="afterString()"`], ['onclick', `onclick="afterMultiline()"`], ['onclick', `onclick="fromFrontmatter()"`], ['onclick', `onclick="fromProcessedScript()"`], ['onclick', `onclick="fromModuleScript()"`], ['onclick', `onclick="fromLayout()"`]],
  'src/pages/broken.astro': [['onclick', `onclick="beforeBreak()"`], ['onclick', `onclick="afterBreak()"`], ['onclick', `onclick="inBroken()"`]],
};
const TAGS = new Set(['element', 'component', 'custom-element']);

// the token each node starts with, in the text
function token(node, isAttribute) {
  if (isAttribute) return node.name;
  if (TAGS.has(node.type)) return '<' + node.name;
  if (node.type === 'fragment') return node.name ? '<' + node.name : '<>';
  if (node.type === 'text') return node.value;
  return { expression: '{', comment: node.value, doctype: '<!', frontmatter: '---' }[node.type] ?? null;
}

// the line and the column of a byte offset, the column counting UTF-16 code units (what the compiler writes)
function lineColumnOfByte(bytes, offset) {
  let line = 1, lineStart = 0;
  for (let i = 0; i < offset && i < bytes.length; i++) if (bytes[i] === 0x0a) { line++; lineStart = i + 1; }
  return { line, column: bytes.subarray(lineStart, offset).toString('utf8').length + 1 };
}
const at = (bytes, text, offset, needle) => ({
  bytes: bytes.subarray(offset, offset + Buffer.byteLength(needle)).toString('utf8') === needle,
  units: text.startsWith(needle, offset),
});

const counts = new Map(); // group -> {key: n}
const bump = (group, key) => { const g = counts.get(group) ?? counts.set(group, {}).get(group); g[key] = (g[key] ?? 0) + 1; };
const odd = [];
const endClasses = new Map();
const events = [];
const allOn = [];
for (const eol of ['\n', '\r\n']) {
  for (const file of sources()) {
    const text = fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n').replace(/\n/g, eol);
    const bytes = Buffer.from(text, 'utf8');
    const label = eol === '\n' ? 'LF  ' : 'CRLF';
    const result = await compiler.parse(text, { position: true });
    const visit = (node, isAttribute) => {
      const kind = isAttribute ? `attribute:${node.kind}` : node.type;
      const group = `${label} ${kind}`;
      bump(group, 'n');
      if (!node.position?.start) { bump(group, 'no position'); return; }
      const { start, end } = node.position;
      const tok = token(node, isAttribute);
      let delta = null;
      if (tok !== null && tok !== '') for (const d of [0, 1, -1]) if (at(bytes, text, start.offset + d, tok).bytes) { delta = d; break; }
      bump(group, delta === 0 ? 'start exact' : delta === null ? 'start: token not near' : `start: token ${delta > 0 ? '+' : ''}${delta} from the offset`);
      const lc = lineColumnOfByte(bytes, start.offset);
      const agree = lc.line === start.line && lc.column === start.column;
      bump(group, agree ? 'line:column agree with the offset' : 'line:column DISAGREE with the offset');
      if (!agree) odd.push(`${group} ${node.name ?? ''} reported ${point(start)}, the offset is at ${lc.line}:${lc.column}`);
      if (tok && delta === 0 && !at(bytes, text, start.offset, tok).units) bump(group, 'offset right only as BYTES, wrong as UTF-16 units');
      bump(group, end ? 'has end' : 'no end');
      if (end && !isAttribute) {
        const slice = bytes.subarray(start.offset, end.offset).toString('utf8');
        let cls;
        if (TAGS.has(node.type) || node.type === 'fragment') {
          cls = slice.endsWith(`</${node.name}>`) ? 'to the end of the closing tag' : slice.endsWith('/') ? 'one before the > of a self-closing tag' : slice.endsWith('>') ? 'to a >' : 'elsewhere';
        } else if (node.type === 'expression') cls = slice.endsWith('}') ? 'to the }' : 'elsewhere';
        else if (node.type === 'text' || node.type === 'comment') cls = slice === node.value ? 'exactly its value' : 'elsewhere';
        else cls = node.type === 'frontmatter' ? (slice.endsWith('---') ? 'to the closing fence' : 'elsewhere') : 'n/a';
        const e = endClasses.get(group) ?? endClasses.set(group, {}).get(group);
        e[cls] = (e[cls] ?? 0) + 1;
      }
    };
    for (const { node } of walk(result.ast)) {
      visit(node, false);
      for (const a of node.attributes ?? []) visit(a, true);
    }
    for (const [attr, needle] of EXPECTED[file] ?? []) {
      const truth = text.indexOf(needle);
      if (truth < 0 || text.lastIndexOf(needle) !== truth) { console.log(`FIXTURE ERROR: ${file} ${needle}`); continue; }
      const nameAt = truth + needle.indexOf(attr); // where the name starts: after the `{` of a shorthand
      const trueByte = Buffer.byteLength(text.slice(0, nameAt));
      const trueLc = lineColumnOfByte(bytes, trueByte);
      const written = needle.startsWith('{') ? null : needle.slice(attr.length + 1).replace(/^["']|["']$/g, '').replace(/^\{`|`\}$/g, '');
      const candidates = [];
      for (const { node } of walk(result.ast)) {
        for (const a of node.attributes ?? []) {
          const v = a.value ?? '';
          if (a.name === attr && (written === null ? a.kind === 'shorthand' : v === written || v === '`' + written + '`')) candidates.push({ a, tag: node.name });
        }
      }
      const hit = candidates[0];
      events.push({ label, file, needle, trueByte, trueLc, got: hit?.a.position?.start, kind: hit?.a.kind, tag: hit?.tag });
    }
    // every attribute the tree holds whose name starts with `on`, against the events the fixture lists (a handler written in a string, a
    // comment or a script is no attribute)
    const onAttributes = [];
    for (const { node } of walk(result.ast)) for (const a of node.attributes ?? []) if (a.name.startsWith('on')) onAttributes.push(`${node.type}<${node.name}> ${a.name}=${JSON.stringify(a.value)}`);
    allOn.push({ label, file, tree: onAttributes.length, listed: (EXPECTED[file] ?? []).length, onAttributes });
  }
}

console.log(`${name} ${version}`);
console.log('\n=== per kind of node: the start of its position against the text');
for (const [group, g] of [...counts].sort()) console.log(`${group}: ` + Object.entries(g).map(([k, v]) => `${k}=${v}`).join('; '));
console.log('\n=== the end of the node, where the compiler gives one');
for (const [group, e] of [...endClasses].sort()) console.log(`${group}: ` + Object.entries(e).map(([k, v]) => `${k}=${v}`).join('; '));
console.log(`\n=== line:column that disagree with the offset (${odd.length})`);
for (const line of odd.slice(0, 30)) console.log(line);

console.log('\n=== the events of the fixture, one by one: the name of the attribute in the text and what the compiler says');
let found = 0, exact = 0;
for (const e of events) {
  if (!e.got) { console.log(`MISSING ${e.label} ${e.file} ${e.needle}`); continue; }
  found++;
  const same = e.got.offset === e.trueByte && e.got.line === e.trueLc.line && e.got.column === e.trueLc.column;
  if (same) exact++;
  console.log(`${same ? 'exact ' : 'WRONG '} ${e.label} ${e.file} ${e.needle.slice(0, 44)} <${e.tag}> ${e.kind}: compiler ${point(e.got)}, text ${e.trueLc.line}:${e.trueLc.column}@${e.trueByte}`);
}
console.log(`\nevents: ${events.length} listed (LF and CRLF), found ${found}, name start exact in offset (bytes), line and column (UTF-16 units) ${exact}`);
console.log('\n=== attributes named on*: in the tree against listed in the fixture (a difference is a handler the tree lacks or one it invents)');
for (const a of allOn) console.log(`${a.tree === a.listed ? 'same ' : 'DIFF '} ${a.label} ${a.file}: tree ${a.tree}, listed ${a.listed}${a.tree === a.listed ? '' : ' -> ' + a.onAttributes.join(' | ')}`);
