// `@astrojs/compiler` (Astro 5, 6): what `parse` gives for every `.astro` file of the fixture: the tree, each node with the position the
// compiler writes (`line:column@offset`, start..end), each attribute with its kind, name, value, raw text and position, the diagnostics.
import fs from 'node:fs';
import { loadCompiler, sources, walk, span, q } from './_lib.mjs';

const { name, compiler, version } = await loadCompiler();
if (name !== '@astrojs/compiler') { console.log(`not applicable: the project's compiler is ${name} ${version}`); process.exit(0); }
console.log(name, version);
for (const file of sources()) {
  const text = fs.readFileSync(file, 'utf8');
  const started = Date.now();
  const result = await compiler.parse(text, { position: true });
  console.log(`\n=== ${file} (${text.length} chars, ${Buffer.byteLength(text)} bytes) in ${Date.now() - started} ms; diagnostics: ${result.diagnostics.length}`);
  for (const d of result.diagnostics) console.log('  diagnostic', JSON.stringify(d));
  for (const { node, depth } of walk(result.ast)) {
    const pad = '  '.repeat(depth);
    const value = typeof node.value === 'string' ? ` value=${q(node.value.length > 50 ? node.value.slice(0, 50) + '...' : node.value)}` : '';
    console.log(`${pad}${node.type}${node.name !== undefined ? ` <${node.name}>` : ''}${value} ${span(node.position)}`);
    for (const a of node.attributes ?? []) {
      console.log(`${pad}  @ ${a.kind} ${q(a.name)} value=${q(a.value)}${a.raw !== undefined ? ` raw=${q(a.raw)}` : ''} ${span(a.position)}  keys=${Object.keys(a).join(',')}`);
    }
  }
}
