// The TypeScript compiler over a project's scripts, in one process: every place a class, an id, a CSS Module
// member, a custom property or a stylesheet import is written. usage: node css_typescript.js CONFIG.json OUT.json
// CONFIG: {"tsconfig": the generated tsconfig, "root": the project, "files": [project-relative paths to read]}.
// A class expression is evaluated to its alternatives, each a list of parts: {s, c} text with the rules that
// stated it (`literal-type`: the checker's string literal type; `initializer`: a const's or a const object's
// initializer; `clsx`...), {h, x, ctx} a value not known statically (h its kind, x its text, ctx `template` or
// `concatenation` when spliced into one), {m, x} a CSS Module member (read by its own record).
"use strict";
const fs = require("fs");
const path = require("path");
const ts = require(process.env.DAODAN_TS_MODULE || "typescript");

const [configPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const cfg = JSON.parse(fs.readFileSync(configPath, "utf8"));
const parsed = ts.getParsedCommandLineOfConfigFile(cfg.tsconfig, {}, {
  ...ts.sys, onUnRecoverableConfigFileDiagnostic: (d) => { throw new Error(ts.flattenDiagnosticMessageText(d.messageText, "\n")); },
});
const program = ts.createProgram({ rootNames: parsed.fileNames, options: parsed.options });
const checker = program.getTypeChecker();
const K = ts.SyntaxKind;
const MAX = 256;
const HELPERS = /[\\/]node_modules[\\/](clsx|classnames|tailwind-merge)[\\/]/;
const MODULE = /\.module\.(css|scss|sass|less)(\?.*)?$/i;
const SHEET = /\.(css|scss|sass|less)(\?.*)?$/i;
const CLASS_ATTR = /^(class|className|[A-Za-z]+ClassName)$/;
const SELECTOR_KEY = /(^|[\s>+~&,(:])[.#]-?[A-Za-z_]/;
const CLASSLIST = { add: Infinity, remove: Infinity, replace: 2, toggle: 1, contains: 1 };
const WRAPPERS = new Set([K.ParenthesizedExpression, K.AsExpression, K.NonNullExpression, K.SatisfiesExpression,
  K.TypeAssertionExpression]);
const key = (p) => path.resolve(p).replace(/\\/g, "/").toLowerCase();
const wanted = new Map(cfg.files.map((rel) => [key(path.join(cfg.root, rel)), rel]));
const out = [];
const walked = [];
let file, modules;

function line(node) { const sf = node.getSourceFile(); return sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1; }
function text(node) { const s = node.getText(node.getSourceFile()).replace(/\s+/g, " "); return s.length > 120 ? s.slice(0, 117) + "..." : s; }
function unwrap(node) { while (node && WRAPPERS.has(node.kind)) node = node.expression; return node; }
function literal(node) {
  node = unwrap(node);
  if (!node) return null;
  if (ts.isStringLiteralLike(node)) return node.text;
  const type = checker.getTypeAtLocation(node);
  return type.isStringLiteral() ? type.value : null;
}
const one = (parts) => [parts];
const hole = (kind, node) => one([{ h: kind, x: text(node) }]);
// A value stated elsewhere (a literal type, an initializer) keeps no line: its site is where it is used.
const tag = (alts, label, here = false) => alts.map((alt) => alt.map((p) => {
  if (p.s === undefined) return p;
  const { l, ...rest } = p;
  return { ...(here ? p : rest), c: [label, ...(p.c || [])] };
}));
const within = (alts, ctx) => alts.map((alt) => alt.map((p) => (p.h && !p.ctx ? { ...p, ctx } : p)));
function union(a, b, node) { return a.length + b.length > MAX ? hole("too-many-values", node) : a.concat(b); }
function cat(a, b, node) {
  if (a.length * b.length > MAX) return hole("too-many-values", node);
  const r = [];
  for (const x of a) for (const y of b) r.push(x.concat(y));
  return r;
}

function symbolOf(node) {
  let symbol = checker.getSymbolAtLocation(node);
  if (symbol && symbol.flags & ts.SymbolFlags.Alias) symbol = checker.getAliasedSymbol(symbol);
  return symbol;
}

function constObject(object) {
  let up = object.parent;
  while (up && WRAPPERS.has(up.kind)) up = up.parent;
  if (!up) return false;
  if (up.kind === K.VariableDeclaration) return Boolean(ts.getCombinedNodeFlags(up) & ts.NodeFlags.Const);
  if (up.kind === K.PropertyAssignment) return constObject(up.parent);
  return false;
}

function moduleMember(node) {
  if (node.kind !== K.PropertyAccessExpression && node.kind !== K.ElementAccessExpression) return null;
  const target = unwrap(node.expression);
  if (target.kind !== K.Identifier || !modules.has(checker.getSymbolAtLocation(target))) return null;
  if (node.kind === K.PropertyAccessExpression) return node.name.text;
  return ts.isStringLiteralLike(node.argumentExpression) ? node.argumentExpression.text : null;
}

function onModule(node) {
  if (node.kind !== K.PropertyAccessExpression && node.kind !== K.ElementAccessExpression) return false;
  const target = unwrap(node.expression);
  return target.kind === K.Identifier && modules.has(checker.getSymbolAtLocation(target));
}

function value(node, depth) {
  if (onModule(node)) return one([{ m: moduleMember(node), x: text(node) }]);  // its member record reads it
  const type = checker.getTypeAtLocation(node);
  const types = type.isUnion() ? type.types : [type];
  if (types.every((t) => t.isStringLiteral())) return tag(types.map((t) => [{ s: t.value }]), "literal-type");
  const name = node.kind === K.PropertyAccessExpression ? node.name
    : node.kind === K.ElementAccessExpression ? node.argumentExpression : node;
  const symbol = symbolOf(name);
  const decl = symbol && (symbol.valueDeclaration || (symbol.declarations || [])[0]);
  if (decl && decl.kind === K.VariableDeclaration && decl.initializer && ts.getCombinedNodeFlags(decl) & ts.NodeFlags.Const)
    return tag(ev(decl.initializer, depth + 1), "initializer");
  if (decl && decl.kind === K.PropertyAssignment && constObject(decl.parent))
    return tag(ev(decl.initializer, depth + 1), "initializer");
  if (decl && decl.kind === K.ShorthandPropertyAssignment && constObject(decl.parent)) return ev(decl.name, depth + 1);
  if (decl && (decl.kind === K.Parameter || decl.kind === K.BindingElement)) return hole("parameter", node);
  return hole(node.kind === K.Identifier ? "variable" : node.kind === K.PropertyAccessExpression ? "property" : "element-access", node);
}

function helperName(callee) {
  const symbol = symbolOf(callee.kind === K.PropertyAccessExpression ? callee.name : callee);
  for (const decl of (symbol && symbol.declarations) || []) {
    const found = HELPERS.exec(decl.getSourceFile().fileName);
    if (found) return found[1];
  }
  return null;
}

// Arguments joined by spaces: their alternatives side by side, since no token spans two of them.
function classArgs(args, depth) {
  const parts = [];
  for (const arg of args) for (const alt of classArg(arg, depth)) parts.push({ s: " " }, ...alt);
  return one(parts);
}

function classArg(arg, depth) {
  arg = unwrap(arg);
  if (arg.kind === K.ArrayLiteralExpression) return classArgs(arg.elements, depth + 1);
  if (arg.kind === K.ObjectLiteralExpression) {
    const alts = [];
    for (const p of arg.properties) {
      const name = p.name && (ts.isIdentifier(p.name) || ts.isStringLiteralLike(p.name)) ? p.name.text : null;
      alts.push(name === null ? [{ h: "computed-key", x: text(p) }] : [{ s: name, l: line(p.name) }]);
    }
    return alts;
  }
  if (arg.kind === K.SpreadElement) return hole("spread", arg);
  return ev(arg, depth + 1);
}

function call(node, depth) {
  const callee = unwrap(node.expression);
  if (callee.kind === K.PropertyAccessExpression && callee.name.text === "join"
      && unwrap(callee.expression).kind === K.ArrayLiteralExpression && node.arguments.length === 1
      && ts.isStringLiteralLike(node.arguments[0]) && /^\s+$/.test(node.arguments[0].text))
    return classArgs(unwrap(callee.expression).elements, depth);
  const helper = helperName(callee);
  return helper ? tag(classArgs(node.arguments, depth), helper, true) : hole("call", node);
}

function ev(node, depth) {
  node = unwrap(node);
  if (!node) return one([]);
  if (depth > 12) return hole("too-deep", node);
  switch (node.kind) {
    case K.StringLiteral: case K.NoSubstitutionTemplateLiteral: return one([{ s: node.text, l: line(node) }]);
    case K.TemplateExpression: {
      let acc = one([{ s: node.head.text, l: line(node.head) }]);
      for (const span of node.templateSpans) {
        acc = cat(cat(acc, within(ev(span.expression, depth + 1), "template"), node), one([{ s: span.literal.text, l: line(span.literal) }]), node);
      }
      return acc;
    }
    case K.ConditionalExpression: return union(ev(node.whenTrue, depth + 1), ev(node.whenFalse, depth + 1), node);
    case K.BinaryExpression: {
      const op = node.operatorToken.kind;
      if (op === K.AmpersandAmpersandToken) return union(ev(node.right, depth + 1), one([]), node);
      if (op === K.BarBarToken || op === K.QuestionQuestionToken) return union(ev(node.left, depth + 1), ev(node.right, depth + 1), node);
      if (op === K.PlusToken) return cat(within(ev(node.left, depth + 1), "concatenation"), within(ev(node.right, depth + 1), "concatenation"), node);
      return hole("expression", node);
    }
    case K.Identifier: return node.text === "undefined" ? one([]) : value(node, depth);
    case K.PropertyAccessExpression: case K.ElementAccessExpression: return value(node, depth);
    case K.CallExpression: return call(node, depth);
    case K.NullKeyword: case K.FalseKeyword: return one([]);
    default: return hole("expression", node);
  }
}

function classes(node, kind, alts, chain) { out.push({ t: "classes", file, line: line(node), kind, chain, alts }); }

function isStyleObject(node) {
  let up = node.parent;
  while (up && WRAPPERS.has(up.kind)) up = up.parent;
  if (up && up.kind === K.JsxExpression && up.parent.kind === K.JsxAttribute && up.parent.name.getText() === "style") return true;
  const type = checker.getContextualType(node);
  const name = type && ((type.aliasSymbol && type.aliasSymbol.name) || (type.symbol && type.symbol.name));
  return name === "CSSProperties";
}

function visit(node) {
  switch (node.kind) {
    case K.ImportDeclaration: {
      const spec = node.moduleSpecifier.text;
      if (SHEET.test(spec)) out.push({ t: "import", file, line: line(node), spec });
      const clause = node.importClause;
      if (MODULE.test(spec) && clause) {
        if (clause.name) modules.set(checker.getSymbolAtLocation(clause.name), spec);
        const bindings = clause.namedBindings;
        if (bindings && ts.isNamespaceImport(bindings)) modules.set(checker.getSymbolAtLocation(bindings.name), spec);
        else if (bindings) for (const el of bindings.elements) out.push({ t: "member", file, line: line(el), spec, name: (el.propertyName || el.name).text });
      }
      return;  // nothing below an import is a class
    }
    case K.JsxAttribute: {
      const name = node.name.getText();
      const init = node.initializer;
      const expr = init && (init.kind === K.JsxExpression ? init.expression : init);
      if (expr && CLASS_ATTR.test(name)) classes(node, "class", ev(expr, 0), []);
      else if (expr && name === "id") classes(node, "id", ev(expr, 0), []);
      break;
    }
    case K.CallExpression: {
      const callee = unwrap(node.expression);
      const first = node.arguments[0];
      if (callee.kind === K.PropertyAccessExpression) {
        const method = callee.name.text;
        const receiver = unwrap(callee.expression);
        if (receiver.kind === K.PropertyAccessExpression && receiver.name.text === "classList" && method in CLASSLIST)
          classes(node, "class", classArgs(node.arguments.slice(0, CLASSLIST[method]), 0), ["classList"]);
        const name = first && literal(first);
        if (method === "setAttribute" && (name === "class" || name === "id") && node.arguments[1])
          classes(node, name, ev(node.arguments[1], 0), ["setAttribute"]);
        if (method === "setProperty" && name)
          out.push({ t: "decl", file, line: line(first), property: name, value: node.arguments[1] ? literal(node.arguments[1]) : null, via: "setProperty" });
        if (method === "getPropertyValue" && name && name.startsWith("--")) out.push({ t: "text", file, line: line(first), text: `var(${name})` });
      }
      const loads = (callee.kind === K.Identifier && callee.text === "require") || node.expression.kind === K.ImportKeyword;
      if (loads && first && ts.isStringLiteralLike(first) && SHEET.test(first.text)) out.push({ t: "import", file, line: line(node), spec: first.text });
      break;
    }
    case K.BinaryExpression:
      if (node.operatorToken.kind === K.EqualsToken && node.left.kind === K.PropertyAccessExpression && node.left.name.text === "className")
        classes(node, "class", ev(node.right, 0), ["className="]);
      break;
    case K.ObjectLiteralExpression: {
      const style = isStyleObject(node);
      for (const p of node.properties) {
        if (p.kind !== K.PropertyAssignment || !(ts.isIdentifier(p.name) || ts.isStringLiteralLike(p.name))) continue;
        const name = p.name.text;
        // A selector key whose value is a declaration block: a CSS-in-JS rule (CodeMirror themes, JSS, emotion
        // objects), read only to tell its class names apart from names no rule declares.
        if (ts.isStringLiteralLike(p.name) && SELECTOR_KEY.test(name) && unwrap(p.initializer).kind === K.ObjectLiteralExpression)
          out.push({ t: "css-in-js", file, line: line(p), selector: name });
        if (name.startsWith("--")) out.push({ t: "decl", file, line: line(p), property: name, value: literal(p.initializer), via: "object-key" });
        else if (style) {
          const v = literal(p.initializer);
          const property = name.replace(/[A-Z]/g, (m) => "-" + m.toLowerCase()).replace(/^(webkit|moz|ms)-/, "-$1-");
          if (v !== null) out.push({ t: "decl", file, line: line(p), property, value: v, via: "style-object" });
        }
      }
      break;
    }
    case K.VariableDeclaration:
      if (node.name.kind === K.ObjectBindingPattern && node.initializer && unwrap(node.initializer).kind === K.Identifier) {
        const spec = modules.get(checker.getSymbolAtLocation(unwrap(node.initializer)));
        if (spec) for (const el of node.name.elements) {
          const name = el.propertyName || el.name;
          if (ts.isIdentifier(name) || ts.isStringLiteralLike(name)) out.push({ t: "member", file, line: line(el), spec, name: name.text });
        }
      }
      break;
    case K.PropertyAccessExpression: case K.ElementAccessExpression: {
      const target = unwrap(node.expression);
      const spec = target.kind === K.Identifier && modules.get(checker.getSymbolAtLocation(target));
      if (spec) {
        const name = moduleMember(node);
        if (name !== null) out.push({ t: "member", file, line: line(node), spec, name });
        else out.push({ t: "hole", file, line: line(node), kind: "module-member", cls: "dynamic-member", name: text(node) });
        return;
      }
      break;
    }
    case K.StringLiteral: case K.NoSubstitutionTemplateLiteral: case K.TemplateHead: case K.TemplateMiddle: case K.TemplateTail: {
      const raw = node.getText(node.getSourceFile());
      if (raw.includes("var(--")) out.push({ t: "text", file, line: line(node), text: raw });
      break;
    }
  }
  ts.forEachChild(node, visit);
}

for (const sf of program.getSourceFiles()) {
  const rel = wanted.get(key(sf.fileName));
  if (rel === undefined) continue;
  file = rel;
  modules = new Map();
  walked.push(rel);
  visit(sf);
}
fs.writeFileSync(outPath, JSON.stringify({ typescript: ts.version, files: walked, records: out,
  seconds: (Date.now() - begun) / 1000 }));
