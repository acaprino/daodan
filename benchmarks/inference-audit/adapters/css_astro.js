// Astro's own compiler (`@astrojs/compiler`) over `.astro` files: the style blocks for the sheet readers (scoped by
// default; `is:global` and `is:inline` global; `define:vars` keys declared as custom properties), and every class and
// id the markup writes (`class`, `class={...}`, `class:list={...}`, `id`). Attribute expressions are text in the
// compiler's tree and are read with acorn (`css_expressions.js`). usage: node css_astro.js IN OUT
// IN: {"engines": node_modules folder, "items": [{"key", "path"}]}.
"use strict";
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const expressions = require("./css_expressions.js");

const [inPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const cfg = JSON.parse(fs.readFileSync(inPath, "utf8"));

async function component(astro, text) {
  const out = { blocks: [], classes: [], styles: [], imports: [] };
  const { ast } = await astro.parse(text, { position: true });
  for (const m of text.split(/^---\s*$/m)[1] ? text.split(/^---\s*$/m)[1].matchAll(/^\s*import\s+(?:([\w$]+)\s*,?\s*)?(?:\{([^}]*)\}\s*)?(?:from\s+)?['"]([^'"]+)['"]/gm) : []) {
    const line = text.slice(0, text.indexOf(m[0])).split("\n").length + (m[0].match(/^\s*/)[0].split("\n").length - 1);
    out.imports.push({ line, spec: m[3], names: [m[1], ...(m[2] || "").split(",").map((x) => x.trim())].filter(Boolean) });
  }
  function value(a, line) {
    if (a.kind === "quoted" || a.kind === "empty") return [[{ s: a.value, l: line }]];
    const source = a.kind === "template-literal" ? "`" + a.value + "`" : a.value;
    const parsed = expressions.parse(cfg.engines, source, line);
    if (!parsed) return [[{ h: "expression", x: source.slice(0, 120) }]];
    const wrapped = `(${source}\n)`;
    const evaluate = expressions.evaluator((n) => wrapped.slice(n.start, n.end), (n) => parsed.base + n.loc.start.line);
    return a.name === "class:list" ? evaluate.classArg(parsed.node, 0) : evaluate.ev(parsed.node);
  }
  function visit(node) {
    const line = node.position ? node.position.start.line : 1;
    if (node.type === "element" && node.name === "style") {
      const attrs = Object.fromEntries((node.attributes || []).map((a) => [a.name, a]));
      const lang = attrs.lang ? String(attrs.lang.value).toLowerCase() : "css";
      const vars = [];
      if (attrs["define:vars"]) {
        const parsed = expressions.parse(cfg.engines, attrs["define:vars"].value, line);
        if (parsed && parsed.node.type === "ObjectExpression")
          for (const p of parsed.node.properties) if (p.key && !p.computed) vars.push(p.key.name || p.key.value);
      }
      out.blocks.push({ line, lang, scoped: !attrs["is:global"] && !attrs["is:inline"], module: null, vars,
        text: (node.children || []).map((c) => c.value || "").join("") });
      return;
    }
    for (const a of node.attributes || []) {
      if (a.name === "class" || a.name === "id" || a.name === "class:list") {
        out.classes.push({ kind: a.name === "id" ? "id" : "class", line: a.position ? a.position.start.line : line,
          chain: a.name === "class:list" ? ["class:list"] : [], alts: a.kind === "shorthand" || a.kind === "spread"
            ? [[{ h: a.kind, x: a.name }]] : value(a, a.position ? a.position.start.line : line) });
      } else if (a.name === "style" && a.kind === "quoted") {
        out.styles.push({ line, text: a.value });
      }
    }
    for (const c of node.children || []) visit(c);
  }
  visit(ast);
  return out;
}

(async () => {
  const astro = await import(pathToFileURL(path.join(cfg.engines, "@astrojs/compiler/dist/node/index.js")).href);
  const out = {};
  for (const item of cfg.items) {
    try {
      out[item.key] = await component(astro, fs.readFileSync(item.path, "utf8"));
    } catch (error) {
      out[item.key] = { error: String((error && error.message) || error).split("\n")[0].slice(0, 200) };
    }
  }
  fs.writeFileSync(outPath, JSON.stringify({ version: require(path.join(cfg.engines, "@astrojs/compiler/package.json")).version,
    seconds: (Date.now() - begun) / 1000, components: out }));
})();
