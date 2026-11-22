// What the CSS engine would read in a declaration value that a Sass, Less or Stylus tree (or a script's style object) hands
// to the stylesheet graph: `parse(value, {context: 'value'})` and the lexer, through the engine's own `declFacts`.
// usage: node value_facts.cjs IN.json OUT.json
//   IN: {"engines": folder, "script": path of css_csstree.js, "pairs": [[property, value], ...]}
//   OUT: [{"status": "ok" | "raw" | "threw", "facts": {...}}, ...] in the order of the pairs
// "raw": the parser keeps something of the value as Raw (no grammar reads it: `$x`, `#{...}`, `@x`...); "threw": it threw.
"use strict";
const fs = require("fs");

const [inPath, outPath] = process.argv.slice(2);
const cfg = JSON.parse(fs.readFileSync(inPath, "utf8"));
const { declFacts } = require(cfg.script);  // reads IN.json as its own settings: `engines` is all it needs
const cs = require("module").createRequire(require("path").join(cfg.engines, "package.json"))("@eslint/css-tree");

const out = cfg.pairs.map(([property, value]) => {
  const comments = [];
  let tree;
  try {
    tree = cs.parse(value, { context: "value", positions: true, parseCustomProperty: true,
                             onComment: (text, loc) => comments.push([loc.start.offset, loc.end.offset]) });
  } catch (error) {
    return { status: "threw", error: String((error && error.message) || error).split("\n")[0].slice(0, 120) };
  }
  let raw = tree.type === "Raw";
  cs.walk(tree, { visit: "Raw", enter() { raw = true; } });
  try {
    const declaration = { type: "Declaration", property, value: tree, loc: { start: { line: 1 } } };
    return { status: raw ? "raw" : "ok", facts: declFacts({ text: value, comments, words: false }, declaration, property) };
  } catch (error) {
    return { status: "threw", error: String((error && error.message) || error).split("\n")[0].slice(0, 120) };
  }
});
fs.writeFileSync(outPath, JSON.stringify(out));
