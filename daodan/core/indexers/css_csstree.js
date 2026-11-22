// The ESLint fork of CSSTree (`@eslint/css-tree`) over plain CSS: a sheet, a `<style>` text or a style attribute, as the
// neutral tree `css.py` reads. usage: node css_csstree.js IN.json OUT.json
// IN: {"engines": the folder of the engines' package.json, "items": [{"key", "path" | "text", "kind": "declarations" for a
//      style attribute, "words": a CSS Module (every word of a value may be one of its `@value` names), "svelte": a
//      Svelte block}]}.
// OUT: {version, seconds, sheets: {key: {tree} | {error}}}; a text that throws (the parser, the stack, bytes that are no
// UTF-8, blocks nested deeper than MAX_DEPTH) is an error, never a partial tree, and costs the other sheets nothing.
// Lines are the snapshot's: CRLF and CR are LF, a form feed is no line end.
// A node {t, line, end, ...}; every text is the source's slice, its comments blanked and its whitespace collapsed:
//   rule {sel: [prelude], names: [[class | id, name, local | global | deep]], custom: [":--x"], lost: [text], kids}
//   decl {prop, value, important, raw, facts: {vars: [{name, fallback, dl}], kf, ff, ct, fam, composes: {names, from},
//         words, unmatched}} (kf, ff, ct: the lexer's answers on animation, font and container; unmatched: it matched no
//         syntax and the value holds a word that could be a name; raw: the parser kept the value as Raw)
//   at {name, params: the Atrule's own slice after its name, text: the at-rule as the source spells it up to its block
//         or its `;`, facts, kids: null for a statement}; facts.unreadable: its prelude is no tree and no exact text of
//         ours reads it
//   hole {kind: rule | statement, name, kids}: what the parser keeps as Raw, once the same parser has read it again where
//         it can (`reread`); kids: the block of a rule at the top level whose prelude is Raw.
// Nothing here reads a text with a pattern: names, urls, layers and values come from the tree and the lexer, the
// prelude of the few at-rules the grammar does not know (`@apply`, `@custom-media`, `@value`...) from the tokenizer.
"use strict";
const fs = require("fs");
const path = require("path");

const [inPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const cfg = JSON.parse(fs.readFileSync(inPath, "utf8"));
const need = require("module").createRequire(path.join(cfg.engines, "package.json"));  // the pinned engines
const cs = need("@eslint/css-tree");
const version = JSON.parse(fs.readFileSync(path.join(cfg.engines, "node_modules", "@eslint", "css-tree", "package.json"), "utf8")).version;
const T = cs.tokenTypes;
const strict = new TextDecoder("utf-8", { fatal: true });

const kids = (n) => (n && n.children ? n.children.toArray() : []);
const KEYFRAMES = new Set(["animation", "animation-name", "-webkit-animation", "-webkit-animation-name"]);
const FAMILIES = new Set(["font", "font-family"]);
const CONTAINER = new Set(["container-name", "container"]);
const MODES = { global: "global", local: "local", deep: "deep", "v-deep": "deep", slotted: "global" };
const COMPOUND = new Set(["ClassSelector", "IdSelector", "AttributeSelector", "PseudoClassSelector", "PseudoElementSelector", "TypeSelector"]);
const decode = (name) => cs.ident.decode(name);
const MAX_DEPTH = 100;  // nested blocks: the tree is read back by JSON and walked by recursion, in Python

// ------------------------------------------------------------------------------------------------ texts
function collapse(text) {  // whitespace runs become one space, the ends are trimmed
  let out = "", gap = false;
  cs.tokenize(text, (type, start, end) => {
    if (type === T.WhiteSpace) { gap = out.length > 0; return; }
    if (gap) out += " ";
    gap = false;
    out += text.slice(start, end);
  });
  return out;
}
function clean(ctx, from, to) {  // the text between two offsets, its comments blanked
  const list = ctx.comments;
  let lo = 0, hi = list.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (list[mid][1] <= from) lo = mid + 1; else hi = mid; }
  let out = "", at = from;
  for (let i = lo; i < list.length && list[i][0] < to; i++) {
    if (list[i][0] > at) out += ctx.text.slice(at, list[i][0]);
    out += " ";
    at = Math.max(at, list[i][1]);
  }
  if (at < to) out += ctx.text.slice(at, to);
  return collapse(out);
}
const cleanLoc = (ctx, loc) => clean(ctx, loc.start.offset, loc.end.offset);
const hole = (kind, n, text) => ({ t: "hole", line: n.loc.start.line, end: n.loc.end.line, kind, name: text.slice(0, 80) });
function lex(text) {  // the tokens of a prelude without its spaces, a string decoded
  const out = [];
  cs.tokenize(text, (type, start, end) => {
    if (type === T.WhiteSpace || type === T.Comment) return;
    const raw = text.slice(start, end);
    out.push({ type, text: type === T.String ? cs.string.decode(raw) : raw });
  });
  return out;
}
function words(text) {  // whitespace-separated runs outside brackets
  const out = [];
  let depth = 0, from = -1, to = 0;
  cs.tokenize(text, (type, start, end) => {
    if (type === T.Function || type === T.LeftParenthesis || type === T.LeftSquareBracket || type === T.LeftCurlyBracket) depth++;
    else if (type === T.RightParenthesis || type === T.RightSquareBracket || type === T.RightCurlyBracket) depth = Math.max(0, depth - 1);
    if (type === T.WhiteSpace && depth === 0) { if (from >= 0) out.push(text.slice(from, to)); from = -1; return; }
    if (from < 0) from = start;
    to = end;
  });
  if (from >= 0) out.push(text.slice(from, to));
  return out;
}

// ------------------------------------------------------------------------------------------------ selectors
// `S`: what a selector yields: names, custom selectors, and the arguments no selector reads (`lost`, declared as holes).
function selectorNames(list, S, mode, svelte) {
  for (const sel of list.type === "SelectorList" ? kids(list) : [list]) walkSelector(kids(sel), mode, S, svelte);
}
function descend(node, mode, S, svelte) {
  if (node.type === "Raw") {  // an argument the grammar does not know (`:global(.a)`, `:deep(.b)`): a selector list again
    let list;
    try { list = cs.parse(node.value, { context: "selectorList" }); } catch (e) { S.lost.push(node.value.slice(0, 80)); return; }
    selectorNames(list, S, mode, svelte);
  } else if (node.type === "SelectorList" || node.type === "Selector") selectorNames(node, S, mode, svelte);
  else if (node.type === "Nth" && node.selector) selectorNames(node.selector, S, mode, svelte);
}
const newNames = () => ({ names: [], custom: [], lost: [] });
function walkSelector(nodes, mode, S, svelte) {
  let m = mode;
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    if (n.type === "ClassSelector") S.names.push(["class", decode(n.name), m]);
    else if (n.type === "IdSelector") S.names.push(["id", decode(n.name), m]);
    else if (n.type === "Combinator") { if (n.name === "/deep/") m = "deep"; }
    else if (n.type === "PseudoClassSelector" || n.type === "PseudoElementSelector") {
      const name = n.name.toLowerCase();
      if (n.type === "PseudoClassSelector" && name.startsWith("--")) S.custom.push(":" + n.name);
      const args = n.children ? kids(n) : null;
      if (MODES[name] === undefined) { for (const a of args || []) descend(a, m, S, svelte); continue; }
      if (!args) { m = MODES[name]; continue; }
      for (const a of args) descend(a, MODES[name], S, svelte);
      if (svelte && name === "global") {  // a compound selector led by `:global(...)` is global as a whole
        let j = i + 1;
        for (; j < nodes.length && COMPOUND.has(nodes[j].type); j++) {
          if (nodes[j].type === "ClassSelector") S.names.push(["class", decode(nodes[j].name), "global"]);
          else if (nodes[j].type === "IdSelector") S.names.push(["id", decode(nodes[j].name), "global"]);
        }
        i = j - 1;
      }
    }
  }
}
function uniq(list) {
  const seen = new Set(), out = [];
  for (const item of list) { const key = item.join("\u0000"); if (!seen.has(key)) { seen.add(key); out.push(item); } }
  return out;
}

// ------------------------------------------------------------------------------------------------ values
const fragText = (nodes) => {
  const items = nodes.toArray ? nodes.toArray() : [...nodes];
  return items.length === 1 && items[0].type === "String" ? items[0].value : items.map((x) => (x.type === "Identifier" ? decode(x.name) : cs.generate(x))).join(" ");
};
// An identifier or a string the lexer could take for a name, outside the `--x` a var() names: where a value the lexer
// cannot match (it has a var()) hides nothing, no hole is declared.
// A var() fallback is a Value of its own (a Raw one, when the parser could not read it: read again as a value).
function hidesName(nodes, skip = 0) {
  return kids(nodes).some((x, i) => {
    if (i < skip) return false;
    if (x.type === "Identifier" || x.type === "String") return true;
    if (x.type === "Function") return hidesName(x, x.name.toLowerCase() === "var" ? 1 : 0);
    if (x.type === "Value") return hidesName(x);
    if (x.type !== "Raw") return false;
    try { return hidesName(cs.parse(x.value, { context: "value" })); } catch (e) { return true; }
  });
}
const fragments = (n, name) => cs.lexer.findDeclarationValueFragments(n, "Type", name).map((f) => fragText(f.nodes));
function declFacts(ctx, n, prop) {
  const v = n.value, facts = {}, vars = [];
  cs.walk(v, { visit: "Function", enter(f) {
    if (f.name.toLowerCase() !== "var") return;
    const a = kids(f);
    if (!a[0] || a[0].type !== "Identifier" || !a[0].name.startsWith("--")) return;
    const comma = a.findIndex((x) => x.type === "Operator" && x.value === ",");
    const fallback = comma >= 0 && a[comma + 1] ? clean(ctx, a[comma + 1].loc.start.offset, a[a.length - 1].loc.end.offset) : "";
    vars.push({ name: a[0].name, fallback: fallback || null, dl: f.loc.start.line - n.loc.start.line });
  } });
  if (vars.length) facts.vars = vars;
  const P = prop.toLowerCase();
  const group = KEYFRAMES.has(P) ? ["kf", "keyframes-name"] : FAMILIES.has(P) ? ["ff", "family-name"] : CONTAINER.has(P) ? ["ct", "custom-ident"] : null;
  if (group) {
    const matched = cs.lexer.matchProperty(P, v);
    if (matched.error) { if (hidesName(v)) facts.unmatched = String(matched.error.message).split("\n")[0].slice(0, 120); }
    else facts[group[0]] = fragments(n, group[1]);
  }
  const first = kids(v);
  if (P === "font-family") facts.fam = first.length === 1 && first[0].type === "String" ? first[0].value : first.filter((x) => x.type === "Identifier").map((x) => decode(x.name)).join(" ");
  if (P === "composes") {  // `composes: a b from "./x.css"` / `from global`: CSS Modules, no grammar of its own
    const names = [];
    let from = null, after = false;
    for (const x of first) {
      if (x.type === "Identifier" && x.name === "from" && !after) after = true;
      else if (!after && x.type === "Identifier") names.push(x.name);
      else if (after && x.type === "String") from = x.value;
      else if (after && x.type === "Identifier") from = x.name;
    }
    facts.composes = { names, from };
  } else if (ctx.words) {
    const found = new Set();
    cs.walk(v, { visit: "Identifier", enter(x) { if (!x.name.startsWith("--")) found.add(x.name); } });
    if (found.size) facts.words = [...found];
  }
  return facts;
}

// ------------------------------------------------------------------------------------------------ at-rules
const unreadable = { unreadable: true };
// The prelude's nodes; a Raw prelude (the grammar does not know the at-rule) is no tree.
const preludeOf = (n) => (n.prelude && n.prelude.type !== "Raw" ? kids(n.prelude) : n.prelude ? null : []);
function atFacts(n, name, params, children) {
  const list = preludeOf(n);
  if (name.endsWith("keyframes")) {
    if (!list) return unreadable;
    const x = list[0];
    return { name: x ? (x.type === "String" ? x.value : decode(x.name)) : "" };
  }
  switch (name) {
    case "import": {
      if (!list) return unreadable;
      let layer;
      for (const x of list) {
        if (x.type === "Identifier" && x.name.toLowerCase() === "layer") layer = "";
        else if (x.type === "Function" && x.name.toLowerCase() === "layer") layer = kids(x).map((l) => l.name).join("");
      }
      return { urls: list.filter((x) => x.type === "String" || x.type === "Url").map((x) => x.value), layer };
    }
    case "layer": return list ? { names: list.flatMap((l) => kids(l).map((x) => x.name)) } : unreadable;
    case "container": return list ? { names: list.filter((x) => x.type === "Identifier").map((x) => decode(x.name)) } : unreadable;
    case "media": {
      if (!list) return unreadable;
      const found = [];
      if (n.prelude) cs.walk(n.prelude, { visit: "Feature", enter(f) { if (f.name.startsWith("--") && !f.value) found.push(f.name); } });
      return found.length ? { custom: found } : {};
    }
    case "scope": {
      if (!list) return unreadable;
      const S = newNames();
      for (const s of list) for (const part of [s.root, s.limit]) if (part) selectorNames(part, S, "local", false);
      return { names: uniq(S.names), ...(S.lost.length ? { lost: S.lost } : {}) };
    }
    case "font-face": {
      const face = children.find((k) => k.t === "decl" && k.prop.toLowerCase() === "font-family");
      return { family: face && face.facts && face.facts.fam !== undefined ? face.facts.fam : "" };
    }
    case "custom-media": case "custom-selector": case "custom-variant": case "variant": case "utility":
      return { word: words(params)[0] || "" };
    case "value": {  // `@value a: 1px` (no grammar: its text) / `@value a, b as c from "./x.css"` / `from global`
      const t = lex(params);
      if (t[0] && t[0].type === T.Ident && t[1] && t[1].type === T.Colon) return { define: t[0].text };
      const at = t.findIndex((x) => x.type === T.Ident && x.text === "from");
      if (at < 0) return {};
      const items = [];
      let current = [];
      for (const x of t.slice(0, at)) {
        if (x.type === T.Comma) { if (current.length) items.push(current); current = []; } else current.push(x.text);
      }
      if (current.length) items.push(current);
      const origin = t[at + 1];
      return { from: origin ? origin.text : null, items: items.map((it) => ({ name: it[0], local: it[2] || it[0] })) };
    }
    case "apply": {
      const w = words(params);
      const bang = w.length && w[w.length - 1].toLowerCase() === "!important";
      const loose = w.length > 1 && w[w.length - 1].toLowerCase() === "important" && w[w.length - 2] === "!";
      return { tokens: (bang ? w.slice(0, -1) : loose ? w.slice(0, -2) : w).join(" ") };
    }
    case "source": {
      if (!list) return unreadable;
      const inline = list.find((x) => x.type === "Function" && x.name.toLowerCase() === "inline");
      const text = list.find((x) => x.type === "String");
      const arg = inline ? kids(inline).find((x) => x.type === "String") : null;
      return { inline: arg ? arg.value : null, path: text ? text.value : null };
    }
    case "plugin": case "config": {
      if (!list) return unreadable;
      const x = list.find((y) => y.type === "String" || y.type === "Url");
      return { path: x ? x.value : null };
    }
    case "extend": {
      const S = newNames();
      try { selectorNames(cs.parse(params, { context: "selectorList" }), S, "local", false); } catch (e) { return unreadable; }
      return { classes: S.names.filter((x) => x[0] === "class").map((x) => x[1]), ...(S.lost.length ? { lost: S.lost } : {}) };
    }
    default: return n.prelude && n.prelude.type === "Raw" ? unreadable : {};  // no grammar, no exact text of ours: a hole
  }
}

// ------------------------------------------------------------------------------------------------ the tree
// A Raw made only of `;` (a stray one, `a{;}` or a `;` after a block) holds nothing: any other Raw is a hole.
const emptyRaw = (text) => text.split(";").every((x) => x.trim() === "");
// What the parser gives up on inside a block is its guess of where a statement ends (a Raw statement; a rule whose prelude
// is Raw, which swallowed the declarations before it: `@theme { --a: 1; @keyframes k { } }`). Inside a block a statement is
// a declaration or a nested rule, so the same parser reads the text again whole, as the contents of a block, with the
// positions of the source; what it still keeps as Raw is a hole. At the top level the CSS Syntax has only rules, and a
// prelude that is not a selector is an invalid rule: a hole there, its block read.
function reread(ctx, node, depth) {
  const at = node.loc.start, comments = [];
  const ast = cs.parse("x{" + ctx.text.slice(at.offset, node.loc.end.offset) + "}", { positions: true, parseCustomProperty: true,
    offset: at.offset - 2, line: at.line, column: at.column - 2, onComment: (value, loc) => comments.push([loc.start.offset, loc.end.offset]) });
  const top = kids(ast);  // a stray `}` in the text would end the wrapper early: then it is read no more than before
  if (top.length !== 1 || top[0].type !== "Rule") return [hole("statement", node, cleanLoc(ctx, node.loc))];
  ctx.comments.push(...comments);  // those inside what was Raw were not reported by the first read
  ctx.comments.sort((x, y) => x[0] - y[0]);
  return convertList(ctx, top[0].block, depth, true);
}
function convertList(ctx, node, depth, again = false) {
  if (depth > MAX_DEPTH) throw new Error(`blocks nested deeper than ${MAX_DEPTH}`);
  const out = [], inBlock = depth > 0 && !again;
  for (const ch of kids(node)) {
    if (ch.type === "Rule") {
      if (ch.prelude.type === "Raw" && inBlock) out.push(...reread(ctx, ch, depth));
      else out.push(convertRule(ctx, ch, depth));
    } else if (ch.type === "Atrule") out.push(convertAt(ctx, ch, depth));
    else if (ch.type === "Declaration") out.push(convertDecl(ctx, ch));
    else if (ch.type === "Raw") {
      const text = cleanLoc(ctx, ch.loc);
      if (emptyRaw(text)) continue;
      if (inBlock) out.push(...reread(ctx, ch, depth));
      else out.push(hole("statement", ch, text));
    }
  }
  return out;
}
function convertRule(ctx, n, depth) {
  const p = n.prelude, inside = convertList(ctx, n.block, depth + 1);
  if (p.type === "Raw") return { ...hole("rule", n, cleanLoc(ctx, p.loc)), kids: inside };  // its block is read all the same
  const S = newNames();
  selectorNames(p, S, "local", ctx.svelte);
  return { t: "rule", line: n.loc.start.line, end: n.loc.end.line, sel: [cleanLoc(ctx, p.loc)], names: uniq(S.names),
           custom: [...new Set(S.custom)], ...(S.lost.length ? { lost: S.lost } : {}), kids: inside };
}
function convertAt(ctx, n, depth) {
  const raw = decode(n.name), name = raw.toLowerCase();
  const from = n.loc.start.offset + 1 + n.name.length;
  let to = n.block ? n.block.loc.start.offset : n.loc.end.offset;
  if (!n.block && ctx.text[to - 1] === ";") to -= 1;
  const params = clean(ctx, from, to);
  const children = n.block ? convertList(ctx, n.block, depth + 1) : null;
  // `text`: the at-rule as the source spells it (`@media(min-width: 1px)`), the label of what is inside
  return { t: "at", line: n.loc.start.line, end: n.loc.end.line, name: raw, params, text: clean(ctx, n.loc.start.offset, to),
           facts: atFacts(n, name, params, children || []), kids: children };
}
function convertDecl(ctx, n) {
  const important = n.important === true || (typeof n.important === "string" && n.important.toLowerCase() === "important");
  const value = cleanLoc(ctx, n.value.loc);
  const base = { t: "decl", line: n.loc.start.line, end: n.loc.end.line, prop: n.property, value, important };
  // A Raw value is exact text no grammar read: the declaration stays (a custom property is declared whatever its value,
  // an empty one too) and is a hole besides, unless it is empty.
  return n.value.type === "Raw" ? { ...base, ...(value ? { raw: true } : {}), facts: {} } : { ...base, facts: declFacts(ctx, n, n.property) };
}

function convert(item) {
  const source = item.text !== undefined ? item.text : strict.decode(fs.readFileSync(item.path));
  const text = source.split("\r\n").join("\n").split("\r").join("\n").split("\f").join(" ");
  const comments = [];
  const options = { positions: true, parseCustomProperty: true, onComment: (value, loc) => comments.push([loc.start.offset, loc.end.offset]) };
  if (item.kind === "declarations") options.context = "declarationList";
  const ast = cs.parse(text, options);
  return convertList({ text, comments, words: !!item.words, svelte: !!item.svelte }, ast, 0);
}

// One sheet at a time, each written as soon as it is done: a sheet that throws (or whose tree is too big for a string)
// is its own error, and the output never has to fit in one string.
// `require`d (benchmarks/css-parser/value_facts.cjs reads values with `declFacts`) it only exports.
module.exports = { declFacts };
if (require.main === module) {
  const fd = fs.openSync(outPath, "w");
  fs.writeSync(fd, '{"sheets":{');
  let first = true;
  for (const item of cfg.items) {
    let piece;
    try {
      piece = JSON.stringify({ tree: convert(item) });
    } catch (error) {
      piece = JSON.stringify({ error: `${(error && error.name) || "Error"}: ${String((error && error.message) || error).split("\n")[0]}`.slice(0, 200) });
    }
    fs.writeSync(fd, (first ? "" : ",") + JSON.stringify(item.key) + ":" + piece);
    first = false;
  }
  fs.writeSync(fd, `},"version":${JSON.stringify(version)},"seconds":${(Date.now() - begun) / 1000}}`);
  fs.closeSync(fd);
}
