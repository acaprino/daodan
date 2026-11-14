// Less's own parser (`less`, the reference implementation) over Less sheets: one tree per sheet in the neutral form
// `css.py` reads (see css_sass.js), without evaluating anything. usage: node css_less.js IN.json OUT.json
// IN: {"engines": node_modules folder, "items": [{"key", "path" | "text"}]}. Less specifics in the tree:
// var {name, literal: its text when the value is a plain word, string or dimension, kids: a detached ruleset};
// include {path: [".a", ".b"] (a mixin call `.a > .b()` or `.a.b;`), symbol, refs}; def {name, params, refs (the guard)};
// rule {sel, refs (a CSS guard), extends: [{sel, all}]}; import {kind: import | plugin, url, options}; refs may be
// {k: "var", name: "@@x"} (a variable variable). Lines come from the parser's indexes; a mixin definition's start,
// which the parser does not keep, is taken where its parse begins.
"use strict";
const fs = require("fs");
const path = require("path");

const [inPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const cfg = JSON.parse(fs.readFileSync(inPath, "utf8"));
const less = require(path.join(cfg.engines, "less"));
const tree = less.tree;

function lineAt(starts, index) {
  let lo = 0, hi = starts.length - 1;
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (starts[mid] <= index) lo = mid; else hi = mid - 1; }
  return lo + 1;
}

// The text of a statement from its start to the `;`, `{` or `}` that ends it at depth 0.
function statementText(text, start, stops) {
  let depth = 0, quote = "", i = start;
  for (; i < text.length; i++) {
    const ch = text[i];
    if (quote) { if (ch === "\\") i++; else if (ch === quote) quote = ""; continue; }
    if (ch === '"' || ch === "'") quote = ch;
    else if (ch === "(" || ch === "[") depth++;
    else if (ch === ")" || ch === "]") depth--;
    else if (depth <= 0 && stops.includes(ch)) break;
  }
  return text.slice(start, i);
}

function refsOf(value, line, out = [], seen = new Set()) {
  if (!value || typeof value !== "object" || seen.has(value)) return out;
  seen.add(value);
  if (Array.isArray(value)) { for (const v of value) refsOf(v, line, out, seen); return out; }
  if (value instanceof tree.Variable) out.push({ k: "var", name: value.name, line });
  else if (value instanceof tree.VariableCall) out.push({ k: "var", name: value.variable, line });
  else if (value instanceof tree.Quoted) {
    for (const m of String(value.value).matchAll(/@\{([\w-]+)\}/g)) out.push({ k: "var", name: "@" + m[1], line });
  }
  for (const key of ["value", "args", "lvalue", "rvalue", "operands", "condition", "features", "selector", "arguments",
    "elements", "params", "lookups"]) {
    const v = value[key];
    if (v && typeof v === "object") refsOf(v, line, out, seen);
  }
  if (Array.isArray(value.args)) for (const a of value.args) if (a && a.value) refsOf(a.value, line, out, seen);
  return out;
}

function literal(value) {
  let v = value;
  while (v && (v instanceof tree.Value || v instanceof tree.Expression) && Array.isArray(v.value) && v.value.length === 1) v = v.value[0];
  if (v instanceof tree.Quoted || v instanceof tree.Keyword || v instanceof tree.Anonymous) return String(v.value);
  if (v instanceof tree.Dimension) return String(v.value) + (v.unit ? v.unit.toString() : "");
  return null;
}

function elementText(el) {
  const value = el.value;
  if (typeof value === "string") return value;
  if (value instanceof tree.Variable) return { v: value.name };
  try { return value.toCSS({}); } catch (e) { return ""; }
}

function selectorParts(selectors) {
  const parts = [];
  selectors.forEach((selector, index) => {
    if (index) parts.push(", ");
    selector.elements.forEach((el, at) => {
      const combinator = el.combinator ? el.combinator.value : "";
      if (combinator && combinator !== " ") parts.push(` ${combinator} `);
      else if (combinator === " " && at) parts.push(" ");
      const part = elementText(el);
      if (part && typeof part === "object" && parts.length && typeof parts[parts.length - 1] === "object") parts.push("");
      parts.push(part);
    });
  });
  return parts.reduce((acc, part) => {
    if (typeof part === "string" && typeof acc[acc.length - 1] === "string") acc[acc.length - 1] += part;
    else acc.push(part);
    return acc;
  }, []);
}

function convert(node, text, starts) {
  const at = (index) => lineAt(starts, index || 0);
  const kids = (rules) => (rules || []).map((c) => convert(c, text, starts)).filter(Boolean);
  if (node instanceof tree.mixin.Definition) {
    const line = at(node._start);
    return { t: "def", kind: "mixin", line, end: line, name: node.name,
      params: (node.params || []).filter((p) => p.name).map((p) => p.name),
      refs: [...refsOf(node.condition, line), ...(node.params || []).flatMap((p) => refsOf(p.value, line))],
      kids: kids(node.rules) };
  }
  if (node instanceof tree.Ruleset) {
    const selectors = node.selectors || [];
    const line = at(selectors.length ? selectors[0]._index : node._index);
    const extend = selectors.flatMap((s) => (s.extendList || []).map((e) => ({
      sel: e.selector.elements.map((el) => elementText(el)).filter((x) => typeof x === "string").join(""), all: e.option === "all" })));
    return { t: "rule", line, end: line, sel: selectorParts(selectors), refs: refsOf(selectors[0] && selectors[0].condition, line),
      extends: extend, kids: kids(node.rules) };
  }
  if (node instanceof tree.Declaration) {
    const line = at(node._index);
    const name = Array.isArray(node.name) ? node.name.map((n) => n.value || "").join("") : node.name;
    if (node.variable) {
      const detached = node.value instanceof tree.DetachedRuleset;
      return { t: "var", line, end: line, name, literal: detached ? null : literal(node.value), refs: detached ? [] : refsOf(node.value, line),
        kids: detached ? kids(node.value.ruleset.rules) : null };
    }
    const raw = statementText(text, node._index, ";}");
    const colon = raw.indexOf(":");
    const value = (colon < 0 ? "" : raw.slice(colon + 1)).replace(/\s*!\s*important\s*$/i, "").trim();
    return { t: "decl", line, end: line, prop: name, value, refs: refsOf(node.value, line) };
  }
  if (node instanceof tree.mixin.Call) {
    const line = at(node._index);
    const pathNames = node.selector.elements.map((el) => elementText(el)).filter((x) => typeof x === "string");
    const symbol = statementText(text, node._index, ";}").replace(/\s*\([\s\S]*$/, "").replace(/\s*!important\s*$/, "").trim();
    return { t: "include", line, end: line, path: pathNames, symbol, refs: (node.arguments || []).flatMap((a) => refsOf(a.value, line)) };
  }
  if (node instanceof tree.VariableCall) {
    const line = at(node._index);
    return { t: "ref", line, end: line, refs: [{ k: "var", name: node.variable, line }] };
  }
  if (node instanceof tree.Extend) {
    const line = at(node._index);
    return { t: "extend", line, end: line, sel: node.selector.elements.map((el) => elementText(el)).filter((x) => typeof x === "string").join(""),
      all: node.option === "all" };
  }
  if (node instanceof tree.Import) {
    const line = at(node._index);
    const url = node.path instanceof tree.URL ? node.path.value.value : node.path.value;
    const options = Object.keys(node.options || {}).filter((k) => node.options[k] === true && k !== "isPlugin");
    return { t: "import", line, end: line, kind: node.options && node.options.isPlugin ? "plugin" : "import", url: String(url), options };
  }
  if (node instanceof tree.Media || node instanceof tree.AtRule || (tree.Container && node instanceof tree.Container)) {
    const line = at(node._index);
    const head = statementText(text, node._index, "{;");
    const match = /^@([\w-]+)\s*([\s\S]*)$/.exec(head.trim());
    // A block nested in a rule holds one ruleset `&` (or, at the top, one without selectors): its body is the block's.
    const only = node.rules && node.rules.length === 1 && node.rules[0] instanceof tree.Ruleset ? node.rules[0] : null;
    const implicit = only && (!only.selectors || (only.selectors.length === 1 && only.selectors[0].elements.length === 1
      && only.selectors[0].elements[0].value === "&"));
    const rules = implicit ? only.rules : node.rules;
    return { t: "at", line, end: line, name: match ? match[1] : node.name, params: match ? match[2].trim() : "",
      refs: refsOf(node.features || node.value, line), kids: node.rules ? kids(rules) : null };
  }
  return null;
}

function parse(text, filename) {
  return new Promise((resolve, reject) => {
    const context = new less.contexts.Parse({ processImports: false, filename });
    const fileInfo = { filename, rootpath: "", currentDirectory: "", entryPath: "", rootFilename: filename };
    const imports = new less.ImportManager(less, context, fileInfo);
    const parser = new less.Parser(context, imports, fileInfo);
    const definition = parser.parsers.mixin.definition;
    parser.parsers.mixin.definition = function () {
      const start = parser.parserInput.i;
      const found = definition.apply(this, arguments);
      if (found) found._start = start;
      return found;
    };
    parser.parse(text, (error, root) => (error ? reject(error) : resolve(root)), {});
  });
}

(async () => {
  const out = {};
  for (const item of cfg.items) {
    try {
      const text = item.text !== undefined ? item.text : fs.readFileSync(item.path, "utf8");
      const starts = [0];
      for (let i = 0; i < text.length; i++) if (text[i] === "\n") starts.push(i + 1);
      const root = await parse(text, item.key);
      out[item.key] = { tree: root.rules.map((n) => convert(n, text, starts)).filter(Boolean) };
    } catch (error) {
      out[item.key] = { error: String((error && error.message) || error).split("\n")[0].slice(0, 200) };
    }
  }
  fs.writeFileSync(outPath, JSON.stringify({ version: require(path.join(cfg.engines, "less/package.json")).version,
    seconds: (Date.now() - begun) / 1000, sheets: out }));
})();
