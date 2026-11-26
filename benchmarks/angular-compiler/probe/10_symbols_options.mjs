// Follow-up 2: the lazy symbol resolvers of the TemplateTypeChecker, which option is really needed, host bindings option, full ngc --help.
import { C, fs, events, q, p } from './_lib.mjs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import ts from 'typescript';

const cli = await import('@angular/compiler-cli');

function make(extra) {
  const config = cli.readConfiguration('/fixture/tsconfig.json');
  Object.assign(config.options, extra);
  const host = cli.createCompilerHost({ options: config.options });
  const program = cli.createProgram({ rootNames: config.rootNames, options: config.options, host });
  return program;
}

console.log('=== A. which option makes getTemplateTypeChecker() work (each in a fresh program) ===');
for (const extra of [{}, { _enableTemplateTypeChecker: true }, { enableTemplateTypeChecker: true }, { _enableTemplateTypeChecker: true, enableTemplateTypeChecker: true }]) {
  const program = make(extra);
  await program.loadNgStructureAsync();
  try { program.compiler.getTemplateTypeChecker(); console.log(`${JSON.stringify(extra)} -> works`); } catch (e) { console.log(`${JSON.stringify(extra)} -> threw: ${e.message}`); }
}

const program = make({ _enableTemplateTypeChecker: true });
await program.loadNgStructureAsync();
const compiler = program.compiler;
const ttc = compiler.getTemplateTypeChecker();
const tsProgram = program.getTsProgram();
const checker = tsProgram.getTypeChecker();
const where = (node) => { const sf = node.getSourceFile(); const { line, character } = sf.getLineAndCharacterOfPosition(node.getStart()); return `${path.relative('/fixture', sf.fileName)}:${line}:${character}`; };
function find(file, name) {
  const sf = tsProgram.getSourceFile(file);
  let out;
  const visit = (n) => { if (ts.isClassDeclaration(n) && n.name?.text === name) out = n; ts.forEachChild(n, visit); };
  visit(sf);
  return out;
}

console.log('\n=== B. lazy resolvers: getTsSymbolOfSymbol / getTypeOfSymbol on the symbols getSymbolOfNode returns ===');
for (const m of ['getTsSymbolOfSymbol', 'getTypeOfSymbol', 'getTsSymbolOfReference']) console.log(`${m}: ${ttc[m].toString().slice(0, 300).replace(/\s+/g, ' ')}`);
{
  const comp = find('/fixture/src/app/app.component.ts', 'AppComponent');
  const nodes = ttc.getTemplate(comp);
  const want = ['save()', 'this.save()', 'svc.cancel()', '!busy && save()', 'busy ? close() : reopen()', 'save(); close()', 'router.navigate([\'/orders\'])'];
  const seen = new Set();
  for (const { ev } of events(nodes)) {
    if (!want.includes(ev.handler.source) || seen.has(ev)) continue;
    seen.add(ev);
    const calls = [];
    class V extends C.RecursiveAstVisitor { visitCall(a, x) { calls.push(a); return super.visitCall(a, x); } }
    new V().visit(ev.handler.ast);
    for (const call of calls) {
      const target = call.receiver; // the PropertyRead naming the method
      let line = `${q(ev.handler.source)} method ${target.name}: `;
      try {
        const sym = ttc.getSymbolOfNode(target, comp);
        const tsSym = sym ? ttc.getTsSymbolOfSymbol(sym) : null;
        const ty = sym ? ttc.getTypeOfSymbol(sym) : null;
        line += `getSymbolOfNode -> ${sym ? 'kind ' + sym.kind : 'null'}; getTsSymbolOfSymbol -> ${tsSym ? `${tsSym.name} decl=${(tsSym.declarations ?? []).map((d) => `${where(d)} ${q(d.getText().split('\n')[0].slice(0, 50))}`).join(' | ')}` : tsSym}; getTypeOfSymbol -> ${ty ? checker.typeToString(ty) : ty}`;
      } catch (e) { line += `THREW ${String(e.message).split('\n')[0]}`; }
      console.log(line);
    }
  }
  // also the (saved) output of the child component and a DOM event
  for (const { ev } of events(nodes)) {
    if (!['onSaved($event)', 'save()', 'submit()'].includes(ev.handler.source)) continue;
    try {
      const sym = ttc.getSymbolOfNode(ev, comp);
      const b = sym.bindings[0];
      const ts1 = b ? ttc.getTsSymbolOfSymbol(b) : null;
      console.log(`event ${ev.name} (${ev.handler.source}): getSymbolOfNode kind ${sym.kind}, bindings ${sym.bindings.length}; getTsSymbolOfSymbol(bindings[0]) -> ${ts1 ? `${ts1.name} ${(ts1.declarations ?? []).map(where).join('|')}` : ts1}`);
    } catch (e) { console.log(`event ${ev.name} THREW ${String(e.message).split('\n')[0]}`); }
  }
}

console.log('\n=== C. getHostElement with and without typeCheckHostBindings ===');
for (const extra of [{ _enableTemplateTypeChecker: true }, { _enableTemplateTypeChecker: true, typeCheckHostBindings: true }]) {
  const pr = make(extra);
  await pr.loadNgStructureAsync();
  const t = pr.compiler.getTemplateTypeChecker();
  const sf = pr.getTsProgram().getSourceFile('/fixture/src/app/inline.component.ts');
  let cls;
  const visit = (n) => { if (ts.isClassDeclaration(n) && n.name?.text === 'InlineComponent') cls = n; ts.forEachChild(n, visit); };
  visit(sf);
  const h = t.getHostElement(cls);
  console.log(`${JSON.stringify(extra)} -> getHostElement: ${h ? `HostElement with ${h.listeners.length} listeners [${h.listeners.map((l) => l.name + '@' + (l.target ?? '-')).join(', ')}], ${h.bindings.length} bindings` : h}`);
}

console.log('\n=== D. full ngc --help ===');
{
  const r = spawnSync('node', ['node_modules/@angular/compiler-cli/bundles/src/bin/ngc.js', '--help'], { cwd: '/fixture', encoding: 'utf8' });
  console.log(r.stdout + r.stderr);
}
