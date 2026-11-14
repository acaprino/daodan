// Stylus's own parser (`stylus`) over Stylus sheets: one tree per sheet in the neutral form `css.py` reads (see
// css_sass.js), without evaluating anything. usage: node css_stylus.js IN.json OUT.json
// IN: {"engines": node_modules folder, "items": [{"key", "path" | "text"}]}. Stylus specifics: a variable has no sigil
// (`brand = #0af`, `$w = 1px`), so a word in a value is a reference only where a variable of that name exists
// (`optional`); a mixin is called as a function or as a property (`pad 4px`); `{x}` interpolates in selectors; `for`
// over a literal range or list gives its iterations.
"use strict";
const fs = require("fs");
const path = require("path");

const [inPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const cfg = JSON.parse(fs.readFileSync(inPath, "utf8"));
const stylus = require(path.join(cfg.engines, "stylus"));
const nodes = stylus.nodes;

function kind(n) { return n && n.constructor ? n.constructor.name : ""; }

function idents(n, line, out = [], seen = new Set()) {
  if (!n || typeof n !== "object" || seen.has(n)) return out;
  seen.add(n);
  const k = kind(n);
  if (k === "Ident" && !(n.val && kind(n.val) !== "Null")) out.push({ k: "var", name: n.name, line: n.lineno || line, optional: !n.name.startsWith("$") });
  if (k === "Call") out.push({ k: "fn", name: n.name, line: n.lineno || line });
  for (const key of ["nodes", "args", "left", "right", "expr", "val", "cond", "segments"]) {
    const v = n[key];
    if (Array.isArray(v)) v.forEach((x) => idents(x, line, out, seen));
    else if (v && typeof v === "object" && key !== "val") idents(v, line, out, seen);
  }
  return out;
}

function literal(n) {
  const k = kind(n);
  if (k === "Unit") return String(n.val) + (n.type || "");
  if (k === "String") return n.val;
  if (k === "Ident" && kind(n.val) === "Null") return n.name;
  if (k === "Expression" && n.nodes.length === 1) return literal(n.nodes[0]);
  return null;
}

function iterations(each) {
  let expr = each.expr;
  while (kind(expr) === "Expression" && expr.nodes.length === 1 && kind(expr.nodes[0]) !== "Unit") expr = expr.nodes[0];
  if (kind(expr) === "BinOp" && (expr.op === ".." || expr.op === "...")) {
    const a = Number(literal(expr.left)), b = Number(literal(expr.right));
    if (!Number.isInteger(a) || !Number.isInteger(b)) return null;
    const end = expr.op === "..." ? b - 1 : b, out = [];
    for (let i = a; i <= end && out.length <= 256; i++) out.push([String(i)]);
    return out;
  }
  const items = kind(expr) === "Expression" ? expr.nodes : [expr];
  const values = items.map(literal);
  return values.every((v) => v !== null) && !each.key ? values.map((v) => [v]) : null;
}

function selector(group) {
  const parts = [];
  group.nodes.forEach((sel, i) => {
    if (i) parts.push(", ");
    for (const seg of sel.segments) {
      if (kind(seg) === "Literal") parts.push(seg.val);
      else {
        const inner = kind(seg) === "Expression" && seg.nodes.length === 1 ? seg.nodes[0] : seg;
        parts.push(kind(inner) === "Ident" ? { v: inner.name } : { x: String(seg), refs: idents(seg, group.lineno) });
      }
    }
  });
  return parts;
}

function convert(n, lines, mixins) {
  const k = kind(n), line = n.lineno || 1;
  const block = (b) => (b ? b.nodes.map((c) => convert(c, lines, mixins)).filter(Boolean) : []);
  if (k === "Group") return { t: "rule", line, end: line, sel: selector(n), kids: block(n.block) };
  if (k === "Property") {
    const prop = n.segments.map((s) => (kind(s) === "Ident" ? s.name : kind(s) === "Literal" ? s.val : String(s))).join("");
    if (mixins.has(prop)) return { t: "include", line, end: line, name: prop, ns: null, refs: idents(n.expr, line), kids: [] };
    const text = (lines[line - 1] || "").trim();
    const value = text.startsWith(prop) ? text.slice(prop.length).replace(/^\s*:?\s*/, "").replace(/;\s*$/, "") : String(n.expr);
    return { t: "decl", line, end: line, prop, value, refs: idents(n.expr, line) };
  }
  if (k === "Ident" && n.val && kind(n.val) === "Function") {
    const fn = n.val, at = (fn.block && fn.block.lineno) || line;
    return { t: "def", line: at, end: at, kind: "mixin", name: n.name, params: fn.params.nodes.map((p) => p.name),
      refs: fn.params.nodes.flatMap((p) => idents(p.val, at)), kids: block(fn.block) };
  }
  if (k === "Ident" && n.val && kind(n.val) !== "Null")
    return { t: "var", line, end: line, name: n.name, literal: literal(n.val), refs: idents(n.val, line) };
  if (k === "Expression") {
    const call = n.nodes.length === 1 && kind(n.nodes[0]) === "Call" ? n.nodes[0] : null;
    if (call) return { t: "include", line, end: line, name: call.name, ns: null, refs: idents(call.args, line), kids: [] };
    return { t: "ref", line, end: line, refs: idents(n, line) };
  }
  if (k === "Each") return { t: "loop", line, end: line, vars: [n.val, n.key].filter(Boolean), values: iterations(n),
    refs: idents(n.expr, line), kids: block(n.block) };
  if (k === "If") return { t: "block", line, end: line, refs: idents(n.cond, line),
    kids: [...block(n.block), ...(n.elses || []).flatMap((e) => (kind(e) === "Block" ? block(e) : [convert(e, lines, mixins)]))] };
  if (k === "Media") return { t: "at", line, end: line, name: "media",
    params: ((lines[line - 1] || "").match(/@media\s+(.*?)\s*\{?\s*$/) || [, String(n.val)])[1], refs: [], kids: block(n.block) };
  if (k === "Supports") return { t: "at", line, end: line, name: "supports", params: String(n.condition), refs: [], kids: block(n.block) };
  if (k === "Keyframes") return { t: "at", line, end: line, name: "keyframes", params: n.segments.map(String).join(""), refs: [], kids: block(n.block) };
  if (k === "Atrule") return { t: "at", line, end: line, name: n.type, params: n.val ? String(n.val) : "", refs: [], kids: n.block ? block(n.block) : null };
  if (k === "Import") {
    const url = literal(n.path) || String(n.path).replace(/^\(|\)$/g, "").replace(/^['"]|['"]$/g, "");
    return { t: "import", line, end: line, kind: "import", url };
  }
  if (k === "Extend") return { t: "extend", line, end: line, sel: n.selectors.map(String).join(", ") };
  return null;
}

const out = {};
for (const item of cfg.items) {
  try {
    const text = item.text !== undefined ? item.text : fs.readFileSync(item.path, "utf8");
    const root = new stylus.Parser(text, { cache: false }).parse();
    const mixins = new Set(root.nodes.filter((n) => kind(n) === "Ident" && n.val && kind(n.val) === "Function").map((n) => n.name));
    for (const name of item.mixins || []) mixins.add(name);
    out[item.key] = { tree: root.nodes.map((n) => convert(n, text.split("\n"), mixins)).filter(Boolean) };
  } catch (error) {
    out[item.key] = { error: String((error && error.message) || error).split("\n")[0].slice(0, 200) };
  }
}
fs.writeFileSync(outPath, JSON.stringify({ version: require(path.join(cfg.engines, "stylus/package.json")).version,
  seconds: (Date.now() - begun) / 1000, sheets: out }));
