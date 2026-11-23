// `@astrojs/compiler-rs` (Astro 7): the shape of what `parse` gives. The result's keys, then an outline of three files of the fixture: each
// node by type, name and `start..end`, each attribute by its type, name, kind of value and range. How a component, an attribute such as
// `client:load`, a custom element, a comment, a doctype, a script, a spread and a shorthand attribute are written; and the diagnostics.
import fs from 'node:fs';
import { loadCompiler } from './_lib.mjs';

const { name, compiler, version } = await loadCompiler();
if (name !== '@astrojs/compiler-rs') { console.log(`not applicable: the project's compiler is ${name} ${version}`); process.exit(0); }

const jsxName = (n) => (!n ? '' : n.type === 'JSXIdentifier' ? n.name : n.type === 'JSXNamespacedName' ? `${n.namespace.name}:${n.name.name}` : n.type === 'JSXMemberExpression' ? `${jsxName(n.object)}.${jsxName(n.property)}` : `<${n.type}>`);
const range = (n) => `${n.start}..${n.end}`;
const text = (s, n) => JSON.stringify(s.slice(n.start, Math.min(n.end, n.start + 30)));
const attributeValue = (a) => (a.value === null || a.value === undefined ? 'no value' : a.value.type === 'Literal' ? `Literal ${JSON.stringify(a.value.raw)}` : `${a.value.type}${a.value.expression ? ` of ${a.value.expression.type}` : ''}`);

function outline(node, source, depth, out) {
  const pad = '  '.repeat(depth);
  if (Array.isArray(node)) { for (const n of node) outline(n, source, depth, out); return; }
  if (!node || typeof node !== 'object') return;
  switch (node.type) {
    case 'JSXElement': {
      const o = node.openingElement;
      out.push(`${pad}JSXElement <${jsxName(o.name)}> ${range(node)} selfClosing=${o.selfClosing} closing=${node.closingElement ? range(node.closingElement) : 'none'}`);
      for (const a of o.attributes) {
        out.push(a.type === 'JSXSpreadAttribute' ? `${pad}  @ JSXSpreadAttribute ${range(a)} ${text(source, a)}` : `${pad}  @ ${a.type} ${jsxName(a.name)} (${a.name.type}) ${range(a)} name at ${a.name.start} value: ${attributeValue(a)} ${a.value ? range(a.value) : ''}`);
      }
      outline(node.children, source, depth + 1, out);
      break;
    }
    case 'JSXText': out.push(`${pad}JSXText ${range(node)} ${JSON.stringify(node.raw.slice(0, 30))}`); break;
    case 'JSXExpressionContainer': out.push(`${pad}JSXExpressionContainer ${range(node)} ${text(source, node)} expression=${node.expression?.type}`); break;
    case 'JSXFragment': out.push(`${pad}JSXFragment ${range(node)}`); outline(node.children, source, depth + 1, out); break;
    default: {
      out.push(`${pad}${node.type} ${typeof node.start === 'number' ? range(node) : ''}${node.value !== undefined && typeof node.value !== 'object' ? ' value=' + JSON.stringify(String(node.value).slice(0, 40)) : ''}`);
    }
  }
}

console.log('node', process.version, name, version);
for (const file of ['src/pages/index.astro', 'src/pages/unicode.astro', 'src/pages/edge.astro']) {
  const source = fs.readFileSync(file, 'utf8');
  const result = compiler.parse(source);
  console.log(`\n=== ${file} (${source.length} chars): keys ${Object.keys(result).join(',')}; diagnostics ${result.diagnostics.length}; ast keys ${Object.keys(result.ast).join(',')}`);
  for (const d of result.diagnostics) console.log('  diagnostic', JSON.stringify(d).slice(0, 400));
  const out = [];
  console.log(`AstroRoot ${range(result.ast)}`);
  if (result.ast.frontmatter) out.push(`frontmatter ${result.ast.frontmatter.type} ${range(result.ast.frontmatter)}`);
  outline(result.ast.body, source, 0, out);
  console.log(out.join('\n'));
}
