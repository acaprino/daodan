// The TypeScript compiler over a project's scripts, in one process: every place a class, an id, a CSS Module
// member, a custom property or a stylesheet import is written. usage: node css_typescript.js CONFIG.json OUT.json
// CONFIG: {"tsconfig": the generated tsconfig, "root": the project, "files": [project-relative paths to read]}.
// A class expression is evaluated to its alternatives, each a list of parts: {s, c} text with the rules that
// stated it (`literal-type`: the checker's string literal type; `initializer`: a const's or a const object's
// initializer; `clsx`...), {h, x, ctx} a value not known statically (h its kind, x its text, ctx `template` or
// `concatenation` when spliced into one), {m, x} a CSS Module member (read by its own record). Every module a file
// loads (import, export from, dynamic import, require) is a `module` record, with the file TypeScript resolves it to.
// CSS-in-JS is read where the package that declares the callee or tag says it is one, never by a bare name: the
// tagged templates of styled-components and emotion (`cssinjs-text`, the template's CSS with each interpolation a
// placeholder unless it is a string literal) and the object styles of vanilla-extract, CodeMirror's
// `EditorView.theme`/`baseTheme`, Stitches, emotion and MUI (`styled`, `sx`) (`cssinjs`, a neutral tree).
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
// Variant tables: every literal of the table is a class written there; a call of the function it makes is read there.
const TABLES = /[\\/]node_modules[\\/](class-variance-authority|tailwind-variants)[\\/]/;
const ANGULAR = /[\\/]node_modules[\\/]@angular[\\/]core[\\/]/;
const MODULE = /\.module\.(css|scss|sass|less|styl|pcss)(\?.*)?$/i;
const SHEET = /\.(css|scss|sass|less|pcss|postcss|styl|stylus)(\?.*)?$/i;
const CLASS_ATTR = /^(class|className|[A-Za-z]+ClassName)$/;
const SELECTOR_KEY = /(^|[\s>+~&,(:])[.#]-?[A-Za-z_]/;
const TEMPLATE_PACKAGES = /[\\/]node_modules[\\/](styled-components|@emotion[\\/](?:styled|react|css))[\\/]/;
const OBJECT_PACKAGES = /[\\/]node_modules[\\/](@codemirror[\\/]view|@vanilla-extract[\\/]css|@stitches[\\/](?:react|core)|@mui[\\/][\w-]+|@emotion[\\/](?:css|react|styled))[\\/]/;
const GLOBAL_STYLES = new Set(["createGlobalStyle", "injectGlobal", "globalCss"]);
const NOT_STYLES = new Set(["keyframes", "globalKeyframes", "createVar", "createTheme", "createThemeContract", "fontFace",
  "globalFontFace", "createGlobalTheme", "cx", "classnames"]);
const RULE_KEY = /^[&.#:\[>*+~]|[\s,]/;  // a string key is a selector anyway
const handled = new Set();
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

// The helper a call names: clsx, classnames or tailwind-merge by the package that declares it, or a project function
// (`cn`) whose body only returns a helper's call over its own rest parameter, which is that helper again.
function helperName(callee, depth = 0) {
  const symbol = symbolOf(callee.kind === K.PropertyAccessExpression ? callee.name : callee);
  for (const decl of (symbol && symbol.declarations) || []) {
    const found = HELPERS.exec(decl.getSourceFile().fileName);
    if (found) return found[1];
  }
  const decl = symbol && symbol.valueDeclaration;
  const fn = decl && (decl.kind === K.FunctionDeclaration ? decl : decl.kind === K.VariableDeclaration && decl.initializer
    && [K.ArrowFunction, K.FunctionExpression].includes(unwrap(decl.initializer).kind) ? unwrap(decl.initializer) : null);
  if (!fn || depth > 2 || fn.parameters.length !== 1 || !fn.parameters[0].dotDotDotToken) return null;
  const rest = fn.parameters[0].name.getText();
  let body = fn.body && unwrap(fn.body);
  if (body && body.kind === K.Block) body = body.statements.length === 1 && body.statements[0].kind === K.ReturnStatement
    ? unwrap(body.statements[0].expression) : null;
  const passes = (call) => call && call.kind === K.CallExpression && call.arguments.length === 1
    && (unwrap(call.arguments[0]).getText() === rest || (unwrap(call.arguments[0]).kind === K.SpreadElement
      && unwrap(call.arguments[0]).expression.getText() === rest) || passes(unwrap(call.arguments[0])));
  return body && body.kind === K.CallExpression && passes(body) ? helperName(unwrap(body.expression), depth + 1) : null;
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

function tableOf(expr) {
  const found = chain(expr);
  const hit = found && found.files.map((f) => TABLES.exec(f)).find(Boolean);
  return hit ? hit[1] : null;
}
// A cva(base, {variants, compoundVariants}) or tv({base, slots, variants, compoundVariants}) table, its strings sites.
function table(node, label) {
  const strings = (value) => {
    value = unwrap(value);
    if (ts.isStringLiteralLike(value)) classes(value, "class", [[{ s: value.text }]], [label]);
    else if (value.kind === K.ArrayLiteralExpression) value.elements.forEach(strings);
    else if (value.kind === K.ObjectLiteralExpression)
      for (const p of value.properties) if (p.kind === K.PropertyAssignment) strings(p.initializer);
  };
  for (const arg of node.arguments) {
    const value = unwrap(arg);
    if (value.kind !== K.ObjectLiteralExpression) { strings(value); continue; }
    for (const p of value.properties) {
      if (p.kind !== K.PropertyAssignment || !p.name) continue;
      const key = p.name.getText().replace(/['"]/g, "");
      if (key === "defaultVariants" || key === "extend") continue;
      if (key === "compoundVariants" || key === "compoundSlots") {
        for (const el of unwrap(p.initializer).elements || []) {
          if (unwrap(el).kind !== K.ObjectLiteralExpression) continue;
          for (const q of unwrap(el).properties)
            if (q.kind === K.PropertyAssignment && /^(class|className)$/.test(q.name.getText())) strings(q.initializer);
        }
      } else strings(p.initializer);
    }
  }
}

function call(node, depth) {
  const callee = unwrap(node.expression);
  if (callee.kind === K.Identifier) {  // a function a variant table made: its classes are read at the table
    const symbol = symbolOf(callee);
    const decl = symbol && symbol.valueDeclaration;
    if (decl && decl.kind === K.VariableDeclaration && decl.initializer && unwrap(decl.initializer).kind === K.CallExpression
        && tableOf(unwrap(decl.initializer).expression)) return one([]);
  }
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

// The package a name comes from, read from the file that declares the leftmost name of an access or call chain.
function chain(expr) {
  const names = [];
  let node = unwrap(expr);
  while (node) {
    if (node.kind === K.PropertyAccessExpression) { names.unshift(node.name.text); node = unwrap(node.expression); }
    else if (node.kind === K.CallExpression || node.kind === K.TaggedTemplateExpression) node = unwrap(node.expression || node.tag);
    else if (node.kind === K.Identifier) { names.unshift(node.text); break; }
    else return null;
  }
  let symbol = node && checker.getSymbolAtLocation(node);
  if (symbol && symbol.flags & ts.SymbolFlags.Alias) symbol = checker.getAliasedSymbol(symbol);
  const files = ((symbol && symbol.declarations) || []).map((d) => d.getSourceFile().fileName);
  return { names, files };
}
function fromPackage(expr, pattern) {
  const found = chain(expr);
  return found && found.files.some((f) => pattern.test(f)) ? found.names[found.names.length - 1] : null;
}

// An object style as the neutral tree css.py reads: a key naming a selector is a rule, an `@` key an at-rule
// (vanilla-extract's `'@media': {query: ...}` too), `selectors` holds rules, any other object nests in place.
function styleTree(object) {
  const kids = [];
  for (const p of object.properties) {
    if (p.kind !== K.PropertyAssignment || !(ts.isIdentifier(p.name) || ts.isStringLiteralLike(p.name))) continue;
    const key = p.name.text, value = unwrap(p.initializer), at = line(p);
    if (value.kind === K.ObjectLiteralExpression) {
      if (key === "selectors") kids.push({ t: "block", line: at, refs: [], kids: styleTree(value).map((k) => k) });
      else if (/^@(media|supports|container|layer)$/.test(key))
        for (const q of value.properties) {
          if (q.kind === K.PropertyAssignment && q.name && unwrap(q.initializer).kind === K.ObjectLiteralExpression)
            kids.push({ t: "at", line: line(q), name: key.slice(1), params: q.name.text || q.name.getText(), refs: [], kids: styleTree(unwrap(q.initializer)) });
        }
      else if (key.startsWith("@")) {
        const m = /^@([\w-]+)\s*(.*)$/.exec(key);
        kids.push({ t: "at", line: at, name: m ? m[1] : key.slice(1), params: m ? m[2] : "", refs: [], kids: styleTree(value) });
      } else if (RULE_KEY.test(key) || ts.isStringLiteralLike(p.name)) kids.push({ t: "rule", line: at, sel: [key], kids: styleTree(value) });
      else kids.push({ t: "block", line: at, refs: [], kids: styleTree(value) });
      continue;
    }
    if (ts.isStringLiteralLike(value)) handled.add(value);
    const text = ts.isStringLiteralLike(value) ? value.text : value.kind === K.NumericLiteral ? value.text : "";
    const prop = key.startsWith("--") ? key : key.replace(/[A-Z]/g, (m) => "-" + m.toLowerCase()).replace(/^(webkit|moz|ms)-/, "-$1-");
    kids.push({ t: "decl", line: at, prop, value: text, refs: [] });
  }
  return kids;
}
function returned(fn) {
  const body = fn && (fn.kind === K.ArrowFunction || fn.kind === K.FunctionExpression) ? unwrap(fn.body) : null;
  return body && body.kind === K.ObjectLiteralExpression ? body : null;
}
function cssInJsCall(node) {
  const name = fromPackage(node.expression, OBJECT_PACKAGES);
  if (!name || NOT_STYLES.has(name)) return;
  const args = node.arguments.map(unwrap);
  const push = (root, object) => out.push({ t: "cssinjs", file, line: line(object), root, tree: styleTree(object) });
  if (name === "globalStyle" && args[0] && ts.isStringLiteralLike(args[0]) && args[1] && args[1].kind === K.ObjectLiteralExpression)
    return push(args[0].text, args[1]);
  if (name === "styleVariants" && args[0] && args[0].kind === K.ObjectLiteralExpression) {
    for (const p of args[0].properties)
      if (p.kind === K.PropertyAssignment && unwrap(p.initializer).kind === K.ObjectLiteralExpression) push("&", unwrap(p.initializer));
    return;
  }
  for (const arg of args) {
    const object = arg.kind === K.ObjectLiteralExpression ? arg : returned(arg);
    if (object) push(GLOBAL_STYLES.has(name) ? null : "&", object);
  }
}
function cssInJsTemplate(node) {
  const name = fromPackage(node.tag, TEMPLATE_PACKAGES);
  if (!name || NOT_STYLES.has(name)) return;
  const template = node.template, holes = {};
  let text;
  if (template.kind === K.NoSubstitutionTemplateLiteral) { text = template.rawText; handled.add(template); }
  else {
    text = template.head.rawText;
    handled.add(template.head);
    template.templateSpans.forEach((span, i) => {
      handled.add(span.literal);
      const e = unwrap(span.expression);
      if (ts.isStringLiteralLike(e)) text += e.text;
      else {
        const key = `__dd${i}__`;
        holes[key] = e.getText(e.getSourceFile()).replace(/\s+/g, " ").slice(0, 120);
        text += key + "\n".repeat((e.getText(e.getSourceFile()).match(/\n/g) || []).length);
      }
      text += span.literal.rawText;
    });
  }
  out.push({ t: "cssinjs-text", file, line: line(template), text, global: GLOBAL_STYLES.has(name), holes });
}

function loaded(node, spec) {
  const found = ts.resolveModuleName(spec, node.getSourceFile().fileName, parsed.options, ts.sys).resolvedModule;
  out.push({ t: "module", file, line: line(node), spec, to: found ? found.resolvedFileName : null });
}

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
      const script = ts.resolveModuleName(spec, node.getSourceFile().fileName, parsed.options, ts.sys).resolvedModule;
      if (SHEET.test(spec) && !script) out.push({ t: "import", file, line: line(node), spec });
      else loaded(node, spec);
      const clause = node.importClause;
      if (MODULE.test(spec) && clause) {
        if (clause.name) modules.set(checker.getSymbolAtLocation(clause.name), spec);
        const bindings = clause.namedBindings;
        if (bindings && ts.isNamespaceImport(bindings)) modules.set(checker.getSymbolAtLocation(bindings.name), spec);
        else if (bindings) for (const el of bindings.elements) out.push({ t: "member", file, line: line(el), spec, name: (el.propertyName || el.name).text });
      }
      return;  // nothing below an import is a class
    }
    case K.TaggedTemplateExpression:
      cssInJsTemplate(node);
      break;
    case K.PropertyAssignment:
      // Tailwind's `safelist`: class names its config always generates.
      if (/(^|[\\/])tailwind\.config\.[cm]?[jt]s$/.test(file) && node.name.getText() === "safelist"
          && unwrap(node.initializer).kind === K.ArrayLiteralExpression) {
        for (const el of unwrap(node.initializer).elements) {
          if (ts.isStringLiteralLike(el)) classes(el, "class", [[{ s: el.text }]], ["safelist"]);
          else out.push({ t: "hole", file, line: line(el), kind: "class", cls: "safelist-pattern", name: text(el) });
        }
      }
      break;
    case K.JsxAttribute: {
      const name = node.name.getText();
      const init = node.initializer;
      const expr = init && (init.kind === K.JsxExpression ? init.expression : init);
      if (expr && name === "sx" && unwrap(expr).kind === K.ObjectLiteralExpression
          && fromPackage(node.parent.parent.tagName, OBJECT_PACKAGES))
        out.push({ t: "cssinjs", file, line: line(expr), root: "&", tree: styleTree(unwrap(expr)) });
      if (expr && CLASS_ATTR.test(name)) classes(node, "class", ev(expr, 0), []);
      else if (expr && name === "id") classes(node, "id", ev(expr, 0), []);
      break;
    }
    case K.Decorator: {
      // Angular's @Component: its template and stylesheets load with it.
      const expr = unwrap(node.expression);
      if (expr.kind === K.CallExpression && fromPackage(expr.expression, ANGULAR) === "Component" && expr.arguments[0]
          && unwrap(expr.arguments[0]).kind === K.ObjectLiteralExpression) {
        for (const p of unwrap(expr.arguments[0]).properties) {
          if (p.kind !== K.PropertyAssignment || !p.name) continue;
          const key = p.name.getText(), value = unwrap(p.initializer);
          if (key === "templateUrl" && ts.isStringLiteralLike(value)) out.push({ t: "template", file, line: line(p), spec: value.text });
          if ((key === "styleUrl" || key === "styleUrls")) {
            for (const v of value.kind === K.ArrayLiteralExpression ? value.elements : [value])
              if (ts.isStringLiteralLike(v)) out.push({ t: "import", file, line: line(p), spec: v.text, component: true });
          }
        }
      }
      break;
    }
    case K.CallExpression: {
      cssInJsCall(node);
      const label = tableOf(node.expression);
      if (label) table(node, label === "class-variance-authority" ? "cva" : label);
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
      else if (loads && first && ts.isStringLiteralLike(first)) loaded(node, first.text);
      break;
    }
    case K.ExportDeclaration:
      if (node.moduleSpecifier && ts.isStringLiteralLike(node.moduleSpecifier)) loaded(node, node.moduleSpecifier.text);
      break;
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
      if (handled.has(node)) break;  // read as CSS-in-JS already
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
