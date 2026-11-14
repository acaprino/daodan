// One TypeScript program over a project, every call and `new` asked to the checker in one process.
// usage: node ts_compiler.js TSCONFIG OUT.jsonl
// TypeScript is required from DAODAN_TS_MODULE (the 6.0 API: TypeScript 7.0 ships without one).
// One JSON line per call site: site and callee name position, how the callee was found (`signature`:
// getResolvedSignature's declaration; `symbol`: getSymbolAtLocation, through getAliasedSymbol), the
// declaration's file, start (after export/default/declare, as tree-sitter starts it) and syntax kind, the
// enclosing function's start, and whether the receiver's type is `any`. The last line holds the run's counts.
"use strict";
const fs = require("fs");
const ts = require(process.env.DAODAN_TS_MODULE || "@typescript/typescript6");
const [configPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const parsed = ts.getParsedCommandLineOfConfigFile(configPath, {}, {
  ...ts.sys, onUnRecoverableConfigFileDiagnostic: (d) => { throw new Error(ts.flattenDiagnosticMessageText(d.messageText, "\n")); },
});
const program = ts.createProgram({ rootNames: parsed.fileNames, options: parsed.options });
const checker = program.getTypeChecker();
const out = fs.openSync(outPath, "w");
const roots = new Set(parsed.fileNames.map((f) => ts.sys.realpath ? ts.sys.realpath(f) : f));
const K = ts.SyntaxKind;
const WRAPPER = new Set([K.ParenthesizedExpression, K.AsExpression, K.NonNullExpression, K.SatisfiesExpression,
  K.TypeAssertionExpression]);
const FUNCTION = new Set([K.FunctionDeclaration, K.FunctionExpression, K.ArrowFunction, K.MethodDeclaration,
  K.Constructor, K.GetAccessor, K.SetAccessor, K.ClassDeclaration, K.ClassExpression]);
const SKIPPED = new Set([K.ExportKeyword, K.DefaultKeyword, K.DeclareKeyword]);
const counts = { files: 0, calls: 0, signature: 0, symbol: 0, none: 0, errors: 0 };

function pos(sf, at) { const p = sf.getLineAndCharacterOfPosition(at); return [p.line + 1, p.character]; }

function start(node) {
  // tree-sitter wraps `export` and `default` around a declaration; its node starts after them.
  const sf = node.getSourceFile();
  const mods = ts.canHaveModifiers(node) ? (ts.getModifiers(node) || []) : [];
  let at = node.getStart(sf);
  for (const m of mods) { if (SKIPPED.has(m.kind) && m.getStart(sf) === at) at = ts.skipTrivia(sf.text, m.end); }
  return pos(sf, at);
}

function declaration(node) {
  if (!node) return null;
  if (node.kind === K.Constructor) node = node.parent;  // a constructor is its class, as the snapshot names it
  // An overload signature names the body that implements it.
  if ((node.kind === K.FunctionDeclaration || node.kind === K.MethodDeclaration) && !node.body && node.name) {
    const symbol = checker.getSymbolAtLocation(node.name);
    const body = symbol && (symbol.declarations || []).find((d) => d.kind === node.kind && d.body);
    if (body) node = body;
  }
  const sf = node.getSourceFile();
  return { file: sf.fileName, start: start(node), kind: K[node.kind] };
}

function viaSymbol(name) {
  let symbol = checker.getSymbolAtLocation(name);
  if (symbol && symbol.flags & ts.SymbolFlags.Alias) symbol = checker.getAliasedSymbol(symbol);
  if (!symbol) return null;
  return symbol.valueDeclaration || (symbol.declarations || [])[0] || null;
}

function enclosing(node) {
  for (let up = node.parent; up; up = up.parent) if (FUNCTION.has(up.kind)) return start(up);
  return null;
}

function visit(sf, node) {
  if (node.kind === K.CallExpression || node.kind === K.NewExpression) {
    counts.calls++;
    let callee = node.expression;
    while (callee && WRAPPER.has(callee.kind)) callee = callee.expression;
    let name = callee, receiverAny = null;
    if (callee && (callee.kind === K.PropertyAccessExpression || callee.kind === K.ElementAccessExpression)) {
      name = callee.kind === K.PropertyAccessExpression ? callee.name : callee.argumentExpression;
      try { receiverAny = !!(checker.getTypeAtLocation(callee.expression).flags & ts.TypeFlags.Any); } catch { receiverAny = null; }
    }
    const row = { site: pos(sf, (name || node).getStart(sf)), kind: node.kind === K.NewExpression ? "new" : "call",
      text: callee ? callee.getText(sf).slice(0, 80) : "", caller: enclosing(node), receiver_any: receiverAny };
    try {
      const signature = checker.getResolvedSignature(node);
      let found = signature && signature.declaration && signature.declaration.kind !== K.JSDocSignature
        ? signature.declaration : null;
      row.via = found ? "signature" : null;
      if (!found && name && name.kind !== K.StringLiteral) { found = viaSymbol(name); row.via = found ? "symbol" : null; }
      row.decl = declaration(found);
      counts[row.via || "none"]++;
    } catch (error) {
      counts.errors++; row.error = String(error).slice(0, 200);
    }
    fs.writeSync(out, JSON.stringify(row) + "\n");
  }
  ts.forEachChild(node, (child) => visit(sf, child));
}

for (const sf of program.getSourceFiles()) {
  if (sf.isDeclarationFile || sf.fileName.includes("/node_modules/")) continue;
  if (!roots.has(ts.sys.realpath ? ts.sys.realpath(sf.fileName) : sf.fileName) && !roots.has(sf.fileName)) continue;
  counts.files++;
  fs.writeSync(out, JSON.stringify({ file: sf.fileName }) + "\n");
  visit(sf, sf);
}
counts.seconds = (Date.now() - begun) / 1000;
counts.version = ts.version;
counts.program_files = program.getSourceFiles().length;
fs.writeSync(out, JSON.stringify({ counts }) + "\n");
fs.closeSync(out);
