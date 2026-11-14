// The official Sass parser (`sass-parser`, the Sass team's PostCSS-compatible wrapper of Dart Sass's own parser) over
// SCSS and indented Sass: one tree per sheet in the neutral form `css.py` reads. usage: node css_sass.js IN.json OUT.json
// IN: {"engines": node_modules folder, "items": [{"key", "path" | "text", "syntax": "scss" | "sass"}]}.
// A node: {t, line, end, ...}. t: rule {sel: parts}, decl {prop, value, refs, kids}, var {name, ns, flags, refs},
// import {kind: use | forward | import, url, ns, prefix, show, hide, config}, def {kind: mixin | function, name,
// params}, include {name, ns, refs, using}, extend {sel}, loop {vars, values: literal iterations or null, refs},
// block {refs} (@if, @else, @while), at {name, params, refs, kids: null for a statement}, ref {refs} (@return...).
// A selector part is text, or {v: "$name", ns} for an interpolated variable, or {x: text, refs} for any other
// interpolated expression. refs: [{k: "var" | "fn", name, ns, line}].
"use strict";
const fs = require("fs");
const path = require("path");

const [inPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const cfg = JSON.parse(fs.readFileSync(inPath, "utf8"));
const sp = require(path.join(cfg.engines, "sass-parser"));
const SKIP = new Set(["parent", "_parent", "source", "raws", "proxyCache", "lastEach", "indexes", "_raws"]);

function refsOf(value, line, out = [], seen = new Set()) {
  if (value === null || typeof value !== "object" || seen.has(value)) return out;
  seen.add(value);
  if (value instanceof Map) { for (const [k, v] of value) { refsOf(k, line, out, seen); refsOf(v, line, out, seen); } return out; }
  if (value instanceof Set || Array.isArray(value)) { for (const v of value) refsOf(v, line, out, seen); return out; }
  const type = value.sassType;
  const at = value.source && value.source.start ? value.source.start.line : line;
  if (type === "variable") out.push({ k: "var", name: "$" + value.variableName, ns: value.namespace || null, line: at });
  else if (type === "function-call") out.push({ k: "fn", name: value.name, ns: value.namespace || null, line: at });
  for (const key of Object.keys(value)) {
    if (SKIP.has(key)) continue;
    let v;
    try { v = value[key]; } catch (e) { continue; }
    if (v && typeof v === "object") refsOf(v, at, out, seen);
  }
  return out;
}

// The literal text of a Sass value: a number, an unquoted or quoted string without interpolation; null otherwise.
function literal(e) {
  if (!e) return null;
  if (e.sassType === "number") return String(e.value) + (e.unit || "");
  if (e.sassType === "string") {
    const nodes = e.text.nodes;
    return nodes.every((n) => typeof n === "string") ? nodes.join("") : null;
  }
  return null;
}

// The iterations of an @each over a list or map written in the rule itself, or of an @for between literal integers:
// one tuple of values per iteration, a value null where it is not literal text; null when the collection is not
// written in the rule.
function iterations(node) {
  if (node.sassType === "for-rule") {
    const from = literal(node.fromExpression), to = literal(node.toExpression);
    if (from === null || to === null || !/^-?\d+$/.test(from) || !/^-?\d+$/.test(to)) return null;
    const a = Number(from);
    let b = Number(to);
    if (node.to === "to") b += a <= b ? -1 : 1;
    const out = [];
    for (let i = a; a <= b ? i <= b : i >= b; i += a <= b ? 1 : -1) { out.push([String(i)]); if (out.length > 256) return null; }
    return out;
  }
  const e = node.eachExpression;
  const vars = node.variables.length;
  if (e.sassType === "map") return e.nodes.map((entry) => (vars > 1 ? [literal(entry.key), literal(entry.value)] : [null]));
  if (e.sassType === "list" || e.sassType === "string" || e.sassType === "number")
    return (e.sassType === "list" ? e.nodes : [e]).map((item) => (vars > 1 ? new Array(vars).fill(null) : [literal(item)]));
  return null;
}

// A selector as text parts and its `#{...}` interpolations: a lone variable `{v, ns}`, anything else `{x, refs}`.
function selectorParts(selector, line) {
  const parts = [];
  let i = 0, last = 0;
  while ((i = selector.indexOf("#{", last)) >= 0) {
    let depth = 1, j = i + 2;
    for (; j < selector.length && depth; j++) depth += selector[j] === "{" ? 1 : selector[j] === "}" ? -1 : 0;
    if (i > last) parts.push(selector.slice(last, i));
    const inner = selector.slice(i + 2, j - 1).trim();
    const lone = /^(?:([\w-]+)\.)?\$([\w-]+)$/.exec(inner);
    if (lone) parts.push({ v: "$" + lone[2], ns: lone[1] || null });
    else parts.push({ x: inner, refs: [...inner.matchAll(/(?:([\w-]+)\.)?\$([\w-]+)/g)].map((m) => ({ k: "var", name: "$" + m[2], ns: m[1] || null, line })) });
    last = j;
  }
  if (last < selector.length) parts.push(selector.slice(last));
  return parts;
}

function names(set) { return set ? [...set] : null; }

function convert(node, text) {
  const line = node.source.start.line, end = node.source.end ? node.source.end.line : line;
  const base = { line, end };
  const kids = () => (node.nodes || []).map((c) => convert(c, text)).filter(Boolean);
  switch (node.sassType) {
    case "rule": return { t: "rule", ...base, sel: selectorParts(node.selector, line), kids: kids() };
    case "decl": {
      const raw = text.slice(node.source.start.offset, node.source.end.offset);
      const colon = raw.indexOf(":");
      let value = colon < 0 ? "" : raw.slice(colon + 1);
      if (node.nodes && node.nodes.length) value = value.slice(0, value.indexOf("{") < 0 ? value.length : value.indexOf("{"));
      const important = /!\s*important\s*$/i.test(value);
      value = value.replace(/\s*!\s*important\s*$/i, "").trim();
      return { t: "decl", ...base, prop: node.prop, value, important, refs: refsOf(node.expression, line),
        kids: kids() };
    }
    case "variable-declaration":
      return { t: "var", ...base, name: "$" + node.variableName, ns: node.namespace || null,
        flags: [...(node.guarded ? ["default"] : []), ...(node.global ? ["global"] : [])], refs: refsOf(node.expression, line) };
    case "use-rule":
      return { t: "import", ...base, kind: "use", url: node.useUrl, ns: node.namespace === undefined ? null : node.namespace,
        config: [...node.configuration.variables()].map((v) => "$" + v.name) };
    case "forward-rule":
      return { t: "import", ...base, kind: "forward", url: node.forwardUrl, prefix: node.prefix || "",
        show: node.show ? [...names(node.show.mixinsAndFunctions), ...names(node.show.variables).map((v) => "$" + v)] : null,
        hide: node.hide ? [...names(node.hide.mixinsAndFunctions), ...names(node.hide.variables).map((v) => "$" + v)] : null };
    case "import-rule":
      return { t: "block", ...base, refs: [], kids: node.imports.nodes.map((i) => (i.sassType === "dynamic-import"
        ? { t: "import", line, end, kind: "import", url: i.url }
        : { t: "at", line, end, name: "import", params: i.staticUrl.toString() + (i.modifiers ? " " + i.modifiers.toString() : ""), refs: [], kids: null })) };
    case "mixin-rule": case "function-rule":
      return { t: "def", ...base, kind: node.sassType === "mixin-rule" ? "mixin" : "function",
        name: node.sassType === "mixin-rule" ? node.mixinName : node.functionName,
        params: node.parameters.nodes.map((p) => "$" + p.name), refs: refsOf(node.parameters, line), kids: kids() };
    case "include-rule":
      return { t: "include", ...base, name: node.includeName, ns: node.namespace || null, refs: refsOf(node.arguments, line),
        using: node.using ? node.using.nodes.map((p) => "$" + p.name) : [], kids: kids() };
    case "each-rule": case "for-rule":
      return { t: "loop", ...base, vars: (node.sassType === "for-rule" ? [node.variable] : node.variables).map((v) => "$" + v),
        values: iterations(node), refs: refsOf(node.sassType === "for-rule" ? [node.fromExpression, node.toExpression] : node.eachExpression, line),
        kids: kids() };
    case "if-rule": case "else-rule": case "while-rule":
      return { t: "block", ...base, refs: refsOf(node.ifCondition || node.elseCondition || node.whileCondition, line), kids: kids() };
    case "return-rule": case "debug-rule": case "warn-rule": case "error-rule":
      return { t: "ref", ...base, refs: refsOf(node.returnExpression || node.debugExpression || node.warnExpression || node.errorExpression, line) };
    case "content-rule": return { t: "ref", ...base, refs: refsOf(node.contentArguments, line) };
    case "atrule": {
      if (node.name === "extend") return { t: "extend", ...base, sel: node.params };
      return { t: "at", ...base, name: node.name, params: node.params || "", refs: refsOf(node.paramsInterpolation, line),
        kids: node.nodes === undefined ? null : kids() };
    }
    case "comment": case "sass-comment": return null;
    default: return { t: "at", ...base, name: node.sassType, params: "", refs: [], kids: node.nodes ? kids() : null };
  }
}

// sass-parser 0.5.6 refuses a percentage keyframe selector (`0% { ... }`, "expected selector"), which Dart Sass
// reads. Inside each `@keyframes` block such a selector is written `to`, on the same line: the walker keeps no
// keyframe selector, only the declarations under it.
function keyframeSelectors(text) {
  let out = text;
  const head = /@(?:-[a-z]+-)?keyframes\b[^{;]*\{/gi;
  let match;
  while ((match = head.exec(out))) {
    let depth = 1, i = match.index + match[0].length;
    for (; i < out.length && depth; i++) depth += out[i] === "{" ? 1 : out[i] === "}" ? -1 : 0;
    const body = out.slice(match.index + match[0].length, i - 1)
      .replace(/(^\s*|[{};,]\s*)(\d+(?:\.\d+)?%)(?=\s*[,{])/g, (all, before, pct) => before + "to".padEnd(pct.length, " "));
    out = out.slice(0, match.index + match[0].length) + body + out.slice(i - 1);
    head.lastIndex = match.index + match[0].length + body.length;
  }
  return out;
}

const out = {};
for (const item of cfg.items) {
  try {
    const text = item.text !== undefined ? item.text : fs.readFileSync(item.path, "utf8");
    const root = (item.syntax === "sass" ? sp.sass : sp.scss).parse(keyframeSelectors(text));
    out[item.key] = { tree: root.nodes.map((n) => convert(n, text)).filter(Boolean) };
  } catch (error) {
    out[item.key] = { error: String((error && error.message) || error).split("\n")[0].slice(0, 200) };
  }
}
fs.writeFileSync(outPath, JSON.stringify({ version: require(path.join(cfg.engines, "sass-parser/package.json")).version,
  seconds: (Date.now() - begun) / 1000, sheets: out }));
