// Vue's own compiler (`@vue/compiler-sfc`) over single-file components: the style blocks (lang, scoped, module) for
// the sheet readers, every class and id the template writes (`class`, `:class`, `v-bind:class`, `id`, with the
// template's CSS Module `$style.x`), the script's imports and bindings (for `v-bind()` in CSS), the components the
// template renders and its root elements (a parent's scoped rules reach a child's root). usage: node css_vue.js IN OUT
// IN: {"engines": node_modules folder, "items": [{"key", "path"}]}.
"use strict";
const fs = require("fs");
const path = require("path");
const expressions = require("./css_expressions.js");

const [inPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const cfg = JSON.parse(fs.readFileSync(inPath, "utf8"));
const sfc = require(path.join(cfg.engines, "@vue/compiler-sfc"));
const ELEMENT = 1, ATTRIBUTE = 6, DIRECTIVE = 7;

function component(text) {
  const { descriptor, errors } = sfc.parse(text, { filename: "component.vue" });
  if (errors.length && !descriptor.template && !descriptor.styles.length) throw errors[0];
  const out = { blocks: [], classes: [], members: [], styles: [], imports: [], bindings: [], components: [], roots: [] };
  const modules = new Map();
  for (const style of descriptor.styles) {
    const name = style.module === true ? "$style" : style.module || null;
    if (name) modules.set(name, name);
    out.blocks.push({ line: style.loc.start.line, lang: (style.lang || "css").toLowerCase(), scoped: Boolean(style.scoped),
      module: name, text: style.content });
  }
  for (const script of [descriptor.script, descriptor.scriptSetup]) {
    if (!script) continue;
    const base = script.loc.start.line - 1;
    for (const m of script.content.matchAll(/^\s*import\s+(?:([\w$]+)\s*,?\s*)?(?:\{([^}]*)\}\s*)?(?:from\s+)?['"]([^'"]+)['"]/gm)) {
      const line = base + script.content.slice(0, m.index + m[0].indexOf("import")).split("\n").length;
      const names = [m[1], ...(m[2] || "").split(",").map((x) => x.trim().split(/\s+as\s+/).pop())].filter(Boolean);
      out.imports.push({ line, spec: m[3], names });
    }
  }
  if (descriptor.scriptSetup || descriptor.script) {
    try {
      const compiled = sfc.compileScript(descriptor, { id: "daodan" });
      const block = descriptor.scriptSetup || descriptor.script;
      const base = block.loc.start.line - 1;
      for (const node of compiled.scriptSetupAst || compiled.scriptAst || []) {
        const line = base + node.loc.start.line;
        if (node.type === "VariableDeclaration")
          for (const d of node.declarations) if (d.id.type === "Identifier") out.bindings.push({ name: d.id.name, line: base + d.loc.start.line });
        if (node.type === "FunctionDeclaration" && node.id) out.bindings.push({ name: node.id.name, line });
        if (node.type === "ImportDeclaration") for (const s of node.specifiers) out.bindings.push({ name: s.local.name, line });
      }
    } catch (error) {
      out.bindingsError = String(error.message || error).slice(0, 200);
    }
  }
  if (!descriptor.template || !descriptor.template.ast) return out;
  const template = descriptor.template;

  function expression(exp, chain) {
    const parsed = expressions.parse(cfg.engines, exp.content, exp.loc.start.line);
    if (!parsed) return [[{ h: "expression", x: exp.content.slice(0, 120) }]];
    const wrapped = `(${exp.content}\n)`;
    const lineOf = (n) => parsed.base + n.loc.start.line;
    const hooks = { value: (n) => {
      if (n.type !== "MemberExpression" || n.object.type !== "Identifier" || !modules.has(n.object.name)) return null;
      const name = n.computed ? (n.property.type === "Literal" ? n.property.value : null) : n.property.name;
      if (name === null) return [[{ h: "dynamic-member", x: wrapped.slice(n.start, n.end) }]];
      out.members.push({ line: lineOf(n), scope: n.object.name, name });
      return [[]];
    } };
    return expressions.evaluator((n) => wrapped.slice(n.start, n.end), lineOf, hooks).ev(parsed.node);
  }

  function visit(node, depth) {
    if (node.type !== ELEMENT) { for (const c of node.children || []) visit(c, depth); return; }
    if (depth === 0) out.roots.push(node.loc.start.line);
    if (node.tagType === 1) out.components.push(node.tag);
    for (const p of node.props) {
      if (p.type === ATTRIBUTE && (p.name === "class" || p.name === "id") && p.value)
        out.classes.push({ kind: p.name, line: p.loc.start.line, chain: [], alts: [[{ s: p.value.content }]] });
      else if (p.type === ATTRIBUTE && p.name === "style" && p.value)
        out.styles.push({ line: p.loc.start.line, text: p.value.content });
      else if (p.type === DIRECTIVE && p.name === "bind" && p.arg && (p.arg.content === "class" || p.arg.content === "id") && p.exp)
        out.classes.push({ kind: p.arg.content, line: p.loc.start.line, chain: [":" + p.arg.content], alts: expression(p.exp) });
    }
    for (const c of node.children || []) visit(c, depth + 1);
  }
  for (const c of template.ast.children) visit(c, 0);
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
fs.writeFileSync(outPath, JSON.stringify({ version: require(path.join(cfg.engines, "@vue/compiler-sfc/package.json")).version,
  seconds: (Date.now() - begun) / 1000, components: out }));
