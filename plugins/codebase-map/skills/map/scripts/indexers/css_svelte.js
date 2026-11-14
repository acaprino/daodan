// Svelte's own compiler (`svelte/compiler`, modern AST) over components: the style blocks for the sheet readers
// (scoped by default, `:global` and `<style global>` global), and every class and id the markup writes (`class`
// with its `{...}` parts, `class={...}` objects and arrays, `class:name`, `id`). The style bodies are blanked before
// the compiler reads the markup, so a block in another dialect cannot stop it; they are read by their own readers.
// usage: node css_svelte.js IN OUT; IN: {"engines": node_modules folder, "items": [{"key", "path"}]}.
"use strict";
const fs = require("fs");
const path = require("path");
const expressions = require("./css_expressions.js");

const [inPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const cfg = JSON.parse(fs.readFileSync(inPath, "utf8"));
const svelte = require(path.join(cfg.engines, "svelte/compiler"));
const STYLE = /<style\b([^>]*)>([\s\S]*?)<\/style\s*>/gi;

function component(text) {
  const out = { blocks: [], classes: [], styles: [], imports: [] };
  const starts = [0];
  for (let i = 0; i < text.length; i++) if (text[i] === "\n") starts.push(i + 1);
  const lineAt = (offset) => { let lo = 0, hi = starts.length - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (starts[m] <= offset) lo = m; else hi = m - 1; } return lo + 1; };
  const blanked = text.replace(STYLE, (whole, attrs, body, at) => {
    const lang = /\blang\s*=\s*['"]?([\w-]+)/i.exec(attrs);
    out.blocks.push({ line: lineAt(at), lang: lang ? lang[1].toLowerCase() : "css", scoped: !/\bglobal\b/.test(attrs), module: null,
      text: text.slice(at + whole.indexOf(">") + 1, at + whole.indexOf(">") + 1 + body.length) });
    return whole.slice(0, whole.indexOf(">") + 1) + body.replace(/[^\n]/g, " ") + whole.slice(whole.indexOf(">") + 1 + body.length);
  });
  const ast = svelte.parse(blanked, { modern: true });
  const lineOf = (n) => lineAt(n.start);
  const source = (n) => text.slice(n.start, n.end);
  const evaluate = expressions.evaluator(source, lineOf);
  for (const script of [ast.instance, ast.module]) {
    if (!script) continue;
    for (const node of script.content.body) {
      if (node.type === "ImportDeclaration")
        out.imports.push({ line: lineOf(node), spec: node.source.value, names: node.specifiers.map((s) => s.local.name) });
    }
  }
  function parts(value) {
    if (value === true) return [[]];
    const items = Array.isArray(value) ? value : [value];
    let acc = [[]];
    for (const item of items) {
      const alts = item.type === "Text" ? [[{ s: item.data, l: lineOf(item) }]]
        : evaluate.ev(item.expression).map((alt) => alt.map((p) => (p.h && !p.ctx && items.length > 1 ? { ...p, ctx: "template" } : p)));
      const next = [];
      for (const a of acc) for (const b of alts) next.push(a.concat(b));
      acc = next.length > 256 ? [[{ h: "too-many-values", x: "class" }]] : next;
    }
    return acc;
  }
  function visit(node) {
    if (!node || typeof node !== "object") return;
    if (Array.isArray(node)) { node.forEach(visit); return; }
    for (const a of node.attributes || []) {
      if (a.type === "Attribute" && (a.name === "class" || a.name === "id")) {
        const single = Array.isArray(a.value) && a.value.length === 1 && a.value[0].type === "ExpressionTag" ? a.value[0].expression : null;
        const alts = single && (single.type === "ObjectExpression" || single.type === "ArrayExpression")
          ? evaluate.classArg(single, 0) : parts(a.value);
        out.classes.push({ kind: a.name, line: lineOf(a), chain: [], alts });
      } else if (a.type === "Attribute" && a.name === "style" && Array.isArray(a.value) && a.value.every((v) => v.type === "Text")) {
        out.styles.push({ line: lineOf(a), text: a.value.map((v) => v.data).join("") });
      } else if (a.type === "ClassDirective") {
        out.classes.push({ kind: "class", line: lineOf(a), chain: ["class:"], alts: [[{ s: a.name }]] });
      }
    }
    for (const key of ["fragment", "nodes", "body", "consequent", "alternate", "pending", "then", "catch", "fallback"]) {
      if (node[key]) visit(node[key]);
    }
  }
  visit(ast.fragment);
  return out;
}

const out = {};
for (const item of cfg.items) {
  try {
    out[item.key] = component(fs.readFileSync(item.path, "utf8"));
  } catch (error) {
    out[item.key] = { error: String((error && error.message) || error).split("\n")[0].slice(0, 200) };
  }
}
fs.writeFileSync(outPath, JSON.stringify({ version: require(path.join(cfg.engines, "svelte/package.json")).version,
  seconds: (Date.now() - begun) / 1000, components: out }));
