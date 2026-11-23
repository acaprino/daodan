// What `parse` does with a file that does not parse: the diagnostics, and whether the events before and after the fault are still given.
import { loadCompiler } from './_lib.mjs';

const { name, compiler, version } = await loadCompiler();
console.log(name, version);
const CASES = {
  'frontmatter not closed': '---\nconst a = 1;\n<button onclick="a()">x</button>\n',
  'tag not closed': '<div>\n<button onclick="a()">x</button>\n<span\n<button onclick="b()">y</button>\n',
  'quote not closed': '<button onclick="a()>x</button>\n<button onclick="b()">y</button>\n',
  'brace not closed': '<p>{items.map(i => <b onclick="a()">x</b>}</p>\n<button onclick="b()">y</button>\n',
  'empty file': '',
  'only text': 'hello\n',
};
// the attributes of either tree: `@astrojs/compiler` writes `attributes` on a node, `@astrojs/compiler-rs` JSX attributes
const attributes = (value, out = []) => {
  if (Array.isArray(value)) { for (const v of value) attributes(v, out); return out; }
  if (!value || typeof value !== 'object') return out;
  if (value.type === 'JSXAttribute') out.push(`${value.name?.name ?? value.name?.namespace?.name}@${value.start}`);
  if (Array.isArray(value.attributes)) for (const a of value.attributes) if (a?.type === 'attribute') out.push(`${a.name}@${a.position?.start?.offset}`);
  for (const [k, v] of Object.entries(value)) if (k !== 'type' && k !== 'position') attributes(v, out);
  return out;
};
for (const [label, text] of Object.entries(CASES)) {
  try {
    const result = await compiler.parse(text, { position: true });
    console.log(`${label}: ${result.diagnostics.length} diagnostics ${JSON.stringify(result.diagnostics).slice(0, 400)}; attributes: ${attributes(result.ast).join(', ')}`);
  } catch (error) {
    console.log(`${label}: THREW ${String(error?.message ?? error).split('\n')[0].slice(0, 200)}`);
  }
}
