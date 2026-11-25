// Point 5a: @angular/compiler-cli: the ngc command and the programmatic NgtscProgram / TemplateTypeChecker.
import { C, fs, events, walk, reportEvents, q, p, render, HTML_EVENTS } from './_lib.mjs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import ts from 'typescript';

console.log('=== A. ngc command ===');
{
  const t0 = Date.now();
  const r = spawnSync('node', ['node_modules/@angular/compiler-cli/bundles/src/bin/ngc.js', '-p', 'tsconfig.json', '--outDir', '/tmp/ngc-out'], { cwd: '/fixture', encoding: 'utf8' });
  console.log(`exit ${r.status} in ${Date.now() - t0} ms; stdout ${q(r.stdout.slice(0, 1500))}; stderr ${q(r.stderr.slice(0, 1500))}`);
  const walkDir = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walkDir(path.join(d, e.name)) : [path.join(d, e.name)]));
  const files = fs.existsSync('/tmp/ngc-out') ? walkDir('/tmp/ngc-out') : [];
  console.log('emitted files:', files);
  const js = '/tmp/ngc-out/app/app.component.js';
  if (fs.existsSync(js)) {
    const lines = fs.readFileSync(js, 'utf8').split('\n');
    console.log(`app.component.js: ${lines.length} lines; lines with ɵɵlistener or ctx. calls:`);
    lines.filter((l) => l.includes('listener')).slice(0, 12).forEach((l) => console.log('   ', l.trim()));
    const i = lines.findIndex((l) => l.includes('ɵɵdefineComponent'));
    console.log('defineComponent line:', i, q(lines[i] ?? ''));
  }
  console.log('does ngc have a routes/list option?', q(spawnSync('node', ['node_modules/@angular/compiler-cli/bundles/src/bin/ngc.js', '--help'], { cwd: '/fixture', encoding: 'utf8' }).stdout.slice(0, 600)));
}

console.log('\n=== B. programmatic: NgtscProgram ===');
const cli = await import('@angular/compiler-cli');
console.log('compiler-cli exports:', Object.keys(cli).sort().join(', '));
const config = cli.readConfiguration('/fixture/tsconfig.json');
console.log('readConfiguration: errors', JSON.stringify(config.errors), 'rootNames', config.rootNames);
// The TemplateTypeChecker is refused unless this internal option is on (the first run threw without it).
config.options._enableTemplateTypeChecker = true;
config.options.enableTemplateTypeChecker = true;
const host = cli.createCompilerHost({ options: config.options });
const program = cli.createProgram({ rootNames: config.rootNames, options: config.options, host });
console.log('program class:', program.constructor.name, '; methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(program)).join(', '));
const t0 = Date.now();
await program.loadNgStructureAsync();
console.log(`loadNgStructureAsync done in ${Date.now() - t0} ms`);
const compiler = program.compiler;
console.log('NgCompiler methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(compiler)).join(', '));
let ttc = null;
try { ttc = compiler.getTemplateTypeChecker(); console.log('TemplateTypeChecker methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(ttc)).join(', ')); } catch (e) { console.log('getTemplateTypeChecker threw:', e.message); }

const diags = compiler.getDiagnostics();
console.log(`compiler.getDiagnostics(): ${diags.length} diagnostics`, diags.slice(0, 5).map((d) => ts.flattenDiagnosticMessageText(d.messageText, '\n')));

const tsProgram = program.getTsProgram();
const checker = tsProgram.getTypeChecker();
const where = (node) => {
  const sf = node.getSourceFile();
  const { line, character } = sf.getLineAndCharacterOfPosition(node.getStart());
  return `${path.relative('/fixture', sf.fileName)}:${line}:${character}`;
};

// every @Component class of the program
const comps = [];
for (const sf of tsProgram.getSourceFiles()) {
  if (!sf.fileName.startsWith('/fixture/src/')) continue;
  const visit = (n) => {
    if (ts.isClassDeclaration(n) && (ts.getDecorators(n) ?? []).some((d) => ts.isCallExpression(d.expression) && ['Component', 'NgModule'].includes(d.expression.expression.getText()))) comps.push(n);
    ts.forEachChild(n, visit);
  };
  visit(sf);
}
console.log('decorated classes:', comps.map((c) => `${c.name.text} (${where(c)})`).join(', '));

console.log('\n=== C. which class owns a template file: getComponentsWithTemplateFile ===');
for (const f of ['/fixture/src/app/app.component.html', '/fixture/src/app/legacy.component.html', '/fixture/src/app/inline.component.ts']) {
  try {
    const set = compiler.getComponentsWithTemplateFile(f);
    console.log(f, '-> NgCompiler.getComponentsWithTemplateFile:', [...set].map((c) => `${c.name.text} (${where(c)})`));
    if (ttc) console.log('   TemplateTypeChecker.getComponentsWithTemplateFile:', [...ttc.getComponentsWithTemplateFile(f)].map((c) => c.name.text));
  } catch (e) { console.log(f, 'threw', e.message); }
}
for (const c of comps) {
  try { const r = compiler.getResourceDependencies?.(c); console.log(`${c.name.text}: getResourceDependencies ->`, r ? [...r].map((s) => s.fileName ?? s) : r); } catch (e) { console.log(c.name.text, 'getResourceDependencies threw', e.message); }
}

console.log('\n=== D. getTemplate(component): the nodes Angular itself holds ===');
const tsTexts = {};
const symbolRows = [];
for (const c of comps) {
  let nodes;
  if (!ttc) { console.log('no TemplateTypeChecker; skipping getTemplate'); break; }
  try { nodes = ttc.getTemplate(c); } catch (e) { console.log(`${c.name.text}: getTemplate threw ${e.message}`); continue; }
  if (!nodes) { console.log(`${c.name.text}: getTemplate -> ${nodes}`); continue; }
  const evs = [...events(nodes)];
  console.log(`${c.name.text}: getTemplate -> ${nodes.length} top-level nodes, ${evs.length} bound events`);
  // positions: which file do the spans belong to, and do they land on the attribute text?
  for (const { ev } of evs.slice(0, 40)) {
    const file = ev.sourceSpan.start.file;
    const txt = file.content;
    const covered = txt.slice(ev.sourceSpan.start.offset, ev.sourceSpan.end.offset);
    console.log(`   ${q(ev.handler.source)} sourceSpan in ${path.relative('/fixture', file.url)} ${p(ev.sourceSpan.start)}..${p(ev.sourceSpan.end)} covers ${q(covered)}`);
  }
  // method declaration for each call in each handler
  for (const { ev } of evs) {
    const calls = [];
    class V extends C.RecursiveAstVisitor { visitCall(a, x) { calls.push(a); return super.visitCall(a, x); } visitSafeCall(a, x) { calls.push(a); return super.visitSafeCall(a, x); } }
    new V().visit(ev.handler.ast);
    for (const call of calls) {
      const tries = { call, 'call.receiver': call.receiver, 'handler(ASTWithSource)': ev.handler };
      for (const [lbl, node] of Object.entries(tries)) {
        try {
          const sym = ttc.getSymbolOfNode(node, c);
          if (!sym) { symbolRows.push(`${c.name.text} ${q(ev.handler.source)} getSymbolOfNode(${lbl}) -> null`); continue; }
          const decls = (sym.tsSymbol?.declarations ?? []).map((d) => `${where(d)} ${q(d.getText().split('\n')[0].slice(0, 60))}`);
          symbolRows.push(`${c.name.text} ${q(ev.handler.source)} getSymbolOfNode(${lbl}) -> kind=${sym.kind} tsSymbol=${sym.tsSymbol?.name} decl=${JSON.stringify(decls)} type=${sym.tsType ? checker.typeToString(sym.tsType) : '-'}`);
        } catch (e) { symbolRows.push(`${c.name.text} ${q(ev.handler.source)} getSymbolOfNode(${lbl}) THREW ${String(e.message).split('\n')[0]}`); }
      }
    }
  }
}
console.log('\n=== E. getSymbolOfNode on handler expressions: does it give the method declaration? ===');
symbolRows.forEach((r) => console.log(r));

console.log('\n=== F. routes ===');
try { console.log('program.listLazyRoutes() ->', JSON.stringify(program.listLazyRoutes())); } catch (e) { console.log('listLazyRoutes threw', e.message); }
const priv = path.join('/fixture/node_modules/@angular/compiler-cli/private');
console.log('compiler-cli/private entries:', fs.existsSync(priv) ? fs.readdirSync(priv) : '(no dir)');


console.log('\n=== G. program.getIndexedComponents(): template identifiers per component ===');
try {
  const idx = program.getIndexedComponents();
  console.log('entries:', idx.size ?? idx.length);
  const kindName = (k) => Object.entries(cli.IdentifierKind).find(([, v]) => v === k)?.[0] ?? k;
  for (const [decl, comp] of idx) {
    console.log(`component ${comp.name} selector=${comp.selector} file=${path.relative('/fixture', comp.file.fileName ?? comp.file)} template.isInline=${comp.template.isInline} template.file=${comp.template.file?.url ?? comp.template.file}`);
    const ids = [...comp.template.identifiers].filter((i) => ['Method', 'Property'].includes(kindName(i.kind)));
    console.log('   method/property identifiers:', ids.map((i) => `${kindName(i.kind)}:${i.name}@${i.span.start}-${i.span.end}`).join(' '));
  }
} catch (e) { console.log('getIndexedComponents threw', e.stack.split('\n').slice(0, 3).join(' | ')); }
