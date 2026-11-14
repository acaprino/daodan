// Class expressions of component templates (Vue `:class`, Svelte `class={...}`, Astro `class:list`), evaluated to
// their alternatives without guessing, in the form `css_typescript.js` gives: each alternative a list of parts, {s, l}
// text and its line, {h, x, ctx} a value not known statically (h its kind), {m, x} a CSS Module member. A string, a
// template, a condition, `&&`, `||`, `??`, `+`, an array (its items side by side) and an object (each key a class
// that applies when its value holds) are read; any other value is a hole of its kind. Used by css_vue.js,
// css_svelte.js and css_astro.js; parses expression text with acorn, an ESTree tree a compiler gave is read as is.
"use strict";
const path = require("path");

const MAX = 256;

function acorn(engines) { return require(path.join(engines, "acorn")); }

// The expression of a text, its lines counted from `line`; null when acorn cannot read it (TypeScript syntax).
function parse(engines, text, line) {
  try {
    const program = acorn(engines).parse(`(${text}\n)`, { ecmaVersion: "latest", locations: true });
    const node = program.body[0].expression;
    return { node, base: line - 1 };
  } catch (error) {
    return null;
  }
}

function evaluator(source, lineOf, hooks = {}) {
  const one = (parts) => [parts];
  const text = (node) => {
    const raw = source(node).replace(/\s+/g, " ");
    return raw.length > 120 ? raw.slice(0, 117) + "..." : raw;
  };
  const hole = (kind, node) => one([{ h: kind, x: text(node) }]);
  const within = (alts, ctx) => alts.map((alt) => alt.map((p) => (p.h && !p.ctx ? { ...p, ctx } : p)));
  const union = (a, b, node) => (a.length + b.length > MAX ? hole("too-many-values", node) : a.concat(b));
  const cat = (a, b, node) => {
    if (a.length * b.length > MAX) return hole("too-many-values", node);
    const r = [];
    for (const x of a) for (const y of b) r.push(x.concat(y));
    return r;
  };
  const isString = (n) => (n.type === "Literal" && typeof n.value === "string") || n.type === "StringLiteral";

  function side(items, depth) {
    const parts = [];
    for (const item of items) {
      if (!item) continue;
      for (const alt of classArg(item, depth)) parts.push({ s: " " }, ...alt);
    }
    return one(parts);
  }

  function classArg(node, depth) {
    if (node.type === "ArrayExpression") return side(node.elements, depth + 1);
    if (node.type === "ObjectExpression") {
      const alts = [];
      for (const p of node.properties) {
        const key = p.key;
        const name = p.computed || !key ? null : key.type === "Identifier" ? key.name : isString(key) ? key.value : null;
        alts.push(name === null ? [{ h: "computed-key", x: text(p) }] : [{ s: name, l: lineOf(key) }]);
      }
      return alts;
    }
    if (node.type === "SpreadElement") return hole("spread", node);
    return ev(node, depth + 1);
  }

  function ev(node, depth = 0) {
    if (!node) return one([]);
    if (depth > 12) return hole("too-deep", node);
    const hooked = hooks.value && hooks.value(node);
    if (hooked) return hooked;
    switch (node.type) {
      case "Literal": case "StringLiteral":
        if (typeof node.value === "string") return one([{ s: node.value, l: lineOf(node) }]);
        return node.value === null || node.value === false ? one([]) : hole("expression", node);
      case "TemplateLiteral": {
        let acc = one([{ s: node.quasis[0].value.cooked, l: lineOf(node.quasis[0]) }]);
        node.expressions.forEach((e, i) => {
          acc = cat(cat(acc, within(ev(e, depth + 1), "template"), node), one([{ s: node.quasis[i + 1].value.cooked, l: lineOf(node.quasis[i + 1]) }]), node);
        });
        return acc;
      }
      case "ConditionalExpression": return union(ev(node.consequent, depth + 1), ev(node.alternate, depth + 1), node);
      case "LogicalExpression":
        if (node.operator === "&&") return union(ev(node.right, depth + 1), one([]), node);
        return union(ev(node.left, depth + 1), ev(node.right, depth + 1), node);
      case "BinaryExpression":
        if (node.operator === "+") return cat(within(ev(node.left, depth + 1), "concatenation"), within(ev(node.right, depth + 1), "concatenation"), node);
        return hole("expression", node);
      case "ArrayExpression": case "ObjectExpression": return classArg(node, depth);
      case "Identifier": return node.name === "undefined" ? one([]) : hole("variable", node);
      case "MemberExpression": return hole(node.computed ? "element-access" : "property", node);
      case "CallExpression": return hole("call", node);
      case "ParenthesizedExpression": return ev(node.expression, depth);
      default: return hole("expression", node);
    }
  }
  return { ev, classArg, side };
}

module.exports = { parse, evaluator };
